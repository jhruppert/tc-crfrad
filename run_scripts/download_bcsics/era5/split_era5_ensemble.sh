#!/bin/bash -l
#PBS -N era-split
#PBS -A UOKL0049
#PBS -l walltime=12:00:00
###PBS -q casper@casper-pbs
#PBS -q main
#PBS -j oe
#PBS -k eod
### Select n nodes with a max of 36 CPUs per node for a total of n*36 MPI processes
###PBS -l select=1:ncpus=1:mem=1GB
#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1
# 
# Bash script to split ERA5 ensemble grib file into individual ensemble members.
# 
# The script uses wgrib to extract individual ensemble members from the grib file
# and assumes a mamba environment containing wgrib is available to be activated.
# 
# James Ruppert
# 9 March 2025

# Activate mamba env containing wgrib
source ~/.bashrc
mamba activate wgrib

# Directories and file paths
scdir="$scratch/tc-crfrad/bcsics"
cd $scdir
ensemb_dir="${scdir}/ensemble_members"
mkdir -p $ensemb_dir

nmem=10 # Number of ensemble members

# Loop over each ensemble member and extract it using wgrib
for em in $(seq 1 $nmem); do # Ensemble member
# for em in 01; do # Ensemble member

  # Create member directory
  output_dir="$ensemb_dir/memb_$(printf "%02d" $em)"
  mkdir -p $output_dir # -p ignores if directory already exists


  ##### SINGLE LEVELS ########################################

  echo "Extracting SL for memb_$(printf "%02d" $em)..."

  era5_grib_file="ERA5-20160701-20160706-ens-sl.grib"
  input_file="$scdir/$era5_grib_file"
  # Get file name up to .grib from input file
  base_file_name="${era5_grib_file%.grib}"

  # Set output filename
  output_file="${output_dir}/${base_file_name}_$(printf "%02d" $em).grib"
  # Remove file if it already exists
  if [ -f $output_file ]; then
    /bin/rm $output_file
  fi

  # Use while loop to extract all records for a given ensemble member
  # "record_number" is key iterator, increasing by $nmem
  # Once record number is not found, loop breaks, moving onto next ensemble member
  # Initialize record number, offset by em
  record_number=${em}
  while true; do
    # Check if the record exists
    record_info=$(wgrib $input_file -s -d $record_number 2>/dev/null)
    if [ -z "$record_info" ]; then # Checks if record_info is null
      break
    fi
    # Extract the record and append to the output file
    wgrib $input_file -d $record_number -grib -append -o $output_file > /dev/null
    # Increment the record number by nens
    record_number=$((record_number + 10))
    # For testing mode
    # if [ $record_number -gt 20 ]; then
    #   break
    # fi
  done


  ##### PRESSURE LEVELS ########################################

  echo "Extracting PL for memb_$(printf "%02d" $em)..."

  era5_grib_file="ERA5-20160701-20160706-ens-pl.grib"
  input_file="$scdir/$era5_grib_file"
  # Get file name up to .grib from input file
  base_file_name="${era5_grib_file%.grib}"

  # Set output filename
  output_file="${output_dir}/${base_file_name}_$(printf "%02d" $em).grib"
  # Remove file if it already exists
  if [ -f $output_file ]; then
    /bin/rm $output_file
  fi

  # Use while loop to extract all records for a given ensemble member
  # "record_number" is key iterator, increasing by $nmem
  # Once record number is not found, loop breaks, moving onto next ensemble member
  # Initialize record number, offset by em
  record_number=${em}
  while true; do
    # Check if the record exists
    record_info=$(wgrib $input_file -s -d $record_number 2>/dev/null)
    if [ -z "$record_info" ]; then # Checks if record_info is null
      break
    fi
    # Extract the record and append to the output file
    wgrib $input_file -d $record_number -grib -append -o $output_file > /dev/null
    # Increment the record number by nens
    record_number=$((record_number + 10))
    # For testing mode
    # if [ $record_number -gt 20 ]; then
    #   break
    # fi
  done

  # For testing mode
  # break

done

echo "Extraction complete. Ensemble members are stored in the $output_dir directory."