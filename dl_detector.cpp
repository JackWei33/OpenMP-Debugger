#include <iostream>
#include <unordered_map>
#include <unordered_set>
#include <string>
#include <stdexcept>
#include <fstream>
#include <thread>
#include <vector>
#include "dl_detector.h"
#include <omp-tools.h>
#include <boost/lockfree/queue.hpp>

enum EventType {
    ACQUIRE,
    ACQUIRED,
    RELEASE,
    BARRIER_BEGIN,
    BARRIER_END
};

enum BarrierState {
    NOT_IN_USE,
    IN_USE
};

struct SynchEvent {
    EventType type;
    ompt_mutex_t kind;
    ompt_wait_id_t wait_id;
    uint64_t thread_id;
};

static boost::lockfree::queue<SynchEvent> event_queue{1024};
std::atomic<bool> should_terminate{false};


void process_mutex_acquire(ompt_mutex_t kind, ompt_wait_id_t wait_id, uint64_t thread_id) {
    SynchEvent event{
        .type = EventType::ACQUIRE,
        .kind = kind,
        .wait_id = wait_id,
        .thread_id = thread_id
    };
    
    event_queue.push(event); 
}

void process_mutex_acquired(ompt_mutex_t kind, ompt_wait_id_t wait_id, uint64_t thread_id) {
    SynchEvent event{
        .type = EventType::ACQUIRED,
        .kind = kind,
        .wait_id = wait_id,
        .thread_id = thread_id
    };
    
    event_queue.push(event); 
}

void process_mutex_released(ompt_mutex_t kind, ompt_wait_id_t wait_id, uint64_t thread_id) {
    SynchEvent event{
        .type = EventType::RELEASE,
        .kind = kind,
        .wait_id = wait_id,
        .thread_id = thread_id
    };
    
    event_queue.push(event); 
}

void process_barrier(ompt_sync_region_t kind, ompt_scope_endpoint_t endpoint, uint64_t thread_id) {
    if (kind == ompt_sync_region_barrier_explicit) {
        SynchEvent event{
            .type = endpoint == ompt_scope_begin ? EventType::BARRIER_BEGIN : EventType::BARRIER_END,
            .thread_id = thread_id
        };

        event_queue.push(event);

    }
}

void start_dl_detector_thread() {
    std::thread(dl_detector_thread).detach(); // Assign new thread
}

void end_dl_detector_thread() {
    should_terminate = true;
}

class DirectedGraph {
private:
    std::unordered_map<std::string, std::unordered_set<std::string>> graph;
    std::vector<std::string> currentCycle;

    bool dfsCycleDetection(const std::string& node, std::unordered_set<std::string>& visited, 
                          std::unordered_set<std::string>& recursionStack, 
                          std::vector<std::string>& cycle) {
        if (recursionStack.find(node) != recursionStack.end()) {
            // Found cycle, reconstruct it starting from this node
            size_t start = 0;
            for (size_t i = 0; i < cycle.size(); i++) {
                if (cycle[i] == node) {
                    start = i;
                    break;
                }
            }
            currentCycle.clear();
            for (size_t i = start; i < cycle.size(); i++) {
                currentCycle.push_back(cycle[i]);
            }
            currentCycle.push_back(node);
            return true;
        }

        if (visited.find(node) != visited.end()) {
            return false;
        }

        visited.insert(node);
        recursionStack.insert(node);
        cycle.push_back(node);

        if (graph.find(node) != graph.end()) {
            for (const auto& neighbor : graph.at(node)) {
                if (dfsCycleDetection(neighbor, visited, recursionStack, cycle)) {
                    return true;
                }
            }
        }

        recursionStack.erase(node);
        cycle.pop_back();
        return false;
    }

public:
    // Add a node to the graph
    void addNode(const std::string& node) {
        if (graph.find(node) == graph.end()) {
            graph[node] = std::unordered_set<std::string>();
        }
    }

    // Add a directed edge from node1 to node2
    void addEdge(const std::string& fromNode, const std::string& toNode) {
        // Ensure both nodes exist
        if (graph.find(fromNode) == graph.end() || graph.find(toNode) == graph.end()) {
            throw std::invalid_argument("One or both nodes do not exist in the graph.");
        }
        graph[fromNode].insert(toNode);
    }

    // Remove a directed edge from node1 to node2
    void removeEdge(const std::string& fromNode, const std::string& toNode) {
        if (graph.find(fromNode) != graph.end()) {
            graph[fromNode].erase(toNode);
        }
    }

    // Display the graph (for debugging purposes)
    void display(std::ofstream& outFile) const {
        outFile << "=== Graph State ===" << std::endl;
        for (const auto& pair : graph) {
            outFile << pair.first << " -> { ";
            bool first = true;
            for (const auto& neighbor : pair.second) {
                if (!first) {
                    outFile << ", ";
                }
                outFile << neighbor;
                first = false;
            }
            outFile << " }" << std::endl;
        }
    }


    bool hasEdge(const std::string& fromNode, const std::string& toNode) const {
        if (graph.find(fromNode) == graph.end() || graph.find(toNode) == graph.end()) {
            return false;
        }

        const auto& neighbors = graph.at(fromNode);
        return neighbors.find(toNode) != neighbors.end();
    }

