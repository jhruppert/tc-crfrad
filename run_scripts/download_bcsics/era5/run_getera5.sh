#!/bin/bash -l
#PBS -N getera
#PBS -A UOKL0049
#PBS -l walltime=12:00:00
#PBS -q casper@casper-pbs
#PBS -j oe
#PBS -k eod
### Select n nodes with a max of 36 CPUs per node for a total of n*36 MPI processes
#PBS -l select=1:ncpus=1:mem=1GB

source ~/.bashrc
mamba activate cdsapi

# Start/end dates

# Nepartak
# DATE1=20160701
# DATE2=20160706

# Maria
# DATE1=20170915
# DATE2=20170920

# Ike
# DATE1=20080831
# DATE2=20080905

# Hector
DATE1=20180730
DATE2=20180805


# Geographical bounds
# Nort=20
# West=-40
# Sout=-5
# East=-10

YY1=`echo $DATE1 | cut -c1-4`
MM1=`echo $DATE1 | cut -c5-6`
DD1=`echo $DATE1 | cut -c7-8`
YY2=`echo $DATE2 | cut -c1-4`
MM2=`echo $DATE2 | cut -c5-6`
DD2=`echo $DATE2 | cut -c7-8`

sed -e "s/DATE-1/"${YY1}-${MM1}-${DD1}"/g;s/DATE-2/"${YY2}-${MM2}-${DD2}"/g;s/DATE1/${DATE1}/g;s/DATE2/${DATE2}/g;" GetERA5-sl.py > GetERA5-${DATE1}-${DATE2}-sl.py
sed -e "s/DATE-1/"${YY1}-${MM1}-${DD1}"/g;s/DATE-2/"${YY2}-${MM2}-${DD2}"/g;s/DATE1/${DATE1}/g;s/DATE2/${DATE2}/g;" GetERA5-pl.py > GetERA5-${DATE1}-${DATE2}-pl.py

python GetERA5-${DATE1}-${DATE2}-sl.py
python GetERA5-${DATE1}-${DATE2}-pl.py

