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

        # get mean and std using the superclass
        mean, stddevs = super(BooreAtkinson2011, self).get_mean_and_stddevs(
            sites, rup, dists, imt, stddev_types)

        # correction factor (see Atkinson and Boore, 2011; equation 5 at
        # page 1126 and nga08_gm_tmr.for line 508
        corr_fact = 10.0**(np.max([0, 3.888 - 0.674 * rup.mag]) -
                           (np.max([0, 2.933 - 0.510 * rup.mag]) *
                            np.log10(dists.rjb + 10.)))

        return np.log(np.exp(mean)*corr_fact), stddevs
