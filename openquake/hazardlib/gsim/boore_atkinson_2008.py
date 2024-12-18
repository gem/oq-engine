# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim.atkinson_boore_2006 import (
    AtkinsonBoore2006, _get_pga_on_rock, _get_site_amplification_linear,
    _get_site_amplification_non_linear, _compute_magnitude_scaling,
    _compute_distance_scaling, set_sig)
from openquake.hazardlib import const, contexts
from openquake.hazardlib.imt import PGA, PGV, SA

PGA_SA0 = (PGA(), SA(0))

def hawaii_adjust(mean, ctx, imt):
    # Defining frequency
    if imt == PGV():
        freq = 2.0
    elif imt.period == 0:
        freq = 50.0
    else:
        freq = 1. / imt.period

    # Equation 3 of Atkinson (2010)
    x1 = np.min([-0.18 + 0.17 * np.log10(freq), 0])

    # Equation 4 a-b-c of Atkinson (2010)
    x0 = np.full_like(ctx.hypo_depth, 0.2)
    x0[ctx.hypo_depth < 20.0] = np.max([0.217 - 0.321 * np.log10(freq), 0])
    x0[ctx.hypo_depth > 35.0] = np.min([0.263 + 0.0924 * np.log10(freq), 0.35])

    # Limiting calculation distance to 1km
    # (as suggested by C. Bruce Worden)
    rjb = [d if d > 1 else 1 for d in ctx.rjb]

    # Equation 2 and 5 of Atkinson (2010)
    mean += (x0 + x1 * np.log10(rjb)) / np.log10(np.e)


