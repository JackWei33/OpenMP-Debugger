# parsing + event classes
from dataclasses import dataclass, field
import datetime
from typing import Optional, List, Dict, Set, Tuple
import os
import uuid
import matplotlib.pyplot as plt
import networkx as nx
from enum import Enum, auto
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
class CustomEventStart(LogEvent):
    name: str

@dataclass
class CustomEventEnd(LogEvent):
    name: str
@dataclass
class ImplicitTaskEvent(LogEvent):
    task_number: int
    endpoint: str
    parallel_id: Optional[int]

    def is_start(self):
        return self.endpoint == "ompt_scope_begin"

@dataclass
class ParallelEvent(LogEvent):
    parallel_id: int
    requested_parallelism: Optional[int] = None

@dataclass
class WorkEvent(LogEvent):
    parallel_id: Optional[int]
    work_type: str
    endpoint: str

    def is_start(self):
        return self.endpoint == "ompt_scope_begin"

@dataclass
class MutexAcquireEvent(LogEvent):
    kind: str
    wait_id: int

@dataclass
class MutexAcquiredEvent(LogEvent):
    kind: str
    wait_id: int

@dataclass
class MutexReleaseEvent(LogEvent):
    kind: str
    wait_id: int

@dataclass
class SyncRegionEvent(LogEvent):
    parallel_id: Optional[int]
    kind: str
    endpoint: str

    def is_start(self):
        return self.endpoint == "ompt_scope_begin"

@dataclass
class SyncRegionWaitEvent(LogEvent):
    parallel_id: Optional[int]
    kind: str
    endpoint: str

    def is_start(self):
        return self.endpoint == "ompt_scope_begin"

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

class EdgeType(Enum):
    TEMPORAL = auto()
    NESTING = auto()
    TASK = auto()
    MUTEX = auto()

@dataclass
class GraphNode:
    event: LogEvent
    children: List[Tuple[EdgeType, 'GraphNode']] = field(default_factory=list)
    parents: List[Tuple[EdgeType, 'GraphNode']] = field(default_factory=list)
    
    def add_child(self, edge_type: EdgeType, child: 'GraphNode'):
        self.children.append((edge_type, child))
        child.parents.append((edge_type, self))

# Same as diagram.py
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

# Same as diagram.py
def extract_parallel_id(event: LogEvent):
    """ Try all events that potentially have parallel_id """
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

# Same as diagram.py
def parse_log(lines: str, thread_number: int):
    """ Parse a log file into a list of events. """
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

# Slightly modified
def create_event(event_dict, thread_number: int):
    """ Create an event object from a dictionary extracted from a log file. """
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
    if event == "Parallel Begin":
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
    if event == "Mutex Acquire":
        return MutexAcquireEvent(
            **base_params,
            kind=event_dict["kind"],
            wait_id=int(event_dict["wait_id"]),
        )
    if event == "Mutex Acquired":
        return MutexAcquiredEvent(
            **base_params,
            kind=event_dict["kind"],
            wait_id=int(event_dict["wait_id"]),
        )
    if event == "Mutex Released":
        return MutexReleaseEvent(
            **base_params,
            kind=event_dict["kind"],
            wait_id=int(event_dict["wait_id"]),
        )
    if event == "Sync Region Wait":
        return SyncRegionWaitEvent(
            **base_params,
            parallel_id=int(event_dict["parallel_id"]) if event_dict.get("parallel_id", "N/A") != "N/A" else None,
            kind=event_dict["kind"],
            endpoint=event_dict["endpoint"],
        )
    if event == "Sync Region":
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
    if event == "Custom Callback Begin":
        return CustomEventStart(
            **base_params,
            name=event_dict["name"]
        )
    if event == "Custom Callback End":
        return CustomEventEnd(
            **base_params,
            name=event_dict["name"]
        )
    return LogEvent(time=time, event=event, thread_number=thread_number)

