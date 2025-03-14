#!/bin/bash

# Run qstat and get numbers at beginning of each line to use for new command
# And separate number from text
qstat -u ruppert | awk '{print $1}' | sed 's/\([0-9]*\).*/\1/' > qstat.txt

# Iterate over all numbers
for job in $(cat qstat.txt); do
    # Cancel job
    qdel $job
done

rm -f qstat.txt

exit
