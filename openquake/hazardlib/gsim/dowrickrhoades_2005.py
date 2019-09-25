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
Module exports :class:`DowrickRhoades2005Asc`,:class:`DowrickRhoades2005SInter`
:class:`DowrickRhoades2005SSlab`, and :class:`DowrickRhoades2005Volc`.
"""
import numpy as np
from openquake.hazardlib.gsim.base import IPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import MMI


class DowrickRhoades2005Asc(IPE):
    """
    Implements IPE developed by D.J. Dowrick and D.A. Rhoades published as
    "Revised models for attenuation of Modified Mercalli Intensity in
    New Zealand earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.38,
    no. 4, p. 185-214, December 2005.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/38(4)0185.pdf
    Last accessed 20 November 2015.

    This class implements the IPE for Active Shallow Crust for different
    faulting types.
    """

    #: Supported tectonic region type for base class is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure type is MMI.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([MMI])

    #: Supported intensity measure component is the horizontal component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation types are Inter, Intra and Total
    # (see description in paragraph 5.2 page 200 )
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: The only site parameter is vs30 used to map to site class to distinguish
    # between rock, stiff soil and soft soil
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude, and rake and hypocentral
    # depth rake is for determining fault style flags. Hypo depth is for
    # subduction GMPEs
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake', 'hypo_depth'))

    #: Required distance measure is rrup (paragraphy x, page xx) which is
    # defined as nearest distance to the source.
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        # extract dictionaries of coefficients specific to required
        # intensity measure type
        C = self.COEFFS[imt]

        # Deltas for Tectonic Region Type and rake angles
        delta_R, delta_S, delta_V, delta_I = self._get_deltas(rup.rake)

        mean = self._compute_mean(C, rup.mag, dists.rrup, rup.hypo_depth,
                                  delta_R, delta_S, delta_V, delta_I,
                                  sites.vs30)

        stddevs = self._get_stddevs(C, stddev_types, sites.vs30.size)

        return mean, stddevs

    def _compute_mean(self, C, mag, rrup, hypo_depth, delta_R, delta_S,
                      delta_V, delta_I, vs30):

        """
        Compute MMI Intensity Value as per Equation in Table 5 and
        Table 7 pag 198.
        """
        # mean is calculated for all the 4 classes using the same equation.
        # For DowrickRhoades2005SSlab, the coefficients which don't appear in
        # Model 3 equationare assigned to zero

        mean = (C['A1'] + (C['A2'] + C['A2R'] * delta_R + C['A2V'] * delta_V) *
                mag + (C['A3'] + C['A3S'] * delta_S + C['A3V'] * delta_V) *
                np.log10(np.power((rrup**3 + C['d']**3), 1.0 / 3.0)) +
                C['A4'] * hypo_depth + C['A5'] * delta_I)

        # Get S site class term
        S = self._get_site_class(vs30, mean)

        # Add S amplification term to mean value
        mean = mean + S

        return mean

    def _get_stddevs(self, C, stddev_types, num_sites):

        """
        Return total standard deviation as described in paragraph 5.2 pag 200.
        """

        # interevent stddev
        sigma_inter = C['tau'] + np.zeros(num_sites)
        # intraevent std
        sigma_intra = C['sigma'] + np.zeros(num_sites)
        std = []

        for stddev_type in stddev_types:
            if stddev_type == const.StdDev.TOTAL:
                # equation in section 5.2 page 200
                std += [np.sqrt(sigma_intra**2 + sigma_inter**2)]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                std.append(sigma_intra)
            elif stddev_type == const.StdDev.INTER_EVENT:
                std.append(sigma_inter)

        return std

    def _get_site_class(self, vs30, mmi_mean):
        """
        Return site class flag for:
        Class E - Very Soft Soil        vs30 < 180
        Class D - Deep or Soft Soil     vs30 >= 180 and vs30 <= 360
        Class C - Shallow Soil          vs30 > 360 and vs30 <= 760
        Class B - Rock                  vs30 > 760 and vs30 <= 1500
        Class A - Strong Rock           vs30 >= 180 and vs30 <= 360
        The S site class is equal to
            S = c1 if MMI <= 7
            S = c1 - d *(MMI - 7.0) if 7<MMI<9.5
            S = c2 if MMI >= 9.5
        """

        if vs30[0] < 180:
            c1 = 1.0
            c2 = -0.25
            d = 0.5
        elif vs30[0] >= 180 and vs30[0] <= 360:
            c1 = 0.5
            c2 = -0.125
            d = 0.25
        elif vs30[0] > 360 and vs30[0] <= 760:
            c1 = 0.
            c2 = 0.
            d = 0.
        elif vs30[0] > 760 and vs30[0] <= 1500:
            c1 = -0.5
            c2 = 0.125
            d = -0.25
        elif vs30[0] > 1500:
            c1 = -1.0
            c2 = 0.25
            d = -0.5

        S = np.zeros_like(vs30)

        for i in range(vs30.size):
            if mmi_mean[i] <= 7.0:
                S[i] += c1
            elif mmi_mean[i] > 7 and mmi_mean[i] < 9.5:
                S[i] += c1 - d * (mmi_mean[i] - 7.0)
            else:
                S[i] += c2

        return S

    def _get_deltas(self, rake):
        """
        Return the value of deltas (delta_R, delta_S, delta_V, delta_I),
        as defined in "Table 5: Model 1" pag 198
        """
        # delta_R = 1 for reverse focal mechanism (45<rake<135)
        # and for interface events, 0 for all other events
        # delta_S = 1 for Strike-slip focal mechanisms (0<=rake<=45) or
        # (135<=rake<=180) or (-45<=rake<=0), 0 for all other events
        # delta_V = 1 for TVZ events, 0 for all other events
        # delta_I = 1 for interface events, 0 for all other events

        # All deltas = 0 for Model 3: Deep Region, pag 198

        delta_R, delta_S = 0, 0
        delta_V, delta_I = 0, 0

        if rake > 45.0 and rake < 135.0:
            delta_R = 1

        if (rake >= 0.0 and rake <= 45.0) or \
           (rake >= 135 and rake <= 180.0) or \
           (rake >= -180.0 and rake <= -135.0) or \
           (rake >= -45.0 and rake < 0.0):
            delta_S = 1

        return delta_R, delta_S, delta_V, delta_I

    #: Coefficient table (table 5, page 198)
    COEFFS = CoeffsTable(table="""\
    IMT  A1   A2   A2R   A2V   A3     A3S   A3V   A4    A5    d     tau  sigma
    MMI  4.74 1.23 0.042 0.292 -3.613 0.100 -1.76 0.007 -0.42 10.28 0.21  0.38
     """)


class DowrickRhoades2005SInter(DowrickRhoades2005Asc):
    """
    Implements IPE developed by D.J. Dowrick and D.A. Rhoades  published as
    "Revised models for attenuation of Modified Mercalli Intensity in
    New Zealand earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.38,
    no. 4, p. 185-214, December 2005.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/38(4)0185.pdf
    Last accessed 20 November 2015.

    This class implements the IPE for Subduction Interface events
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    def _get_deltas(self, rake):
        """
        Return the value of deltas (delta_R, delta_S, delta_V, delta_I),
        as defined in "Table 5: Model 1" pag 198
        """
        # delta_I = 1, delta_R = 1 for interface events
        # delta_S = 0, delta_V = 0

        delta_R, delta_S = 1, 0
        delta_V, delta_I = 0, 1

        return delta_R, delta_S, delta_V, delta_I