def generate_dag(thread_num_to_events: Dict[int, List[LogEvent]]):
    """
    Generates a DAG from the given thread events, creating temporal and dependency edges.

    Assumptions:
    1. Parallel regions can be disjoint
    2. Logs are well-formed
        - All event "begin" and "end" (e.g., ompt_scope_begin, ompt_scope_end) events abide by parenthetical rules
        - All task create events have a corresponding task switch and complete event (and only one of each)
        - All mutex acquire events have a corresponding mutex acquired and released event (and only one of each)
            - Moreover, nothing else happens between the mutex acquire and acquired events
        - All sync region begin and end events have corresponding sync region wait and end events "within them"
            - Moreover, nothing else happens between the sync region begin/wait begin and end/wait end events
            
            
    Output graph:
    1. Nodes:
        - Every event in the logs gets a node
        - Shapes:
            - parallelogram: Implicit task
            - Msquare: Parallel region
            - invhouse: Sync region begin / Sync region wait begin
            - house: Sync region end / Sync region wait end
            - doublecircle: Thread create
            - rarrow: Task create
            - larrow: Task schedule switch
            - signature: Task complete
            - invhouse: Mutex acquire
            - rectangle: Mutex acquired
            - house: Mutex released
            - oval: Work
            
    2. Edges:
        a. Temporal edges:
            - Every chronologically subsequent event gets a "temporal" edge from the previous event
        b. Dependency edges:
            - Every task create event gets a dependency edge to its corresponding task schedule switch event
                - Can be matched afterwards using task number
            - Every task schedule switch event gets a dependency edge to its corresponding task complete event
                - Can be matched afterwards using task number
            - Every first event (typically an implicit task begin) of a parallel region (except for parallel begin) gets a dependency edge to its corresponding parallel begin event
            - Every last event (typically an implicit task end) of a parallel region (except for parallel end) gets a dependency edge to its corresponding parallel end event
            - (TBD) Every mutex acquire event gets a dependency edge to its corresponding mutex acquired event
            - (TBD) Every sync region begin event gets a dependency edge to its corresponding sync region wait begin event
            - (TBD) Every sync region wait end event gets a dependency edge to its corresponding sync region end event
            
    Algorithm:
    1. Transform all events into nodes, and create temporal edges
    2. Gather all parallel ids from nodes
    3. For each parallel id:
        - For each thread:
            - Get boundary events (using stack algorithm)
            - Perform dependency edge creation
                - For tasks
                - For parallel begin / end
                - (TBD) ...
    """
    graph_nodes: List[GraphNode] = []
    event_nodes: Dict[str, GraphNode] = {}  # Map from event unique_id to GraphNode
    task_number_to_create_node: Dict[int, GraphNode] = {}
    task_number_to_schedule_node: Dict[int, GraphNode] = {}
    task_number_to_complete_node: Dict[int, GraphNode] = {}
    parallel_id_to_begin_node: Dict[int, GraphNode] = {}
    parallel_id_to_end_node: Dict[int, GraphNode] = {}
    mutex_wait_id_to_nodes: Dict[int, Dict[str, GraphNode]] = {}

    # Find minimum time
    min_time = min(event.time for events in thread_num_to_events.values() for event in events)

    # Step 1: Transform all events into nodes and create temporal edges
    for thread_number, events in thread_num_to_events.items():
        events.sort(key=lambda e: e.time)
        prev_node: Optional[GraphNode] = None
        for event in events:
            event.time = event.time - min_time
            if isinstance(event, SyncRegionWaitEvent):
                # skip sync region wait events
                continue
            if isinstance(event, SyncRegionEvent) and ('implicit' in event.kind or 'taskgroup' in event.kind):
                continue
            node = GraphNode(event=event)
            event_nodes[event.unique_id] = node
            graph_nodes.append(node)
            if prev_node:
                # Create temporal edge
                prev_node.add_child(EdgeType.TEMPORAL, node)
            prev_node = node

            # Collect mappings for dependency edges
            if isinstance(event, TaskCreateEvent):
                task_number_to_create_node[event.task_number] = node
            elif isinstance(event, TaskScheduleEvent):
                if event.prior_task_status == "ompt_task_switch":
                    task_number_to_schedule_node[event.next_task_data] = node
                elif event.prior_task_status == "ompt_task_complete":
                    task_number_to_complete_node[event.prior_task_data] = node
            elif isinstance(event, ParallelEvent):
                parallel_id_to_begin_node[event.parallel_id] = node
            elif isinstance(event, ParallelEndEvent):
                parallel_id_to_end_node[event.parallel_id] = node
            elif isinstance(event, MutexAcquireEvent):
                mutex_wait_id_to_nodes.setdefault((event.wait_id, event.thread_number), {})['acquire'] = node
            elif isinstance(event, MutexAcquiredEvent):
                mutex_wait_id_to_nodes.setdefault((event.wait_id, event.thread_number), {})['acquired'] = node
            elif isinstance(event, MutexReleaseEvent):
                mutex_wait_id_to_nodes.setdefault((event.wait_id, event.thread_number), {})['release'] = node

    # Step 2: Create dependency edges
    # a. Task dependencies
    for task_number in task_number_to_create_node:
        create_node = task_number_to_create_node.get(task_number)
        schedule_node = task_number_to_schedule_node.get(task_number)
        complete_node = task_number_to_complete_node.get(task_number)
        assert create_node and schedule_node and complete_node, "Task create, schedule, and complete nodes must all be present"
        create_node.add_child(EdgeType.TASK, schedule_node)
        schedule_node.add_child(EdgeType.TASK, complete_node)
    # b. Parallel region dependencies
    parallel_ids = set(extract_parallel_id(node.event) for node in graph_nodes if extract_parallel_id(node.event) is not None)
    for parallel_id in parallel_ids:
        parallel_begin_node: Optional[GraphNode] = parallel_id_to_begin_node.get(parallel_id)
        parallel_end_node: Optional[GraphNode] = parallel_id_to_end_node.get(parallel_id)
        if not parallel_begin_node and not parallel_end_node:
            continue
        if not parallel_begin_node or not parallel_end_node:
            raise ValueError(f"Parallel region {parallel_id} has no begin or end node")
        # For each thread, find first and last events within the parallel region
        for thread_number, events in thread_num_to_events.items():
            events_in_parallel = []
            in_parallel = False
            first_event = last_event = None
            for event in events:
                if in_parallel:
                    # If we are in a parallel region, we can start the stack algorithm
                    if isinstance(event, ImplicitTaskEvent):
                        if event.endpoint == "ompt_scope_end":
                            events_in_parallel.pop()
                        else:
                            events_in_parallel.append(event)
                        if not events_in_parallel:
                            last_event = event
                            break
                else:
                    # If we are not in a parallel region, we can start the stack algorithm
                    event_parallel_id = extract_parallel_id(event)
                    if event_parallel_id == parallel_id:
                        if isinstance(event, ParallelEvent) or (isinstance(event, ImplicitTaskEvent) and event.endpoint == 'ompt_scope_end'):
                            continue
                        else:
                            in_parallel = True
                            first_event = event
                            assert isinstance(first_event, ImplicitTaskEvent), "First event of parallel region must be an implicit task begin"
                            events_in_parallel.append(event)
            assert (first_event and last_event) or (not first_event and not last_event), f"Either both first and last event must be present or neither for parallel region {parallel_id} in thread {thread_number}"
            if first_event and last_event:
                # Link first event to parallel begin
                first_node = event_nodes[first_event.unique_id]
                parallel_begin_node.add_child(EdgeType.NESTING, first_node)
                last_node = event_nodes[last_event.unique_id]
                last_node.add_child(EdgeType.NESTING, parallel_end_node)
    # c. Mutex dependencies
    for (wait_id, thread_number), nodes in mutex_wait_id_to_nodes.items():
        acquire_node = nodes.get('acquire')
        acquired_node = nodes.get('acquired')
        release_node = nodes.get('release')
        assert acquire_node and acquired_node and release_node, "Mutex acquire, acquired, and release nodes must all be present"
        acquire_node.add_child(EdgeType.MUTEX, acquired_node)
        acquired_node.add_child(EdgeType.MUTEX, release_node)

    return graph_nodes