class BooreAtkinson2008(GMPE):
    """
    Implements GMPE developed by David M. Boore and Gail M. Atkinson
    and published as "Ground-Motion Prediction Equations for the
    Average Horizontal Component of PGA, PGV, and 5%-Damped PSA
    at Spectral Periods between 0.01 and 10.0 s" (2008, Earthquake Spectra,
    Volume 24, No. 1, pages 99-138).
    """
    #: Supported tectonic region type is active shallow crust, see
    #: paragraph 'Introduction', page 99.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration, see table 3
    #: pag. 110
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.GMRotI50`, see paragraph
    #: 'Response Variables', page 100 and table 8, pag 121.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotI50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see equation 2, pag 106.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters is Vs30.
    #: See paragraph 'Predictor Variables', pag 103
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, and rake.
    #: See paragraph 'Predictor Variables', pag 103
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is Rjb.
    #: See paragraph 'Predictor Variables', pag 103
    REQUIRES_DISTANCES = {'rjb'}

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    kind = 'base'
    sgn = 0

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # horrible hack to fix the distance parameters; needed for the can15
        # subclasses; extra distances are add in can15.eastern
        # this also affects generic_gmpe_avgsa_test.py
        vars(ctx).update(contexts.get_dists(ctx))

        # compute PGA on rock conditions - needed to compute non-linear
        # site amplification term
        pga4nl = _get_pga_on_rock(self.COEFFS[PGA()], ctx)
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            C_SR = self.COEFFS_SOIL_RESPONSE[imt]

            # equation 1, pag 106, without sigma term, that is only the first 3
            # terms. The third term (site amplification) is computed as given
            # in equation (6), that is the sum of a linear term - equation (7)
            # - and a non-linear one - equations (8a) to (8c).
            # Mref, Rref values are given in the caption to table 6, pag 119.
            if imt in PGA_SA0:
                # avoid recomputing PGA on rock, just add site terms
                mean[m] = np.log(pga4nl) + \
                    _get_site_amplification_linear(ctx.vs30, C_SR) + \
                    _get_site_amplification_non_linear(ctx.vs30, pga4nl, C_SR)
            else:
                mean[m] = _compute_magnitude_scaling(ctx, C) + \
                    _compute_distance_scaling(ctx, C) + \
                    _get_site_amplification_linear(ctx.vs30, C_SR) + \
                    _get_site_amplification_non_linear(ctx.vs30, pga4nl, C_SR)

            if self.kind in ('2011', 'prime'):
                # correction factor (see Atkinson and Boore, 2011; equation 5
                # at page 1126 and nga08_gm_tmr.for line 508
                corr_fact = 10.0**(np.clip(3.888 - 0.674 * ctx.mag, 0, None) -
                                   (np.clip(2.933 - 0.510 * ctx.mag, 0, None) *
                                    np.log10(ctx.rjb + 10.)))
                mean[m] = np.log(np.exp(mean[m]) * corr_fact)

            if self.kind == 'hawaii':
                hawaii_adjust(mean[m], ctx, imt)
            elif self.kind == 'prime':
                # Implements the Boore & Atkinson (2011) adjustment to the
                # Atkinson (2008) GMPE
                A08 = self.COEFFS_A08[imt]
                f_ena = 10.0 ** (A08["c"] + A08["d"] * ctx.rjb)
                mean[m] = np.log(np.exp(mean[m]) * f_ena)

            set_sig(self.kind, C, sig[m], tau[m], phi[m])

    #: Coefficient table is constructed from values in tables 6, 7 and 8
    #: (pages 119, 120, 121). Spectral acceleration is defined for damping
    #: of 5%, see 'Response Variables' page 100.
    #: c1, c2, c3, h are the period-dependent distance scaling coefficients.
    #: e1, e2, e3, e4, e5, e6, e7, Mh are the period-dependent magnitude-
    # scaling coefficients.
    #: sigma, tau, std are the intra-event uncertainty, inter-event
    #: uncertainty, and total standard deviation, respectively.
    #: Note that only the inter-event and total standard deviation for
    #: 'specified' fault type are considered (because rake angle is always
    #: specified)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT     c1       c2       c3      h     e1       e2       e3       e4      e5       e6      e7      Mh   sigma tau   std
    pgv    -0.87370  0.10060 -0.00334 2.54  5.00121  5.04727  4.63188  5.08210 0.18322 -0.12736 0.00000 8.50 0.500 0.256 0.560
    pga    -0.66050  0.11970 -0.01151 1.35 -0.53804 -0.50350 -0.75472 -0.50970 0.28805 -0.10164 0.00000 6.75 0.502 0.260 0.564
    0.010  -0.66220  0.12000 -0.01151 1.35 -0.52883 -0.49429 -0.74551 -0.49966 0.28897 -0.10019 0.00000 6.75 0.502 0.262 0.566
    0.020  -0.66600  0.12280 -0.01151 1.35 -0.52192 -0.48508 -0.73906 -0.48895 0.25144 -0.11006 0.00000 6.75 0.502 0.262 0.566
    0.030  -0.69010  0.12830 -0.01151 1.35 -0.45285 -0.41831 -0.66722 -0.42229 0.17976 -0.12858 0.00000 6.75 0.507 0.274 0.576
    0.050  -0.71700  0.13170 -0.01151 1.35 -0.28476 -0.25022 -0.48462 -0.26092 0.06369 -0.15752 0.00000 6.75 0.516 0.286 0.589
    0.075  -0.72050  0.12370 -0.01151 1.55  0.00767  0.04912 -0.20578  0.02706 0.01170 -0.17051 0.00000 6.75 0.513 0.320 0.606
    0.10   -0.70810  0.11170 -0.01151 1.68  0.20109  0.23102  0.03058  0.22193 0.04697 -0.15948 0.00000 6.75 0.520 0.318 0.608
    0.15   -0.69610  0.09884 -0.01113 1.86  0.46128  0.48661  0.30185  0.49328 0.17990 -0.14539 0.00000 6.75 0.518 0.290 0.594
    0.20   -0.58300  0.04273 -0.00952 1.98  0.57180  0.59253  0.40860  0.61472 0.52729 -0.12964 0.00102 6.75 0.523 0.288 0.596
    0.25   -0.57260  0.02977 -0.00837 2.07  0.51884  0.53496  0.33880  0.57747 0.60880 -0.13843 0.08607 6.75 0.527 0.267 0.592
    0.30   -0.55430  0.01955 -0.00750 2.14  0.43825  0.44516  0.25356  0.51990 0.64472 -0.15694 0.10601 6.75 0.546 0.269 0.608
    0.40   -0.64430  0.04394 -0.00626 2.24  0.39220  0.40602  0.21398  0.46080 0.78610 -0.07843 0.02262 6.75 0.541 0.267 0.603
    0.50   -0.69140  0.06080 -0.00540 2.32  0.18957  0.19878  0.00967  0.26337 0.76837 -0.09054 0.00000 6.75 0.555 0.265 0.615
    0.75   -0.74080  0.07518 -0.00409 2.46 -0.21338 -0.19496 -0.49176 -0.10813 0.75179 -0.14053 0.10302 6.75 0.571 0.299 0.645
    1.0    -0.81830  0.10270 -0.00334 2.54 -0.46896 -0.43443 -0.78465 -0.39330 0.67880 -0.18257 0.05393 6.75 0.573 0.302 0.647
    1.5    -0.83030  0.09793 -0.00255 2.66 -0.86271 -0.79593 -1.20902 -0.88085 0.70689 -0.25950 0.19082 6.75 0.566 0.373 0.679
    2.0    -0.82850  0.09432 -0.00217 2.73 -1.22652 -1.15514 -1.57697 -1.27669 0.77989 -0.29657 0.29888 6.75 0.580 0.389 0.700
    3.0    -0.78440  0.07282 -0.00191 2.83 -1.82979 -1.74690 -2.22584 -1.91814 0.77966 -0.45384 0.67466 6.75 0.566 0.401 0.695
    4.0    -0.68540  0.03758 -0.00191 2.89 -2.24656 -2.15906 -2.58228 -2.38168 1.24961 -0.35874 0.79508 6.75 0.583 0.385 0.698
    5.0    -0.50960 -0.02391 -0.00191 2.93 -1.28408 -1.21270 -1.50904 -1.41093 0.14271 -0.39006 0.00000 8.50 0.601 0.437 0.744
    7.5    -0.37240 -0.06568 -0.00191 3.00 -1.43145 -1.31632 -1.81022 -1.59217 0.52407 -0.37578 0.00000 8.50 0.626 0.477 0.787
    10.0   -0.09824 -0.13800 -0.00191 3.04 -2.15446 -2.16137 -2.53323 -2.14635 0.40387 -0.48492 0.00000 8.50 0.645 0.477 0.801
    """)

    COEFFS_SOIL_RESPONSE = AtkinsonBoore2006.COEFFS_SOIL_RESPONSE

    COEFFS_A08 = CoeffsTable(sa_damping=5, table="""\
    IMT         c         d
    pgv     0.450   0.00211
    pga     0.419   0.00039
    0.005   0.417   0.00192
    0.050   0.417   0.00192
    0.100   0.245   0.00273
    0.200   0.042   0.00232
    0.300  -0.078   0.00190
    0.500  -0.180   0.00180
    1.000  -0.248   0.00153
    2.000  -0.214   0.00117
    3.030  -0.084   0.00091
    5.000   0.000   0.00000
    10.00   0.000   0.00000
    """)


class Atkinson2010Hawaii(BooreAtkinson2008):
    """
    Modification of the original base class adjusted for application
    to the Hawaii region as described in:
    Atkinson, G. M. (2010) 'Ground-Motion Prediction Equations for Hawaii
    from a Referenced Empirical Approach", Bulletin of the Seismological
    Society of America, Vol. 100, No. 2, pp. 751–761
    """
    kind = 'hawaii'

    #: Supported tectonic region type is active volcanic, see
    #: paragraph 'Introduction', page 99.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure component is geometric mean, see paragraph
    #: 'Response Variables', page 100 and table 8, pag 121.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types is total
    #: see equation 2, pag 106.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    # Adding hypocentral depth as required rupture parameter
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'hypo_depth'}
