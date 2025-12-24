# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module exports :class:`Scala2025CampiFlegrei_repi_Md`
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def _compute_distance(rval2, C, ctx, h):   
    """
    Compute the distance function
    """
    
    rval = np.sqrt(rval2 ** 2 + h ** 2)
    return (C['c1'] + C['c2']*ctx.mag) * np.log10(rval)


def _compute_magnitude(ctx, C):
    """
    Compute the magnitude function, equation (9):
    """
    return C['a'] + C['b'] * ctx.mag


def _get_site_amplification(ctx, C):
    """
    Compute the site amplification function given by FS = eiSi, for
    i = 1,2 where Si are the coefficients determined through regression
    analysis, and ei are dummy variables (0 or 1) used to denote the
    different EC8 site classes. Due to the regression dataset only sites 
    B and C are considered. Hence in the current version site class A (rock)
    is considered as equivalent to site class B, and site class D (soft soil)
    is considered as equivalent to site class C."""
    ssb, ssc = _get_site_type_dummy_variables(ctx)

    return (C['sB'] * ssb) + (C['sC'] * ssc)


def _get_site_type_dummy_variables(ctx):
    """
    Get site type dummy variables, which classified the ctx into
    different site classes based on the shear wave velocity in the
    upper 30 m (Vs30) according to the EC8 (CEN 2003):
    class A: Vs30 > 800 m/s
    class B: Vs30 = 360 - 800 m/s
    class C: Vs30 = 180 - 360 m/s
    class D: Vs30 < 180 m/s
    """
    ssb = np.zeros(len(ctx.vs30))
    ssc = np.zeros(len(ctx.vs30))
    # Class C; Vs30 < 360 m/s.
    idx = (ctx.vs30 < 360.0)
    ssc[idx] = 1.0
    # Class B; 360 m/s <= Vs30 <= 800 m/s.
    idx = (ctx.vs30 >= 360.0) & (ctx.vs30 < 800.0)
    ssb[idx] = 1.0

    return ssb, ssc


class Scala2025CampiFlegrei_repi_Md(GMPE):
    """
    Implements GMPE developed by Antonio Scala and co-authors (2025) and
    submitted as "Ground Motion Models for Campi Flegrei (Italy)"
    Bulletin of Earthquake Engineering. DOI: https://doi.org/10.1007/s10518-025-02315-6

    GMPE derives from earthquakes in the volcanic area of Campi Flegrei in Italy 
    in the magnitude range 2.5<Md<4.4 and using the duration magnitude as covariate 
    for epicentral distances <40 km, and for stiff soil (EC8-B) and soft soil (EC8-C).

    Test tables are generated from a spreadsheet provided by the authors, and
    modified according to OQ format (e.g. conversion from cm/s2 to m/s2).
    """
    

    #: Supported tectonic region type is 'volcanic'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure types are PGA and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the maximum of two horizontal
    #: components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is magnitude.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Repi.
    REQUIRES_DISTANCES = {'repi'}
    H=1.4
    DIST_TYPE = 'repi'  # check kind
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        
        
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            rval_distance = getattr(ctx, self.DIST_TYPE)
            imean = (_compute_magnitude(ctx, C) +
                     _compute_distance(rval_distance, C, ctx, self.H) +
                     _get_site_amplification(ctx, C))
            intra = np.sqrt(C['phi']**2 + C['sigma0']**2)
            istddevs = [C['sigma'], C['tau'], intra]

            # Convert units to g, but only for PGA and SA (not PGV)
            if imt.string.startswith(("SA", "PGA")):
                mean[m] = np.log((10.0 ** (imean - 2.0)) / g)
            else:  # PGV:
                mean[m] = np.log(10.0 ** imean)
            # Return stddevs in terms of natural log scaling
            sig[m], tau[m], phi[m] = np.log(10.0 ** np.array(istddevs))
            # mean_LogNaturale = np.log((10 ** mean) * 1e-2 / g)

    # Sigma values in log10
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT		a		b		c1		 c2		 sB		sC		tau	 	phi     sigma0	sigma
    pga     0.2109	0.6156	-3.3924	 0.2565	 0.     0.1412	0.2595	0.2267	0.2530	0.4275				
    pgv    -2.0430	0.7552	-2.8356	 0.2019	 0.     0.0819	0.2443	0.2161	0.2053	0.3854				
    0.020   0.4061	0.5929	-3.5384	 0.2818	 0.     0.1299	0.2770	0.2303	0.2883	0.4614							
    0.030   0.5721	0.5869	-3.6702	 0.2884	 0.     0.1773	0.2947	0.2444	0.3022	0.4878					
    0.050   0.6933	0.5812	-3.7826	 0.3178	 0.     0.2003	0.2919  0.2344	0.2994	0.4794			
    0.075   0.5753	0.5855	-3.6236	 0.3215	 0.     0.2181	0.2731	0.2302	0.2770	0.4520			
    0.100   0.3010  0.6303	-3.1736	 0.2333	 0.     0.2182	0.2505	0.2432	0.2487	0.4287							
    0.150   -0.2887 0.7368  -2.4511	 0.0936	 0.     0.2276	0.2268	0.2313	0.2183	0.3906							
    0.200   -0.5327 0.7521  -2.3063	 0.1039	 0.     0.2071	0.2216	0.2369	0.2033	0.3828							
    0.250   -0.8199 0.8103  -2.1561  0.0793  0.     0.1666	0.2349	0.2412  0.1939	0.3885			
    0.300   -1.0524 0.8428  -2.0540  0.0725  0.     0.1482	0.2364	0.2529  0.1847	0.3924								
    0.400   -1.3113 0.8550  -2.0443  0.1013  0.     0.1178  0.2484  0.2577  0.1723  0.3972					
    0.500   -1.6931 0.8860  -1.9081  0.1076  0.     0.1511	0.2574	0.2590	0.1641	0.4003
	0.750   -2.1378 0.9068  -2.0097  0.1630  0.     0.1503  0.2701  0.2275  0.1642  0.3894								
    1.000   -2.4076 0.9101  -2.2138  0.2277  0.     0.1463  0.2859  0.2242  0.1727  0.4023			
    1.500   -2.7775 0.9039  -2.5407  0.3066  0.     0.1876  0.3006  0.2074  0.1798  0.4071					
    2.000   -3.0828 0.9123  -2.6147  0.3269  0.     0.2131  0.3013  0.2012  0.1859  0.4073				
    3.000   -3.1462 0.8632  -2.8777  0.3618  0.     0.1775  0.2915  0.1746  0.1941  0.3913							
    4.000   -3.1714 0.8267  -2.9881  0.3664  0.     0.1627  0.2833  0.1719  0.1999  0.3870						
    5.000   -3.1195 0.7798  -3.1680  0.4042  0.     0.1413  0.2777  0.1735  0.2040  0.3858						
    """)