def get_shape(node: GraphNode):
    shape = None
    if isinstance(node.event, ImplicitTaskEvent):
        shape = 'parallelogram'
    elif isinstance(node.event, ParallelEvent) or isinstance(node.event, ParallelEndEvent):
        shape = 'Mdiamond'  # Msquare is not a standard shape in Graphviz
    elif isinstance(node.event, SyncRegionEvent) and node.event.endpoint == 'ompt_scope_begin':
        shape = 'invhouse'
    elif isinstance(node.event, SyncRegionEvent) and node.event.endpoint == 'ompt_scope_end':
        shape = 'house'
    elif isinstance(node.event, SyncRegionWaitEvent) and node.event.endpoint == 'ompt_scope_begin':
        shape = 'invhouse'
    elif isinstance(node.event, SyncRegionWaitEvent) and node.event.endpoint == 'ompt_scope_end':
        shape = 'house'
    elif isinstance(node.event, ThreadCreateEvent):
        shape = 'doublecircle'
    elif isinstance(node.event, TaskCreateEvent):
        shape = 'diamond'
    elif isinstance(node.event, TaskScheduleEvent) and node.event.prior_task_status == 'ompt_task_switch':
        shape = 'invtriangle'
    elif isinstance(node.event, TaskScheduleEvent) and node.event.prior_task_status == 'ompt_task_complete':
        shape = 'triangle'
    elif isinstance(node.event, MutexAcquireEvent):
        shape = 'rectangle'
    elif isinstance(node.event, MutexAcquiredEvent):
        shape = 'invhouse'
    elif isinstance(node.event, MutexReleaseEvent):
        shape = 'house'
    elif isinstance(node.event, WorkEvent) and node.event.endpoint == 'ompt_scope_begin':
        shape = 'Mcircle'
    elif isinstance(node.event, WorkEvent) and node.event.endpoint == 'ompt_scope_end':
        shape = 'circle'
    elif isinstance(node.event, CustomEventStart):
        shape = 'Mcircle'
    elif isinstance(node.event, CustomEventEnd):
        shape = 'circle'
    else:
        shape = 'box'
    return shape

