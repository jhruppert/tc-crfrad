#!/bin/bash

# Now running REAL and WRF fully separately using below switches

run_real=0
run_wrf=0
run_post_ncl=1
  post_depend=0 # for NCL only
#run_post_idl=0
  partition="radclouds"
#  partition="normal"

storm="haiyan"
storm="maria"
#  Main tests:
#    ncrf36h for Haiyan, ncrf48h for Maria
#    crfon60h for Haiyan, crfon72h for Maria

# Haiyan
test_name='ctl'
# test_name='ncrf36h'
# test_name='crfon60h'
# test_name='STRATANVIL_ON'
# test_name='STRATANVIL_OFF'
# test_name='STRAT_OFF'

# Maria
# test_name='ctl'
# test_name='ncrf48h'
# test_name='crfon72h'

# WRF simulation details
  jobname="${storm}_${test_name}"
  # Restart
    irestart=0
#    timstr='04:00' # HH:MM

# NCL settings
  # ncl_time="01:00" # For single variable
  ncl_time="06:00" # For all variables
  dom="d02"
  # Variable list
#    varstr="{1..3} {8..23} 25 {27..29} 32 33 {36..51}" # 53" # Full list
  # varstr="24" # Single var
  # varstr="36 37 38 39 40 41 42 43"
  varstr="13 14 15 21 22 27 28" # Vars for isentrop analysis
  # varstr="14 15" # Vars for isentrop analysis

###################################################

# Supercomputer-specific details
  system='oscer'
  if [[ ${system} == 'oscer' ]]; then
    queue='radclouds'
    bigN=7 # n node
    smn=56 # np per node
    nnodes=$((${smn}*${bigN}))
    submit="sbatch"
    mpiex="mpirun"
    wkdir=${HOME}/ensemble-tropical-cyclone-cases
    ensdir=${ourdisk}/tc_ens/${storm}
    # ensdir=${scratch}/tc_ens/${storm}
    ncl_module="NCL"
  elif [[ ${system} == 'cheyenne' ]]; then
    queue="regular"
    bigN=12 # n node
    smn=36 # np per node
    submit="qsub"
    mpiex="mpiexec_mpt"
    wkdir=${work}/ensemble-tropical-cyclone-cases
    ensdir=${scratch}/tc_ens/${storm}
    ncl_module="ncl"
  fi

  wrfdir=$wkdir/wrf_$test_name
  srcfile=bashrc_wrf_${system}
  srcpath=$wkdir/env/$srcfile

###################################################

# Storm-specific settings
  if [[ ${storm} == 'maria' ]]; then

  # WRF simulation details
    test_t_stamp="2017-09-14_00:00:00"
    timstr='10:00' #'22:00' # HH:MM Job run time
      # Set to 22h for 7 d of Maria
  # NCL settings
    start_date="201709140000" # Start date for NCL
    ndays=4
  # Mechanism denial tests
#    if [[ ${test_name} == 'ncrf' ]]; then
    if [[ ${test_name} == 'ncrf36h' ]]; then
      timstr='05:00' # HH:MM Job run time
      test_t_stamp="2017-09-15_12:00:00"
      start_date="201709151200" # Start date for NCL
      ndays=1
      restart_base='ctl'
    elif [[ ${test_name} == 'ncrf48h' ]]; then
      timstr='05:00' # HH:MM Job run time
      test_t_stamp="2017-09-16_00:00:00"
      start_date="201709160000" # Start date for NCL
      ndays=2
      restart_base='ctl'
#test_t_stamp="2017-09-17_00:00:00"
#restart_base=${test_name}
    elif [[ ${test_name} == 'crfon72h' ]]; then
      timstr='05:00' # HH:MM Job run time
      test_t_stamp="2017-09-17_00:00:00"
      start_date="201709170000" # Start date for NCL
      ndays=0.5
      restart_base='ncrf48h'
    fi

  elif [[ ${storm} == 'haiyan' ]]; then

  # WRF simulation details
    test_t_stamp="2013-11-01_00:00:00"
    timstr='22:00' # HH:MM Job run time
      # 22h for 7 d of Haiyan
  # NCL settings
    start_date="201311010000" # Start date for NCL
    ndays=4
  # Mechanism denial tests
    if [[ ${test_name} == 'ncrf36h' ]]; then
      timstr='05:00' # HH:MM Job run time
      test_t_stamp="2013-11-02_12:00:00"
      start_date="201311021200" # For NCL
      ndays=2 # For NCL
      restart_base='ctl'
