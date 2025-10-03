# Calculate and write out vmf, p-class, and PE from Rosi's MPAS simulations.
# 
# Using modified code from Rosi's notebooks.
# 
# This version reads in pre-processed VMF from netCDF files per experiment and time step.
# 
# Optimized by gemini.

# ### Main settings and cluster

import xarray as xr
import numpy as np
import dask
import zarr
import pickle
import dask.array as da
from precip_class_mpas import *
from mpi4py import MPI

comm = MPI.COMM_WORLD
nproc = comm.Get_size()

# #### Set paths, read initial conditions, find tropical indexes

dx = "TC_3km"
# grid_path = "/glade/work/rberrios/MPAS/aqua_sstmax10N_ASD/plus4K/TC_3km/x5.tropical_3km_10N.init.nc"
grid_pickle_file = "/glade/campaign/univ/uokl0049/jruppert/pickle_out/grid_data.pickle"
with open(grid_pickle_file, 'rb') as f:
    areaCell, latCell, lonCell = pickle.load(f)

exp_names = ["CTL", "HOMO_RAD", "CLIM_RAD"]
#find indexes within desired latitudinal range
latbounds_all = [
    [0, 15.0],
    [10, 20.0],
    [15, 20],
]

# latbounds = [15, 20.0]
# latbounds = [0, 15.0]
# ind_within_lat = np.where( (latCell >= latbounds[0]) & (latCell <= latbounds[1]) )[0]

# areaCell_tropical = areaCell.isel(nCells=ind_within_lat)
# len(ind_within_lat)

# ### Functions

# #### Function to get PE, VMF

### Function to calculate mass-flux based precipitation efficiency ###
def calc_massFlux_precipitationEfficiency(M_u, M_d, cape, cin, areaCell, c_type_dask):

    # ntime = M_u.shape[0]

    # mu_clouds = da.zeros((ntime, 6), dtype=M_u.dtype) # Assuming M_u is a Dask array
    # md_clouds = da.zeros((ntime, 6), dtype=M_u.dtype)
    # count_clouds = da.zeros((ntime, 6), dtype=M_u.dtype) # How many cells contribute to each cloud type
    mu_clouds = da.zeros(6, dtype=M_u.dtype) # Assuming M_u is a Dask array
    md_clouds = da.zeros(6, dtype=M_u.dtype)
    cape_clouds = da.zeros(6, dtype=M_u.dtype)
    cin_clouds = da.zeros(6, dtype=M_u.dtype)
    count_clouds = da.zeros(6, dtype=M_u.dtype) # How many cells contribute to each cloud type

    # for it in range(ntime):

    for i in np.arange(1, 7): # Assuming c_type_dask ranges from 1 to 5
    # for i in np.arange(6, 7): # Assuming c_type_dask ranges from 1 to 5

        print(f"Processing cloud type {i}")

        # Ensure mask is computed as a dask array if c_type_dask is dask
        if i == 6:
            mask = ((c_type_dask == 1) | (c_type_dask == 4) | (c_type_dask == 5)) # Combine DC, ST, AN
        else:
            mask = (c_type_dask == i)

        count = mask.sum()

        # epsilon_mask = epsilon_v2.where(mask)
        Md_mask = M_d.where(mask)
        Mu_mask = M_u.where(mask)
        cape_mask = cape.where(mask)
        cin_mask = cin.where(mask)
        # areaCell_mask = da.repeat(areaCell[da.newaxis,...], M_d.shape[0]).where(mask) # areaCell should ideally be broadcastable or have matching dims
        areaCell_mask = areaCell.where(mask) # areaCell should ideally be broadcastable or have matching dims

        # It's better to compute the weighted sum and total area, then divide.
        # This will create a dask graph. The .compute() will happen outside the loop
        # if the list is returned, or if you explicitly call .compute() here.
        # For a list, you'd typically gather them later.
        # weighted_sum = (epsilon_mask * areaCell_mask).sum(dim='nCells', skipna=True)
        total_area = areaCell_mask.sum(dim='nCells', skipna=True)
        Mu_weighted_sum = (Mu_mask * areaCell_mask).sum(dim='nCells', skipna=True)
        Md_weighted_sum = (Md_mask * areaCell_mask).sum(dim='nCells', skipna=True)
        cape_weighted_sum = (cape_mask * areaCell_mask).sum(dim='nCells', skipna=True)
        cin_weighted_sum = (cin_mask * areaCell_mask).sum(dim='nCells', skipna=True)

        # Handle division by zero for total_area to avoid NaN/inf
        # epsilon_mask_mean_v2 = (weighted_sum / total_area).where(total_area != 0)
        Mu_mask_mean = (Mu_weighted_sum / total_area).where(total_area != 0)
        Md_mask_mean = (Md_weighted_sum / total_area).where(total_area != 0)
        cape_mask_mean = (cape_weighted_sum / total_area).where(total_area != 0)
        cin_mask_mean = (cin_weighted_sum / total_area).where(total_area != 0)

        # Finally, calculate epsilon for cloud type with averaged Md, Mu
        # V1
        # epsilon_mask_mean_v1 = 1.0 - (Md_mask_mean / Mu_mask_mean).where(Mu_mask_mean != 0) # Avoid inf/NaN where M_d is zero
        # epsilon_clouds.append(epsilon_mask_mean_v1) # Append dask.array.Array objects
        # count_clouds.append(count)
        # mu_clouds.append(Mu_mask_mean)
        # md_clouds.append(Md_mask_mean)
        count_clouds[i-1] = count
        mu_clouds[i-1] = Mu_mask_mean
        md_clouds[i-1] = Md_mask_mean
        cape_clouds[i-1] = cape_mask_mean
        cin_clouds[i-1] = cin_mask_mean

        # Put V2 after V1
        # epsilon_clouds.append(epsilon_mask_mean_v2) # Append dask.array.Array objects

    # finally, domain-mean
    # If you want to compute the domain mean of epsilon for the whole domain (not by cloud type)
    # domain_mean_epsilon = (epsilon * areaCell).sum(dim='nCells', skipna=True) / areaCell.sum(dim='nCells', skipna=True)
    # You could return both epsilon_clouds and domain_mean_epsilon, or whatever makes sense for your output.
    return [count_clouds, mu_clouds, md_clouds, cape_clouds, cin_clouds] # This will be a list of Dask DataArray 

