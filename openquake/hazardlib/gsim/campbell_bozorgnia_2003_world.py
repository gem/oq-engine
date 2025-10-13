# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
Module exports :class:`CampbellBozorgnia2003`
                class:`CampbellBozorgnia2003Vertical`.
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.campbell_bozorgnia_2003 import (
    _compute_magnitude_scaling, _compute_faulting_mechanism 
)


def _get_mean(C, mag, rake, dip, rrup, rjb, vs30):
    """
    Return mean value (eq. 1, page 319).
    """
    f1 = _compute_magnitude_scaling(C, mag)
    f2 = _compute_distance_scaling(C, mag, rrup, vs30)
    f3 = _compute_faulting_mechanism(C, rake, dip)
    f4 = _compute_far_source_soil_effect(C, vs30)
    f5 = _compute_hanging_wall_effect(C, rjb, rrup, dip, mag, rake, vs30)
    return C['c1'] + f1 + C['c4'] * np.log(np.sqrt(f2)) + f3 + f4 + f5


def _compute_distance_scaling(C, mag, rrup, vs30):
    """
    Compute distance scaling term (eq.3, page 319).

    """
    svfs , ssr, sfr = _get_site_type_dummy_variables(vs30)
    g = C['c5'] + C['c6'] * (svfs + ssr) + C['c7'] * sfr

    return rrup ** 2 + (np.exp(
        C['c8'] * mag + C['c9'] * (8.5 - mag) ** 2) * g) ** 2

def _get_site_type_dummy_variables(vs30):
        """
        Get site type dummy variables, four site types are considered
        based on the shear wave velocity intervals in the uppermost 30 m, Vs30:
        firm soil: 298 < Vs30 <= 368 m/s
        very firm soil: 368 < Vs30 <= 421 m/s
        soft rock: 421 < Vs30 <= 830 m/s
        firm rock: Vs30 > 830 m/s
        """
        svfs = np.zeros(len(vs30))
        ssr = np.zeros(len(vs30))
        sfr = np.zeros(len(vs30))

        # very firm soil
        idx = (vs30 >= 368) & (vs30 <= 421)
        svfs[idx] = 1.0
        # soft rock
        idx = (vs30 > 421) & (vs30 <= 830)
        ssr[idx] = 1.0
        # firm rock
        idx = (vs30 > 830)
        sfr[idx] = 1.0
        return svfs, ssr ,sfr


def _compute_far_source_soil_effect(C, vs30):
    """
    Compute far-source effect of local site conditions (see eq. 6,
    page 319).
    """
    svfs , ssr, sfr = _get_site_type_dummy_variables(vs30)
    return C['c12']*svfs + C['c13']*ssr + C['c14']*sfr


def _compute_hanging_wall_effect(C, rjb, rrup, dip, mag, rake, vs30):
    """
    Compute hanging-wall effect (see eq. 7, 8, 9 and 10 page 319).
    Considers correct version of equation 8 as given in the erratum and not
    in the original paper.
    """
    # flag for reverse faulting
    frv = (dip > 45) & (22.5 <= rake) & (rake <= 157.5)
    # flag for thrust faulting
    fth = (dip <= 45) & (22.5 <= rake) & (rake <= 157.5)
    
    svfs , ssr, sfr = _get_site_type_dummy_variables(vs30)

    # eq. 8
    hw = np.zeros_like(rjb)

    idx1 = rjb < 5
    svfs = ((svfs*((5 - rjb) / 5))*idx1 + 0.0)*(dip <= 70)
    ssr  = ((ssr*((5 - rjb) / 5))*idx1 + 0.0)*(dip <= 70)
    sfr  = ((sfr*((5 - rjb) / 5))*idx1 + 0.0)*(dip <= 70)
    hw = svfs+ssr+sfr

    # eq. 9
    f_m = np.where(mag>6.5, 1, np.where(mag<5.5, 0, mag-5.5))

    # eq. 10
    f_rrup = C['c15'] + np.zeros_like(rrup)
    idx = rrup < 8
    f_rrup[idx] *= rrup[idx] / 8

    # eq. 7
    f_hw = (hw * f_m * f_rrup * (frv + fth))

    return f_hw


