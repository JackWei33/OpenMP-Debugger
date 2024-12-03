# parsing + event classes
from dataclasses import dataclass, field
from typing import Optional, List
import os
import uuid
import matplotlib.pyplot as plt
import networkx as nx

@dataclass
class LogEvent:
    time: int
    event: str
    thread_number: int

    def __post_init__(self):
        self.unique_id = str(uuid.uuid4())

@dataclass
class ThreadCreateEvent(LogEvent):
    thread_type: str

@dataclass
class ImplicitTaskEvent(LogEvent):
    task_number: int
    endpoint: str
    parallel_id: Optional[int]

@dataclass
class ParallelEvent(LogEvent):
    parallel_id: int
    requested_parallelism: Optional[int] = None

@dataclass
class WorkEvent(LogEvent):
    parallel_id: Optional[int]
    work_type: str
    endpoint: str

@dataclass
class MutexEvent(LogEvent):
    kind: str
    wait_id: int

@dataclass
class SyncRegionEvent(LogEvent):
    parallel_id: Optional[int]
    kind: str
    endpoint: str

@dataclass
class SyncRegionWaitEvent(LogEvent):
    parallel_id: Optional[int]
    kind: str
    endpoint: str

@dataclass
class TaskCreateEvent(LogEvent):
    task_number: int
    parent_task_number: int

@dataclass
class TaskScheduleEvent(LogEvent):
    prior_task_data: int
    prior_task_status: str
    next_task_data: Optional[int]

@dataclass
class ParallelEndEvent(LogEvent):
    parallel_id: int

@dataclass
class GraphNode:
    event: LogEvent
    children: List['GraphNode'] = field(default_factory=list)

# Parsing Logic
def parse_log(lines: str, thread_number: int):
    events = []
    current_event = {}
    for line in lines.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("--------------------------"):
            if current_event:
                
                event = create_event(current_event, thread_number)
                if event:
                    events.append(event)
                current_event = {}
            continue
        key, value = map(str.strip, line.split(": ", 1))
        current_event[key.replace(" ", "_").lower()] = value
    return events

def create_event(event_dict, thread_number: int):
    time = int(event_dict["time"].split()[0])
    event = event_dict["event"]
    base_params = {
        "time": time,
        "event": event,
        "thread_number": thread_number
    }
    if event == "Thread Create":
        return ThreadCreateEvent(
            **base_params,
            thread_type=event_dict["thread_type"]
        )
    if event == "Implicit Task":
        return ImplicitTaskEvent(
            **base_params,
            task_number=int(event_dict["task_number"]),
            endpoint=event_dict["endpoint"],
            parallel_id=int(event_dict["parallel_id"]) if event_dict.get("parallel_id", "N/A") != "N/A" else None
        )
    if event in ["Parallel Begin", "Parallel Start"]:
        return ParallelEvent(
            **base_params,
            parallel_id=int(event_dict["parallel_id"]),
            requested_parallelism=int(event_dict.get("requested_parallelism", 0)),
        )
    if event == "Parallel End":
        return ParallelEndEvent(
            **base_params,
            parallel_id=int(event_dict["parallel_id"]),
        )
    if event == "Work":
        return WorkEvent(
            **base_params,
            parallel_id=int(event_dict["parallel_id"]) if event_dict.get("parallel_id", "N/A") != "N/A" else None,
            work_type=event_dict["work_type"],
            endpoint=event_dict["endpoint"],
        )
    if event in ["Mutex Acquire", "Mutex Acquired", "Mutex Released"]:
        return MutexEvent(
            **base_params,
            kind=event_dict["kind"],
            wait_id=int(event_dict["wait_id"]),
        )
    if event in ["Sync Region", "Sync Region Wait"]:
        if event == "Sync Region Wait":
            return SyncRegionWaitEvent(
                **base_params,
                parallel_id=int(event_dict["parallel_id"]) if event_dict.get("parallel_id", "N/A") != "N/A" else None,
                kind=event_dict["kind"],
                endpoint=event_dict["endpoint"],
            )
        return SyncRegionEvent(
            **base_params,
            parallel_id=int(event_dict["parallel_id"]) if event_dict.get("parallel_id", "N/A") != "N/A" else None,
            kind=event_dict["kind"],
            endpoint=event_dict["endpoint"],
        )
    if event == "Task Create":
        return TaskCreateEvent(
            **base_params,
            task_number=int(event_dict["task_number"]),
            parent_task_number=int(event_dict["parent_task_number"]),
        )
    if event == "Task Schedule":
        return TaskScheduleEvent(
            **base_params,
            prior_task_data=int(event_dict["prior_task_data"]),
            prior_task_status=event_dict["prior_task_status"],
            next_task_data=int(event_dict["next_task_data"]) if event_dict.get("next_task_data", "N/A") != "N/A" else None
        )
    return LogEvent(time=time, event=event, thread_number=thread_number)