# ### Main driver loop

# #### Get file list

# Get list of desired file times
file_times_arr = np.arange('2000-05-01T06:00:00', '2000-05-11T06:00:00', 6, dtype='datetime64[h]')
file_times = [file_times_arr[i].astype('datetime64[D]').astype(str)+'_'+str(file_times_arr[i]).split('T')[1].split(':')[0]+'.00.00' for i in range(len(file_times_arr))]

# istart_set=11
# file_times[istart_set]

# #### Start loops

# Main loop
import pickle

pclass_names = ['DC', 'CG', 'SC', 'ST', 'AN', 'DSA']

print('Starting loop...')
nCells_chunk_size = 100000

main_path = "/glade/campaign/mmm/dpm/rberrios/glade_scratch/MPAS_APE/aqua_sstmax10N_ASD/"
pickle_dir = '/glade/campaign/univ/uokl0049/jruppert/pickle_out/'

# for latbounds in latbounds_all:
# for latbounds in latbounds_all[0:1]:
latbounds = latbounds_all[comm.rank // 3]

ind_within_lat = np.where( (latCell >= latbounds[0]) & (latCell <= latbounds[1]) )[0]
areaCell_tropical = areaCell.isel(nCells=ind_within_lat)

def preprocess(ds):
    return ds.isel(nCells=ind_within_lat)

expName = exp_names[comm.rank % 3]
# for expName in exp_names:
# for expName in exp_names[0:1]:

data_path = f"{main_path}{expName}/TC_3km/"
scdir = '/glade/derecho/scratch/ruppert/tc-crfrad/mpas/'+expName+'/'

# data_path = f"/glade/campaign/mmm/dpm/rberrios/glade_scratch/MPAS_APE/aqua_sstmax10N_ASD/{expName}/TC_3km/"

# Open the dataset with dask backend. This loads lazily.
# Specify chunks to optimize memory usage and parallel processing.
# You'll need to know typical chunk sizes for your variables, or let xarray guess.
# For large datasets, manual chunking can be critical.
# Example: If 'Time' dimension is large, chunk it. 'nCells' might be good to chunk too.
# ds = xr.open_mfdataset(data_path + "waterPaths*", combine="nested", concat_dim="Time",
#                        chunks={'Time': 'auto', 'nCells': 'auto'}) # 'auto' lets Dask guess
# Or specify explicitly, e.g., {'Time': 24, 'nCells': 1000}

if expName == "CTL":
    istart = 0
elif expName == "HOMO_RAD":
    istart = 0
elif expName == "CLIM_RAD":
    istart = 0#istart_set

for time in file_times[istart:]:
# for time in file_times[0:1]:

    print(f"Rank: {comm.rank}; Processing file: VMF_pclass_{expName}_{time}_{str(latbounds[0])}-{str(latbounds[1])}.pickle")
    print()

    # print('opening files')
    # wp_files = [data_path+'waterPaths.'+time+'.nc' for time in file_times]
    wp_files = data_path+'waterPaths.'+time+'.nc'
    # ds = xr.open_mfdataset(wp_files,
    ds_tropical = xr.open_mfdataset(wp_files,
                # combine="nested", concat_dim="Time", 
                preprocess = preprocess,
                parallel=True, 
                chunks={"Time": -1, "nCells": nCells_chunk_size})

    # vmf_files = [scdir+'vmfs.'+time+'.nc' for time in file_times]
    vmf_files = scdir+'vmfs.'+time+'.nc'
    # ds_vmf = xr.open_mfdataset(vmf_files,
    ds_vmf_tropical = xr.open_mfdataset(vmf_files,
                # combine="nested", concat_dim="Time", 
                preprocess = preprocess,
                parallel=True,
                chunks={"Time": -1, "nCells": nCells_chunk_size})

    # READ IN CAPE FROM ZARR
    cape_path = f"{scdir}/CAPE_{time}.zarr"
    root = zarr.open(cape_path, mode="r")
    # Wrap Zarr arrays as Dask arrays
    cape_da = xr.DataArray(da.from_array(root["CAPE"], chunks=nCells_chunk_size), dims=("nCells",))
    cin_da  = xr.DataArray(da.from_array(root["CIN"],  chunks=nCells_chunk_size), dims=("nCells",))

    # Subset datasets
    # print('subsetting')
    # Select cells within latitude range. This operation is also lazy if `ds` is Dask-backed.
    # ds_tropical = ds.isel(nCells=ind_within_lat)
    # ds_vmf_tropical = ds_vmf.isel(nCells=ind_within_lat)

    # print('reading variables')
    # Convert to a list of DataArrays, and wrap in dask.array.stack to create a single Dask array
    # This creates a Dask-backed array 'q_int_dask' without loading data into memory yet.
    q_int_dask = da.stack([
        ds_tropical.lwp.data,
        ds_tropical.iwp.data,
        ds_tropical.rwp.data,
        ds_tropical.gwp.data
    ], axis=0) # Stack along a new 0th dimension for the different water paths

    mu = ds_vmf_tropical.mu
    md = ds_vmf_tropical.md

    # Subset and tidy up CAPE, CIN to cooperate with VMF function
    cape_da = cape_da.isel(nCells=ind_within_lat)
    cin_da  = cin_da.isel(nCells=ind_within_lat)
    cape_da = cape_da.expand_dims("Time")
    cin_da  = cin_da.expand_dims("Time")
    cape_da = cape_da.chunk({"Time": 1, "nCells": nCells_chunk_size})
    cin_da  = cin_da.chunk({"Time": 1, "nCells": nCells_chunk_size})

    # print('classifying')
    # Call the classification function. This will return a Dask array (c_type_dask).
    # The actual computation of c_type is still lazy at this point.
    c_type_dask = precip_class_mpas(q_int_dask)

    # print('getting PE')
    # Get Mu, Md as a function of PClass
    vmf_pclass = calc_massFlux_precipitationEfficiency(mu, md, cape_da, cin_da, areaCell_tropical, c_type_dask[0])

    # print('daks.compute for VMFs')
    results = dask.compute(vmf_pclass)[0] # dask.compute returns a tuple of results
    count_results = results[0]
    mu_results    = results[1]
    md_results    = results[2]
    cape_results  = results[3]
    cin_results   = results[4]

    # Write out to pickle

    # pickle_file_out = f"{scdir}PE_massFlux_{expName}_{time}.pickle"
    pickle_file_out = f"{pickle_dir}VMF_pclass_{expName}_{time}_{str(latbounds[0])}-{str(latbounds[1])}.pickle"
    with open(pickle_file_out, 'wb') as f:
        # pickle.dump(PE_thisExp, f)
        pickle.dump([count_results, mu_results, md_results, cape_results, cin_results], f)

print(f"Finished processing {expName}")

# print('Classification complete.')

