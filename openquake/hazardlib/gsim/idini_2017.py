# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
Module exports :class:`IdiniEtAl2017SInter`
               :class:`IdiniEtAl2017SSlab`
"""
import numpy as np

from openquake.baselib.general import CallableDict
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.imt import PGA, SA

CONSTS = {'Mr': 5,
          'Vref': 1530,
          'c4': 0.1,
          'c6': 5,
          'c7': 0.35,
          'h0': 50}

_get_distance_term = CallableDict()


@_get_distance_term.add(const.TRT.SUBDUCTION_INTERFACE)
def _get_distance_term_1(trt, C, ctx):
    """
    Returns the magnitude dependent distance scaling term defined in
    Equation (5)
    """
    mag = ctx.mag
    R = np.where(mag < 7.7, ctx.rhypo, ctx.rrup)
    g = C['c3'] + CONSTS['c4'] * (mag - CONSTS['Mr'])
    Ro = CONSTS['c6'] * 10 ** (CONSTS['c7'] * (mag - CONSTS['Mr']))
    return g * np.log10(R + Ro) + C['c5'] * R


@_get_distance_term.add(const.TRT.SUBDUCTION_INTRASLAB)
def _get_distance_term_2(trt, C, ctx):
    """
    Returns the magnitude dependent distance scaling term defined in
    Equation (5)
    """
    mag = ctx.mag
    R = ctx.rhypo
    g = C['c3'] + CONSTS['c4'] * (mag - CONSTS['Mr']) + C['dc3']
    return g * np.log10(R) + C['c5'] * R


_get_magnitude_term = CallableDict()


@_get_magnitude_term.add(const.TRT.SUBDUCTION_INTERFACE)
def _get_magnitude_term_1(trt, C, ctx):
    """
    Returns the magnitude scaling term defined in Equation (3)
    """
    return C['c1'] + C['c2'] * ctx.mag + C['c9'] * ctx.mag ** 2.0


@_get_magnitude_term.add(const.TRT.SUBDUCTION_INTRASLAB)
def _get_magnitude_term_2(trt, C, ctx):
    """
    Returns the magnitude scaling term defined in Equation (3)
    """
    mag = ctx.mag
    H = ctx.hypo_depth
    return C['c1'] + C['c2'] * mag + C['c8'] * (H - CONSTS['h0']) + \
        C['dc1'] + C['dc2'] * mag


def _get_site_term(C, ctx):
    """
    Returns the site scaling term defined in Equation (18)
    """
    soiltype = ctx.soiltype
    vs30 = ctx.vs30

    # sT* depends on the soil type.
    # If soiltype > 6, use soiltype = 1 (rock)
    sT = [C['s%i' % st] if st > 1 and st <= 6 else 0 for st in soiltype]

    return sT * np.log10(vs30 / CONSTS['Vref'])


def _get_stddevs(C):
    """
    Returns the standard deviations
    """
    # sigma_e and sigma_r are in log10 base, so we need to transform them
    tau = np.log(10 ** C['sigma_e'])
    phi = np.log(10 ** C['sigma_r'])
    return [np.sqrt(tau ** 2.0 + phi ** 2.0), tau, phi]


class IdiniEtAl2017SInter(GMPE):
    """
    Implements the GMPE developed by Idini et al. (2017) for subduction
    interface earthquakes, publised as:

    Idini, B., F. Rojas, S. Ruiz, and C. Pastén. 2017. “Ground motion
    prediction equations for the Chilean subduction zone.” Bull. Earthq. Eng.
    15(5): 1853–1880.
    """

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Site amplification is dependent on the Site Class and Vs30
    REQUIRES_SITES_PARAMETERS = {'soiltype', 'vs30'}

    #: Required rupture parameters are only magnitude for the interface model
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is closest distance to rupture, for
    #: interface events M>=7.7, and hypocentral distance for interface events
    #: M<7.7
    REQUIRES_DISTANCES = {'rrup', 'rhypo'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            mean[m] = (_get_magnitude_term(trt, C, ctx) +
                       _get_distance_term(trt, C, ctx) +
                       _get_site_term(C, ctx))
            # Convert from log10 to ln
            mean[m] = np.log(10 ** mean[m])
            sig[m], tau[m], phi[m] = _get_stddevs(C)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt	          c1	     c2	       c9	      c8	    dc1	      dc2	sigma_e	sigma_t	       c3	       c5	      dc3	sigma_r	     s2	     s3	     s4	     s5	     s6                         
    pga	    -2.85480	0.77410	 -0.039580	0.005860	2.56990	 -0.47610	0.1720	0.2890	-0.975580	-0.001740	-0.527450	0.2320	-0.5840	-0.3220	-0.1090	-0.0950	-0.2120
    0.01	-2.84240	0.80520	 -0.041350	0.005840	2.73700	 -0.51910	0.1730	0.2880	-1.029930	-0.001750	-0.504660	0.2310	-0.5230	-0.2620	-0.1000	-0.0920	-0.1930
    0.02	-2.83370	0.83830	 -0.043250	0.005830	2.90870	 -0.56400	0.1760	0.2920	-1.085670	-0.001760	-0.480430	0.2330	-0.4590	-0.2080	-0.0920	-0.0890	-0.1770
    0.03	-2.82350	0.88380	 -0.045950	0.005860	3.07350	 -0.62270	0.1780	0.2950	-1.159510	-0.001760	-0.424900	0.2350	-0.3900	-0.1600	-0.0850	-0.0880	-0.1640
    0.05	-2.73580	0.95390	 -0.050330	0.006210	3.21470	 -0.70790	0.1900	0.3070	-1.286400	-0.001780	-0.312390	0.2410	-0.3060	-0.0880	-0.0750	-0.0900	-0.1460
    0.07	-2.60040	0.98080	 -0.052250	0.006030	3.08510	 -0.74250	0.2130	0.3290	-1.346440	-0.001810	-0.179950	0.2510	-0.3510	-0.0560	-0.0690	-0.0960	-0.1410
    0.10	-2.48910	0.95440	 -0.050600	0.005710	2.80910	 -0.70550	0.1950	0.3210	-1.323530	-0.001820	-0.132080	0.2550	-0.5240	-0.0870	-0.0700	-0.1130	-0.1560
    0.15	-2.65050	0.92320	 -0.048790	0.005600	2.62600	 -0.62700	0.1600	0.3020	-1.176870	-0.001830	-0.264510	0.2550	-0.6910	-0.3360	-0.0950	-0.1660	-0.2450
    0.20	-3.00960	0.94260	 -0.050340	0.005730	2.60630	 -0.59760	0.1570	0.3100	-1.045080	-0.001820	-0.391050	0.2680	-0.6710	-0.5470	-0.1270	-0.2090	-0.3590
    0.25	-3.33210	0.95780	 -0.051430	0.005070	2.36540	 -0.58200	0.1420	0.2990	-0.943630	-0.001780	-0.343480	0.2640	-0.5840	-0.6740	-0.1780	-0.2350	-0.4440
    0.30	-3.54220	0.94410	 -0.050520	0.004280	2.20170	 -0.54120	0.1410	0.2960	-0.848140	-0.001730	-0.366950	0.2600	-0.5060	-0.7300	-0.2580	-0.2340	-0.4910
    0.40	-3.39850	0.77730	 -0.038850	0.003080	1.63670	 -0.34480	0.1570	0.3060	-0.692780	-0.001660	-0.463010	0.2630	-0.3860	-0.7180	-0.4230	-0.1640	-0.5350
    0.50	-2.80410	0.50690	 -0.019730	0.002570	0.76210	 -0.06170	0.1520	0.3020	-0.578990	-0.001610	-0.540980	0.2610	-0.3000	-0.6350	-0.5370	-0.1100	-0.5570
    0.75	-4.45880	0.86910	 -0.041790	0.001350	2.10030	 -0.43490	0.1460	0.2910	-0.568870	-0.001580	-0.462660	0.2520	-0.2760	-0.3950	-0.5750	-0.3580	-0.5990
    1.00	-5.33910	1.01670	 -0.049990	0.000450	2.56100	 -0.56780	0.1530	0.2900	-0.532820	-0.001540	-0.423140	0.2470	-0.2750	-0.2540	-0.4620	-0.6700	-0.5840
    1.50	-6.12040	1.10050	 -0.054260	0.000680	2.89230	 -0.58980	0.1520	0.2890	-0.462630	-0.001450	-0.585190	0.2460	-0.2490	-0.2380	-0.3000	-0.8010	-0.5220
    2.00	-7.03340	1.25010	 -0.063560	0.000510	3.39410	 -0.70090	0.1570	0.2910	-0.405940	-0.001390	-0.659990	0.2450	-0.2180	-0.2310	-0.2200	-0.7460	-0.4790
    3.00	-8.25070	1.46520	 -0.077970	0.000660	4.00330	 -0.84650	0.1550	0.2790	-0.339570	-0.001370	-0.790040	0.2310	-0.1800	-0.2190	-0.2100	-0.6280	-0.4610
    4.00	-8.74330	1.48270	 -0.078630	0.000630	3.93370	 -0.81340	0.1600	0.2790	-0.264790	-0.001370	-0.865450	0.2280	-0.1710	-0.2180	-0.2120	-0.5310	-0.4480
    5.00	-8.99270	1.46300	 -0.076380	0.000670	3.75760	 -0.76420	0.1670	0.2860	-0.223330	-0.001370	-0.887350	0.2320	-0.1680	-0.2180	-0.2030	-0.4380	-0.4390
    7.50	-9.82450	1.63830	 -0.086200	0.001080	4.39480	 -0.93130	0.1640	0.2830	-0.303460	-0.001310	-0.912590	0.2310	-0.1680	-0.2180	-0.1530	-0.2560	-0.4350
    10.00	-9.86710	1.58770	 -0.081680	0.000140	4.38750	 -0.88920	0.1760	0.2700	-0.337710	-0.001170	-0.963630	0.2040	-0.1680	-0.2180	-0.1250	-0.2310	-0.4350    
    """)


class IdiniEtAl2017SSlab(IdiniEtAl2017SInter):
    """
    Implements the GMPE developed by Idini et al. (2017) for subduction
    inslab (intraslab) earthquakes, publised as:

    Idini, B., F. Rojas, S. Ruiz, and C. Pastén. 2017. “Ground motion
    prediction equations for the Chilean subduction zone.” Bull. Earthq. Eng.
    15(5): 1853–1880.
    """
    #: Supported tectonic region type is subduction in-slab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Required rupture parameters for the in-slab model are magnitude and top
    # of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}
