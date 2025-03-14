#!/bin/bash
# Script to run WPS for each ERA5 ensemble member.

scdir="/glade/derecho/scratch/ruppert/tc-crfrad/bcsics/ensemble_members"
wpsdir="${scdir}/WPS"

nens=10
# nens=2

for i in $(seq 1 $nens); do

    echo "Processing member $i"

    memb_dir="${scdir}/$(printf "memb_%02d" $i)"
    cd $memb_dir

    # mkdir -p grib
    # mkdir -p met_em
    # mv *.grib grib/

    # cp -r $wpsdir .
    cd WPS
    rm -f GRIBFILE*
    ./link_grib.csh "../grib/*grib"
    # ./ungrib.exe
    # rm -f GRIBFILE*
    # ./metgrid.exe
    # rm -f FILE*
    # mv met_em* $memb_dir

# Put the following text into a new text file

cat > run_wps_era5ens.sh << EOF
#!/bin/bash
#PBS -N $(printf "memb_%02d" $i)
#PBS -A UOKL0049
#PBS -l walltime=12:00:00
#PBS -q main
#PBS -j oe
#PBS -k eod
### Select n nodes with 64 CPUs each for a total of n*64 MPI processes
#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1

export TMPDIR=/glade/derecho/scratch/$USER/temp
mkdir -p $TMPDIR

# /bin/cp ../bashrc_wrf_der bashrc_wrf
source bashrc_wrf_der

# ./link_grib.csh ../grib/*grib
./ungrib.exe
rm -f GRIBFILE*
./metgrid.exe
rm -f FILE*
mv met_em* ../met_em/

EOF

    qsub run_wps_era5ens.sh

done

echo "Done!!"
