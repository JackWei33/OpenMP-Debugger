APP_NAME=wireroute

OBJS=wireroute.o validate.o
OMPT_LIB := /usr/local/opt/libomp/lib
LIBRARIES := -L$(OMPT_LIB)

CXX = clang++
CXXFLAGS = -Wall -O3 -std=c++17 -m64 -I. -fopenmp -Wno-unknown-pragmas -g

all: $(APP_NAME)

$(APP_NAME): $(OBJS)
	$(CXX) $(CXXFLAGS) $(LIBRARIES) -o $@ $(OBJS)

%.o: %.cpp %.h
	$(CXX) $(CXXFLAGS) -c $<

clean:
	/bin/rm -rf *~ *.o $(APP_NAME) *.class

# TOOL_LIB=../../libompt_tool.dylib

# run: $(APP_NAME)
# 	OMP_TOOL_LIBRARIES=$(PWD)/$(TOOL_LIB) ./$(APP_NAME)