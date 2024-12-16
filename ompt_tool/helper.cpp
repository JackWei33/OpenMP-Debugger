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

std::string ompt_work_t_to_string(ompt_work_t workType) {
    switch (workType) {
        case ompt_work_loop:
            return "ompt_work_loop";
        case ompt_work_sections:
            return "ompt_work_sections";
        case ompt_work_single_executor:
            return "ompt_work_single_executor";
        case ompt_work_single_other:
            return "ompt_work_single_other";
        case ompt_work_workshare:
            return "ompt_work_workshare";
        case ompt_work_distribute:
            return "ompt_work_distribute";
        case ompt_work_taskloop:
            return "ompt_work_taskloop";
        case ompt_work_scope:
            return "ompt_work_scope";
        case ompt_work_loop_static:
            return "ompt_work_loop_static";
        case ompt_work_loop_dynamic:
            return "ompt_work_loop_dynamic";
        case ompt_work_loop_guided:
            return "ompt_work_loop_guided";
        case ompt_work_loop_other:
            return "ompt_work_loop_other";
        default:
            return "Unknown work type";
    }
}

std::string ompt_task_status_t_to_string(ompt_task_status_t taskStatus) {
    switch (taskStatus) {
        case ompt_task_complete:
            return "ompt_task_complete";
        case ompt_task_yield:
            return "ompt_task_yield";
        case ompt_task_cancel:
            return "ompt_task_cancel";
        case ompt_task_detach:
            return "ompt_task_detach";
        case ompt_task_early_fulfill:
            return "ompt_task_early_fulfill";
        case ompt_task_late_fulfill:
            return "ompt_task_late_fulfill";
        case ompt_task_switch:
            return "ompt_task_switch";
        case ompt_taskwait_complete:
            return "ompt_taskwait_complete";
        default:
            return "Unknown task status";
    }
}


std::string ompt_state_t_to_string(int state) {
    switch (state) {
        // undefined state
        case ompt_state_undefined:
            return "ompt_state_undefined";

        // work states
        case ompt_state_work_serial:
            return "ompt_state_work_serial";
        case ompt_state_work_parallel:
            return "ompt_state_work_parallel";
        case ompt_state_work_reduction:
            return "ompt_state_work_reduction";

        // barrier wait states
        case ompt_state_wait_barrier:
            return "ompt_state_wait_barrier";
        case ompt_state_wait_barrier_implicit_parallel:
            return "ompt_state_wait_barrier_implicit_parallel";
        case ompt_state_wait_barrier_implicit_workshare:
            return "ompt_state_wait_barrier_implicit_workshare";
        case ompt_state_wait_barrier_implicit:
            return "ompt_state_wait_barrier_implicit";
        case ompt_state_wait_barrier_explicit:
            return "ompt_state_wait_barrier_explicit";
        case ompt_state_wait_barrier_implementation:
            return "ompt_state_wait_barrier_implementation";
        case ompt_state_wait_barrier_teams:
            return "ompt_state_wait_barrier_teams";

        // task wait states
        case ompt_state_wait_taskwait:
            return "ompt_state_wait_taskwait";
        case ompt_state_wait_taskgroup:
            return "ompt_state_wait_taskgroup";

        // mutex wait states
        case ompt_state_wait_mutex:
            return "ompt_state_wait_mutex";
        case ompt_state_wait_lock:
            return "ompt_state_wait_lock";
        case ompt_state_wait_critical:
            return "ompt_state_wait_critical";
        case ompt_state_wait_atomic:
            return "ompt_state_wait_atomic";
        case ompt_state_wait_ordered:
            return "ompt_state_wait_ordered";

        // target wait states
        case ompt_state_wait_target:
            return "ompt_state_wait_target";
        case ompt_state_wait_target_map:
            return "ompt_state_wait_target_map";
        case ompt_state_wait_target_update:
            return "ompt_state_wait_target_update";

        // misc states
        case ompt_state_idle:
            return "ompt_state_idle";
        case ompt_state_overhead:
            return "ompt_state_overhead";

        default:
            return "Unknown state";
    }
}