    bool hasCycle() {
        std::unordered_set<std::string> visited;
        std::unordered_set<std::string> recursionStack;
        std::vector<std::string> cycle;
        currentCycle.clear();

        for (const auto& pair : graph) {
            if (dfsCycleDetection(pair.first, visited, recursionStack, cycle)) {
                return true;
            }
        }
        return false;
    }

    void displayCycle(std::ofstream& outFile) const {
        if (currentCycle.empty()) {
            outFile << "No cycle detected" << std::endl;
            return;
        }

        outFile << "=== Deadlock Cycle ===" << std::endl;
        for (size_t i = 0; i < currentCycle.size(); i++) {
            outFile << currentCycle[i];
            if (i < currentCycle.size() - 1) {
                outFile << " -> ";
            }
        }
        outFile << std::endl;
    }
};


void dl_detector_thread() {
    DirectedGraph graph;
    std::unordered_map<std::string, int> threads_to_iteration;
    BarrierState barrierState = NOT_IN_USE;
    std::string barrierName = "Barrier";
    int barrier_iteration = 0;
    std::ofstream outFile("dl_detector_logs/graph_state.txt", std::ios::trunc);

    graph.addNode(barrierName);

    while (true) {
        SynchEvent event;

        while (event_queue.empty() && !should_terminate) {
        }

        if (should_terminate && event_queue.empty()) {
            break;
        }

        if (!event_queue.pop(event)) {
            continue;
        }

        std::string threadName = "Thread: " + std::to_string(event.thread_id);
        std::string mutexName = "Mutex: " + std::to_string(event.wait_id);

        if (event.kind == ompt_mutex_lock || event.kind == ompt_mutex_test_lock || event.kind == ompt_mutex_nest_lock || event.kind == ompt_mutex_test_nest_lock) {
            mutexName = "Lock: " + std::to_string(event.wait_id);
        } else if (event.kind == ompt_mutex_critical) {
            mutexName = "Critical: " + std::to_string(event.wait_id);
        }
        
        if (threads_to_iteration.find(threadName) == threads_to_iteration.end()) {
            threads_to_iteration[threadName] = 0;
        }

        graph.addNode(threadName);
        if (event.type == EventType::ACQUIRE || event.type == EventType::ACQUIRED || event.type == EventType::RELEASE) {
            graph.addNode(mutexName);
        }

        switch (event.type) {
            case EventType::BARRIER_BEGIN:
                switch (barrierState) {
                    case BarrierState::NOT_IN_USE:
                        for (const auto& pair : threads_to_iteration) {
                            graph.addEdge(barrierName, pair.first);
                        }
                        barrierState = BarrierState::IN_USE;

                        graph.removeEdge(barrierName, threadName);
                        graph.addEdge(threadName, barrierName);
                        break;
                    case BarrierState::IN_USE:
                        graph.removeEdge(barrierName, threadName);
                        graph.addEdge(threadName, barrierName);
                        break;
                }
                break;

            case EventType::BARRIER_END:
                switch (barrierState) {
                    case BarrierState::NOT_IN_USE:
                        threads_to_iteration[threadName]++;
                        break;
                    case BarrierState::IN_USE:
                        if (threads_to_iteration[threadName] == barrier_iteration) {
                            for (const auto& pair : threads_to_iteration) {
                                graph.removeEdge(barrierName, pair.first);
                                graph.removeEdge(pair.first, barrierName);
                            }
                            barrierState = NOT_IN_USE;
                            barrier_iteration++;
                        }
                        
                        threads_to_iteration[threadName]++;
                        break;
                }
                break;

            case EventType::ACQUIRE:
                switch (event.kind) {
                    case ompt_mutex_lock:
                    case ompt_mutex_critical:
                        graph.addEdge(threadName, mutexName);
                        break;
                    case ompt_mutex_nest_lock:
                        if (!graph.hasEdge(mutexName, threadName)) {
                            graph.addEdge(threadName, mutexName);
                        }
                        break;
                    case ompt_mutex_test_nest_lock:
                    case ompt_mutex_test_lock:
                    case ompt_mutex_atomic:
                    case ompt_mutex_ordered:
                        break;
                }
                break;

            case EventType::ACQUIRED:
                switch (event.kind) {
                    case ompt_mutex_lock:
                    case ompt_mutex_critical:
                    case ompt_mutex_nest_lock:
                    case ompt_mutex_test_nest_lock:
                    case ompt_mutex_test_lock:
                        graph.removeEdge(threadName, mutexName);
                        graph.addEdge(mutexName, threadName);
                        break;
                    case ompt_mutex_atomic:
                    case ompt_mutex_ordered:
                        break;
                }
                break;
                

            case EventType::RELEASE:
                switch (event.kind) {
                    case ompt_mutex_lock:
                    case ompt_mutex_critical:
                    case ompt_mutex_nest_lock:
                    case ompt_mutex_test_nest_lock:
                    case ompt_mutex_test_lock:
                        graph.removeEdge(mutexName, threadName);
                        break;
                    case ompt_mutex_atomic:
                    case ompt_mutex_ordered:
                        break;
                }
                break;
        }
        
        if (graph.hasCycle()) {
            std::cout << "Deadlock Detected!\n";
            graph.display(outFile);
            graph.displayCycle(outFile);
            break;
        }
        graph.display(outFile);
    }
    std::cout << "Deadlock Detector Thread Terminated\n";
}