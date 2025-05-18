# Script to post-process high-resolution WRF model output.
# 
# Major tasks include computing the following for selected variables:
#   1. domain-averages to produce time series
#   2. vertical integrals
#   3. pressure-level vertical interpolation
# 
# This script leverages the CDO (https://code.mpimet.mpg.de/projects/cdo/) module via
# subprocess (executes as a terminal command) to generate basic time series, which helps
# for checking for RCE. This should be available either by loading as a module or
# installing into the conda/mamba kernel you're running.
# 
# James Ruppert
# jruppert@ou.edu
# 11/2/2024

import numpy as np
from post_proc_functions import *
import os
import xarray as xr

# Post-processing for each test needs to follow the below sequence:

# Basic 2D variables - takes 06:00 (HH:MM) for 4 days of data
do_2d_vars = False # Set select=10:ncpus=1:mpiprocs=1:ompthreads=1

# 2D ACRE variables - takes 00:45 (HH:MM) for 4 days of data
do_acre = True # Set select=1:ncpus=8:mpiprocs=8:ompthreads=1

# Rainrate - takes 00:05 (HH:MM) for 4 days of data
do_rainrate = False # Set select=10:ncpus=1:mpiprocs=1:ompthreads=1

# Reflectivity (lowest model level)
do_refl = False # Set select=1:ncpus=1:mpiprocs=1:ompthreads=1

# Special variables (includes 3D variables)
#  SLP takes 05:00 (HH:MM) for 4 days of data
#  AVO takes 09:25 (HH:MM) for 4 days of data
do_special_vars = False # Set select=10:ncpus=1:mpiprocs=1:ompthreads=1

########################################################
# Directories and test selection
########################################################

case = "nepartak"
test_process = "ctl"
# test_process = "ncrf12h"

# CTL start/end times
t0_ctl = np.datetime64('2016-07-02T00:00:00')
t1_ctl = np.datetime64('2016-07-06T00:00:00')

wrf_dom = "wrf_fine"
nmem = 10 # number of ensemble members

npd_override = 24*3

# Data directory
# Scratch
# datdir = "/glade/derecho/scratch/ruppert/piccolo/"
# Campaign storage
datdir = "/glade/campaign/univ/uokl0049/"

# Ens-member string tags (e.g., memb_01, memb_02, etc.)
memb0=1 # Starting member to read
memb_nums_str=np.arange(memb0,nmem+memb0,1).astype(str)
nustr = np.char.zfill(memb_nums_str, 2)
memb_all=np.char.add('memb_',nustr)

# Function to get date tag for output files
def get_datetag(datetime):
    # string = np.datetime_as_string(datetime, unit='h').replace("-","").replace(" ","").replace(":","")
    string = np.datetime_as_string(datetime, unit='m').replace("-","").replace(" ","").replace(":","")
    return string

########################################################
# Use CDO to process basic 2D variables
########################################################

if do_2d_vars:

    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    nproc = comm.Get_size()

    # Get variable list
    vars2d = var_list_2d()

    memb_dir = memb_all[comm.rank]
    # for memb_dir in memb_all:

    print("Processing basic 2D variables for "+memb_dir)

    # for ivar in vars2d:
    for ivar in vars2d[5:]:
    # ivar = comm.rank

        varname_str = ivar.upper()
        print("Processing "+varname_str)

        outdir, wrffiles, nfiles, npd = memb_dir_settings(datdir, case, test_process, wrf_dom, memb_dir)
        cdo_merge_wrf_variable(outdir, wrffiles, varname_str)

        # comm.barrier()

    print("Done writing out 2D basic variables for "+memb_dir)

########################################################
# Get reflectivity (lowest level)
########################################################

if do_refl:

    # memb_dir = memb_all[comm.rank]
    for memb_dir in memb_all:
    # for memb_dir in memb_all[-1:]:

        print("Processing reflectivity for "+memb_dir)

        varname_str = 'REFL_10CM'
        outdir, wrffiles, nfiles, npd = memb_dir_settings(datdir, case, test_process, wrf_dom, memb_dir)
        cdo_merge_wrf_variable(outdir, wrffiles, varname_str)

        # comm.barrier()

    print("Done writing out 2D basic variables")

########################################################
# Use CDO to generate ACRE
########################################################

