#ifndef TRACE_LOGGING_H
#define TRACE_LOGGING_H

#include <omp.h>
#include <fstream>
#include <string>
#include <vector>
#include <utility>
#include <chrono>
#include <cstdint>

// Global variable to store the start time

long long get_time_microsecond() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    auto micros = std::chrono::duration_cast<std::chrono::microseconds>(duration).count();
    return micros;
}

// The logging function
inline void log_event(uint64_t thread_id, const std::string &event_type,
                      const std::vector<std::pair<std::string, std::string>> &details) {
    std::ofstream outFile;
    std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
    outFile.open(filename, std::ios::app);

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

// Macros for beginning and ending a trace section
#define LIBRARY_BEGIN_TRACE() do { \
    uint64_t tid = (uint64_t)omp_get_thread_num(); \
    log_event(tid, "Custom Callback Begin", {}); \
} while(0)

#define LIBRARY_END_TRACE() do { \
    uint64_t tid = (uint64_t)omp_get_thread_num(); \
    log_event(tid, "Custom Callback End", {}); \
} while(0)

#endif // TRACE_LOGGING_H
