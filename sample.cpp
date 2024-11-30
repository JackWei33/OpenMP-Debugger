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

    omp_set_num_threads(5);

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

    #pragma omp parallel for schedule(static, 1)
    for (int i = 0; i < 5; i++) {
        #pragma omp critical
        sum++;
    }
    
    #pragma omp parallel for schedule(static, 1)
    for (int i = 0; i < 5; i++) {
        #pragma omp critical
        sum*=2;
    }
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
