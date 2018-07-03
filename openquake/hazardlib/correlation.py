# The Hazard Library
# Copyright (C) 2012-2018 GEM Foundation
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
Module :mod:`openquake.hazardlib.correlation` defines correlation models for
spatially-distributed ground-shaking intensities.
"""
import abc
import numpy


class BaseCorrelationModel(metaclass=abc.ABCMeta):
    """
    Base class for correlation models for spatially-distributed ground-shaking
    intensities.
    """

    @abc.abstractmethod
    def get_lower_triangle_correlation_matrix(self, sites, imt):
        """
        Get lower-triangle matrix as a result of Cholesky-decomposition
        of correlation matrix.

        The resulting matrix should have zeros on values above
        the main diagonal.

        The actual implementations of :class:`BaseCorrelationModel` interface
        might calculate the matrix considering site collection and IMT (like
        :class:`JB2009CorrelationModel` does) or might have it pre-constructed
        for a specific site collection and IMT, in which case they will need
        to make sure that parameters to this function match parameters that
        were used to pre-calculate decomposed correlation matrix.

        :param sites:
            :class:`~openquake.hazardlib.site.SiteCollection` to create
            correlation matrix for.
        :param imt:
            Intensity measure type object, see :mod:`openquake.hazardlib.imt`.
        """

    def apply_correlation(self, sites, imt, residuals):
        """
        Apply correlation to randomly sampled residuals.

        :param sites:
            :class:`~openquake.hazardlib.site.SiteCollection` residuals were
            sampled for.
        :param imt:
            Intensity measure type object, see :mod:`openquake.hazardlib.imt`.
        :param residuals:
            2d numpy array of sampled residuals, where first dimension
            represents sites (the length as ``sites`` parameter) and
            second one represents different realizations (samples).
        :returns:
            Array of the same structure and semantics as ``residuals``
            but with correlations applied.

        NB: the correlation matrix is cached. It is computed only once
        per IMT for the complete site collection and then the portion
        corresponding to the sites is multiplied by the residuals.
        """
        # intra-event residual for a single relization is a product
        # of lower-triangle decomposed correlation matrix and vector
        # of N random numbers (where N is equal to number of sites).
        # we need to do that multiplication once per realization
        # with the same matrix and different vectors.
        try:
            corma = self.cache[imt]
        except KeyError:
            corma = self.get_lower_triangle_correlation_matrix(
                sites.complete, imt)
            self.cache[imt] = corma
        if len(sites.complete) == len(sites):
            return numpy.dot(corma, residuals)
        # it is important to allocate little memory, this is why I am
        # accumulating below; if S is the length of the complete sites
        # the correlation matrix has shape (S, S) and the residuals (N, s),
        # where s is the number of samples
        return numpy.sum(corma[sites.sids, sid] * res
                         for sid, res in zip(sites.sids, residuals))


class JB2009CorrelationModel(BaseCorrelationModel):
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
        self.cache = {}  # imt -> correlation model

    def _get_correlation_matrix(self, sites, imt):
        return jbcorrelation(sites, imt, self.vs30_clustering)

    def get_lower_triangle_correlation_matrix(self, sites, imt):
        """
        See :meth:`BaseCorrelationModel.get_lower_triangle_correlation_matrix`.
        """
        return numpy.linalg.cholesky(self._get_correlation_matrix(sites, imt))


def jbcorrelation(sites_or_distances, imt, vs30_clustering=False):
        """
        Returns the Jayaram-Baker correlation model.

        :param sites_or_distances:
            SiteCollection instance o ristance matrix
        :param imt:
            Intensity Measure Type (PGA or SA)
        :param vs30_clustering:
            flag, defalt false
        """
        if hasattr(sites_or_distances, 'mesh'):
            distances = sites_or_distances.mesh.get_distance_matrix()
        else:
            distances = sites_or_distances

        # formulae are from page 1700
        if imt.period < 1:
            if not vs30_clustering:
                # case 1, eq. (17)
                b = 8.5 + 17.2 * imt.period
            else:
                # case 2, eq. (18)
                b = 40.7 - 15.0 * imt.period
        else:
            # both cases, eq. (19)
            b = 22.0 + 3.7 * imt.period

        # eq. (20)
        return numpy.exp((- 3.0 / b) * distances)
