#!/bin/bash -l
expn="CTL/TC_3km/"
dir="/glade/campaign/mmm/dpm/rberrios/glade_scratch/MPAS_APE/aqua_sstmax10N_ASD/${expn}/"

cd $dir

for filename in diag.2000-??-??_{00,06,12,18}.00.00.nc; do ##cmpr_diag*06.00.00.nc cmpr_diag*12.00.00.nc cmpr_diag*18.00.00.nc; do

  #get date info for adding time variable and finding history file
  filename_date="$(cut -d'.' -f2 <<< $filename)"
  ofile="waterPaths.${filename_date}.00.00.nc"
  echo $ofile

  # check if it exists
  if test -f "$ofile"; then echo "$ofile exists."; continue; fi

  # if it doesn't, then proceed with calculation in a separate bash job

  cat << EOF > job.sh 
#!/bin/bash -l
### Job Name
#PBS -N job 
### Charging account
#PBS -A NMMM0004 
### Request one chunk of resources with 1 CPU and 10 GB of memory
#PBS -l select=1:ncpus=1:mem=100GB
### Allow job to run up to 30 minutes
#PBS -l walltime=06:00:00
### Route the job to the casper queue
#PBS -q casper
### Join output and error streams into single file
#PBS -j oe

export TMPDIR=/glade/scratch/$USER/temp
mkdir -p $TMPDIR

module load cdo
module load nco

date

tmp="tmp_${filename}"

##echo "extracting 3D fields"
ncks -O -4 --cnk_dmn nCells,100 -v rho,qc,qg,qs,qi,qr -d nVertLevels,0,51 ${filename} \${tmp}

#add dz
ncks -A -v dz,z -d nVertLevels,0,51 z.nc \${tmp} 

#calculate vertical integrals; these are our water paths
##echo "calculating cloud water path - in thompson, this is qc+qi+qs"
##ncap2 -A -4 --cnk_dmn nCells,100 -v -s 'clwvi=(float(rho*dz*(qc+qi+qs))).total(\$nVertLevels);' \${tmp} \${tmp}

echo "calculating LWP..."
### liquid water path
ncap2 -A -4 --cnk_dmn nCells,100 -v -s 'lwp=(float(rho*dz*(qr+qc))).total(\$nVertLevels);' \${tmp} \${tmp}

### ice water path
echo "calculating IWP..."
ncap2 -A -4 --cnk_dmn nCells,100 -v -s 'iwp=(float(rho*dz*(qi+qs+qg))).total(\$nVertLevels);' \${tmp} \${tmp}

### column integrated graupel and rain
echo "calculating GWP..."
ncap2 -A -4 --cnk_dmn nCells,100 -v -s 'gwp=(float(rho*dz*(qg))).total(\$nVertLevels);' \${tmp} \${tmp}
echo "calculating RWP..."
ncap2 -A -4 --cnk_dmn nCells,100 -v -s 'rwp=(float(rho*dz*(qr))).total(\$nVertLevels);' \${tmp} \${tmp}

echo "cleaning up..."
### lastly save the ratio of iwp/lwp to find convective vs stratiform
##ncap2 -A --cnk_dmn nCells,100 -v -s 'CR=iwp;where(lwp<=0.1)CR=0;where(lwp>0.1)CR=float(iwp/lwp);' \${tmp} \${tmp}

### finally clean up
ncks -O -v gwp,rwp,lwp,iwp \${tmp} ${ofile}

### delete temporary file
rm -f \${tmp}

echo "ALL DONE!"
EOF
  qsub job.sh
done
