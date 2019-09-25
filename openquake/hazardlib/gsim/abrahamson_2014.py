# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Module exports :class:`AbrahamsonEtAl2014`
               :class:`AbrahamsonEtAl2014RegCHN`
               :class:`AbrahamsonEtAl2014RegJPN`
               :class:`AbrahamsonEtAl2014RegTWN`
"""
import copy
import numpy as np

from scipy import interpolate
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA

METRES_PER_KM = 1000.0


class AbrahamsonEtAl2014(GMPE):
    """
    Implements GMPE by Abrahamson, Silva and Kamai developed within the
    the PEER West 2 Project. This GMPE is described in a paper
    published in 2014 on Earthquake Spectra, Volume 30, Number 3 and
    titled 'Summary of the ASK14 Ground Motion Relation for Active Crustal
    Regions'.
    """
    #: Supported tectonic region type is active shallow crust, see title!
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration, peak
    #: ground velocity and peak ground acceleration, see tables 4
    #: pages 1036
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: average horizontal :attr:`~openquake.hazardlib.const.IMC.RotD50`,
    #: see page 1025.
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
    #: Unit of measure for Z1.0 is [m]
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'z1pt0', 'vs30measured'))

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
        # get the necessary set of coefficients
        C = self.COEFFS[imt]
        # compute median sa on rock (vs30=1180m/s). Used for site response
        # term calculation
        sa1180 = np.exp(self._get_sa_at_1180(C, imt, sites, rup, dists))

        # get the mean value
        mean = (self._get_basic_term(C, rup, dists) +
                self._get_faulting_style_term(C, rup) +
                self._get_site_response_term(C, imt, sites.vs30, sa1180) +
                self._get_hanging_wall_term(C, dists, rup) +
                self._get_top_of_rupture_depth_term(C, imt, rup) +
                self._get_soil_depth_term(C, sites.z1pt0 / METRES_PER_KM,
                                          sites.vs30)
                )
        mean += self._get_regional_term(C, imt, sites.vs30, dists.rrup)
        # get standard deviations
        stddevs = self._get_stddevs(C, imt, rup, sites, stddev_types, sa1180,
                                    dists)
        return mean, stddevs

    def _get_sa_at_1180(self, C, imt, sites, rup, dists):
        """
        Compute and return mean imt value for rock conditions
        (vs30 = 1100 m/s)
        """
        # reference vs30 = 1180 m/s
        vs30_1180 = np.ones_like(sites.vs30) * 1180.
        # reference shaking intensity = 0
        ref_iml = np.zeros_like(sites.vs30)
        # fake Z1.0 - Since negative it will be replaced by the default Z1.0
        # for the corresponding region
        fake_z1pt0 = np.ones_like(sites.vs30) * -1
        return (self._get_basic_term(C, rup, dists) +
                self._get_faulting_style_term(C, rup) +
                self._get_site_response_term(C, imt, vs30_1180, ref_iml) +
                self._get_hanging_wall_term(C, dists, rup) +
                self._get_top_of_rupture_depth_term(C, imt, rup) +
                self._get_soil_depth_term(C, fake_z1pt0, vs30_1180) +
                self._get_regional_term(C, imt, vs30_1180, dists.rrup)
                )

    def _get_basic_term(self, C, rup, dists):
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
        R = np.sqrt(dists.rrup**2. + c4m**2.)
        # basic form
        base_term = C['a1'] * np.ones_like(dists.rrup) + C['a17'] * dists.rrup
        # equation 2 at page 1030
        if rup.mag >= C['m1']:
            base_term += (C['a5'] * (rup.mag - C['m1']) +
                          C['a8'] * (8.5 - rup.mag)**2. +
                          (C['a2'] + C['a3'] * (rup.mag - C['m1'])) *
                          np.log(R))
        elif rup.mag >= self.CONSTS['m2']:
            base_term += (C['a4'] * (rup.mag - C['m1']) +
                          C['a8'] * (8.5 - rup.mag)**2. +
                          (C['a2'] + C['a3'] * (rup.mag - C['m1'])) *
                          np.log(R))
        else:
            base_term += (C['a4'] * (self.CONSTS['m2'] - C['m1']) +
                          C['a8'] * (8.5 - self.CONSTS['m2'])**2. +
                          C['a6'] * (rup.mag - self.CONSTS['m2']) +
                          C['a7'] * (rup.mag - self.CONSTS['m2'])**2. +
                          (C['a2'] + C['a3'] * (self.CONSTS['m2'] - C['m1'])) *
                          np.log(R))
        return base_term

    def _get_faulting_style_term(self, C, rup):
        """
        Compute and return faulting style term, that is the sum of the second
        and third terms in equation 1, page 74.
        """
        # this implements equations 5 and 6 at page 1032. f7 is the
        # coefficient for reverse mechanisms while f8 is the correction
        # factor for normal ruptures
        if rup.mag > 5.0:
            f7 = C['a11']
            f8 = C['a12']
        elif rup.mag >= 4:
            f7 = C['a11'] * (rup.mag - 4.)
            f8 = C['a12'] * (rup.mag - 4.)
        else:
            f7 = 0.0
            f8 = 0.0
        # ranges of rake values for each faulting mechanism are specified in
        # table 2, page 1031
        return (f7 * float(rup.rake > 30 and rup.rake < 150) +
                f8 * float(rup.rake > -150 and rup.rake < -30))

    def _get_vs30star(self, vs30, imt):
        """
        This computes equations 8 and 9 at page 1034
        """
        # compute the v1 value (see eq. 9, page 1034)
        if imt.name == "SA":
            t = imt.period
            if t <= 0.50:
                v1 = 1500.0
            elif t < 3.0:
                v1 = np.exp(-0.35 * np.log(t / 0.5) + np.log(1500.))
            else:
                v1 = 800.0
        elif imt.name == "PGA":
            v1 = 1500.0
        else:
            # This covers the PGV case
            v1 = 1500.0
        # set the vs30 star value (see eq. 8, page 1034)
        vs30_star = np.ones_like(vs30) * vs30
        vs30_star[vs30 >= v1] = v1
        return vs30_star

    def _get_site_response_term(self, C, imt, vs30, sa1180):
        """
        Compute and return site response model term see page 1033
        """
        # vs30 star
        vs30_star = self._get_vs30star(vs30, imt)
        # compute the site term
        site_resp_term = np.zeros_like(vs30)
        gt_vlin = vs30 >= C['vlin']
        lw_vlin = vs30 < C['vlin']
        # compute site response term for sites with vs30 greater than vlin
        vs30_rat = vs30_star / C['vlin']
        site_resp_term[gt_vlin] = ((C['a10'] + C['b'] * self.CONSTS['n']) *
                                   np.log(vs30_rat[gt_vlin]))
        # compute site response term for sites with vs30 lower than vlin
        site_resp_term[lw_vlin] = (C['a10'] * np.log(vs30_rat[lw_vlin]) -
                                   C['b'] * np.log(sa1180[lw_vlin] + C['c']) +
                                   C['b'] * np.log(sa1180[lw_vlin] + C['c'] *
                                                   vs30_rat[lw_vlin] **
                                                   self.CONSTS['n']))
        return site_resp_term

    def _get_hanging_wall_term(self, C, dists, rup):
        """
        Compute and return hanging wall model term, see page 1038.
        """
        if rup.dip == 90.0:
            return np.zeros_like(dists.rx)
        else:
            Fhw = np.zeros_like(dists.rx)
            Fhw[dists.rx > 0] = 1.
            # Compute taper t1
            T1 = np.ones_like(dists.rx)
            T1 *= 60./45. if rup.dip <= 30. else (90.-rup.dip)/45.0
            # Compute taper t2 (eq 12 at page 1039) - a2hw set to 0.2 as
            # indicated at page 1041
            T2 = np.zeros_like(dists.rx)
            a2hw = 0.2
            if rup.mag > 6.5:
                T2 += (1. + a2hw * (rup.mag - 6.5))
            elif rup.mag > 5.5:
                T2 += (1. + a2hw * (rup.mag - 6.5) - (1. - a2hw) *
                       (rup.mag - 6.5)**2)
            else:
                T2 *= 0.
            # Compute taper t3 (eq. 13 at page 1039) - r1 and r2 specified at
            # page 1040
            T3 = np.zeros_like(dists.rx)
            r1 = rup.width * np.cos(np.radians(rup.dip))
            r2 = 3. * r1
            #
            idx = dists.rx < r1
            T3[idx] = (np.ones_like(dists.rx)[idx] * self.CONSTS['h1'] +
                       self.CONSTS['h2'] * (dists.rx[idx] / r1) +
                       self.CONSTS['h3'] * (dists.rx[idx] / r1)**2)
            #
            idx = ((dists.rx >= r1) & (dists.rx <= r2))
            T3[idx] = 1. - (dists.rx[idx] - r1) / (r2 - r1)
            # Compute taper t4 (eq. 14 at page 1040)
            T4 = np.zeros_like(dists.rx)
            #
            if rup.ztor <= 10.:
                T4 += (1. - rup.ztor**2. / 100.)
            # Compute T5 (eq 15a at page 1040) - ry1 computed according to
            # suggestions provided at page 1040
            T5 = np.zeros_like(dists.rx)
            ry1 = dists.rx * np.tan(np.radians(20.))
            #
            idx = (dists.ry0 - ry1) <= 0.0
            T5[idx] = 1.
            #
            idx = (((dists.ry0 - ry1) > 0.0) & ((dists.ry0 - ry1) < 5.0))
            T5[idx] = 1. - (dists.ry0[idx] - ry1[idx]) / 5.0
            # Finally, compute the hanging wall term
            return Fhw*C['a13']*T1*T2*T3*T4*T5

    def _get_top_of_rupture_depth_term(self, C, imt, rup):
        """
        Compute and return top of rupture depth term. See paragraph
        'Depth-to-Top of Rupture Model', page 1042.
        """
        if rup.ztor >= 20.0:
            return C['a15']
        else:
            return C['a15'] * rup.ztor / 20.0

    def _get_z1pt0ref(self, vs30):
        """
        This computes the reference depth to the 1.0 km/s interface using
        equation 18 at page 1042 of Abrahamson et al. (2014)
        """
        return (1. / 1000.) * np.exp((-7.67 / 4.)*np.log((vs30**4 + 610.**4) /
                                                         (1360.**4 + 610.**4)))

    def _get_soil_depth_term(self, C, z1pt0, vs30):
        """
        Compute and return soil depth term.  See page 1042.
        """
        # Get reference z1pt0
        z1ref = self._get_z1pt0ref(vs30)
        # Get z1pt0
        z10 = copy.deepcopy(z1pt0)
        # This is used for the calculation of the motion on reference rock
        idx = z1pt0 < 0
        z10[idx] = z1ref[idx]
        factor = np.log((z10 + 0.01) / (z1ref + 0.01))
        # Here we use a linear interpolation as suggested in the 'Application
        # guidelines' at page 1044
        # Above 700 m/s the trend is flat, but we extend the Vs30 range to
        # 6,000 m/s (basically the upper limit for mantle shear wave velocity
        # on earth) to allow extrapolation without throwing an error.
        f2 = interpolate.interp1d(
            [0.0, 150, 250, 400, 700, 1000, 6000],
            [C['a43'], C['a43'], C['a44'], C['a45'], C['a46'], C['a46'],
             C['a46']],
            kind='linear')
        return f2(vs30) * factor

    def _get_regional_term(self, C, imt, vs30, rrup):
        """
        In accordance with Abrahamson et al. (2014) we assume California
        as the default region hence here the regional term is assumed = 0.
        """
        return 0.

    def _get_stddevs(self, C, imt, rup, sites, stddev_types, sa1180, dists):
        """
        Return standard deviations as described in paragraph 'Equations for
        standard deviation', page 1046.
        """
        std_intra = self._get_intra_event_std(C, rup.mag, sa1180, sites.vs30,
                                              sites.vs30measured, dists.rrup)
        std_inter = self._get_inter_event_std(C, rup.mag, sa1180, sites.vs30)
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(std_intra ** 2 +
                                       std_inter ** 2))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(std_intra)
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(std_inter)
        return stddevs

    def _get_intra_event_std(self, C, mag, sa1180, vs30, vs30measured,
                             rrup):
        """
        Returns Phi as described at pages 1046 and 1047
        """
        phi_al = self._get_phi_al_regional(C, mag, vs30measured, rrup)
        derAmp = self._get_derivative(C, sa1180, vs30)
        phi_amp = 0.4
        idx = phi_al < phi_amp
        if np.any(idx):
            # In the case of small magnitudes and long periods it is possible
            # for phi_al to take a value less than phi_amp, which would return
            # a complex value. According to the GMPE authors in this case
            # phi_amp should be reduced such that it is fractionally smaller
            # than phi_al
            phi_amp = 0.4 * np.ones_like(phi_al)
            phi_amp[idx] = 0.99 * phi_al[idx]
        phi_b = np.sqrt(phi_al**2 - phi_amp**2)
        phi = np.sqrt(phi_b**2 * (1 + derAmp)**2 + phi_amp**2)
        return phi

    def _get_derivative(self, C, sa1180, vs30):
        """
        Returns equation 30 page 1047
        """
        derAmp = np.zeros_like(vs30)
        n = self.CONSTS['n']
        c = C['c']
        b = C['b']
        idx = vs30 < C['vlin']
        derAmp[idx] = (b * sa1180[idx] * (-1./(sa1180[idx]+c) +
                       1./(sa1180[idx] + c*(vs30[idx]/C['vlin'])**n)))
        return derAmp

    def _get_phi_al_regional(self, C, mag, vs30measured, rrup):
        """
        Returns intra-event (Phi) standard deviation (equation 24, page 1046)
        """
        phi_al = np.ones((len(vs30measured)))
        s1 = np.ones_like(phi_al) * C['s1e']
        s2 = np.ones_like(phi_al) * C['s2e']
        s1[vs30measured] = C['s1m']
        s2[vs30measured] = C['s2m']
        if mag < 4:
            phi_al *= s1
        elif mag <= 6:
            phi_al *= s1 + (s2 - s1) / 2. * (mag - 4.)
        else:
            phi_al *= s2
        return phi_al

    def _get_inter_event_std(self, C, mag, sa1180, vs30):
        """
        Returns inter event (tau) standard deviation (equation 25, page 1046)
        """
        if mag < 5:
            tau_al = C['s3']
        elif mag <= 7:
            tau_al = C['s3'] + (C['s4'] - C['s3']) / 2. * (mag - 5.)
        else:
            tau_al = C['s4']
        tau_b = tau_al
        tau = tau_b * (1 + self._get_derivative(C, sa1180, vs30))
        return tau

    #: Coefficient tables as per annex B of Abrahamson et al. (2014)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT     m1      vlin    b       c       c4      a1      a2      a3      a4      a5      a6      a7   a8      a10     a11     a12     a13     a14     a15     a17     a43     a44     a45     a46     a25     a28     a29     a31     a36     a37     a38     a39     a40     a41     a42     s1e     s2e     s3      s4      s1m     s2m     s5      s6
pga     6.75    660     -1.47   2.4     4.5     0.587   -0.79   0.275   -0.1    -0.41   2.154   0.0  -0.015  1.735   0       -0.1    0.6     -0.3    1.1     -0.0072 0.1     0.05    0       -0.05   -0.0015 0.0025  -0.0034 -0.1503 0.265   0.337   0.188   0       0.088   -0.196  0.044   0.754   0.52    0.47    0.36    0.741   0.501   0.54    0.6300
pgv     6.75    330     -2.02   2400    4.5     5.975   -0.919  0.275   -0.1    -0.41   2.366   0.0  -0.094  2.36    0       -0.1    0.25    0.22    0.3     -0.0005 0.28    0.15    0.09    0.07    -0.0001 0.0005  -0.0037 -0.1462 0.377   0.212   0.157   0       0.095   -0.038  0.065   0.662   0.51    0.38    0.38    0.66    0.51    0.58    0.5300
0.01    6.75    660     -1.47   2.4     4.5     0.587   -0.790  0.275   -0.1    -0.41   2.154   0.0  -0.015  1.735   0       -0.1    0.6     -0.3    1.1     -0.0072 0.1     0.05    0       -0.05   -0.0015 0.0025  -0.0034 -0.1503 0.265   0.337   0.188   0       0.088   -0.196  0.044   0.754   0.52    0.47    0.36    0.741   0.501   0.54    0.6300
0.02    6.75    680     -1.46   2.4     4.5     0.598   -0.790  0.275   -0.1    -0.41   2.146   0.0  -0.015  1.718   0       -0.1    0.6     -0.3    1.1     -0.0073 0.1     0.05    0       -0.05   -0.0015 0.0024  -0.0033 -0.1479 0.255   0.328   0.184   0       0.088   -0.194  0.061   0.76    0.52    0.47    0.36    0.747   0.501   0.54    0.6300
0.03    6.75    770     -1.39   2.4     4.5     0.602   -0.790  0.275   -0.1    -0.41   2.157   0.0  -0.015  1.615   0       -0.1    0.6     -0.3    1.1     -0.0075 0.1     0.05    0       -0.05   -0.0016 0.0023  -0.0034 -0.1447 0.249   0.32    0.18    0       0.093   -0.175  0.162   0.781   0.52    0.47    0.36    0.769   0.501   0.55    0.6300
0.05    6.75    915     -1.22   2.4     4.5     0.707   -0.790  0.275   -0.1    -0.41   2.085   0.0  -0.015  1.358   0       -0.1    0.6     -0.3    1.1     -0.008  0.1     0.05    0       -0.05   -0.002  0.0027  -0.0033 -0.1326 0.202   0.289   0.167   0       0.133   -0.09   0.451   0.81    0.53    0.47    0.36    0.798   0.512   0.56    0.6500
0.075   6.75    960     -1.15   2.4     4.5     0.973   -0.790  0.275   -0.1    -0.41   2.029   0.0  -0.015  1.258   0       -0.1    0.6     -0.3    1.1     -0.0089 0.1     0.05    0       -0.05   -0.0027 0.0032  -0.0029 -0.1353 0.126   0.275   0.173   0       0.186   0.09    0.506   0.81    0.54    0.47    0.36    0.798   0.522   0.57    0.6900
0.1     6.75    910     -1.23   2.4     4.5     1.169   -0.790  0.275   -0.1    -0.41   2.041   0.0  -0.015  1.31    0       -0.1    0.6     -0.3    1.1     -0.0095 0.1     0.05    0       -0.05   -0.0033 0.0036  -0.0025 -0.1128 0.022   0.256   0.189   0       0.16    0.006   0.335   0.81    0.55    0.47    0.36    0.795   0.527   0.57    0.7000
0.15    6.75    740     -1.59   2.4     4.5     1.442   -0.790  0.275   -0.1    -0.41   2.121   0.0  -0.022  1.66    0       -0.1    0.6     -0.3    1.1     -0.0095 0.1     0.05    0       -0.05   -0.0035 0.0033  -0.0025 0.0383  -0.136  0.162   0.108   0       0.068   -0.156  -0.084  0.801   0.56    0.47    0.36    0.773   0.519   0.58    0.7000
0.2     6.75    590     -2.01   2.4     4.5     1.637   -0.790  0.275   -0.1    -0.41   2.224   0.0  -0.03   2.22    0       -0.1    0.6     -0.3    1.1     -0.0086 0.1     0.05    0       -0.03   -0.0033 0.0027  -0.0031 0.0775  -0.078  0.224   0.115   0       0.048   -0.274  -0.178  0.789   0.565   0.47    0.36    0.753   0.514   0.59    0.7000
0.25    6.75    495     -2.41   2.4     4.5     1.701   -0.790  0.275   -0.1    -0.41   2.312   0.0  -0.038  2.77    0       -0.1    0.6     -0.24   1.1     -0.0074 0.1     0.05    0       0       -0.0029 0.0024  -0.0036 0.0741  0.037   0.248   0.122   0       0.055   -0.248  -0.187  0.77    0.57    0.47    0.36    0.729   0.513   0.61    0.7000
0.3     6.75    430     -2.76   2.4     4.5     1.712   -0.790  0.275   -0.1    -0.41   2.338   0.0  -0.045  3.25    0       -0.1    0.6     -0.19   1.03    -0.0064 0.1     0.05    0.03    0.03    -0.0027 0.002   -0.0039 0.2548  -0.091  0.203   0.096   0       0.073   -0.203  -0.159  0.74    0.58    0.47    0.36    0.693   0.519   0.63    0.7000
0.4     6.75    360     -3.28   2.4     4.5     1.662   -0.790  0.275   -0.1    -0.41   2.469   0.0  -0.055  3.99    0       -0.1    0.58    -0.11   0.92    -0.0043 0.1     0.07    0.06    0.06    -0.0023 0.001   -0.0048 0.2136  0.129   0.232   0.123   0       0.143   -0.154  -0.023  0.699   0.59    0.47    0.36    0.644   0.524   0.66    0.7000
0.5     6.75    340     -3.6    2.4     4.5     1.571   -0.790  0.275   -0.1    -0.41   2.559   0.0  -0.065  4.45    0       -0.1    0.56    -0.04   0.84    -0.0032 0.1     0.1     0.1     0.09    -0.002  0.0008  -0.005  0.1542  0.31    0.252   0.134   0       0.16    -0.159  -0.029  0.676   0.6     0.47    0.36    0.616   0.532   0.69    0.7000
0.75    6.75    330     -3.8    2.4     4.5     1.299   -0.790  0.275   -0.1    -0.41   2.682   0.0  -0.095  4.75    0       -0.1    0.53    0.07    0.68    -0.0025 0.14    0.14    0.14    0.13    -0.001  0.0007  -0.0041 0.0787  0.505   0.208   0.129   0       0.158   -0.141  0.061   0.631   0.615   0.47    0.36    0.566   0.548   0.73    0.6900
1       6.75    330     -3.5    2.4     4.5     1.043   -0.790  0.275   -0.1    -0.41   2.763   0.0  -0.11   4.3     0       -0.1    0.5     0.15    0.57    -0.0025 0.17    0.17    0.17    0.14    -0.0005 0.0007  -0.0032 0.0476  0.358   0.208   0.152   0       0.145   -0.144  0.062   0.609   0.63    0.47    0.36    0.541   0.565   0.77    0.6800
1.5     6.75    330     -2.4    2.4     4.5     0.665   -0.790  0.275   -0.1    -0.41   2.836   0.0  -0.124  2.6     0       -0.1    0.42    0.27    0.42    -0.0022 0.22    0.21    0.2     0.16    -0.0004 0.0006  -0.002  -0.0163 0.131   0.108   0.118   0       0.131   -0.126  0.037   0.578   0.64    0.47    0.36    0.506   0.576   0.8     0.6600
2       6.75    330     -1      2.4     4.5     0.329   -0.790  0.275   -0.1    -0.41   2.897   0.0  -0.138  0.55    0       -0.1    0.35    0.35    0.31    -0.0019 0.26    0.25    0.22    0.16    -0.0002 0.0003  -0.0017 -0.1203 0.123   0.068   0.119   0       0.083   -0.075  -0.143  0.555   0.65    0.47    0.36    0.48    0.587   0.8     0.6200
3       6.82    330     0       2.4     4.5     -0.060  -0.790  0.275   -0.1    -0.41   2.906   0.0  -0.172  -0.95   0       -0.1    0.2     0.46    0.16    -0.0015 0.34    0.3     0.23    0.16    0       0       -0.002  -0.2719 0.109   -0.023  0.093   0       0.07    -0.021  -0.028  0.548   0.64    0.47    0.36    0.472   0.576   0.8     0.5500
4       6.92    330     0       2.4     4.5     -0.299  -0.790  0.275   -0.1    -0.41   2.889   0.0  -0.197  -0.95   0       -0.1    0       0.54    0.05    -0.001  0.41    0.32    0.23    0.14    0       0       -0.002  -0.2958 0.135   0.028   0.084   0       0.101   0.072   -0.097  0.527   0.63    0.47    0.36    0.447   0.565   0.76    0.5200
5       7       330     0       2.4     4.5     -0.562  -0.765  0.275   -0.1    -0.41   2.898   0.0  -0.218  -0.93   0       -0.1    0       0.61    -0.04   -0.001  0.51    0.32    0.22    0.13    0       0       -0.002  -0.2718 0.189   0.031   0.058   0       0.095   0.205   0.015   0.505   0.63    0.47    0.36    0.425   0.568   0.72    0.5000
6       7.06    330     0       2.4     4.5     -0.875  -0.711  0.275   -0.1    -0.41   2.896   0.0  -0.235  -0.91   0       -0.2    0       0.65    -0.11   -0.001  0.55    0.32    0.2     0.1     0       0       -0.002  -0.2517 0.215   0.024   0.065   0       0.133   0.285   0.104   0.477   0.63    0.47    0.36    0.395   0.571   0.7     0.5000
7.5     7.15    330     0       2.4     4.5     -1.303  -0.634  0.275   -0.1    -0.41   2.870   0.0  -0.255  -0.87   0       -0.2    0       0.72    -0.19   -0.001  0.49    0.28    0.17    0.09    0       0       -0.002  -0.14   0.15    -0.07   0       0       0.151   0.329   0.299   0.457   0.63    0.47    0.36    0.378   0.575   0.67    0.5000
10      7.25    330     0       2.4     4.5     -1.928  -0.529  0.275   -0.1    -0.41   2.843   0.0  -0.285  -0.8    0       -0.2    0       0.8     -0.3    -0.001  0.42    0.22    0.14    0.08    0       0       -0.002  -0.0216 0.092   -0.159  -0.05   0       0.124   0.301   0.243   0.429   0.63    0.47    0.36    0.359   0.585   0.64    0.5000
    """)

    #: equation constants (that are IMT independent)
    CONSTS = {
        'n': 1.5,
        # m2 specified at page 1032 (top)
        'm2': 5.00,
        # h1, h2, h3 specified at page 1040 (top)
        'h1': +0.25,
        'h2': +1.50,
        'h3': -0.75,
    }


