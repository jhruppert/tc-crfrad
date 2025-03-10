# 
# Bash script to download GEFS data from NCEI HAS.
# 
# James Ruppert
# 24 Jan 2025

##### MAIN SETTINGS #####

download_dir='/glade/work/ruppert/tc-crfrad/bcsics/gefs/' # Directory to save files
cd $download_dir

wget -erobots=off -nv -m -np -nH --cut-dirs=2 --reject "index.html*" https://www1.ncdc.noaa.gov/pub/has/HAS012588382/