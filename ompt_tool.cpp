// #include <spdlog/spdlog.h>
// #include <spdlog/async.h> // Support for asynchronous logging
// #include <spdlog/sinks/basic_file_sink.h>
// #include <spdlog/sinks/stdout_color_sinks.h>
#include "quill/Backend.h"
#include "quill/Frontend.h"
#include "quill/LogMacros.h"
#include "quill/Logger.h"
#include "quill/sinks/FileSink.h"
#include "quill/sinks/ConsoleSink.h"

#include <iostream>
// #include <unordered_map>
#include <memory>
// #include <mutex>
#include <filesystem>
#include <vector>
#include <string>
#include <chrono>

#include <omp-tools.h>
#include <omp.h>

#include "helper.h"
#include "dl_detector.h"

ompt_function_lookup_t global_lookup = NULL;
int global_task_number = 0;
int parallel_id_number = 1;
bool use_dl_detector = false;

long long get_time_microsecond() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    auto micros = std::chrono::duration_cast<std::chrono::microseconds>(duration).count();
    return micros;
}

// // Introduce a thread_local logger
// thread_local std::shared_ptr<spdlog::logger> thread_logger = nullptr;

// // Refactored function to retrieve or create a logger for the current thread
// std::shared_ptr<spdlog::logger> get_thread_logger(uint64_t thread_id)
// {
//     if (!thread_logger)
//     {
//         std::cout << "Creating logger for thread " << thread_id << std::endl;
//         // Ensure the logs directory exists
//         if (!std::filesystem::exists("logs")) {
//             std::cerr << "Logs directory does not exist. Please create it before running the tool." << std::endl;
//             return nullptr;
//         }

//         // Create a new logger for the thread
//         std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
//         auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(filename, true);
//         file_sink->set_level(spdlog::level::info);
//         file_sink->set_pattern("%v");

//         thread_logger = std::make_shared<spdlog::logger>("logger_thread_" + std::to_string(thread_id), file_sink);
//         thread_logger->set_level(spdlog::level::info);
//         thread_logger->flush_on(spdlog::level::info);

//         // Register the logger with spdlog's registry
//         spdlog::register_logger(thread_logger);
//         std::cout << "Created logger for thread " << thread_id << std::endl;
//     }
//     return thread_logger;
// }


// // Refactored function to retrieve or create a logger for the current thread
// std::shared_ptr<spdlog::logger> get_thread_logger(uint64_t thread_id)
// {
//     if (!thread_logger)
//     {
//         std::cout << "Creating logger for thread " << thread_id << std::endl;
//         // Ensure the logs directory exists
//         if (!std::filesystem::exists("logs")) {
//             std::cerr << "Logs directory does not exist. Please create it before running the tool." << std::endl;
//             return nullptr;
//         }

//         // Create a new logger for the thread
//         std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
//         auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(filename, true);
//         file_sink->set_level(spdlog::level::info);
//         file_sink->set_pattern("%v");

//         thread_logger = std::make_shared<spdlog::logger>("logger_thread_" + std::to_string(thread_id), file_sink);
//         thread_logger->set_level(spdlog::level::info);
//         thread_logger->flush_on(spdlog::level::info);

//         // Register the logger with spdlog's registry
//         spdlog::register_logger(thread_logger);
//         std::cout << "Created logger for thread " << thread_id << std::endl;
//     }
//     return thread_logger;
// }


// void wipe_log(uint64_t thread_id) {
//     std::ofstream outFile;
//     std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
//     outFile.open(filename, std::ios::trunc);
// }