#test_t_stamp="2013-11-03_12:00:00"
#restart_base=${test_name}
    elif [[ ${test_name} == 'ncrf48h' ]]; then
      timstr='05:00' # HH:MM Job run time
      test_t_stamp="2013-11-03_00:00:00"
      start_date="201311030000" # Start date for NCL
      ndays=1
      restart_base='ctl'
    elif [[ ${test_name} == 'crfon60h' ]]; then
      timstr='05:00' # HH:MM Job run time
      test_t_stamp="2013-11-03_12:00:00"
      start_date="201311031200" # Start date for NCL
      ndays=0.5
      restart_base='ncrf36h'
    elif [[ ${test_name} == 'STRATANVIL_ON' ]] || [[ ${test_name} == 'STRATANVIL_OFF' ]] || [[ ${test_name} == 'STRAT_OFF' ]]; then
      timstr='10:00' # HH:MM Job run time
      test_t_stamp="2013-11-02_12:00:00"
      start_date="201311021200" # For NCL
      ndays=2 # For NCL
      restart_base='ctl'
    fi

  fi # Storm ID

cd $ensdir

# All
#for em in 0{1..9} {10..20}; do # Ensemble member
#for em in 0{1..9} 10; do # Ensemble member
# Special cases
for em in 0{1..9} 10; do # Ensemble member
#for em in 03; do # Ensemble member

  memdir="$ensdir/memb_${em}"
  mkdir -p $memdir
  testdir=$memdir/$test_name
  mkdir -p $testdir
  mkdir -p $testdir/wrf
  cd $testdir/wrf

  echo "Running: $testdir"

