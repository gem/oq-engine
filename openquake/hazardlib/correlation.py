# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
    def apply_correlation(self, sites, imt, residuals, stddev_intra=0):
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
        :param stddev_intra:
            Intra-event standard deviation array (phi). Different sites do
            not necessarily have the same intra-event standard deviation.
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
        # if N is the length of the complete site collection, then the
        # correlation matrix has shape (N, N) and the residuals (N, s),
        # where s is the number of samples
        N = len(sites.complete)
        n = len(sites)
        if n < N:  # filtered site collection
            res = numpy.zeros((N, residuals.shape[1]))
            res[sites.sids] = residuals
            return (corma @ res)[sites.sids, :]  # shape (n, s)
        else:  # complete site collection
            return corma @ residuals  # shape (N, s)


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
    period = 1.0 if imt.string == 'PGV' else imt.period
    if period < 1:
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


class HM2018CorrelationModel(BaseCorrelationModel):
    """
    "Uncertainty in intraevent spatial correlation of elastic pseudo-
    acceleration spectral ordinates"
    by Pablo Heresi and Eduardo Miranda. Submitted for possible publication
    in Bulletin of Earthquake Engineering, 2018.

    :param uncertainty_multiplier:
        Value to be multiplied by the uncertainty in the correlation parameter
        beta. If uncertainty_multiplier = 0 (default), the median value is
        used as a constant value.
    """
    def __init__(self, uncertainty_multiplier=0):
        self.uncertainty_multiplier = uncertainty_multiplier
        self.distance_matrix = {}
        self.cache = {}

    def _get_correlation_matrix(self, sites, imt):
        return hmcorrelation(sites, imt, self.uncertainty_multiplier)

    def apply_correlation(self, sites, imt, residuals, stddev_intra):
        """
        Apply correlation to randomly sampled residuals
        """
        # TODO: the case of filtered sites is probably managed incorrectly
        # NB: this is SLOW and we cannot use the cache as in JB2009 because
        # we are not using the complete site collection
        nsites = len(sites)
        assert len(residuals) == len(stddev_intra) == nsites
        D = numpy.diag(stddev_intra)  # phi as a diagonal matrix

        if self.uncertainty_multiplier == 0:   # No uncertainty

            # residuals were sampled from a normal distribution with
            # stddev_intra standard deviation. 'residuals_norm' are residuals
            # normalized, sampled from a standard normal distribution.
            # For this, every row of 'residuals' (every site) is divided by its
            # corresponding standard deviation element.
            residuals_norm = residuals / stddev_intra[:, None]

            # Lower diagonal of the Cholesky decomposition
            # Note that instead of computing the whole correlation matrix
            # corresponding to sites.complete, here we compute only the
            # correlation matrix corresponding to sites
            cormaLow = numpy.linalg.cholesky(
                D @ self._get_correlation_matrix(sites, imt) @ D)

            # Apply correlation
            return cormaLow @ residuals_norm

        else:   # Variability (uncertainty) is included
            nsim = residuals.shape[1]

            # Re-sample all the residuals
            residuals_correlated = residuals * 0
            for isim in range(0, nsim):
                # FIXME: the seed is not set!
                corma = self._get_correlation_matrix(sites, imt)
                # NB: corma is different at each loop since contains randomicity
                residuals_correlated[0:, isim] = (
                    numpy.random.multivariate_normal(
                        numpy.zeros(nsites), D @ corma @ D, 1))

            return residuals_correlated


def hmcorrelation(sites_or_distances, imt, uncertainty_multiplier=0):
    """
    Returns the Heresi-Miranda correlation model.

    :param sites_or_distances:
        SiteCollection instance o distance matrix
    :param imt:
        Intensity Measure Type (PGA or SA)
    :param uncertainty_multiplier:
        Value to be multiplied by the uncertainty in the correlation parameter
        beta. If uncertainty_multiplier = 0 (default), the median value is
        used as a constant value.
    """
    if hasattr(sites_or_distances, 'mesh'):
        distances = sites_or_distances.mesh.get_distance_matrix()
    else:
        distances = sites_or_distances

    period = imt.period

    # Eq. (9)
    if period < 1.37:
        Med_b = 4.231 * period * period - 5.180 * period + 13.392
    else:
        Med_b = 0.140 * period * period - 2.249 * period + 17.050

    # Eq. (10)
    Std_b = (4.63e-3 * period*period + 0.028 * period + 0.713)

    # Obtain realization of b
    if uncertainty_multiplier == 0:
        beta = Med_b
    else:
        beta = numpy.random.lognormal(
            numpy.log(Med_b), Std_b * uncertainty_multiplier)

    # Eq. (8)
    res = numpy.exp(-numpy.power((distances / beta), 0.55))
    return res
