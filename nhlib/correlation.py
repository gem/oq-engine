# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
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
Module :mod:`nhlib.correlation` define correlation models for spatially-\
distributed ground-shaking intensities.
"""
import numpy

from nhlib.imt import SA, PGA


class JB2009CorrelationModel(object):
    """
    "Correlation model for spatially distributed ground-motion intensities"
    by Nirmal Jayaram and Jack W. Baker. Published in Earthquake Engineering
    and Structural Dynamics 2009; 38, pages 1687-1708.

    :param vs30_clustering:
        Boolean value to indicate whether "Case 1" or "Case 2" from page 1700
        should be applied. ``True`` value means that Vs 30 values show or are
        expected to show clustering ("Case 2"), ``False`` means otherwise.
    """
    def __init__(self, vs30_clustering):
        self.vs30_clustering = vs30_clustering

    def get_correlation_matrix(self, distances, imt):
        """
        Calculate correlation matrix for a given sites collection.

        Correlation depends on spectral period, Vs 30 clustering behaviour
        and distance between sites.

        :param distances:
            Numpy square matrix of mutual distances between
            sites in km (like the one returned from
            :meth:`nhlib.geo.mesh.Mesh.get_distance_matrix`)
        :param imt:
            Intensity measure type object, an instance of either
            of :class:`nhlib.imt.SA` or :class:`nhlib.imt.PGA`.
        :returns:
            Square matrix of the same rank as ``distances`` with
            correlation data (values between 0 and 1).
        """
        if isinstance(imt, SA):
            period = imt.period
        else:
            assert isinstance(imt, PGA)
            period = 0

        # formulae are from page 1700
        if period < 1:
            if not self.vs30_clustering:
                # case 1, eq. (17)
                b = 8.5 + 17.2 * period
            else:
                # case 2, eq. (18)
                b = 40.7 - 15.0 * period
        else:
            # both cases, eq. (19)
            b = 22.0 + 3.7 * period

        # eq. (20)
        return numpy.exp((- 3.0 / b) * distances)
