#ifndef TRACE_LOGGING_H
#define TRACE_LOGGING_H

#include <omp.h>
#include <fstream>
#include <string>
#include <vector>
#include <utility>
#include <chrono>
#include <cstdint>
#include <filesystem>

std::string extract_until(const std::string& path, const std::string& target) {
    size_t pos = path.find(target); // Find the target in the string
    if (pos == std::string::npos) {
        throw std::runtime_error("Target not found in path");
    }
    size_t lastSlash = path.rfind('/', pos - 1); // Find the last '/' before the target
    return path.substr(0, lastSlash + 1);       // Extract up to that '/'
}

std::filesystem::path currentPath = std::filesystem::current_path();
std::string pathToFolder = extract_until(currentPath.string(), "OpenMP-Debugger") + "OpenMP-Debugger/";

// Function to get the current time in microseconds
inline long long get_time_microsecond() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    auto micros = std::chrono::duration_cast<std::chrono::microseconds>(duration).count();
    return micros;
}

// The logging function
inline void log_event(uint64_t thread_id, const std::string &event_type,
                      const std::vector<std::pair<std::string, std::string>> &details) {
    std::ofstream outFile;
    std::string filename = pathToFolder + "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
    outFile.open(filename, std::ios::app);
    if (!outFile.is_open()) {
        // Handle error (optional)
        return;
    }

    std::string log_message;
    log_message += "Time: " + std::to_string(get_time_microsecond()) + " µs\n";
    log_message += "Event: " + event_type + "\n";

    for (const auto &detail : details) {
        log_message += detail.first + ": " + detail.second + "\n";
    }

    log_message += "--------------------------\n";

    outFile << log_message;
    outFile.flush();  // Ensure the write is completed
}

// Macros for beginning and ending a trace section with a callback name
#define compass_trace_begin(name) do { \
    uint64_t tid = static_cast<uint64_t>(omp_get_thread_num()); \
    std::vector<std::pair<std::string, std::string>> details = { {"Name", name} }; \
    log_event(tid, "Custom Callback Begin", details); \
} while(0)

#define compass_trace_end(name) do { \
    uint64_t tid = static_cast<uint64_t>(omp_get_thread_num()); \
    std::vector<std::pair<std::string, std::string>> details = { {"Name", name} }; \
    log_event(tid, "Custom Callback End", details); \
} while(0)

#endif // TRACE_LOGGING_H
