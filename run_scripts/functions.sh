#!/bin/bash
# 
# Functions to be used in run_ensemble_ndown_wrf.sh
# 
# James Ruppert
# 16 Dec 2024

# Function to modify namelist dates
# Run as, e.g., set_startend_times $t_stamp_start "start" $namelist_file
set_startend_times() {
  MM=`echo $1 | cut -d'-' -f 2`
  DD=`echo $1 | cut -d'-' -f 3 | cut -d'_' -f 1`
  HH=`echo $1 | cut -d'_' -f 2 | cut -d':' -f 1`
  sed -i "s/${2}_month.*/${2}_month = ${MM}, ${MM},/" $3
  sed -i "s/${2}_day.*/${2}_day = ${DD}, ${DD},/" $3
  sed -i "s/${2}_hour.*/${2}_hour = ${HH}, ${HH},/" $3
}
