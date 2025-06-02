
# Write out times series of tracked variables from ensemble TC simulations

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import rc
import seaborn as sns
from read_wrf_functions import *
from mpi4py import MPI
import pickle
import sys

# Takes about 10 min to complete
comm = MPI.COMM_WORLD
nproc = comm.Get_size()

# ### Track and plot settings

track_vars = [
    'avor_850-600',
    'slp',
]
ntracks = len(track_vars)

plot_vars = [
    'pmin',
    'vmax',
    # 'lwacre',
    # 'sst',
    # 'shear',
]
nvars = len(plot_vars)

# ### Directories and test selection

case = "nepartak"
test_process = "ctl"
# test_process = "ncrf12h"

dx_grid = 1 # grid spacing [km]

wrf_dom = "wrf_fine"
nmem = 10 # number of ensemble members

datdir = "/glade/campaign/univ/uokl0049/"

# Ens-member string tags (e.g., memb_01, memb_02, etc.)
memb0=1 # Starting member to read
memb_nums_str=np.arange(memb0,nmem+memb0,1).astype(str)
nustr = np.char.zfill(memb_nums_str, 2)
memb_all=np.char.add('memb_',nustr)

outdir, postproc_files, nt, nx, ny, lon, lat = get_postproc_dims(datdir, case, test_process, wrf_dom, memb_all[0])

# ### Read tracks and process variables

def get_track_extrema(outdir, lon, lat, clon, clat, plot_vars):

    nt = len(clon)
    it_valid = np.where(np.isfinite(clon))[0]
    it_invalid = np.where(np.isnan(clon))[0]
    ny, nx = lon.shape

    r_max=100 # Mask out beyond this radius [km]
    # ix_rmax = int(r_max/dx_grid) # Number of grid points to search
    # half_rmax = int(ix_rmax/2) # Half of the search radius

    # New grid dimensions [km]
    xdim = np.arange(nx) / dx_grid
    ydim = np.arange(ny) / dx_grid
    xdim = np.repeat(xdim[np.newaxis,:], ny, axis=0)
    ydim = np.repeat(ydim[:,np.newaxis], nx, axis=1)

    radius = np.full((nt,ny,nx), np.nan)
    for it in it_valid:
        radius_latlon = np.sqrt( (lon - clon[it])**2 + (lat - clat[it])**2 )
        ixiy_center = np.unravel_index(np.ma.argmin(radius_latlon), radius_latlon.shape)
        # Center the grid on the TC center
        radius[it,...] = np.sqrt( (xdim - xdim[ixiy_center[0], ixiy_center[1]])**2 + 
                                  (ydim - ydim[ixiy_center[0], ixiy_center[1]])**2 )

    all_vars = {}
    for ivar in plot_vars:

        if ivar == 'pmin':
            ds = xr.open_dataset(outdir+"slp.nc")
            slp = ds['slp'].values
            ds.close()
            # Mask outside of max radius
            slp = np.ma.masked_where(radius > r_max, slp, copy=False)
            slp[np.where(radius > r_max)] = np.nan
            all_vars['pmin'] = np.nanmin(slp, axis=(1,2))
            try:
                all_vars['pmin'][it_invalid] = np.nan # Mask out invalid values
            except:
                pass
            print("Min SLP: ", all_vars['pmin'])
            print()
        elif ivar == 'vmax':
            ds = xr.open_dataset(outdir+"U10.nc")
            u10 = ds['U10'].values
            ds.close()
            ds = xr.open_dataset(outdir+"V10.nc")
            v10 = ds['V10'].values
            ds.close()
            wspd = np.sqrt(u10**2 + v10**2)
            # Mask outside of max radius
            wspd[np.where(radius > r_max)] = np.nan
            all_vars['vmax'] = np.nanmax(wspd, axis=(1,2))
            try:
                all_vars['vmax'][it_invalid] = np.nan # Mask out invalid values
            except:
                pass
            print("Max wind speed: ", all_vars['vmax'])
            print()

    return all_vars

# Main loop

imemb = comm.rank
# for imemb in range(nmem):
outdir = datdir+case+'/'+memb_all[imemb]+'/'+test_process+"/"+wrf_dom+"/post_proc/"
for itrack in range(ntracks):
    # Read the data for the current member
    i_clon, i_clat = read_tc_track(outdir, track_vars[itrack])
    all_vars = get_track_extrema(outdir, lon, lat, i_clon, i_clat, plot_vars)

    # Write pickle file
    pickle_file = outdir+"track_"+track_vars[itrack]+"_tseries.pkl"
    with open(pickle_file, 'wb') as f:
        pickle.dump(all_vars, f)