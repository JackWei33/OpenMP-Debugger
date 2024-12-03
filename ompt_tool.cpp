#include <omp-tools.h>
#include <omp.h>
#include <iostream>
#include <fstream>
#include <chrono>
#include "helper.h"
#include <vector>
#include <string>
#include <utility>

ompt_function_lookup_t global_lookup = NULL;
long long start_time;
int global_task_number = 0;

long long get_time_microsecond() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    auto micros = std::chrono::duration_cast<std::chrono::microseconds>(duration).count();
    return micros;
}

void wipe_log(uint64_t thread_id) {
    std::ofstream outFile;
    std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
    outFile.open(filename, std::ios::trunc);
}

void log_event(uint64_t thread_id, const std::string &event_type, const std::vector<std::pair<std::string, std::string>> &details) {
    std::ofstream outFile;
    std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
    outFile.open(filename, std::ios::app);

    outFile << "Time: " << (get_time_microsecond() - start_time) << " µs" << std::endl;
    outFile << "Event: " << event_type << std::endl;

    for (const auto &detail : details) {
        outFile << detail.first << ": " << detail.second << std::endl;
    }

    outFile << "--------------------------" << std::endl;
}

// Callback for parallel region start
void on_parallel_begin(ompt_data_t *task_data, const ompt_frame_t *task_frame,
                       ompt_data_t *parallel_data, uint32_t requested_parallelism,
                       int flags, const void *codeptr_ra) {
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");
    ompt_get_unique_id_t ompt_get_unique_id = (ompt_get_unique_id_t)global_lookup("ompt_get_unique_id");

    if (ompt_get_unique_id) {
        uint64_t unique_id = ompt_get_unique_id();
        parallel_data->value = unique_id;
    }

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
        {"Task Number", std::to_string(task_number)},
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

    int task_number = global_task_number;
    #pragma omp atomic
    global_task_number++;

    log_event(thread_id, "Implicit Task", {
        {"Task Number", std::to_string(task_number)},
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

    wipe_log(omp_thread_num);

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
}

// OMPT initialization
int ompt_initialize(ompt_function_lookup_t lookup, int initial_device_num, ompt_data_t *tool_data)
{
    std::cout << "OMPT tool initialized.\n";
    global_lookup = lookup;
    start_time = get_time_microsecond();
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
    return 1; // Successful initialization
}

// OMPT finalization
void ompt_finalize(ompt_data_t *tool_data)
{
    std::cout << "OMPT tool finalized.\n";
}

// Tool entry point
ompt_start_tool_result_t *ompt_start_tool(unsigned int omp_version, const char *runtime_version)
{
    std::cout << "ompt_start_tool invoked.\n";

    static ompt_start_tool_result_t result = {&ompt_initialize, &ompt_finalize, 0};
    return &result;
}
