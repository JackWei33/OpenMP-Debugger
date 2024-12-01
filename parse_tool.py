# parsing + event classes
from dataclasses import dataclass
from typing import Optional
import os

# graph classes
from dataclasses import dataclass, field
from typing import List, Union

# plotting
import networkx as nx
import plotly.graph_objects as go
@dataclass
class LogEvent:
    time: int
    event: str

@dataclass
class ThreadCreateEvent(LogEvent):
    thread_type: str

@dataclass
class ImplicitTaskEvent(LogEvent):
    endpoint: str
    actual_parallelism: int
    index: int
    flags: int
    parallel_id: int

@dataclass
class ParallelEvent(LogEvent):
    parallel_id: int
    requested_parallelism: Optional[int] = None
    flags: Optional[int] = None
    code_pointer: Optional[int] = None

@dataclass
class WorkEvent(LogEvent):
    parallel_id: int
    work_type: str
    endpoint: str
    count: int
    code_pointer: int

@dataclass
class MutexEvent(LogEvent):
    kind: str
    wait_id: int
    code_pointer: int

@dataclass
class SyncRegionEvent(LogEvent):
    parallel_id: int
    kind: str
    endpoint: str
    code_pointer: int

@dataclass
class ParallelEndEvent(LogEvent):
    parallel_id: int
    code_pointer: int

# Parsing Logic
def parse_log(lines: str):
    events = []
    current_event = {}
    for line in lines.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("--------------------------"):
            if current_event:
                event = create_event(current_event)
                if event:
                    events.append(event)
                current_event = {}
            continue
        key, value = map(str.strip, line.split(": ", 1))
        current_event[key.replace(" ", "_").lower()] = value
    return events

def create_event(event_dict):
    time = int(event_dict["time"].split()[0])
    event = event_dict["event"]
    if event == "Thread Create":
        return ThreadCreateEvent(time=time, event=event, thread_type=event_dict["thread_type"])
    if event == "Implicit Task":
        return ImplicitTaskEvent(
            time=time,
            event=event,
            endpoint=event_dict["endpoint"],
            actual_parallelism=int(event_dict["actual_parallelism"]),
            index=int(event_dict["index"]),
            flags=int(event_dict["flags"]),
            parallel_id=int(event_dict["parallel_id"]),
        )
    if event == "Parallel Begin":
        return ParallelEvent(
            time=time,
            event=event,
            parallel_id=int(event_dict["parallel_id"]),
            requested_parallelism=int(event_dict.get("requested_parallelism", 0)),
            flags=int(event_dict.get("flags", 0)),
            code_pointer=int(event_dict.get("code_pointer_return_address", 0)),
        )
    if event == "Work":
        return WorkEvent(
            time=time,
            event=event,
            parallel_id=int(event_dict["parallel_id"]),
            work_type=event_dict["work_type"],
            endpoint=event_dict["endpoint"],
            count=int(event_dict["count"]),
            code_pointer=int(event_dict["code_pointer_return_address"]),
        )
    if event in ["Mutex Acquire", "Mutex Acquired", "Mutex Released"]:
        return MutexEvent(
            time=time,
            event=event,
            kind=event_dict["kind"],
            wait_id=int(event_dict["wait_id"]),
            code_pointer=int(event_dict["code_pointer_return_address"]),
        )
    if event in ["Sync Region", "Sync Region Wait"]:
        return SyncRegionEvent(
            time=time,
            event=event,
            parallel_id=int(event_dict["parallel_id"]),
            kind=event_dict["kind"],
            endpoint=event_dict["endpoint"],
            code_pointer=int(event_dict["code_pointer_return_address"]),
        )
    if event == "Parallel End":
        return ParallelEndEvent(
            time=time,
            event=event,
            parallel_id=int(event_dict["parallel_id"]),
            code_pointer=int(event_dict["code_pointer_return_address"]),
        )
    return LogEvent(time=time, event=event)

def parse_logs_for_thread_events():
    """ Parses files in logs/ to return event objects for each log file (thread). """
    log_files = list(os.listdir("logs"))
    sorted_log_files = sorted(log_files) # sorted by file name (i.e., thread number)
    thread_num_to_events = {}
    for i, file in enumerate(sorted_log_files):
        log_data = open(f"logs/{file}").read()
        parsed_events = parse_log(log_data)
        thread_num_to_events[i] = parsed_events
    return thread_num_to_events

def get_parallel_ids_to_thread(thread_num_to_events: dict):
    parallel_ids_to_thread = {}
    for thread_num, events in thread_num_to_events.items():
        for event in events:
            if isinstance(event, ParallelEvent):
                parallel_ids_to_thread[event.parallel_id] = thread_num
    return parallel_ids_to_thread

def event_has_parallel_id(event: LogEvent, parallel_id: int):
    if isinstance(event, ParallelEvent):
        return event.parallel_id == parallel_id
    elif isinstance(event, ImplicitTaskEvent):
        return event.parallel_id == parallel_id
    elif isinstance(event, WorkEvent):
        return event.parallel_id == parallel_id
    elif isinstance(event, SyncRegionEvent):
        return event.parallel_id == parallel_id
    elif isinstance(event, ParallelEndEvent):
        return event.parallel_id == parallel_id
    return False

