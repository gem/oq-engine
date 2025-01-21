# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
Module exports :class:`BahrampouriEtAldm2021`
               :class:`BahrampouriEtAldm2021ASC`
               :class:`BahrampouriEtAldm2021SSlab`
               :class:`BahrampouriEtAldm2021SInter`
"""
import numpy as np
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import RSD595, RSD575


def _get_source_term(trt, C, ctx):
    """
    Compute the source term described in Eq. 8:
    `` 10.^(m1*(M-m2))+m3``
    m3 = varies as per focal mechanism for ASC and Slab TRTs
    """
    if trt == const.TRT.SUBDUCTION_INTERFACE:
        m3 = np.full_like(ctx.rake, C["m3_RS"])  # reverse
    else:
        ss = C["m3_SS"]  # strike-slip
        m3 = np.full_like(ctx.rake, ss)
        m3[(ctx.rake <= -45.) & (ctx.rake >= -135.)] = C["m3_NS"]  # normal
        m3[(ctx.rake >= 45.) & (ctx.rake <= 135.)] = C["m3_RS"]  # reverse
    fsource = np.round(10 ** (C['m1'] * (ctx.mag - C['m2'])) + m3, 4)
    return fsource


def _get_path_term(C, ctx):
    """
    Implementing Eqs. 9, 10 and 11
    """
    slope = C['r1'] + C['r2'] * (ctx.mag - 4.0)
    mse = (ctx.mag - C['M1']) / (C['M2'] - C['M1'])
    mse[ctx.mag > C['M2']] = 1.
    mse[ctx.mag <= C['M1']] = 0.
    fpath = np.round(slope * ctx.rrup, 4)
    idx = ctx.rrup > C['R1']
    term = mse[idx] * (ctx.rrup[idx] - C['R1'])
    fpath[idx] = np.round(slope[idx] * (C['R1'] + term), 4)
    return fpath


def _get_basin_term(C, ctx, region=None):
    """
    Get the basin term
    """
    mean_z1pt0 = (np.exp(((-5.23 / 2.) * np.log((ctx.vs30 ** 2. +
                  412.39 ** 2.) / (1360 ** 2. + 412.39 ** 2.)))-0.9))
    delta_z1pt0 = np.round(ctx.z1pt0 - mean_z1pt0, 4)
    return C['s2'] * np.minimum(delta_z1pt0, 250.0)


def _get_site_term(C, ctx):
    """
    Implementing Eqs. 5, 6 and 12
    """
    fbasin = _get_basin_term(C, ctx)

    fsite = np.round(C['s1'] * np.log(np.clip(ctx.vs30, None, 600.0) / 600.0) +
                     fbasin + C['s3'], 4)

    return fsite


def _get_stddevs(C):
    """
    The authors have provided the values of
    sigma = np.sqrt(tau**2+phi_ss**2+phi_s2s**2)
    The within event term (phi) has been calculated by
    combining the phi_ss and phi_s2s
    """
    sig = C['sig']
    tau = C['tau']
    phi = np.sqrt(C['phi_ss']**2 + C['phi_s2s']**2)
    return sig, tau, phi


class BahrampouriEtAldm2021Asc(GMPE):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek
    and Russell A Green developed from the KiK-net database. This GMPE is
    specifically derived for significant durations: Ds5-Ds95,D25-Ds75. This
    GMPE is described in a paper published in 2021 on Earthquake Spectra,
    Volume 37, Pg 903-920 and titled 'Ground motion prediction equations for
    significant duration using the KiK-net database'.
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are 5 - 95 % Arias and 5 - 75 % Arias
    #: significant duration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {RSD595, RSD575}

    #: Supported intensity measure component is the geometric mean horizontal
    #: component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0'}

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is closest distance to rupture
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = np.log(
                _get_source_term(trt, C, ctx) + _get_path_term(C, ctx)
            ) + _get_site_term(C, ctx)
            sig[m], tau[m], phi[m] = _get_stddevs(C)


    COEFFS = CoeffsTable(table="""
    imt        m1     m2    m3_RS   m3_SS   m3_NS   M1    M2     r1      r2   R1       s1       s2      s3      sig    tau    phi_s2s  phi_ss
    rsd595  0.6899  6.511   4.584   4.252   5.522   4.    6.5  0.21960    0.  60.  -0.3008  0.00119   -0.1107  0.462   0.204   0.185    0.370
    rsd575  0.7966  6.5107 0.06828  0.2902  0.613   4.    6.5  0.1248     0.  60.  -0.1894  0.0003362 -0.03979 0.586   0.233   0.223    0.490
    """)


class BahrampouriEtAldm2021SSlab(BahrampouriEtAldm2021Asc):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek
    and Russell A Green developed from the KiK-net database. This GMPE is
    specifically derived for significant durations: Ds5-Ds95,D25-Ds75. This
    GMPE is described in a paper published in 2021 on Earthquake Spectra,
    Volume 37, Pg 903-920 and titled 'Ground motion prediction equations for
    significant duration using the KiK-net database'.
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Supported intensity measure types are 5 - 95 % Arias and 5 - 75 % Arias
    #: significant duration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {RSD595, RSD575}

    #: Supported intensity measure component is the geometric mean horizontal
    #: component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0'}

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is closest distance to rupture
    REQUIRES_DISTANCES = {'rrup'}

    COEFFS = CoeffsTable(sa_damping=5, table="""
    imt       m1     m2    m3_RS  m3_SS  m3_NS   M1  M2    r1      r2      R1     s1      s2        s3      sig    tau    phi_s2s  phi_ss
    rsd595  0.385  4.1604  5.828  4.231  5.496  5.5  8.0  0.09936  0.02495  200.0  -0.244  0.001409  -0.04109  0.458   0.194   0.245   0.335
    rsd575  0.4232 5.1674  0.975  0.3965 0.8712 5.0  8.0  0.057576  0.01316  200.0  -0.1431  0.001440  0.04534  0.593   0.261   0.288   0.449
    """)


class BahrampouriEtAldm2021SInter(BahrampouriEtAldm2021Asc):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek
    and Russell A Green developed from the KiK-net database. This GMPE is
    specifically derived for significant durations: Ds5-Ds95,D25-Ds75. This
    GMPE is described in a paper published in 2021 on Earthquake Spectra,
    Volume 37, Pg 903-920 and titled 'Ground motion prediction equations for
    significant duration using the KiK-net database'.
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are 5 - 95 % Arias and 5 - 75 % Arias
    #: significant duration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {RSD595, RSD575}

    #: Supported intensity measure component is the geometric mean horizontal
    #: component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0'}

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is closest distance to rupture
    REQUIRES_DISTANCES = {'rrup'}

    COEFFS = CoeffsTable(sa_damping=5, table="""
    imt       m1     m2      m3_RS  M1    M2    r1      r2       R1           s1      s2        s3      sig    tau    phi_s2s  phi_ss
    rsd595  0.2384  4.16    8.4117  5.5    8.0  0.08862  0.04194   200.0  -0.2875 0.001234  -0.03137  0.403  0.191   0.233    0.275
    rsd575  0.4733  6.1623  0.515   5.0    8.0  0.07505  0.0156    200.0  -0.1464 0.00075     0.357   0.490  0.218   0.238    0.369
    """)