if do_acre:

    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    nproc = comm.Get_size()

    for memb_dir in memb_all:

        outdir, wrffiles, nfiles, npd = memb_dir_settings(datdir, case, test_process, wrf_dom, memb_dir)

        # Remove first if exists
        operation_str = 'rm -rf '+outdir+'LWacre.nc '+outdir+'SWacre.nc'
        process = subprocess.Popen(operation_str, shell=True, universal_newlines=True)
        # runshell(operation_str)

        if comm.rank == 0:
            operation_str = 'cdo sub '+outdir+'LWUPT.nc '+outdir+'LWDNT.nc '+outdir+'lw_t.nc'
        if comm.rank == 1:
            operation_str = 'cdo sub '+outdir+'LWUPB.nc '+outdir+'LWDNB.nc '+outdir+'lw_b.nc'
        if comm.rank == 2:
            operation_str = 'cdo sub '+outdir+'LWUPTC.nc '+outdir+'LWDNTC.nc '+outdir+'lw_tC.nc'
        if comm.rank == 3:
            operation_str = 'cdo sub '+outdir+'LWUPBC.nc '+outdir+'LWDNBC.nc '+outdir+'lw_bC.nc'
        if comm.rank == 4:
            operation_str = 'cdo sub '+outdir+'SWUPT.nc '+outdir+'SWDNT.nc '+outdir+'sw_t.nc'
        if comm.rank == 5:
            operation_str = 'cdo sub '+outdir+'SWUPB.nc '+outdir+'SWDNB.nc '+outdir+'sw_b.nc'
        if comm.rank == 6:
            operation_str = 'cdo sub '+outdir+'SWUPTC.nc '+outdir+'SWDNTC.nc '+outdir+'sw_tC.nc'
        if comm.rank == 7:
            operation_str = 'cdo sub '+outdir+'SWUPBC.nc '+outdir+'SWDNBC.nc '+outdir+'sw_bC.nc'

        process = subprocess.Popen(operation_str, shell=True, universal_newlines=True)
        process.wait()
        # runshell(operation_str)

        comm.barrier()

        if comm.rank == 0:
            operation_str = 'cdo sub '+outdir+'lw_b.nc '+outdir+'lw_t.nc '+outdir+'lw_net.nc'
        if comm.rank == 1:
            operation_str = 'cdo sub '+outdir+'lw_bC.nc '+outdir+'lw_tC.nc '+outdir+'lw_netC.nc'
        if comm.rank == 2:
            operation_str = 'cdo sub '+outdir+'sw_b.nc '+outdir+'sw_t.nc '+outdir+'sw_net.nc'
        if comm.rank == 3:
            operation_str = 'cdo sub '+outdir+'sw_bC.nc '+outdir+'sw_tC.nc '+outdir+'sw_netC.nc'

        if comm.rank < 4:
            process = subprocess.Popen(operation_str, shell=True, universal_newlines=True)
            process.wait()
            # runshell(operation_str)
        comm.barrier()

        # Calculate the longwave ACRE
        if comm.rank == 0:
            operation_str = 'cdo sub '+outdir+'lw_net.nc '+outdir+'lw_netC.nc '+outdir+'LWacre.nc'
        # Calculate the shortwave ACRE
        if comm.rank == 1:
            operation_str = 'cdo sub '+outdir+'sw_net.nc '+outdir+'sw_netC.nc '+outdir+'SWacre.nc'

        if comm.rank < 2:
            process = subprocess.Popen(operation_str, shell=True, universal_newlines=True)
            process.wait()
            # runshell(operation_str)
        comm.barrier()

        # Delete unneeded files
        if comm.rank == 0:
            for operation_str in [
                'rm -rf '+outdir+'LWD*.nc '+outdir+'LWUPTC.nc '+outdir+'LWUPB*.nc',
                'rm -rf '+outdir+'SWU*nc '+outdir+'SWD*nc',
                'rm -rf '+outdir+'lw_t.nc '+outdir+'lw_b.nc '+outdir+'lw_tC.nc '+outdir+'lw_bC.nc',
                'rm -rf '+outdir+'sw_t.nc '+outdir+'sw_b.nc '+outdir+'sw_tC.nc '+outdir+'sw_bC.nc',
                # 'rm -rf '+outdir+'lw_net.nc '+outdir+'lw_netC.nc '+outdir+'sw_net.nc '+outdir+'sw_netC.nc',
                'rm -rf '+outdir+'*.log',
            ]:
                process = subprocess.Popen(operation_str, shell=True, universal_newlines=True)

    print("Done writing out ACRE variables")

########################################################
# Loop over ensemble members to calculate rainrate
########################################################

