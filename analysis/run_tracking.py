# Python script to run and save vortex tracking from WRF TC output
# 
# James Ruppert  
# jruppert@ou.edu  
# September 2022

import numpy as np
from object_track import *
from read_wrf_functions import *
from mpi4py import MPI

comm = MPI.COMM_WORLD
nproc = comm.Get_size()

########################################################
# Track options
########################################################

# var_tag = 'avor'
var_tag = 'avor_850-600'

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

########################################################
# Functions
########################################################

# Function to account for crossing of the Intl Date Line
def dateline_lon_shift(lon_in, reverse):
    if reverse == 0:
        lon_offset = np.zeros(lon_in.shape)
        lon_offset[np.where(lon_in < 0)] += 360
    else:
        lon_offset = np.zeros(lon_in.shape)
        lon_offset[np.where(lon_in > 180)] -= 360
    # return lon_in + lon_offset
    return lon_offset

def write_track_nc(file_out, nt, track, clon_offset):
    ncfile = Dataset(file_out,mode='w')

    time_dim = ncfile.createDimension('time', nt) # unlimited axis (can be appended to).

    clat = ncfile.createVariable('clat', np.float64, ('time',))
    clat.units = 'degrees_north'
    clat.long_name = 'clat'
    clat[:] = track[1,:]

    clon = ncfile.createVariable('clon', np.float64, ('time',))
    clon.units = 'degrees_east'
    clon.long_name = 'clon'
    clon[:] = track[0,:] + clon_offset

    ncfile.close()
    return

########################################################
# Prepare and call tracking
########################################################

# For initializing tracks in sensitivity tests
if test_process == 'ctl':
    i_senstest=False
else:
    i_senstest=True

# Sensitivity tests basis and time step from that basis
if test_process == 'ncrf36h':
    test_basis='ctl'
    it_basis=36
elif test_process == 'ncrf48h':
    test_basis='ctl'
    it_basis=48
else:
    test_basis=''

# Get dimensions
memb_dir = memb_all[comm.rank]
outdir, postproc_files, nt, nx, ny = get_postproc_dims(datdir, case, test_process, wrf_dom, memb_dir)
file_read = Dataset(outdir+'avo.nc')
lon = file_read.variables['XLONG'][:,:]
lat = file_read.variables['XLAT'][:,:]
file_read.close()

if (lon.min() < 0) and (lon.max() > 0):
    lon_offset = dateline_lon_shift(lon, reverse=0)
else:
    lon_offset = 0

# for imemb in range(nmem):
# for imemb in range(1):
imemb = comm.rank

print("Running tracking for member "+str(imemb))

# Prepare variable to use for tracking
if var_tag == 'avor':

    # Level selection
    ptrack  = 850 # tracking pressure level [hPa]
    ikread = np.where(pres == ptrack)[0][0]

    track_file_tag = var_tag+'_'+str(round(pres[ikread]))+'hPa'

    # Read variable
    fil = Dataset(datdir+'AVOR.nc') # this opens the netcdf file
    var = fil.variables['AVOR'][:,ikread,:,:] # 10**-5 /s
    fil.close()

elif var_tag == 'avor_850-600':

    track_file_tag = var_tag

    fil = Dataset(outdir+'avo.nc')
    pres = fil.variables['interp_level'][:] # hPa
    ikread = np.where((pres <= 850) & (pres >=600))[0]
    avor = fil.variables['avo'][:,ikread,:,:] # 10**-5 /s
    fil.close()
    var = np.mean(avor, axis=1)
    print("var shape: ", np.shape(var))

nt=np.shape(var)[0]

# Set basis starting point for tracking for sensitivity tests
if i_senstest:
    track_file = outdir+'../../'+test_basis+'/wrf_fine/post_proc/track_'+track_file_tag+'.nc'
    ncfile = Dataset(track_file)
    clon = ncfile.variables['clon'][it_basis] # deg
    clat = ncfile.variables['clat'][it_basis] # deg
    ncfile.close()
    basis = [clon, clat]
else:
    basis=0

# Run tracking
track, f_masked = object_track(var, lon + lon_offset, lat, i_senstest, basis)

clon=track[0,:]
clon_offset = dateline_lon_shift(clon, reverse=1)
# clat=track[1,:]

# Write out to netCDF file
file_out = outdir+'track_'+track_file_tag+'.nc'
write_track_nc(file_out, nt, track, clon_offset)

print("Done with tracking for member "+str(imemb)+'!!')