class CampbellBozorgnia2003(GMPE):
    """
    Implements GMPE developed by Kenneth W. Campbell and Yousef Bozorgnia and
    published as "Updated Near-Source Ground-Motion (Attenuation) Relations for
    the Horizontal and Vertical Components of Peak Ground Acceleration and
    Acceleration Response Spectra", Bulletin of the Seismological Society of
    America, Vol. 93, No. 1, pp. 314-331, 2003.
    """
    #: Supported tectonic region type is 'active shallow crust' (see Abstract)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are PGA and SA (see Abstract)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components (see paragraph 'Strong-Motion Database', page 316)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is Total (see equations 11, 12 pp. 319
    #: 320)
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, rake and dip (eq. 1 and
    #: following, page 319).
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'dip'}

    #: Required distance measure are RRup and Rjb (eq. 1 and following,
    #: page 319).
    REQUIRES_DISTANCES = {'rrup', 'rjb'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _get_mean(
                C, ctx.mag, ctx.rake, ctx.dip, ctx.rrup, ctx.rjb, ctx.vs30)
            sig[m] = C['c16'] - np.where(ctx.mag < 7.4, 0.07 * ctx.mag, 0.518)

    #: Coefficient table (table 4, page 321. Coefficients for horizontal
    #: component SA and for corrected PGA)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT	     c1	    c2	     c3	     c4	    c5	     c6	     c7	    c8	     c9	     c10	c11	     c12	 c13	 c14	c15	    c16
    PGA	    -4.033	0.812	 0.036	-1.061	0.041	-0.005	-0.018	0.766	 0.034	 0.343	0.351	-0.123	-0.138	-0.289	0.370	0.920
    0.05	-3.740	0.812	 0.036	-1.121	0.058	-0.004	-0.028	0.724	 0.032	 0.302	0.362	-0.140	-0.158	-0.205	0.370	0.940
    0.08	-3.076	0.812	 0.050	-1.252	0.121	-0.005	-0.051	0.648	 0.040	 0.243	0.333	-0.150	-0.196	-0.208	0.370	0.952
    0.10	-2.661	0.812	 0.060	-1.308	0.166	-0.009	-0.068	0.621	 0.046	 0.224	0.313	-0.146	-0.253	-0.258	0.370	0.958
    0.15	-2.270	0.812	 0.041	-1.324	0.212	-0.033	-0.081	0.613	 0.031	 0.318	0.344	-0.176	-0.267	-0.284	0.370	0.974
    0.20	-2.771	0.812	 0.030	-1.153	0.098	-0.014	-0.038	0.704	 0.026	 0.296	0.342	-0.148	-0.183	-0.359	0.370	0.981
    0.30	-2.999	0.812	 0.007	-1.080	0.059	-0.007	-0.022	0.752	 0.007	 0.359	0.385	-0.162	-0.157	-0.585	0.370	0.984
    0.40	-3.511	0.812	-0.015	-0.964	0.024	-0.002	-0.005	0.842	-0.016	 0.379	0.438	-0.078	-0.129	-0.557	0.370	0.987
    0.50	-3.556	0.812	-0.035	-0.964	0.023	-0.002	-0.004	0.842	-0.036	 0.406	0.479	-0.122	-0.130	-0.701	0.370	0.990
    0.75	-3.709	0.812	-0.071	-0.964	0.021	-0.002	-0.002	0.842	-0.074	 0.347	0.419	-0.108	-0.124	-0.796	0.331	1.021
    1.00	-3.867	0.812	-0.101	-0.964	0.019	 0.000	 0.000	0.842	-0.105	 0.329	0.338	-0.073	-0.072	-0.858	0.281	1.021
    1.50	-4.093	0.812	-0.150	-0.964	0.019	 0.000	 0.000	0.842	-0.155	 0.217	0.188	-0.079	-0.056	-0.954	0.210	1.021
    2.00	-4.311	0.812	-0.180	-0.964	0.019	 0.000	 0.000	0.842	-0.187	 0.060	0.064	-0.124	-0.116	-0.916	0.160	1.021
    3.00	-4.817	0.812	-0.193	-0.964	0.019	 0.000	 0.000	0.842	-0.200	-0.079	0.021	-0.154	-0.117	-0.873	0.089	1.021
    4.00	-5.211	0.812	-0.202	-0.964	0.019	 0.000	 0.000	0.842	-0.209	-0.061	0.057	-0.054	-0.261	-0.889	0.039	1.021
    """)


class CampbellBozorgnia2003Vertical(CampbellBozorgnia2003):
    #: Supported intensity measure component is vertical
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VERTICAL

    #: Coefficient table (table 4, page 321. Coefficients for vertical
    #: component SA and for corrected PGA)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT	     c1	    c2	     c3	     c4	    c5	     c6	     c7	    c8	     c9	     c10	c11	     c12	 c13	 c14	c15	    c16
    PGA	    -3.108	0.756	 0.000	-1.287	0.142	0.046	-0.040	0.587	 0.000	0.253	0.173	-0.135	-0.138	-0.256	0.630	0.975
    0.05	-1.918	0.756	 0.000	-1.517	0.309	0.069	-0.023	0.498	 0.000	0.058	0.100	-0.195	-0.274	-0.219	0.630	1.031
    0.08	-1.504	0.756	 0.000	-1.551	0.343	0.083	 0.000	0.487	 0.000	0.135	0.182	-0.224	-0.303	-0.263	0.630	1.031
    0.10	-1.672	0.756	 0.000	-1.473	0.282	0.062	 0.001	0.513	 0.000	0.168	0.210	-0.198	-0.275	-0.252	0.630	1.031
    0.15	-2.323	0.756	 0.000	-1.280	0.171	0.045	 0.008	0.591	 0.000	0.223	0.238	-0.170	-0.175	-0.270	0.630	1.031
    0.20	-2.998	0.756	 0.000	-1.131	0.089	0.028	 0.004	0.668	 0.000	0.234	0.256	-0.098	-0.041	-0.311	0.571	1.031
    0.30	-3.721	0.756	 0.007	-1.028	0.050	0.010	 0.004	0.736	 0.007	0.249	0.328	-0.026	 0.082	-0.265	0.488	1.031
    0.40	-4.536	0.756	-0.015	-0.812	0.012	0.000	 0.000	0.931	-0.018	0.299	0.317	-0.017	 0.022	-0.257	0.428	1.031
    0.50	-4.651	0.756	-0.035	-0.812	0.012	0.000	 0.000	0.931	-0.043	0.243	0.354	-0.020	 0.092	-0.293	0.383	1.031
    0.75	-4.903	0.756	-0.071	-0.812	0.012	0.000	 0.000	0.931	-0.087	0.295	0.418	 0.078	 0.091	-0.349	0.299	1.031
    1.00	-4.950	0.756	-0.101	-0.812	0.012	0.000	 0.000	0.931	-0.124	0.266	0.315	 0.043	 0.101	-0.481	0.240	1.031
    1.50	-5.073	0.756	-0.150	-0.812	0.012	0.000	 0.000	0.931	-0.184	0.171	0.211	-0.038	-0.018	-0.518	0.240	1.031
    2.00	-5.292	0.756	-0.180	-0.812	0.012	0.000	 0.000	0.931	-0.222	0.114	0.115	 0.033	-0.022	-0.503	0.240	1.031
    3.00	-5.748	0.756	-0.193	-0.812	0.012	0.000	 0.000	0.931	-0.238	0.179	0.159	-0.010	-0.047	-0.539	0.240	1.031
    4.00	-6.042	0.756	-0.202	-0.812	0.012	0.000	 0.000	0.931	-0.248	0.237	0.134	-0.059	-0.267	-0.606	0.240	1.031
    """)
