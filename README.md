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