class AbrahamsonEtAl2014RegTWN(AbrahamsonEtAl2014):
    """
    Implements GMPE developed by Abrahamson, Silva and Kamai in 2014 as
    part of the PEER West 2 Project. The GMPE is described in a paper
    published in 2014 on Earthquake Spectra, Volume 30, Number 3.

    Regional corrections for Taiwan
    """

    def _get_regional_term(self, C, imt, vs30, rrup):
        """
        In accordance with Abrahamson et al. (2014) we assume as the default
        region California
        """
        vs30star = self._get_vs30star(vs30, imt)
        return C['a31'] * np.log(vs30star/C['vlin']) + C['a25'] * rrup


class AbrahamsonEtAl2014RegCHN(AbrahamsonEtAl2014):
    """
    Implements GMPE developed by Abrahamson, Silva and Kamai in 2014 as
    part of the PEER West 2 Project. The GMPE is described in a paper
    published in 2014 on Earthquake Spectra, Volume 30, Number 3.

    Regional corrections for China
    """

    def _get_regional_term(self, C, imt, vs30, rrup):
        """
        In accordance with Abrahamson et al. (2014) we assume as the default
        region California
        """
        return C['a28'] * rrup


class AbrahamsonEtAl2014RegJPN(AbrahamsonEtAl2014):
    """
    Implements GMPE developed by Abrahamson, Silva and Kamai in 2014 as
    part of the PEER West 2 Project. The GMPE is described in a paper
    published in 2014 on Earthquake Spectra, Volume 30, Number 3.

    Regional corrections for Japan
    """

    def _get_z1pt0ref(self, vs30):
        """
        This provides the default depth to the 1.0 km/s interface for Japan
        """
        return 1./1000. * np.exp(-5.23/2.*np.log((vs30**2+412.**2.) /
                                                 (1360.**2+412**2.)))

    def _get_regional_term(self, C, imt, vs30, rrup):
        """
        Compute regional term for Japan. See page 1043
        """
        f3 = interpolate.interp1d(
            [150, 250, 350, 450, 600, 850, 1150, 2000],
            [C['a36'], C['a37'], C['a38'], C['a39'], C['a40'], C['a41'],
             C['a42'], C['a42']],
            kind='linear')
        return f3(vs30) + C['a29'] * rrup

    def _get_phi_al_regional(self, C, mag, vs30measured, rrup):
        """
        Returns intra-event (Tau) standard deviation (equation 26, page 1046)
        """
        phi_al = np.ones((len(vs30measured)))

        idx = rrup < 30
        phi_al[idx] *= C['s5']

        idx = ((rrup <= 80) & (rrup >= 30.))
        phi_al[idx] *= C['s5'] + (C['s6'] - C['s5']) / 50. * (rrup[idx] - 30.)

        idx = rrup > 80
        phi_al[idx] *= C['s6']

        return phi_al