if do_rainrate:

    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    nproc = comm.Get_size()
    print("Rank "+str(comm.rank))

    # for memb_dir in memb_all:
    memb_dir = memb_all[comm.rank]

    print("Processing rainrate for "+memb_dir)

    outdir, wrffiles, nfiles, npd = memb_dir_settings(datdir, case, test_process, wrf_dom, memb_dir)

    ds = xr.open_dataset(outdir+'RAINNC.nc')
    rainnc = ds['RAINNC'].copy(deep=True)
    ds.close()
    # Get rainrate
    # rainrate = calculate_rainrate(rainnc, npd)
    rainrate = calculate_rainrate(rainnc, npd_override)
    # Write out
    var_name='rainrate'
    write_ncfile(outdir, rainrate, var_name)

    print("Done writing out rainrate for "+memb_dir)

########################################################
# Loop over ensemble members to process special variables
# (including all 3D variables)
########################################################

if do_special_vars:

    # Define time period to process 3D variables
    # t0 = np.datetime64('2024-09-02T00:00:00')
    # t1 = np.datetime64('2024-09-03T00:00:00')
    # t1 = np.datetime64('2024-09-02T00:40:00')
    # Use full record
    t0 = t0_ctl
    t1 = t1_ctl
    # t1 = t0 + np.timedelta64(60, 'm')

    # Set to True to append to existing file
    do_append = False

    # t0_str = get_datetag(t0)
    # t1_str = get_datetag(t1)
    tag_extra = ''#'_'+t0_str+'-'+t1_str

    # Define new output pressure levels
    dp=50
    new_p_levels=np.arange(1000,0,-dp)
    # new_p_levels=np.array([500,400])
    # For AVOR for tracking
    # avor_plevels=np.array([850,800,750,700,650,600])
    avor_plevels=np.arange(1000,600-dp,-dp)

    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    nproc = comm.Get_size()

    # Get variable list
    var_list = var_list_special()

    # for memb_dir in memb_all:
    memb_dir = memb_all[comm.rank]

    # for test_process in ["ctl", "ncrf12h"]:

    outdir, wrffiles, nfiles, npd = memb_dir_settings(datdir, case, test_process, wrf_dom, memb_dir)

    # for ivar_str in var_list[1]:
    ivar_str = 'slp'

    print("Processing "+ivar_str+" for "+memb_dir)

    # Set special pressure levels
    if ivar_str == 'avo':
        p_levels=avor_plevels
    else:
        p_levels=new_p_levels

    # Determine 2D or 3D
    if ivar_str == 'slp' or ivar_str == 'pclass' or ivar_str == 'pw' or \
        ivar_str == 'vmf' or ivar_str == 'pw_sat':
        tag2d = '2D'
    else:
        tag2d = '3D'

    # Read in variable from WRF files

    file_out = outdir+ivar_str+tag_extra+'.nc'
    if do_append and os.path.exists(file_out):
        # If file exists, open and load contents
        print("File already exists, loading contents...")
        ds = xr.open_dataset(file_out)
        xtime_read = ds['Time'].copy(deep=True).values
        var_alltime = ds[ivar_str].copy(deep=True)
        ds.close()
    else:
        # Create empty array
        xtime_read = np.array([], dtype='datetime64[s]')
        var_alltime = None

    for ifile in range(nfiles):

        # Open the WRF file
        wrffile = wrffiles[ifile]

        # Get variables for entire file
        var_ifile, xtime_read = get_vars_ifile_special(wrffile, ivar_str, xtime_read, t0, t1, tag=tag2d, new_p_levels=p_levels)
        # Check if dictionary is empty
        if var_ifile is None:
            continue

        # Concatenate variable
        try:
            var_alltime = xr.concat((var_alltime, var_ifile), 'Time')
        except:
            var_alltime = var_ifile.copy(deep=True)

        # Add multiple write-out steps to avoid complete loss after long job
        if (ifile == 2) or ((ifile+1) % 20) == 0: # after 2 steps and every 20 steps
            # Write out the variables
            write_ncfile(outdir, var_alltime, ivar_str, tag_extra=tag_extra)

    # Remove duplicate time steps
    # vars_alltime[ivar_str] = vars_alltime[ivar_str].drop_duplicates(dim="Time", keep='first')
    # Write out the variables
    write_ncfile(outdir, var_alltime, ivar_str, tag_extra=tag_extra)

    print("Done writing out "+ivar_str+" for "+memb_dir)