if [ $run_real -eq 1 ]; then

  ln -sf ${wrfdir}/run/* .

  cat ${wkdir}/namelists/var_extra_output > var_extra_output
  rm -f namelist.input
  cp ${wkdir}/namelists/namelist.input.wrf.${storm}.ctl ./namelist.input

  # Create REAL batch script
cat $wkdir/batch/header_${system}.txt > batch_real.job
cat << EOF >> batch_real.job


cp $srcpath .
source $srcfile .

${mpiex} ./real.exe

EOF

  # Fill in placeholders
  sed -i "s/QUEUE/${queue}/g" batch_real.job
  sed -i "s/JOBNAME/${jobname}/g" batch_real.job
  sed -i "s/EMM/${em}/g" batch_real.job
  sed -i "s/BIGN/1/g" batch_real.job
  sed -i "s/SMN/${smn}/g" batch_real.job
  if [[ ${system} == 'oscer' ]]; then
    sed -i "s/NNODES/${smn}/g" batch_real.job
  fi
  sed -i "s/TIMSTR/00:30/g" batch_real.job

  # Submit REAL job
  if [[ `grep SUCCESS rsl.error.0000 | wc -l` -eq 0 ]]; then
    ${submit} batch_real.job > submit_real_out.txt
  fi

fi

#  JOBID=$(grep Submitted submit_real_out.txt | cut -d' ' -f 4)


if [ $run_wrf -eq 1 ]; then

# Special case for data transfered from Expanse
  ln -sf ${wrfdir}/run/* .
  cat ${wkdir}/namelists/var_extra_output > var_extra_output
  rm -f namelist.input

  # Prep restart (only if running wrf.exe)
  if [ ${irestart} -eq 1 ]; then
    namelist=${wkdir}/namelists/namelist.input.wrf.${storm}.${test_name}.restart
  else
    namelist=${wkdir}/namelists/namelist.input.wrf.${storm}.${test_name}
  fi

  # Create WRF batch script
cat $wkdir/batch/header_${system}.txt > batch_wrf_${test_name}.job
cat << EOF >> batch_wrf_${test_name}.job

### SBATCH --dependency=afterany:${JOBID}

# Copy restart files and BCs from CTL if running mechanism denial test
if [[ ${test_name} == *'crf'* ]] || [[ ${test_name} == *'STRAT'* ]]; then
  ln -sf "$memdir/${restart_base}/wrfrst_d01_${test_t_stamp}" .
  ln -sf "$memdir/${restart_base}/wrfrst_d02_${test_t_stamp}" .
  ln -sf "$memdir/${restart_base}/wrfbdy_d01" .
  ln -sf "$memdir/${restart_base}/wrflowinp_d01" .
  ln -sf "$memdir/${restart_base}/wrflowinp_d02" .
  # mv "../wrfrst_d01_2013-11-03_12:00:00" .
  # mv "../wrfrst_d02_2013-11-03_12:00:00" .
fi

cp $srcpath .
source $srcfile .

cp ${namelist} ./namelist.input

# Modify NAMELIST for nproc specs
sed -i '/nproc_x/c\ nproc_x = 20,' namelist.input
sed -i '/nproc_y/c\ nproc_y = 19,' namelist.input

# Delete old text-out
rm rsl*
rm namelist.output

# Run WRF
${mpiex} ./wrf.exe

mkdir -p ../text_out
mkdir -p ../post
mkdir -p ../post/d01
mkdir -p ../post/d02
mv wrfout* wrfrst* ../
#mv rsl* 
mv namelist.out* out_wrf.* ../text_out/
cp namelist.input ../text_out/
if [[ ${test_name} == 'ctl' ]]; then
  mv wrfinput* wrfbdy* wrflow* ../
fi

EOF

  # Fill in placeholders
  sed -i "s/QUEUE/${queue}/g" batch_wrf_${test_name}.job
  sed -i "s/JOBNAME/${jobname}/g" batch_wrf_${test_name}.job
  sed -i "s/EMM/${em}/g" batch_wrf_${test_name}.job
  sed -i "s/BIGN/${bigN}/g" batch_wrf_${test_name}.job
  sed -i "s/SMN/${smn}/g" batch_wrf_${test_name}.job
  if [[ ${system} == 'oscer' ]]; then
    sed -i "s/NNODES/${nnodes}/g" batch_wrf_${test_name}.job
  fi
  sed -i "s/TIMSTR/${timstr}/g" batch_wrf_${test_name}.job

  # Submit WRF job
  # if [[ `grep SUCCESS rsl.error.0000 | wc -l` -eq 0 ]] then
    ${submit} batch_wrf_${test_name}.job > submit_wrf_out.txt
  # fi
  tail submit_wrf_out.txt

fi

cd ..

if [ $run_post_ncl -eq 1 ]; then

  # Prep NCL post-proc
  cp -raf ${wkdir}/postproc .
  cd postproc

  # Create NCL batch script
cat $wkdir/batch/header_${system}.txt > batch_ncl.sh
cat << EOF >> batch_ncl.sh

### SBATCH --dependency=afterany:

# source $srcfile
module purge
module load ${ncl_module}

dom="${dom}"

# Link first time step for mechanism denial tests for writing post-processed output
if [[ "${test_name}" == *'crf'* ]] || [[ "${test_name}" == *'STRAT'* ]]; then
  ln -sf $memdir/${restart_base}/wrfout_d0*_${test_t_stamp} ../
fi

# Modify NCL file
  sed -i "/Setdays/c\    nd=${ndays} ; Setdays" process_wrf.ncl
  sed -i '/Start time/c\    t0="'${start_date}'" ; Start time' process_wrf.ncl
  sed -i '/project directory/c\  dir=".." ; project directory' process_wrf.ncl

del=6 # number of nodes per ncl call

EOF

  if [ $post_depend -eq 1 ]; then
    # JOBID
    JOBID=$(grep Submitted ../wrf/submit_wrf_out.txt | cut -d' ' -f 4)
    sed -i "/dependency/c\#SBATCH --dependency=afterok:${JOBID}" batch_ncl.sh
  fi

  cat loop.sh >> batch_ncl.sh

  # Insert var list
  sed -i "/loopvars/c\for v in ${varstr}; do" batch_ncl.sh

  # Fill in placeholders
  sed -i "s/QUEUE/${queue}/g" batch_ncl.sh
  sed -i "s/JOBNAME/ncl/g" batch_ncl.sh
  sed -i "s/EMM/${em}/g" batch_ncl.sh
  sed -i "s/BIGN/1/g" batch_ncl.sh
  sed -i "s/SMN/${smn}/g" batch_ncl.sh
  if [[ ${system} == 'oscer' ]]; then
    sed -i "s/NNODES/${smn}/g" batch_ncl.sh
  fi
  sed -i "s/TIMSTR/${ncl_time}/g" batch_ncl.sh

  ${submit} batch_ncl.sh > submit_ncl_out.txt

fi

cd ../../

done

exit
