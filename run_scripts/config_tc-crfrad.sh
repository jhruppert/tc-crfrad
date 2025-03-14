#!/bin/bash
# 
# Configuration file for running WRF for ensemble simulations with downscaling
# using ndown.exe for a two-domain setup.
# 
# Driver script that calls this configuration file is run_ensemble_ndown.sh
# 
# James Ruppert
# 6 March 2025

############################################
# Main settings and directory paths

############################################
# CISL project code

# Current ongoing projects (totals as of as of 11/16/24):
#  - XX UFSU0031: Allison's exploratory allocation (remaining: 465k)
#  - UOKL0053: James's PICCOLO large allocation (20M)
#  - UOKL0049: James's TC-CRF large allocation (22M)
#  - UOKL0056: Frederick's TC small allocation (500k)
#  - UOKL0062: Small alloc for TC-Tor ET (1M)

project_code="UOKL0049" # Project to charge core hours against

# Project name
project_name="tc-crfrad"

# Select case/storm name
case_name="nepartak"

# Select test (e.g., "ctl", "ncrf", etc.)
test_name="ctl"
# test_name="ncrf12h"

# Select compiled wrf version to use (usually ctl) to fill run directory
wrf_compiled="ctl"

# Special input/output?
do_special_io=true

# Directory paths
work_dir=${work}/${project_name} # main directory containing WRF/, namelists/, etc.
source_file=${work_dir}/bashrc_wrf_der # source file for setting environment variables
# wrf_run_dir=${work_dir}/tests_compiled/$wrf_compiled # directory with all WRF run code for selected test
wrf_run_dir=${work}/wrf-largedomfix/tests_compiled/$wrf_compiled # directory with all WRF run code for selected test
ensemb_dir=${scratch}/${project_name}/${case_name} # output directory for ensemble simulations

############################################
# NDOWN settings

# inner nest start time
ndown_t_stamp_start="2016-07-02_00:00:00"
# ndown_t_stamp_start="2015-07-04_00:00:00"

############################################
# Restart settings

# Select test to use namelist, BCs, ICs from for restart
restart_base="ctl"

# Restart time stamp for WRF
restart_t_stamp_start="2015-07-04_18:00:00"
restart_t_stamp_end="2015-07-06_00:00:00"
