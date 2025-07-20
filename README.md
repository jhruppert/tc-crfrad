# tc-crfrad
Repo containing all start-data and code for the NSF-funded numerical modeling study on cloud-radiation feedback in tropical cyclones

Forcing data:
- ERA5:
  - Now using ERA5 analysis time steps downloaded from CDS:
    - Deterministic: 1-hourly, 0.25º
    - 10 memb. ensemble: 3-hourly, 0.5º
- Ensemble forcing methodology:
  - Given the different resolution between the deterministic analysis and ensemble members, we incorporate the smaller-scale spatiotemporal variance of the deterministic analysis into the forcing data used for each ensemble member $\phi_i$ according to  
  $\phi_i = \phi_{i,0} - \overline{\phi_{i,0}} + \phi^*$, or  
  $\phi_i = \phi_{i,0} + \phi^* - \overline{\phi_{i,0}} = \phi_{i,0} + \phi'$,  
  $\phi' = \phi^* - \overline{\phi_{i,0}}$,  
  where $\phi_{i,0}$ corresponds to the unmodified ensemble member, $\overline{\phi_{i,0}}$ the mean of those members, and $\phi^*$ the deterministic analysis. This computation is done after each input is already interpolated onto an hourly grid and the model spatial grid using WPS.


WRF setup notes:
- Using NDOWN to provide greatest constraint of large-scale environment across tests of the model experiment
- Domain setup:
  - 5km outer nest, 1km inner nest
  - No nudging for final version. [XX Outer nest is nudged (using analysis nudging) for entire period, only above the PBL]
  - Outer nest is initialized 12 hours earlier than inner 1km nest
- Based on tests and recommendations of [Delfenio et al. 2022](https://doi.org/10.5194/nhess-22-3285-2022):
  - isftcflx set to 1.
  - No cumulus scheme since coarse grid is 5km.
- Using zadvect_implicit = 1 to handle implicit vertical advection, which permits a larger time step.
- ***Major fix:*** Using the large-domain [fix](https://github.com/wrf-model/WRF/pull/2157) provided by Ben Kirk (NCAR, CISL) seems to do the trick, which includes a replacement of a c-code script.
- ***Major fix:*** Set max_time_step = 10000 along with targe_cfl = 2.0 so that the adaptive time stepping scheme becomes CFL-limited instead of hitting an arbitrary max time step limit. This led to a change from dt=8s to dt=18s, a 225% speed-up.
- ***Major fix:*** Changed io_form_output, io_form_output = 13 (from 2, the default) to take advantage of parallel I/O, writing from each processor to one file. This sped up I/O steps by a factor of ~17 (~10 min for wrfout, ~30 min for wrfrst, now < 1 min for each). Since I/O was dominating wall-clock times, this speed-up is fully realized by the simulations. This requires setting the environmental variable NETCDFPAR and recompiling, per the [WRF/doc/README.netcdf4par](https://github.com/wrf-model/WRF/blob/master/doc/README.netcdf4par).
- ***Apparent bug:*** WRF crashes at an arbitrary output time step when using io_form = 13 and doing multiple output frames per file (was writing 24 hours worth of 20-min output per file). Changing to single frame-per-file avoided this crash.


<br />

Technical step-by-step
1. Use ***run_getera5_ens.sh*** to download 1) single-level and 2) pressure-level ERA5 ensemble grid files in grib format. These two files include all ensemble member data packed into each, so need to be separated.
2. To separate into individual ensemble member files, run ***split_era5_ensemble.sh***.
3. Have a compiled WPS directory ready in the same folder as the parent ensemble folder, and run ***run_wps_era5ens.sh***.
4. ...

<br />

No longer using:
- GEFS:
  - For automated script for downloading GEFS data from AWS, see run_scripts/download_gefs.py
    - https://github.com/awslabs/open-data-docs/tree/main/docs/noaa/noaa-gefs-pds
  - X For older GEFS data (pre-2017), downloading from NCEI: https://www.ncei.noaa.gov/products/weather-climate-models/global-ensemble-forecast
    - File conventions:
      - gens_2 is 2.5º and gens_3 is 1º
      - File name: gens_2_YYYYMMDDHH_NN.g2.tar, where NN is ensemble member
      - gens-a* files contain most common variables
      - gens-b* files contain more uncommon variables
  - X Downloading deterministic GFS for testing from RDA: https://rda.ucar.edu/datasets/d084001/