void log_event(uint64_t thread_id, const std::string &event_type, const std::vector<std::pair<std::string, std::string>> &details) {
    // std::ofstream outFile;
    // std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
    // outFile.open(filename, std::ios::app);

    // std::string log_message;
    // log_message += "Time: " + std::to_string(get_time_microsecond()) + " µs\n";
    // log_message += "Event: " + event_type + "\n";

    // for (const auto &detail : details) {
    //     log_message += detail.first + ": " + detail.second + "\n";
    // }

    // log_message += "--------------------------\n";

    // outFile << log_message;
    // outFile.flush();  // Ensure the write is completed

    // auto logger = get_thread_logger(thread_id);

    // if (thread_logger) {
    //     // Construct the log message using spdlog's formatting
    //     std::string log_message = fmt::format("Time: {} µs\nEvent: {}\n", get_time_microsecond(), event_type);
    //     for (const auto &detail : details) {
    //         log_message += fmt::format("{}: {}\n", detail.first, detail.second);
    //     }
    //     log_message += "--------------------------\n";

    //     // Log asynchronously
    //     thread_logger->info("{}", log_message);
    // } else {
    //     std::cout << "Failed to get logger for thread " << thread_id << std::endl;
    // }


    auto console_sink = quill::Frontend::create_or_get_sink<quill::ConsoleSink>("console_sink_" + std::to_string(thread_id));
    auto logger = quill::Frontend::create_or_get_logger("thread_logger_" + std::to_string(thread_id), console_sink);

    std::string log_message;
    log_message += "Time: " + std::to_string(get_time_microsecond()) + " µs\n";
    log_message += "Event: " + event_type + "\n";

    for (const auto &detail : details) {
        log_message += detail.first + ": " + detail.second + "\n";
    }

    QUILL_LOG_INFO(logger, "{}", log_message);
}

// Callback for parallel region start
void on_parallel_begin(ompt_data_t *task_data, const ompt_frame_t *task_frame,
                       ompt_data_t *parallel_data, uint32_t requested_parallelism,
                       int flags, const void *codeptr_ra) {
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");
        
    parallel_data->value = parallel_id_number;
    #pragma omp atomic
    parallel_id_number++;

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;

    log_event(thread_id, "Parallel Begin", {
        {"Parallel ID", std::to_string(parallel_data ? parallel_data->value : 0)},
        {"Requested Parallelism", std::to_string(requested_parallelism)},
        {"Flags", std::to_string(flags)},
        {"Code Pointer Return Address", std::to_string(reinterpret_cast<uint64_t>(codeptr_ra))}
    });
}

// Callback for parallel region end
void on_parallel_end(ompt_data_t *parallel_data, ompt_data_t *task_data, const void *codeptr_ra) {
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");
    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;

    log_event(thread_id, "Parallel End", {
        {"Parallel ID", std::to_string(parallel_data ? parallel_data->value : 0)},
        {"Code Pointer Return Address", std::to_string(reinterpret_cast<uint64_t>(codeptr_ra))}
    });
}

void on_work(
    ompt_work_t work_type,
    ompt_scope_endpoint_t endpoint,
    ompt_data_t *parallel_data,
    ompt_data_t *task_data,
    uint64_t count,
    const void *codeptr_ra)
{
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;

    log_event(thread_id, "Work", {
        {"Parallel ID", parallel_data ? std::to_string(parallel_data->value) : "N/A"},
        {"Work Type", ompt_work_t_to_string(work_type)},
        {"Endpoint", ompt_scope_endpoint_t_to_string(endpoint)},
        {"Count", std::to_string(count)},
        {"Code Pointer Return Address", std::to_string(reinterpret_cast<uint64_t>(codeptr_ra))}
    });
}


void on_task_create(ompt_data_t *parent_task_data, const ompt_frame_t *parent_task_frame,
                    ompt_data_t *new_task_data, int flags, int has_dependences, const void *codeptr_ra) {
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");
    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;

    int task_number = global_task_number;
    #pragma omp atomic
    global_task_number++;

    new_task_data->value = task_number;

    log_event(thread_id, "Task Create", {
        {"Task Number", std::to_string(new_task_data->value)},
        {"Parent Task Number", std::to_string(parent_task_data->value)},
        {"Flags", std::to_string(flags)},
        {"Has Dependences", std::to_string(has_dependences)},
        {"Code Pointer Return Address", std::to_string(reinterpret_cast<uint64_t>(codeptr_ra))}
    });
}

void on_task_schedule(ompt_data_t *prior_task_data, ompt_task_status_t prior_task_status,
                      ompt_data_t *next_task_data) {
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");
    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;

    log_event(thread_id, "Task Schedule", {
        {"Prior Task Data", std::to_string(prior_task_data->value)},
        {"Prior Task Status", ompt_task_status_t_to_string(prior_task_status)},
        {"Next Task Data", next_task_data ? std::to_string(next_task_data->value) : "N/A"}
    });
}


