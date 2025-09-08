# import required packages
import numpy as np
from .numba import njit
from . import constants
from . import utilities

# define the function to calculate CAPE
@njit()
def cape(TP,RP,PP,T,R,P,ascent_flag=0,ptop=50,miss_handle=1):
    """Calculate the CAPE of a parcel given parcel and environmental conditions.

    function [CAPED,TOB,LNB,IFLAG]= cape(TP,RP,PP,T,R,P,ascent_flag=0,ptop=50,miss_handle=1)

    This function calculates the CAPE of a parcel given parcel pressure PP (hPa), 
    temperature TP (K) and mixing ratio RP (gram/gram) and given a sounding
    of temperature (T in K) and mixing ratio (R in gram/gram) as a function
    of pressure (P in hPa). CAPED is the calculated value of CAPE following
    Emanuel 1994 (E94) Equation 6.3.6 and TOB is the temperature at the
    level of neutral buoyancy ("LNB") for the displaced parcel.

    Args:
        TP (float): Parcel temperature (K)
        RP (float): Parcel mixing ratio (gram/gram)
        PP (float): Parcel pressure (hPa)
        T (array): Environmental temperature profile (K)
        R (array): Environmental mixing ratio profile (gram/gram)
        P (array): Environmental pressure profile (hPa)
            The arrays MUST be arranged so that the lowest index corresponds
            to the lowest model level, with increasing index corresponding to
            decreasing pressure.
        ascent_flag (int, optional): Adjustable constant fraction for buoyancy of displaced parcels.
            0 = Reversible ascent (default)
            1 = Pseudo-adiabatic ascent.
        ptop (float, optional): Pressure below which sounding is ignored (hPa). Defaults to 50.
        miss_handle (int, optional): Flag for handling missing values.
            0 = ignore NaN (BE02 default)
                    NaN values in profile are ignored and PI is still calcuated.
            1 = return missing values (pyPI default)
                    given NaN values PI will be set to missing (with IFLAG=3)
                    NOTE: If any missing values are between the lowest valid level and ptop
                    then PI will automatically be set to missing (with IFLAG=3)

    Returns:
        tuple: (CAPED, TOB, LNB, IFLAG) where:
            - CAPED (float): Convective Available Potential Energy (J/kg)
            - TOB (float): Temperature at level of neutral buoyancy (K)
            - LNB (float): Level of neutral buoyancy pressure (hPa)
            - IFLAG (int): Status flag where:
                1 = Success
                0 = Improper sounding/parcel
                2 = Did not converge
                3 = Missing values in input profile
    """
    #
    #   ***  Handle missing values   ***
    #
    
    # find if any values are missing in the temperature or mixing ratio array
    valid_i=~np.isnan(T)
    first_valid=np.where(valid_i)[0][0]
    # Are there missing values? If so, assess according to flag
    if (np.sum(valid_i) != len(P)):
        # if not allowed, set IFLAG=3 and return missing CAPE
        if (miss_handle != 0):
            CAPED=np.nan
            TOB=np.nan
            LNB=np.nan
            IFLAG=3
            # Return the unsuitable values
            return(CAPED,TOB,LNB,IFLAG)
        else:
            # if allowed, but there are missing values between the lowest existing level
            # and ptop, then set IFLAG=3 and return missing CAPE
            if np.sum(np.isnan(T[first_valid:len(P)])>0):
                CAPED=np.nan
                TOB=np.nan
                LNB=np.nan
                IFLAG=3
                # Return the unsuitable values
                return(CAPED,TOB,LNB,IFLAG)
            else:
                first_lvl=first_valid
    else:
        first_lvl=0

    # Populate new environmental profiles removing values above ptop and
    # find new number, N, of profile levels with which to calculate CAPE
    N=np.argmin(np.abs(P-ptop))
    
    P=P[first_lvl:N]
    T=T[first_lvl:N]
    R=R[first_lvl:N]
    nlvl=len(P)
    TVRDIF = np.zeros((nlvl,))
    
    #
    #   ***  Run checks   ***
    #
    
    # CHECK: is the input profile ordered with increasing pressure? If not, return missing CAPE
    if (P[2]-P[1] > 0):
        CAPED=0
        TOB=np.nan
        LNB=np.nan
        IFLAG=0
        # Return the unsuitable values
        return(CAPED,TOB,LNB,IFLAG)

    # CHECK: Is the input parcel suitable? If not, return missing CAPE
    if ((RP < 1e-6) or (TP < 200)):
        CAPED=0
        TOB=np.nan
        LNB=np.nan
        IFLAG=0
        # Return the unsuitable values
        return(CAPED,TOB,LNB,IFLAG)
    
    #
    #  ***  Define various parcel quantities, including reversible   ***
    #  ***                       entropy, S                          ***
    #                         
    TPC=utilities.T_ktoC(TP)                 # Parcel temperature in Celsius
    ESP=utilities.es_cc(TPC)                # Parcel's saturated vapor pressure
    EVP=utilities.ev(RP,PP)                 # Parcel's partial vapor pressure
    RH=EVP/ESP                              # Parcel's relative humidity
    RH=min([RH,1.0])                        # ensure that the relatively humidity does not exceed 1.0
    # calculate reversible total specific entropy per unit mass of dry air (E94, EQN. 4.5.9)
    S=utilities.entropy_S(TP,RP,PP)
    
    
    #
    #   ***  Estimate lifted condensation level pressure, PLCL   ***
    #     Based on E94 "calcsound.f" code at http://texmex.mit.edu/pub/emanuel/BOOK/
    #     see also https://psl.noaa.gov/data/composites/day/calculation.html
    #
    #   NOTE: Modern PLCL calculations are made following the exact expressions of Romps (2017),
    #   see https://journals.ametsoc.org/doi/pdf/10.1175/JAS-D-17-0102.1
    #   and Python PLCL code at http://romps.berkeley.edu/papers/pubdata/2016/lcl/lcl.py
    #
    PLCL=utilities.e_pLCL(TP,RH,PP)
    
    # Initial default values before loop
    CAPED=0
    TOB=T[0]
    IFLAG=1
    # Values to help loop
    NCMAX=0
    jmin=int(1e6)
    
    #
    #   ***  Begin updraft loop   ***
    #

    # loop over each level in the profile
    for j in range(nlvl):
        
        # jmin is the index of the lowest pressure level evaluated in the loop
        jmin=int(min([jmin,j]))
    
        #
        #   *** Calculate Parcel quantities BELOW lifted condensation level   ***
        #
        if (P[j] >= PLCL):
            # Parcel temperature at this pressure
            TG=TP*(P[j]/PP)**(constants.RD/constants.CPD)
            # Parcel Mixing ratio
            RG=RP
            # Parcel and Environmental Density Temperatures at this pressure (E94, EQN. 4.3.1 and 6.3.7)
            TLVR=utilities.Trho(TG,RG,RG)
            TVENV=utilities.Trho(T[j],R[j],R[j])
            # Bouyancy of the parcel in the environment (Proxy of E94, EQN. 6.1.5)
            TVRDIF[j,]=TLVR-TVENV
            
        #
        #   *** Calculate Parcel quantities ABOVE lifted condensation level   ***
        # 
        else:
            TG, RG, IFLAG = solve_temperature_from_entropy(S=S, P=P[j], RP=RP, T_initial=T[j])
            if IFLAG == 2:  # Did not converge
                CAPED=0
                TOB=T[0]
                LNB=P[0]
                # Return the uncoverged values
                return(CAPED,TOB,LNB,IFLAG)

            #
            #   *** Calculate buoyancy   ***
            #
            # Parcel total mixing ratio: either reversible (ascent_flag=0) or pseudo-adiabatic (ascent_flag=1)
            RMEAN=ascent_flag*RG+(1-ascent_flag)*RP
            # Parcel and Environmental Density Temperatures at this pressure (E94, EQN. 4.3.1 and 6.3.7)
            TLVR=utilities.Trho(TG,RMEAN,RG)
            TENV=utilities.Trho(T[j],R[j],R[j])
            # Bouyancy of the parcel in the environment (Proxy of E94, EQN. 6.1.5)
            TVRDIF[j,]=TLVR-TENV
            

    #
    #  ***  Begin loop to find Positive areas (PA) and Negative areas (NA) ***
    #                  ***  and CAPE from reversible ascent ***
    NA=0.0
    PA=0.0
    
    #
    #   ***  Find maximum level of positive buoyancy, INB    ***
    #
    INB=0
    for j in range(nlvl-1, jmin, -1):
        if (TVRDIF[j] > 0):
            INB=max([INB,j])
            
    # CHECK: Is the LNB higher than the surface? If not, return zero CAPE  
    if (INB==0):
        CAPED=0
        TOB=T[0]
        LNB=P[INB]
