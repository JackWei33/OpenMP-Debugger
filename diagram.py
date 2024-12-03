# parsing + event classes
from dataclasses import dataclass, field
import datetime
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

def parse_logs_for_thread_events(folder_name: str):
    """ Parses text files in logs/ to return event objects for each log file (thread). """
    log_files = [file for file in os.listdir(folder_name) if file.endswith(".txt")]
    sorted_log_files = sorted(log_files)  # sorted by file name (i.e., thread number)
    thread_num_to_events = {}
    for i, file in enumerate(sorted_log_files):
        with open(f"{folder_name}/{file}", "r") as f:
            log_data = f.read()
        parsed_events = parse_log(log_data, i)  # Pass thread_number
        thread_num_to_events[i] = parsed_events
    return thread_num_to_events

def create_graph_for_thread_col_vs_time_viz(thread_num_to_events: dict):
    graph_nodes = []
    task_number_to_creation_node = {}
    task_number_to_schedule_node = {}
    task_number_to_complete_node = {}
    
    """ gather creation and schedule nodes """
    for _, events in thread_num_to_events.items():
        for event in events:
            node = GraphNode(event=event)
            graph_nodes.append(node)
            if isinstance(event, TaskCreateEvent):
                task_number_to_creation_node[event.task_number] = node
            elif isinstance(event, TaskScheduleEvent):
                if event.prior_task_status == "ompt_task_switch":
                    task_number_to_schedule_node[event.next_task_data] = node
                elif event.prior_task_status == "ompt_task_complete":
                    task_number_to_complete_node[event.prior_task_data] = node
    
    """ connect creation and schedule nodes and complete nodes """
    for task_number, creation_node in task_number_to_creation_node.items():
        schedule_node = task_number_to_schedule_node[task_number]
        creation_node.children.append(schedule_node)
        complete_node = task_number_to_complete_node[task_number]
        schedule_node.children.append(complete_node)
    
    return graph_nodes

def plot_thread_col_vs_time_viz(nodes: List['GraphNode'], file_path: str):
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
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="->", arrowsize=20)
    
    # Draw nodes with bounding boxes
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
    plt.savefig(f"graphs/{file_path}.png")
    plt.close()

def extract_parallel_id(event: LogEvent):
    """ try all events that potentially have parallel_id """
    if isinstance(event, ParallelEvent):
        return event.parallel_id
    if isinstance(event, ParallelEndEvent):
        return event.parallel_id
    if isinstance(event, ImplicitTaskEvent):
        return event.parallel_id
    if isinstance(event, WorkEvent):
        return event.parallel_id
    if isinstance(event, SyncRegionEvent):
        return event.parallel_id
    if isinstance(event, SyncRegionWaitEvent):
        return event.parallel_id
    return None

