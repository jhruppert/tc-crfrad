# tc-crfrad
Repo containing all start-data and code for the NSF-funded numerical modeling study on cloud-radiation feedback in tropical cyclones

Forcing data:
- For automated script for downloading GEFS data from AWS, see run_scripts/download_gefs.py
  - https://github.com/awslabs/open-data-docs/tree/main/docs/noaa/noaa-gefs-pds
- For older GEFS data (pre-2017), downloading from NCEI: https://www.ncei.noaa.gov/products/weather-climate-models/global-ensemble-forecast
  - File conventions:
    - gens_2 is 2.5º and gens_3 is 1º
    - File name: gens_2_YYYYMMDDHH_NN.g2.tar, where NN is ensemble member
    - gens-a* files contain most common variables
    - gens-b* files contain more uncommon variables
- Downloading deterministic GFS for testing from RDA: https://rda.ucar.edu/datasets/d084001/

Namelist settings and approach:
- Using NDOWN to provide greatest constraint of large-scale environment across tests of the model experiment
- Domains: 5km outer nest, 1km inner nest
- Outer nest is initialized 12 hours earlier than inner 1km nest, with nudging imposed for entire period on outer nest.
- Based on tests and recommendations of [Delfenio et al. 2022](https://doi.org/10.5194/nhess-22-3285-2022):
  - isftcflx set to 1.
  - No cumulus scheme since coarse grid is 5km.
