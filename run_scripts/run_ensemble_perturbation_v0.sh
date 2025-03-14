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
det=${scdir}/deterministic
emdir=${scdir}/ens_mean

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
  # $2 = WRF directory
  qsub_header ${1}
echo "
# Get ensemble mean
if [ ${2} == "wrf_coarse" ]; then
  echo "Running ens mean: wrfinput_d01"
  nces ../../memb_*/ctl/${2}/wrfinput_d01 wrfinput_d01_em
  echo "Running ens mean: wrfbdy_d01"
  nces ../../memb_*/ctl/${2}/wrfbdy_d01 wrfbdy_d01_em
  echo "Running ens mean: wrffdda_d01"
  nces ../../memb_*/ctl/${2}/wrffdda_d01 wrffdda_d01_em
fi

# The only file that doesn't get processed by NDOWN, so need it for both domains
echo "Running ens mean: wrflowinp_d01"
if [ ${2} == "wrf_fine" ]; then
  nces ../../memb_*/ctl/${2}/ndown_save/wrflowinp_d02 wrflowinp_d01_em
else
  nces ../../memb_*/ctl/${2}/wrflowinp_d01 wrflowinp_d01_em
fi

# Get difference deterministic - ensemble mean
if [ ${2} == "wrf_coarse" ]; then
  echo "Running diff: wrfinput_d01"
  ncdiff ../../deterministic/ctl/${2}/wrfinput_d01 wrfinput_d01_em wrfinput_d01_prm
  echo "Running diff: wrfbdy_d01"
  ncdiff ../../deterministic/ctl/${2}/wrfbdy_d01 wrfbdy_d01_em wrfbdy_d01_prm
  echo "Running diff: wrffdda_d01"
  ncdiff ../../deterministic/ctl/${2}/wrffdda_d01 wrffdda_d01_em wrffdda_d01_prm
fi

# The only file that doesn't get processed by NDOWN, so need it for both domains
echo "Running diff: wrflowinp_d01"
if [ ${2} == "wrf_fine" ]; then
  ncdiff ../../deterministic/ctl/${2}/ndown_save/wrflowinp_d02 wrflowinp_d01_em wrflowinp_d01_prm
else
  ncdiff ../../deterministic/ctl/${2}/wrflowinp_d01 wrflowinp_d01_em wrflowinp_d01_prm
fi
" >> ${1}
}
############################################################################
##### Function to calculate perturbations ##################################
function qsub_file_final {
  # $1 = batch file name
  # $2 = ensemble member directory
  # $3 = WRF directory
  qsub_header ${1}
echo "


# Link wrfinput files to current directory
if [ ${3} == "wrf_coarse" ]; then
  ln -sf ../../${3}/wrfinput_d01    wrfinput_d01
  ln -sf ../../${3}/wrfbdy_d01      wrfbdy_d01
  ln -sf ../../${3}/wrffdda_d01 wrffdda_d01
fi
if [ ${2} == "wrf_fine" ]; then
  ln -sf ../../${3}/ndown_save/wrflowinp_d01   wrflowinp_d01
else
  ln -sf ../../${3}/wrflowinp_d01   wrflowinp_d01
fi

# Add prime terms to ensemble member to get final forcings
if [ ${3} == "wrf_coarse" ]; then
  echo "Running add: wrfinput_d01"
  ncadd wrfinput_d01 ${emdir}/${3}/wrfinput_d01_prm    wrfinput_d01_final
  echo "Running add: wrfbdy_d01"
  ncadd wrfbdy_d01 ${emdir}/${3}/wrfbdy_d01_prm      wrfbdy_d01_final
  echo "Running add: wrffdda_d01"
  ncadd wrffdda_d01 ${emdir}/${3}/wrffdda_d01_prm wrffdda_d01_final
fi
echo "Running add: wrflowinp_d01"
ncadd wrflowinp_d01 ${emdir}/${3}/wrflowinp_d01_prm   wrflowinp_d01_final
" >> ${1}
}
############################################################################


if [ "$do_ens_mean" = true ]; then

  # Create ensemble mean directory
  mkdir -p ${emdir}
  mkdir -p ${emdir}/wrf_coarse
  mkdir -p ${emdir}/wrf_fine
  cd ${emdir}

  # Create PBS script to get ensemble mean
  cd wrf_coarse
  batch_file="calc_ens_mean_coarse.sh"
  qsub_file_ensmean ${batch_file} "wrf_coarse"
  qsub ${batch_file}

  cd ../wrf_fine
  batch_file="calc_ens_mean_fine.sh"
  qsub_file_ensmean ${batch_file} "wrf_fine"
  qsub ${batch_file}

else

# Loop over ensemble members
for em in $(seq -w 01 $nmem); do # Ensemble member

  memb_dir="$scdir/memb_${em}/ctl"

  cd $memb_dir
  mkdir -p enspert
  mkdir -p enspert/wrf_coarse
  cd enspert/wrf_coarse
  batch_file="calc_perturbations_coarse.sh"
  qsub_file_final ${batch_file} "memb_${em}_coarse" "wrf_coarse"
  qsub ${batch_file}

  cd $memb_dir
  mkdir -p enspert/wrf_fine
  cd enspert/wrf_fine
  batch_file="calc_perturbations_fine.sh"
  qsub_file_final ${batch_file} "memb_${em}_fine" "wrf_fine"
  qsub ${batch_file}

done

fi

echo "Done!!"

exit
