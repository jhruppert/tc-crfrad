# Read functions for WRF output.
# 
# James Ruppert
# 23 Nov 2024

from netCDF4 import Dataset
import numpy as np
import subprocess

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
    nt = wrffile_read.dimensions['Time'].size
    wrffile_read.close()
    return lat1d, lon1d, nx1, nx2, nz, nt

# Read arbitrary dimension size
def get_file_dim(infile, dimname):
    file_read = Dataset(infile)
    ndim = file_read.dimensions[dimname].size
    file_read.close()
    return ndim

# Read WRF variable
def wrf_var_read(infile, varname):
    ncfile = Dataset(infile)
    var = ncfile.variables[varname][...]
    ncfile.close()
    return np.squeeze(var)

def get_times_wrffiles(files, interval, units):
    # def slicer_vectorized(a,start,end):
    #     b = a.view((str,1)).reshape(len(a),-1)[:,start:end]
    #     return np.frombuffer(b.tobytes(),dtype=(str,end-start))
    # for ifile in range(len(files)):
    #     files[ifile] = files[ifile].strip()
    #     filenc=nc.Dataset(files[ifile])
    #     char_var = filenc.variables['Time']
    #     # try:
    #     #     char_var = filenc.variables['Time']
    #     # except:
    #     #     char_var = filenc.variables['Times']
    #     try:
    #         itime = nc.chartostring(char_var[:])
    #         itime = [t.replace("_", "T") for t in itime]  # Replace underscore with space
    #     except:
    #         if char_var.shape[0] == 1:
    #             split = files[ifile].split('_')
    #             itime = split[-2]+'T'+split[-1]
    #         else:
    #             print('Need another fix here')
    #     filenc.close()
    #     itime_dt = np.array(itime, dtype='datetime64[m]')
    #     if ifile == 0:
    #         times_sav=itime_dt
    #     else:
    #         try:
    #             times_sav=np.concatenate((times_sav, itime_dt))
    #         except:
    #             times_sav=np.concatenate((times_sav, itime_dt[np.newaxis]))
    def date_from_wrf_filename(filename):
        wrfname = filename.split("/")[-1]
        yyyy = wrfname.split("_")[2][0:4]
        mm = wrfname.split("_")[2].split("-")[1][0:2]
        dd = wrfname.split("_")[2].split("-")[2][0:2]
        hh = wrfname.split("_")[3][0:2]
        nn = wrfname.split("_")[4][0:2]
        datestr = f"{yyyy}-{mm}-{dd}T{hh}:{nn}:00"
        return datestr

    times_sav = np.arange(
        np.array(date_from_wrf_filename(files[0]), dtype='datetime64['+units+']'),
        np.array(date_from_wrf_filename(files[-1]), dtype='datetime64['+units+']') + np.timedelta64(interval, units),
        interval,
        dtype='datetime64['+units+']')

    return times_sav
