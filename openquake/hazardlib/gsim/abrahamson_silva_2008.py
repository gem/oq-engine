# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
Module exports :class:`AbrahamsonSilva2008`.
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA

#: equation constants (that are IMT independent)
#: coefficients in table 4, page 84
CONSTS = {
    'c1': 6.75,
    'c4': 4.5,
    'a3': 0.265,
    'a4': -0.231,
    'a5': -0.398,
    'n': 1.18,
    'c': 1.88,
    'c2': 50,
    'sigma_amp': 0.3}


def _compute_base_term(C, ctx):
    """
    Compute and return base model term, that is the first term in equation
    1, page 74. The calculation of this term is explained in paragraph
    'Base Model', page 75.
    """
    c1 = CONSTS['c1']
    R = np.sqrt(ctx.rrup ** 2 + CONSTS['c4'] ** 2)

    base_term = (C['a1'] +
                 C['a8'] * ((8.5 - ctx.mag) ** 2) +
                 (C['a2'] + CONSTS['a3'] * (ctx.mag - c1)) *
                 np.log(R))
    extra_term = np.where(ctx.mag <= c1,
                          CONSTS['a4'] * (ctx.mag - c1),
                          CONSTS['a5'] * (ctx.mag - c1))
    return base_term + extra_term


def _compute_faulting_style_term(C, ctx):
    """
    Compute and return faulting style term, that is the sum of the second
    and third terms in equation 1, page 74.
    """
    # ranges of rake values for each faulting mechanism are specified in
    # table 2, page 75
    return (C['a12'] * ((ctx.rake > 30) & (ctx.rake < 150)) +
            C['a13'] * ((ctx.rake > -120) & (ctx.rake < -60)))


def _compute_site_response_term(C, imt, ctx, pga1100):
    """
    Compute and return site response model term, that is the fifth term
    in equation 1, page 74.
    """
    site_resp_term = np.zeros_like(ctx.vs30)

    vs30_star, _ = _compute_vs30_star_factor(imt, ctx.vs30)
    vlin, c, n = C['VLIN'], CONSTS['c'], CONSTS['n']
    a10, b = C['a10'], C['b']

    idx = ctx.vs30 < vlin
    arg = vs30_star[idx] / vlin
    site_resp_term[idx] = (a10 * np.log(arg) -
                           b * np.log(pga1100[idx] + c) +
                           b * np.log(pga1100[idx] + c * (arg ** n)))

    idx = ctx.vs30 >= vlin
    site_resp_term[idx] = (a10 + b * n) * np.log(vs30_star[idx] / vlin)

    return site_resp_term


def _compute_hanging_wall_term(C, ctx):
    """
    Compute and return hanging wall model term, that is the sixth term in
    equation 1, page 74. The calculation of this term is explained in
    paragraph 'Hanging-Wall Model', page 77.
    """
    idx = (ctx.rx > 0) & (ctx.dip != 90.0)
    Fhw = np.zeros_like(ctx.rx)
    Fhw[idx] = 1

    # equation 8, page 77
    T1 = np.zeros_like(ctx.rx)
    idx1 = (ctx.rjb < 30.0) & idx
    T1[idx1] = 1.0 - ctx.rjb[idx1] / 30.0

    # equation 9, page 77
    T2 = np.ones_like(ctx.rx)
    idx2 = (ctx.rx <= ctx.width * np.cos(np.radians(ctx.dip))) & idx
    T2[idx2] = 0.5 + ctx.rx[idx2] / (
        2 * ctx.width[idx2] * np.cos(np.radians(ctx.dip[idx2])))

    # equation 10, page 78
    T3 = np.ones_like(ctx.rx)
    idx3 = (ctx.rx < ctx.ztor) & idx
    T3[idx3] = ctx.rx[idx3] / ctx.ztor[idx3]

    # equation 11, page 78
    T4 = ctx.mag - 6
    T4[ctx.mag <= 6.] = 0.
    T4[ctx.mag >= 7.] = 1.0

    # equation 5, in AS08_NGA_errata.pdf
    T5 = np.where(ctx.dip >= 30, 1.0 - (ctx.dip - 30.0) / 60.0, 1.0)

    return Fhw * C['a14'] * T1 * T2 * T3 * T4 * T5


def _compute_top_of_rupture_depth_term(C, ctx):
    """
    Compute and return top of rupture depth term, that is the seventh term
    in equation 1, page 74. The calculation of this term is explained in
    paragraph 'Depth-to-Top of Rupture Model', page 78.
    """
    return np.where(ctx.ztor >= 10, C['a16'], C['a16'] * ctx.ztor / 10.0)


