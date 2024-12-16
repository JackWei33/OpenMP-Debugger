# Makefile for Building OMPT Tool and Sample OpenMP Code

# ============================
# Variables
# ============================

# Compiler and Flags
CXX := clang++ 
CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -fPIC 

# OpenMP Flags (Ensure OpenMP and OMPT support)
FLAGS := -fopenmp

# Boost Include Path (Update this path based on your Boost installation)
BOOST_INC := /usr/local/opt/boost/include
OMPT_INC := /usr/local/opt/libomp/include
QUILL_INC := /usr/local/opt/quill/include

BOOST_LIB := /usr/local/opt/boost/lib
OMPT_LIB := /usr/local/opt/libomp/lib
QUILL_LIB := /usr/local/opt/quill/lib

# Directories
SAMPLE_SRC_DIR := .
TOOL_SRC_DIR := ompt_tool
BUILD_DIR := build
LOG_DIR := logs

# OMPT Tool
TOOL_SRC := $(TOOL_SRC_DIR)/ompt_tool.cpp $(TOOL_SRC_DIR)/helper.cpp $(TOOL_SRC_DIR)/dl_detector.cpp
TOOL_OBJ := $(patsubst %.cpp,$(BUILD_DIR)/%.o,$(notdir $(TOOL_SRC)))
TOOL_LIB := build/libompt_tool.dylib
TOOL_LDFLAGS := -shared

# Sample Code
SAMPLE_SRC := $(SAMPLE_SRC_DIR)/examples.cpp $(TOOL_SRC_DIR)/compass.cpp
SAMPLE_BIN := build/sample

# Include Paths
INCLUDES := -I$(TOOL_SRC_DIR) -I$(BOOST_INC) -I$(OMPT_INC) -I$(QUILL_INC)
LIBRARIES := -L$(BOOST_LIB) -L$(OMPT_LIB) -L$(QUILL_LIB)

# ============================
# Targets
# ============================

.PHONY: all clean run

# Default target: Build everything
all: $(BUILD_DIR) $(TOOL_LIB) $(SAMPLE_BIN)

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Compile OMPT Tool Object Files
$(BUILD_DIR)/%.o: $(TOOL_SRC_DIR)/%.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

# Link OMPT Tool into Dynamic Library
$(TOOL_LIB): $(TOOL_OBJ)
	$(CXX) $(CXXFLAGS) $(FLAGS) $(TOOL_LDFLAGS) $(LIBRARIES) -o $@ $^

# Compile Sample Code
$(SAMPLE_BIN): $(SAMPLE_SRC)
	$(CXX) $(CXXFLAGS) $(FLAGS) $(INCLUDES) $(LIBRARIES) -o $@ $^

# Clean Build and Logs
clean:
	rm -rf $(BUILD_DIR) $(SAMPLE_BIN)

# Clean log folder of .txt files
clean_logs:
	rm -rf $(LOG_DIR)/*.txt

# Run Sample with OMPT Tool
run: all
	make clean_logs
	# Set OMPT tool environment variable and run the sample executable
	OMP_TOOL_LIBRARIES=$(PWD)/$(TOOL_LIB) ./$(SAMPLE_BIN)

# ============================
# Dependencies
# ============================