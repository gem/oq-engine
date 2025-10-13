# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2025, GEM Foundation
# 
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import numpy as np
from math import e
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

g: float = 9.81

def critical_accel(
    factor_of_safety: np.ndarray,
    slope: np.ndarray,
    crit_accel_threshold=0.0001,
) -> np.ndarray:
    """
    Calculates the critical acceleration, i.e. the acceleration at which the
    slope safety factor is 1.
    
    Reference: Newmark, N. M. (1965). Effects of earthquakes on dams
    and embankments. Geotechnique, 15(2), 139-160.
    https://www.icevirtuallibrary.com/doi/abs/10.1680/geot.1965.15.2.139.

    :param factor_of_safety:
        Static Factor of Safety 

    :param slope:
        slope angle in m/m.

    :returns: 
        crit_accel: critical acceleration in g units
    """    
    crit_accel = (factor_of_safety - 1) * np.sin(np.arctan(slope))
    return np.array([max([crit_accel_threshold, ca]) for ca in crit_accel])
                     

def jibson_2007_model_a( 
    pga: np.ndarray,
    crit_accel: np.ndarray,
    c1: float = 0.215,
    c2: float = 2.341,
    c3: float = -1.438,
    accel_ratio_threshold: float = 0.05,
) -> np.ndarray:
    """
    Calculates earthquake-induced displacements of landslides from PGA, and
    critical acceleration, from Jibson (2007), equation 6.
    
    Reference: Jibson, R.W. (2007). Regression models for estimating coseismic
    landslide displacement. Engineering Geology, 91(2-4), 209-218. 
    https://doi.org/10.1016/j.enggeo.2007.01.013.

    :param pga:
        Peak Ground Acceleration, measured in g.

    :param crit_accel:
        Critical Acceleration, measured in g; this is the acceleration at
        which the slope failures occur.

    :param c1:
        Empirical constant

    :param c2:
        Empirical constant

    :param c3:
        Empirical constant

    :param accel_ratio_threshold:
        Lower bound for the acceleration ratio. Values close to or below zero
        may reflect an incorrect factor of safety calculation or site
        characterization, and produce unreasonably high displacements.
        Defaults to 0.05

    :returns:
        Disp: Earthquake-induced displacements in m.
    """
    Disp = np.zeros_like(pga)
    ok = pga > 0
    accel_ratio = crit_accel[ok] / pga[ok]

    # Corrects too high or too low accel ratios 
    accel_ratio[accel_ratio > 1.0] = 1.0
    accel_ratio[accel_ratio <= accel_ratio_threshold] = \
        accel_ratio_threshold

    pow_1 = (1 - accel_ratio) ** c2
    pow_2 = accel_ratio**c3
    pow_prod = pow_1 * pow_2
    pow_prod[pow_prod == 0.0] = 1e-100  # fix zeros
    log_Disp = c1 + np.log10(pow_prod)

    Disp_cm = 10.0 ** log_Disp
    # convert output to m
    Disp[ok] = Disp_cm / 100.0
    return Disp


