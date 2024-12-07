#include <iostream>
#include <unordered_map>
#include <unordered_set>
#include <string>
#include <stdexcept>
#include "dl_detector.h"
#include <omp-tools.h>
#include <boost/lockfree/queue.hpp>

enum EventType {
    ACQUIRE,
    ACQUIRED,
    RELEASE
};

struct MutexEvent {
    EventType type;
    ompt_mutex_t kind;
    ompt_wait_id_t wait_id;
    uint64_t thread_id;
};

boost::lockfree::queue<MutexEvent> event_queue{1024};
std::mutex event_queue_mutex;
std::condition_variable event_queue_cv;
bool should_terminate = false;


void process_mutex_acquire(ompt_mutex_t kind, ompt_wait_id_t wait_id, uint64_t thread_id) {
    MutexEvent event{
        .type = EventType::ACQUIRE,
        .kind = kind,
        .wait_id = wait_id,
        .thread_id = thread_id
    };
    
    event_queue.push(event);
    event_queue_cv.notify_one(); 
}

void process_mutex_acquired(ompt_mutex_t kind, ompt_wait_id_t wait_id, uint64_t thread_id) {
    MutexEvent event{
        .type = EventType::ACQUIRED,
        .kind = kind,
        .wait_id = wait_id,
        .thread_id = thread_id
    };
    
    event_queue.push(event);
    event_queue_cv.notify_one(); 
}

void process_mutex_released(ompt_mutex_t kind, ompt_wait_id_t wait_id, uint64_t thread_id) {
    MutexEvent event{
        .type = EventType::RELEASE,
        .kind = kind,
        .wait_id = wait_id,
        .thread_id = thread_id
    };
    
    event_queue.push(event);
    event_queue_cv.notify_one(); 
}

class DirectedGraph {
private:
    std::unordered_map<std::string, std::unordered_set<std::string>> graph;

    bool dfsCycleDetection(const std::string& node, std::unordered_set<std::string>& visited, std::unordered_set<std::string>& recursionStack) const {
        if (recursionStack.find(node) != recursionStack.end()) {
            return true; // Cycle detected
        }

        if (visited.find(node) != visited.end()) {
            return false; // Already visited, no cycle found
        }

        visited.insert(node);
        recursionStack.insert(node);

        // Recurse for all neighbors
        if (graph.find(node) != graph.end()) {
            for (const auto& neighbor : graph.at(node)) {
                if (dfsCycleDetection(neighbor, visited, recursionStack)) {
                    return true;
                }
            }
        }

        recursionStack.erase(node);
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
    void display() const {
        for (const auto& pair : graph) {
            std::cout << pair.first << " -> { ";
            for (const auto& neighbor : pair.second) {
                std::cout << neighbor << " ";
            }
            std::cout << "}\n";
        }
    }

    bool hasCycle() const {
        std::unordered_set<std::string> visited;
        std::unordered_set<std::string> recursionStack;

        for (const auto& pair : graph) {
            if (dfsCycleDetection(pair.first, visited, recursionStack)) {
                return true;
            }
        }
        return false;
    }
};


void dl_detector_thread() {
    DirectedGraph graph;

    while (true) {
        MutexEvent event;

        {
            std::unique_lock<std::mutex> lock(event_queue_mutex);

            // Wait for an event or termination signal
            event_queue_cv.wait(lock, []{ return !event_queue.empty() || should_terminate; });

            // Exit if termination signal is received and the queue is empty
            if (should_terminate && event_queue.empty()) {
                break;
            }

            // Pop an event from the queue
            if (!event_queue.pop(event)) {
                continue;
            }
        }

        // Print event details
        // std::cout << "New Event Detected:\n";
        // std::cout << "  Thread ID: " << event.thread_id << "\n";
        // std::cout << "  Wait ID: " << event.wait_id << "\n";

        std::string threadName = "Thread: " + std::to_string(event.thread_id);
        std::string mutexName = "Mutex: " + std::to_string(event.wait_id);

        graph.addNode(threadName);
        graph.addNode(mutexName);
        
        switch (event.type) {
            case ACQUIRE:
                graph.addEdge(threadName, mutexName);
                break;

            case ACQUIRED:
                graph.removeEdge(threadName, mutexName);
                graph.addEdge(mutexName, threadName);
                break;

            case RELEASE:
                graph.removeEdge(mutexName, threadName);
                break;
        }
        if (graph.hasCycle()) {
            std::cout << "Deadlock Detected!\n";
            graph.display();
            break;
        }
    }

    std::cout << "Deadlock Detector Thread Terminated\n";
}