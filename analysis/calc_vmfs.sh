#!/bin/bash -l
# expn="CTL/TC_3km/"
# expn="HOMO_RAD/TC_3km/"
# expn="CLIM_RAD/TC_3km/"

# dir="/glade/campaign/mmm/dpm/rberrios/glade_scratch/MPAS_APE/aqua_sstmax10N_ASD/CTL/TC_3km/"
dir="/glade/campaign/mmm/dpm/rberrios/glade_scratch/MPAS_APE/aqua_sstmax10N_ASD/HOMO_RAD/TC_3km/"
# dir="/glade/derecho/scratch/rberrios/MPAS_APE/aqua_sstmax10N/CLIM_RAD/TC_3km/"

expn=$(echo "$dir" | awk -F'/' '{print $(NF-2)}')
echo $expn

dir_out="/glade/derecho/scratch/ruppert/tc-crfrad/mpas/${expn}/"
mkdir -p $dir_out

cd $dir_out

# for day in $(seq -w 01 11); do
day=11
  for hour in 00 06 12 18; do
    filename="diag.2000-05-${day}_${hour}.00.00.nc"

# for filename in diag.2000-05-0?_{00,06,12,18}.00.00.nc; do
# filename=diag.2000-05-04_00.00.00.nc

    echo "Processing $filename"

  #get date info for adding time variable and finding history file
  filename_date="$(cut -d'.' -f2 <<< $filename)"
  # ofile="waterPaths.${filename_date}.00.00.nc"
  ofile="${dir_out}vmfs.${filename_date}.00.00.nc"
  echo $ofile

  # check if it exists
  if test -f "$ofile"; then echo "$ofile exists."; continue; fi

  # if it doesn't, then proceed with calculation in a separate bash job

  cat << EOF > job.sh 
#!/bin/bash -l
### Job Name
#PBS -N job 
### Charging account
#PBS -A UOKL0049
### Request one chunk of resources with 1 CPU and 10 GB of memory
#PBS -l select=1:ncpus=1:mem=100GB
### Allow job to run up to 30 minutes
#PBS -l walltime=01:00:00
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
ncks -O -4 --cnk_dmn nCells,100 -v rho -d nVertLevels,0,51 ${dir}${filename} \${tmp}
ncks -A -4 --cnk_dmn nCells,100 -v w -d nVertLevelsP1,0,52 ${dir}${filename} \${tmp}

#add dz
ncks -A -4 -v dz,z -d nVertLevels,0,51 /glade/campaign/mmm/dpm/rberrios/glade_scratch/MPAS_APE/aqua_sstmax10N_ASD/CTL/TC_3km/z.nc \${tmp} 

echo "destaggering w"
ncap2 -A -4 --cnk_dmn nCells,100 -v -s 'w_destag[Time,nCells,nVertLevels]=float((w(:,:,0:51)+w(:,:,1:52))/2.0)' \${tmp} \${tmp}

#Mu
echo "subsetting for positive values of w..."
ncap2 -A -4 --cnk_dmn nCells,100 -v -s 'w_up=w_destag; where(w_destag<0) w_up=0;' \${tmp} \${tmp}
#Md
echo "subsetting for negative values of w..."
ncap2 -A -4 --cnk_dmn nCells,100 -v -s 'w_dn=w_destag; where(w_destag>0) w_dn=0;' \${tmp} \${tmp}

### vertically integrate
echo "vertically integrating..."
ncap2 -A -4 --cnk_dmn nCells,100 -v -s 'md=(float(rho*dz*w_dn)).total(\$nVertLevels);' \${tmp} \${tmp}
ncap2 -A -4 --cnk_dmn nCells,100 -v -s 'mu=(float(rho*dz*w_up)).total(\$nVertLevels);' \${tmp} \${tmp}

### finally clean up
ncks -O -4 -v mu,md \${tmp} ${ofile}

### delete temporary file
rm -f \${tmp}

### Update metadata
ncatted -O -h -a long_name,mu,m,c,'Upward mass flux' ${ofile}
ncatted -O -h -a long_name,md,m,c,'Downward mass flux' ${ofile}
ncatted -O -h -a units,mu,m,c,'kg m^{-2} s^{-1}' ${ofile}
ncatted -O -h -a units,md,m,c,'kg m^{-2} s^{-1}' ${ofile}

echo "ALL DONE!"
EOF

    qsub job.sh

  done
# done