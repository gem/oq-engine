# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module exports :class:`AbrahamsonSilva2008`.
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class AbrahamsonSilva2014(GMPE):
    """
    Implements GMPE developed by Abrahamson, Silva and Kamal in 2014 as
    part of the PEER West 2 Project. The GMPE is described in a paper
    published in 2014 on Earthquake Spectra, Volume 30, Number 3.
    """
    #: Supported tectonic region type is active shallow crust, see paragraph
    #: 'Data Set Selection', see page 68.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration, peak
    #: ground velocity and peak ground acceleration, see tables 5a and 5b
    #: pages 84, 85, respectively.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: average horizontal :attr:`~openquake.hazardlib.const.IMC.GMRotI50`,
    #: see abstract, page 67.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see paragraph "Equations for standard deviations", page
    #: 1046.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters are Vs30 and Z1.0, see table 2, page 1031
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'z1pt0'))

    #: Required rupture parameters are magnitude, rake, dip, ztor, and width
    #: (see table 2, page 1031)
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake', 'dip', 'ztor', 'width'))

    #: Required distance measures are Rrup, Rjb, Ry0 and Rx (see Table 2,
    #: page 1031).
    REQUIRES_DISTANCES = set(('rrup', 'rjb', 'rx', 'ry0'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type and for PGA
        C = self.COEFFS[imt]

        # this is used to compute the PGA on reference bedrock
        C_PGA = self.COEFFS[PGA()]

        # compute median pga on rock (vs30=1180m/s), used for site response
        # term calculation
        pga1180 = np.exp(self._compute_imt1180(PGA(), sites, rup, dists))

        # get the mean value
        mean = (self._compute_basic_term(C, rup, dists) +
                self._compute_faulting_style_term(C, rup) +
                self._compute_site_response_term(C, imt, sites, pga1180) +
                self._compute_hanging_wall_term(C, dists, rup) +
                self._compute_top_of_rupture_depth_term(C, rup) +
                self._compute_large_distance_term(C, dists, rup) +
                self._compute_soil_depth_term(C, imt, sites.z1pt0, sites.vs30))

        # get standard deviation
        stddevs = self._get_stddevs(C, C_PGA, pga1180, rup, sites,
                                    stddev_types)

        return mean, stddevs

    def _compute_basic_term(self, C, rup, dists):
        """
        Compute and return basic form, see page 1030.
        """
        # Fictitious depth calculation
        if rup.mag > 5.:
            c4m = C['c4']
        elif rup.mag > 4.:
            c4m = C['c4'] - (C['c4']-1.) * (5. - rup.mag)
        else:
            c4m = 1.
        R = np.sqrt(dists.rrup ** 2 + c4m ** 2)
        # basic form
        base_term = (C['a1'] + C['a8'] * (8.5 - rup.mag) +
                     C['a17'] * dists.rrup +
                     (C['a2'] + C['a3'] * (rup.mag - C['m1'])) * np.log(R))
        # note that equation 2 at page 1030 do not specify the case for
        # m == M1
        if rup.mag > C['m1']:
            base_term += C['a5'] * (rup.mag - C['m1'])
        elif rup.mag >= self.CONSTS['m2']:
            base_term += C['a4'] * (rup.mag - C['m1'])
        else:
            base_term += (C['a4'] * (self.CONSTS['m2'] - C['m1']) +
                          C['a6'] * (rup.mag - self.CONSTS['m2']) +
                          C['a7'] * (rup.mag - self.CONSTS['m2'])**2.)
        return base_term

    def _compute_faulting_style_term(self, C, rup):
        """
        Compute and return faulting style term, that is the sum of the second
        and third terms in equation 1, page 74.
        """
        # this implements equations 5 and 6 at page 1032. f7 is the 
        # coefficient for reverse mechanisms while f8 is the the correction
        # factor for normal ruptures
        if rup.mag > 5.0:
            f7 = C['a11']
            f8 = C['a12']
        elif rup.mag >= 4:
            f7 = C['a11'] * (rup.mag - 4)
            f8 = C['a12'] * (rup.mag - 4)
        else:
            f7 = 0.0
            f8 = 0.0
        # ranges of rake values for each faulting mechanism are specified in
        # table 2, page 1031
        return (f7 * float(rup.rake > 30 and rup.rake < 150) +
                f8 * float(rup.rake > -150 and rup.rake < -30))

    def _compute_site_response_term(self, C, imt, sites, pga1100):
        """
        Compute and return site response model term, that is the fifth term
        in equation 1, page 74.
        """
        site_resp_term = np.zeros_like(sites.vs30)

        vs30_star, _ = self._compute_vs30_star_factor(imt, sites.vs30)
        vlin, c, n = C['VLIN'], self.CONSTS['c'], self.CONSTS['n']
        a10, b = C['a10'], C['b']

        idx = sites.vs30 < vlin
        arg = vs30_star[idx] / vlin
        site_resp_term[idx] = (a10 * np.log(arg) -
                               b * np.log(pga1100[idx] + c) +
                               b * np.log(pga1100[idx] + c * (arg ** n)))

        idx = sites.vs30 >= vlin
        site_resp_term[idx] = (a10 + b * n) * np.log(vs30_star[idx] / vlin)

        return site_resp_term

    def _compute_hanging_wall_term(self, C, dists, rup):
        """
        Compute and return hanging wall model term, that is the sixth term in
        equation 1, page 74. The calculation of this term is explained in
        paragraph 'Hanging-Wall Model', page 77.
        """
        if rup.dip == 90.0:
            return np.zeros_like(dists.rx)
        else:
            idx = dists.rx > 0
            Fhw = np.zeros_like(dists.rx)
            Fhw[idx] = 1

            # equation 8, page 77
            T1 = np.zeros_like(dists.rx)
            idx1 = (dists.rjb < 30.0) & (idx)
            T1[idx1] = 1.0 - dists.rjb[idx1] / 30.0

            # equation 9, page 77
            T2 = np.ones_like(dists.rx)
            idx2 = ((dists.rx <= rup.width * np.cos(np.radians(rup.dip))) &
                    (idx))
            T2[idx2] = (0.5 + dists.rx[idx2] /
                        (2 * rup.width * np.cos(np.radians(rup.dip))))

            # equation 10, page 78
            T3 = np.ones_like(dists.rx)
            idx3 = (dists.rx < rup.ztor) & (idx)
            T3[idx3] = dists.rx[idx3] / rup.ztor

            # equation 11, page 78
            if rup.mag <= 6.0:
                T4 = 0.0
            elif rup.mag > 6 and rup.mag < 7:
                T4 = rup.mag - 6
            else:
                T4 = 1.0

            # equation 5, in AS08_NGA_errata.pdf
            if rup.dip >= 30:
                T5 = 1.0 - (rup.dip - 30.0) / 60.0
            else:
                T5 = 1.0

            return Fhw * C['a14'] * T1 * T2 * T3 * T4 * T5

    def _compute_top_of_rupture_depth_term(self, C, rup):
        """
        Compute and return top of rupture depth term, that is the seventh term
        in equation 1, page 74. The calculation of this term is explained in
        paragraph 'Depth-to-Top of Rupture Model', page 78.
        """
        if rup.ztor >= 10.0:
            return C['a16']
        else:
            return C['a16'] * rup.ztor / 10.0

    def _compute_large_distance_term(self, C, dists, rup):
        """
        Compute and return large distance model term, that is the 8-th term
        in equation 1, page 74. The calculation of this term is explained in
        paragraph 'Large Distance Model', page 78.
        """
        # equation 15, page 79
        if rup.mag < 5.5:
            T6 = 1.0
        elif rup.mag >= 5.5 and rup.mag <= 6.5:
            T6 = 0.5 * (6.5 - rup.mag) + 0.5
        else:
            T6 = 0.5

        # equation 14, page 79
        large_distance_term = np.zeros_like(dists.rrup)
        idx = dists.rrup >= 100.0
        large_distance_term[idx] = C['a18'] * (dists.rrup[idx] - 100.0) * T6

        return large_distance_term

    def _compute_soil_depth_term(self, C, imt, z1pt0, vs30):
        """
        Compute and return soil depth model term, that is the 9-th term in
        equation 1, page 74. The calculation of this term is explained in
        paragraph 'Soil Depth Model', page 79.
        """
        a21 = self._compute_a21_factor(C, imt, z1pt0, vs30)
        a22 = self._compute_a22_factor(imt)
        median_z1pt0 = self._compute_median_z1pt0(vs30)

        soil_depth_term = a21 * np.log((z1pt0 + self.CONSTS['c2']) /
                                       (median_z1pt0 + self.CONSTS['c2']))

        idx = z1pt0 >= 200
        soil_depth_term[idx] += a22 * np.log(z1pt0[idx] / 200)

        return soil_depth_term

    def _compute_imt1100(self, imt, sites, rup, dists):
        """
        Compute and return mean imt value for rock conditions
        (vs30 = 1100 m/s)
        """
        vs30_1100 = np.zeros_like(sites.vs30) + 1100
        vs30_star, _ = self._compute_vs30_star_factor(imt, vs30_1100)
        C = self.COEFFS[imt]
        mean = (self._compute_base_term(C, rup, dists) +
                self._compute_faulting_style_term(C, rup) +
                self._compute_hanging_wall_term(C, dists, rup) +
                self._compute_top_of_rupture_depth_term(C, rup) +
                self._compute_large_distance_term(C, dists, rup) +
                self._compute_soil_depth_term(C, imt, sites.z1pt0, vs30_1100) +
                # this is the site response term in case of vs30=1100
                ((C['a10'] + C['b'] * self.CONSTS['n']) *
                np.log(vs30_star / C['VLIN'])))

        return mean

    def _get_stddevs(self, C, C_PGA, pga1100, rup, sites, stddev_types):
        """
        Return standard deviations as described in paragraph 'Equations for
        standard deviation', page 81.
        """
        std_intra = self._compute_intra_event_std(C, C_PGA, pga1100, rup.mag,
                                                  sites.vs30,
                                                  sites.vs30measured)
        std_inter = self._compute_inter_event_std(C, C_PGA, pga1100, rup.mag,
                                                  sites.vs30)
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(std_intra ** 2 + std_inter ** 2))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(std_intra)
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(std_inter)
        return stddevs

    def _compute_intra_event_std(self, C, C_PGA, pga1100, mag, vs30,
                                 vs30measured):
        """
        Compute intra event standard deviation (equation 24) as described
        in the errata and not in the original paper.
        """
        sigma_b = self._compute_sigma_b(C, mag, vs30measured)
        sigma_b_pga = self._compute_sigma_b(C_PGA, mag, vs30measured)
        delta_amp = self._compute_partial_derivative_site_amp(C, pga1100, vs30)

        std_intra = np.sqrt(sigma_b ** 2 + self.CONSTS['sigma_amp'] ** 2 +
                            (delta_amp ** 2) * (sigma_b_pga ** 2) +
                            2 * delta_amp * sigma_b * sigma_b_pga * C['rho'])

        return std_intra

    def _compute_inter_event_std(self, C, C_PGA, pga1100, mag, vs30):
        """
        Compute inter event standard deviation, equation 25, page 82.
        """
        tau_0 = self._compute_std_0(C['s3'], C['s4'], mag)
        tau_b_pga = self._compute_std_0(C_PGA['s3'], C_PGA['s4'], mag)
        delta_amp = self._compute_partial_derivative_site_amp(C, pga1100, vs30)

        std_inter = np.sqrt(tau_0 ** 2 + (delta_amp ** 2) * (tau_b_pga ** 2) +
                            2 * delta_amp * tau_0 * tau_b_pga * C['rho'])

        return std_inter

    def _compute_sigma_b(self, C, mag, vs30measured):
        """
        Equation 23, page 81.
        """
        sigma_0 = self._compute_sigma_0(C, mag, vs30measured)
        sigma_amp = self.CONSTS['sigma_amp']

        return np.sqrt(sigma_0 ** 2 - sigma_amp ** 2)

    def _compute_sigma_0(self, C, mag, vs30measured):
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

        return self._compute_std_0(s1, s2, mag)

    def _compute_std_0(self, c1, c2, mag):
        """
        Common part of equations 27 and 28, pag 82.
        """
        if mag < 5:
            return c1
        elif mag >= 5 and mag <= 7:
            return c1 + (c2 - c1) * (mag - 5) / 2
        else:
            return c2

    def _compute_partial_derivative_site_amp(self, C, pga1100, vs30):
        """
        Partial derivative of site amplification term with respect to
        PGA on rock (equation 26), as described in the errata and not
        in the original paper.
        """
        delta_amp = np.zeros_like(vs30)
        vlin = C['VLIN']
        c = self.CONSTS['c']
        b = C['b']
        n = self.CONSTS['n']

        idx = vs30 < vlin
        delta_amp[idx] = (- b * pga1100[idx] / (pga1100[idx] + c) +
                          b * pga1100[idx] / (pga1100[idx] + c *
                          ((vs30[idx] / vlin) ** n)))

        return delta_amp

    def _compute_a21_factor(self, C, imt, z1pt0, vs30):
        """
        Compute and return a21 factor, equation 18, page 80.
        """
        e2 = self._compute_e2_factor(imt, vs30)
        a21 = e2.copy()

        vs30_star, v1 = self._compute_vs30_star_factor(imt, vs30)
        median_z1pt0 = self._compute_median_z1pt0(vs30)

        numerator = ((C['a10'] + C['b'] * self.CONSTS['n']) *
                     np.log(vs30_star / np.min([v1, 1000])))
        denominator = np.log((z1pt0 + self.CONSTS['c2']) /
                             (median_z1pt0 + self.CONSTS['c2']))

        idx = numerator + e2 * denominator < 0
        a21[idx] = - numerator[idx] / denominator[idx]

        idx = vs30 >= 1000
        a21[idx] = 0.0

        return a21

    def _compute_vs30_star_factor(self, imt, vs30):
        """
        Compute and return vs30 star factor, equation 5, page 77.
        """
        v1 = self._compute_v1_factor(imt)
        vs30_star = vs30.copy()
        vs30_star[vs30_star >= v1] = v1

        return vs30_star, v1

    def _compute_v1_factor(self, imt):
        """
        Compute and return v1 factor, equation 6, page 77.
        """
        if isinstance(imt, SA):
            t = imt.period
            if t <= 0.50:
                v1 = 1500.0
            elif t > 0.50 and t <= 1.0:
                v1 = np.exp(8.0 - 0.795 * np.log(t / 0.21))
            elif t > 1.0 and t < 2.0:
                v1 = np.exp(6.76 - 0.297 * np.log(t))
            else:
                v1 = 700.0
        elif isinstance(imt, PGA):
            v1 = 1500.0
        else:
            # this is for PGV
            v1 = 862.0

        return v1

    def _compute_e2_factor(self, imt, vs30):
        """
        Compute and return e2 factor, equation 19, page 80.
        """
        e2 = np.zeros_like(vs30)

        if isinstance(imt, PGV):
            period = 1
        elif isinstance(imt, PGA):
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

    def _compute_median_z1pt0(self, vs30):
        """
        Compute and return median z1pt0 (in m), equation 17, pqge 79.
        """
        z1pt0_median = np.zeros_like(vs30) + 6.745

        idx = np.where((vs30 >= 180.0) & (vs30 <= 500.0))
        z1pt0_median[idx] = 6.745 - 1.35 * np.log(vs30[idx] / 180.0)

        idx = vs30 > 500.0
        z1pt0_median[idx] = 5.394 - 4.48 * np.log(vs30[idx] / 500.0)

        return np.exp(z1pt0_median)

    def _compute_a22_factor(self, imt):
        """
        Compute and return the a22 factor, equation 20, page 80.
        """
        if isinstance(imt, PGA) or isinstance(imt, PGV):
            return 0
        elif isinstance(imt, SA):
            period = imt.period
            if period < 2.0:
                return 0.0
            else:
                return 0.0625 * (period - 2.0)

    #: Coefficient tables as per appendix B of Abrahamson et al. (2014)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT     m1      vlin    b       c       c4      a1      a2      a3      a4      a5      a6      a8      a10     a11     a12     a13     a14     a15     a17     a43     a44     a45     a46     a25     a28     a29     a31     a36     a37     a38     a39     a40     a41     a42     s1e     s2e     s3      s4      s1m     s2m     s5      s6
0       6.75    660     -1.47   2.4     4.5     0.587   -0.79   0.275   -0.1    -0.41   2.154   -0.015  1.735   0       -0.1    0.6     -0.3    1.1     -0.0072 0.1     0.05    0       -0.05   -0.0015 0.0025  -0.0034 -0.1503 0.265   0.337   0.188   0       0.088   -0.196  0.044   0.754   0.52    0.47    0.36    0.741   0.501   0.54    0.6300
-1      6.75    330     -2.02   2400    4.5     5.975   -0.919  0.275   -0.1    -0.41   2.366   -0.094  2.36    0       -0.1    0.25    0.22    0.3     -0.0005 0.28    0.15    0.09    0.07    -0.0001 0.0005  -0.0037 -0.1462 0.377   0.212   0.157   0       0.095   -0.038  0.065   0.662   0.51    0.38    0.38    0.66    0.51    0.58    0.5300
0.01    6.75    660     -1.47   2.4     4.5     0.587   -0.790  0.275   -0.1    -0.41   2.154   -0.015  1.735   0       -0.1    0.6     -0.3    1.1     -0.0072 0.1     0.05    0       -0.05   -0.0015 0.0025  -0.0034 -0.1503 0.265   0.337   0.188   0       0.088   -0.196  0.044   0.754   0.52    0.47    0.36    0.741   0.501   0.54    0.6300
0.02    6.75    680     -1.46   2.4     4.5     0.598   -0.790  0.275   -0.1    -0.41   2.146   -0.015  1.718   0       -0.1    0.6     -0.3    1.1     -0.0073 0.1     0.05    0       -0.05   -0.0015 0.0024  -0.0033 -0.1479 0.255   0.328   0.184   0       0.088   -0.194  0.061   0.76    0.52    0.47    0.36    0.747   0.501   0.54    0.6300
0.03    6.75    770     -1.39   2.4     4.5     0.602   -0.790  0.275   -0.1    -0.41   2.157   -0.015  1.615   0       -0.1    0.6     -0.3    1.1     -0.0075 0.1     0.05    0       -0.05   -0.0016 0.0023  -0.0034 -0.1447 0.249   0.32    0.18    0       0.093   -0.175  0.162   0.781   0.52    0.47    0.36    0.769   0.501   0.55    0.6300
0.05    6.75    915     -1.22   2.4     4.5     0.707   -0.790  0.275   -0.1    -0.41   2.085   -0.015  1.358   0       -0.1    0.6     -0.3    1.1     -0.008  0.1     0.05    0       -0.05   -0.002  0.0027  -0.0033 -0.1326 0.202   0.289   0.167   0       0.133   -0.09   0.451   0.81    0.53    0.47    0.36    0.798   0.512   0.56    0.6500
0.075   6.75    960     -1.15   2.4     4.5     0.973   -0.790  0.275   -0.1    -0.41   2.029   -0.015  1.258   0       -0.1    0.6     -0.3    1.1     -0.0089 0.1     0.05    0       -0.05   -0.0027 0.0032  -0.0029 -0.1353 0.126   0.275   0.173   0       0.186   0.09    0.506   0.81    0.54    0.47    0.36    0.798   0.522   0.57    0.6900
0.1     6.75    910     -1.23   2.4     4.5     1.169   -0.790  0.275   -0.1    -0.41   2.041   -0.015  1.31    0       -0.1    0.6     -0.3    1.1     -0.0095 0.1     0.05    0       -0.05   -0.0033 0.0036  -0.0025 -0.1128 0.022   0.256   0.189   0       0.16    0.006   0.335   0.81    0.55    0.47    0.36    0.795   0.527   0.57    0.7000
0.15    6.75    740     -1.59   2.4     4.5     1.442   -0.790  0.275   -0.1    -0.41   2.121   -0.022  1.66    0       -0.1    0.6     -0.3    1.1     -0.0095 0.1     0.05    0       -0.05   -0.0035 0.0033  -0.0025 0.0383  -0.136  0.162   0.108   0       0.068   -0.156  -0.084  0.801   0.56    0.47    0.36    0.773   0.519   0.58    0.7000
0.2     6.75    590     -2.01   2.4     4.5     1.637   -0.790  0.275   -0.1    -0.41   2.224   -0.03   2.22    0       -0.1    0.6     -0.3    1.1     -0.0086 0.1     0.05    0       -0.03   -0.0033 0.0027  -0.0031 0.0775  -0.078  0.224   0.115   0       0.048   -0.274  -0.178  0.789   0.565   0.47    0.36    0.753   0.514   0.59    0.7000
0.25    6.75    495     -2.41   2.4     4.5     1.701   -0.790  0.275   -0.1    -0.41   2.312   -0.038  2.77    0       -0.1    0.6     -0.24   1.1     -0.0074 0.1     0.05    0       0       -0.0029 0.0024  -0.0036 0.0741  0.037   0.248   0.122   0       0.055   -0.248  -0.187  0.77    0.57    0.47    0.36    0.729   0.513   0.61    0.7000
0.3     6.75    430     -2.76   2.4     4.5     1.712   -0.790  0.275   -0.1    -0.41   2.338   -0.045  3.25    0       -0.1    0.6     -0.19   1.03    -0.0064 0.1     0.05    0.03    0.03    -0.0027 0.002   -0.0039 0.2548  -0.091  0.203   0.096   0       0.073   -0.203  -0.159  0.74    0.58    0.47    0.36    0.693   0.519   0.63    0.7000
0.4     6.75    360     -3.28   2.4     4.5     1.662   -0.790  0.275   -0.1    -0.41   2.469   -0.055  3.99    0       -0.1    0.58    -0.11   0.92    -0.0043 0.1     0.07    0.06    0.06    -0.0023 0.001   -0.0048 0.2136  0.129   0.232   0.123   0       0.143   -0.154  -0.023  0.699   0.59    0.47    0.36    0.644   0.524   0.66    0.7000
0.5     6.75    340     -3.6    2.4     4.5     1.571   -0.790  0.275   -0.1    -0.41   2.559   -0.065  4.45    0       -0.1    0.56    -0.04   0.84    -0.0032 0.1     0.1     0.1     0.09    -0.002  0.0008  -0.005  0.1542  0.31    0.252   0.134   0       0.16    -0.159  -0.029  0.676   0.6     0.47    0.36    0.616   0.532   0.69    0.7000
0.75    6.75    330     -3.8    2.4     4.5     1.299   -0.790  0.275   -0.1    -0.41   2.682   -0.095  4.75    0       -0.1    0.53    0.07    0.68    -0.0025 0.14    0.14    0.14    0.13    -0.001  0.0007  -0.0041 0.0787  0.505   0.208   0.129   0       0.158   -0.141  0.061   0.631   0.615   0.47    0.36    0.566   0.548   0.73    0.6900
1       6.75    330     -3.5    2.4     4.5     1.043   -0.790  0.275   -0.1    -0.41   2.763   -0.11   4.3     0       -0.1    0.5     0.15    0.57    -0.0025 0.17    0.17    0.17    0.14    -0.0005 0.0007  -0.0032 0.0476  0.358   0.208   0.152   0       0.145   -0.144  0.062   0.609   0.63    0.47    0.36    0.541   0.565   0.77    0.6800
1.5     6.75    330     -2.4    2.4     4.5     0.665   -0.790  0.275   -0.1    -0.41   2.836   -0.124  2.6     0       -0.1    0.42    0.27    0.42    -0.0022 0.22    0.21    0.2     0.16    -0.0004 0.0006  -0.002  -0.0163 0.131   0.108   0.118   0       0.131   -0.126  0.037   0.578   0.64    0.47    0.36    0.506   0.576   0.8     0.6600
2       6.75    330     -1      2.4     4.5     0.329   -0.790  0.275   -0.1    -0.41   2.897   -0.138  0.55    0       -0.1    0.35    0.35    0.31    -0.0019 0.26    0.25    0.22    0.16    -0.0002 0.0003  -0.0017 -0.1203 0.123   0.068   0.119   0       0.083   -0.075  -0.143  0.555   0.65    0.47    0.36    0.48    0.587   0.8     0.6200
3       6.82    330     0       2.4     4.5     -0.060  -0.790  0.275   -0.1    -0.41   2.906   -0.172  -0.95   0       -0.1    0.2     0.46    0.16    -0.0015 0.34    0.3     0.23    0.16    0       0       -0.002  -0.2719 0.109   -0.023  0.093   0       0.07    -0.021  -0.028  0.548   0.64    0.47    0.36    0.472   0.576   0.8     0.5500
4       6.92    330     0       2.4     4.5     -0.299  -0.790  0.275   -0.1    -0.41   2.889   -0.197  -0.95   0       -0.1    0       0.54    0.05    -0.001  0.41    0.32    0.23    0.14    0       0       -0.002  -0.2958 0.135   0.028   0.084   0       0.101   0.072   -0.097  0.527   0.63    0.47    0.36    0.447   0.565   0.76    0.5200
5       7       330     0       2.4     4.5     -0.562  -0.765  0.275   -0.1    -0.41   2.898   -0.218  -0.93   0       -0.1    0       0.61    -0.04   -0.001  0.51    0.32    0.22    0.13    0       0       -0.002  -0.2718 0.189   0.031   0.058   0       0.095   0.205   0.015   0.505   0.63    0.47    0.36    0.425   0.568   0.72    0.5000
6       7.06    330     0       2.4     4.5     -0.875  -0.711  0.275   -0.1    -0.41   2.896   -0.235  -0.91   0       -0.2    0       0.65    -0.11   -0.001  0.55    0.32    0.2     0.1     0       0       -0.002  -0.2517 0.215   0.024   0.065   0       0.133   0.285   0.104   0.477   0.63    0.47    0.36    0.395   0.571   0.7     0.5000
7.5     7.15    330     0       2.4     4.5     -1.303  -0.634  0.275   -0.1    -0.41   2.870   -0.255  -0.87   0       -0.2    0       0.72    -0.19   -0.001  0.49    0.28    0.17    0.09    0       0       -0.002  -0.14   0.15    -0.07   0       0       0.151   0.329   0.299   0.457   0.63    0.47    0.36    0.378   0.575   0.67    0.5000
10      7.25    330     0       2.4     4.5     -1.928  -0.529  0.275   -0.1    -0.41   2.843   -0.285  -0.8    0       -0.2    0       0.8     -0.3    -0.001  0.42    0.22    0.14    0.08    0       0       -0.002  -0.0216 0.092   -0.159  -0.05   0       0.124   0.301   0.243   0.429   0.63    0.47    0.36    0.359   0.585   0.64    0.5000
    """)

    #: equation constants (that are IMT independent)
    CONSTS = {
        # m2 specified at page 1032 (top)
        'm2': 5.00,
    }
