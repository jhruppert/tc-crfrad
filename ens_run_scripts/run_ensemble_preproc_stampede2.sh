#!/bin/bash
#SBATCH --job-name=preproc
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=128
#SBATCH --partition=compute
#SBATCH -t 02:00:00 # runtime
#SBATCH --output=out_ens_prepoc.%j
#SBATCH --account=pen116

# This script prepares all ensemble members and runs pre-processing

storm='haiyan'
#storm='maria'

# Directories
home=${HOME}/ensemble-tropical-cyclone-cases
wpsdir=$home/WPS
maindir=${SCRATCH}/tc_ens
ensdir=$maindir/$storm
gefsdir=${WORK}/gefs/$storm
srcfile=$home/bashrc_wrf

source $srcfile

mkdir -p $ensdir
cd $ensdir

# Run pre-processing for each member

#for em in 0{1..9} {10..20}; do # Ensemble member
for em in 0{1..9} 10; do # Ensemble member
#for em in 0{5..9} 10; do # Ensemble member
#for em in 01; do # Ensemble member

  dir="memb_${em}"
  mkdir -p $dir
  cd $dir

  echo "WORKING ON MEMBER: "${em}

  #LINK FILES

    mkdir -p wps
    cd wps

    #WPS files
    cp $srcfile .
    cp ${home}/namelists/namelist.wps.${storm} ./namelist.wps
    ln -sf ${wpsdir}/geo_em.d01.nc.${storm} geo_em.d01.nc
    ln -sf ${wpsdir}/geo_em.d02.nc.${storm} geo_em.d02.nc
    ln -sf ${wpsdir}/ungrib.exe .
    ln -sf ${wpsdir}/metgrid.exe .
    ln -sf ${wpsdir}/METGRID.TBL .
    ln -sf ${wpsdir}/Vtable .
  
    #GEFS files
    #This links gens-a* and gens-b* files, which have different variables
    ${wpsdir}/link_grib.csh ${gefsdir}/gens-*_${em}.grb2

  #RUN WPS

    ./ungrib.exe > ungrib.out 2>&1
    ./metgrid.exe > metgrid.out 2>&1

  cd ..

  #SET UP WRF DIRECTORY

    mkdir -p wrf
    cd wrf

    ln -sf ../wps/met_em* .

  cd ../../

done