void on_implicit_task(ompt_scope_endpoint_t endpoint, ompt_data_t *parallel_data,
                      ompt_data_t *task_data, unsigned int actual_parallelism,
                      unsigned int index, int flags) {
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");
    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;
    
    ompt_get_parallel_info_t ompt_get_parallel_info = (ompt_get_parallel_info_t)global_lookup("ompt_get_parallel_info");
    int team_size;
    ompt_get_parallel_info(0, &parallel_data, &team_size);

    if (endpoint == ompt_scope_begin) {
        task_data->value = global_task_number;
        #pragma omp atomic
        global_task_number++;
    }
    

    log_event(thread_id, "Implicit Task", {
        {"Task Number", std::to_string(task_data->value)},
        {"Endpoint", ompt_scope_endpoint_t_to_string(endpoint)},
        {"Actual Parallelism", std::to_string(actual_parallelism)},
        {"Index", std::to_string(index)},
        {"Flags", std::to_string(flags)},
        {"Parallel ID", parallel_data ? std::to_string(parallel_data->value) : "N/A"}
    });
}

// Callback for thread creation
void on_thread_create(ompt_thread_t thread_type, ompt_data_t *thread_data)
{
    int omp_thread_num = omp_get_thread_num();
    
    thread_data->value = (uint64_t)omp_get_thread_num();

    // if (thread_logger == nullptr) {
    //     // thread_logger = spdlog::basic_logger_mt<spdlog::async_factory>("thread_logger_" + std::to_string(omp_thread_num), "logs/logs_thread_" + std::to_string(omp_thread_num) + ".txt");
    //     thread_logger->set_level(spdlog::level::info);
    //     thread_logger->flush_on(spdlog::level::info);
    //     thread_logger->set_pattern("%v");

    //     spdlog::register_logger(thread_logger);
    // }

    log_event(omp_thread_num, "Thread Create", {
        {"Thread Type", ompt_thread_t_to_string(thread_type)}
    });
}

// Callback for synchronization region begin and end
void on_sync_region(ompt_sync_region_t kind,
                    ompt_scope_endpoint_t endpoint,
                    ompt_data_t *parallel_data,
                    ompt_data_t *task_data,
                    const void *codeptr_ra)
{
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;

    log_event(thread_id, "Sync Region", {
        {"Parallel ID", parallel_data ? std::to_string(parallel_data->value) : "N/A"},
        {"Kind", ompt_sync_region_t_to_string(kind)},
        {"Endpoint", ompt_scope_endpoint_t_to_string(endpoint)},
        {"Code Pointer Return Address", std::to_string(reinterpret_cast<uint64_t>(codeptr_ra))}
    });
}

// Mutex acquire callback
void on_mutex_acquire(
    ompt_mutex_t kind,      // The kind of mutex (e.g., lock, critical)
    unsigned int hint,      // Hint for optimization (runtime-dependent)
    unsigned int impl,      // Implementation-specific information
    ompt_wait_id_t wait_id, // ID of the mutex
    const void *codeptr_ra  // Return address of the call site
)
{
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;

    if (use_dl_detector) {
        process_mutex_acquire(kind, wait_id, thread_id);
    }

    log_event(thread_id, "Mutex Acquire", {
        {"Kind", ompt_mutex_t_to_string(kind)},
        {"Wait id", std::to_string(wait_id)},
        {"Code Pointer Return Address", std::to_string(reinterpret_cast<uint64_t>(codeptr_ra))}
    });
}

void on_mutex_acquired(
    ompt_mutex_t kind,      // The kind of mutex (e.g., lock, critical)
    ompt_wait_id_t wait_id, // ID of the mutex
    const void *codeptr_ra  // Return address of the call site
)
{
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;

    if (use_dl_detector) {
        process_mutex_acquired(kind, wait_id, thread_id);
    }

    log_event(thread_id, "Mutex Acquired", {
        {"Kind", ompt_mutex_t_to_string(kind)},
        {"Wait id", std::to_string(wait_id)},
        {"Code Pointer Return Address", std::to_string(reinterpret_cast<uint64_t>(codeptr_ra))}
    });
}

