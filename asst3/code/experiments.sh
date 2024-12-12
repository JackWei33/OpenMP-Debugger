#!/bin/bash

# Output file
output_file="/afs/andrew.cmu.edu/usr6/lborlett/private/15418/shared-asst3/code/experiments_output.txt"

# Clear or create the output file
echo "Running batch operations" > "$output_file"

# Loop through ALGO_TYPE values
for algo_type in W A; do
    # Loop through NUM_THREADS values
    for num_threads in 1 2 4 8 16; do
        # Inform which configuration is running
        echo "Running wireroute with ALGO_TYPE=$algo_type and NUM_THREADS=$num_threads" >> "$output_file"

        # Run the make and wireroute command, followed by the validate script
        make && ./wireroute -f inputs/timeinput/hard_4096.txt -n $num_threads -m $algo_type -b 1 >> "$output_file" && \
        ./validate.py -r inputs/timeinput/hard_4096_wires_$num_threads.txt -c inputs/timeinput/medium_4096_occupancy_$num_threads.txt >> "$output_file"
    done
done