def _compute_large_distance_term(C, ctx):
    """
    Compute and return large distance model term, that is the 8-th term
    in equation 1, page 74. The calculation of this term is explained in
    paragraph 'Large Distance Model', page 78.
    """
    # equation 15, page 79
    T6 = 0.5 * (6.5 - ctx.mag) + 0.5
    T6[ctx.mag < 5.5] = 1.0
    T6[ctx.mag >= 6.5] = 0.5

    # equation 14, page 79
    large_distance_term = np.zeros_like(ctx.rrup)
    idx = ctx.rrup >= 100.0
    large_distance_term[idx] = C['a18'] * (ctx.rrup[idx] - 100.0) * T6[idx]

    return large_distance_term


def _get_basin_term(C, ctx, region, imt, v1100=None):
    """
    Compute and return soil depth model term, that is the 9-th term in
    equation 1, page 74. The calculation of this term is explained in
    paragraph 'Soil Depth Model', page 79.
    """
    z1pt0 = ctx.z1pt0.copy()
    
    # Use GMM's vs30 to z1pt0 for none-measured values
    mask = z1pt0 == -999
    z1pt0[mask] = _compute_median_z1pt0(ctx.vs30[mask])
    
    if v1100 is None:
        vs30 = ctx.vs30
    else:
        vs30 = v1100
    a21 = _compute_a21_factor(C, imt, z1pt0, vs30)
    a22 = _compute_a22_factor(imt)
    median_z1pt0 = _compute_median_z1pt0(vs30)

    soil_depth_term = a21 * np.log((z1pt0 + CONSTS['c2']) /
                                   (median_z1pt0 + CONSTS['c2']))

    idx = z1pt0 >= 200
    soil_depth_term[idx] += a22 * np.log(z1pt0[idx] / 200)

    return soil_depth_term


def _compute_imt1100(C_PGA, ctx):
    """
    Compute and return mean imt value for rock conditions
    (vs30 = 1100 m/s)
    """
    imt = PGA()
    vs30_1100 = np.zeros_like(ctx.vs30) + 1100
    vs30_star, _ = _compute_vs30_star_factor(imt, vs30_1100)
    mean = (_compute_base_term(C_PGA, ctx) +
            _compute_faulting_style_term(C_PGA, ctx) +
            _compute_hanging_wall_term(C_PGA, ctx) +
            _compute_top_of_rupture_depth_term(C_PGA, ctx) +
            _compute_large_distance_term(C_PGA, ctx) +
            _get_basin_term(C_PGA, ctx, None, imt, vs30_1100) +
            # this is the site response term in case of vs30=1100
            ((C_PGA['a10'] + C_PGA['b'] * CONSTS['n']) *
             np.log(vs30_star / C_PGA['VLIN'])))

    return mean


def _get_stddevs(C, C_PGA, pga1100, ctx):
    """
    Return standard deviations as described in paragraph 'Equations for
    standard deviation', page 81.
    """
    std_intra = _compute_intra_event_std(C, C_PGA, pga1100, ctx.mag,
                                         ctx.vs30, ctx.vs30measured)
    std_inter = _compute_inter_event_std(C, C_PGA, pga1100, ctx.mag,
                                         ctx.vs30)
    return [np.sqrt(std_intra ** 2 + std_inter ** 2), std_inter, std_intra]


def _compute_intra_event_std(C, C_PGA, pga1100, mag, vs30, vs30measured):
    """
    Compute intra event standard deviation (equation 24) as described
    in the errata and not in the original paper.
    """
    sigma_b = _compute_sigma_b(C, mag, vs30measured)
    sigma_b_pga = _compute_sigma_b(C_PGA, mag, vs30measured)
    delta_amp = _compute_partial_derivative_site_amp(C, pga1100, vs30)

    std_intra = np.sqrt(sigma_b ** 2 + CONSTS['sigma_amp'] ** 2 +
                        (delta_amp ** 2) * (sigma_b_pga ** 2) +
                        2 * delta_amp * sigma_b * sigma_b_pga * C['rho'])

    return std_intra


def _compute_inter_event_std(C, C_PGA, pga1100, mag, vs30):
    """
    Compute inter event standard deviation, equation 25, page 82.
    """
    tau_0 = _compute_std_0(C['s3'], C['s4'], mag)
    tau_b_pga = _compute_std_0(C_PGA['s3'], C_PGA['s4'], mag)
    delta_amp = _compute_partial_derivative_site_amp(C, pga1100, vs30)

    std_inter = np.sqrt(tau_0 ** 2 + (delta_amp ** 2) * (tau_b_pga ** 2) +
                        2 * delta_amp * tau_0 * tau_b_pga * C['rho'])

    return std_inter