def get_label(node: GraphNode):
    name = node.event.event
    if isinstance(node.event, ImplicitTaskEvent) or isinstance(node.event, SyncRegionEvent) or isinstance(node.event, SyncRegionWaitEvent) or isinstance(node.event, WorkEvent):
        if node.event.endpoint == 'ompt_scope_begin':
            name += ' Begin'
        elif node.event.endpoint == 'ompt_scope_end':
            name += ' End'
        if isinstance(node.event, WorkEvent):
            name += f'\n({node.event.work_type})'
    elif isinstance(node.event, TaskCreateEvent):
        name += f' ({node.event.task_number})'
    elif isinstance(node.event, TaskScheduleEvent):
        if node.event.prior_task_status == 'ompt_task_switch':
            name += f' ({node.event.next_task_data})'
        elif node.event.prior_task_status == 'ompt_task_complete':
            name += f' ({node.event.prior_task_data})'
    elif isinstance(node.event, SyncRegionEvent) or isinstance(node.event, SyncRegionWaitEvent):
        if 'implicit' in node.event.kind or 'taskgroup' in node.event.kind:
            name += f'\n(implicit)'
        else:
            name += f'\n(explicit)'
    # elif isinstance(node.event, MutexAcquireEvent) or isinstance(node.event, MutexAcquiredEvent) or isinstance(node.event, MutexReleaseEvent):
        # name += f' ({node.event.wait_id})'
    return f"{name}\nThread: {node.event.thread_number}\nTime: {node.event.time}"

