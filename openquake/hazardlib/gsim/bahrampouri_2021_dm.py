#!/usr/bin/env python
# coding: utf-8

# In[2]:


"""
Module exports :class:`BahrampouriEtAl2021dm`,
               :class:`BahrampouriEtAl2021dmASC`
               :class:`BahrampouriEtAl2021dmSSlab` 
               :class:`BahrampouriEtAl2021dmSInter`
"""
import numpy as np

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import RSD595, RSD575


# In[3]:


def _get_source_term(C, ctx):
    """
    Compute the source term described in Eq. 8:
    `` 10.^(m1*(M-m2))+m3``
    m3 = varies as per focal mechanism for ASC and Slab TRTs        
    """
    
    if ctx.rake <= -45.0 and ctx.rake >= -135.0:
        # Normal faulting
        m3 = C["m3_NS"]
        return m3
    elif ctx.rake > 45.0 and ctx.rake < 135.0:
        # Reverse faulting
        m3 = C["m3_RS"]
        return m3
    else:
        # No adjustment for strike-slip faulting
        m3 = C["m3_SS"]
        return m3

    fsource = 10**(C['m1']* (ctx.mag-C['m2']))+ m3
    return fsource


# In[4]:


def _get_path_term(C, ctx):
    """
    Implementing Eqs. 9, 10 and 11
    """
    slope = C['r1'] + C['r2']*(ctx.mag-4.0)
    
    if ctx.mag > C['M2']:
        mse = 1
    elif ctx.mag <= C['M1']:
        mse = 0
    else:
        mse = ((ctx.mag - C['M1'])/(C['M2'] - C['M1']))
    
    if ctx.rrup > C['R1']:
        fpath = slope * (C['R1']+(mse*(ctx.rrup - C['R1'])))
    else:
        fpath = slope * ctx.rrup
        
    return fpath


# In[5]:


def _get_site_term(C, ctx):
    """
    Implementing Eqs. 5, 6 and 12
    """
    mean_z1pt0 = np.exp(((-5.23 / 2.) * np.log(((ctx.vs30 ** 2.) + 412.39 ** 2.)
                                           / (1360 ** 2. + 412.39 ** 2.)))-0.9)
    delta_z1pt0 = ctx.z1pt0 - mean_z1pt0
    
    fsite = C['s1']*np.log(min(ctx.vs30, 600.)/600.) + C['s2']*min(delta_z1pt0, 250.0) + C['s3']
    
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


# In[11]:


class BahrampouriEtAl2021dmAsc(GMPE):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek and Russell A Green 
    developed from the Kiban-Kyoshin network (KiK)-net database. This GMPE is specifically derived
    for significant durations: Ds5-Ds95,D25-Ds75 . This GMPE is described in a paper
    published in 2021 on Earthquake Spectra, Volume 37, Pg 903-920 and
    titled 'Ground motion prediction equations for significant duration using the KiK-net database'.
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are 5 - 95 % Arias and 5 - 75 % Arias
    #: significant duration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {RSD595, RSD575}

    #: Supported intensity measure component is the geometric mean horizontal
    #: component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.MEDIAN_HORIZONTAL

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0'}

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is closest distance to rupture
    REQUIRES_DISTANCES = {'rrup'}
    
    

    def compute(self, ctx, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = np.exp((np.log(_get_source_term(C, ctx) +_get_path_term(C, ctx))) +_get_site_term(C, ctx))
            sig[m], tau[m],phi[m] = _get_stddevs(C)
            
        
    COEFFS = CoeffsTable(table="""
    imt        m1     m2    m3_RS   m3_SS   m3_NS   M1    M2     r1      r2   R1       s1       s2      s3      sig    tau    phi_s2s  phi_ss
    rsd595  0.6899  6.511   4.584   4.252   5.522   4.    6.5  0.21960    0.  60.  -0.3008  0.00119   -0.1107  0.462   0.204   0.185    0.370
    rsd575  0.7966  6.5107 0.06828  0.2902  0.613   4.    6.5  0.1248     0.  60.  -0.1894  0.0003362 -0.03979 0.586   0.233   0.223    0.490
    """)


# In[12]:


class BahrampouriEtAl2021dmSSlab(GMPE):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek and Russell A Green 
    developed from the Kiban-Kyoshin network (KiK)-net database. This GMPE is specifically derived
    for significant durations: Ds5-Ds95,D25-Ds75 . This GMPE is described in a paper
    published in 2021 on Earthquake Spectra, Volume 37, Pg 903-920 and
    titled 'Ground motion prediction equations for significant duration using the KiK-net database'.
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Supported intensity measure types are 5 - 95 % Arias and 5 - 75 % Arias
    #: significant duration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {RSD595, RSD575}

    #: Supported intensity measure component is the geometric mean horizontal
    #: component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
    const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0'}

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is closest distance to rupture
    REQUIRES_DISTANCES = {'rrup'}

        

    def compute(self, ctx, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = np.exp((np.log(_get_source_term(C, ctx) +_get_path_term(C, ctx))) +_get_site_term(C, ctx))
            sig[m], tau[m],phi[m] = _get_stddevs(C)
            

    COEFFS = CoeffsTable(sa_damping=5, table="""
    imt       m1     m2    m3_RS  m3_SS  m3_NS   M1  M2    r1      r2      R1     s1      s2        s3      sig    tau    phi_s2s  phi_ss
    rsd595  0.385  4.1604  5.828  4.231  5.496  5.5  8.0  0.09936  0.02495  200.0  -0.244  0.001409  -0.04109  0.458   0.194   0.245   0.335
    rsd575  0.4232  5.16  0.975  0.3965  0.8712  5.0  8.0  0.057576  0.01316  200.0  -0.1431  0.001248  0.04534  0.593   0.261   0.288   0.449
    """)


# In[12]:


class BahrampouriEtAl2021dmSInter(GMPE):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek and Russell A Green 
    developed from the Kiban-Kyoshin network (KiK)-net database. This GMPE is specifically derived
    for significant durations: Ds5-Ds95,D25-Ds75 . This GMPE is described in a paper
    published in 2021 on Earthquake Spectra, Volume 37, Pg 903-920 and
    titled 'Ground motion prediction equations for significant duration using the KiK-net database'.
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are 5 - 95 % Arias and 5 - 75 % Arias
    #: significant duration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {RSD595, RSD575}

    #: Supported intensity measure component is the geometric mean horizontal
    #: component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
    const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0'}

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is closest distance to rupture
    REQUIRES_DISTANCES = {'rrup'}
    
    
    def compute(self, ctx, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = np.exp((np.log(_get_source_term(C, ctx) +_get_path_term(C, ctx))) +_get_site_term(C, ctx))
            sig[m], tau[m],phi[m] = _get_stddevs(C)
            


    COEFFS = CoeffsTable(sa_damping=5, table="""
    imt       m1     m2    m3_RS  M1    M2    r1      r2       R1           s1      s2        s3      sig    tau    phi_s2s  phi_ss
    rsd595  0.2384  4.16  8.4117  5.5    8.0  0.08862  0.04194   200.0  -0.2875 0.001234  -0.03137  0.403  0.191   0.233    0.275
    rsd575  0.4733  6.16  0.515   5.0    8.0  0.07505  0.0156    200.0  -0.1464 0.00075     0.357   0.490  0.218   0.238    0.369
    """)

