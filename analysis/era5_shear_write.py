# #### Jupyter notebook to compute shear across ERA5 ensemble for Nepartak forcing data.
# 
# James Ruppert  
# jruppert@ou.edu  
# 6/15/25
# 
# With support from ChatGPT

# #### Main Settings

import numpy as np
from read_wrf_functions import *
import xarray as xr
from tropycal import tracks, recon, utils, realtime
from geopy.distance import distance
from mpi4py import MPI

comm = MPI.COMM_WORLD
nproc = comm.Get_size()


#### Directories and grib files
datdir = "/glade/campaign/univ/uokl0049/nepartak/"
file_tag="mem*/grib/ERA*-pl*grib"

# Get grib file ensemble
grib_files = get_wrf_file_list(datdir, file_tag)
nfiles = len(grib_files)
# grib_files

# General regional subset to work with smaller dataset
latmin, latmax, lonmin, lonmax = -4, 33.0, 110.0, 156.0

# Get times
grib_file = xr.open_mfdataset(grib_files[0], engine="cfgrib", combine='by_coords')
grib_file = grib_file.sel(latitude=slice(latmax, latmin), longitude=slice(lonmin, lonmax))
grib_times = grib_file.time.values.astype('datetime64[ns]')
# Create 2D mesh of lat-lon points
lat = grib_file['latitude']
lon = grib_file['longitude']
lon2d, lat2d = np.meshgrid(lon, lat)
grib_file.close()

nt_grib = len(grib_times)

# ### Read and process data

# #### Read in observed storm track

# Read in basin only if it hasn't been yet
if 'basin' not in locals():
    basin = tracks.TrackDataset(basin='west_pacific',source='ibtracs')
storm = basin.get_storm(('nepartak',2016))
tc_track = {
    'vmax': storm.vars['vmax'],
    'mslp': storm.vars['mslp'],
    'lon': storm.vars['lon'],
    'lat': storm.vars['lat'],
    'time': np.array(storm.vars['time'], dtype='datetime64[ns]'),
    # 'lon': storm.vars['wmo_lon'],
    # 'lat': storm.vars['wmo_lat'],
    }

# Interpolate observed TC track to GRIB data times

valid_times = []
vmax = []
pres = []
ilon = []
ilat = []
for it in range(nt_grib):
    # Skip if the time is not in the TC track
    if grib_times[it] < np.min(tc_track['time']) or grib_times[it] > np.max(tc_track['time']):
        continue
    # print(f"Interpolating TC track for time {grib_times[it]}")
    valid_times.append(grib_times[it])
    vmax.append(np.interp(grib_times[it].astype(float), tc_track['time'].astype(float), tc_track['vmax']))
    pres.append(np.interp(grib_times[it].astype(float), tc_track['time'].astype(float), tc_track['mslp']))
    ilon.append(np.interp(grib_times[it].astype(float), tc_track['time'].astype(float), tc_track['lon']))
    ilat.append(np.interp(grib_times[it].astype(float), tc_track['time'].astype(float), tc_track['lat']))

# Convert lists to numpy arrays
tc_track_gribtimes = {
    'time': np.array(valid_times, dtype='datetime64[ns]'),
    'vmax': np.array(vmax),
    'mslp': np.array(pres),
    'lon': np.array(ilon),
    'lat': np.array(ilat),
}

nt_interp = len(tc_track_gribtimes['time'])

# #### Read in ERA5 shear

# # Print some metadata

# # ds = xr.open_mfdataset(grib_files[0], combine='by_coords', engine="cfgrib")
# ds_plevs = xr.open_mfdataset(grib_files[0], combine='by_coords', engine="cfgrib", filter_by_keys={'typeOfLevel': 'isobaricInhPa'})
# # ds_meansea = xr.open_mfdataset(grib_files[0], combine='by_coords', engine="cfgrib", filter_by_keys={'typeOfLevel': 'meanSea'})

# for ds in [ds_plevs]:
# # for ds in [ds_plevs, ds_sfc]:
# # for ds in [ds_sngllev]:
# # for ds in [ds_meansea]:
#     for ivar in ds.data_vars:
#         print(ivar)
#         print(ds[ivar].attrs['standard_name'])
#         print(ds[ivar].attrs['long_name'])
#         print(ds[ivar].dims)
#         print(ds[ivar].shape)
#         print()

