# 
# Column-based precipitation classification algorithm designed for application on
# numerical model output.
# 
# It has been designed using WRF model output using the Thompson and Eidhammer
# (2014, JAS) microphysics scheme, which has 2 liquid and 3 frozen categories as
# listed and expected below.
# 
# Input:
# 
#       Q_INT: n-D array of vertically integrated hydrometeors as f(q, X), where
#               q(5) is the hydrometeor dimension, arranged as
#               ['QCLOUD', 'QRAIN', 'QICE', 'QSNOW', 'QGRAUP'] and X includes the
#               remaining (time and) spatial dimensions.
# Returns:
# 
#       C_TYPE: (n-2)-D array as f(X) with classification results:
#               0: non-cloud
#           Convective:
#               1: deep convective
#               2: congestus
#               3: shallow
#           Layered:
#               4: stratiform
#               5: anvil (weaker rainfall)
# 
# Emily Luschen - emily.w.luschen-1@ou.edu
# James Ruppert - jruppert@ou.edu
# 5/19/23
# Rosi RB - modified to ingest water paths and to return dask arrays

def precip_class_mpas(q_int):

    import numpy as np
    import dask.array as da
    import xarray as xr

    shape = q_int.shape
    ndims=len(shape)
    shape_out = shape[1:ndims]

    # Integrated water variables
    # Ensure these are Dask arrays if q_int is a Dask array
    LWP = q_int[0]
    IWP = q_int[1]
    # For Q_INT input, q_int[2] is QICE, q_int[3] is QSNOW, q_int[4] is QGRAUP
    # Your original code used q_int[2] for rain, q_int[3] for graupel.
    # Make sure this indexing is consistent with your actual 'q_int' structure.
    # Based on the function docstring: ['QCLOUD', 'QRAIN', 'QICE', 'QSNOW', 'QGRAUP']
    # And your q_int = np.array([ds.lwp, ds.iwp, ds.rwp, ds.gwp]), this means:
    # q_int[0] = lwp (QCLOUD + QRAIN combined in your data?)
    # q_int[1] = iwp (QICE + QSNOW + QGRAUP combined in your data?)
    # q_int[2] = rwp (QRAIN from your data)
    # q_int[3] = gwp (QGRAUP from your data)
    # So, the original function's `q_int[2]` (for rain_thresh) is `rwp` (your q_int[2])
    # and `q_int[3]` (for graup_thresh) is `gwp` (your q_int[3]).
    # This seems consistent, just making sure the comments are aligned.

    RWP = q_int[2] # Rain Water Path
    GWP = q_int[3] # Graupel Water Path

    TWP = LWP + IWP

    # Use xarray.where for masking with Dask arrays
    # Ensure LWP is not zero before division to avoid inf/nan
    cr = xr.where(LWP != 0, IWP / LWP, np.inf) # Use np.inf for where LWP is zero, so cr_thresh condition handles it

    # Threshold parameters (unchanged)
    twp_thresh = 1e-1
    cr_thresh = 2
    graup_thresh = 1e-4
    rain_thresh_conv = 1e-1
    rain_thresh_strat = 1e-2

    # Initialize output array as a Dask array of zeros
    # Use dask.array.zeros or xarray.zeros_like to create a Dask-backed array
    # The shape should be (Time, nCells) after the initial q_int[0] selection
    # Assuming q_int has dimensions (variable, Time, nCells)
    c_type_shape = LWP.shape # Should be (Time, nCells)
    c_type = da.zeros(c_type_shape, dtype=np.int8)

    # Use dask.array.where for efficient boolean indexing with Dask arrays
    # Deep convection
    condition_dc = ((LWP != 0) & (TWP > twp_thresh) & \
                    (cr <= cr_thresh) & \
                    (RWP >= rain_thresh_conv) & \
                    (GWP >= graup_thresh))
    c_type = da.where(condition_dc, 1, c_type)

    # Congestus
    condition_cg = ((LWP != 0) & (TWP > twp_thresh) & \
                    (cr <= cr_thresh) & \
                    (RWP >= rain_thresh_conv) & \
                    (GWP < graup_thresh))
    c_type = da.where(condition_cg, 2, c_type)

    # Shallow
    condition_sc = ((LWP != 0) & (TWP > twp_thresh) & \
                    (cr <= cr_thresh) & \
                    (RWP < rain_thresh_conv))
    c_type = da.where(condition_sc, 3, c_type)

    # Stratiform
    condition_st = ((LWP != 0) & (TWP > twp_thresh) & \
                    (cr > cr_thresh) & \
                    (RWP >= rain_thresh_strat))
    c_type = da.where(condition_st, 4, c_type)

    # Anvil
    condition_an = ((LWP != 0) & (TWP > twp_thresh) & \
                    (cr > cr_thresh) & \
                    (RWP < rain_thresh_strat))
    c_type = da.where(condition_an, 5, c_type)

    return c_type # This will return a Dask array