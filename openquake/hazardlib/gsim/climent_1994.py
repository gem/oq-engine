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
Module exports :class:'ClimentEtAl1994'.
"""
import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g


from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class ClimentEtAl1994(GMPE):
    """
    Implements GMPE developed by Climent, A, W. Taylor, M. Ciudad Real,
    W. Strauch, M. Villagran, A. Dahle, and H. Bungum. Published as a
    NORSAR report: "Spectral strong motion attenuation in Central Ame-
    rica", NORSAR Technical Report No. 2-17, 46 pp.
    The original formulation predict PGA (m/s*s) and 5% damped PSV (m/s)
    for the largest component of horizontal ground motion.
    In this implementation:
    Spectral acceleration (SA) values are obtained from PSV ones using
    the following formula :

        SA = [PSV * (2 * pi/ T)]/ratio(SA_larger/SA_geo_mean)
        StdDev.TOTAL=StdDev.TOTAL/sd_ratio(SA_larger/SA_geo_mean)

    The ratio() and sd_ratio() from Beyer and Bommer(2006)
    """
    #: Supported tectonic region type is active shallow crust and/or
    #: interface subduction the authors did not distinction between shallow
    #: and sudbdution events (see topic 5.3 "Shallow crustal vs.subduction
    #: events, pag. 32).
    #: Any factor/parameter is used in the formulation to discriminate between
    #: shallow or interface tectonic regime, here this GMPE is implemented
    #: for active_shallow_crust only
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration. See Table 2 in page 1865
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the largest component of
    #: two horizontal components
    #: :attr:`openquake.hazardlib.const.IMC.GREATER_OF_TWO_HORIZONTAL`,
    #: see paragraph before table on Summary, page 1.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation types is total.
    #: See equation 1 on the Summary and Table 4.1, page 22.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: Required site parameters. The GMPE was developed for rock and soil
    #: site conditions. The parameter S in eq. 1 (see Summary) define the
    #: soil condition: S=0 for rock, S=1 for soil.
    #: Here we use the Vs30=760 as limit between the two soil conditions
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is Rhypo, explained in page 1(eq. 1)
    REQUIRES_DISTANCES = set(('rhypo',))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]

        mean = self._compute_mean(C, rup, dists, sites, imt)

        stddevs = self._get_stddevs(C, stddev_types, sites.vs30.shape[0])

        return mean, stddevs

    def _compute_term_1_2(self, rup, C):
        """
        Compute terms 1 and 2 in equation 1 page 1.
        """
        return C['c1'] + C['c2'] * rup.mag

    def _compute_term_3_4(self, dists, C):
        """
        Compute term 3 and 4 in equation 1 page 1.
        """
        cutoff = 6.056877878
        rhypo = dists.rhypo.copy()
        rhypo[rhypo <= cutoff] = cutoff
        return C['c3'] * np.log(rhypo) + C['c4'] * rhypo

    def _get_site_amplification(self, sites, imt, C):
        """
        Compute the fith term of the equation (1), p. 1:
        ``c5 * S``
        """
        S = self._get_site_type_dummy_variables(sites)
        return (C['c5'] * S)

    def _get_site_type_dummy_variables(self, sites):
        """
        Get site type dummy variables, ``S`` (for rock and soil sites)
        """
        S = np.zeros_like(sites.vs30)
        # S=0 for rock sites, S=1 otherwise pag 1.
        idxS = (sites.vs30 < 760.0)
        S[idxS] = 1
        return S

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return total standard deviation.
        """
        stddevs = []
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        stddevs = [np.zeros(num_sites) + C['SigmaB'] / C['r_std']
                   for _ in stddev_types]
        return stddevs

    def _compute_mean(self, C, rup, dists, sites, imt):
        """
        Compute mean value for PGA and pseudo-velocity response spectrum,
        as given in equation 1. Converts also pseudo-velocity response
        spectrum values to SA, using:

          SA = (PSV * W)/ratio(SA_larger/SA_geo_mean)
           W = (2 * pi / T)
           T = period (sec)
        """

        mean = (self._compute_term_1_2(rup, C) +
                self._compute_term_3_4(dists, C) +
                self._get_site_amplification(sites, imt, C))

        # convert from m/s**2 to g for PGA and from m/s to g for PSV
        # and divided this value for the ratio(SA_larger/SA_geo_mean)
        if imt.name == "PGA":
            mean = (np.exp(mean) / g) / C['r_SA']
        else:
            W = (2. * np.pi)/imt.period
            mean = ((np.exp(mean) * W) / g) / C['r_SA']
        return np.log(mean)

    #: Equation coefficients, described in Table 4.1 on pp. 22
    #: the original imt values are defined as frequencies values
    #: the sigma_ls was excluded
    COEFFS = CoeffsTable(sa_damping=5, table="""\
     IMT     c1      c2       c3       c4       c5      SigmaB r_SA    r_std
     pga    -1.6870  0.5530  -0.5370  -0.00302  0.3270  0.750  1.1000  1.0200
     0.025  -7.2140  0.5530  -0.5370  -0.00302  0.3270  0.750  1.1000  1.0200
     0.050  -5.4870  0.4470  -0.5500  -0.00246  0.3090  0.780  1.1000  1.0200
     0.100  -4.7260  0.4830  -0.5810  -0.00199  0.3810  0.800  1.2020  1.0200
     0.200  -4.8760  0.6420  -0.6420  -0.00156  0.4700  0.820  1.2040  1.0200
     0.500  -5.8620  0.9170  -0.7260  -0.00107  0.5660  0.820  1.2100  1.0200
     1.000  -6.7440  1.0810  -0.7560  -0.00077  0.5880  0.820  1.2200  1.0200
     2.000  -7.3480  1.1280  -0.7280  -0.00053  0.5360  0.790  1.2400  1.0200
     4.000  -7.4410  1.0070  -0.6010  -0.00040  0.4960  0.730  1.2800  1.0200
    """)
