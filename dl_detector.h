#ifndef DL_DETECTOR_H
#define DL_DETECTOR_H

#include <omp-tools.h>

void process_mutex_acquire(ompt_mutex_t kind, ompt_wait_id_t wait_id, uint64_t thread_id);
void process_mutex_acquired(ompt_mutex_t kind, ompt_wait_id_t wait_id, uint64_t thread_id);
void process_mutex_released(ompt_mutex_t kind, ompt_wait_id_t wait_id, uint64_t thread_id);
void dl_detector_thread();

#endif