def create_graph_for_dependency_viz(thread_num_to_events: dict):
    """ get all parallel ids """
    parallel_ids = set()
    for _, events in thread_num_to_events.items():
        for event in events:
            if isinstance(event, ParallelEvent):
                parallel_ids.add(event.parallel_id)

    """ for each parallel id, for each thread, get the boundary events """
    parallel_id_to_thread_to_boundary_events = {}
    for parallel_id in parallel_ids: 
        parallel_id_to_thread_to_boundary_events[parallel_id] = {}
        for thread_number, events in thread_num_to_events.items():
            first_event = None
            last_event = None
            stack = []
            for event in events:
                if extract_parallel_id(event) == parallel_id and first_event is None:
                    first_event = event
                    stack.append(event)
                elif first_event is not None:
                    if isinstance(event, ImplicitTaskEvent):
                        if event.endpoint == "ompt_scope_begin":
                            stack.append(event)
                        else:
                            stack.pop()
                    if isinstance(event, ParallelEndEvent):
                        stack.pop()
                    if not stack:
                        last_event = event
                        break
            parallel_id_to_thread_to_boundary_events[parallel_id][thread_number] = (first_event, last_event)
    
    """ for each parallel id, for each thread, get all events that fit within the first and last event of the parallel id """
    parallel_id_to_graph_nodes = {}
    for parallel_id, thread_to_boundary_events in parallel_id_to_thread_to_boundary_events.items():
        graph_nodes = []
        task_number_to_creation_node = {}
        task_number_to_switch_node = {}
        task_number_to_complete_node = {}
        thread_to_barrier_nodes = {}
        begin_event = None
        end_event = None

        for _, events in thread_num_to_events.items():
            for event in events:
                if isinstance(event, ParallelEvent):
                    begin_event = GraphNode(event=event)
                    graph_nodes.append(begin_event)
                elif isinstance(event, ParallelEndEvent):
                    end_event = GraphNode(event=event)
                    graph_nodes.append(end_event)
                    
        for thread_number, events in thread_num_to_events.items():
            prev_nodes = [begin_event]
            for event in events:
                if thread_to_boundary_events[thread_number][0].time <= event.time <= thread_to_boundary_events[thread_number][1].time:
                    node = GraphNode(event=event)
                    if isinstance(event, SyncRegionWaitEvent) or isinstance(event, ParallelEvent) or isinstance(event, ParallelEndEvent):
                        continue
                    elif isinstance(event, TaskCreateEvent):
                        task_number_to_creation_node[event.task_number] = node
                        for prev_node in prev_nodes:
                            prev_node.children.append(node)
                    elif isinstance(event, TaskScheduleEvent):
                        if event.prior_task_status == "ompt_task_switch":
                            task_number_to_switch_node[event.next_task_data] = node
                        elif event.prior_task_status == "ompt_task_complete":
                            task_number_to_complete_node[event.prior_task_data] = node
                            prev_nodes.append(node)
                    else:
                        if isinstance(event, SyncRegionEvent):
                            if thread_number not in thread_to_barrier_nodes:
                                thread_to_barrier_nodes[thread_number] = []
                            thread_to_barrier_nodes[thread_number].append((node, prev_nodes))
                        for prev_node in prev_nodes:
                            prev_node.children.append(node)
                        prev_nodes = [node]
                    graph_nodes.append(node)
            for prev_node in prev_nodes:
                prev_node.children.append(end_event)
                
        for task_number, creation_node in task_number_to_creation_node.items():
            schedule_node = task_number_to_switch_node[task_number]
            creation_node.children.append(schedule_node)
            complete_node = task_number_to_complete_node[task_number]
            schedule_node.children.append(complete_node)
            
        # assert all threads have the same number of barrier nodes
        num_barrier_nodes = [len(barrier_nodes) for barrier_nodes in thread_to_barrier_nodes.values()]
        assert len(set(num_barrier_nodes)) == 1, "All threads must have the same number of barrier nodes"
        
        # barrier logic
        
                    
        parallel_id_to_graph_nodes[parallel_id] = graph_nodes
    
    return parallel_id_to_graph_nodes

def plot_dag(nodes: List['GraphNode'], file_path: str):
    import matplotlib.pyplot as plt
    import networkx as nx

    G = nx.DiGraph()

    # Add nodes with labels
    for node in nodes:
        label = f"{node.event.event} \n(Thread {node.event.thread_number})"
        G.add_node(node.event.unique_id, label=label)

    # Add edges based on the children relationships
    for node in nodes:
        for child in node.children:
            G.add_edge(node.event.unique_id, child.event.unique_id)

    # Define a top-down layout using Graphviz's 'dot' layout
    try:
        from networkx.drawing.nx_agraph import graphviz_layout
        pos = graphviz_layout(G, prog='dot')  # Requires PyGraphviz or pydot
    except ImportError:
        print("Graphviz layout not available. Falling back to spring_layout.")
        pos = nx.spring_layout(G)

    # Generate labels for nodes
    labels = nx.get_node_attributes(G, 'label')

    # Create plot
    plt.figure(figsize=(12, 8))

    # Draw edges with arrows
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='->', arrowsize=20)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=1500, node_color='lightblue')

    # Draw labels with bounding boxes
    nx.draw_networkx_labels(
        G, pos, labels, font_size=10, font_weight="bold",
        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3')
    )

    # Remove axes for a cleaner look
    plt.axis('off')

    # Adjust layout to prevent clipping
    plt.tight_layout()

    # Save the plot to the specified file
    plt.savefig(f"graphs/{file_path}.png")
    plt.close()

