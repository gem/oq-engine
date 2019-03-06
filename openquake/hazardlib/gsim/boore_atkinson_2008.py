# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
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
Module exports :class:`BooreAtkinson2008`.
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


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
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.GMRotI50`, see paragraph
    #: 'Response Variables', page 100 and table 8, pag 121.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotI50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see equation 2, pag 106.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters is Vs30.
    #: See paragraph 'Predictor Variables', pag 103
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude, and rake.
    #: See paragraph 'Predictor Variables', pag 103
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake'))

    #: Required distance measure is Rjb.
    #: See paragraph 'Predictor Variables', pag 103
    REQUIRES_DISTANCES = set(('rjb', ))

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        C_SR = self.COEFFS_SOIL_RESPONSE[imt]

        # compute PGA on rock conditions - needed to compute non-linear
        # site amplification term
        pga4nl = self._get_pga_on_rock(rup, dists, C)

        # equation 1, pag 106, without sigma term, that is only the first 3
        # terms. The third term (site amplification) is computed as given in
        # equation (6), that is the sum of a linear term - equation (7) - and
        # a non-linear one - equations (8a) to (8c).
        # Mref, Rref values are given in the caption to table 6, pag 119.
        if imt == PGA():
            # avoid recomputing PGA on rock, just add site terms
            mean = np.log(pga4nl) + \
                self._get_site_amplification_linear(sites.vs30, C_SR) + \
                self._get_site_amplification_non_linear(sites.vs30, pga4nl,
                                                        C_SR)
        else:
            mean = self._compute_magnitude_scaling(rup, C) + \
                self._compute_distance_scaling(rup, dists, C) + \
                self._get_site_amplification_linear(sites.vs30, C_SR) + \
                self._get_site_amplification_non_linear(sites.vs30, pga4nl,
                                                        C_SR)

        stddevs = self._get_stddevs(C, stddev_types, num_sites=len(sites.vs30))

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations as defined in table 8, pag 121.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(C['std'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C['sigma'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(num_sites))
        return stddevs

    def _compute_distance_scaling(self, rup, dists, C):
        """
        Compute distance-scaling term, equations (3) and (4), pag 107.
        """
        Mref = 4.5
        Rref = 1.0
        R = np.sqrt(dists.rjb ** 2 + C['h'] ** 2)
        return (C['c1'] + C['c2'] * (rup.mag - Mref)) * np.log(R / Rref) + \
            C['c3'] * (R - Rref)

    def _compute_magnitude_scaling(self, rup, C):
        """
        Compute magnitude-scaling term, equations (5a) and (5b), pag 107.
        """
        U, SS, NS, RS = self._get_fault_type_dummy_variables(rup)
        if rup.mag <= C['Mh']:
            return C['e1'] * U + C['e2'] * SS + C['e3'] * NS + C['e4'] * RS + \
                C['e5'] * (rup.mag - C['Mh']) + \
                C['e6'] * (rup.mag - C['Mh']) ** 2
        else:
            return C['e1'] * U + C['e2'] * SS + C['e3'] * NS + C['e4'] * RS + \
                C['e7'] * (rup.mag - C['Mh'])

    def _get_fault_type_dummy_variables(self, rup):
        """
        Get fault type dummy variables, see Table 2, pag 107.
        Fault type (Strike-slip, Normal, Thrust/reverse) is
        derived from rake angle.
        Rakes angles within 30 of horizontal are strike-slip,
        angles from 30 to 150 are reverse, and angles from
        -30 to -150 are normal. See paragraph 'Predictor Variables'
        pag 103.
        Note that the 'Unspecified' case is not considered,
        because rake is always given.
        """
        U, SS, NS, RS = 0, 0, 0, 0
        if rup.rake == 'undefined':
            U = 1
        elif np.abs(rup.rake) <= 30.0 or (180.0 - np.abs(rup.rake)) <= 30.0:
            # strike-slip
            SS = 1
        elif rup.rake > 30.0 and rup.rake < 150.0:
            # reverse
            RS = 1
        else:
            # normal
            NS = 1

        return U, SS, NS, RS

    def _get_site_amplification_linear(self, vs30, C):
        """
        Compute site amplification linear term,
        equation (7), pag 107.
        """
        return C['blin'] * np.log(vs30 / 760.0)

    def _get_pga_on_rock(self, rup, dists, _C):
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
        C_pga = self.COEFFS[PGA()]
        pga4nl = np.exp(self._compute_magnitude_scaling(rup, C_pga) +
                        self._compute_distance_scaling(rup, dists, C_pga))

        return pga4nl

    def _get_site_amplification_non_linear(self, vs30, pga4nl, C):
        """
        Compute site amplification non-linear term,
        equations (8a) to (13d), pag 108-109.
        """
        # non linear slope
        bnl = self._compute_non_linear_slope(vs30, C)
        # compute the actual non-linear term
        return self._compute_non_linear_term(pga4nl, bnl)

    def _compute_non_linear_slope(self, vs30, C):
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
        idx = vs30 <= V1
        bnl[idx] = C['b1']

        # equation (13b)
        idx = np.where((vs30 > V1) & (vs30 <= V2))
        bnl[idx] = (C['b1'] - C['b2']) * \
                   np.log(vs30[idx] / V2) / np.log(V1 / V2) + C['b2']

        # equation (13c)
        idx = np.where((vs30 > V2) & (vs30 < Vref))
        bnl[idx] = C['b2'] * np.log(vs30[idx] / Vref) / np.log(V2 / Vref)
        return bnl

    def _compute_non_linear_term(self, pga4nl, bnl):
        """
        Compute non-linear term,
        equation (8a) to (8c), pag 108.
        """

        fnl = np.zeros(pga4nl.shape)
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


class Atkinson2010Hawaii(BooreAtkinson2008):
    """
    Modification of the original base class adjusted for application
    to the Hawaii region as described in:
    Atkinson, G. M. (2010) 'Ground-Motion Prediction Equations for Hawaii
    from a Referenced Empirical Approach", Bulletin of the Seismological
    Society of America, Vol. 100, No. 2, pp. 751–761
    """

    #: Supported tectonic region type is active volcanic, see
    #: paragraph 'Introduction', page 99.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure component is geometric mean, see paragraph
    #: 'Response Variables', page 100 and table 8, pag 121.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VECTORIAL

    #: Supported standard deviation types is total
    #: see equation 2, pag 106.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    # Adding hypocentral depth as required rupture parameter
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake', 'hypo_depth'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Using a frequency dependent correction for the mean ground motion.
        Standard deviation is fixed.
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists,
                                                     imt, stddev_types)
        # Defining frequency
        if imt == PGA():
            freq = 50.0
        elif imt == PGV():
            freq = 2.0
        else:
            freq = 1./imt.period

        # Equation 3 of Atkinson (2010)
        x1 = np.min([-0.18+0.17*np.log10(freq), 0])

        # Equation 4 a-b-c of Atkinson (2010)
        if rup.hypo_depth < 20.0:
            x0 = np.max([0.217-0.321*np.log10(freq), 0])
        elif rup.hypo_depth > 35.0:
            x0 = np.min([0.263+0.0924*np.log10(freq), 0.35])
        else:
            x0 = 0.2

        # Limiting calculation distance to 1km
        # (as suggested by C. Bruce Worden)
        rjb = [d if d > 1 else 1 for d in dists.rjb]

        # Equation 2 and 5 of Atkinson (2010)
        mean += (x0 + x1*np.log10(rjb))/np.log10(np.e)

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return total standard deviation.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        # Using a frequency independent value of sigma as recommended
        # in the caption of Table 2 of Atkinson (2010)
        stddevs = [0.26/np.log10(np.e) + np.zeros(num_sites)]

        return stddevs
