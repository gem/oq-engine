#!/usr/bin/env python
# coding: utf-8

# In[2]:


"""
Module exports :class:`bahrampouriEtAl2021IA`,
class:`bahrampouriEtAl2021Asc`,
class:`bahrampouriEtAl2021SSlab`,
class:`bahrampouriEtAl2021SInter`,
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import IA
from scipy.interpolate import interp1d
from math import sin, cos, sqrt, atan2, radians
from openquake.hazardlib.geo.geodetic import npoints_towards
from openquake.hazardlib.geo import Point
import pandas as pd


# In[3]:
# coordinates from the author
##Kyushu - VOLCANIC_FRONT_KI_LATS 
x2 = np.array([27.250, 28.800, 30.433, 32.767, 33.567, 34.367])
##VOLCANIC_FRONT_KI_LONS 
y2 = np.array([127.067, 128.983, 130.217, 130.817, 131.600, 131.850])
##Honshu - VOLCANIC_FRONT_HHI_LATS 
x3 = np.array([45.417, 44.450, 43.683, 43.600, 43.500, 43.400, 42.050, 41.267, 40.450, 
               39.033, 37.733, 36.600, 35.383, 33.133, 30.483, 28.317, 25.417])

##VOLCANIC_FRONT_HHI_LONS 
y3 = np.array([148.583, 146.917, 144.717, 144.017, 142.683, 141.517, 140.667, 141.117,
               141.000, 140.583, 140.133, 138.367, 138.733, 139.750, 140.300, 140.567, 141.267])


def _compute_magnitude(ctx, C, trt):
    
    """
    Compute the source term described in Eq. 7 for ASC and 9 for subduction:
    `` a1 + a2 * M + a3 * max(M - a4, 0) + a7 * ln(Ztor + 1)------ASC
        a1 + a2 * M + a3 * max (M - a4, 0) + a5 * max(M - a6, 0) + a7 * ln(Ztor + 1) + a8 * Finter-------Subduction``
        
        Finter = 0 (subduction interslab)
        Finter = 1 (subduction interface)
    """
    for m, z in zip(ctx.mag, ctx.ztor):
        if trt == const.TRT.ACTIVE_SHALLOW_CRUST:
            fsource = C['a1'] + (C['a2'] * m) + (C['a3'] * max((m- C['a4']),0 )) + (C['a7'] * np.log((z)+1))
        
        else:
            if trt == const.TRT.SUBDUCTION_INTERFACE:
                Finter = 1
            elif trt == const.TRT.SUBDUCTION_INTRASLAB:
                Finter = 0
            fsource = C['a1'] + (C['a2'] * m) + (C['a3'] * max((m - C['a4']),0 )) +(C['a5'] * max((z - C['a6']),0 ))+ (C['a7'] * np.log((z)+1)) +(C['a8'] * Finter)
    return fsource


# In[4]:


def _get_source_saturation_term (ctx, C):
    """
    compute the near source saturation as described in Eq. 11. This is common for all the TRTs
    ``h = b5 +b6*(M-b7)..... M<=b7
    h = b9 + b10*(M - b7)+b11*(M - b7)**2+b12*(M - b7)**3 ...b7< M <= b8
    h = b13 + b14*(M - b8).....M>b8``
    """
    h = C['b13'] + (C['b14'] * (ctx.mag - C['b8']))
    above = ctx.mag <= C['b7']
    h[tuple(above)] = C['b5'] + C['b6'] * (ctx.mag[tuple(above)]-C['b7'])
    below = [(ctx.mag < C['b7']) & (ctx.mag <= C['b8'])]
    h[tuple(below)] = C['b9'] + (C['b10']*(ctx.mag[tuple(below)]-C['b7']))+(C['b11']*(ctx.mag[tuple(below)]-C['b7'])**2) + (C['b12']*(ctx.mag[tuple(below)]-C['b7'])**3)
        
    return h
    


# In[5]:


def _get_site_term(ctx, C):
    """
    compute site scaling as described in Eq.12
    Fsite = c1*ln(vs30)

    """
    fsite = C['c1']*np.log(ctx.vs30)
    return fsite


# In[6]:


def _get_stddevs(C):
    """
    The authors have provided the values of sigma = np.sqrt(tau**2+phi_ss**2+phi_s2s**2)
    
    The within event term (phi) has been calculated by combining the phi_ss and phi_s2s
    """
    sig = C['sig']
    tau = C['tau']
    phi = np.sqrt(C['phi_ss']**2 +C['phi_s2s']**2)
    return sig, tau, phi


# In[1]:

def _compute_forearc_distances(x_values, site_distance, volcano_trace, dist):
    ## tracing on the volcanic arc from lower lat to higher lat, the sites on the right belong to forearc
#     
    under_curve = site_distance < volcano_trace

    ### to calculate rrup in the forearc region
    if under_curve.all():
        lat1 = radians(x_values[under_curve][0])
        lon1 = radians(site_distance[under_curve][0])
        lat2 = radians(x_values[under_curve][-1])
        lon2 = radians(site_distance[under_curve][-1])

        # approximate radius of earth in km
        R = 6373.0
        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        r2 = np.round(R * c, 1) ##forearc
        r1 = np.round(dist - r2, 1)##backarc
    else:
        r2 = 0
        r1 = dist
    return r1, r2


def _interpolation (x1, x2, f1, f2):
    x_interp = np.linspace(max(x1.min(), x2.min()), min(x1.max(), x2.max()), 100) ## common x values
    y1_interp = f1(x_interp) ## rupture distance
    y2_interp = f2(x_interp) ## volcano
    return x_interp, y1_interp, y2_interp

def _get_intersection(ctx):

    f2 = interp1d(x2, y2, kind = 'linear', bounds_error=False, fill_value='extrapolate')
    f3 = interp1d(x3, y3, kind = 'linear', bounds_error=False, fill_value='extrapolate')

    
    rrup_b=np.array([])
    rrup_f=np.array([])
    for i, (dist, lo, la) in enumerate(zip(ctx.rrup,ctx.hypo_lon, ctx.hypo_lat)):
        hypoc = Point(lo, la, 0)  

        y1, x1, deps = npoints_towards(lon=hypoc.longitude, 
                                   lat=hypoc.latitude, depth=0, 
                                   azimuth=45, hdist=dist, vdist=0, 
                                   npoints=dist/5)
        f1 = interp1d(x1, y1, kind = 'linear', bounds_error=False, fill_value='extrapolate')
    

        index = np.where(np.logical_and(x1 >= f2.x.min(), x1<= f2.x.max())) ## checking interpolation range
        index_new = np.where(np.logical_and(x1 >= f3.x.min(), x1<= f3.x.max()))
        if len(index) & len(index_new) ==0: ## for sites not in the volcanic region
            idx = 0
            rrup_b = 0
            rrup_f = 0
        if len(index) != 0:
        ##stage 1 - checking if the site is near Kyushu volcanic arc
            x_interp, y1_interp, y2_interp = _interpolation(x1, x2, f1, f2)
            idx = np.argwhere(np.diff(np.sign(y1_interp - y2_interp))).flatten()
            rrup_b_1, rrup_f_1 = _compute_forearc_distances(x_interp, y1_interp, y2_interp, dist)

            if len(idx) == 0: ## if no intersection with Kyushu volcanic arc
            ##stage 2 - checking if the site is intersecting with the honshu voclanic arc
                x_interp, y1_interp, y3_interp = _interpolation(x1, x3, f1, f3)
                idx_new = np.argwhere(np.diff(np.sign(y1_interp - y3_interp))).flatten()
                rrup_b_2, rrup_f_2 = _compute_forearc_distances(x_interp, y1_interp, y3_interp, dist)
                if len(idx_new) ==0: ## no intersection with both the arcs
                    if rrup_b_1 < rrup_f_2: ## finding the nearest voclanic arc
                        rrup_b = np.append(rrup_b, rrup_b_1)
                        rrup_f= np.append(rrup_f, rrup_f_1)
                    else:
                        rrup_b = np.append(rrup_b, rrup_b_2)
                        rrup_f= np.append(rrup_f, rrup_f_2)
                else:
                    rrup_b = np.append(rrup_b, rrup_b_2)
                    rrup_f= np.append(rrup_f, rrup_f_2)
            else:
                rrup_b = np.append(rrup_b, rrup_b_1)
                rrup_f= np.append(rrup_f, rrup_f_1)
        else: 
            x_interp, y1_interp, y3_interp = _interpolation(x1, x3, f1, f3)
            idx_new = np.argwhere(np.diff(np.sign(y1_interp - y3_interp))).flatten()
            rrup_b_2, rrup_f_2 = _compute_forearc_distances(x_interp, y1_interp, y3_interp, dist)
            rrup_b = np.append(rrup_b, rrup_b_2)
            rrup_f= np.append(rrup_f, rrup_f_2)
        
    return rrup_b, rrup_f, idx


# In[8]:


def _compute_distance(ctx, C, trt):
    """
    fpath = b1 * ln(sqrt(rrup^2+(10^h)^2)) + b3b * rrupb + b3f * rrupf + b4m * cm + b4k * ck ---ASC
    fpath = (b1 +b2*Finter)*ln(sqrt(rrup^2+(10^h)^2))+ b3b * rrupb + b3f * rrupf + b4m * cm + b4k * ck ---subduction
    f = forearc
    b = backarc
    Cm is 1 if the path from the source to the site crosses the volcanic front in Honshu and
    Hokkaido and 0 otherwise; 
    CK is 1 if the path from the source to the site crosses the volcanic 
    front in Kyushu and 0 otherwise;
    """
    rrup_b, rrup_f, idx = _get_intersection(ctx)
    if len(idx) == 0:
        cm = 1 # temporary fix
        ck = 0 # temporary fix
    else:
        cm = 0
        ck = 1


    if trt == const.TRT.ACTIVE_SHALLOW_CRUST:
        fpath = C['b1']*(np.log(np.sqrt((ctx.rrup**2) + ((10**_get_source_saturation_term (ctx, C))**2)))) + C['b3b'] * rrup_b + C['b3f'] * rrup_f + C['b4m']*cm + C['b4k']*ck

    else: 
        if trt == const.TRT.SUBDUCTION_INTERFACE:
            Finter = 1
        elif trt == const.TRT.SUBDUCTION_INTRASLAB:
            Finter = 0

        fpath = (C['b1'] + C['b2']*Finter) * (np.log(np.sqrt((ctx.rrup**2) + ((10**_get_source_saturation_term (ctx, C))**2)))) + C['b3b'] * rrup_b + C['b3f'] * rrup_f  + C['b4m']*cm + C['b4k']*ck
    
    return fpath


# In[10]:


def _get_arias_intensity_term(ctx, C, trt):
    """
    Implementing Eq. 6
    
    """

    ia_l = _compute_magnitude(ctx, C, trt) + _compute_distance (ctx, C, trt) + _get_site_term (ctx, C)
    return ia_l


# In[11]:


def _get_arias_intensity_second_term(ctx, C, trt):
    """
    the second term in Eq. 5 is computed
    
    """
    t1 = []
    for i, x in enumerate(ctx.vs30):
        g = np.exp(C['c3']*(min(ctx.vs30[i], 1100)-280))
        t1.append(g)
    t2 = np.exp(C['c3']*(1100-280))
    t3 = np.log((np.exp(_get_arias_intensity_term(ctx, C, trt))+C['c4'])/C['c4'])
    ia_2 = C['c2'] * (t1 - t2) * t3
    return ia_2


# In[41]:


class BahrampouriEtAl2021Asc(GMPE):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek and Russell A Green 
    developed from the Kiban-Kyoshin network (KiK)-net database. This GMPE is specifically derived
    for arias intensity. This GMPE is described in a paper
    published in 2021 on Earthquake Spectra, Volume 37, Pg 428-448 and
    titled 'Ground motion prediction equations for Arias Intensity using the Kik-net database'.
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are areas intensity
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {IA}

    #: Supported intensity measure component is geometric mean
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.MEDIAN_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see paragraph "Equations for standard deviations", page
    #: 1046.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30 and xvf
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude,ztor
   
    REQUIRES_RUPTURE_PARAMETERS = {'mag','ztor','hypo_lon', 'hypo_lat'}

    #: Required distance measures are rrup (see Table 2,
    #: page 1031).
    REQUIRES_DISTANCES = {'rrup',}
    
    
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Implements mean model (equation 12)
            mean[m] = _get_arias_intensity_term (ctx, C, trt) + _get_arias_intensity_second_term (ctx, C, trt)

            sig[m], tau[m], phi[m] = _get_stddevs(C)

    #: For Ia, coefficients are taken from table 3
    COEFFS = CoeffsTable(sa_damping=5, table="""    IMT      a1     a2      a3    a4    a7     b1      b3b    b3f     b4m     b4k      b5    b6   b7   b8     b9    b10    b11     b12     b13   b14     c1      c2      c3    c4   phi_ss    tau    phi_s2s   sig
    ia    -4.2777 2.9352 -2.3986 7.0 0.7008 -2.8299 -0.0039 -0.0016 -0.6542 -0.2876 0.7497 0.43 5.744 7.744 0.7497 0.43 -0.0488 -0.08312 1.4147 0.235 -1.1076 -0.3607 -0.0077 0.35 0.761585 0.77617 0.840053 1.374096
    """)


# In[42]:


class BahrampouriEtAl2021SInter(GMPE):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek and Russell A Green 
    developed from the Kiban-Kyoshin network (KiK)-net database. This GMPE is specifically derived
    for arias intensity. This GMPE is described in a paper
    published in 2021 on Earthquake Spectra, Volume 37, Pg 428-448 and
    titled 'Ground motion prediction equations for Arias Intensity using the Kik-net database'.
    """
    #: Supported tectonic region type is SUBDUCTION INTERFACE, see title!
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are areas intensity
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {IA}

    #: Supported intensity measure component is geometric mean
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.MEDIAN_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see paragraph "Equations for standard deviations", page
    #: 1046.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30 and xvf
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude,ztor
   
    REQUIRES_RUPTURE_PARAMETERS = {'mag','ztor','hypo_lon', 'hypo_lat'}

    #: Required distance measures are rrup (see Table 2,
    #: page 1031).
    REQUIRES_DISTANCES = {'rrup',}
    
    
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Implements mean model (equation 12)
            mean[m] = _get_arias_intensity_term (ctx, C, trt) + _get_arias_intensity_second_term (ctx, C, trt)

            sig[m], tau[m], phi[m] = _get_stddevs(C)

    #: For Ia, coefficients are taken from table 3
    COEFFS = CoeffsTable(sa_damping=5, table="""    IMT      a1      a2      a3   a4      a5     a6    a7      a8      b1      b2      b3b      b3f      b4m      b4k      b5      b6    b7      b8    b9      b10      b11      b12    b13     b14      c1      c2      c3      c4      phi_ss   tau     phi_s2s    sig
    ia    -0.6169  2.5269  1.531  6.5  -3.2923  7.5  0.5462  0.6249  -2.7534  -0.2816  -0.0044  -0.003  -1.2608  -0.2992  0.7497  0.43  5.744  7.744  0.7497  0.43  -0.0488  -0.08312  1.4147  0.235  -1.3763  -0.1003  -0.0069  0.356  0.73761  0.92179  1.12747  1.632469
    """)