#         TOB=np.nan
        LNB=0
        # Return the unconverged values
        return(CAPED,TOB,LNB,IFLAG)
    
    # if check is passed, continue with the CAPE calculation
    else:
    
    #
    #   ***  Find positive and negative areas and CAPE  ***
    #                  via E94, EQN. 6.3.6)
    #
        for j in range(jmin+1, INB+1, 1):
            PFAC=constants.RD*(TVRDIF[j]+TVRDIF[j-1])*(P[j-1]-P[j])/(P[j]+P[j-1])
            PA=PA+max([PFAC,0.0])
            NA=NA-min([PFAC,0.0])

    #
    #   ***   Find area between parcel pressure and first level above it ***
    #
        PMA=(PP+P[jmin])
        PFAC=constants.RD*(PP-P[jmin])/PMA
        PA=PA+PFAC*max([TVRDIF[jmin],0.0])
        NA=NA-PFAC*min([TVRDIF[jmin],0.0])
        
    #
    #   ***   Find residual positive area above INB and TO  ***
    #         and finalize estimate of LNB and its temperature
    #
        PAT=0.0
        TOB=T[INB]
        LNB=P[INB]
        if (INB < nlvl-1):
            PINB=(P[INB+1]*TVRDIF[INB]-P[INB]*TVRDIF[INB+1])/(TVRDIF[INB]-TVRDIF[INB+1])
            LNB=PINB
            PAT=constants.RD*TVRDIF[INB]*(P[INB]-PINB)/(P[INB]+PINB)
            TOB=(T[INB]*(PINB-P[INB+1])+T[INB+1]*(P[INB]-PINB))/(P[INB]-P[INB+1])
    
    #
    #   ***   Find CAPE  ***
    #            
        CAPED=PA+PAT-NA
        CAPED=max([CAPED,0.0])
        # set the flag to OK if procedure reached this point
        IFLAG=1
        # Return the calculated outputs to the above program level 
        return(CAPED,TOB,LNB,IFLAG)
