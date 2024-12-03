#include <iostream>
#include <omp.h>
#include <vector>
#include <thread> // For std::this_thread::sleep_for
#include <chrono> // For std::chrono::microseconds

long long get_time_microsecond() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    auto micros = std::chrono::duration_cast<std::chrono::microseconds>(duration).count();
    return micros;
}

void my_func(int sum) {
    // Critical region to update sum
    #pragma omp critical
    sum++;
}

int main()
{
    long long start_time = get_time_microsecond();
    int sum = 0;

    /* Example 1: Tasks spawn from single */
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

    /* Example 2: Tasks spawn from parallel */
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

    /* Example 3: Tasks spawn from tasks */
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

    /* Example 4: Parallel for */
    // #pragma omp parallel num_threads(4)
    // {
    //     #pragma omp for
    //     for (int i = 0; i < 5; i++) {
    //         sum++;
    //     }
    // }

    /* Example 5: Taskloop */
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

    // /* Example 6: Barrier and critical */
    #pragma omp parallel num_threads(2)
    {
        #pragma omp critical
        {
            sum++;
        }
    }

    #pragma omp parallel num_threads(4)
    {
        #pragma omp critical
        {
            sum++;
        }
    }

    // #pragma omp parallel num_threads(2) 
    // {
    //     #pragma omp parallel num_threads(2) 
    //     {
    //         #pragma omp critical
    //         {
    //             sum++;
    //         }
    //     }
    // }

    

    // // Sleep for 1 second
    // std::this_thread::sleep_for(std::chrono::seconds(1));

    // #pragma omp parallel num_threads(5)
    // {
    //     my_func(sum);
    //     #pragma omp barrier
    //     #pragma omp single
    //     {
    //         std::cout << "Single thread" << std::endl;

    //         #pragma omp taskloop num_tasks(10)
            
    //     }
    // }

    // #pragma omp parallel for schedule(static, 1)
    // for (int i = 0; i < 5; i++) {
    //     #pragma omp critical
    //     sum++;
    // }

    // #pragma omp parallel for schedule(static, 1)
    // for (int i = 0; i < 5; i++) {
    //     #pragma omp critical
    //     sum++;
    // }


    // #pragma omp parallel
    // {
    //     #pragma omp single
    //     sum++;

    //     #pragma omp barrier

    //     #pragma omp single 
    //     sum++;

    //     #pragma omp barrier

    //     #pragma omp single 
    //     {
    //         sum++;
    //     }
    // }

    // #pragma omp single ...
    
    // #pragma omp parallel num_threads(2)
    // {
    //     if (pid == 1) {
    //         #pragma omp task 
    //         {
    //             // get_parallel_data... to link task to 
    //         }
    //     }
    //     #pragma omp parallel for schedule(static, 1)
    //     for (int i = 0; i < 2; i++) {
    //         #pragma omp critical
    //         sum*=2;
    //     }
    // }

    // // Parallel region using OpenMP
    // #pragma omp parallel num_threads(5)
    // {
    //     my_func(sum);
    //     #pragma omp barrier
    // }

    // #pragma omp parallel num_threads(5)
    // {
    //     my_func(sum);
    //     #pragma omp barrier
    // }

    std::cout << "Output: " << sum << std::endl;
    std::cout << "Runtime: " << get_time_microsecond() - start_time << std::endl;

    return 0;
}
