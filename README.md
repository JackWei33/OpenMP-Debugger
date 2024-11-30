Command to compile the tool:
`clang++ -fPIC -shared -o libompt_tool.dylib ompt_tool.cpp helper.cpp -I. -I/usr/local/opt/libomp/include -L/usr/local/opt/libomp/lib -fopenmp`

Command to compile the sample code with the tool:
`clang++ -fopenmp -L/usr/local/opt/libomp/lib -I/usr/local/opt/libomp/include sample.cpp -o sample`

Run the sample code executable:
`./sample`