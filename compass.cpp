#include "quill/Backend.h"
#include "quill/Frontend.h"
#include "quill/LogMacros.h"
#include "quill/Logger.h"
#include "quill/sinks/FileSink.h"

#include "compass.h"

#include <omp.h>
#include <fstream>
#include <vector>
#include <chrono>
#include <cstdint>

// Anonymous namespace to restrict visibility to this translation unit

inline long long get_time_microsecond() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    auto micros = std::chrono::duration_cast<std::chrono::microseconds>(duration).count();
    return micros;
}

void log_event(uint64_t thread_id, const std::string &event_type, const std::vector<std::pair<std::string, std::string>> &details) {
    std::string log_message;
    log_message += "Time: " + std::to_string(get_time_microsecond()) + " µs\n";
    log_message += "Event: " + event_type + "\n";

    for (const auto &detail : details) {
        log_message += detail.first + ": " + detail.second + "\n";
    }

    if (quill::Backend::is_running()) {
        
        auto file_sink = quill::Frontend::create_or_get_sink<quill::FileSink>(
            "logs/logs_thread_" + std::to_string(thread_id) + ".txt",
            []()
        {
            quill::FileSinkConfig cfg;
            cfg.set_open_mode('a');
            return cfg;
        }());

        quill::Logger* logger =
            quill::Frontend::create_or_get_logger("thread_logger_" + std::to_string(thread_id), std::move(file_sink));

        
        LOG_INFO(logger, "{}", log_message);
    } else {
        std::ofstream outFile;
        std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
        outFile.open(filename, std::ios::app);
        log_message += "--------------------------\n";
        outFile << log_message;
        outFile.flush();  // Ensure the write is completed
    }
}

// Helper function to construct the details vector with mandatory "Name" and optional key-value pairs
std::vector<std::pair<std::string, std::string>> make_details(
    const std::string& name, 
    std::initializer_list<std::pair<std::string, std::string>> optional_details = {}) 
{
    std::vector<std::pair<std::string, std::string>> details = { {"Name", name} };
    details.insert(details.end(), optional_details.begin(), optional_details.end());
    return details;
}

void compass_trace_begin(const std::string& name, 
                         std::initializer_list<std::pair<std::string, std::string>> optional_details) 
{
    uint64_t tid = static_cast<uint64_t>(omp_get_thread_num());
    log_event(tid, "Custom Callback Begin", make_details(name, optional_details));
}

void compass_trace_end(const std::string& name) 
{
    uint64_t tid = static_cast<uint64_t>(omp_get_thread_num());
    std::vector<std::pair<std::string, std::string>> details = { {"Name", name} };
    log_event(tid, "Custom Callback End", details);
}