#!/bin/bash

test_name0='ctl'

# storm="haiyan"
# test_name1='ncrf36h'
# rst_tag="_2013-11-04_00:00:00"

storm="maria"
test_name1='ncrf48h'
rst_tag="_2017-09-17_12:00:00"

#test_name='ncrf'
#test_name='wsm6'

# Directories
outdir=$scratch/tc_ens
indir=$scratch/temptc

# All
#for em in 0{1..9} {10..20}; do # Ensemble member
for em in 0{1..9} 10; do # Ensemble member
# for em in 01; do # Ensemble member

  cd $outdir/$storm

  memdir="memb_${em}"
  mkdir -p $memdir
  cd $memdir

  # CTL ICs/BCs
  mkdir -p $test_name0
  cd $indir/$storm/$memdir/$test_name0/
  mv wrfinput* wrflow* wrfbd* $outdir/$storm/$memdir/$test_name0/

  cd $outdir/$storm/$memdir

  # NCRF restart
  mkdir -p $test_name1
  cd $indir/$storm/$memdir/$test_name1/
  mv wrfrst_d0*${rst_tag} $outdir/$storm/$memdir/$test_name1/

done

exit
