#include <iostream>
#include <omp.h>
#include <vector>
#include <thread> // For std::this_thread::sleep_for
#include <chrono> // For std::chrono::microseconds
#include "trace_logging.h"

void my_func(int& sum, omp_lock_t& lock) {
    // Use lock to update sum
    omp_set_lock(&lock);
    sum++;
    omp_unset_lock(&lock);
}

int fib(int n) {
    int i, j;
    if (n < 2) return n;
    #pragma omp task
    i = fib(n - 1);
    #pragma omp task
    j = fib(n - 2);
    #pragma omp taskwait
    return i + j;
}

int main()
{
    long long start_time = get_time_microsecond();
    int sum = 0;

    std::cout << "Thread: " << omp_get_thread_num() << std::endl;

    // /* Example 1: Tasks spawn from single */
    // #pragma omp parallel num_threads(4)
    // {
    //     #pragma omp single
    //     {
    //         for (int i = 0; i < 5; ++i) {
    //             #pragma omp task firstprivate(i)
    //             {
    //                 std::cout << "Task " << i << " executed by thread " << omp_get_thread_num() << std::endl;
    //                 // my_func(sum);
    //                 sum++;
    //             }
    //         }
    //     }
    // }

    // /* Example 2: Tasks spawn from parallel */
    // #pragma omp parallel num_threads(4)
    // {
    //     #pragma omp task
    //     {
    //         int pid = omp_get_thread_num();
    //         std::cout << "Task 1 executed by thread " << pid << std::endl;
    //         if (pid == 0) {
    //             std::this_thread::sleep_for(std::chrono::seconds(1));
    //         }
    //         sum++;
    //     }

    //     #pragma omp task
    //     {
    //         int pid = omp_get_thread_num();
    //         std::cout << "Task 2 executed by thread " << pid << std::endl;
    //         if (pid == 0) {
    //             std::this_thread::sleep_for(std::chrono::seconds(1));
    //         }
    //         sum++;
    //     }
    // }

    // /* Example 3: Tasks spawn from tasks */
    // #pragma omp parallel num_threads(4)
    // {
    //     #pragma omp single
    //     {
    //         #pragma omp task
    //         {
    //             int pid = omp_get_thread_num();
    //             std::cout << "Task 1 executed by thread " << pid << std::endl;
    //             #pragma omp task
    //             {
    //                 int pid_inner = omp_get_thread_num();
    //                 std::cout << "Task 1.1 executed by thread " << pid_inner << std::endl;
    //                 sum++;
    //             }
    //             sum++;
    //         }

    //         #pragma omp task
    //         {
    //             int pid = omp_get_thread_num();
    //             std::cout << "Task 2 executed by thread " << pid << std::endl;
    //             #pragma omp task
    //             {
    //                 int pid_inner = omp_get_thread_num();
    //                 std::cout << "Task 2.1 executed by thread " << pid_inner << std::endl;
    //                 sum++;
    //             }
    //             sum++;
    //         }
    //     }
    // }

    // /* Example 4: Parallel for */
    // #pragma omp parallel num_threads(4)
    // {
    //     #pragma omp for
    //     for (int i = 0; i < 5; i++) {
    //         sum++;
    //     }
    // }

    #pragma omp parallel num_threads(4)
    {
        compass_trace_begin("Parallel for");
        #pragma omp for
        for (int i = 0; i < 5; i++) {
            // Your work here
        }
        compass_trace_end("Parallel for");
    }

    /* Example 5: Taskloop */
    LIBRARY_BEGIN_TRACE("hi");
    #pragma omp parallel num_threads(4)
    {
        #pragma omp single
        {
            #pragma omp taskloop num_tasks(5)
            for (int i = 0; i < 10; i++) {
                int pid = omp_get_thread_num();
                std::cout << "Task " << i << " executed by thread " << pid << std::endl;
                sum++;
            }
        }
    }
    LIBRARY_END_TRACE("hi");

    // // /* Example 6: Barrier and critical */
    // omp_lock_t lock;
    // omp_init_lock(&lock);

    // // #pragma omp parallel num_threads(2)
    // // {
    // //     my_func(sum, lock);
    // // }

    // #pragma omp parallel num_threads(4)
    // {
    //     my_func(sum, lock);
    //     #pragma omp barrier
    // }
    // omp_destroy_lock(&lock);

    // omp_set_nested(1);
    // omp_set_max_active_levels(3);
    // #pragma omp parallel num_threads(2) 
    // {
    //     // parallel_func(sum);
    //     #pragma omp parallel for num_threads(3)
    //     for (int i = 0; i < 100; i++) {
    //         std::cout << "Thread " << omp_get_thread_num() << " executing iteration " << i << std::endl;
    //         sum++;
    //     }
    // }

    // /* Example 3: Tasks spawn from tasks */
    // #pragma omp parallel num_threads(4)
    // {
    //     #pragma omp single
    //     {
    //         #pragma omp task
    //         {
    //             int pid = omp_get_thread_num();
    //             std::cout << "Task 1 executed by thread " << pid << std::endl;
    //             #pragma omp task
    //             {
    //                 int pid_inner = omp_get_thread_num();
    //                 std::cout << "Task 1.1 executed by thread " << pid_inner << std::endl;
    //                 sum++;
    //             }
    //             sum++;
    //         }

    //         #pragma omp task
    //         {
    //             int pid = omp_get_thread_num();
    //             std::cout << "Task 2 executed by thread " << pid << std::endl;
    //             #pragma omp task
    //             {
    //                 int pid_inner = omp_get_thread_num();
    //                 std::cout << "Task 2.1 executed by thread " << pid_inner << std::endl;
    //                 sum++;
    //             }
    //             sum++;
    //         }
    //     }
    // }

    // /* Example 4: Parallel for */
    // #pragma omp parallel num_threads(4)
    // {
    //     #pragma omp for
    //     for (int i = 0; i < 5; i++) {
    //         sum++;
    //     }
    // }

    // #pragma omp parallel num_threads(4)
    // {
    //     compass_trace_begin("Parallel for");
    //     #pragma omp for
    //     for (int i = 0; i < 5; i++) {
    //         // Your work here
    //     }
    //     compass_trace_end("Parallel for");
    // }

#pragma omp parallel
{
    #pragma omp single nowait
    #pragma omp taskloop nogroup
    for (int j=0; j<4; j++) {
        // do work
        compass_trace_begin("Taskloop");
        // do other work
        compass_trace_end("Taskloop");
    }
}

    // // /* Example 5: Taskloop */
    // #pragma omp parallel num_threads(4)
    // {
    //     #pragma omp single
    //     {
    //         #pragma omp taskloop num_tasks(5)
    //         for (int i = 0; i < 10; i++) {
    //             int pid = omp_get_thread_num();
    //             std::cout << "Task " << i << " executed by thread " << pid << std::endl;
    //             sum++;
    //         }
    //     }
    // }

    // // /* Example 6: Barrier and critical */
    // omp_lock_t lock;
    // omp_init_lock(&lock);

    // // #pragma omp parallel num_threads(2)
    // // {
    // //     my_func(sum, lock);
    // // }

    // #pragma omp parallel num_threads(4)
    // {
    //     my_func(sum, lock);
    //     #pragma omp barrier
    // }
    // omp_destroy_lock(&lock);

    // // omp_set_nested(1);
    // // omp_set_max_active_levels(3);
    // // #pragma omp parallel num_threads(2) 
    // // {
    // //     // parallel_func(sum);
    // //     #pragma omp parallel for num_threads(3)
    // //     for (int i = 0; i < 100; i++) {
    // //         std::cout << "Thread " << omp_get_thread_num() << " executing iteration " << i << std::endl;
    // //         sum++;
    // //     }
    // // }

    

    // // // // Sleep for 1 second
    // // // std::this_thread::sleep_for(std::chrono::seconds(1));

    // // // #pragma omp parallel num_threads(5)
    // // // {
    // // //     my_func(sum);
    // // //     #pragma omp barrier
    // // //     #pragma omp single
    // // //     {
    // // //         std::cout << "Single thread" << std::endl;

    // // //         #pragma omp taskloop num_tasks(10)
            
    // // //     }
    // // // }

    // // // #pragma omp parallel for schedule(static, 1)
    // // // for (int i = 0; i < 5; i++) {
    // // //     #pragma omp critical
    // // //     sum++;
    // // // }

    // // // #pragma omp parallel for schedule(static, 1)
    // // // for (int i = 0; i < 5; i++) {
    // // //     #pragma omp critical
    // // //     sum++;
    // // // }

    // // // omp_set_max_active_levels(3);
    // // // omp_set_max_active_levels(1);
    // // // #pragma omp parallel num_threads(4)
    // // // {
    // // //     //do something on 4 threads
    // // //     #pragma omp parallel for num_threads(2)
    // // //     for(int i=0;i<10;i++){
    // // //         std::cout << "Thread " << omp_get_thread_num() << " executing iteration " << i << std::endl;
    // // //         std::cout << "Total threads: " << omp_get_num_threads() << std::endl;
    // // //         //do something on 8 threads in total
    // // //     }
    // // // }

    // // // // mutex with task creation inside of it
    // // omp_lock_t lock;
    // // omp_init_lock(&lock);
    // // #pragma omp parallel num_threads(2)
    // // {
    // //     omp_set_lock(&lock);
    // //     #pragma omp task
    // //     {
    // //         sum++;
    // //     }
    // //     omp_unset_lock(&lock);
    // // }
    // // omp_destroy_lock(&lock);

    // // // #pragma omp parallel
    // // // {
    // // //     #pragma omp single
    // // //     sum++;

    // // //     #pragma omp barrier

    // // //     #pragma omp single 
    // // //     sum++;

    // // //     #pragma omp barrier

    // // //     #pragma omp single 
    // // //     {
    // // //         sum++;
    // // //     }
    // // // }

    // // // #pragma omp single ...
    
    // // // #pragma omp parallel num_threads(2)
    // // // {
    // // //     if (pid == 1) {
    // // //         #pragma omp task 
    // // //         {
    // // //             // get_parallel_data... to link task to 
    // // //         }
    // // //     }
    // // //     #pragma omp parallel for schedule(static, 1)
    // // //     for (int i = 0; i < 2; i++) {
    // // //         #pragma omp critical
    // // //         sum*=2;
    // // //     }
    // // // }

    // // // // Parallel region using OpenMP
    // // // #pragma omp parallel num_threads(5)
    // // // {
    // // //     my_func(sum);
    // // //     #pragma omp barrier
    // // // }

    // // // #pragma omp parallel num_threads(5)
    // // // {
    // // //     my_func(sum);
    // // //     #pragma omp barrier
    // // // }

    std::cout << "Output: " << sum << std::endl;
    std::cout << "Runtime: " << get_time_microsecond() - start_time << std::endl;

    return 0;
}
