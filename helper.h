#ifndef HELPER_H
#define HELPER_H

#include <string>
#include <omp.h>
#include <omp-tools.h>

// Function declarations (prototypes)
std::string ompt_thread_t_to_string(ompt_thread_t threadType);
std::string ompt_mutex_t_to_string(ompt_mutex_t mutexType);
std::string ompt_sync_region_t_to_string(ompt_sync_region_t syncRegion);
std::string ompt_scope_endpoint_t_to_string(ompt_scope_endpoint_t scopeEndpoint);
std::string ompt_work_t_to_string(ompt_work_t workType);
std::string ompt_task_status_t_to_string(ompt_task_status_t taskStatus);
std::string ompt_state_t_to_string(int state);

#endif // HELPER_H