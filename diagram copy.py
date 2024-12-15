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

def generate_dag(thread_num_to_events: Dict[int, List[LogEvent]], detailed: bool = False):
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
            # if isinstance(event,)
            # if isinstance(event, SyncRegionEvent) or isinstance(event, SyncRegionWaitEvent):
            #     # skip sync region events and sync region wait events
            #     continuefgreen
            if isinstance(event, WorkEvent) and event.work_type == 'ompt_work_single_other':
                continue
            if isinstance(event, SyncRegionEvent):
                continue
            if isinstance(event, SyncRegionWaitEvent) and ('implicit' in event.kind or 'taskgroup' in event.kind or 'ompt_scope_begin' in event.endpoint):
                continue
            # if isinstance(event, SyncRegionWaitEvent):
            #     # skip sync region wait events
            #     continue
            # if isinstance(event, SyncRegionEvent) and ('implicit' in event.kind or 'taskgroup' in event.kind):
            #     continue
            # if isinstance(event, WorkEvent) and event.endpoint == 'ompt_scope_end':
            #     continue
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
        shape = 'diamond'
    elif isinstance(node.event, SyncRegionEvent) and node.event.endpoint == 'ompt_scope_begin':
        shape = 'octagon'
    elif isinstance(node.event, SyncRegionEvent) and node.event.endpoint == 'ompt_scope_end':
        shape = 'octagon'
    elif isinstance(node.event, SyncRegionWaitEvent) and node.event.endpoint == 'ompt_scope_begin':
        shape = 'octagon'
    elif isinstance(node.event, SyncRegionWaitEvent) and node.event.endpoint == 'ompt_scope_end':
        shape = 'octagon'
    elif isinstance(node.event, ThreadCreateEvent):
        shape = 'doublecircle'
    elif isinstance(node.event, TaskCreateEvent):
        shape = 'diamond'
    elif isinstance(node.event, TaskScheduleEvent) and node.event.prior_task_status == 'ompt_task_switch':
        shape = 'diamond'
    elif isinstance(node.event, TaskScheduleEvent) and node.event.prior_task_status == 'ompt_task_complete':
        shape = 'square'
    elif isinstance(node.event, MutexAcquireEvent):
        shape = 'octagon'
    elif isinstance(node.event, MutexAcquiredEvent):
        shape = 'octagon'
        # shape = 'invtriangle'
    elif isinstance(node.event, MutexReleaseEvent):
        shape = 'octagon'
        # shape = 'triangle'
    elif isinstance(node.event, WorkEvent) and node.event.endpoint == 'ompt_scope_begin':
        shape = 'diamond'
    elif isinstance(node.event, WorkEvent) and node.event.endpoint == 'ompt_scope_end':
        shape = 'diamond'
    elif isinstance(node.event, CustomEventStart):
        shape = 'star'
    elif isinstance(node.event, CustomEventEnd):
        shape = 'star'
    else:
        shape = 'box'
    return shape

def get_label(node: GraphNode):
    # return ''
    if isinstance(node.event, TaskScheduleEvent):
        if node.event.prior_task_status == 'ompt_task_complete':
            return 'C'
        elif node.event.prior_task_status == 'ompt_task_switch':
            return 'S'
    elif isinstance(node.event, MutexAcquireEvent):
        return 'W'
    elif isinstance(node.event, MutexAcquiredEvent):
        return 'A'
    elif isinstance(node.event, MutexReleaseEvent):
        return 'R'
    elif isinstance(node.event, TaskCreateEvent) or isinstance(node.event, ImplicitTaskEvent):
        return f'{node.event.task_number}'
    elif isinstance(node.event, ThreadCreateEvent):
        return f'{node.event.thread_number}'
    elif isinstance(node.event, SyncRegionWaitEvent):
        if 'implicit' in node.event.kind:
            return "I"
        if 'taskwait' in node.event.kind:
            return "TW"
        else:
            return "B"
    else:
        return ''
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
    if isinstance(node.event, MutexAcquireEvent):
        return 'darkred'
    elif isinstance(node.event, MutexAcquiredEvent):
        return 'red'
    elif isinstance(node.event, MutexReleaseEvent):
        return 'pink'
    elif isinstance(node.event, SyncRegionEvent) or isinstance(node.event, SyncRegionWaitEvent):
        if 'implicit' in node.event.kind or 'taskgroup' in node.event.kind:
            return 'gray'
        if 'taskwait' in node.event.kind:
            return 'orange'
        else:
            return 'darkgreen'
    elif isinstance(node.event, TaskScheduleEvent):
        if node.event.prior_task_status == 'ompt_task_switch':
            return 'lightgreen'
        elif node.event.prior_task_status == 'ompt_task_complete':
            return 'green'
    elif isinstance(node.event, TaskCreateEvent):
        return 'lightgreen'
    elif isinstance(node.event, WorkEvent):
        if node.event.work_type == 'ompt_work_single_other':
            return 'gray'
        else:
            return 'lightblue'
    elif isinstance(node.event, ThreadCreateEvent):
        return 'purple'
    elif isinstance(node.event, ImplicitTaskEvent):
        return 'pink'
    elif isinstance(node.event, ParallelEvent) or isinstance(node.event, ParallelEndEvent):
        return 'yellow'
    elif isinstance(node.event, CustomEventStart) or isinstance(node.event, CustomEventEnd):
        return 'blue'
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
                    c.node(node.event.unique_id, label=label, shape=shape, fillcolor=color, style='filled,solid', width='0.5')
                    add_edges_to_object(c, node, within_thread=True)

        # Add edges between threads
        for node in graph_nodes:
            add_edges_to_object(dot, node, within_thread=False)
            
    elif style == 'no_thread_groups':
        def add_edges_to_object(c: Digraph, node: GraphNode):
            for edge_type, child_node in node.children:
                style, penwidth, color = get_edge_attributes(edge_type)
                c.edge(node.event.unique_id, child_node.event.unique_id, style=style, color=color, penwidth=penwidth)
                
        sorted_graph_nodes = sorted(graph_nodes, key=lambda n: n.event.time)
        
        for node in sorted_graph_nodes:
            label = get_label(node)
            shape = get_shape(node)
            color = get_color(node)
            dot.node(node.event.unique_id, label=label, shape=shape, fillcolor=color, style='filled,solid', width='0.5')
            add_edges_to_object(dot, node)

    # Save and render the graph
    dot.render(output_file, view=False, format='png')

