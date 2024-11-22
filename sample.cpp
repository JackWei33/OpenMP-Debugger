#include <iostream>
#include <omp.h>
#include <vector>
#include <thread> // For std::this_thread::sleep_for
#include <chrono> // For std::chrono::microseconds

int main()
{
    int sum = 0;

    // Parallel summation using OpenMP
    #pragma omp parallel num_threads(2)
    {
        // Critical region to update sum
        #pragma omp critical
        {
            sum += 1;
        }

        // #pragma omp barrier

        // if (omp_get_thread_num() == 0) {
        //     #pragma omp critical
        //     {
        //         sum = 0; // Reset sum inside a critical region
        //     }
        // }

        // #pragma omp critical
        // {
        //     sum += 1;
        // }
    }

    std::cout << "Sum of the array: " << sum << std::endl;

    return 0;
}
