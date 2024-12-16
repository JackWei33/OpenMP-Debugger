## Important commands:

Command to compile the tool:

`clang++ -fPIC -shared -o libompt_tool.dylib ompt_tool.cpp helper.cpp -I. -I/usr/local/opt/libomp/include -L/usr/local/opt/libomp/lib -fopenmp`

Command to compile the sample code with the tool:

`clang++ -fopenmp -L/usr/local/opt/libomp/lib -I/usr/local/opt/libomp/include sample.cpp -o sample`

Run the sample code executable:

`./sample`


## Important path variables:

This was so compiling the sample code actually uses the tool:

`export OMP_TOOL_LIBRARIES=/Users/lucaborletti/Desktop/OpenMP-Debugger/libompt_tool.dylib`

This helped me use the right clang version:

`export PATH=/Library/Developer/CommandLineTools/usr/bin:$PATH`


## Summary
We are developing a powerful debugging tool for C++ code using OpenMP. This tool will help developers visualize task-based workloads, optimize performance, and ensure correctness by detecting potential deadlocks.
Extended descriptions for all the following sections can be found in the project proposal, midway report and final report.

---

## Background
### Planned Features:
1. **Post-execution Analysis on Thread Workload Distribution**:
   - Graph workload distribution across threads.
   - Provide statistics for idle, busy, or waiting threads.
   - Leverages OMPT for data collection and callback injection.

2. **Post-execution Analysis on Intrathread Workloads**:
   - Analyze thread performance within individual threads.
   - Provide data on memory operations vs. arithmetic operations.
   - Display function-level timing to identify bottlenecks.

3. **Race Condition Checks**: (NOT IMPLEMENTED - REPLACED WITH THE PARALLEL EXECUTION GRAPH)
   - Detect race conditions at runtime using tools like Intel PIN or OMPT.
   - Explore static race condition detection by studying existing algorithms.

4. **Deadlock Detection**:
   - Identify circular dependencies using lock acquisition/release patterns.
   - Notify users of offending threads and locks causing deadlocks.

5. **Additional Possible Features**:
   - Debugger with breakpoint control (similar to gdb).
   - Memory leak detection.
   - Automatic performance optimization suggestions.

---

## The Challenge
Developing this tool poses unique challenges:
- Creating a lightweight debugger with minimal execution overhead.
- Ensuring ease of use with minimal setup.
- Collecting and analyzing data effectively using OMPT and other tools.
- Tackling advanced debugging algorithms for detecting race conditions and deadlocks.

---

## Resources
- **OMPT (OpenMP Tools API)**: Primary resource for tracking runtime activities.
- **OMPD**: Plugin for execution control, may provide supplementary insights.
- **Existing Debugging Tools**:
  - Otter
  - Intel VTune
  - Perf

---

## Goals and Deliverables
### Plan to Achieve:
1. Post-execution analysis of thread workload distribution.
2. Post-execution analysis of intrathread workloads.
3. Race condition detection (runtime and static).
4. Deadlock detection.
5. Stretch Goals:
   - Breakpoint control.
   - Memory leak detection.
   - Performance optimization suggestions.

### Demo:
- Showcase debugging capabilities on a Parallel VLSI Wire Routing project.
- Use example programs to demonstrate correctness in detecting race conditions and deadlocks.

### System Capabilities:
- Identify performance bottlenecks in C++ OpenMP code.
- Detect race conditions and deadlocks.
- Lightweight design with minimal user setup.

---

## Platform Choice
- **Language**: C++ with OpenMP.
- **Test Environment**: Multi-core processors on Gates Machines.

---

## Progress (Dec 2)

We have done extensive work and experimenting with OMPT — OpenMP’s own API for tool construction.
After reading several papers to understand how OMPT works and the different features it implements, we created a logging tool that uses callbacks to log events. When linking our tool to the runtime, running an OpenMP program will output several log files describing events like task creation, thread creation, parallel regions starting and ending, mutex acquistion, etc.
Our current work is to use these logs to output three graphs.

    1. Graph of nodes and edges representing the task structure of the program. Every OpenMP program will create implicit tasks and users can create explicit tasks. These tasks define the workflow of the program. Our graph will also include synchronization primitives that affect how the different tasks interact with one another.

    2. Bar graph of threads and tasks. This graph will output what threads worked on which tasks and for how long. We will also implement custom callbacks that allow a user to track the runtime length of their own regions. In combination with the first graph, a user will be able to see which tasks are eating up their runtime and what code regions that task corresponds to.

    3. Bar graph of threads and synchronization. This graph will output how long each thread spends working vs idling in synchronization regions. This will allow users to track how synchronization and work distribution is affecting their runtime.
    
These graphs are in progress and we expect to finish implementing them within the next two to three days. In relation to our goals and deliverables, we are only slightly behind schedule. The three graphs described above are roughly the deliverables we intended to have completed by the midway report. The delay in schedule is largely due to OMPT being more difficult to understand than we initially anticipated. We still believe we will be able to hit all our deliverables and implement the two remaining features of race condition and deadlock detection. The “nice to haves” of the project proposal were a debugger like gdb, a memory leak detector, and a performance optimization suggestor. These seem largely out of reach as we will likely only have time to complete our initial deliverables and goals.

## Reports:
[Project Proposal](./Project_Proposal.pdf)
[Midway Report](./Midway_Report.pdf)
[Final Report](./Final_Report.pdf)


## Schedule
### November 13 - November 19:
- Set up development environment and research OMPT.
- Draft architecture and feature outline.

### November 20 - November 26:
- Begin basic OMPT integration.
- Collect basic thread and task scheduling data.
- Implement data logging and verification.

### November 27 - December 3:
- Provide post-execution analysis for workload distribution and synchronization primitives.
- Provide post-execution analysis on task-based workloads.

### December 4 - December 10:
- Develop deadlock detection using dependency graphs.
- Build parallel task graph of nodes and edges for implicit and explicit tasks
- Transition to asynchronous logging

### December 11 - December 15:
- Design user-friendly output/UI for debugging.
- Integrate visualizations
- Design poster