def parse_logs_for_thread_events():
    """ Parses text files in logs/ to return event objects for each log file (thread). """
    log_files = [file for file in os.listdir("logs") if file.endswith(".txt")]
    sorted_log_files = sorted(log_files)  # sorted by file name (i.e., thread number)
    thread_num_to_events = {}
    for i, file in enumerate(sorted_log_files):
        with open(f"logs/{file}", "r") as f:
            log_data = f.read()
        parsed_events = parse_log(log_data, i)  # Pass thread_number
        thread_num_to_events[i] = parsed_events
    return thread_num_to_events

def create_graph_from_events(thread_num_to_events: dict):
    graph_nodes = []
    for thread_number, events in thread_num_to_events.items():
        for event in events:
            graph_nodes.append(GraphNode(event=event))
    return graph_nodes

def plot_graph(nodes: List['GraphNode']):
    """
    Plots a Directed Acyclic Graph (DAG) using unique IDs as node identifiers.
    Each node is labeled with "{event} ({thread_number})" and positioned based on time.

    Args:
        nodes (List[GraphNode]): A list of GraphNode objects to be plotted.
    """
    G = nx.DiGraph()

    # Add nodes with labels
    for node in nodes:
        label = f"{node.event.event} ({node.event.thread_number})"
        G.add_node(node.event.unique_id, label=label, time=node.event.time)

    # Add edges based on the children relationships
    for node in nodes:
        for child in node.children:
            G.add_edge(node.event.unique_id, child.event.unique_id)

    # Organize nodes by thread and sort by time
    threads = {}
    for node in nodes:
        thread = node.event.thread_number
        if thread not in threads:
            threads[thread] = []
        threads[thread].append(node)

    for thread_nodes in threads.values():
        thread_nodes.sort(key=lambda n: n.event.time)

    # Assign positions to nodes
    pos = {}
    x_spacing = 2  # Space between threads
    y_scale = 1    # Scale for time positioning
    for i, (thread, thread_nodes) in enumerate(sorted(threads.items())):
        for node in thread_nodes:
            # Position: x based on thread number, y based on time
            pos[node.event.unique_id] = (i * x_spacing, -node.event.time * y_scale)

    # Generate labels for nodes
    labels = {node: data['label'] for node, data in G.nodes(data=True)}

    # Create plot
    plt.figure(figsize=(12, 8))
    # nx.draw_networkx_nodes(G, pos, node_size=700, node_color="lightblue")
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="->", arrowsize=20)
    # Draw nodes with bounding boxes
    # nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold")
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold", bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'))

    # Add thread labels on the x-axis
    plt.xticks(
        [i * x_spacing for i in range(len(threads))],
        [f"Thread {thread}" for thread in sorted(threads.keys())],
        fontsize=12
    )
    plt.yticks(
        sorted({-node.event.time for node in nodes}),
        [str(time) for time in sorted({node.event.time for node in nodes})],
        fontsize=12
    )

    # Label axes
    plt.xlabel("Threads", fontsize=14)   
    plt.ylabel("Time", fontsize=14)

    # Scale axes to avoid clipping
    plt.xlim(-1 * x_spacing, len(threads) * x_spacing)
    plt.ylim(-max([node.event.time for node in nodes]) * y_scale * 1.1, 1)
    
    # Add a number for each thread
    for i, thread in enumerate(sorted(threads.keys())):
        plt.text(i * x_spacing, -1, str(thread), ha="center", va="bottom", fontsize=12)
        
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def main():
    thread_num_to_events = parse_logs_for_thread_events()
    for thread_number, events in thread_num_to_events.items():
        print(f"Thread {thread_number}:")
        for event in events:
            print(f"  {event} {event.unique_id}")
    graph_nodes = create_graph_from_events(thread_num_to_events)
    plot_graph(graph_nodes)

if __name__ == "__main__":
    main()