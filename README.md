# tc-crfrad
Repo containing all start-data and code for the NSF-funded numerical modeling study on cloud-radiation feedback in tropical cyclones

Forcing data:
- ~~GEFS:~~
  - For automated script for downloading GEFS data from AWS, see run_scripts/download_gefs.py
    - https://github.com/awslabs/open-data-docs/tree/main/docs/noaa/noaa-gefs-pds
  - X For older GEFS data (pre-2017), downloading from NCEI: https://www.ncei.noaa.gov/products/weather-climate-models/global-ensemble-forecast
    - File conventions:
      - gens_2 is 2.5º and gens_3 is 1º
      - File name: gens_2_YYYYMMDDHH_NN.g2.tar, where NN is ensemble member
      - gens-a* files contain most common variables
      - gens-b* files contain more uncommon variables
  - X Downloading deterministic GFS for testing from RDA: https://rda.ucar.edu/datasets/d084001/
- ERA5:
  - Now using ERA5 analysis time steps, downloaded from CDS, which has a 10-member ensemble.
  - For doing the ensemble, which is 3-hourly and 1-deg resolution (coarser in space and time than deterministic), using WPS/metgrid to interpolate ens. members to hourly, and using BLANK to downscale files to deterministic grid and add perturbations to the deterministic.

Namelist settings and approach:
- Using NDOWN to provide greatest constraint of large-scale environment across tests of the model experiment
- Domains:
  - 5km outer nest, 1km inner nest
  - Outer nest is nudged (using analysis nudging) for entire period, only above the PBL
  - Outer nest is initialized 12 hours earlier than inner 1km nest
- Based on tests and recommendations of [Delfenio et al. 2022](https://doi.org/10.5194/nhess-22-3285-2022):
  - isftcflx set to 1.
  - No cumulus scheme since coarse grid is 5km.
- Using zadvect_implicit = 1 to handle implicit vertical advection, which permits a larger time step.
- ***Major fix:*** Set max_time_step = 10000 along with targe_cfl = 2.0 so that the adaptive time stepping scheme becomes CFL-limited instead of hitting an arbitrary max time step limit. This led to a change from dt=8s to dt=18s, a 225% speed-up.

Using the large-domain [fix](https://github.com/wrf-model/WRF/pull/2157) provided by Ben Kirk (NCAR, CISL) seems to do the trick, which includes a replacement of a c-code script.
