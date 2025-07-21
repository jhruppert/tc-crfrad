# Python script to run and save vortex tracking from WRF TC output
# 
# James Ruppert  
# jruppert@ou.edu  
# September 2022

import numpy as np
from object_track import *
from read_wrf_functions import *
from mpi4py import MPI
import sys

# Takes about 10 min to complete
comm = MPI.COMM_WORLD
nproc = comm.Get_size()

########################################################
# Track options
########################################################

# var_tag = 'avor'
# var_tag = 'avor_850-600'
# var_tag = 'slp'

# Input string at command line
var_tag = ' '.join(sys.argv[1:]) # Combine arguments into a string

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

# for imemb in range(nmem):
imemb = comm.rank

print("Running tracking using "+var_tag+" for member "+str(imemb))

outdir, postproc_files, nt, nx, ny, lon, lat = get_postproc_dims(datdir, case, test_process, wrf_dom, memb_all[imemb])

# Prepare variable to use for tracking
# if var_tag == 'avor':

#     # Level selection
#     ptrack  = 850 # tracking pressure level [hPa]
#     ikread = np.where(pres == ptrack)[0][0]

#     track_file_tag = var_tag+'_'+str(round(pres[ikread]))+'hPa'

#     # Read variable
#     fil = Dataset(datdir+'AVOR.nc') # this opens the netcdf file
#     var = fil.variables['AVOR'][:,ikread,:,:] # 10**-5 /s
#     fil.close()

if var_tag == 'slp':

    track_file_tag = var_tag

    ds = Dataset(outdir+'slp.nc')
    var = ds.variables['slp'][:,:,:] # hPa
    ds.close()

    # Flip sign of SLP since tracking locates field maxima
    var *= -1

elif var_tag == 'avor_850-600':

    # Tracking via vertically averaged AVOR from 600 to 850 hPa.
    # 
    # Mass-weighting is implicit on a pressure vertical grid
    # with constant dp (as it is in this case).

    track_file_tag = var_tag

    ds = Dataset(outdir+'avo.nc')
    pres = ds.variables['interp_level'][:] # hPa
    ikread = np.where((pres <= 850) & (pres >=600))[0]
    avor = ds.variables['avo'][:,ikread,:,:] # 10**-5 /s
    ds.close()

    # Mask out bad values
    avor = np.where((np.abs(avor) < 1e10), avor, np.nan)
    # Take vertical average
    var = np.nanmean(avor, axis=1)

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

if (lon.min() < 0) and (lon.max() > 0):
    lon_offset = dateline_lon_shift(lon, reverse=0)
else:
    lon_offset = 0

# Run tracking
track, f_masked = object_track(var, lon + lon_offset, lat, sens_test=i_senstest, basis=basis)

clon=track[0,:]
clon_offset = dateline_lon_shift(clon, reverse=1)
# clat=track[1,:]

# Write out to netCDF file
file_out = outdir+'track_'+track_file_tag+'.nc'
write_track_nc(file_out, nt, track, clon_offset)

print("Done with tracking for member "+str(imemb)+'!!')