def _compute_sigma_b(C, mag, vs30measured):
    """
    Equation 23, page 81.
    """
    sigma_0 = _compute_sigma_0(C, mag, vs30measured)
    sigma_amp = CONSTS['sigma_amp']

    return np.sqrt(sigma_0 ** 2 - sigma_amp ** 2)


def _compute_sigma_0(C, mag, vs30measured):
    """
    Equation 27, page 82.
    """
    s1 = np.zeros_like(vs30measured, dtype=float)
    s2 = np.zeros_like(vs30measured, dtype=float)

    idx = vs30measured == 1
    s1[idx] = C['s1mea']
    s2[idx] = C['s2mea']

    idx = vs30measured == 0
    s1[idx] = C['s1est']
    s2[idx] = C['s2est']

    return _compute_std_0(s1, s2, mag)


def _compute_std_0(c1, c2, mag):
    """
    Common part of equations 27 and 28, pag 82.
    """
    res = c1 + (c2 - c1) * (mag - 5) / 2
    res[mag < 5] = c1[mag < 5] if isinstance(c1, np.ndarray) else c1
    res[mag > 7] = c2[mag > 7] if isinstance(c2, np.ndarray) else c2
    return res


def _compute_partial_derivative_site_amp(C, pga1100, vs30):
    """
    Partial derivative of site amplification term with respect to
    PGA on rock (equation 26), as described in the errata and not
    in the original paper.
    """
    delta_amp = np.zeros_like(vs30)
    vlin = C['VLIN']
    c = CONSTS['c']
    b = C['b']
    n = CONSTS['n']

    idx = vs30 < vlin
    delta_amp[idx] = (- b * pga1100[idx] / (pga1100[idx] + c) +
                      b * pga1100[idx] / (pga1100[idx] + c *
                      ((vs30[idx] / vlin) ** n)))

    return delta_amp


def _compute_a21_factor(C, imt, z1pt0, vs30):
    """
    Compute and return a21 factor, equation 18, page 80.
    """
    e2 = _compute_e2_factor(imt, vs30)
    a21 = e2.copy()

    vs30_star, v1 = _compute_vs30_star_factor(imt, vs30)
    median_z1pt0 = _compute_median_z1pt0(vs30)

    numerator = ((C['a10'] + C['b'] * CONSTS['n']) *
                 np.log(vs30_star / np.min([v1, 1000])))
    denominator = np.log((z1pt0 + CONSTS['c2']) /
                         (median_z1pt0 + CONSTS['c2']))

    idx = numerator + e2 * denominator < 0
    a21[idx] = - numerator[idx] / denominator[idx]

    idx = vs30 >= 1000
    a21[idx] = 0.0

    return a21


def _compute_vs30_star_factor(imt, vs30):
    """
    Compute and return vs30 star factor, equation 5, page 77.
    """
    v1 = _compute_v1_factor(imt)
    vs30_star = vs30.copy()
    vs30_star[vs30_star >= v1] = v1

    return vs30_star, v1


def _compute_v1_factor(imt):
    """
    Compute and return v1 factor, equation 6, page 77.
    """
    if imt.string[:2] == "SA":
        t = imt.period
        if t <= 0.50:
            v1 = 1500.0
        elif t > 0.50 and t <= 1.0:
            v1 = np.exp(8.0 - 0.795 * np.log(t / 0.21))
        elif t > 1.0 and t < 2.0:
            v1 = np.exp(6.76 - 0.297 * np.log(t))
        else:
            v1 = 700.0
    elif imt.string == "PGA":
        v1 = 1500.0
    else:
        # this is for PGV
        v1 = 862.0

    return v1


def _compute_e2_factor(imt, vs30):
    """
    Compute and return e2 factor, equation 19, page 80.
    """
    e2 = np.zeros_like(vs30)

    if imt.string == "PGV":
        period = 1
    elif imt.string == "PGA":
        period = 0
    else:
        period = imt.period

    if period < 0.35:
        return e2
    else:
        idx = vs30 <= 1000
        if period >= 0.35 and period <= 2.0:
            e2[idx] = (-0.25 * np.log(vs30[idx] / 1000) *
                       np.log(period / 0.35))
        elif period > 2.0:
            e2[idx] = (-0.25 * np.log(vs30[idx] / 1000) *
                       np.log(2.0 / 0.35))
        return e2