def jibson_2007_model_b(
    pga: np.ndarray,
    crit_accel: np.ndarray,
    mag: float,
    c1: float = -2.71,
    c2: float = 2.335,
    c3: float = -1.478,
    c4: float = 0.424,
    accel_ratio_threshold: float = 0.05,
) -> np.ndarray:
    """
    Computes earthquake-induced displacements of landlsides from 
    pga, magnitude, and critical acceleration, from Jibson (2007), equation 7.
    The use of this model is reccomended for magnitude >= 5.3 and <= 7.6.
    
    Reference: Jibson, R.W. (2007). Regression models for estimating
    coseismic landslide displacement.
    Engineering Geology, 91(2-4), 209-218. 
    https://doi.org/10.1016/j.enggeo.2007.01.013.

    :param pga:
        Peak Ground Acceleration, measured in g

    :param crit_accel:
        Critical Acceleration, measured in g; this is the acceleration at which
        the slope fails.

    :param mag:
        Moment magnitude  of the earthquake

    :param c1:
        Empirical constant

    :param c2:
        Empirical constant

    :param c3:
        Empirical constant

    :param c4:
        Empirical constant

    :param accel_ratio_threshold:
        Lower bound for the acceleration ratio. Values close to or below zero
        may reflect an incorrect factor of safety calculation or site
        characterization, and produce unreasonably high displacements.
        Defaults to 0.05

    :returns:
        Disp: Earthquake-induced displacements in meters.
    """
    if mag < 5.3 or mag > 7.6:
        logging.warning('The use of this model is recommended for '
                        f'magnitudes in the range 5.3 - 7.6 (current: {mag})')

    Disp = np.zeros_like(pga)
    ok = pga > 0
    accel_ratio = crit_accel[ok] / pga[ok]

    # Corrects too high or too low accel ratios 
    accel_ratio[accel_ratio > 1.0] = 1.0
    accel_ratio[accel_ratio <= accel_ratio_threshold] = accel_ratio_threshold

    pow_1 = (1 - accel_ratio) ** c2
    pow_2 = accel_ratio ** c3
    pow_prod = pow_1 * pow_2
    pow_prod[pow_prod == 0.0] = 1e-100  # fix zeros
    log_Disp = c1 + np.log10(pow_prod) + c4 * mag

    Disp_cm = 10.0 ** log_Disp

    # Convert output to m
    Disp[ok] = Disp_cm / 100.0
    
    return Disp


def cho_rathje_2022(pgv_, tslope_, crit_accel_, hratio_):
    '''
    Calculates earthquake-induced displacements of landslides by
    Eq.4a, Cho&Rathje(2022)
    
    Reference: Cho, Y., & Rathje, E. M. (2022). Generic predictive model
    of earthquake-induced slope displacements derived from finite-element
    analysis. Journal of Geotechnical and Geoenvironmental Engineering,
    148(4), 04022010.
    https://doi.org/10.1061/(ASCE)GT.1943-5606.0002757
    
    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param crit_accel:
        Critical acceleration of the landslide, measured in units of g
    :param tslope:
        Fundamental period of the slope, measured in s. It is calculated as 
        tslope = (4* Hslope / vs) with vs = material shear wave velocity and 
        Hslope = slope height
    :param hratio:
        Ratio between the depth of the landslide and the height of the slope
        (adimensional)
        
    :returns:   
        Disp: Earthquake-induced displacement in m.
    '''
    Disp = np.zeros_like(pgv_)
    for i, (hratio, pgv, tslope, crit_accel) in enumerate(
            zip(hratio_, pgv_, tslope_, crit_accel_)):
        if pgv == 0:
            continue
        elif hratio <= 0.6:
            a0 = - 1.01 + 1.57*np.log(tslope) - 0.25*np.log(crit_accel)
            a1 = 0.81 - 1.05*np.log(tslope) - 0.60*np.power((np.log(tslope)), 2)
            log_Disp = a0 + a1*np.log(pgv)
            Disp_ = np.power(e, log_Disp)  #Disp in cm
            Disp[i] = Disp_/100              #Disp in m
        else:
            a0 = - 4.50 - 1.37*np.log(crit_accel)
            a1 = 1.51 + 0.10*np.log(crit_accel)
            log_Disp = a0 + a1*np.log(pgv)
            Disp_ = np.power(e, log_Disp)  #Disp in cm
            Disp[i] = Disp_/100            #Disp in m
    return Disp


def fotopoulou_pitilakis_2015_model_a(pgv, mag, crit_accel):
    '''
    Calculates earthquake-induced displacements of landslides by eq.8,
    Fotopoulo & Pitikalis (2015).
    Reference: Fotopoulou, S. D., & Pitilakis, K. D. (2015). Predictive
    relationships for seismically  induced slope displacements using numerical
    analysis results. Bulletin of Earthquake Engineering, 
    13, 3207-3238. 
    https://doi.org/10.1007/s10518-015-9768-4
    
    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param mag:
        Moment magnitude
    :param crit_accel
        Critical acceleration of the landslide, measured in units of g
    
    :returns:
        Disp: Earthquake-induced displacements in m.
    '''
    Disp = np.zeros_like(pgv)
    ok = pgv > 0
    log_Disp = (-9.891 + 1.873*np.log(pgv[ok]) -
                5.964*crit_accel[ok] + 0.285*mag)
    Disp[ok] = np.power(e, log_Disp)
    return Disp

    