def get_color(node: GraphNode):
    if isinstance(node.event, MutexAcquireEvent) or isinstance(node.event, MutexAcquiredEvent) or isinstance(node.event, MutexReleaseEvent):
        return 'red'
    elif isinstance(node.event, SyncRegionEvent) or isinstance(node.event, SyncRegionWaitEvent):
        if 'implicit' in node.event.kind or 'taskgroup' in node.event.kind:
            return 'gray'
        else:
            return 'orange'
    elif isinstance(node.event, TaskCreateEvent) or isinstance(node.event, TaskScheduleEvent):
        return 'green'
    elif isinstance(node.event, WorkEvent):
        if node.event.work_type == 'ompt_work_single_other':
            return 'gray'
        else:
            return 'blue'
    elif isinstance(node.event, ThreadCreateEvent):
        return 'purple'
    elif isinstance(node.event, ImplicitTaskEvent):
        return 'pink'
    elif isinstance(node.event, ParallelEvent) or isinstance(node.event, ParallelEndEvent):
        return 'pink'
    elif isinstance(node.event, CustomEventStart) or isinstance(node.event, CustomEventEnd):
        return 'yellow'
    else:
        return 'black'

def create_graphviz_graph(graph_nodes: List[GraphNode], output_file: str, style: str = 'thread_groups'):
    """
    Create a Graphviz graph from the given graph nodes and save it to a file.

    Args:
        graph_nodes (List[GraphNode]): The list of graph nodes generated by generate_dag.
        output_file (str): The path to the output file where the graph will be saved.
    """
    from graphviz import Digraph

    dot = Digraph(comment='DAG from Events')

    def get_edge_attributes(edge_type: EdgeType):
        if edge_type == EdgeType.TEMPORAL:
            style = 'solid'
            penwidth = '1.0'
            color = 'black'
        elif edge_type == EdgeType.NESTING:
            style = 'solid'
            penwidth = '2.0'
            color = 'pink'
        elif edge_type == EdgeType.MUTEX:
            style = 'solid'
            penwidth = '2.0'
            color = 'red'
        elif edge_type == EdgeType.TASK:
            style = 'solid'
            penwidth = '2.0'
            color = 'green'
        return style, penwidth, color
    
    if style == 'thread_groups':
        # Group nodes by thread number
        thread_groups = {}
        for node in graph_nodes:
            thread_number = node.event.thread_number
            if thread_number not in thread_groups:
                thread_groups[thread_number] = []
            thread_groups[thread_number].append(node)


        def add_edges_to_object(c: Digraph, node: GraphNode, within_thread: bool):
            for edge_type, child_node in node.children:
                if within_thread:
                    if child_node.event.thread_number != node.event.thread_number:
                        continue
                else:
                    if child_node.event.thread_number == node.event.thread_number:
                        continue
                style, penwidth, color = get_edge_attributes(edge_type)
                c.edge(node.event.unique_id, child_node.event.unique_id, style=style, color=color, penwidth=penwidth)

        # Add nodes and edges per thread within clusters
        for thread_number, nodes in thread_groups.items():
            with dot.subgraph(name=f'cluster_thread_{thread_number}') as c:
                c.attr(label=f'Thread {thread_number}', style='dashed')
                # Add nodes
                for node in nodes:
                    label = get_label(node)
                    shape = get_shape(node)
                    color = get_color(node)
                    c.node(node.event.unique_id, label=label, shape=shape, color=color, style='filled')
                    add_edges_to_object(c, node, within_thread=True)

        # Add edges between threads
        for node in graph_nodes:
            add_edges_to_object(dot, node, within_thread=False)
            
    elif style == 'no_thread_groups':
        def add_edges_to_object(c: Digraph, node: GraphNode):
            for edge_type, child_node in node.children:
                style, penwidth, color = get_edge_attributes(edge_type)
                c.edge(node.event.unique_id, child_node.event.unique_id, style=style, color=color, penwidth=penwidth)
                
        for node in graph_nodes:
            label = get_label(node)
            shape = get_shape(node)
            color = get_color(node)
            dot.node(node.event.unique_id, label=label, shape=shape, color=color, style='filled')
            add_edges_to_object(dot, node)

    # Save and render the graph
    dot.render(output_file, view=False, format='png')