def get_parallel_id_to_graph(thread_num: int, parallel_id: int, thread_num_to_events: dict):
    filtered_thread_num_to_constrained_events = {}
    for thread_num, events in thread_num_to_events.items():
        start_index = -1
        for i, event in enumerate(events):
            if event_has_parallel_id(event, parallel_id):
                start_index = i
                break
        
        end_index = 0
        for i, event in enumerate(events[start_index:]):
            if event_has_parallel_id(event, parallel_id):
                end_index = i

        if start_index != -1:
            filtered_thread_num_to_constrained_events[thread_num] = events[start_index:end_index + 1]
    return filtered_thread_num_to_constrained_events
 
@dataclass
class GraphNode:
    time: int
    thread: int
    event: Union[LogEvent, None]
    children: List["GraphNode"] = field(default_factory=list)

    def add_child(self, child: "GraphNode"):
        """Adds a child node to the current node."""
        self.children.append(child)
  
def get_thread_events_to_events_graph(thread_num_to_events: dict):
    """ Converts individual thread events into a graph of each parallel region.
    
    1. Gets all parallel id's and their originating thread.
    2. For each parallel id:
        - For each thread that contains the parallel id, starting with original thread:
            - Create "party ballooned events" for each thread's list of events. Balloon sections are separated by:
                a. Barrier events
                b. First and last events of the thread
    """
    
    parallel_ids_to_thread = get_parallel_ids_to_thread(thread_num_to_events)
    
    parallel_id_to_graph = {}
    for parallel_id, thread_num in parallel_ids_to_thread.items():
        graph = get_parallel_id_to_graph(thread_num, parallel_id, thread_num_to_events)
        parallel_id_to_graph[parallel_id] = graph
    
    # TODO: Add logic to step through until first barrier is found and then step through other threads till that same barrier is found,
    # making parent -> child connections as we go and join/forking at the start, barriers, and end of the parallel region.
    
    raise NotImplementedError

def visualize_dag(root: GraphNode):
    """
    Visualizes a DAG of GraphNode objects using Plotly.
    Nodes are styled differently based on the event type.
    """
    # Step 1: Build a NetworkX graph
    G = nx.DiGraph()
    labels = {}
    node_colors = []

    def add_to_graph(node: GraphNode):
        """Recursively add nodes and edges to the graph."""
        G.add_node(
            id(node),
            label=f"{node.event.event if node.event else 'Root'}<br>Thread: {node.thread}<br>Time: {node.time}"
        )
        labels[id(node)] = G.nodes[id(node)]["label"]

        # Determine color based on event type
        if isinstance(node.event, ThreadCreateEvent):
            node_colors.append("blue")
        elif isinstance(node.event, ImplicitTaskEvent):
            node_colors.append("green")
        elif isinstance(node.event, ParallelEvent):
            node_colors.append("orange")
        elif isinstance(node.event, WorkEvent):
            node_colors.append("purple")
        elif isinstance(node.event, MutexEvent):
            node_colors.append("red")
        elif isinstance(node.event, SyncRegionEvent):
            node_colors.append("brown")
        elif isinstance(node.event, ParallelEndEvent):
            node_colors.append("gray")
        else:  # Root or unknown
            node_colors.append("black")

        for child in node.children:
            G.add_edge(id(node), id(child))
            add_to_graph(child)

    add_to_graph(root)

    # Step 2: Use a spring layout for positioning
    pos = nx.spring_layout(G, seed=42)  # Use spring layout for a DAG-like structure
    x_vals = [pos[n][0] for n in G.nodes]
    y_vals = [pos[n][1] for n in G.nodes]

    # Step 3: Extract edge positions
    edge_x = []
    edge_y = []
    for edge in G.edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    # Step 4: Create Plotly traces
    # Edges
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    # Nodes
    node_trace = go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers+text",
        text=[labels[node] for node in G.nodes],
        textposition="top center",
        hoverinfo="text",
        marker=dict(
            color=node_colors,
            size=10,
            line_width=2,
        ),
    )

    # Step 5: Combine traces into a figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="DAG Visualization of Events",
            titlefont_size=16,
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            plot_bgcolor="white",
        ),
    )

    fig.show()

if __name__ == "__main__":
    # !!! example dag !!!
    root = GraphNode(time=0, thread=0, event=None)
    child1 = GraphNode(time=100, thread=1, event=ThreadCreateEvent(100, "Thread Create", "ompt_thread_initial"))
    child2 = GraphNode(time=200, thread=1, event=ParallelEvent(200, "Parallel Begin", 281474976710657))
    child3 = GraphNode(time=300, thread=1, event=ParallelEvent(200, "Parallel Begin", 281474976710657))
    child4 = GraphNode(time=400, thread=1, event=ParallelEvent(200, "Parallel Begin", 281474976710657))
    child5 = GraphNode(time=500, thread=1, event=ParallelEvent(200, "Parallel Begin", 281474976710657))
    child1.add_child(child2)
    child2.add_child(child3)
    child2.add_child(child4)
    child3.add_child(child5)
    child4.add_child(child5)
    root.add_child(child1)
    visualize_dag(root)
    
    # Actual code we care about
    thread_num_to_events = parse_logs_for_thread_events()
    print(get_thread_events_to_events_graph(thread_num_to_events))
    # TODO: 
