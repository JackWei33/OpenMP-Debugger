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

## Progress (Dec 2)

We have done extensive work and experimenting with OMPT — OpenMP’s own API for tool construction.
After reading several papers to understand how OMPT works and the different features it implements, we created a logging tool that uses callbacks to log events. When linking our tool to the runtime, running an OpenMP program will output several log files describing events like task creation, thread creation, parallel regions starting and ending, mutex acquistion, etc.
Our current work is to use these logs to output three graphs.

    1. Graph of nodes and edges representing the task structure of the program. Every OpenMP program will create implicit tasks and users can create explicit tasks. These tasks define the workflow of the program. Our graph will also include synchronization primitives that affect how the different tasks interact with one another.

    2. Bar graph of threads and tasks. This graph will output what threads worked on which tasks and for how long. We will also implement custom callbacks that allow a user to track the runtime length of their own regions. In combination with the first graph, a user will be able to see which tasks are eating up their runtime and what code regions that task corresponds to.

    3. Bar graph of threads and synchronization. This graph will output how long each thread spends working vs idling in synchronization regions. This will allow users to track how synchronization and work distribution is affecting their runtime.
    
These graphs are in progress and we expect to finish implementing them within the next two to three days. In relation to our goals and deliverables, we are only slightly behind schedule. The three graphs described above are roughly the deliverables we intended to have completed by the midway report. The delay in schedule is largely due to OMPT being more difficult to understand than we initially anticipated. We still believe we will be able to hit all our deliverables and implement the two remaining features of race condition and deadlock detection. The “nice to haves” of the project proposal were a debugger like gdb, a memory leak detector, and a performance optimization suggestor. These seem largely out of reach as we will likely only have time to complete our initial deliverables and goals.

## Schedule
1. December 3 - December 6
• Luca: Complete algorithm for parsing logs to extract necessary information for the 3 graphs
• Jack: Build UI for graphs using Plotly
2. December 6 - December 9
• Luca: Research and implement race condition detection
• Jack: Research and implement deadlock detection
3. December 9 - December 12
• Luca: Design and build our poster
• Jack: Use our debugger on example programs and our Assignment 3
4. December 12 - December 15
• Jack and Luca: Finish up any remaining work and write the final report