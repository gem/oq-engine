# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
Module exports :class:'FukushimaTanaka1990' and :class:
'FukushimaTanakaSite1990'
"""
from __future__ import division
import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g


from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA


class FukushimaTanaka1990(GMPE):
    """
    Implements the PGA GMPE of Fukushima and Tanaka (1990)
    Fukushima, Y. and Tanaka, T. (1990) A New Attenuation Relation for Peak
    Horizontal Acceleration of Strong Earthquake Ground Motion in Japan.
    Bulletin of the Seismological Society of America, 80(4), 757 - 783
    """
    #: The GMPE is derived from shallow earthquakes in California and Japan
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
    ])

    #: Supported intensity measure component is the average horizontal
    #: component
    #: :attr:`openquake.hazardlib.const.IMC.AVERAGE_HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: Required site parameters. The GMPE was developed for an ''average''
    #: site conditions. The authors specify that for rock sites the
    #: values should be lowered by 40 % and for soil site they should be
    #: raised by 40 %. For greatest consistencty the site condition is
    #: neglected currently but a site-dependent GMPE may be implemented
    #: inside a subclass.
    REQUIRES_SITES_PARAMETERS = set(())

    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is rupture distance
    REQUIRES_DISTANCES = set(('rrup',))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        C = self.COEFFS[imt]

        imean = (self._compute_magnitude_scaling(C, rup.mag) +
                 self._compute_distance_scaling(C, dists.rrup, rup.mag))
        # Original GMPE returns log10 acceleration in cm/s/s
        # Converts to natural logarithm of g
        mean = np.log((10.0 ** (imean - 2.0)) / g)
        istddevs = self._compute_stddevs(
            C, dists.rrup.shape, stddev_types
        )
        # Convert from common logarithm to natural logarithm
        stddevs = np.log(10 ** np.array(istddevs))
        return mean, stddevs

    def _compute_magnitude_scaling(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        return C["c1"] * mag + C["c5"]

    def _compute_distance_scaling(self, C, rrup, mag):
        """
        Returns the distance scaling term
        """
        rscale1 = rrup + C["c2"] * (10.0 ** (C["c3"] * mag))
        return -np.log10(rscale1) - (C["c4"] * rrup)

    def _compute_stddevs(self, C, num_sites, stddev_types):
        """
        Return total standard deviation.
        """
        std_total = C['sigma']

        stddevs = []
        for _ in stddev_types:
            stddevs.append(np.zeros(num_sites) + std_total)
        return stddevs

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     c1      c2     c3         c4    c5   sigma
    pga   0.41   0.032   0.41    0.0034  1.30    0.21
    """)


class FukushimaTanakaSite1990(FukushimaTanaka1990):
    """
    Implements the Fukushima and Tanaka (1990) model correcting for
    site class. The authors specify that the ground motions should
    be raised by 40 % on soft soil sites and reduced by 40 % on rock sites.
    The specific site classification is not known, so it is assumed that
    in this context "average" site conditions refer to NEHRP C, rock conditions
    to NEHRP A and B, and soft soil conditions to NEHRP D and E

    """
    #: Input sites as vs30 although only three classes considered
    REQUIRES_SITES_PARAMETERS = set(("vs30",))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        C = self.COEFFS[imt]

        imean = (self._compute_magnitude_scaling(C, rup.mag) +
                 self._compute_distance_scaling(C, dists.rrup, rup.mag))
        # Original GMPE returns log10 acceleration in cm/s/s
        # Converts to natural logarithm of g
        mean = np.log((10.0 ** (imean - 2.0)) / g)
        mean = self._compute_site_scaling(sites.vs30, mean)
        istddevs = self._compute_stddevs(
            C, dists.rrup.shape, stddev_types
        )
        # Convert from common logarithm to natural logarithm
        stddevs = np.log(10 ** np.array(istddevs))
        return mean, stddevs

    def _compute_site_scaling(self, vs30, mean):
        """
        Scales the ground motions by increasing 40 % on NEHRP class D/E sites,
        and decreasing by 40 % on NEHRP class A/B sites
        """
        site_factor = np.ones(len(vs30), dtype=float)
        idx = vs30 <= 360.
        site_factor[idx] = 1.4
        idx = vs30 > 760.0
        site_factor[idx] = 0.6
        return np.log(np.exp(mean) * site_factor)
