#!/bin/bash
# 
# Bash script to do the simple algebra to combine deterministic and ensemble
# perturbations for each ensemble member.
# 
# James Ruppert
# 11 March 2025

echo "Starting perturbation calculations..."

# Settings
wrf_dir="wrf_coarse"
# wrf_dir="wrf_fine"

# Paths
scdir="${scratch}/tc-crfrad/nepartak"
det="${scdir}/deterministic"
emdir="${scdir}/ens_mean"

# Number of ensemble members
nmem=10
# nmem=1

# Get ensemble mean
do_ens_mean=true
# do_ens_mean=false

##### Function to get header ########################################
function qsub_header {
  # $1 = batch file name
cat > "$1" << EOF
#!/bin/bash
#PBS -N ensmean
#PBS -A UOKL0049
#PBS -l walltime=12:00:00
#PBS -j oe
#PBS -k eod
#PBS -q main
#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1
###PBS -q casper@casper-pbs
###PBS -l select=1:ncpus=1:mem=1GB

export TMPDIR=/glade/derecho/scratch/$USER/tmp
mkdir -p $TMPDIR

module load nco
EOF
}

##### Function to get ensemble mean ########################################
function qsub_file_ensmean {
  # $1 = batch file name
  qsub_header ${1}
echo "
# Get ensemble means
echo "Calculating ensemble means..."
cd met_em_mean
# Iterate over file list
while read -r file; do
  echo "Running ens mean: \$file"
  nces ../../memb_*/met_em/\${file} \${file}
done < ../file_list.txt

# Get difference deterministic - ensemble mean
echo " "
echo "Calculating differences..."
cd ../met_em_prime
# Iterate over file list
while read -r file; do
  echo "Running diff: \$file"
  ncdiff ../../deterministic/met_em/\${file} ../met_em_mean/\${file} \${file}
done < ../file_list.txt
" >> ${1}
}
############################################################################
##### Function to calculate perturbations ##################################
function qsub_file_final {
  # $1 = batch file name
  # $2 = ensemble member directory
  qsub_header ${1}
echo "
# Add prime terms to ensemble member to get final forcings
echo "Combining prime and ens. members to produce final forcing"
# Iterate over file list
while read -r file; do
  echo "Running add: \$file"
  ncadd ../met_em/\${file} ../../ens_mean/met_em_prime/\${file} \${file}
done < ../file_list.txt
" >> ${1}
}
############################################################################


if [ "$do_ens_mean" = true ]; then

  # Create ensemble mean directory
  mkdir -p ${emdir}
  cd ${emdir}
  dir_mean="${emdir}/met_em_mean"
  dir_prime="${emdir}/met_em_prime"
  mkdir -p ${dir_mean}
  mkdir -p ${dir_prime}

  # Get list of met_em files
  ls -1 ../memb_01/met_em/met_em* | awk -F'/' '{print $NF}' > file_list.txt

  # Get ensemble means
  batch_file="calc_ens_mean.sh"
  qsub_file_ensmean ${batch_file}
  qsub ${batch_file}

else

# Loop over ensemble members
for em in $(seq -w 01 $nmem); do # Ensemble member

  memb_dir="${scdir}/memb_${em}"
  dir_final="${memb_dir}/met_em_final"
  mkdir -p ${dir_final}
  cd ${dir_final}

  # Add prime terms to ensemble member to get final forcings
  batch_file="calc_perturbations.sh"
  qsub_file_final ${batch_file} "memb_${em}"
  # qsub ${batch_file}

done

fi

echo "Done!!"

exit
