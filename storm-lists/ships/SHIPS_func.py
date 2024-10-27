import xarray as xr
import numpy as np
import pandas as pd
import mpu
import glob,os

def find_latlon_xy(ds,lat,lon):
    abslat = np.abs(ds.lat-lat)
    abslon = np.abs(ds.lon-lon)
    c = np.maximum(abslon, abslat)
    closest = np.where(c == np.min(c))
    if len(closest[0])>1:
        xloc = closest[0][0]
        yloc = closest[1][0]
    elif len(closest[0])<=1:
        ([xloc], [yloc]) = closest
    return xloc,yloc
    
def readyear_automatic(data2,year):
    dm1 = xr.open_dataset(data2+'/sst/sst_'+str(year)+'.nc')
    return dm1

def make_timeseries_onestorm(tracksDF,TCname,basin):
    if basin=='WPAC':
        track=tracksDF[tracksDF['name']==TCname].reset_index(drop=True).iloc[::2,:].reset_index(drop=True)
    else:
        track=tracksDF[tracksDF['name']==TCname].reset_index(drop=True)
    lon1=track['lon'].to_numpy()
    lat1=track['lat'].to_numpy()
    lonx=np.mod(lon1,360)
    pos = arr = np.stack((lat1, lonx), axis=1)
    return pos

def get_closest_land_xy(path,era5,basin,year,stormname,time_before_tcg):
    if basin=='WP':
        track = sorted(glob.glob(path+f'wp/wp_{year}.csv'))
        tracksDF = pd.read_csv(track[0])
        try:
            stormloc = make_timeseries_onestorm(tracksDF,stormname,'WPAC')[int(time_before_tcg)]
        except IndexError:
            tracksDFn = pd.read_csv(sorted(glob.glob(path+f'wp/WP_{year}_6hr_fred.csv'))[0])
            stormloc = make_timeseries_onestorm(tracksDFn,stormname,'WPAC')[int(time_before_tcg)]
    elif basin=='EP':
        track = sorted(glob.glob(path+f'ep/EP_{year}*.csv'))
        tracksDF = pd.read_csv(track[0])
        try:
            stormloc = make_timeseries_onestorm(tracksDF,stormname,'EPAC')[int(time_before_tcg)]
        except IndexError:
            tracksDFn = pd.read_csv(sorted(glob.glob(path+f'ep/EP_{year}_6hr_fred.csv'))[0])
            stormloc = make_timeseries_onestorm(tracksDFn,stormname,'EPAC')[int(time_before_tcg)]            
    elif basin=='AL':
        track = sorted(glob.glob(path+f'na/NA_{year}.csv'))
        tracksDF = pd.read_csv(track[0])
        stormloc = make_timeseries_onestorm(tracksDF,stormname,'NATL')[int(time_before_tcg)]
    
    closestloc = find_latlon_xy(era5,stormloc[0],stormloc[1])
    AA = np.argwhere(np.isnan(np.transpose(era5['var34'][0,...].values)))
    distances = np.linalg.norm(AA-closestloc, axis=1)
    min_index = np.argmin(distances)
    return stormloc,closestloc,AA[min_index]
    
def get_distance_km(era5,TClocxy,landlocxy):
    """
    https://gis.stackexchange.com/questions/416091/converting-a-netcdf-from-0-to-360-to-180-to-180-via-xarray
    """
    TClat,TClon = era5.lat[TClocxy[1]],(era5.lon[TClocxy[0]]+ 180) % 360 - 180
    landlat,landlon = era5.lat[landlocxy[1]],(era5.lon[landlocxy[0]]+ 180) % 360 - 180
    dist = mpu.haversine_distance((TClat, TClon), (landlat, landlon))
    return dist