def fotopoulou_pitilakis_2015_model_b(pga, mag, crit_accel):
    '''
    Calculates earthquake-induced displacements of landslides by eq.9,
    Fotopoulo & Pitikalis (2015)
    
    Reference: Fotopoulou, S. D., & Pitilakis, K. D. (2015).
    Predictive relationships for seismically induced slope displacements
    using numerical analysis results. Bulletin of Earthquake Engineering, 
    13, 3207-3238. 
    https://doi.org/10.1007/s10518-015-9768-4
    
    :param pga:
        Peak Ground Acceleration, measured in units of g
    :param mag:
        Moment magnitude
    :param crit_accel
        Critical acceleration of the landslide, measured in units of g
    
    :returns:
        Disp: Earthquake-induced displacements in m.
    '''
    Disp = np.zeros_like(pga)
    ok = pga > 0
    log_Disp = (-2.965 + 2.127*np.log(pga[ok]) -
                6.583*crit_accel[ok] + 0.535*mag)
    Disp[ok] = np.power(e, log_Disp)   #return Disp in m
    return Disp
    
    
def fotopoulou_pitilakis_2015_model_c(pga, mag, crit_accel):
    '''
    Calculates earthquake-induced displacements of landslides by eq.10, Fotopoulo & Pitikalis (2015).
    Compared to model_b from Fotopoulou & Pitilakis (2015), pga appears in terms of ratio with the critical
    acceleration.
    
    Reference: Fotopoulou, S. D., & Pitilakis, K. D. (2015). Predictive relationships for seismically 
    induced slope displacements using numerical analysis results. Bulletin of Earthquake Engineering, 
    13, 3207-3238. 
    https://doi.org/10.1007/s10518-015-9768-4
    
    :param pga:
        Peak Ground Acceleration, measured in units of g
    :param mag:
        Moment magnitude
    :param crit_accel
        Critical acceleration of the landslide, measured in units of g
    
    :returns:
        Disp: Earthquake-induced displacements in m.
    '''    
    accel_ratio_threshold: float = 0.05
    
    # Corrections of invalid values
    ok = pga > 0
    Disp = np.zeros_like(pga)
    accel_ratio = crit_accel[ok] / pga[ok]
    
    # Corrects too high or too low accel ratios 
    accel_ratio[accel_ratio > 1.0] = 1.0
    accel_ratio[accel_ratio <= accel_ratio_threshold] = accel_ratio_threshold
    
    log_Disp = (-10.246 - 2.165 * np.log(accel_ratio) +
                7.844 * crit_accel[ok] + 0.654*mag)
    Disp[ok] = np.power(e, log_Disp) #return Disp in m
    return Disp
    
    
def fotopoulou_pitilakis_2015_model_d(pgv, pga, crit_accel):
    '''
    Calculates earthquake-induced displacements of landslides by eq.12, Fotopoulo & Pitikalis (2015).
    
    Reference: Fotopoulou, S. D., & Pitilakis, K. D. (2015). Predictive relationships for seismically 
    induced slope displacements using numerical analysis results. Bulletin of Earthquake Engineering, 
    13, 3207-3238. 
    https://doi.org/10.1007/s10518-015-9768-4
    
    :param pga:
        Peak Ground Acceleration, measured in units of g
    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param crit_accel
        Critical acceleration of the landslide, measured in units of g
    
    :returns:
        Disp: Earthquake-induced displacements in m.
        
    '''
    Disp = np.zeros_like(pga)
    accel_ratio_threshold: float = 0.05
    ok = (pga > 0) & (pgv > 0)        
    accel_ratio = crit_accel[ok] / pga[ok]
    
    # Corrects too high or too low accel ratios 
    accel_ratio[accel_ratio > 1.0] = 1.0
    accel_ratio[accel_ratio <= accel_ratio_threshold] = accel_ratio_threshold
    
    log_Disp = (-8.360 + 1.873*np.log(pgv[ok]) -
                0.347*np.log(accel_ratio) - 5.964*crit_accel[ok])
    Disp[ok] = np.power(e, log_Disp) #return Disp in m
    return Disp
    
    
