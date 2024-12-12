# Makefile for Building OMPT Tool and Sample OpenMP Code

# ============================
# Variables
# ============================

# Compiler and Flags
CXX := clang++ 
CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -fPIC 
# CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -fPIC -lfmt

# OpenMP Flags (Ensure OpenMP and OMPT support)
OMPFLAGS := -fopenmp

# Boost Include Path (Update this path based on your Boost installation)
BOOST_INC := /usr/local/opt/boost/include
OMPT_INC := /usr/local/opt/libomp/include
# SPDLOG_INC := /usr/local/opt/spdlog/include
# FMT_INC := /usr/local/opt/fmt/include

BOOST_LIB := /usr/local/opt/boost/lib
OMPT_LIB := /usr/local/opt/libomp/lib
# SPDLOG_LIB := /usr/local/opt/spdlog/lib
# FMT_LIB := /usr/local/opt/fmt/lib


# Directories
SRC_DIR := .
BUILD_DIR := build
LOG_DIR := logs

# OMPT Tool
TOOL_SRC := $(SRC_DIR)/ompt_tool.cpp $(SRC_DIR)/helper.cpp $(SRC_DIR)/dl_detector.cpp
TOOL_OBJ := $(patsubst %.cpp,$(BUILD_DIR)/%.o,$(notdir $(TOOL_SRC)))
TOOL_LIB := libompt_tool.dylib
TOOL_LDFLAGS := -shared

# Sample Code
SAMPLE_SRC := $(SRC_DIR)/sample.cpp
SAMPLE_BIN := sample

# Include Paths
INCLUDES := -I$(SRC_DIR) -I$(BOOST_INC) -I$(OMPT_INC)
LIBRARIES := -L$(BOOST_LIB) -L$(OMPT_LIB)
# INCLUDES := -I$(SRC_DIR) -I$(BOOST_INC) -I$(OMPT_INC) -I$(SPDLOG_INC) -I$(FMT_INC)
# LIBRARIES := -L$(BOOST_LIB) -L$(OMPT_LIB) -L$(SPDLOG_LIB) -L$(FMT_LIB)

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
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

# Link OMPT Tool into Dynamic Library
$(TOOL_LIB): $(TOOL_OBJ)
	$(CXX) $(CXXFLAGS) $(OMPFLAGS) $(TOOL_LDFLAGS) $(LIBRARIES) -o $@ $^

# Compile Sample Code
$(SAMPLE_BIN): $(SAMPLE_SRC)
	$(CXX) $(CXXFLAGS) $(OMPFLAGS) $(LIBRARIES) -o $@ $<

# Clean Build and Logs
clean:
	rm -rf $(BUILD_DIR) $(TOOL_LIB) $(SAMPLE_BIN)

# Run Sample with OMPT Tool
run: all
	# Set OMPT tool environment variable and run the sample executable
	OMP_TOOL_LIBRARIES=$(PWD)/$(TOOL_LIB) ./$(SAMPLE_BIN)

# ============================
# Dependencies
# ============================

# Optional: Add dependencies if using headers
# For example:
# $(BUILD_DIR)/ompt_tool.o: $(SRC_DIR)/ompt_tool.cpp $(SRC_DIR)/helper.h $(SRC_DIR)/dl_detector.h
# Similarly for other object files
