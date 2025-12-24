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
Module exports :class:`Scala2025CampiFlegrei_repi`,
               :class:`Scala2025CampiFlegrei_rhypo`
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


class Scala2025CampiFlegrei_repi(GMPE):
    """
    Implements GMPE developed by Antonio Scala and co-authors (2025) and
    submitted as "Ground Motion Models for Campi Flegrei (Italy)"
    Bulletin of Earthquake Engineering.

    GMPE derives from earthquakes in the volcanic area of Campi Flegrei in Italy 
    in the magnitude range 1.5<Mw<4.0 (corresponding to a range 2.5<Md<4.4) 
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
    pga     0.4094	0.6191	-3.6229	 0.3639	 0.     0.1493	0.1746	0.2260	0.2496	0.3793			
    pgv    -1.6914	0.7191	-3.0713	 0.3046	 0.     0.0888	0.1749	0.2150	0.2023	0.3431				
    0.020   0.6010	0.5958	-3.8461	 0.4186	 0.     0.1392	0.1859	0.2304	0.2835	0.4099				
    0.030   0.7359	0.5996	-3.9841	 0.4293	 0.     0.1883	0.2007	0.2436	0.2972	0.4336			
    0.050   0.8067	0.6108	-3.9975	 0.4276	 0.     0.2107	0.1968	0.2346	0.2959	0.4258				
    0.075   0.6920	0.6134	-3.7435	 0.3984	 0.     0.2275	0.1926	0.2313	0.2753	0.4079				
    0.100   0.5311	0.6229	-3.3363	 0.3146	 0.     0.2256	0.1908	0.2447	0.2466	0.3964				
    0.150   0.1077	0.6844	-2.7511	 0.2056	 0.     0.2316	0.1732	0.2328	0.2158	0.3616				
    0.200   -0.1031	0.6885	-2.6100	 0.2187	 0.     0.2120	0.1716	0.2370	0.2006	0.3548				
    0.250   -0.3742	0.7479	-2.4484	 0.1875	 0.     0.1707	0.1819	0.2409	0.1918	0.3576				
    0.300   -0.5983	0.7810	-2.3072	 0.1662	 0.     0.1514	0.1870	0.2529	0.1830	0.3639				
    0.400   -0.9019	0.8098	-2.2243	 0.1734	 0.     0.1213	0.1940	0.2573	0.1709	0.3648			
    0.500   -1.2458	0.8286	-2.0745	 0.1769	 0.     0.1561	0.2139	0.2585	0.1627	0.3729			
    0.750   -1.6757	0.8439	-2.1797	 0.2413	 0.     0.1589	0.2251	0.2283	0.1621	0.3592				
    1.000   -1.9719	0.8556	-2.3701	 0.3094	 0.     0.1575	0.2329	0.2254	0.1702	0.3660			
    1.500   -2.3896	0.8644	-2.6398	 0.3780	 0.     0.2010	0.2425	0.2092	0.1781	0.3664			
    2.000   -2.6768	0.8664	-2.7034	 0.3972	 0.     0.2272	0.2509	0.2030	0.1844	0.3717				
    3.000   -2.7556	0.8177	-3.0000	 0.4472	 0.     0.1923	0.2360	0.1757	0.1917	0.3512				
    4.000   -2.7906	0.7817	-3.1544	 0.4670	 0.     0.1771	0.2207	0.1724	0.1965	0.3421			
    5.000   -2.7500	0.7332	-3.3747	 0.5232	 0.     0.1573	0.2095	0.1735	0.1991	0.3371			
    """)

class Scala2025CampiFlegrei_rhypo(Scala2025CampiFlegrei_repi):
    """
    Implements GMPE developed by Antonio Scala and co-authors (2025) and
    submitted as "Ground Motion Models for Campi Flegrei (Italy)"
    Bulletin of Earthquake Engineering.

    GMPE derives from earthquakes in the volcanic area of Campi Flegrei in Italy 
    in the magnitude range 1.5<Mw<4.0 (corresponding to a range 2.5<Md<4.4) 
    for epicentral distances <40 km (but considering Hypocentral distance as a covariate), 
    and for stiff soil (EC8-B) and soft soil (EC8-C).

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
    REQUIRES_DISTANCES = {'rhypo'}
    
    H=1.0 
    DIST_TYPE = 'rhypo'
    
    # Sigma values in log10
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT		a		b		c1		 c2		 sB		sC		tau	 	phi     sigma0	sigma
	pga     0.3439	0.9372	-3.7449	0.1718	 0.     0.0511	0.1968	0.2787	0.2577	0.4276			
    pgv     -1.7282	0.9950	-3.1904	0.1368	 0.     -0.0058	0.1468	0.2484	0.2107	0.3573			
    0.020   0.5330	0.9108	-3.9743	0.2321	 0.     0.0498	0.2143	0.2846	0.2915	0.4603			
    0.030   0.6720	0.9307	-4.1345	0.2363	 0.     0.0893	0.2414	0.2974	0.3031	0.4884		
    0.050   0.7207	0.9386	-4.1303	0.2377	 0.     0.1244	0.2373	0.2707	0.3013	0.4694
    0.075   0.6235	0.9193	-3.8811	0.2224	 0.     0.1447	0.2192	0.2515	0.2796	0.4353
    0.100   0.4839	0.9231	-3.4819	0.1392	 0.     0.1288	0.2025	0.2637	0.2500	0.4160			
    0.150   0.0722	0.9656	-2.8804	0.0359	 0.     0.1290	0.1604	0.2535	0.2176	0.3706
    0.200   -0.1001	0.9469	-2.7656	0.0653	 0.     0.1051	0.1405	0.2572	0.2025	0.3563
    0.250   -0.3376	1.0018	-2.6452	0.0420	 0.     0.0519	0.1416	0.2584	0.1917	0.3515
    0.300   -0.5348	1.0284	-2.5341	0.0283	 0.     0.0243	0.1390	0.2622	0.1819	0.3481
    0.400   -0.8112	1.0424	-2.4822	0.0501	 0.     -0.0086	0.1312	0.2571	0.1706	0.3353
    0.500   -1.1361	1.0357	-2.3516	0.0753	 0.     0.0330	0.1457	0.2410	0.1632	0.3255
    0.750   -1.5799	1.0264	-2.4344	0.1562	 0.     0.0586	0.1596	0.2033	0.1652	0.3068
    1.000   -1.8728	1.0248	-2.6233	0.2340	 0.     0.0692	0.1749	0.1995	0.1748	0.3177
    1.500   -2.3300	1.0284	-2.8500	0.3045	 0.     0.1357	0.1881	0.1785	0.1893	0.3211
    2.000   -2.6197	1.0301	-2.9099	0.3235	 0.     0.1640	0.1985	0.1725	0.1962	0.3281
    3.000   -2.7296	0.9921	-3.1817	0.3656	 0.     0.1408	0.1867	0.1656	0.2035	0.3220
    4.000   -2.7761	0.9643	-3.3290	0.3798	 0.     0.1289	0.1748	0.1761	0.2087	0.3242
    5.000   -2.7188	0.9130	-3.5715	0.4415	 0.     0.1105	0.1682	0.1843	0.2119	0.3273
    """)