def create_graph_for_thread_col_vs_time_viz(thread_num_to_events: Dict[int, List[LogEvent]]):
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
    """ get all disjoint parallel ids """
    # Only get parallel ids that are disjoint. Assume that all disjoint parallel regions are started by thread 0.
    parallel_ids = set()
    stack = []
    for thread, events in thread_num_to_events.items():
        if thread != 0:
            continue
        for event in events:
            if isinstance(event, ParallelEvent):
                if not stack:
                    parallel_ids.add(event.parallel_id)
                stack.append(event)
            elif isinstance(event, ParallelEndEvent):
                stack.pop()

    """ for each parallel id, for each thread, get the boundary events """
    parallel_id_to_thread_to_boundary_events = {}
    for parallel_id in parallel_ids: 
        parallel_id_to_thread_to_boundary_events[parallel_id] = {}
        for thread_number, events in thread_num_to_events.items():
            first_event = None
            last_event = None
            stack = []
            for event in events:
                if first_event is None and extract_parallel_id(event) == parallel_id and isinstance(event, ImplicitTaskEvent) and event.endpoint == "ompt_scope_begin":
                    first_event = event
                    stack.append(event)
                elif first_event is not None:
                    if isinstance(event, ImplicitTaskEvent):
                        if event.endpoint == "ompt_scope_begin":
                            stack.append(event)
                        else:
                            stack.pop()
                    if not stack:
                        last_event = event
                        break
            if (first_event is not None) and (last_event is not None):
                parallel_id_to_thread_to_boundary_events[parallel_id][thread_number] = (first_event, last_event)
    
    """ for each parallel id, for each thread, get all events that fit within the first and last event of the parallel id """
    parallel_id_to_graph_nodes = {}
    for parallel_id, thread_to_boundary_events in parallel_id_to_thread_to_boundary_events.items():
        graph_nodes = []
        task_number_to_creation_node = {}
        task_number_to_switch_node = {}
        task_number_to_complete_node = {}
        # thread_to_barrier_nodes = {}
        begin_event = None
        end_event = None

        for _, events in thread_num_to_events.items():
            for event in events:
                if isinstance(event, ParallelEvent) and extract_parallel_id(event) == parallel_id:
                    begin_event = GraphNode(event=event)
                    graph_nodes.append(begin_event)
                elif isinstance(event, ParallelEndEvent) and extract_parallel_id(event) == parallel_id:
                    end_event = GraphNode(event=event)
                    graph_nodes.append(end_event)
                    
        for thread_number, events in thread_num_to_events.items():
            if thread_number not in thread_to_boundary_events:
                continue
            prev_nodes = [begin_event]
            for event in events:
                # event.time
                # thread_to_boundary_events[thread_number][0].time
                # if (thread_to_boundary_events[thread_number][1] == None):
                #     print(f"thread: {thread_number} first_event: {thread_to_boundary_events[thread_number][0]} last_event: {thread_to_boundary_events[thread_number][1]}")
                if not (thread_to_boundary_events[thread_number][0].time <= event.time <= thread_to_boundary_events[thread_number][1].time):
                    continue

                node = GraphNode(event=event)
                if isinstance(event, SyncRegionWaitEvent) or (isinstance(event, ParallelEvent) and extract_parallel_id(event) == parallel_id) or (isinstance(event, ParallelEndEvent) and extract_parallel_id(event) == parallel_id): # 
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
                    # if isinstance(event, SyncRegionEvent):
                    #     if thread_number not in thread_to_barrier_nodes:
                    #         thread_to_barrier_nodes[thread_number] = []
                    #     thread_to_barrier_nodes[thread_number].append((node, prev_nodes))
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
        # num_barrier_nodes = [len(barrier_nodes) for barrier_nodes in thread_to_barrier_nodes.values()]
        # assert len(set(num_barrier_nodes)) == 1, "All threads must have the same number of barrier nodes"
        
        # barrier logic
          
        parallel_id_to_graph_nodes[parallel_id] = graph_nodes
    
    return parallel_id_to_graph_nodes

