# Read functions for WRF simulations.
# 
# James Ruppert
# 23 Nov 2024

from netCDF4 import Dataset
import numpy as np
import subprocess
import os

# Read WRF file list
def get_wrf_file_list(filedir, tag):
    process = subprocess.Popen(['ls '+filedir+tag],shell=True,
        stdout=subprocess.PIPE,universal_newlines=True)
    files = process.stdout.readlines()
    for ifile in range(len(files)):
        files[ifile] = files[ifile].strip()
    # times = get_times_wrffiles(files)
    return files#, times

# Read WRF dimensions
def wrf_dims(wrffile):
    wrffile_read = Dataset(wrffile)
    lat = wrffile_read.variables['XLAT'][:][0] # deg
    lon = wrffile_read.variables['XLONG'][:][0] # deg
    lat1d = lat[:,0]
    lon1d = lon[0,:]
    nx1 = lat1d.size
    nx2 = lon1d.size
    nz = wrffile_read.dimensions['bottom_top'].size
    npd = wrffile_read.dimensions['Time'].size
    wrffile_read.close()
    return lat1d, lon1d, nx1, nx2, nz, npd

# Get ensemble member settings
def memb_dir_settings(datdir, case, test_process, wrf_dom, memb_dir):
    wrfdir = datdir+case+'/'+memb_dir+'/'+test_process+"/"+wrf_dom+"/"
    outdir = wrfdir+"post_proc/"
    os.makedirs(outdir, exist_ok=True)
    # Get WRF file list, dimensions
    wrffiles = get_wrf_file_list(wrfdir, "wrfout_d01*")
    lat, lon, nx1, nx2, nz, npd = wrf_dims(wrffiles[0])
    nfiles = len(wrffiles)
    return outdir, wrffiles, nfiles, npd#, lat, lon

# Read arbitrary dimension size
def get_file_dim(infile, dimname):
    file_read = Dataset(infile)
    ndim = file_read.dimensions[dimname].size
    file_read.close()
    return ndim

# Read post-processed file list and dimensions
def get_postproc_dims(datdir, case, test_process, wrf_dom, memb_dir):
    outdir = datdir+case+'/'+memb_dir+'/'+test_process+"/"+wrf_dom+"/post_proc/"
    # Get file list, dimensions
    postproc_files = get_wrf_file_list(outdir, "*nc")
    # Find file tmpk
    # ifile = np.where(['tmpk' in postproc_files[ifile] for ifile in range(len(postproc_files))])[0][0]
    ifile = np.where(['HFX' in postproc_files[ifile] for ifile in range(len(postproc_files))])[0][0]
    file_read = Dataset(postproc_files[ifile])
    nt = file_read.dimensions['XTIME'].size
    lon = file_read.variables['XLONG'][:,:] # deg
    lat = file_read.variables['XLAT'][:,:] # deg
    nx = file_read.dimensions['west_east'].size
    ny = file_read.dimensions['south_north'].size
    # p_levels = file_read.variables['p_interp'][...]
    file_read.close()
    return outdir, postproc_files, nt, nx, ny, lon, lat

# Read WRF variable
def wrf_var_read(infile, varname):
    ncfile = Dataset(infile)
    var = ncfile.variables[varname][...]
    ncfile.close()
    return np.squeeze(var)

# Read WRF dimensions
def read_tc_track(dir, var_name):
    track_file = dir+'track_'+var_name+'.nc'
    ds = Dataset(track_file)
    clon = ds.variables['clon'][:]
    clat = ds.variables['clat'][:]
    ds.close()
    # Set invalid values to NaN
    clon = np.where((np.abs(clon) < 1e10), clon, np.nan) # Set bad values to NaN
    clat = np.where((np.abs(clat) < 1e10), clat, np.nan) # Set bad values to NaN
    return clon, clat

# def get_times_wrffiles(files):
#     # def slicer_vectorized(a,start,end):
#     #     b = a.view((str,1)).reshape(len(a),-1)[:,start:end]
#     #     return np.frombuffer(b.tobytes(),dtype=(str,end-start))
#     for ifile in range(len(files)):
#         files[ifile] = files[ifile].strip()
#         filenc=nc.Dataset(files[ifile])
#         char_var = filenc.variables['Time']
#         # try:
#         #     char_var = filenc.variables['Time']
#         # except:
#         #     char_var = filenc.variables['Times']
#         try:
#             itime = nc.chartostring(char_var[:])
#             itime = [t.replace("_", "T") for t in itime]  # Replace underscore with space
#         except:
#             if char_var.shape[0] == 1:
#                 split = files[ifile].split('_')
#                 itime = split[-2]+'T'+split[-1]
#             else:
#                 print('Need another fix here')
#         filenc.close()
#         itime_dt = np.array(itime, dtype='datetime64[m]')
#         if ifile == 0:
#             times_sav=itime_dt
#         else:
#             try:
#                 times_sav=np.concatenate((times_sav, itime_dt))
#             except:
#                 times_sav=np.concatenate((times_sav, itime_dt[np.newaxis]))
#     return times_sav