# Parameters for shear calculation
plevs_shear=(850,200)
radius_min_km = 200 # Maximum distance from TC center to compute shear
radius_max_km = 800

# Compute great-circle distance from each grid point to center point
def compute_distance_grid(lat_grid, lon_grid, center_lat, center_lon):
    flat_lat = lat_grid.ravel()
    flat_lon = lon_grid.ravel()
    distances = np.array([
        distance((center_lat, center_lon), (la, lo)).km
        for la, lo in zip(flat_lat, flat_lon)
    ])
    return distances.reshape(lat_grid.shape)

# mean_shear_ens = []

grib_file = grib_files[comm.rank]
# for imember, grib_file in enumerate(tqdm_notebook(grib_files[:2])):

ds = xr.open_mfdataset(grib_file, engine="cfgrib", combine='by_coords',
                       filter_by_keys={'typeOfLevel': 'isobaricInhPa'})
ds = ds.sel(latitude=slice(latmax, latmin), longitude=slice(lonmin, lonmax))

# Get wind components
# u850 = ds.u.sel(isobaricInhPa=plevs_shear[0])
# u200 = ds.u.sel(isobaricInhPa=plevs_shear[1])
# v850 = ds.v.sel(isobaricInhPa=plevs_shear[0])
# v200 = ds.v.sel(isobaricInhPa=plevs_shear[1])
# ushear = u200 - u850
# vshear = v200 - v850
# shear = np.sqrt(ushear**2 + vshear**2)

mean_shear_imemb = np.full(nt_interp, np.nan)

for itime in range(nt_interp):

    print(f"Processing time {itime} for member {comm.rank}")

    # Get wind components
    u850 = ds.u.sel(isobaricInhPa=plevs_shear[0], time=tc_track_gribtimes['time'][itime])
    u200 = ds.u.sel(isobaricInhPa=plevs_shear[1], time=tc_track_gribtimes['time'][itime])
    v850 = ds.v.sel(isobaricInhPa=plevs_shear[0], time=tc_track_gribtimes['time'][itime])
    v200 = ds.v.sel(isobaricInhPa=plevs_shear[1], time=tc_track_gribtimes['time'][itime])

    # Get the center point of the TC track at this time
    lat_center = tc_track_gribtimes['lat'][itime]
    lon_center = tc_track_gribtimes['lon'][itime]

    # Compute distance grid from center point
    distance_grid = compute_distance_grid(lat2d, lon2d, lat_center, lon_center)

    # Mask the winds for desired annulus
    u850_masked = u850.where((distance_grid >= radius_min_km) & (distance_grid <= radius_max_km))
    u200_masked = u200.where((distance_grid >= radius_min_km) & (distance_grid <= radius_max_km))
    v850_masked = v850.where((distance_grid >= radius_min_km) & (distance_grid <= radius_max_km))
    v200_masked = v200.where((distance_grid >= radius_min_km) & (distance_grid <= radius_max_km))

    # Take the mean of the masked winds
    u850_masked = u850_masked.mean(skipna=True).values
    u200_masked = u200_masked.mean(skipna=True).values
    v850_masked = v850_masked.mean(skipna=True).values
    v200_masked = v200_masked.mean(skipna=True).values

    # Compute shear
    ushear = u200_masked - u850_masked
    vshear = v200_masked - v850_masked
    shear_itime_masked = np.sqrt(ushear**2 + vshear**2)

    # Take the mean, add to ens. member time series list
    mean_shear_imemb[itime] = shear_itime_masked

    # plt.contourf(lon2d, lat2d, shear_itime_masked, levels=np.arange(0, 30, 1), cmap='viridis')

# Convert array to xarray dataset
mean_shear_imemb_ds = xr.DataArray(mean_shear_imemb[:,np.newaxis],
                                   name='mean_shear',
                                   attrs=dict(
                                       description="Mean 200-850-hPa shear (vector difference) from ERA5, annulus from 200 to 800 km from TC center",
                                       units="m/s"),
                                   dims=['time', 'member'],
                                   coords={'time': tc_track_gribtimes['time'],
                                           'member': [comm.rank]})

# Write to netCDF file
fileout = "nepartak_shear_imemb_" + str(comm.rank) + ".nc"
mean_shear_imemb_ds.to_netcdf(fileout, mode='w', format='NETCDF4')

print("Finished!")
