#include <string>
#include <omp.h>
#include <omp-tools.h>
#include "helper.h"

std::string ompt_thread_t_to_string(ompt_thread_t threadType) {
    switch (threadType) {
        case ompt_thread_initial:
            return "ompt_thread_initial";
        case ompt_thread_worker:
            return "ompt_thread_worker";
        case ompt_thread_other:
            return "ompt_thread_other";
        case ompt_thread_unknown:
            return "ompt_thread_unknown";
        default:
            return "Unknown thread type";
    }
}

std::string ompt_mutex_t_to_string(ompt_mutex_t mutexType) {
    switch (mutexType) {
        case ompt_mutex_lock:
            return "ompt_mutex_lock";
        case ompt_mutex_test_lock:
            return "ompt_mutex_test_lock";
        case ompt_mutex_nest_lock:
            return "ompt_mutex_nest_lock";
        case ompt_mutex_test_nest_lock:
            return "ompt_mutex_test_nest_lock";
        case ompt_mutex_critical:
            return "ompt_mutex_critical";
        case ompt_mutex_atomic:
            return "ompt_mutex_atomic";
        case ompt_mutex_ordered:
            return "ompt_mutex_ordered";
        default:
            return "Unknown mutex type";
    }
}

std::string ompt_sync_region_t_to_string(ompt_sync_region_t syncRegion) {
    switch (syncRegion) {
        case ompt_sync_region_barrier:
            return "ompt_sync_region_barrier (DEPRECATED_51)";
        case ompt_sync_region_barrier_implicit:
            return "ompt_sync_region_barrier_implicit (DEPRECATED_51)";
        case ompt_sync_region_barrier_explicit:
            return "ompt_sync_region_barrier_explicit";
        case ompt_sync_region_barrier_implementation:
            return "ompt_sync_region_barrier_implementation";
        case ompt_sync_region_taskwait:
            return "ompt_sync_region_taskwait";
        case ompt_sync_region_taskgroup:
            return "ompt_sync_region_taskgroup";
        case ompt_sync_region_reduction:
            return "ompt_sync_region_reduction";
        case ompt_sync_region_barrier_implicit_workshare:
            return "ompt_sync_region_barrier_implicit_workshare";
        case ompt_sync_region_barrier_implicit_parallel:
            return "ompt_sync_region_barrier_implicit_parallel";
        case ompt_sync_region_barrier_teams:
            return "ompt_sync_region_barrier_teams";
        default:
            return "Unknown sync region";
    }
}

std::string ompt_scope_endpoint_t_to_string(ompt_scope_endpoint_t scopeEndpoint) {
    switch (scopeEndpoint) {
        case ompt_scope_begin:
            return "ompt_scope_begin";
        case ompt_scope_end:
            return "ompt_scope_end";
        case ompt_scope_beginend:
            return "ompt_scope_beginend";
        default:
            return "Unknown scope endpoint";
    }
}