from typing import Union

import numpy as np
from math import e

g: float = 9.81


def newmark_critical_accel(
    factor_of_safety: Union[float, np.ndarray], slope: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """
    Calculates the critical acceleration, i.e. the acceleration at which the
    slope fails.

    :param factor_of_safety:
        Static Factor of Safety for the site in question.

    :param slope:
        Slope of site in degrees.

    :returns:
        Critical acceleration in terms of g (9.81 m s^-2)
    """

    crit_accel = (factor_of_safety - 1) * np.sin(np.radians(slope)) * g
    print(factor_of_safety)
    print(crit_accel)
    print("crit_accel")
    if np.isscalar(crit_accel):
        return max([0.0, crit_accel])
    else:
        return np.array([max([0.0, ca]) for ca in crit_accel])
        


def newmark_displ_from_pga_M(
    pga: Union[float, np.ndarray],
    critical_accel: Union[float, np.ndarray],
    M: float,
    c1: float = -2.71,
    c2: float = 2.335,
    c3: float = -1.478,
    c4: float = 0.424,
    crit_accel_threshold: float = 0.05,
) -> Union[float, np.ndarray]:
    """
    Landslide displacement calculated from PGA, M, and critical acceleration,
    from Jibson (2007), equation 7.

    :param pga:
        Peak Ground Acceleration, measured in g.

    :param critical_accel:
        Critical Acceleration, measured in g; this is the acceleration at which
        the slope fails.

    :param M:
        Magnitude (Mw) of the earthquake.

    :param c1:
        Empirical constant

    :param c2:
        Empirical constant

    :param c3:
        Empirical constant

    :param c4:
        Empirical constant

    :param crit_accel_threshold:
        Lower bound for critical acceleration. Values close to or below zero
        may reflect an incorrect factor of safety calculation or site
        characterization, and produce unreasonably high displacements.
        Defaults to 0.05

    :returns:
        Predicted earthquake displacement in meters.
    """

    # Corrections of invalid values
    if np.isscalar(pga):
        if pga == 0.0:
            pga = 1e-5
    else:
        pga[pga == 0.0] = 1e-5

    accel_ratio = critical_accel / pga

    # Corrects too high or too low accel ratios (it breaks powers below)
    if np.isscalar(accel_ratio):
        if accel_ratio > 1.0:
            accel_ratio = 1.0
        elif accel_ratio <= crit_accel_threshold:
            accel_ratio == crit_accel_threshold
    else:
        accel_ratio[accel_ratio > 1.0] = 1.0
        accel_ratio[accel_ratio <= crit_accel_threshold] = crit_accel_threshold

    pow_1 = (1 - accel_ratio) ** c2
    pow_2 = accel_ratio**c3

    pow_prod = pow_1 * pow_2

    # Fix zero products of powers (which breaks log below)
    if np.isscalar(pow_prod):
        if pow_prod == 0.0:
            pow_prod = 1e-100
    else:
        pow_prod[pow_prod == 0.0] = 1e-100

    log_d = c1 + np.log10(pow_prod) + c4 * M

    d_cm = 10.0 ** (log_d)

    # Zero product of powers fix re-fixed to zero displacement
    if np.isscalar(d_cm):
        if d_cm < 1e-99:
            d_cm = 0.0
    else:
        d_cm[d_cm < 1e-99] = 0.0

    # Convert output to m
    d_m = d_cm / 100.0

    return d_m


def prob_failure_given_displacement(
    displacement: Union[float, np.ndarray],
    c1: float = 0.335,
    c2: float = -0.048,
    c3: float = 1.565,
) -> Union[float, np.ndarray]:
    """
    Computes the probability of ground failure using a Weibull
    model based on the predicted Newmark displacements.

    Constants from Jibson et al., 2000 for the Northridge earthquake.

    :param displacement:
        Predicted Newmark displacement at a site, in meters (will be converted
        to cm in the function).  Can be scalar or array.

    :returns:
        Scalar or array of ground failure probability.
    """

    Dn = displacement * 100.0

    return c1 * (1 - np.exp(c2 * Dn**c3))



def Cho_Rathje_2022_PGV(PGV_, Tslope_, crit_accel_, H_ratio_):

    '''
    Calculation of earthquake-induced displacements of landslides by Eq.4a Cho&Rathje(2022)
    
    PGV is the peak ground velocity in cm/s
    crit_accel is the critical acceleration of the landslide in units of g
    Tslope is the fundamental period of the slope = 4* Hslope / vs with vs equal to shear wave velocity
    H_ratio is the ratio between the depth of the landslide and the height of the slope (adimensional)
    Dn is the displacement in cm but then converted in m

    ''' 
    Disp=[]
    for H_ratio, PGV, Tslope, crit_accel in zip(H_ratio_, PGV_, Tslope_, crit_accel_):
        if H_ratio <= 0.6:
            a0 = - 1.01 + 1.57*np.log(Tslope) - 0.25*np.log(crit_accel)
            a1 = 0.81 - 1.05*np.log(Tslope) - 0.60*np.power((np.log(Tslope)), 2)
            log_Disp = a0 + a1*np.log(PGV)
            Disp_ = np.power(e, log_Disp)  #disp in cm
            Disp_ = Disp_/100              #disp in m

        else:
            a0 = - 4.50 - 1.37*np.log(crit_accel)
            a1 = 1.51 + 0.10*np.log(crit_accel)
            log_Disp = a0 + a1*np.log(PGV)
            Disp_ = np.power(e, log_Disp)  #disp in cm
            Disp_ = Disp_/100              #disp in m
        
        Disp.append(Disp_)

    return Disp

def Fotopoulou_Pitilakis_2015_PGV_M(PGV, M, crit_accel):
    '''

    Computation of earthquake-induced displacements of landslides by eq. 8-12 from Fotopoulo & Pitikalis (2015)

    Disp is the displacements in meters
    PGA is the peak ground acceleration in g
    PGV is the peak ground velocity in cm/s
    IA is the arias intensity in m/s
    M is the moment magnitude


    '''

    log_Disp = -9.891 + 1.873*np.log(PGV) - 5.964*crit_accel + 0.285*M
    Disp = np.power(e, log_Disp) #return disp in m
    
    
    return Disp
    
def Fotopoulou_Pitilakis_2015_PGA_M(PGA, M, crit_accel):

    log_Disp = - 2.965 + 2.127*np.log(PGA) - 6.583*crit_accel + 0.535*M
    Disp = np.power(e, log_Disp)   #return disp in m
    
    return Disp
    
    
def Fotopoulou_Pitilakis_2015_PGA_M_b(PGA, M, crit_accel):

    log_Disp = -10.246 - 2.165*np.log(crit_accel/PGA) + 7.844*crit_accel + 0.654*M
    Disp = np.power(e, log_Disp) #return disp in m
    
    return Disp
    
    
    
def Fotopoulou_Pitilakis_2015_PGV_PGA(PGV, PGA, crit_accel):

    log_Disp = -8.360 + 1.873*np.log(PGV) - 0.347*np.log(crit_accel/PGA) - 5.964*crit_accel
    Disp = np.power(e, log_Disp) #return disp in m
    
    return Disp
    
    
def Saygili_Rathje_2008(PGA, PGV, crit_accel):

    '''

    Computation of earthquake-induced displacements of landslides by eq. 6 from Sayigili & Rathje (2008)

    Disp is the displacements in cm but then converted in m
    PGA is the peak ground acceleration in g
    crit_accel is the critical acceleration of the landslide in g
    PGV is the peak ground velocity in cm/s


    '''
    
    log_Disp = -1.56 - 4.58*(crit_accel/PGA) - 20.84*(np.power((crit_accel/PGA), 2)) + 44.75*(np.power((crit_accel/PGA), 3)) - 30.50*(np.power((crit_accel/PGA), 4)) - 0.64*(np.log(PGA)) + 1.55*(np.log(PGV))
    Disp = np.power(e, log_Disp)
    Disp =  Disp/100
    
    return Disp
    
def Rathje_Saygili_2009_PGA_M(PGA, M, crit_accel):

    '''

    Computation of earthquake-induced displacements of landlsides by eq.8 from Sayigili & Rathje (2009)
    ls_disp is in cm but then converted in m
    crit_accel is the critical acceleration of the landslide in g
    PGA is the peak ground acceleration in g
    M is the moment magnitude

    '''

    log_Disp = 4.89 -4.85*(crit_accel/PGA) - 19.64*(np.power((crit_accel/PGA), 2)) + 42.49*(np.power((crit_accel/PGA), 3)) - 29.06*(np.power((crit_accel/PGA), 4)) + 0.72*(np.log(PGA)) + 0.89*(M-6)
    Disp = np.power(e, log_Disp) #in cm
    Disp = Disp/100             #conversion in m
        
    
    return Disp    
    