def get_time_spent_by_section(thread_num_to_events: dict):
    """ 
    Calculates the time spent by each thread in different sections within each parallel section.

    Returns a dictionary in the following format:
    {
        'Parallel Section 1': {
            'Thread 0': {'Working': 5, 'Critical': 3, 'Mutex': 2},
            'Thread 1': {'Working': 4, 'Critical': 6, 'Mutex': 1},
            ...
        },
        'Parallel Section 2': {
            ...
        },
        ...
    }
    """
    sections = {}

    # First, identify all parallel IDs from the events
    parallel_ids = set()
    for _, events in thread_num_to_events.items():
        for event in events:
            if isinstance(event, ParallelEvent):
                parallel_ids.add(event.parallel_id)

    # For each parallel ID, determine the boundary events per thread
    for i, parallel_id in enumerate(parallel_ids):
        section_name = f"Parallel Section {i}"
        sections[section_name] = {}

        for thread_number, events in thread_num_to_events.items():
            # Initialize the time categories for the thread
            sections[section_name][f"Thread {thread_number}"] = {
                'Working': 0,
                'Critical': 0,
                'Mutex': 0
            }

            # Identify boundary events (first and last) for this parallel_id in the current thread
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
            
            print(f"thread: {thread_number} first_event: {first_event} last_event: {last_event}")

            # Extract events within the boundary
            events_in_section = [
                event for event in events
                if first_event.time <= event.time <= last_event.time
            ]
            
            # Initialize tracking variables
            prev_event = first_event

            for event in events_in_section[1:]:
                delta_time = event.time - prev_event.time
                
                # TODO... need to strictly define what "work" time is so we can accurately measure it. Most likely defined as time within an implicit task that isn't in mutex or time between task switch and complete that isn't in mutex

                if isinstance(prev_event, SyncRegionWaitEvent):
                    sections[section_name][f"Thread {thread_number}"]["Mutex"] += delta_time
                elif prev_event.event == "Mutex Acquire":
                    sections[section_name][f"Thread {thread_number}"]["Mutex"] += delta_time
                elif prev_event.event == "Mutex Acquired":
                    sections[section_name][f"Thread {thread_number}"]["Critical"] += delta_time
                
                prev_event = event

    return sections

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
        # plot_dag(graph_nodes, f"{folder_name}/{parallel_id}_dag")
        # plot_dag_with_time(graph_nodes, f"{folder_name}/{parallel_id}_dag_with_time")

def generate_graph_folder():
    now = datetime.datetime.now()
    folder_name = now.strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(f"graphs/{folder_name}", exist_ok=True)
    return folder_name

def main():
    folder_name = generate_graph_folder()
    log_folder_name = "logs/"
    thread_num_to_events = parse_logs_for_thread_events(log_folder_name)
    for thread_number, events in thread_num_to_events.items():
        print(f"Thread {thread_number}:")
        for event in events:
            print(f"  {event} {event.unique_id}")
    # graph_nodes = create_graph_for_thread_col_vs_time_viz(thread_num_to_events)
    # plot_thread_col_vs_time_viz(graph_nodes, f"{folder_name}/thread_col_vs_time")
    
    graph_nodes = create_graph_for_dependency_viz(thread_num_to_events)
    plot_dependency_viz(graph_nodes, folder_name)

    # time_spent_by_section = get_time_spent_by_section(thread_num_to_events)
    # print(time_spent_by_section)

def main_graphviz():
    folder_name = generate_graph_folder()
    log_folder_name = "logs/"
    thread_num_to_events = parse_logs_for_thread_events(log_folder_name)
    graph_nodes = generate_dag(thread_num_to_events)
    create_graphviz_graph(graph_nodes, f"graphs/{folder_name}/dag", style='thread_groups')
    create_graphviz_graph(graph_nodes, f"graphs/{folder_name}/dag_no_thread_groups", style='no_thread_groups')
    print(f"Graph saved to graphs/{folder_name}/dag.png")

if __name__ == "__main__":
    # main()
    main_graphviz()