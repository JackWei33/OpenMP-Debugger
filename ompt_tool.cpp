#include <omp-tools.h>
#include <iostream>

// Callback for parallel region start
void on_parallel_begin(ompt_data_t *task_data, const ompt_frame_t *task_frame,
                       ompt_data_t *parallel_data, uint32_t requested_parallelism,
                       int flags, const void *codeptr_ra)
{
    std::cout << "Parallel region started." << std::endl;

    // Print task data
    if (task_data && task_data->value != 0)
    {
        std::cout << "Task Data: " << task_data->value << std::endl;
    }
    else
    {
        std::cout << "Task Data: NULL or uninitialized." << std::endl;
    }

    // Print task frame information
    if (task_frame)
    {
        std::cout << "Task Frame:" << std::endl;
        std::cout << "  Enter Frame value: " << task_frame->enter_frame.value << std::endl;
        std::cout << "  Exit Frame value: " << task_frame->exit_frame.value << std::endl;
        std::cout << "  Enter Frame ptr: " << task_frame->enter_frame.ptr << std::endl;
        std::cout << "  Exit Frame ptr: " << task_frame->exit_frame.ptr << std::endl;
    }
    else
    {
        std::cout << "Task Frame: NULL" << std::endl;
    }

    // Print parallel data
    if (parallel_data && parallel_data->value != 0)
    {
        std::cout << "Parallel Data: " << parallel_data->value << std::endl;
    }
    else
    {
        std::cout << "Parallel Data: NULL or uninitialized." << std::endl;
    }

    // Print requested parallelism
    std::cout << "Requested Parallelism: " << requested_parallelism << std::endl;

    // Print flags
    std::cout << "Flags: " << flags << std::endl;

    // Print code pointer return address
    std::cout << "Code Pointer Return Address: " << codeptr_ra << std::endl;
}

// Callback for parallel region end
void on_parallel_end(ompt_data_t *parallel_data, ompt_data_t *task_data, const void *codeptr_ra)
{
    std::cout << "Parallel region ended.\n";
}

// OMPT initialization
int ompt_initialize(ompt_function_lookup_t lookup, int initial_device_num, ompt_data_t *tool_data)
{
    std::cout << "OMPT tool initialized.\n";

    auto register_callback = (ompt_set_callback_t)lookup("ompt_set_callback");
    if (register_callback)
    {
        register_callback(ompt_callback_parallel_begin, (ompt_callback_t)on_parallel_begin);
        register_callback(ompt_callback_parallel_end, (ompt_callback_t)on_parallel_end);
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
