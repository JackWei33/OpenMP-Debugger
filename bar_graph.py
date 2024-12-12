import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass, field
import datetime
from typing import Optional, List
import os
import uuid
from enum import Enum
import plotly.express as px
from collections import defaultdict
from diagram import *


def convert_from_micro_to_milli(d: dict):
    for key1 in d:
        for key2 in d[key1]:
            for key3 in d[key1][key2]:
                d[key1][key2][key3] = round(d[key1][key2][key3] / 1000, 3)

def get_time_spent_by_section(thread_num_to_events: dict):
    """ 
    Calculates the time spent synchronizing by each thread in different sections within each parallel section.

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
    sections = defaultdict(lambda : defaultdict(lambda : defaultdict(int)))

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

    # Get start and end events for each parallel section
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

    # Get total time spent by each thread in each parallel section
    parallel_id_to_thread_to_total_time = {}
    for parallel_id in parallel_id_to_thread_to_boundary_events:
        parallel_id_to_thread_to_total_time[parallel_id] = {}
        for thread in parallel_id_to_thread_to_boundary_events[parallel_id]:
            first_event, last_event = parallel_id_to_thread_to_boundary_events[parallel_id][thread]
            parallel_id_to_thread_to_total_time[parallel_id][thread] = last_event.time - first_event.time
    
    # Fill in sections with time spent in each section
    for parallel_id in parallel_id_to_thread_to_boundary_events:
        for thread in parallel_id_to_thread_to_boundary_events[parallel_id]:
            first_event, last_event = parallel_id_to_thread_to_boundary_events[parallel_id][thread]
            events = thread_num_to_events[thread]
            prev_event = None

            for event in events:
                if not (first_event.time <= event.time <= last_event.time):
                    continue
                if isinstance(event, MutexAcquireEvent) and event.kind == "ompt_mutex_critical":
                    assert(prev_event == None)
                    prev_event = event
                elif isinstance(event, MutexAcquiredEvent) and event.kind == "ompt_mutex_critical":
                    assert(isinstance(prev_event, MutexAcquireEvent) and prev_event.kind == "ompt_mutex_critical")
                    sections[f"Parallel id: {parallel_id}"][thread]["Critical"] += event.time - prev_event.time
                    prev_event = None
                elif isinstance(event, MutexAcquireEvent) and event.kind == "ompt_mutex_lock":
                    assert(prev_event == None)
                    prev_event = event
                elif isinstance(event, MutexAcquiredEvent) and event.kind == "ompt_mutex_lock":
                    assert(isinstance(prev_event, MutexAcquireEvent) and prev_event.kind == "ompt_mutex_lock")
                    sections[f"Parallel id: {parallel_id}"][thread]["Lock"] += event.time - prev_event.time
                    prev_event = None
                elif isinstance(event, SyncRegionWaitEvent) and event.endpoint == "ompt_scope_begin" \
                        and (event.kind == "ompt_sync_region_barrier_implicit_parallel" or event.kind == "ompt_sync_region_barrier_implicit_workshare" or event.kind == "ompt_sync_region_barrier_implicit"):
                    assert(prev_event == None)
                    prev_event = event
                elif isinstance(event, SyncRegionWaitEvent) and event.endpoint == "ompt_scope_end" \
                        and (event.kind == "ompt_sync_region_barrier_implicit_parallel" or event.kind == "ompt_sync_region_barrier_implicit_workshare" or event.kind == "ompt_sync_region_barrier_implicit"):
                    assert(isinstance(prev_event, SyncRegionWaitEvent) and prev_event.endpoint == "ompt_scope_begin")
                    sections[f"Parallel id: {parallel_id}"][thread]["Implicit Barrier"] += event.time - prev_event.time
                    prev_event = None
                elif isinstance(event, SyncRegionWaitEvent) and event.endpoint == "ompt_scope_begin" \
                        and event.kind == "ompt_sync_region_barrier_explicit":
                    assert(prev_event == None)
                    prev_event = event
                elif isinstance(event, SyncRegionWaitEvent) and event.endpoint == "ompt_scope_end" \
                        and event.kind == "ompt_sync_region_barrier_explicit":
                    assert(isinstance(prev_event, SyncRegionWaitEvent) and prev_event.endpoint == "ompt_scope_begin")
                    sections[f"Parallel id: {parallel_id}"][thread]["Barrier"] += event.time - prev_event.time
                    prev_event = None
                    
            # Fill in work
            total_time = parallel_id_to_thread_to_total_time[parallel_id][thread]
            spent_time = sum(sections[f"Parallel id: {parallel_id}"][thread].values())
            sections[f"Parallel id: {parallel_id}"][thread]["Working"] = total_time - spent_time
    
    return sections

def get_time_spent_by_task(thread_num_to_events: dict):
    """ 
    Calculates the time spent in each task by each thread in different sections within each parallel section.

    Returns a dictionary in the following format:
    {
        'Parallel Section 1': {
            'Thread 0': {'Task 1': 5, 'Task 2': 3, 'Task 3': 2},
            'Thread 1': {'Task 4': 4, 'Task 5': 6, 'Task 6': 1},
            ...
        },
        'Parallel Section 2': {
            ...
        },
        ...
    }
    """
    sections = defaultdict(lambda : defaultdict(lambda : defaultdict(int)))
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

    # Get start and end events for each parallel section
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
    
    # Get total time spent by each thread in each task
    for parallel_id in parallel_id_to_thread_to_boundary_events:
        for thread in parallel_id_to_thread_to_boundary_events[parallel_id]:
            first_event, last_event = parallel_id_to_thread_to_boundary_events[parallel_id][thread]
            events = thread_num_to_events[thread]
            stack = []
            prev_custom_callback = {}

            for event in events:
                if not (first_event.time <= event.time <= last_event.time):
                    continue
                if isinstance(event, ImplicitTaskEvent) and event.endpoint == "ompt_scope_begin":
                    stack.append(event)
                elif isinstance(event, ImplicitTaskEvent) and event.endpoint == "ompt_scope_end":
                    prev_event = stack.pop()
                    assert((isinstance(prev_event, ImplicitTaskEvent) and prev_event.task_number == event.task_number) \
                        or (isinstance(prev_event, TaskScheduleEvent) and prev_event.next_task_data == event.task_number))
                    sections[f"Parallel id: {parallel_id}"][thread]["Task " + str(event.task_number)] += event.time - prev_event.time
                elif isinstance(event, TaskScheduleEvent):
                    # Task Schedule Event is essentially an end TaskEvent and then a start TaskEvent
                    prev_event = stack.pop()
                        
                    assert((isinstance(prev_event, ImplicitTaskEvent) and prev_event.task_number == event.prior_task_data) \
                        or (isinstance(prev_event, TaskScheduleEvent) and prev_event.next_task_data == event.prior_task_data))
                    sections[f"Parallel id: {parallel_id}"][thread]["Task " + str(event.prior_task_data)] += event.time - prev_event.time
                    
                    stack.append(event)
                elif isinstance(event, CustomEventStart):
                    prev_custom_callback[event.name] = event
                elif isinstance(event, CustomEventEnd):
                    assert(prev_custom_callback[event.name])
                    sections["Custom Callback"][thread][f"Custom Callback: {event.name}"] += event.time - prev_custom_callback[event.name].time
                    

    # Add global view of parallel sections
    thread_to_total_time = {}
    for thread, events in thread_num_to_events.items():
        first_event = events[0]
        last_event = events[-1]
        thread_to_total_time[thread] = last_event.time - first_event.time

    for parallel_id in parallel_id_to_thread_to_boundary_events:
        for thread in parallel_id_to_thread_to_boundary_events[parallel_id]:
            first_event, last_event = parallel_id_to_thread_to_boundary_events[parallel_id][thread]
            total_time = last_event.time - first_event.time
            sections["Global"][thread][f"Parallel id {parallel_id}"] = total_time
    
    for thread in thread_to_total_time:
        sections["Global"][thread]["Non Parallel Work"] = thread_to_total_time[thread] - sum(sections["Global"][thread].values())

    return sections
                    
                    
def create_stacked_bar_chart(parallel_sections_data, sections):
    """
    Creates and displays a stacked bar chart using Plotly for each parallel section.

    Parameters:
    - parallel_sections_data: A dictionary where each key is a parallel section name, and each value
                              is a dictionary where each key is a thread name, and each value is another
                              dictionary mapping section names to the time spent in that section.
    """
    # Fill in section colors
    color_scale = px.colors.qualitative.Plotly
    section_colors = {section: color_scale[i % len(color_scale)] for i, section in enumerate(sorted(sections))}

    num_sections = len(parallel_sections_data)
    subplot_titles = sorted(list(parallel_sections_data.keys()))

    # Create subplots with a variable number of columns
    fig = make_subplots(rows=1, cols=num_sections, subplot_titles=subplot_titles)

    # Sort sections for consistent legend order
    sorted_sections = sorted(sections, key=lambda x: (len(str(x)), str(x)))

    for pos, (parallel_id, thread_data) in enumerate(sorted(parallel_sections_data.items())):
        # Extract thread names
        threads = list(thread_data.keys())

        # Prepare data for plotting
        section_times = {section: [] for section in sorted_sections}
        for thread in threads:
            for section in sorted_sections:
                section_times[section].append(thread_data[thread].get(section, 0))

        # Add a bar for each section
        for section in sorted_sections:
            fig.add_trace(go.Bar(
                name=section,
                x=threads,
                y=section_times[section],
                marker_color=section_colors[section],
                hovertemplate=(
                    'Thread: %{x}<br>' +
                    'Section: ' + str(section) + '<br>' +
                    'Time Spent: %{y}<extra></extra>'
                ),
                showlegend=(pos == 0),  # Show legend only for the first subplot
                legendgroup=section  # Group traces by section for synchronized toggling
            ), row=1, col=pos + 1)

    fig.update_layout(
        barmode='stack',
        title='Time Spent by Threads in Different Sections in Parallel Regions',
        xaxis_title='Threads',
        yaxis_title='Time Spent (ms)',
        legend_title='Sections'
    )

    # Show the plot
    fig.show()


def make_synchronization_bar_chart():
    log_folder_name = "logs/"
    thread_num_to_events = parse_logs_for_thread_events(log_folder_name)
    parallel_sections_data = get_time_spent_by_section(thread_num_to_events)
    convert_from_micro_to_milli(parallel_sections_data)

    sections = set(['Working', 'Critical', 'Lock', 'Implicit Barrier', 'Barrier', 'Other'])

    create_stacked_bar_chart(parallel_sections_data, sections)

def make_task_bar_chart():
    log_folder_name = "logs/"
    thread_num_to_events = parse_logs_for_thread_events(log_folder_name)
    parallel_sections_data = get_time_spent_by_task(thread_num_to_events)
    convert_from_micro_to_milli(parallel_sections_data)

    sections = set()
    for parallel_id in parallel_sections_data:
        for thread in parallel_sections_data[parallel_id]:
            for task in parallel_sections_data[parallel_id][thread]:
                sections.add(task)

    create_stacked_bar_chart(parallel_sections_data, sections)

if __name__ == "__main__":
    make_synchronization_bar_chart()
    make_task_bar_chart()