def create_graphviz_graph_by_time(graph_nodes: List[GraphNode], output_file: str):
    """
    Create a Graphviz graph from the given graph nodes and save it to a file.

    Args:
        graph_nodes (List[GraphNode]): The list of graph nodes generated by generate_dag.
        output_file (str): The path to the output file where the graph will be saved.
    """
    max_time = max(node.event.time for node in graph_nodes)
    min_time = min(node.event.time for node in graph_nodes)
    
    for node in graph_nodes:
        node.event.time = (node.event.time - min_time) / (max_time - min_time)
    
    width_per_thread = 200
    total_height = 1000
    
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
                x = thread_number * width_per_thread
                y = node.event.time * total_height  
                c.node(node.event.unique_id, label=label, shape=shape, fillcolor=color, style='filled,solid', pos=f"{x},{y}!")
                add_edges_to_object(c, node, within_thread=True)

    # Add edges between threads
    for node in graph_nodes:
        add_edges_to_object(dot, node, within_thread=False)
            
    # Save and render the graph
    dot.render(output_file, view=False, format='png')


def generate_graph_folder():
    now = datetime.datetime.now()
    folder_name = now.strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(f"graphs/{folder_name}", exist_ok=True)
    return folder_name



def generate_graphviz_legend(output_file: str):
    all_possible_events: List[Tuple[GraphNode, str]] = [
        (GraphNode(ImplicitTaskEvent(0, '', 0, 0, 'ompt_task_begin', 0)), 'Implicit Task'),
        (GraphNode(ParallelEvent(0, '', 0, 0)), 'Parallel Region'),
        (GraphNode(SyncRegionWaitEvent(0, '', 0, 0, 'taskwait', 'ompt_scope_begin')), 'Taskwait'),
        (GraphNode(SyncRegionWaitEvent(0, '', 0, 0, 'implicit', 'ompt_scope_begin')), 'Implicit Barrier'),
        (GraphNode(SyncRegionWaitEvent(0, '', 0, 0, 'explicit', 'ompt_scope_begin')), 'Explicit Barrier'),
        (GraphNode(ThreadCreateEvent(0, '', 1, '')), 'Thread Create'),
        (GraphNode(TaskCreateEvent(0, '', 42, 0, 0)), 'Task Create'),
        (GraphNode(TaskScheduleEvent(0, '', 42, 0, 'ompt_task_switch', 0)), 'Task Switch'),
        (GraphNode(TaskScheduleEvent(0, '', 42, 0, 'ompt_task_complete', 0)), 'Task Complete'),
        (GraphNode(MutexAcquireEvent(0, '', 0, '', 0)), 'Mutex Acquire'),
        (GraphNode(MutexAcquiredEvent(0, '', 0, '', 0)), 'Mutex Acquired'),
        (GraphNode(MutexReleaseEvent(0, '', 0, '', 0)), 'Mutex Release'),
        (GraphNode(WorkEvent(0, '', 0, 0, 'ompt_work_single_other', '')), 'Work Other'),
        (GraphNode(WorkEvent(0, '', 0, 0, 'ompt_work_single_self', '')), 'Work Self'),
        (GraphNode(CustomEventStart(0, '', 0, 'ompt_custom_begin')), 'Custom Callback'),
    ]
    
    from graphviz import Digraph
    dot = Digraph(comment='DAG from Events')
    """ Create a cluster that represents the legend """
    """ Create every possible event type, and a node for it, and then add it to the cluster
    draw an arrow to the a plaintext node that says its event name """

    for tuple in all_possible_events:
        print(tuple)
        node, event_name = tuple
        shape = get_shape(node)
        color = get_color(node)
        label = get_label(node)
        dot.node(event_name, label=label, shape=shape, fillcolor=color, style='filled,solid', width='0.5', height='0.5')
        dot.node(event_name + '_legend', label=event_name, shape='plaintext', fillcolor='white', style='filled,solid', width='0.5', height='0.5')
        dot.edge(event_name, event_name + '_legend', arrowhead='none')
    dot.render(output_file, view=False, format='png')

def main_graphviz():
    folder_name = generate_graph_folder()
    log_folder_name = "asst3/code/logs/"
    # log_folder_name = "logs/"
    thread_num_to_events = parse_logs_for_thread_events(log_folder_name)
    graph_nodes = generate_dag(thread_num_to_events)
    create_graphviz_graph(graph_nodes, f"graphs/{folder_name}/dag", style='thread_groups')
    create_graphviz_graph(graph_nodes, f"graphs/{folder_name}/dag_no_thread_groups", style='no_thread_groups')
    # create_graphviz_graph_by_time(graph_nodes, f"graphs/{folder_name}/dag_by_time")
    generate_graphviz_legend(f"graphs/{folder_name}/legend")
    print(f"Graph saved to graphs/{folder_name}/dag.png")

if __name__ == "__main__":
    main_graphviz()