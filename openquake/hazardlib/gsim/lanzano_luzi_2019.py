# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
Module exports :class:`LanzanoLuzi2019shallow`,
               :class:`LanzanoLuzi2019deep`
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class LanzanoLuzi2019shallow(GMPE):
    """
    Implements GMPE developed by Giovanni Lanzano and Lucia Luzi (2019) and
    submitted as "A ground motion model for volcanic areas in Italy"
    Bulletin of Earthquake Engineering.

    GMPE derives from earthquakes in the volcanic areas in Italy in the
    magnitude range 3<ML<5 for hypocentral distances <200 km, and for rock (EC8-A),
    stiff soil (EC8-B) and soft soil (EC8-C and EC8-D).

    The GMPE distinguishes between shallow volcano-tectonic events related to
    flank movements (focal depths <5km) and deeper events occurring due to
    regional tectonics (focal depths >5km), considering two different attenuations 
    with distances.

    Test tables are generated from a spreadsheet provided by the authors, and
    modified according to OQ format (e.g. conversion from cm/s2 to m/s2).
    """
    #: Supported tectonic region type is 'volcanic'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure types are PGA and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])
    
    #: Required site parameter is Vs30
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Required rupture parameter is magnitude.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: Required distance measure is Rhypo.
    REQUIRES_DISTANCES = set(('rhypo', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type
        C = self.COEFFS[imt]

        imean = (self._compute_magnitude(rup, C) +
                 self._compute_distance(dists.rhypo, C) +
                 self._get_site_amplification(sites, C))

        istddevs = self._get_stddevs(C,
                                     stddev_types,
                                     num_sites=sites.vs30.size)

		# Convert units to g,
        # but only for PGA and SA (not PGV):
        if imt.name in "SA PGA":
            mean = np.log((10.0 ** (imean - 2.0)) / g)
        else:
            # PGV:
            mean = np.log(10.0 ** imean)
        # Return stddevs in terms of natural log scaling
        stddevs = np.log(10.0 ** np.array(istddevs))
        # mean_LogNaturale = np.log((10 ** mean) * 1e-2 / g)
        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations components.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(C['sigma'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C['phi'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(num_sites))
        return stddevs

    def _compute_distance(self, rval2, C):
        """
        Compute the distance function, equation (9):
        """
        h1 = 2
        rval = np.sqrt(rval2 ** 2 + (h1) ** 2)
        return C['c1'] * np.log10(rval)

    def _compute_magnitude(self, rup, C):
        """
        Compute the magnitude function, equation (9):
        """
        return C['a'] + (C['b'] * (rup.mag))

    def _get_site_amplification(self, sites, C):
        """
        Compute the site amplification function given by FS = eiSi, for
        i = 1,2,3 where Si are the coefficients determined through regression
        analysis, and ei are dummy variables (0 or 1) used to denote the
        different EC8 site classes.
        """
        ssb, ssc = self._get_site_type_dummy_variables(sites)

        return (C['sB'] * ssb) + (C['sC'] * ssc)

    def _get_site_type_dummy_variables(self, sites):
        """
        Get site type dummy variables, which classified the sites into
        different site classes based on the shear wave velocity in the
        upper 30 m (Vs30) according to the EC8 (CEN 2003):
        class A: Vs30 > 800 m/s
        class B: Vs30 = 360 - 800 m/s
        class C: Vs30 = 180 - 360 m/s
        class D: Vs30 < 180 m/s
        """
        ssb = np.zeros(len(sites.vs30))
        ssc = np.zeros(len(sites.vs30))
        # Class C; Vs30 < 360 m/s.
        idx = (sites.vs30 < 360.0)
        ssc[idx] = 1.0
        # Class B; 360 m/s <= Vs30 <= 800 m/s.
        idx = (sites.vs30 >= 360.0) & (sites.vs30 < 800.0)
        ssb[idx] = 1.0

        return ssb, ssc
        
          # Sigma values in log10
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT		a		b		c1		c2		c3		sB		sC		tau	 	phiS2S	sigma0	phi		sigma
	pga		-0.4185	0.8146	-2.0926	-1.5694	-0.0062	0.088	0.3382	0.1892	0.2624	0.2215	0.3434	0.3921
	pgv		-2.5366	0.9809	-1.8482	-1.5676	-0.0042	0.0995	0.3747	0.1433	0.2126	0.2099	0.2988	0.3313	
	0.025	-0.3849	0.8113	-2.0995	-1.5689	-0.0063	0.0866	0.3373	0.1887	0.2644	0.2228	0.3458	0.3939
	0.040	-0.2622	0.7983	-2.1271	-1.5777	-0.0065	0.0861	0.3306	0.1908	0.2725	0.2246	0.3531	0.4014
	0.050	-0.1428	0.7870	-2.1536	-1.5859	-0.0069	0.0863	0.3323	0.1955	0.2846	0.2284	0.3649	0.4140
	0.070	 0.0810	0.7714	-2.2186	-1.5859	-0.0076	0.0774	0.3139	0.2039	0.3078	0.2392	0.3898	0.4399
	0.100	 0.4160	0.7293	-2.2624	-1.6135	-0.0075	0.0609	0.2997	0.2164	0.3240	0.2312	0.3980	0.4531
	0.150	 0.2806	0.7569	-2.2177	-1.5882	-0.0069	0.0714	0.3465	0.2193	0.3204	0.2155	0.3861	0.4441
	0.200	 0.0339	0.8028	-2.1606	-1.5803	-0.0060	0.0716	0.3297	0.2200	0.3039	0.2126	0.3709	0.4312
	0.250	-0.2205	0.8577	-2.1228	-1.5948	-0.0052	0.0512	0.3204	0.1995	0.2837	0.2101	0.3530	0.4055
	0.300	-0.4404	0.8872	-2.0652	-1.5829	-0.0047	0.0752	0.3468	0.1932	0.2726	0.2053	0.3413	0.3922
	0.350	-0.6916	0.9169	-2.0099	-1.5577	-0.0042	0.0838	0.3818	0.1838	0.2607	0.2043	0.3312	0.3788
	0.400	-1.0431	0.9744	-1.9542	-1.5409	-0.0038	0.0820	0.3672	0.1850	0.2576	0.2034	0.3282	0.3768
	0.450	-1.2374	1.0111	-1.9411	-1.5544	-0.0038	0.0878	0.3882	0.1794	0.2467	0.2053	0.3210	0.3677
	0.500	-1.3532	1.0303	-1.9337	-1.5871	-0.0034	0.1033	0.4053	0.1736	0.2461	0.2039	0.3196	0.3637
	0.600	-1.6118	1.0629	-1.8831	-1.6015	-0.0029	0.1161	0.4056	0.1681	0.2336	0.2006	0.3079	0.3508
	0.700	-1.9639	1.1092	-1.8177	-1.5795	-0.0027	0.1086	0.4195	0.1550	0.2300	0.1974	0.3031	0.3404
	0.750	-2.0659	1.1181	-1.7968	-1.5618	-0.0029	0.1159	0.4277	0.1581	0.2314	0.195	0.3026	0.3414
	0.800	-2.1093	1.1189	-1.7961	-1.5741	-0.0027	0.1174	0.4371	0.1541	0.2289	0.1944	0.3003	0.3375
	0.900	-2.2763	1.1315	-1.7722	-1.5776	-0.0023	0.1212	0.4374	0.1552	0.2287	0.1885	0.2964	0.3345
	1.000	-2.5171	1.1553	-1.7230	-1.5615	-0.0018	0.1201	0.448	0.1496	0.2279	0.1904	0.2970	0.3325
	1.200	-2.698	1.1748	-1.7111	-1.6079	-0.0013	0.1195	0.4313	0.1595	0.2286	0.1865	0.2950	0.3354
	1.400	-2.9144	1.1842	-1.6536	-1.5777	-0.0015	0.1155	0.4136	0.1846	0.2217	0.1855	0.2891	0.3430
	1.600	-3.0714	1.2011	-1.6641	-1.6102	-0.0013	0.1269	0.377	0.1953	0.2226	0.1823	0.2877	0.3477
	1.800	-3.1426	1.1967	-1.6553	-1.6305	-0.0012	0.1337	0.3756	0.1888	0.2221	0.1793	0.2854	0.3422
	2.000	-3.2273	1.1995	-1.6524	-1.6597	-0.0009	0.1440	0.3917	0.1929	0.2187	0.1824	0.2848	0.3440
	2.500	-3.4744	1.2057	-1.6227	-1.642	-0.0011	0.1388	0.3712	0.2060	0.2111	0.185	0.2807	0.3482
	3.000	-3.7121	1.2118	-1.5741	-1.6063	-0.0012	0.1261	0.3836	0.2356	0.2139	0.1825	0.2812	0.3668
	3.500	-3.4558	1.1198	-1.5393	-1.6194	-0.0011	0.1101	0.3639	0.2506	0.2098	0.1816	0.2775	0.3739
	4.000	-3.5044	1.0943	-1.4949	-1.6025	-0.0012	0.1064	0.3447	0.2442	0.2093	0.1832	0.2782	0.3701
	4.500	-3.3949	1.0490	-1.475	-1.6088	-0.0011	0.0908	0.3587	0.2287	0.1952	0.1835	0.2679	0.3522
	5.000	-3.4022	1.0258	-1.4711	-1.6097	-0.0011	0.0856	0.3386	0.2273	0.1954	0.1835	0.2681	0.3515
    """)
        
class LanzanoLuzi2019deep(GMPE):
 
     #: Supported tectonic region type is 'volcanic'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure types are PGA and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])
    
    #: Required site parameter is Vs30
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Required rupture parameter is magnitude.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: Required distance measure is Rhypo.
    REQUIRES_DISTANCES = set(('rhypo', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type
        C = self.COEFFS[imt]

        imean = (self._compute_magnitude(rup, C) +
                 self._compute_distance(dists.rhypo, C) +
                 self._get_site_amplification(sites, C))

        istddevs = self._get_stddevs(C,
                                     stddev_types,
                                     num_sites=sites.vs30.size)

		# Convert units to g,
        # but only for PGA and SA (not PGV):
        if imt.name in "SA PGA":
            mean = np.log((10.0 ** (imean - 2.0)) / g)
        else:
            # PGV:
            mean = np.log(10.0 ** imean)
        # Return stddevs in terms of natural log scaling
        stddevs = np.log(10.0 ** np.array(istddevs))
        # mean_LogNaturale = np.log((10 ** mean) * 1e-2 / g)
        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations components.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(C['sigma'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C['phi'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(num_sites))
        return stddevs
        
    def _compute_distance(self, rval2, C):
        """
        Compute the distance function, equation (5).
        """
        h2 = 5
        rval = np.sqrt(rval2 ** 2 + (h2) ** 2)
        return C['c2'] * np.log10(rval) + C['c3'] * rval

    def _compute_magnitude(self, rup, C):
        """
        Compute the magnitude function, equation (9):
        """
        return C['a'] + (C['b'] * (rup.mag))

    def _get_site_amplification(self, sites, C):
        """
        Compute the site amplification function given by FS = eiSi, for
        i = 1,2,3 where Si are the coefficients determined through regression
        analysis, and ei are dummy variables (0 or 1) used to denote the
        different EC8 site classes.
        """
        ssb, ssc = self._get_site_type_dummy_variables(sites)

        return (C['sB'] * ssb) + (C['sC'] * ssc)

    def _get_site_type_dummy_variables(self, sites):
        """
        Get site type dummy variables, which classified the sites into
        different site classes based on the shear wave velocity in the
        upper 30 m (Vs30) according to the EC8 (CEN 2003):
        class A: Vs30 > 800 m/s
        class B: Vs30 = 360 - 800 m/s
        class C: Vs30 = 180 - 360 m/s
        class D: Vs30 < 180 m/s
        """
        ssb = np.zeros(len(sites.vs30))
        ssc = np.zeros(len(sites.vs30))
        # Class C; Vs30 < 360 m/s.
        idx = (sites.vs30 < 360.0)
        ssc[idx] = 1.0
        # Class B; 360 m/s <= Vs30 <= 800 m/s.
        idx = (sites.vs30 >= 360.0) & (sites.vs30 < 800.0)
        ssb[idx] = 1.0

        return ssb, ssc
        
          # Sigma values in log10
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT		a		b		c1		c2		c3		sB		sC		tau	 	phiS2S	sigma0	phi		sigma
	pga		-0.4185	0.8146	-2.0926	-1.5694	-0.0062	0.088	0.3382	0.1892	0.2624	0.2215	0.3434	0.3921
	pgv		-2.5366	0.9809	-1.8482	-1.5676	-0.0042	0.0995	0.3747	0.1433	0.2126	0.2099	0.2988	0.3313	
	0.025	-0.3849	0.8113	-2.0995	-1.5689	-0.0063	0.0866	0.3373	0.1887	0.2644	0.2228	0.3458	0.3939
	0.040	-0.2622	0.7983	-2.1271	-1.5777	-0.0065	0.0861	0.3306	0.1908	0.2725	0.2246	0.3531	0.4014
	0.050	-0.1428	0.7870	-2.1536	-1.5859	-0.0069	0.0863	0.3323	0.1955	0.2846	0.2284	0.3649	0.4140
	0.070	 0.0810	0.7714	-2.2186	-1.5859	-0.0076	0.0774	0.3139	0.2039	0.3078	0.2392	0.3898	0.4399
	0.100	 0.4160	0.7293	-2.2624	-1.6135	-0.0075	0.0609	0.2997	0.2164	0.3240	0.2312	0.3980	0.4531
	0.150	 0.2806	0.7569	-2.2177	-1.5882	-0.0069	0.0714	0.3465	0.2193	0.3204	0.2155	0.3861	0.4441
	0.200	 0.0339	0.8028	-2.1606	-1.5803	-0.0060	0.0716	0.3297	0.2200	0.3039	0.2126	0.3709	0.4312
	0.250	-0.2205	0.8577	-2.1228	-1.5948	-0.0052	0.0512	0.3204	0.1995	0.2837	0.2101	0.3530	0.4055
	0.300	-0.4404	0.8872	-2.0652	-1.5829	-0.0047	0.0752	0.3468	0.1932	0.2726	0.2053	0.3413	0.3922
	0.350	-0.6916	0.9169	-2.0099	-1.5577	-0.0042	0.0838	0.3818	0.1838	0.2607	0.2043	0.3312	0.3788
	0.400	-1.0431	0.9744	-1.9542	-1.5409	-0.0038	0.0820	0.3672	0.1850	0.2576	0.2034	0.3282	0.3768
	0.450	-1.2374	1.0111	-1.9411	-1.5544	-0.0038	0.0878	0.3882	0.1794	0.2467	0.2053	0.3210	0.3677
	0.500	-1.3532	1.0303	-1.9337	-1.5871	-0.0034	0.1033	0.4053	0.1736	0.2461	0.2039	0.3196	0.3637
	0.600	-1.6118	1.0629	-1.8831	-1.6015	-0.0029	0.1161	0.4056	0.1681	0.2336	0.2006	0.3079	0.3508
	0.700	-1.9639	1.1092	-1.8177	-1.5795	-0.0027	0.1086	0.4195	0.1550	0.2300	0.1974	0.3031	0.3404
	0.750	-2.0659	1.1181	-1.7968	-1.5618	-0.0029	0.1159	0.4277	0.1581	0.2314	0.195	0.3026	0.3414
	0.800	-2.1093	1.1189	-1.7961	-1.5741	-0.0027	0.1174	0.4371	0.1541	0.2289	0.1944	0.3003	0.3375
	0.900	-2.2763	1.1315	-1.7722	-1.5776	-0.0023	0.1212	0.4374	0.1552	0.2287	0.1885	0.2964	0.3345
	1.000	-2.5171	1.1553	-1.7230	-1.5615	-0.0018	0.1201	0.448	0.1496	0.2279	0.1904	0.2970	0.3325
	1.200	-2.698	1.1748	-1.7111	-1.6079	-0.0013	0.1195	0.4313	0.1595	0.2286	0.1865	0.2950	0.3354
	1.400	-2.9144	1.1842	-1.6536	-1.5777	-0.0015	0.1155	0.4136	0.1846	0.2217	0.1855	0.2891	0.3430
	1.600	-3.0714	1.2011	-1.6641	-1.6102	-0.0013	0.1269	0.377	0.1953	0.2226	0.1823	0.2877	0.3477
	1.800	-3.1426	1.1967	-1.6553	-1.6305	-0.0012	0.1337	0.3756	0.1888	0.2221	0.1793	0.2854	0.3422
	2.000	-3.2273	1.1995	-1.6524	-1.6597	-0.0009	0.1440	0.3917	0.1929	0.2187	0.1824	0.2848	0.3440
	2.500	-3.4744	1.2057	-1.6227	-1.642	-0.0011	0.1388	0.3712	0.2060	0.2111	0.185	0.2807	0.3482
	3.000	-3.7121	1.2118	-1.5741	-1.6063	-0.0012	0.1261	0.3836	0.2356	0.2139	0.1825	0.2812	0.3668
	3.500	-3.4558	1.1198	-1.5393	-1.6194	-0.0011	0.1101	0.3639	0.2506	0.2098	0.1816	0.2775	0.3739
	4.000	-3.5044	1.0943	-1.4949	-1.6025	-0.0012	0.1064	0.3447	0.2442	0.2093	0.1832	0.2782	0.3701
	4.500	-3.3949	1.0490	-1.475	-1.6088	-0.0011	0.0908	0.3587	0.2287	0.1952	0.1835	0.2679	0.3522
	5.000	-3.4022	1.0258	-1.4711	-1.6097	-0.0011	0.0856	0.3386	0.2273	0.1954	0.1835	0.2681	0.3515
    """)