void on_mutex_released(
    ompt_mutex_t kind,      // The kind of mutex (e.g., lock, critical)
    ompt_wait_id_t wait_id, // ID of the mutex
    const void *codeptr_ra  // Return address of the call site
)
{
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;

    if (use_dl_detector) {
        process_mutex_released(kind, wait_id, thread_id);
    }

    log_event(thread_id, "Mutex Released", {
        {"Kind", ompt_mutex_t_to_string(kind)},
        {"Wait id", std::to_string(wait_id)},
        {"Code Pointer Return Address", std::to_string(reinterpret_cast<uint64_t>(codeptr_ra))}
    });
}

// Callback for synchronization region wait begin and end
void on_sync_region_wait(ompt_sync_region_t kind,
                         ompt_scope_endpoint_t endpoint,
                         ompt_data_t *parallel_data,
                         ompt_data_t *task_data,
                         const void *codeptr_ra)
{
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;

    log_event(thread_id, "Sync Region Wait", {
        {"Parallel ID", parallel_data ? std::to_string(parallel_data->value) : "N/A"},
        {"Kind", ompt_sync_region_t_to_string(kind)},
        {"Endpoint", ompt_scope_endpoint_t_to_string(endpoint)},
        {"Code Pointer Return Address", std::to_string(reinterpret_cast<uint64_t>(codeptr_ra))}
    });

    process_barrier(kind, endpoint, thread_id);
}

// OMPT initialization
int ompt_initialize(ompt_function_lookup_t lookup, int initial_device_num, ompt_data_t *tool_data)
{
    // initialize_spdlog();
    quill::Backend::start();

    global_lookup = lookup;
    auto register_callback = (ompt_set_callback_t)lookup("ompt_set_callback");

    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)lookup("ompt_get_thread_data");
    if (!ompt_get_thread_data)
    {
        std::cout << "ompt_get_thread_data function not found\n";
        return 0;
    }

    if (register_callback)
    {
        register_callback(ompt_callback_parallel_begin, (ompt_callback_t)on_parallel_begin);
        register_callback(ompt_callback_parallel_end, (ompt_callback_t)on_parallel_end);
        register_callback(ompt_callback_sync_region, (ompt_callback_t)on_sync_region);
        register_callback(ompt_callback_sync_region_wait, (ompt_callback_t)on_sync_region_wait);
        register_callback(ompt_callback_thread_begin, (ompt_callback_t)on_thread_create);
        register_callback(ompt_callback_mutex_acquire, (ompt_callback_t)on_mutex_acquire);
        register_callback(ompt_callback_mutex_acquired, (ompt_callback_t)on_mutex_acquired);
        register_callback(ompt_callback_mutex_released, (ompt_callback_t)on_mutex_released);
        register_callback(ompt_callback_task_create, (ompt_callback_t)on_task_create);
        register_callback(ompt_callback_implicit_task, (ompt_callback_t)on_implicit_task);
        register_callback(ompt_callback_task_schedule, (ompt_callback_t)on_task_schedule);
        register_callback(ompt_callback_work, (ompt_callback_t)on_work);
    }
    else
    {
        std::cerr << "Failed to retrieve ompt_set_callback.\n";
    }

    if (use_dl_detector) {
        start_dl_detector_thread();
    }

    std::cout << "OMPT tool initialized.\n";

    return 1; // Successful initialization
}

// OMPT finalization
void ompt_finalize(ompt_data_t *tool_data)
{
    // quill::Backend::stop();

    if (use_dl_detector) {
        end_dl_detector_thread();
    }
    // shutdown_spdlog();
    std::cout << "OMPT tool finalized.\n";
}

// Tool entry point
ompt_start_tool_result_t *ompt_start_tool(unsigned int omp_version, const char *runtime_version)
{
    std::cout << "ompt_start_tool invoked.\n";

    static ompt_start_tool_result_t result = {&ompt_initialize, &ompt_finalize, 0};
    return &result;
}
