# The Hazard Library
# Copyright (C) 2014 GEM Foundation
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
Module exports :class:`BooreAtkinson2011`.
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.imt import PGA


class BooreAtkinson2011(BooreAtkinson2008):
    """
    Implements GMPE based on the corrections proposed by Gail M. Atkinson
    and D. Boore in 2011 and published as "Modifications to Existing
    Ground-Motion Prediction Equations in Light of New Data " (2011,
    Bulletin of the Seismological Society of America, Volume 101, No. 3,
    pages 1121-1135).
    """

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

        # correction factor (see Atkinson and Boore, 2011; equation 5 at
        # page 1126 and nga08_gm_tmr.for line 508

        """
        corr_fact = 10.0**(np.max([0, 3.888 - 0.674 * rup.mag]) -
                           (np.max([0, 2.933 - 0.510 * rup.mag]) *
                            np.log(dists.rjb + 10.)))
        """
        corr_fact = 1

        # equation 1, pag 106, without sigma term, that is only the first 3
        # terms. The third term (site amplification) is computed as given in
        # equation (6), that is the sum of a linear term - equation (7) - and
        # a non-linear one - equations (8a) to (8c).
        # Mref, Rref values are given in the caption to table 6, pag 119.
        if imt == PGA():
            # avoid recomputing PGA on rock, just add site terms
            mean = np.log(pga4nl) + \
                self._get_site_amplification_linear(sites, C_SR) + \
                self._get_site_amplification_non_linear(sites, pga4nl, C_SR)
        else:
            mean = self._compute_magnitude_scaling(rup, C) + \
                self._compute_distance_scaling(rup, dists, C) + \
                self._get_site_amplification_linear(sites, C_SR) + \
                self._get_site_amplification_non_linear(sites, pga4nl, C_SR)

        stddevs = self._get_stddevs(C, stddev_types, num_sites=len(sites.vs30))

        return mean*corr_fact, stddevs
