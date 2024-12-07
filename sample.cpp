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

int main() {
    long long start_time = get_time_microsecond();
    int sum = 0;

    omp_lock_t lock1, lock2;
    omp_init_lock(&lock1);
    omp_init_lock(&lock2);

    #pragma omp parallel num_threads(2)
    {
        int tid = omp_get_thread_num();

        if (tid == 0) {
            omp_set_lock(&lock1);
            std::this_thread::sleep_for(std::chrono::microseconds(100)); // Simulate some work
            omp_set_lock(&lock2);
            // Critical section
            sum += tid;
            omp_unset_lock(&lock2);
            omp_unset_lock(&lock1);
        } else {
            omp_set_lock(&lock2);
            std::this_thread::sleep_for(std::chrono::microseconds(100)); // Simulate some work
            omp_set_lock(&lock1);
            // Critical section
            sum += tid;
            omp_unset_lock(&lock1);
            omp_unset_lock(&lock2);
        }
    }

    omp_destroy_lock(&lock1);
    omp_destroy_lock(&lock2);

    std::cout << "Output: " << sum << std::endl;
    std::cout << "Runtime: " << get_time_microsecond() - start_time << std::endl;

    return 0;
}
