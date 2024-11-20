#include <iostream>
#include <omp.h>
#include <vector>

int main()
{
    const int size = 1000000;        // Size of the array
    std::vector<int> array(size, 1); // Initialize an array with all elements as 1
    int sum = 0;

// Parallel summation using OpenMP
#pragma omp parallel for num_threads(4)
    for (int i = 0; i < size; i++)
    {
        sum += array[i];
    }

    std::cout << "Sum of the array: " << sum << std::endl;
    return 0;
}
