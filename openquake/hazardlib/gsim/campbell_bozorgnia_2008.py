# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
Module exports :class:`CampbellBozorgnia2008`, and
:class:'CampbellBozorgnia2008Arbitrary'
"""
import numpy as np
from math import log, exp
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, PGD, CAV, SA


class CampbellBozorgnia2008(GMPE):
    """
    Implements GMPE developed by Kenneth W. Campbell and Yousef Bozorgnia,
    published as "NGA Ground Motion Model for the Geometric Mean Horizontal
    Component of PGA, PGV, PGD and 5 % Damped Linear Elastic Response Spectra
    for Periods Ranging from 0.01 to 10s" (2008, Earthquake Spectra,
    Volume 24, Number 1, pages 139 - 171).
    This class implements the model for the Geometric Mean of the elastic
    spectra.
    Included in the coefficient set are the coefficients for the
    Campbell & Bozorgnia (2010) GMPE for predicting Cumulative Absolute
    Velocity (CAV), published as "A Ground Motion Prediction Equation for
    the Horizontal Component of Cumulative Absolute Velocity (CSV) Based on
    the PEER-NGA Strong Motion Database" (2010, Earthquake Spectra, Volume 26,
    Number 3, 635 - 650).
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration, peak
    #: ground velocity, peak ground displacement and peak ground acceleration
    #: Additional model for cumulative absolute velocity defined in
    #: Campbell & Bozorgnia (2010)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        PGD,
        CAV,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: average horizontal :attr:`~openquake.hazardlib.const.IMC.GMRotI50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotI50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section "Aleatory Uncertainty Model", page 147.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters are Vs30, Vs30 type (measured or inferred),
    #: and depth (km) to the 2.5 km/s shear wave velocity layer (z2pt5)
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'z2pt5'))

    #: Required rupture parameters are magnitude, rake, dip, ztor
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake', 'dip', 'ztor'))

    #: Required distance measures are Rrup and Rjb.
    REQUIRES_DISTANCES = set(('rrup', 'rjb'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type and for PGA
        C = self.COEFFS[imt]
        C_PGA = self.COEFFS[PGA()]

        # compute median pga on rock (vs30=1100), needed for site response
        # term calculation
        # For spectral accelerations at periods between 0.0 and 0.25 s, Sa (T)
        # cannot be less than PGA on soil, therefore if the IMT is in this
        # period range it is necessary to calculate PGA on soil
        if imt.name == 'SA' and imt.period > 0.0 and imt.period < 0.25:
            get_pga_site = True
        else:
            get_pga_site = False
        pga1100, pga_site = self._compute_imt1100(C_PGA,
                                                  sites,
                                                  rup,
                                                  dists,
                                                  get_pga_site)

        # Get the median ground motion
        mean = (self._compute_magnitude_term(C, rup.mag) +
                self._compute_distance_term(C, rup, dists) +
                self._compute_style_of_faulting_term(C, rup) +
                self._compute_hanging_wall_term(C, rup, dists) +
                self._compute_shallow_site_response(C, sites, pga1100) +
                self._compute_basin_response_term(C, sites.z2pt5))

        # If it is necessary to ensure that Sa(T) >= PGA (see previous comment)
        if get_pga_site:
            idx = mean < np.log(pga_site)
            mean[idx] = np.log(pga_site[idx])

        stddevs = self._get_stddevs(C,
                                    sites,
                                    pga1100,
                                    C_PGA['s_lny'],
                                    stddev_types)
        return mean, stddevs

    def _compute_imt1100(self, C, sites, rup, dists, get_pga_site=False):
        """
        Computes the PGA on reference (Vs30 = 1100 m/s) rock.
        """
        # Calculates simple site response term assuming all sites 1100 m/s
        fsite = (C['c10'] + (C['k2'] * C['n'])) * log(1100. / C['k1'])
        # Calculates the PGA on rock
        pga1100 = np.exp(self._compute_magnitude_term(C, rup.mag) +
                         self._compute_distance_term(C, rup, dists) +
                         self._compute_style_of_faulting_term(C, rup) +
                         self._compute_hanging_wall_term(C, rup, dists) +
                         self._compute_basin_response_term(C, sites.z2pt5) +
                         fsite)
        # If PGA at the site is needed then remove factor for rock and
        # re-calculate on correct site condition
        if get_pga_site:
            pga_site = np.exp(np.log(pga1100) - fsite)
            fsite = self._compute_shallow_site_response(C, sites, pga1100)
            pga_site = np.exp(np.log(pga_site) + fsite)
        else:
            pga_site = None
        return pga1100, pga_site

    def _compute_magnitude_term(self, C, mag):
        """
        Returns the magnitude scaling factor (equation (2), page 144)
        """
        fmag = C['c0'] + C['c1'] * mag
        if mag <= 5.5:
            return fmag
        elif mag > 6.5:
            return fmag + (C['c2'] * (mag - 5.5)) + (C['c3'] * (mag - 6.5))
        else:
            return fmag + (C['c2'] * (mag - 5.5))

    def _compute_distance_term(self, C, rup, dists):
        """
        Returns the distance scaling factor (equation (3), page 145)
        """
        return (C['c4'] + C['c5'] * rup.mag) * \
            np.log(np.sqrt(dists.rrup ** 2. + C['c6'] ** 2.))

    def _compute_style_of_faulting_term(self, C, rup):
        """
        Returns the style of faulting factor, depending on the mechanism (rake)
        and top of rupture depth (equations (4) and (5), pages 145 - 146)
        """
        frv, fnm = self._get_fault_type_dummy_variables(rup.rake)

        if frv > 0.:
            # Top of rupture depth term only applies to reverse faults
            if rup.ztor < 1.:
                ffltz = rup.ztor
            else:
                ffltz = 1.
        else:
            ffltz = 0.
        return (C['c7'] * frv * ffltz) + (C['c8'] * fnm)

    def _get_fault_type_dummy_variables(self, rake):
        """
        Returns the coefficients FRV and FNM, describing if the rupture is
        reverse (FRV = 1.0, FNM = 0.0), normal (FRV = 0.0, FNM = 1.0) or
        strike-slip/oblique-slip (FRV = 0.0, FNM = 0.0). Reverse faults are
        classified as those with a rake in the range 30 to 150 degrees. Normal
        faults are classified as having a rake in the range -150 to -30 degrees
        :returns:
            FRV, FNM
        """
        if (rake > 30.0) and (rake < 150.):
            return 1., 0.
        elif (rake > -150.0) and (rake < -30.0):
            return 0., 1.
        else:
            return 0., 0.

    def _compute_hanging_wall_term(self, C, rup, dists):
        """
        Returns the hanging wall scaling term, the product of the scaling
        coefficient and four separate scaling terms for distance, magnitude,
        rupture depth and dip (equations 6 - 10, page 146). Individual
        scaling terms defined in separate functions
        """
        return (C['c9'] *
                self._get_hanging_wall_distance_term(dists, rup.ztor) *
                self._get_hanging_wall_magnitude_term(rup.mag) *
                self._get_hanging_wall_depth_term(rup.ztor) *
                self._get_hanging_wall_dip_term(rup.dip))

    def _get_hanging_wall_distance_term(self, dists, ztor):
        """
        Returns the hanging wall distance scaling term (equation 7, page 146)
        """
        fhngr = np.ones_like(dists.rjb, dtype=float)
        idx = dists.rjb > 0.
        if ztor < 1.:
            temp_rjb = np.sqrt(dists.rjb[idx] ** 2. + 1.)
            r_max = np.max(np.column_stack([dists.rrup[idx], temp_rjb]),
                           axis=1)
            fhngr[idx] = (r_max - dists.rjb[idx]) / r_max
        else:
            fhngr[idx] = (dists.rrup[idx] - dists.rjb[idx]) / dists.rrup[idx]
        return fhngr

    def _get_hanging_wall_magnitude_term(self, mag):
        """
        Returns the hanging wall magnitude scaling term (equation 8, page 146)
        """
        if mag <= 6.0:
            return 0.
        elif mag >= 6.5:
            return 1.
        else:
            return 2. * (mag - 6.0)

    def _get_hanging_wall_depth_term(self, ztor):
        """
        Returns the hanging wall depth scaling term (equation 9, page 146)
        """
        if ztor >= 20.0:
            return 0.
        else:
            return (20. - ztor) / 20.0

    def _get_hanging_wall_dip_term(self, dip):
        """
        Returns the hanging wall dip scaling term (equation 10, page 146)
        """
        if dip > 70.0:
            return (90.0 - dip) / 20.0
        else:
            return 1.0

    def _compute_shallow_site_response(self, C, sites, pga1100):
        """
        Returns the shallow site response term (equation 11, page 146)
        """
        stiff_factor = C['c10'] + (C['k2'] * C['n'])
        # Initially default all sites to intermediate rock value
        fsite = stiff_factor * np.log(sites.vs30 / C['k1'])
        # Check for soft soil sites
        idx = sites.vs30 < C['k1']
        if np.any(idx):
            pga_scale = np.log(pga1100[idx] +
                               (C['c'] * ((sites.vs30[idx] / C['k1']) **
                                C['n']))) - np.log(pga1100[idx] + C['c'])
            fsite[idx] = C['c10'] * np.log(sites.vs30[idx] / C['k1']) + \
                (C['k2'] * pga_scale)
        # Any very hard rock sites are rendered to the constant amplification
        # factor
        idx = sites.vs30 >= 1100.
        if np.any(idx):
            fsite[idx] = stiff_factor * log(1100. / C['k1'])

        return fsite

    def _compute_basin_response_term(self, C, z2pt5):
        """
        Returns the basin response term (equation 12, page 146)
        """
        fsed = np.zeros_like(z2pt5, dtype=float)
        idx = z2pt5 < 1.0
        if np.any(idx):
            fsed[idx] = C['c11'] * (z2pt5[idx] - 1.0)

        idx = z2pt5 > 3.0
        if np.any(idx):
            fsed[idx] = (C['c12'] * C['k3'] * exp(-0.75)) *\
                (1.0 - np.exp(-0.25 * (z2pt5[idx] - 3.0)))
        return fsed

    def _get_stddevs(self, C, sites, pga1100, sigma_pga, stddev_types):
        """
        Returns the standard deviations as described in the "ALEATORY
        UNCERTAINTY MODEL" section of the paper. Equations 13 to 19, pages 147
        to 151
        """
        std_intra = self._compute_intra_event_std(C,
                                                  sites.vs30,
                                                  pga1100,
                                                  sigma_pga)

        std_inter = C['t_lny'] * np.ones_like(sites.vs30)
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(self._get_total_sigma(C, std_intra, std_inter))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(std_intra)
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(std_inter)
        return stddevs

    def _compute_intra_event_std(self, C, vs30, pga1100, sigma_pga):
        """
        Returns the intra-event standard deviation at the site, as defined in
        equation 15, page 147
        """
        # Get intra-event standard deviation at the base of the site profile
        sig_lnyb = np.sqrt(C['s_lny'] ** 2. - C['s_lnAF'] ** 2.)
        sig_lnab = np.sqrt(sigma_pga ** 2. - C['s_lnAF'] ** 2.)
        # Get linearised relationship between f_site and ln PGA
        alpha = self._compute_intra_event_alpha(C, vs30, pga1100)

        return np.sqrt(
            (sig_lnyb ** 2.) +
            (C['s_lnAF'] ** 2.) +
            ((alpha ** 2.) * (sig_lnab ** 2.)) +
            (2.0 * alpha * C['rho'] * sig_lnyb * sig_lnab))

    def _compute_intra_event_alpha(self, C, vs30, pga1100):
        """
        Returns the linearised functional relationship between fsite and
        pga1100, determined from the partial derivative defined on equation 17
        on page 148
        """
        alpha = np.zeros_like(vs30, dtype=float)
        idx = vs30 < C['k1']
        if np.any(idx):
            temp1 = (pga1100[idx] +
                     C['c'] * (vs30[idx] / C['k1']) ** C['n']) ** -1.
            temp1 = temp1 - ((pga1100[idx] + C['c']) ** -1.)
            alpha[idx] = C['k2'] * pga1100[idx] * temp1

        return alpha

    def _get_total_sigma(self, C, std_intra, std_inter):
        """
        Returns the total sigma term as defined by equation 16, page 147
        This method is defined here as the Campbell & Bozorgnia (2008) model
        can also be applied to the "arbitrary" horizontal component
        definition, in which case the total sigma is modified.
        """
        return np.sqrt(std_intra ** 2. + std_inter ** 2.)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
      imt      c0     c1      c2      c3      c4    c5    c6     c7      c8     c9     c10    c11   c12    k1      k2     k3     c     n  s_lny  t_lny s_lnAF  c_lny    rho
      cav  -4.354  0.942  -0.178  -0.346  -1.309 0.087  7.24  0.111  -0.108  0.362   2.549  0.090  1.277  400  -2.690  1.000  1.88  1.18  0.371  0.196  0.300  0.089  0.735
      pgd  -5.270  1.600  -0.070   0.000  -2.000  0.17  4.00  0.000   0.000  0.000  -0.820  0.300  1.000  400   0.000  2.744  1.88  1.18  0.667  0.485  0.300  0.290  0.174
      pgv   0.954  0.696  -0.309  -0.019  -2.016  0.17  4.00  0.245   0.000  0.358   1.694  0.092  1.000  400  -1.955  1.929  1.88  1.18  0.484  0.203  0.300  0.190  0.691
      pga  -1.715  0.500  -0.530  -0.262  -2.118  0.17  5.60  0.280  -0.120  0.490   1.058  0.040  0.610  865  -1.186  1.839  1.88  1.18  0.478  0.219  0.300  0.166  1.000
    0.010  -1.715  0.500  -0.530  -0.262  -2.118  0.17  5.60  0.280  -0.120  0.490   1.058  0.040  0.610  865  -1.186  1.839  1.88  1.18  0.478  0.219  0.300  0.166  1.000
    0.020  -1.680  0.500  -0.530  -0.262  -2.123  0.17  5.60  0.280  -0.120  0.490   1.102  0.040  0.610  865  -1.219  1.840  1.88  1.18  0.480  0.219  0.300  0.166  0.999
    0.030  -1.552  0.500  -0.530  -0.262  -2.145  0.17  5.60  0.280  -0.120  0.490   1.174  0.040  0.610  908  -1.273  1.841  1.88  1.18  0.489  0.235  0.300  0.165  0.989
    0.050  -1.209  0.500  -0.530  -0.267  -2.199  0.17  5.74  0.280  -0.120  0.490   1.272  0.040  0.610 1054  -1.346  1.843  1.88  1.18  0.510  0.258  0.300  0.162  0.963
    0.075  -0.657  0.500  -0.530  -0.302  -2.277  0.17  7.09  0.280  -0.120  0.490   1.438  0.040  0.610 1086  -1.471  1.845  1.88  1.18  0.520  0.292  0.300  0.158  0.922
    0.100  -0.314  0.500  -0.530  -0.324  -2.318  0.17  8.05  0.280  -0.099  0.490   1.604  0.040  0.610 1032  -1.624  1.847  1.88  1.18  0.531  0.286  0.300  0.170  0.898
    0.150  -0.133  0.500  -0.530  -0.339  -2.309  0.17  8.79  0.280  -0.048  0.490   1.928  0.040  0.610  878  -1.931  1.852  1.88  1.18  0.532  0.280  0.300  0.180  0.890
    0.200  -0.486  0.500  -0.446  -0.398  -2.220  0.17  7.60  0.280  -0.012  0.490   2.194  0.040  0.610  748  -2.188  1.856  1.88  1.18  0.534  0.249  0.300  0.186  0.871
    0.250  -0.890  0.500  -0.362  -0.458  -2.146  0.17  6.58  0.280   0.000  0.490   2.351  0.040  0.700  654  -2.381  1.861  1.88  1.18  0.534  0.240  0.300  0.191  0.852
    0.300  -1.171  0.500  -0.294  -0.511  -2.095  0.17  6.04  0.280   0.000  0.490   2.460  0.040  0.750  587  -2.518  1.865  1.88  1.18  0.544  0.215  0.300  0.198  0.831
    0.400  -1.466  0.500  -0.186  -0.592  -2.066  0.17  5.30  0.280   0.000  0.490   2.587  0.040  0.850  503  -2.657  1.874  1.88  1.18  0.541  0.217  0.300  0.206  0.785
    0.500  -2.569  0.656  -0.304  -0.536  -2.041  0.17  4.73  0.280   0.000  0.490   2.544  0.040  0.883  457  -2.669  1.883  1.88  1.18  0.550  0.214  0.300  0.208  0.735
    0.750  -4.844  0.972  -0.578  -0.406  -2.000  0.17  4.00  0.280   0.000  0.490   2.133  0.077  1.000  410  -2.401  1.906  1.88  1.18  0.568  0.227  0.300  0.221  0.628
    1.000  -6.406  1.196  -0.772  -0.314  -2.000  0.17  4.00  0.255   0.000  0.490   1.571  0.150  1.000  400  -1.955  1.929  1.88  1.18  0.568  0.255  0.300  0.225  0.534
    1.500  -8.692  1.513  -1.046  -0.185  -2.000  0.17  4.00  0.161   0.000  0.490   0.406  0.253  1.000  400  -1.025  1.974  1.88  1.18  0.564  0.296  0.300  0.222  0.411
    2.000  -9.701  1.600  -0.978  -0.236  -2.000  0.17  4.00  0.094   0.000  0.371  -0.456  0.300  1.000  400  -0.299  2.019  1.88  1.18  0.571  0.296  0.300  0.226  0.331
    3.000 -10.556  1.600  -0.638  -0.491  -2.000  0.17  4.00  0.000   0.000  0.154  -0.820  0.300  1.000  400   0.000  2.110  1.88  1.18  0.558  0.326  0.300  0.229  0.289
    4.000 -11.212  1.600  -0.316  -0.770  -2.000  0.17  4.00  0.000   0.000  0.000  -0.820  0.300  1.000  400   0.000  2.200  1.88  1.18  0.576  0.297  0.300  0.237  0.261
    5.000 -11.684  1.600  -0.070  -0.986  -2.000  0.17  4.00  0.000   0.000  0.000  -0.820  0.300  1.000  400   0.000  2.291  1.88  1.18  0.601  0.359  0.300  0.237  0.200
    7.500 -12.505  1.600  -0.070  -0.656  -2.000  0.17  4.00  0.000   0.000  0.000  -0.820  0.300  1.000  400   0.000  2.517  1.88  1.18  0.628  0.428  0.300  0.271  0.174
    10.00 -13.087  1.600  -0.070  -0.422  -2.000  0.17  4.00  0.000   0.000  0.000  -0.820  0.300  1.000  400   0.000  2.744  1.88  1.18  0.667  0.485  0.300  0.290  0.174
    """)


class CampbellBozorgnia2008Arbitrary(CampbellBozorgnia2008):
    """
    Implements the Campbell & Bozorgnia (2008) GMPE as modified to represent
    the arbitrary horizontal component of ground motion, instead of the
    Rotationally Independent Geometric Mean (GMRotI) originally defined in
    the paper.
    """

    #: Supported intensity measure component is arbitrary horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    def _get_total_sigma(self, C, std_intra, std_inter):
        """
        Returns the total sigma term for the arbitrary horizontal component of
        ground motion defined by equation 18, page 150
        """
        return np.sqrt(std_intra ** 2. + std_inter ** 2. + C['c_lny'] ** 2.)