# In[43]:


class BahrampouriEtAl2021SSlab(GMPE):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek and Russell A Green 
    developed from the Kiban-Kyoshin network (KiK)-net database. This GMPE is specifically derived
    for arias intensity. This GMPE is described in a paper
    published in 2021 on Earthquake Spectra, Volume 37, Pg 428-448 and
    titled 'Ground motion prediction equations for Arias Intensity using the Kik-net database'.
    """
    #: Supported tectonic region type is SUBDUCTION INTERFACE, see title!
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Supported intensity measure types are areas intensity
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {IA}

    #: Supported intensity measure component is geometric mean
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.MEDIAN_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see paragraph "Equations for standard deviations", page
    #: 1046.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30 and xvf
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude,ztor
   
    REQUIRES_RUPTURE_PARAMETERS = {'mag','ztor','hypo_lon', 'hypo_lat'}

    #: Required distance measures are rrup (see Table 2,
    #: page 1031).
    REQUIRES_DISTANCES = {'rrup',}
    
    
    def compute(self, ctx:np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Implements mean model (equation 12)
            mean[m] = _get_arias_intensity_term (ctx, C, trt) + _get_arias_intensity_second_term (ctx, C, trt)

            sig[m], tau[m], phi[m] = _get_stddevs(C)

    #: For Ia, coefficients are taken from table 3
    COEFFS = CoeffsTable(sa_damping=5, table="""    IMT      a1      a2      a3   a4      a5     a6    a7      a8      b1      b2      b3b      b3f      b4m      b4k      b5      b6    b7      b8    b9      b10      b11      b12    b13     b14      c1      c2      c3      c4      phi_ss   tau     phi_s2s    sig
    ia    -0.6169  2.5269  1.531  6.5  -3.2923  7.5  0.5462  0.6249  -2.7534  -0.2816  -0.0044  -0.003  -1.2608  -0.2992  0.7497  0.43  5.744  7.744  0.7497  0.43  -0.0488  -0.08312  1.4147  0.235  -1.3763  -0.1003  -0.0069  0.356  0.73761  0.92179  1.12747  1.632469
    """)

