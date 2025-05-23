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
# DATE1=20160701
# DATE2=20160704
DATE1=20160705
DATE2=20160707

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

YY='"year": ['
for i in $(seq -f "%04g" $YY1 $YY2); do
  YY+='"'$i'", '
done
# Remove the trailing comma and space, then add the closing bracket
YY=${YY%, }']'

MM='"month": ['
for i in $(seq -f "%02g" $MM1 $MM2); do
  MM+='"'$i'", '
done
# Remove the trailing comma and space, then add the closing bracket
MM=${MM%, }']'

DD='"day": ['
for i in $(seq -f "%02g" $DD1 $DD2); do
  DD+='"'$i'", '
done
# Remove the trailing comma and space, then add the closing bracket
DD=${DD%, }']'

# sed -e "s/YY/${YY}/g;s/MM/${MM}/g;s/DD/${DD}/g;s/Nort/${Nort}/g;s/West/${West}/g;s/Sout/${Sout}/g;s/East/${East}/g;s/DATE1/${DATE1}/g;s/DATE2/${DATE2}/g;" GetERA5-sl.py > GetERA5-${DATE1}-${DATE2}-sl.py
# sed -e "s/YY/${YY}/g;s/MM/${MM}/g;s/DD/${DD}/g;s/Nort/${Nort}/g;s/West/${West}/g;s/Sout/${Sout}/g;s/East/${East}/g;s/DATE1/${DATE1}/g;s/DATE2/${DATE2}/g;" GetERA5-pl.py > GetERA5-${DATE1}-${DATE2}-pl.py

sed -e "s/YY/${YY}/g;s/MM/${MM}/g;s/DD/${DD}/g;s/DATE1/${DATE1}/g;s/DATE2/${DATE2}/g;" GetERA5-ens-sl.py > GetERA5-${DATE1}-${DATE2}-ens-sl.py
sed -e "s/YY/${YY}/g;s/MM/${MM}/g;s/DD/${DD}/g;s/DATE1/${DATE1}/g;s/DATE2/${DATE2}/g;" GetERA5-ens-pl.py > GetERA5-${DATE1}-${DATE2}-ens-pl.py

python GetERA5-${DATE1}-${DATE2}-ens-sl.py
python GetERA5-${DATE1}-${DATE2}-ens-pl.py