def _compute_median_z1pt0(vs30):
    """
    Compute and return median z1pt0 (in m), equation 17, pqge 79.
    """
    z1pt0_median = np.full_like(vs30, 6.745)

    idx = np.where((vs30 >= 180.0) & (vs30 <= 500.0))
    z1pt0_median[idx] = 6.745 - 1.35 * np.log(vs30[idx] / 180.0)

    idx = vs30 > 500.0
    z1pt0_median[idx] = 5.394 - 4.48 * np.log(vs30[idx] / 500.0)

    return np.exp(z1pt0_median)


def _compute_a22_factor(imt):
    """
    Compute and return the a22 factor, equation 20, page 80.
    """
    if imt.string == 'PGV':
        return 0.0
    period = imt.period
    if period < 2.0:
        return 0.0
    else:
        return 0.0625 * (period - 2.0)


class AbrahamsonSilva2008(GMPE):
    """
    Implements GMPE developed by Norman Abrahamson and Walter Silva and
    published as "Summary of the Abrahamson & Silva NGA Ground-Motion
    Relations" (2008, Earthquakes Spectra, Volume 24, Number 1, pages 67-97).
    This class implements only the equations for mainshock/foreshocks/swarms
    type events, that is the aftershock term (4th term in equation 1, page 74)
    is set to zero. The constant displacement model (page 80) is also not
    implemented (that is equation 1, page 74 is used for all periods and no
    correction is applied for periods greater than the constant displacement
    period). This class implements also the corrections (for standard
    deviation and hanging wall term calculation) as described in:
    http://peer.berkeley.edu/products/abrahamson-silva_nga_report_files/
    AS08_NGA_errata.pdf
    """
    #: Supported tectonic region type is active shallow crust, see paragraph
    #: 'Data Set Selection', see page 68.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration, peak
    #: ground velocity and peak ground acceleration, see tables 5a and 5b
    #: pages 84, 85, respectively.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is orientation-independent
    #: average horizontal :attr:`~openquake.hazardlib.const.IMC.GMRotI50`,
    #: see abstract, page 67.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotI50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see paragraph "Equations for standard deviations", page 81.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30, Vs30 type (measured or inferred),
    #: and Z1.0, see paragraph 'Soil Depth Model', page 79, and table 6,
    #: page 86.
    REQUIRES_SITES_PARAMETERS = {'vs30', 'vs30measured', 'z1pt0'}

    #: Required rupture parameters are magnitude, rake, dip, ztor, and width
    #: (see table 2, page 75)
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'dip', 'ztor', 'width'}

    #: Required distance measures are Rrup, Rjb and Rx (see Table 2, page 75).
    REQUIRES_DISTANCES = {'rrup', 'rjb', 'rx'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        C_PGA = self.COEFFS[PGA()]

        # compute median pga on rock (vs30=1100), needed for site response
        # term calculation
        pga1100 = np.exp(_compute_imt1100(C_PGA, ctx))
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (_compute_base_term(C, ctx) +
                       _compute_faulting_style_term(C, ctx) +
                       _compute_site_response_term(C, imt, ctx, pga1100) +
                       _compute_hanging_wall_term(C, ctx) +
                       _compute_top_of_rupture_depth_term(C, ctx) +
                       _compute_large_distance_term(C, ctx) +
                       _get_basin_term(C, ctx, None, imt))

            sig[m], tau[m], phi[m] = _get_stddevs(C, C_PGA, pga1100, ctx)

    #: Coefficient tables obtained by joining table 5a page 84, and table 5b
    #: page 85.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    VLIN     b       a1       a2       a8       a10     a12      a13     a14      a15      a16      a18     s1est  s2est  s1mea  s2mea  s3     s4     rho
    pga     865.1  -1.186   0.804   -0.9679  -0.0372   0.9445  0.0000  -0.0600  1.0800  -0.3500   0.9000  -0.0067  0.590  0.470  0.576  0.453  0.470  0.300  1.000
    0.010   865.1  -1.186   0.811   -0.9679  -0.0372   0.9445  0.0000  -0.0600  1.0800  -0.3500   0.9000  -0.0067  0.590  0.470  0.576  0.453  0.420  0.300  1.000
    0.020   865.1  -1.219   0.855   -0.9774  -0.0372   0.9834  0.0000  -0.0600  1.0800  -0.3500   0.9000  -0.0067  0.590  0.470  0.576  0.453  0.420  0.300  1.000
    0.030   907.8  -1.273   0.962   -1.0024  -0.0372   1.0471  0.0000  -0.0600  1.1331  -0.3500   0.9000  -0.0067  0.605  0.478  0.591  0.461  0.462  0.305  0.991
    0.040   994.5  -1.308   1.037   -1.0289  -0.0315   1.0884  0.0000  -0.0600  1.1708  -0.3500   0.9000  -0.0067  0.615  0.483  0.602  0.466  0.492  0.309  0.982
    0.050  1053.5  -1.346   1.133   -1.0508  -0.0271   1.1333  0.0000  -0.0600  1.2000  -0.3500   0.9000  -0.0076  0.623  0.488  0.610  0.471  0.515  0.312  0.973
    0.075  1085.7  -1.471   1.375   -1.0810  -0.0191   1.2808  0.0000  -0.0600  1.2000  -0.3500   0.9000  -0.0093  0.630  0.495  0.617  0.479  0.550  0.317  0.952
    0.100  1032.5  -1.624   1.563   -1.0833  -0.0166   1.4613  0.0000  -0.0600  1.2000  -0.3500   0.9000  -0.0093  0.630  0.501  0.617  0.485  0.550  0.321  0.929
    0.150   877.6  -1.931   1.716   -1.0357  -0.0254   1.8071  0.0181  -0.0600  1.1683  -0.3500   0.9000  -0.0093  0.630  0.509  0.616  0.491  0.550  0.326  0.896
    0.200   748.2  -2.188   1.687   -0.9700  -0.0396   2.0773  0.0309  -0.0600  1.1274  -0.3500   0.9000  -0.0083  0.630  0.514  0.614  0.495  0.520  0.329  0.874
    0.250   654.3  -2.381   1.646   -0.9202  -0.0539   2.2794  0.0409  -0.0600  1.0956  -0.3500   0.9000  -0.0069  0.630  0.518  0.612  0.497  0.497  0.332  0.856
    0.300   587.1  -2.518   1.601   -0.8974  -0.0656   2.4201  0.0491  -0.0600  1.0697  -0.3500   0.9000  -0.0057  0.630  0.522  0.611  0.499  0.479  0.335  0.841
    0.400   503.0  -2.657   1.511   -0.8677  -0.0807   2.5510  0.0619  -0.0600  1.0288  -0.3500   0.8423  -0.0039  0.630  0.527  0.608  0.501  0.449  0.338  0.818
    0.500   456.6  -2.669   1.397   -0.8475  -0.0924   2.5395  0.0719  -0.0600  0.9971  -0.3191   0.7458  -0.0025  0.630  0.532  0.606  0.504  0.426  0.341  0.783
    0.750   410.5  -2.401   1.137   -0.8206  -0.1137   2.1493  0.0800  -0.0600  0.9395  -0.2629   0.5704   0.0000  0.630  0.539  0.602  0.506  0.385  0.346  0.680
    1.000   400.0  -1.955   0.915   -0.8088  -0.1289   1.5705  0.0800  -0.0600  0.8985  -0.2230   0.4460   0.0000  0.630  0.545  0.594  0.503  0.350  0.350  0.607
    1.500   400.0  -1.025   0.510   -0.7995  -0.1534   0.3991  0.0800  -0.0600  0.8409  -0.1668   0.2707   0.0000  0.615  0.552  0.566  0.497  0.350  0.350  0.504
    2.000   400.0  -0.299   0.192   -0.7960  -0.1708  -0.6072  0.0800  -0.0600  0.8000  -0.1270   0.1463   0.0000  0.604  0.558  0.544  0.491  0.350  0.350  0.431
    3.000   400.0   0.000  -0.280   -0.7960  -0.1954  -0.9600  0.0800  -0.0600  0.4793  -0.0708  -0.0291   0.0000  0.589  0.565  0.527  0.500  0.350  0.350  0.328
    4.000   400.0   0.000  -0.639   -0.7960  -0.2128  -0.9600  0.0800  -0.0600  0.2518  -0.0309  -0.1535   0.0000  0.578  0.570  0.515  0.505  0.350  0.350  0.255
    5.000   400.0   0.000  -0.936   -0.7960  -0.2263  -0.9208  0.0800  -0.0600  0.0754   0.0000  -0.2500   0.0000  0.570  0.587  0.510  0.529  0.350  0.350  0.200
    7.500   400.0   0.000  -1.527   -0.7960  -0.2509  -0.7700  0.0800  -0.0600  0.0000   0.0000  -0.2500   0.0000  0.611  0.618  0.572  0.579  0.350  0.350  0.200
    10.00   400.0   0.000  -1.993   -0.7960  -0.2683  -0.6630  0.0800  -0.0600  0.0000   0.0000  -0.2500   0.0000  0.640  0.640  0.612  0.612  0.350  0.350  0.200
    pgv     400.0  -1.955   5.7578  -0.9046  -0.1200   1.5390  0.0800  -0.0600  0.7000  -0.3900   0.6300   0.0000  0.590  0.470  0.576  0.453  0.420  0.300  0.740
    """)