class DowrickRhoades2005SSlab(DowrickRhoades2005Asc):
    """
    Implements IPE developed by D.J. Dowrick and D.A. Rhoades  published as
    "Revised models for attenuation of Modified Mercalli Intensity in
    New Zealand earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.38,
    no. 4, p. 185-214, December 2005.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/38(4)0185.pdf
    Last accessed 20 November 2015.

    This class implements the IPE for Subduction Slab events
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    def _get_deltas(self, rake):
        """
        Return the value of deltas (delta_R, delta_S, delta_V, delta_I),
        as defined in "Table 5: Model 1" pag 198
        """
        # All deltas = 0 for DowrickRhoades2005SSlab Model 3: Deep Region,
        # pag 198

        delta_R, delta_S = 0, 0
        delta_V, delta_I = 0, 0

        return delta_R, delta_S, delta_V, delta_I

    #: Coefficient table (table 7, page 198)
    COEFFS = CoeffsTable(table="""\
    IMT  A1   A2   A2R  A2V  A3    A3S  A3V  A4      A5   d   tau  sigma
    MMI  3.76 1.48 0.0  0.0  -3.50 0.0  0.0  0.0031  0.0  0.0 0.27  0.42
        """)


class DowrickRhoades2005Volc(DowrickRhoades2005Asc):
    """
    Implements IPE developed by D.J. Dowrick and D.A. Rhoades  published as
    "Revised models for attenuation of Modified Mercalli Intensity in
    New Zealand earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.38,
    no. 4, p. 185-214, December 2005.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/38(4)0185.pdf
    Last accessed 20 November 2015.

    This class implements the IPE for events with a volcanic source
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    def _get_deltas(self, rake):
        """
        Return the value of deltas (delta_R, delta_S, delta_V, delta_I),
        as defined in "Table 5: Model 1" pag 198
        """
        # delta_V = 1 for TVZ events, 0 for all other events
        # delta_R =0, delta_S = 0, delta_I = 0

        delta_R, delta_S = 0, 0
        delta_V, delta_I = 1, 0

        return delta_R, delta_S, delta_V, delta_I
