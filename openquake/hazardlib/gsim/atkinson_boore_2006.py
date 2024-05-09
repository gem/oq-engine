# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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
Module exports :class:`BooreAtkinson2008`,
:class:`AtkinsonBoore2006`,
:class:`AtkinsonBoore2006Modified2011`.
:class:`AtkinsonBoore2006SGS`.
"""
import numpy as np
from scipy.constants import g
from math import log10

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable, add_alias
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.utils import (
    mblg_to_mw_atkinson_boore_87, mblg_to_mw_johnston_96, clip_mean,
    get_fault_type_dummy_variables)

#: IMT-independent coefficients. std_total is the total standard deviation,
#: see Table 6, pag 2192 and Table 9, pag 2202. R0, R1, R2 are coefficients
#: required for mean calculation - see equation (5) pag 2191. v1, v2, Vref
#: are coefficients required for soil response calculation, see table 8,
#: p. 2201
# the std is converted from base 10 to base e
std_total = np.log(10 ** 0.30),
R0 = 10.0
R1 = 70.0
R2 = 140.0
# v1 = 180.0
# v2 = 300.0
# Vref = 760.0


def _clip_distances(rrup):
    """
    Return array of distances with values clipped to 1. See end of
    paragraph 'Methodology and Model Parameters', p. 2182. The equations
    have a singularity for distance = 0, so that's why distances are
    clipped to 1.
    """
    rrup = rrup.copy()
    rrup[rrup < 1] = 1
    return rrup


def _compute_distance_scaling(ctx, C):
    """
    Compute distance-scaling term, equations (3) and (4), pag 107.
    """
    Mref = 4.5
    Rref = 1.0
    R = np.sqrt(ctx.rjb ** 2 + C['h'] ** 2)
    return (C['c1'] + C['c2'] * (ctx.mag - Mref)) * np.log(R / Rref) + \
        C['c3'] * (R - Rref)


def _compute_f0_factor(rrup):
    """
    Compute and return factor f0 - see equation (5), 6th term, p. 2191.
    """
    f0 = np.log10(R0 / rrup)
    f0[f0 < 0] = 0.0
    return f0


def _compute_f1_factor(rrup):
    """
    Compute and return factor f1 - see equation (5), 4th term, p. 2191
    """
    f1 = np.log10(rrup)
    logR1 = np.log10(R1)
    f1[f1 > logR1] = logR1
    return f1


def _compute_f2_factor(rrup):
    """
    Compute and return factor f2, see equation (5), 5th term, pag 2191
    """
    f2 = np.log10(rrup / R2)
    f2[f2 < 0] = 0.0
    return f2


def _compute_magnitude_scaling(ctx, C):
    """
    Compute magnitude-scaling term, equations (5a) and (5b), pag 107.
    """
    return _compute_ms(ctx, C)


def _compute_mean(C, f0, f1, f2, SC, mag, rrup, idxs, mean, scale_fac):
    """
    Compute mean value (for a set of indexes) without site amplification
    terms. This is equation (5), p. 2191, without S term.
    """
    if idxs.sum() == 0:  # no effect
        return
    if isinstance(scale_fac, np.ndarray):
        scale_fac = scale_fac[idxs]
    mag = mag[idxs]
    sda = _compute_stress_drop_adjustment(SC, mag, scale_fac)
    mean[idxs] = (C['c1'] +
                  C['c2'] * mag +
                  C['c3'] * (mag ** 2) +
                  (C['c4'] + C['c5'] * mag) * f1[idxs] +
                  (C['c6'] + C['c7'] * mag) * f2[idxs] +
                  (C['c8'] + C['c9'] * mag) * f0[idxs] +
                  C['c10'] * rrup[idxs] + sda)


def _compute_ms(ctx, C):
    SS, NS, RS = get_fault_type_dummy_variables(ctx)
    res = C['e2'] * SS + C['e3'] * NS + C['e4'] * RS + C['e7'] * (
        ctx.mag - C['Mh'])
    less = ctx.mag <= C['Mh']
    res[less] = (C['e2'] * SS[less] + C['e3'] * NS[less] + C['e4'] * RS[less] +
                 C['e5'] * (ctx.mag[less] - C['Mh']) + C['e6'] *
                 (ctx.mag[less] - C['Mh']) ** 2)
    return res


def _compute_non_linear_slope(vs30, C):
    """
    Compute non-linear slope factor,
    equations (13a) to (13d), pag 108-109.
    """
    V1 = 180.0
    V2 = 300.0
    Vref = 760.0

    # equation (13d), values are zero for vs30 >= Vref = 760.0
    bnl = np.zeros(vs30.shape)

    # equation (13a)
    bnl[vs30 <= V1] = C['b1']

    # equation (13b)
    idx = np.where((vs30 > V1) & (vs30 <= V2))
    bnl[idx] = (C['b1'] - C['b2']) * \
        np.log(vs30[idx] / V2) / np.log(V1 / V2) + C['b2']

    # equation (13c)
    idx = np.where((vs30 > V2) & (vs30 < Vref))
    bnl[idx] = C['b2'] * np.log(vs30[idx] / Vref) / np.log(V2 / Vref)
    return bnl


def _compute_non_linear_term(pga4nl, bnl):
    """
    Compute non-linear term,
    equation (8a) to (8c), pag 108.
    """

    fnl = np.zeros(pga4nl.shape)
    if len(bnl) < len(fnl):  # single site case, fix shape
        bnl = np.repeat(bnl, len(fnl))
    a1 = 0.03
    a2 = 0.09
    pga_low = 0.06

    # equation (8a)
    idx = pga4nl <= a1
    fnl[idx] = bnl[idx] * np.log(pga_low / 0.1)

    # equation (8b)
    idx = np.where((pga4nl > a1) & (pga4nl <= a2))
    delta_x = np.log(a2 / a1)
    delta_y = bnl[idx] * np.log(a2 / pga_low)
    c = (3 * delta_y - bnl[idx] * delta_x) / delta_x ** 2
    d = -(2 * delta_y - bnl[idx] * delta_x) / delta_x ** 3
    fnl[idx] = bnl[idx] * np.log(pga_low / 0.1) +\
        c * (np.log(pga4nl[idx] / a1) ** 2) + \
        d * (np.log(pga4nl[idx] / a1) ** 3)

    # equation (8c)
    idx = pga4nl > a2
    fnl[idx] = np.squeeze(bnl[idx]) * np.log(pga4nl[idx] / 0.1)

    return fnl


def _compute_soil_amplification(C, vs30, pga_bc, mean):
    """
    Compute soil amplification, that is S term in equation (5), p. 2191,
    and add to mean values for non hard rock sites.
    """
    # convert from base e (as defined in BA2008) to base 10 (as used in
    # AB2006)
    sal = np.log10(np.exp(_get_site_amplification_linear(vs30, C)))
    sanl = np.log10(np.exp(
        _get_site_amplification_non_linear(vs30, pga_bc, C)))

    idxs = vs30 < 2000.0
    mean[idxs] = mean[idxs] + sal[idxs] + sanl[idxs]


def _compute_stress_drop_adjustment(SC, mag, scale_fac):
    """
    Compute equation (6) p. 2200
    """
    clipped_mag = np.clip(mag - SC['M1'], 0, None)
    return scale_fac * np.clip(
        0.05 + SC['delta'] * clipped_mag / (SC['Mh'] - SC['M1']),
        None, SC['delta'] + 0.05)


def _convert_magnitude(mag_eq, mag):
    """
    Convert magnitude from Mblg to Mw using various equations
    equation
    """
    if mag_eq == 'Mblg87':
        return mblg_to_mw_atkinson_boore_87(mag)
    elif mag_eq == 'Mblg96':
        return mblg_to_mw_johnston_96(mag)
    elif mag_eq == 'Mw':
        return mag


def _extract_coeffs(self, imt):
    """
    Extract dictionaries of coefficients specific to required
    intensity measure type.
    """
    C_HR = self.COEFFS_HARD_ROCK[imt]
    C_BC = self.COEFFS_BC[imt]
    C_SR = self.COEFFS_SOIL_RESPONSE[imt]
    SC = self.COEFFS_STRESS[imt]

    return C_HR, C_BC, C_SR, SC


def _get_mean(self, vs30, mag, rrup, imt, scale_fac):
    """
    Compute and return mean
    """
    C_HR, C_BC, C_SR, SC = _extract_coeffs(self, imt)

    rrup = _clip_distances(rrup)

    f0 = _compute_f0_factor(rrup)
    f1 = _compute_f1_factor(rrup)
    f2 = _compute_f2_factor(rrup)

    pga_bc = _get_pga_bc(
        self.COEFFS_BC[PGA()], f0, f1, f2, SC, mag, rrup, vs30, scale_fac)

    # compute mean values for hard-rock sites (vs30 >= 2000),
    # and non-hard-rock sites (vs30 < 2000) and add soil amplification
    # term
    mean = np.zeros_like(vs30)
    _compute_mean(C_HR, f0, f1, f2, SC, mag, rrup,
                  vs30 >= 2000.0, mean, scale_fac)
    _compute_mean(C_BC, f0, f1, f2, SC, mag, rrup,
                  vs30 < 2000.0, mean, scale_fac)
    _compute_soil_amplification(C_SR, vs30, pga_bc, mean)

    # convert from base 10 to base e
    if imt == PGV():
        mean = np.log(10 ** mean)
    else:
        # convert from cm/s**2 to g
        mean = np.log((10 ** mean) * 1e-2 / g)

    return mean


def _get_pga_bc(C_pga_bc, f0, f1, f2, SC, mag, rrup, vs30, scale_fac):
    """
    Compute and return PGA on BC boundary
    """
    pga_bc = np.zeros_like(vs30)
    _compute_mean(C_pga_bc, f0, f1, f2, SC, mag,
                  rrup, vs30 < 2000.0, pga_bc, scale_fac)

    return (10 ** pga_bc) * 1e-2 / g


def _get_pga_on_rock(C_pga, ctx):
    """
    Compute and return PGA on rock conditions (that is vs30 = 760.0 m/s).
    This is needed to compute non-linear site amplification term
    """
    # Median PGA in g for Vref = 760.0, without site amplification,
    # that is equation (1) pag 106, without the third and fourth terms
    # Mref and Rref values are given in the caption to table 6, pag 119
    # Note that in the original paper, the caption reads:
    # "Distance-scaling coefficients (Mref=4.5 and Rref=1.0 km for all
    # periods, except Rref=5.0 km for pga4nl)". However this is a mistake
    # as reported in http://www.daveboore.com/pubs_online.php:
    # ERRATUM: 27 August 2008. Tom Blake pointed out that the caption to
    # Table 6 should read "Distance-scaling coefficients (Mref=4.5 and
    # Rref=1.0 km for all periods)".
    pga4nl = np.exp(_compute_magnitude_scaling(ctx, C_pga) +
                    _compute_distance_scaling(ctx, C_pga))
    return pga4nl


def _get_site_amplification_linear(vs30, C):
    """
    Compute site amplification linear term,
    equation (7), pag 107.
    """
    return C['blin'] * np.log(vs30 / 760.0)


def _get_site_amplification_non_linear(vs30, pga4nl, C):
    """
    Compute site amplification non-linear term,
    equations (8a) to (13d), pag 108-109.
    """
    # non linear slope
    bnl = _compute_non_linear_slope(vs30, C)
    # compute the actual non-linear term
    return _compute_non_linear_term(pga4nl, bnl)


def set_sig(kind, C, sig, tau, phi):
    """
    Set standard deviations as defined in table 8, pag 121.
    """
    if kind == 'hawaii':
        # Using a frequency independent value of sigma as recommended
        # in the caption of Table 2 of Atkinson (2010)
        sig[:] = 0.26 / np.log10(np.e)
    elif kind == '2006':
        sig[:] = std_total
    else:
        sig[:] = C['std']
        tau[:] = C['tau']
        phi[:] = C['sigma']


def _get_stress_drop_scaling_factor(magnitude):
    """
    Returns the magnitude dependent stress drop scaling factor defined in
    equation 6 (page 1128) of Atkinson & Boore (2011)
    """
    stress_drop = 10.0 ** (3.45 - 0.2 * magnitude)
    cap = 10.0 ** (3.45 - 0.2 * 5.0)
    stress_drop[stress_drop > cap] = cap
    return np.log10(stress_drop / 140.0) / log10(2.0)


class AtkinsonBoore2006(GMPE):
    """
    Implements GMPE developed by Gail M. Atkinson and David M. Boore and
    published as "Earthquake Ground-Motion Prediction Equations for Eastern
    North America" (2006, Bulletin of the Seismological Society of America,
    Volume 96, No. 6, pages 2181-2205). This class implements only the
    equations for stress parameter of 140 bars. The correction described in
    'Adjustment of Equations to Consider Alternative Stress Parameters',
    p. 2198, is not implemented.
    This class uses the same soil amplification function as the
    BooreAtkinson2008. Note that in the paper, the reported soil
    amplification function is the one used in a preliminary version of the
    Boore and Atkinson 2008 GMPE, while the one that should be used is the
    one described in the final paper. See comment in:
    http://www.daveboore.com/pubs_online/ab06_gmpes_programs_and_tables.pdf
    """
    #: Supported tectonic region type is stable continental, given
    #: that the equations have been derived for Eastern North America
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration, see paragraph
    #: 'Methodology and Model Parameters', p. 2182
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`,
    #: personal communication with Gail Atkinson
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is total, see table 6
    #: and 9, p. 2192 and 2202, respectively.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameters is Vs30.
    #: See paragraph 'Equations for soil sites', p. 2200
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is magnitude (see
    #: paragraph 'Methodology and Model Parameters', p. 2182)
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rrup.
    #: See paragraph 'Methodology and Model Parameters', p. 2182
    REQUIRES_DISTANCES = {'rrup'}

    REQUIRES_ATTRIBUTES = {'mag_eq', 'scale_fac'}

    CUTOFF_RRUP = 0.

    kind = '2006'

    def __init__(self, mag_eq="NA", scale_fac=0, **kwargs):
        assert mag_eq in "Mblg87 Mblg96 Mw NA", mag_eq
        super().__init__(**kwargs)
        self.mag_eq = mag_eq
        self.scale_fac = scale_fac

    # used in the "Modified" version
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        if self.CUTOFF_RRUP:  # for SGS subclass
            ctx = ctx.copy()
            ctx.rrup[ctx.rrup <= self.CUTOFF_RRUP] = self.CUTOFF_RRUP
        for m, imt in enumerate(imts):
            if self.mag_eq == "NA":
                if 'Modified' in self.__class__.__name__:
                    # stress drop scaling factor is now a property of magnitude
                    scale_fac = _get_stress_drop_scaling_factor(ctx.mag)
                else:
                    scale_fac = 0
                mean[m] = _get_mean(
                    self, ctx.vs30, ctx.mag, ctx.rrup, imt,
                    scale_fac=scale_fac)
                set_sig(self.kind, None, sig[m], tau[m], phi[m])
            else:
                mag = _convert_magnitude(self.mag_eq, ctx.mag)
                # stress drop scaling factor defined in subroutine getAB06
                mean[m] = _get_mean(
                    self, ctx.vs30, mag, ctx.rrup, imt,
                    scale_fac=self.scale_fac)
                mean[m] = clip_mean(imt, mean[m])
                set_sig(self.kind, None, sig[m], tau[m], phi[m])

    # notice the presence of a dummy parameter `C` to keep the same
    # interface as the base class BooreAtkinson2008
    #: Hard rock coefficents, table 6, pag 2192,
    #: coefficient values taken from Fortran implementation of Dave Boore
    #: (higher precision than in the paper)
    COEFFS_HARD_ROCK = CoeffsTable(sa_damping=5, table="""\
    IMT     c1          c2          c3          c4          c5          c6          c7          c8          c9          c10
    5.000  -5.408E+00   1.714E+00  -9.012E-02  -2.537E+00   2.267E-01  -1.268E+00   1.162E-01   9.792E-01  -1.767E-01  -1.757E-04
    4.000  -5.791E+00   1.916E+00  -1.071E-01  -2.441E+00   2.113E-01  -1.162E+00   1.018E-01   1.012E+00  -1.824E-01  -2.010E-04
    3.125  -6.038E+00   2.080E+00  -1.221E-01  -2.367E+00   2.002E-01  -1.073E+00   8.950E-02   1.002E+00  -1.803E-01  -2.306E-04
    2.500  -6.169E+00   2.211E+00  -1.348E-01  -2.299E+00   1.898E-01  -9.860E-01   7.860E-02   9.683E-01  -1.765E-01  -2.823E-04
    2.000  -6.183E+00   2.302E+00  -1.442E-01  -2.223E+00   1.770E-01  -9.370E-01   7.067E-02   9.518E-01  -1.768E-01  -3.220E-04
    1.587  -6.043E+00   2.342E+00  -1.496E-01  -2.157E+00   1.662E-01  -8.704E-01   6.047E-02   9.207E-01  -1.734E-01  -3.748E-04
    1.250  -5.724E+00   2.324E+00  -1.505E-01  -2.104E+00   1.565E-01  -8.202E-01   5.186E-02   8.563E-01  -1.661E-01  -4.329E-04
    1.000  -5.272E+00   2.264E+00  -1.483E-01  -2.069E+00   1.497E-01  -8.132E-01   4.666E-02   8.262E-01  -1.622E-01  -4.862E-04
    0.794  -4.604E+00   2.132E+00  -1.406E-01  -2.062E+00   1.468E-01  -7.974E-01   4.345E-02   7.748E-01  -1.558E-01  -5.790E-04
    0.629  -3.917E+00   1.987E+00  -1.314E-01  -2.045E+00   1.419E-01  -7.818E-01   4.297E-02   7.878E-01  -1.590E-01  -6.948E-04
    0.500  -3.216E+00   1.826E+00  -1.201E-01  -2.018E+00   1.344E-01  -8.134E-01   4.437E-02   8.839E-01  -1.751E-01  -7.704E-04
    0.397  -2.437E+00   1.649E+00  -1.084E-01  -2.051E+00   1.363E-01  -8.426E-01   4.483E-02   7.386E-01  -1.557E-01  -8.509E-04
    0.315  -1.721E+00   1.483E+00  -9.739E-02  -2.080E+00   1.382E-01  -8.893E-01   4.869E-02   6.101E-01  -1.389E-01  -9.538E-04
    0.251  -1.121E+00   1.342E+00  -8.722E-02  -2.082E+00   1.349E-01  -9.714E-01   5.628E-02   6.140E-01  -1.432E-01  -1.055E-03
    0.199  -6.153E-01   1.227E+00  -7.886E-02  -2.087E+00   1.312E-01  -1.120E+00   6.788E-02   6.055E-01  -1.459E-01  -1.125E-03
    0.158  -1.455E-01   1.123E+00  -7.143E-02  -2.116E+00   1.302E-01  -1.303E+00   8.311E-02   5.617E-01  -1.438E-01  -1.182E-03
    0.125   2.144E-01   1.054E+00  -6.664E-02  -2.154E+00   1.295E-01  -1.608E+00   1.046E-01   4.273E-01  -1.303E-01  -1.153E-03
    0.100   4.797E-01   1.017E+00  -6.404E-02  -2.201E+00   1.270E-01  -2.007E+00   1.326E-01   3.371E-01  -1.266E-01  -1.047E-03
    0.079   6.906E-01   9.974E-01  -6.276E-02  -2.262E+00   1.246E-01  -2.487E+00   1.636E-01   2.139E-01  -1.207E-01  -8.469E-04
    0.063   9.109E-01   9.802E-01  -6.208E-02  -2.360E+00   1.263E-01  -2.972E+00   1.910E-01   1.069E-01  -1.173E-01  -5.786E-04
    0.050   1.105E+00   9.719E-01  -6.197E-02  -2.466E+00   1.276E-01  -3.390E+00   2.144E-01  -1.391E-01  -9.839E-02  -3.167E-04
    0.040   1.264E+00   9.680E-01  -6.232E-02  -2.581E+00   1.317E-01  -3.644E+00   2.276E-01  -3.506E-01  -8.126E-02  -1.225E-04
    0.031   1.436E+00   9.592E-01  -6.276E-02  -2.714E+00   1.400E-01  -3.728E+00   2.343E-01  -5.430E-01  -6.448E-02  -3.230E-05
    0.025   1.522E+00   9.597E-01  -6.351E-02  -2.813E+00   1.458E-01  -3.654E+00   2.362E-01  -6.544E-01  -5.500E-02  -4.848E-05
    pga     9.069E-01   9.830E-01  -6.595E-02  -2.698E+00   1.594E-01  -2.795E+00   2.120E-01  -3.011E-01  -6.532E-02  -4.484E-04
    pgv    -1.442E+00   9.909E-01  -5.848E-02  -2.701E+00   2.155E-01  -2.436E+00   2.659E-01   8.479E-02  -6.927E-02  -3.734E-04
    """)

    #: Coefficients for NEHRP BC boundary (Vs30 = 760 m/s), table 9, pag 2202
    #: coefficient values taken from Fortran implementation of Dave Boore
    #: (higher precision than in the paper)
    COEFFS_BC = CoeffsTable(sa_damping=5, table="""\
    IMT     c1          c2          c3          c4          c5          c6          c7          c8          c9         c10
    5.000  -4.852E+00   1.580E+00  -8.066E-02  -2.530E+00   2.216E-01  -1.426E+00   1.361E-01   6.340E-01  -1.413E-01  -1.608E-04
    4.000  -5.256E+00   1.787E+00  -9.785E-02  -2.435E+00   2.068E-01  -1.307E+00   1.210E-01   7.340E-01  -1.560E-01  -1.959E-04
    3.125  -5.590E+00   1.972E+00  -1.136E-01  -2.331E+00   1.908E-01  -1.204E+00   1.099E-01   8.449E-01  -1.723E-01  -2.452E-04
    2.500  -5.800E+00   2.126E+00  -1.278E-01  -2.257E+00   1.790E-01  -1.123E+00   9.539E-02   8.911E-01  -1.797E-01  -2.601E-04
    2.000  -5.853E+00   2.233E+00  -1.385E-01  -2.195E+00   1.688E-01  -1.037E+00   8.002E-02   8.666E-01  -1.790E-01  -2.860E-04
    1.587  -5.754E+00   2.287E+00  -1.450E-01  -2.131E+00   1.582E-01  -9.568E-01   6.762E-02   8.670E-01  -1.789E-01  -3.429E-04
    1.250  -5.489E+00   2.289E+00  -1.476E-01  -2.081E+00   1.501E-01  -9.000E-01   5.794E-02   8.208E-01  -1.719E-01  -4.070E-04
    1.000  -5.058E+00   2.233E+00  -1.454E-01  -2.030E+00   1.408E-01  -8.744E-01   5.412E-02   7.922E-01  -1.697E-01  -4.886E-04
    0.794  -4.446E+00   2.119E+00  -1.387E-01  -2.009E+00   1.356E-01  -8.576E-01   4.976E-02   7.084E-01  -1.589E-01  -5.751E-04
    0.629  -3.748E+00   1.973E+00  -1.294E-01  -1.997E+00   1.313E-01  -8.417E-01   4.820E-02   6.772E-01  -1.557E-01  -6.763E-04
    0.500  -3.007E+00   1.803E+00  -1.178E-01  -1.982E+00   1.274E-01  -8.466E-01   4.698E-02   6.670E-01  -1.546E-01  -7.676E-04
    0.397  -2.281E+00   1.629E+00  -1.054E-01  -1.967E+00   1.227E-01  -8.880E-01   5.033E-02   6.839E-01  -1.582E-01  -8.587E-04
    0.315  -1.560E+00   1.455E+00  -9.312E-02  -1.977E+00   1.209E-01  -9.466E-01   5.576E-02   6.499E-01  -1.558E-01  -9.552E-04
    0.251  -8.756E-01   1.293E+00  -8.193E-02  -2.014E+00   1.226E-01  -1.027E+00   6.341E-02   5.808E-01  -1.491E-01  -1.053E-03
    0.199  -3.056E-01   1.156E+00  -7.211E-02  -2.038E+00   1.220E-01  -1.147E+00   7.375E-02   5.082E-01  -1.430E-01  -1.140E-03
    0.158   1.194E-01   1.057E+00  -6.473E-02  -2.054E+00   1.190E-01  -1.355E+00   9.160E-02   5.164E-01  -1.503E-01  -1.178E-03
    0.125   5.356E-01   9.647E-01  -5.835E-02  -2.110E+00   1.205E-01  -1.672E+00   1.156E-01   3.433E-01  -1.322E-01  -1.130E-03
    0.100   7.818E-01   9.235E-01  -5.555E-02  -2.165E+00   1.191E-01  -2.097E+00   1.483E-01   2.847E-01  -1.319E-01  -9.897E-04
    0.079   9.667E-01   9.033E-01  -5.476E-02  -2.249E+00   1.215E-01  -2.530E+00   1.775E-01   1.001E-01  -1.147E-01  -7.724E-04
    0.063   1.109E+00   8.875E-01  -5.386E-02  -2.334E+00   1.229E-01  -2.881E+00   2.007E-01  -3.189E-02  -1.069E-01  -5.483E-04
    0.050   1.209E+00   8.830E-01  -5.441E-02  -2.440E+00   1.295E-01  -3.035E+00   2.133E-01  -2.098E-01  -8.997E-02  -4.145E-04
    0.040   1.261E+00   8.789E-01  -5.515E-02  -2.536E+00   1.388E-01  -2.994E+00   2.158E-01  -3.908E-01  -6.746E-02  -3.881E-04
    0.031   1.191E+00   8.884E-01  -5.642E-02  -2.577E+00   1.451E-01  -2.840E+00   2.121E-01  -4.370E-01  -5.866E-02  -4.329E-04
    0.025   1.052E+00   9.030E-01  -5.768E-02  -2.571E+00   1.483E-01  -2.652E+00   2.065E-01  -4.084E-01  -5.769E-02  -5.122E-04
    pga     5.233E-01   9.686E-01  -6.196E-02  -2.439E+00   1.465E-01  -2.335E+00   1.912E-01  -8.695E-02  -8.285E-02  -6.304E-04
    pgv    -1.662E+00   1.050E+00  -6.035E-02  -2.496E+00   1.840E-01  -2.301E+00   2.500E-01   1.268E-01  -8.704E-02  -4.266E-04
    """)

    COEFFS_STRESS = CoeffsTable(sa_damping=5, table="""\
    IMT    delta  M1    Mh
    pga    0.15   0.50  5.50
    0.025  0.15   0.00  5.00
    0.031  0.15   0.00  5.00
    0.04   0.15   0.00  5.00
    0.05   0.15   0.00  5.00
    0.063  0.15   0.17  5.17
    0.079  0.15   0.34  5.34
    0.1    0.15   0.50  5.50
    0.126  0.15   1.15  5.67
    0.158  0.15   1.85  5.84
    0.199  0.15   2.50  6.00
    0.251  0.15   2.90  6.12
    0.315  0.15   3.30  6.25
    0.397  0.15   3.65  6.37
    0.5    0.15   4.00  6.50
    0.629  0.15   4.17  6.70
    0.794  0.15   4.34  6.95
    1.00   0.15   4.50  7.20
    1.25   0.15   4.67  7.45
    1.587  0.15   4.84  7.70
    2.0    0.15   5.00  8.00
    2.5    0.15   5.25  8.12
    3.125  0.15   5.50  8.25
    4.0    0.15   5.75  8.37
    5.0    0.15   6.00  8.50
    pgv    0.11   2.00  5.50
    """)

    #: Table 3, pag. 110. + coefficient values for additional frequencies
    #: extracted from Fortran code implementing soil response function
    #: developed by the original author (ab06_fmrvs_evaluate_gmpes.for
    #: available at http://www.daveboore.com/pubs_online.html - see code
    #: available for Atkinson, G. M. and D. M. Boore (2006). Earthquake ground
    #: -motion prediction equations for eastern North America)
    COEFFS_SOIL_RESPONSE = CoeffsTable(sa_damping=5, table="""\
    IMT     blin    b1      b2
    pgv    -0.60   -0.50   -0.06
    pga    -0.36   -0.64   -0.14
    0.010  -0.36   -0.64   -0.14
    0.020  -0.34   -0.63   -0.12
    0.030  -0.33   -0.62   -0.11
    0.040  -0.31   -0.61   -0.11
    0.050  -0.29   -0.64   -0.11
    0.060  -0.25   -0.64   -0.11
    0.075  -0.23   -0.64   -0.11
    0.090  -0.23   -0.64   -0.12
    0.100  -0.25   -0.60   -0.13
    0.120  -0.26   -0.56   -0.14
    0.150  -0.28   -0.53   -0.18
    0.170  -0.29   -0.53   -0.19
    0.200  -0.31   -0.52   -0.19
    0.240  -0.38   -0.52   -0.16
    0.250  -0.39   -0.52   -0.16
    0.300  -0.44   -0.52   -0.14
    0.360  -0.48   -0.51   -0.11
    0.400  -0.50   -0.51   -0.10
    0.460  -0.55   -0.50   -0.08
    0.500  -0.60   -0.50   -0.06
    0.600  -0.66   -0.49   -0.03
    0.750  -0.69   -0.47   -0.00
    0.850  -0.69   -0.46   -0.00
    1.000  -0.70   -0.44   -0.00
    1.500  -0.72   -0.40   -0.00
    2.000  -0.73   -0.38   -0.00
    3.000  -0.74   -0.34   -0.00
    4.000  -0.75   -0.31   -0.00
    5.000  -0.75   -0.291  -0.00
    7.500  -0.692  -0.247  -0.00
    10.00  -0.650  -0.215  -0.00
    """)


add_alias("AtkinsonBoore2006MblgAB1987bar140NSHMP2008",
          AtkinsonBoore2006, mag_eq="Mblg87", scale_fac=0.)
add_alias("AtkinsonBoore2006MblgJ1996bar140NSHMP2008",
          AtkinsonBoore2006, mag_eq="Mblg96", scale_fac=0.)
add_alias("AtkinsonBoore2006Mwbar140NSHMP2008", AtkinsonBoore2006,
          mag_eq="Mw", scale_fac=0.)
add_alias("AtkinsonBoore2006MblgAB1987bar200NSHMP2008",
          AtkinsonBoore2006, mag_eq="Mblg87", scale_fac=0.5146)
add_alias("AtkinsonBoore2006MblgJ1996bar200NSHMP2008",
          AtkinsonBoore2006, mag_eq="Mblg96", scale_fac=0.5146)
add_alias("AtkinsonBoore2006Mwbar200NSHMP2008",
          AtkinsonBoore2006, mag_eq="Mw", scale_fac=0.5146)


class AtkinsonBoore2006Modified2011(AtkinsonBoore2006):
    """
    This GMPE modifies the original implementation of :class:
    `AtkinsonBoore2006` with the magnitude dependent stress-drop scaling
    factor proposed in Atkinson & Boore (2011)
    Atkinson, G. A. and Boore D. M. (2011) Modifications to Existing
    Ground-Motion Prediciton Equations in Light of New Data. Bulletin of the
    Seismological Society of America, 101(3), 1121 - 1135
    """


class AtkinsonBoore2006SGS(AtkinsonBoore2006):
    """
    This class extends the original base class
    :class:`openquake.hazardlib.gsim.atkinson_boore_2006.AtkinsonBoore2006`
    by introducing a distance filter for the near field, as implemented
    by SGS for the national PSHA model for Saudi Arabia.
    """
    CUTOFF_RRUP = 5.
