#include <omp-tools.h>
#include <omp.h>
#include <iostream>
#include <fstream>
#include <chrono>
#include "helper.h"

ompt_function_lookup_t global_lookup = NULL;
long long start_time;

long long get_time_microsecond() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    auto micros = std::chrono::duration_cast<std::chrono::microseconds>(duration).count();
    return micros;
}

// Callback for parallel region start
void on_parallel_begin(ompt_data_t *task_data, const ompt_frame_t *task_frame,
                       ompt_data_t *parallel_data, uint32_t requested_parallelism,
                       int flags, const void *codeptr_ra)
{
    long long end_time = get_time_microsecond();
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;
   
    std::ofstream outFile;
    std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
    outFile.open(filename, std::ios::app);

    int time = (int)(end_time - start_time);
    outFile << "--------------------------" << std::endl;
    outFile << "Time: " << time << std::endl;
    outFile << "Parallel region begins" << std::endl;
    outFile << "--------------------------" << std::endl;
}

// Callback for parallel region end
void on_parallel_end(ompt_data_t *parallel_data, ompt_data_t *task_data, const void *codeptr_ra)
{
    long long end_time = get_time_microsecond();
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;
   
    std::ofstream outFile;
    std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
    outFile.open(filename, std::ios::app);

    int time = (int)(end_time - start_time);
    outFile << "--------------------------" << std::endl;
    outFile << "Time: " << time << std::endl;
    outFile << "Parallel region ends" << std::endl;
    outFile << "--------------------------" << std::endl;
}

// Callback for thread creation
void on_thread_create(ompt_thread_t thread_type, ompt_data_t *thread_data)
{
    long long end_time = get_time_microsecond();
    int omp_thread_num = omp_get_thread_num();
    thread_data->value = (uint64_t)omp_get_thread_num();
   
    std::ofstream outFile;
    std::string filename = "logs/logs_thread_" + std::to_string(omp_thread_num) + ".txt";
    outFile.open(filename);

    int time = (int)(end_time - start_time);
    outFile << "--------------------------" << std::endl;
    outFile << "Time: " << time << std::endl;
    outFile << "Thread creation" << std::endl;
    outFile << "Thread type: " << ompt_thread_t_to_string(thread_type) << std::endl;
    outFile << "--------------------------" << std::endl;
}

// Callback for synchronization region begin and end
void on_sync_region(ompt_sync_region_t kind,
                    ompt_scope_endpoint_t endpoint,
                    ompt_data_t *parallel_data,
                    ompt_data_t *task_data,
                    const void *codeptr_ra)
{
    long long end_time = get_time_microsecond();
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;
   
    std::ofstream outFile;
    std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
    outFile.open(filename, std::ios::app);

    int time = (int)(end_time - start_time);
    outFile << "--------------------------" << std::endl;
    outFile << "Time: " << time << std::endl;
    outFile << "Sync Region" << std::endl;
    outFile << "Kind: " << ompt_sync_region_t_to_string(kind) << std::endl;
    outFile << "Endpoint: " << ompt_scope_endpoint_t_to_string(endpoint) << std::endl;
    outFile << "Code pointer return address: " << codeptr_ra << std::endl;
    outFile << "--------------------------" << std::endl;
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
    long long end_time = get_time_microsecond();
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;
   
    std::ofstream outFile;
    std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
    outFile.open(filename, std::ios::app);

    int time = (int)(end_time - start_time);
    outFile << "--------------------------" << std::endl;
    outFile << "Time: " << time << std::endl;
    outFile << "On Mutex Acquire" << std::endl;
    outFile << "Kind: " << ompt_mutex_t_to_string(kind) << std::endl;
    outFile << "Wait id: " << wait_id << std::endl;
    outFile << "Code pointer return address: " << codeptr_ra << std::endl;
    outFile << "--------------------------" << std::endl;
}

// Callback for synchronization region wait begin and end
void on_sync_region_wait(ompt_sync_region_t kind,
                         ompt_scope_endpoint_t endpoint,
                         ompt_data_t *parallel_data,
                         ompt_data_t *task_data,
                         const void *codeptr_ra)
{
    long long end_time = get_time_microsecond();
    ompt_get_thread_data_t ompt_get_thread_data = (ompt_get_thread_data_t)global_lookup("ompt_get_thread_data");

    ompt_data_t *thread_data = ompt_get_thread_data();
    uint64_t thread_id = thread_data->value;
   
    std::ofstream outFile;
    std::string filename = "logs/logs_thread_" + std::to_string(thread_id) + ".txt";
    outFile.open(filename, std::ios::app);

    int time = (int)(end_time - start_time);
    outFile << "--------------------------" << std::endl;
    outFile << "Time: " << time << std::endl;
    outFile << "Sync Region Wait" << std::endl;
    outFile << "Kind: " << ompt_sync_region_t_to_string(kind) << std::endl;
    outFile << "Endpoint: " << ompt_scope_endpoint_t_to_string(endpoint) << std::endl;
    outFile << "Code pointer return address: " << codeptr_ra << std::endl;
    outFile << "--------------------------" << std::endl;
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