def plot_dag_with_time(nodes: List['GraphNode'], file_path: str):
    """
    Plots a Directed Acyclic Graph (DAG) with nodes arranged in their respective thread columns 
    and positioned vertically based on their timestamps. Thread labels are added without displaying 
    the x and y axes.

    Args:
        nodes (List[GraphNode]): A list of GraphNode objects to be plotted.
        file_path (str): The file path where the plot image will be saved.
    """
    import matplotlib.pyplot as plt
    import networkx as nx

    G = nx.DiGraph()

    # Add nodes with labels
    for node in nodes:
        label = f"{node.event.event} ({node.event.thread_number})"
        G.add_node(node.event.unique_id, label=label, time=node.event.time, thread=node.event.thread_number)

    # Add edges based on the children relationships
    for node in nodes:
        for child in node.children:
            G.add_edge(node.event.unique_id, child.event.unique_id)

    # Group nodes by thread and sort by time
    threads = {}
    for node in nodes:
        thread = node.event.thread_number
        if thread not in threads:
            threads[thread] = []
        threads[thread].append(node)

    for thread_nodes in threads.values():
        thread_nodes.sort(key=lambda n: n.event.time)

    min_time = min(node.event.time for node in nodes)
    max_time = max(node.event.time for node in nodes)

    # Assign positions to nodes
    pos = {}
    x_spacing = 2  # Space between threads
    y_scale = 1    # Scale for time positioning

    sorted_threads = sorted(threads.keys())
    thread_to_x = {thread: i * x_spacing for i, thread in enumerate(sorted_threads)}

    for thread, thread_nodes in threads.items():
        for node in thread_nodes:
            x = thread_to_x[thread]
            y = -y_scale * (node.event.time - min_time) / (max_time - min_time) if max_time != min_time else 0
            pos[node.event.unique_id] = (x, y)

    # Generate labels for nodes
    labels = {node: data['label'] for node, data in G.nodes(data=True)}

    # Create plot
    plt.figure(figsize=(12, 8))
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="->", arrowsize=20)
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold", 
                            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'))

    # Add thread labels at the top
    for thread, x in thread_to_x.items():
        plt.text(x, max(-y_scale * (node.event.time - min_time) / (max_time - min_time) for node in threads[thread]) + 0.5, 
                 f"Thread {thread}", ha="center", va="bottom", fontsize=12, fontweight="bold")

    # Remove axes
    plt.axis('off')

    plt.tight_layout()
    plt.savefig(f"graphs/{file_path}.png")
    plt.close()

def plot_dependency_viz(nodes: List['GraphNode'], folder_name: str):
    for parallel_id, graph_nodes in nodes.items():
        plot_thread_col_vs_time_viz(graph_nodes, f"{folder_name}/{parallel_id}_dag_col_vs_time")
        plot_dag(graph_nodes, f"{folder_name}/{parallel_id}_dag")
        plot_dag_with_time(graph_nodes, f"{folder_name}/{parallel_id}_dag_with_time")

def generate_graph_folder():
    now = datetime.datetime.now()
    folder_name = now.strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(f"graphs/{folder_name}", exist_ok=True)
    return folder_name

def main():
    folder_name = generate_graph_folder()
    log_folder_name = "logs/tasks from single"
    thread_num_to_events = parse_logs_for_thread_events(log_folder_name)
    for thread_number, events in thread_num_to_events.items():
        print(f"Thread {thread_number}:")
        for event in events:
            print(f"  {event} {event.unique_id}")
    graph_nodes = create_graph_for_thread_col_vs_time_viz(thread_num_to_events)
    plot_thread_col_vs_time_viz(graph_nodes, f"{folder_name}/thread_col_vs_time")
    
    graph_nodes = create_graph_for_dependency_viz(thread_num_to_events)
    plot_dependency_viz(graph_nodes, folder_name)

if __name__ == "__main__":
    main()