def saygili_rathje_2008(pga, pgv, crit_accel):
    '''
    Computes earthquake-induced displacements of landslides by eq.6, Sayigili & Rathje (2008).
    
    Reference:  Saygili, G., & Rathje, E. M. (2008). Empirical predictive models for earthquake-induced 
    sliding displacements of slopes. Journal of geotechnical and geoenvironmental engineering, 134(6), 790-803.
    https://doi.org/10.1061/(ASCE)1090-0241(2008)134:6(790).
    
    :param pga:
        Peak Ground Acceleration, measured in units of g
    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param crit_accel:
        Critical acceleration of the landslide, measured in units of g
        
    :returns:
        Disp: Earthquake-induced displacements in m.
    ''' 
    accel_ratio_threshold: float = 0.05
    
    Disp = np.zeros_like(pga)
    ok = pga > 0

    accel_ratio = crit_accel[ok] / pga[ok]
    
    # Corrects too high or too low accel ratios 
    accel_ratio[accel_ratio > 1.0] = 1.0
    accel_ratio[accel_ratio <= accel_ratio_threshold] = accel_ratio_threshold
    
    log_Disp = (-1.56 - 4.58*accel_ratio -
                20.84*accel_ratio**2 +
                44.75*accel_ratio**3 -
                30.50*accel_ratio**4 -
                0.64*np.log(pga[ok]) +
                1.55*np.log(pgv[ok]))
    Disp_cm = np.power(e, log_Disp)
    Disp[ok] =  Disp_cm / 100
    return Disp
    
    
def rathje_saygili_2009(pga, mag, crit_accel):
    '''
    Calculates earthquake-induced displacements of landlsides by eq.8, Sayigili & Rathje (2009)
    
    Reference: Rathje, E. M., & Saygili, G. (2009).
    Probabilistic assessment of earthquake-induced 
    sliding displacements of natural slopes. Bulletin of the
    New Zealand Society for Earthquake Engineering, 42(1), 18-27.
    https://doi.org/10.5459/bnzsee.42.1.18-27.

    :param pga:
        Peak Ground Acceleration, measured in units of g
    :param mag:
        Moment magnitude
    :param crit_accel:
        Critical acceleration of the landslide, measured in units of g
    
    :returns:
        Disp: Earthquake-induced displacements in m.
    '''
    accel_ratio_threshold: float = 0.05
    
    # Corrections of invalid values
    ok = pga > 0
    Disp = np.zeros_like(pga)
    accel_ratio = crit_accel[ok] / pga[ok]
    
    # Corrects too high or too low accel ratios 
    accel_ratio[accel_ratio > 1.0] = 1.0
    accel_ratio[accel_ratio <= accel_ratio_threshold] = accel_ratio_threshold
        
    log_Disp = (4.89 -4.85*accel_ratio -
                19.64*accel_ratio**2 +
                42.49*accel_ratio**3 -
                29.06*accel_ratio**4 +
                0.72*np.log(pga[ok]) + 0.89*(mag-6))
    Disp_cm = np.power(e, log_Disp) # in cm
    Disp[ok] = Disp_cm/100     # conversion in m
    return Disp

    
def jibson_etal_2000(ia, crit_accel):
    ''' 
    Calculates earthquake-induced displacements of landslides from arias intensity
    and critical acceleration according to eq. 3 from Jibson et al. (2000).
    
    Reference: Jibson, R. W., Harp, E. L., & Michael, J. A. (2000). A method for 
    producing digital probabilistic seismic landslide hazard maps. Engineering 
    geology, 58(3-4), 271-289.
    Jibson, R.W., Harp, E.L., & Michael, J.A. (2000). A method for producing digital probabilistic
    seismic landslide hazard maps. Engineering Geology, 58(3-4), 271-289.
    https://doi.org/10.1016/S0013-7952(00)00039-9.
    
    :param ia:
        Arias Intensity, measured in m/s
    
    :param crit_accel:
        Critical acceleration of the landslide, measured in g units
    
    :returns:
        Disp: Earthquake-induced displacements in m.
    '''
    Disp = np.zeros_like(ia)
    ok = ia > 0
    log_Disp = 1.521*np.log10(ia[ok]) - 1.993*np.log10(crit_accel[ok]) - 1.546   
    Disp_cm = np.power(10, log_Disp)
    Disp[ok] = Disp_cm/100
    return Disp
