# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Module exports :class:`AkkarCagnan2010`.
"""
from __future__ import division

import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g

from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class AkkarCagnan2010(BooreAtkinson2008):
    """
    Implements GMPE developed by Sinnan Akkar and Zehra Cagnan and
    published as "A Local Ground-Motion Predictive Model for Turkey,
    and Its Comparison with Other Regional and Global Ground-Motion
    Models" (2010, Bulletin of the Seismological Society of America,
    Volume 100, No. 6, pages 2978-2995). It extends
    :class:`openquake.hazardlib.gsim.boore_atkinson_2008.BooreAtkinson2008`
    because the linear and non-linear site effects are described by
    the same site response function used in Boore and Atkinson 2008.
    """
    #: Supported tectonic region type is active shallow crust (the
    #: equations being developed for Turkey, see paragraph 'Strong Motion
    #: Databank', p. 2981)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration, see paragraph
    # 'Functional Form', p. 2981
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is geometric mean
    #: of two horizontal components :
    #: attr:`~openquake.hazardlib.const.IMC.AVERAGE_HORIZONTAL`, see paragraph
    #: 'Functional Form', p. 2981.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see Table 3, p. 2985.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters is Vs30.
    #: See paragraph 'Functionl Form', p. 2981.
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude, and rake.
    #: See paragraph 'Functional Form', p. 2981.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake'))

    #: Required distance measure is Rjb.
    #: See paragraph 'Functional Form', p. 2981.
    REQUIRES_DISTANCES = set(('rjb', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients (for soil amplification)
        # specific to required intensity measure type
        C_SR = self.COEFFS_SOIL_RESPONSE[imt]

        # compute median PGA on rock (in g), needed to compute non-linear site
        # amplification
        C = self.COEFFS_AC10[PGA()]
        pga4nl = np.exp(
            self._compute_mean(C, rup.mag, dists.rjb, rup.rake)) * 1e-2 / g

        # compute full mean value by adding site amplification terms
        # (but avoiding recomputing mean on rock for PGA)
        if imt == PGA():
            mean = (np.log(pga4nl) +
                    self._get_site_amplification_linear(sites.vs30, C_SR) +
                    self._get_site_amplification_non_linear(sites.vs30, pga4nl,
                                                            C_SR))
        else:
            C = self.COEFFS_AC10[imt]
            mean = (self._compute_mean(C, rup.mag, dists.rjb, rup.rake) +
                    self._get_site_amplification_linear(sites.vs30, C_SR) +
                    self._get_site_amplification_non_linear(sites.vs30, pga4nl,
                                                            C_SR))

        # convert from cm/s**2 to g for SA (PGA is already computed in g)
        if isinstance(imt, SA):
            mean = np.log(np.exp(mean) * 1e-2 / g)

        stddevs = self._get_stddevs(C, stddev_types, num_sites=len(sites.vs30))

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations as defined in table 3, p. 2985.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                sigma_t = np.sqrt(C['sigma'] ** 2 + C['tau'] ** 2)
                stddevs.append(sigma_t + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C['sigma'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(num_sites))
        return stddevs

    def _compute_linear_magnitude_term(self, C, mag):
        """
        Compute and return second term in equations (1a)
        and (1b), pages 2981 and 2982, respectively.
        """
        if mag <= self.c1:
            # this is the second term in eq. (1a), p. 2981
            return C['a2'] * (mag - self.c1)
        else:
            # this is the second term in eq. (1b), p. 2982
            return C['a3'] * (mag - self.c1)

    def _compute_quadratic_magnitude_term(self, C, mag):
        """
        Compute and return third term in equations (1a)
        and (1b), pages 2981 and 2982, respectively.
        """
        return C['a4'] * (8.5 - mag) ** 2

    def _compute_logarithmic_distance_term(self, C, mag, rjb):
        """
        Compute and return fourth term in equations (1a)
        and (1b), pages 2981 and 2982, respectively.
        """
        return ((C['a5'] + C['a6'] * (mag - self.c1)) *
                np.log(np.sqrt(rjb ** 2 + C['a7'] ** 2)))

    def _compute_faulting_style_term(self, C, rake):
        """
        Compute and return fifth and sixth terms in equations (1a)
        and (1b), pages 2981 and 2982, respectively.
        """
        Fn = float(rake > -135.0 and rake < -45.0)
        Fr = float(rake > 45.0 and rake < 135.0)

        return C['a8'] * Fn + C['a9'] * Fr

    def _compute_mean(self, C, mag, rjb, rake):
        """
        Compute and return mean value without site conditions,
        that is equations (1a) and (1b), p.2981-2982.
        """
        mean = (C['a1'] +
                self._compute_linear_magnitude_term(C, mag) +
                self._compute_quadratic_magnitude_term(C, mag) +
                self._compute_logarithmic_distance_term(C, mag, rjb) +
                self._compute_faulting_style_term(C, rake))

        return mean

    # c1 is the reference magnitude, fixed to 6.5
    # see paragraph 'Functional Form', p. 2982
    c1 = 6.5

    #: Coefficient table (from Table 3, p. 2985)
    #: sigma is the 'intra-event' standard deviation,
    #: while tau is the 'inter-event' standard deviation
    COEFFS_AC10 = CoeffsTable(sa_damping=5, table="""\
    IMT   a1        a2     a3     a4       a5       a6       a7       a8       a9       sigma   tau
    pgv   5.60931  -0.513 -0.695 -0.25800 -0.90393  0.21576  5.57472 -0.10481  0.07791  0.6154  0.526
    pga   8.92418  -0.513 -0.695 -0.18555 -1.25594  0.18105  7.33617 -0.02125  0.01851  0.6527  0.5163
    0.03  8.85984  -0.513 -0.695 -0.17123 -1.25132  0.18421  7.46968 -0.0134   0.03512  0.6484  0.5148
    0.05  9.05262  -0.513 -0.695 -0.15516 -1.28796  0.1984   7.26552  0.02076  0.01484  0.6622  0.5049
    0.075 9.56670  -0.513 -0.695 -0.13840 -1.38817  0.20246  8.03646  0.07311  0.02492  0.6849  0.5144
    0.10  9.85606  -0.513 -0.695 -0.11563 -1.43846  0.21833  8.84202  0.11044 -0.00620  0.7001  0.5182
    0.15  10.43715 -0.513 -0.695 -0.17897 -1.46786  0.15588  9.39515  0.03555  0.19751  0.6958  0.549
    0.20  10.63516 -0.513 -0.695 -0.21034 -1.44625  0.11590  9.60868 -0.03536  0.18594  0.6963  0.5562
    0.25  10.12551 -0.513 -0.695 -0.25565 -1.27388  0.09426  7.54353 -0.10685  0.13574  0.7060  0.5585
    0.30  10.12745 -0.513 -0.695 -0.27020 -1.26899  0.08352  8.03144 -0.10685  0.13574  0.6718  0.5735
    0.40  9.47855  -0.513 -0.695 -0.30498 -1.09793  0.06082  6.24042 -0.11197  0.16555  0.6699  0.5857
    0.50  8.95147  -0.513 -0.695 -0.29877 -1.01703  0.09099  5.67936 -0.10118  0.23546  0.6455  0.5782
    0.75  8.10498  -0.513 -0.695 -0.3349  -0.84365  0.08647  4.93842 -0.0456   0.10993  0.6463  0.6168
    1.00  7.61737  -0.513 -0.695 -0.35366 -0.75840  0.09623  4.12590 -0.01936  0.19729  0.6485  0.6407
    1.50  7.20427  -0.513 -0.695 -0.39858 -0.70134  0.11219  3.46535 -0.02618  0.21977  0.6300  0.6751
    2.00  6.70845  -0.513 -0.695 -0.39528 -0.70766  0.12032  3.8822  -0.03215  0.20584  0.6243  0.6574
    """)
