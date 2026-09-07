# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""Base interfaces shared by ground-motion correlation models."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

import numpy
from scipy import stats

from openquake.hazardlib import const
from openquake.hazardlib.correlation_utils import corr_clipped, cov_nearest
from openquake.hazardlib.imt import IMT
from openquake.hazardlib.truncated_mvn import TruncatedMVN


class ResidualComponent(str, Enum):
    """Residual components for which a model can be calibrated."""

    TOTAL = 'total'
    WITHIN_EVENT = 'within'
    BETWEEN_EVENT = 'between'


@dataclass(frozen=True)
class CorrelationContext:
    """Optional predictors used by context-dependent correlation models."""

    mag: float | None = None
    rake: float | None = None
    trt: str | None = None
    region: str | None = None


@runtime_checkable
class CorrelationFactor(Protocol):
    """A factorization capable of applying correlation to samples."""

    def apply(self, samples: numpy.ndarray) -> numpy.ndarray:
        """Apply the factorization to standard-normal samples."""


@dataclass(frozen=True)
class CholeskyFactor:
    """Dense Cholesky factorization used by the default implementation."""

    lower_triangle: numpy.ndarray

    def apply(self, samples):
        return self.lower_triangle @ samples


class CorrelationModel:
    """Common metadata and validation for all correlation models."""

    SUPPORTS_CIRCULANT_EMBEDDING = False
    DEFINED_FOR_RESIDUAL_COMPONENT = None
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = None
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = None
    CALIBRATED_FOR_INTENSITY_MEASURE_TYPES = None
    INTENSITY_MEASURE_TYPE_APPROXIMATIONS = {}
    DEFINED_FOR_SA_DAMPING = None
    DEFINED_FOR_SA_PERIOD_RANGE = None
    DEFINED_FOR_REGION = None

    def validate(self):
        """Validate model parameters after construction."""
        imc = self.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT
        if imc is not None and not isinstance(imc, const.IMC):
            raise TypeError(
                f'{self.__class__.__name__}.'
                'DEFINED_FOR_INTENSITY_MEASURE_COMPONENT must be an '
                'openquake.hazardlib.const.IMC member')
        supported = self.DEFINED_FOR_INTENSITY_MEASURE_TYPES
        calibrated = self._calibrated_imts()
        approximations = self.INTENSITY_MEASURE_TYPE_APPROXIMATIONS
        if supported is not None and not calibrated <= supported:
            raise ValueError(
                f'{self.__class__.__name__} declares calibrated intensity '
                'measure types that it does not support')
        if supported is not None and not approximations.keys() <= supported:
            raise ValueError(
                f'{self.__class__.__name__} declares approximations for '
                'unsupported intensity measure types')
        if not all(isinstance(imt, IMT) for imt in approximations.values()):
            raise TypeError(
                f'{self.__class__.__name__} intensity measure type '
                'approximations must map to IMT instances')

    def validate_imts(self, imts):
        """Raise when an IMT is outside the model's declared scope."""
        model_name = self.__class__.__name__
        supported = self.DEFINED_FOR_INTENSITY_MEASURE_TYPES
        if supported is not None:
            supported_names = {imt_type.__name__ for imt_type in supported}
            unsupported = sorted({
                imt.name for imt in imts
                if imt.name not in supported_names})
            if unsupported:
                raise ValueError(
                    f'{model_name} does not support '
                    f'{", ".join(unsupported)}')
        for imt in imts:
            damping = self.DEFINED_FOR_SA_DAMPING
            if (imt.name == 'SA' and damping is not None and
                    imt.damping != damping):
                raise ValueError(
                    f'{model_name} supports only '
                    f'{damping:g}%-damped SA')
            period_range = self.DEFINED_FOR_SA_PERIOD_RANGE
            if imt.name == 'SA' and period_range is not None:
                minimum, maximum = period_range
                if not minimum <= imt.period <= maximum:
                    raise ValueError(
                        f'{model_name} supports {imt.name} periods from '
                        f'{minimum:g} to {maximum:g} s, not '
                        f'{imt.period:g} s')
        self._validate_imt_combination(imts)

    def _validate_imt_combination(self, imts):
        """Validate restrictions involving more than one IMT."""

    @staticmethod
    def _validate_distances(sites_or_distances):
        """Return a finite, non-negative distance matrix in float64."""
        if hasattr(sites_or_distances, 'mesh'):
            distances = sites_or_distances.mesh.get_distance_matrix()
        else:
            distances = sites_or_distances
        distances = numpy.asarray(distances, dtype=numpy.float64)
        if distances.ndim != 2:
            raise ValueError('Distances must be a two-dimensional matrix')
        if not numpy.all(numpy.isfinite(distances)):
            raise ValueError('Distances must be finite')
        if numpy.any(distances < 0):
            raise ValueError('Distances must be non-negative')
        return distances

    @staticmethod
    def _validate_block(block, expected_shape, check_bounds=True):
        """Validate the shape and values returned by a model."""
        block = numpy.asarray(block)
        if block.shape != expected_shape:
            raise ValueError(
                f'Expected a correlation block with shape {expected_shape}, '
                f'got {block.shape}')
        if not numpy.all(numpy.isfinite(block)):
            raise ValueError('Correlation values must be finite')
        if (check_bounds and
                numpy.any(numpy.abs(block) > 1 + 1E-12)):
            raise ValueError('Correlation values must be between -1 and 1')
        return block

    @classmethod
    def _calibrated_imts(cls):
        calibrated = cls.CALIBRATED_FOR_INTENSITY_MEASURE_TYPES
        if calibrated is None:
            return cls.DEFINED_FOR_INTENSITY_MEASURE_TYPES
        return calibrated

    def _get_component(self, component=None):
        if component is None:
            return self.DEFINED_FOR_RESIDUAL_COMPONENT
        try:
            component = ResidualComponent(component)
        except ValueError as exc:
            allowed = ', '.join(item.value for item in ResidualComponent)
            raise ValueError(
                f'Unknown residual component {component!r}; use {allowed}'
            ) from exc
        defined_component = self.DEFINED_FOR_RESIDUAL_COMPONENT
        if (defined_component is not None and
                component != defined_component):
            raise ValueError(
                f'{self.__class__.__name__} provides '
                f'{defined_component.value} correlation, not '
                f'{component.value}')
        return component


class SpatialCrossIMTCorrelationModel(CorrelationModel):
    """Correlation over a joint, IMT-major vector of sites and IMTs."""

    def correlation_block(self, distances, imts1, imts2=None,
                          component=None, context=None):
        """Return correlation between two IMT-major site vectors.

        ``distances`` has shape ``(N1, N2)`` and the returned matrix has
        shape ``(len(imts1) * N1, len(imts2) * N2)``. Joint models should
        implement this method so they can also be used for conditioning.
        """
        self._get_component(component)
        if imts2 is None:
            imts2 = imts1
        self.validate_imts(imts1)
        self.validate_imts(imts2)
        distances = self._validate_distances(distances)
        block = self._correlation_block(
            distances, imts1, imts2, context=context)
        expected = (len(imts1) * distances.shape[0],
                    len(imts2) * distances.shape[1])
        return self._validate_block(block, expected)

    def _correlation_block(self, distances, imts1, imts2, context=None):
        """Implement :meth:`correlation_block` in a concrete model."""
        raise NotImplementedError

    def covariance(self, sites, imts, component=None, context=None):
        """Return a covariance matrix with shape ``(M*N, M*N)``."""
        distances = sites.mesh.get_distance_matrix()
        return self.correlation_block(
            distances, imts, component=component, context=context)

    def factor(self, sites, imts, component=None, context=None,
               ensure_psd=True):
        """Return the default dense factorization of :meth:`covariance`.

        The fast path attempts Cholesky decomposition directly. A covariance
        repair is performed only when decomposition fails and ``ensure_psd``
        is true. Models with efficient structured factorizations should
        override this method.
        """
        covariance = numpy.asarray(
            self.covariance(sites, imts, component, context))
        if covariance.ndim != 2 or covariance.shape[0] != covariance.shape[1]:
            raise ValueError('A correlation matrix must be square')
        self._validate_block(
            covariance, covariance.shape, check_bounds=False)
        if not numpy.allclose(covariance, covariance.T):
            raise ValueError('A correlation matrix must be symmetric')
        if not numpy.allclose(numpy.diag(covariance), 1):
            raise ValueError('A correlation matrix must have a unit diagonal')
        try:
            lower_triangle = numpy.linalg.cholesky(covariance)
        except numpy.linalg.LinAlgError:
            if not ensure_psd:
                raise
            covariance = cov_nearest(covariance, threshold=1E-12)
            lower_triangle = numpy.linalg.cholesky(covariance)
        return CholeskyFactor(lower_triangle)

    def correlate(self, sites, imts, samples, component=None, context=None):
        """Correlate standard-normal samples across IMTs and sites.

        ``samples`` must have shape ``(M, N, E)``. The first two dimensions
        are flattened in IMT-major order before applying the factorization.
        """
        samples = numpy.asarray(samples)
        expected = (len(imts), len(sites))
        if samples.ndim != 3 or samples.shape[:2] != expected:
            raise ValueError(
                f'Expected samples with shape {expected} + (E,), got '
                f'{samples.shape}')
        factor = self.factor(sites, imts, component, context)
        correlated = factor.apply(samples.reshape(-1, samples.shape[-1]))
        return correlated.reshape(samples.shape)


class SpatialCorrelationModel(SpatialCrossIMTCorrelationModel):
    """Same-IMT spatial correlation over a collection of sites."""

    def __init__(self):
        self.cache = {}

    def correlation_matrix(self, sites, imt, component=None, context=None):
        """Return a same-IMT spatial correlation matrix or block."""
        self._get_component(component)
        self.validate_imts([imt])
        distances = self._validate_distances(sites)
        implementation = type(self)._correlation_matrix
        if implementation is not SpatialCorrelationModel._correlation_matrix:
            matrix = implementation(self, distances, imt, context)
        else:
            legacy = type(self)._get_correlation_matrix
            if legacy is SpatialCorrelationModel._get_correlation_matrix:
                raise NotImplementedError
            matrix = legacy(self, distances, imt)
        matrix = self._validate_block(matrix, distances.shape)
        is_self_distance = (
            distances.shape[0] == distances.shape[1] and
            numpy.allclose(distances, distances.T) and
            numpy.allclose(numpy.diag(distances), 0))
        if is_self_distance:
            if not numpy.allclose(matrix, matrix.T):
                raise ValueError('A correlation matrix must be symmetric')
            if not numpy.allclose(numpy.diag(matrix), 1):
                raise ValueError(
                    'A correlation matrix must have a unit diagonal')
        return matrix

    def _correlation_matrix(self, distances, imt, context=None):
        """Implement :meth:`correlation_matrix` in a concrete model."""
        legacy = type(self)._get_correlation_matrix
        if legacy is SpatialCorrelationModel._get_correlation_matrix:
            raise NotImplementedError
        return legacy(self, distances, imt)

    def _get_correlation_matrix(self, sites, imt):
        return self.correlation_matrix(sites, imt)

    def get_lower_triangle_correlation_matrix(self, sites, imt):
        """Return the dense Cholesky factor of the correlation matrix."""
        return numpy.linalg.cholesky(
            self.correlation_matrix(sites, imt))

    def apply_correlation(self, sites, imt, residuals, stddev_intra=0):
        """Apply spatial correlation to sampled within-event residuals."""
        try:
            lower_triangle = self.cache[imt]
        except KeyError:
            lower_triangle = self.get_lower_triangle_correlation_matrix(
                sites.complete, imt)
            self.cache[imt] = lower_triangle
        num_complete = len(sites.complete)
        if len(sites) < num_complete:
            complete = numpy.zeros((num_complete, residuals.shape[1]))
            complete[sites.sids] = residuals
            return (lower_triangle @ complete)[sites.sids, :]
        return lower_triangle @ residuals

    def covariance(self, sites, imts, component=None, context=None):
        """Embed same-IMT matrices in IMT-major diagonal blocks."""
        num_sites = len(sites)
        covariance = numpy.zeros(
            (len(imts) * num_sites, len(imts) * num_sites))
        for imt_index, imt in enumerate(imts):
            start = imt_index * num_sites
            block = slice(start, start + num_sites)
            covariance[block, block] = self.correlation_matrix(
                sites, imt, component, context)
        return covariance

    def _correlation_block(self, distances, imts1, imts2, context=None):
        """Return same-IMT spatial blocks for two site vectors."""
        num_sites1, num_sites2 = distances.shape
        correlation = numpy.zeros(
            (len(imts1) * num_sites1, len(imts2) * num_sites2))
        for index1, imt1 in enumerate(imts1):
            for index2, imt2 in enumerate(imts2):
                if imt1 != imt2:
                    continue
                rows = slice(index1 * num_sites1,
                             (index1 + 1) * num_sites1)
                cols = slice(index2 * num_sites2,
                             (index2 + 1) * num_sites2)
                correlation[rows, cols] = self._correlation_matrix(
                    distances, imt1, context)
        return correlation


class CrossIMTCorrelationModel(SpatialCrossIMTCorrelationModel):
    """Cross-IMT correlation at a single site."""

    def rho(self, from_imt, to_imt, component=None, context=None):
        """Return the correlation between two IMTs."""
        self._get_component(component)
        self.validate_imts([from_imt, to_imt])
        implementation = type(self)._rho
        if implementation is not CrossIMTCorrelationModel._rho:
            correlation = implementation(
                self, from_imt, to_imt, context=context)
        else:
            legacy = type(self).get_correlation
            if legacy is CrossIMTCorrelationModel.get_correlation:
                raise NotImplementedError
            correlation = legacy(self, from_imt, to_imt)
        if not numpy.isscalar(correlation) or not numpy.isfinite(correlation):
            raise ValueError('A correlation coefficient must be finite')
        if abs(correlation) > 1 + 1E-12:
            raise ValueError(
                'A correlation coefficient must be between -1 and 1')
        return correlation

    def _rho(self, from_imt, to_imt, context=None):
        """Implement :meth:`rho` in a concrete model."""
        legacy = type(self).get_correlation
        if legacy is CrossIMTCorrelationModel.get_correlation:
            raise NotImplementedError
        return legacy(self, from_imt, to_imt)

    def get_correlation(self, from_imt, to_imt):
        """Compatibility alias for :meth:`rho`."""
        return self.rho(from_imt, to_imt)

    def correlation_matrix(self, imts, component=None, context=None,
                           dtype=float):
        """Return an ``M x M`` cross-IMT correlation matrix."""
        self._get_component(component)
        self.validate_imts(imts)
        matrix = numpy.zeros((len(imts), len(imts)), dtype)
        for row, from_imt in enumerate(imts):
            for col in range(row, len(imts)):
                correlation = self.rho(
                    from_imt, imts[col], component, context)
                matrix[row, col] = correlation
                matrix[col, row] = correlation
        return matrix

    def get_cross_correlation_mtx(self, imts):
        """Compatibility alias returning the historical float32 matrix."""
        return self.correlation_matrix(imts, dtype=numpy.float32)

    def covariance(self, sites, imts, component=None, context=None):
        """Embed cross-IMT matrices for each site in IMT-major ordering."""
        num_sites = len(sites)
        num_imts = len(imts)
        imt_correlation = self.correlation_matrix(
            imts, component, context)
        covariance = numpy.zeros(
            (num_imts * num_sites, num_imts * num_sites))
        for site_index in range(num_sites):
            indexes = [imt_index * num_sites + site_index
                       for imt_index in range(num_imts)]
            covariance[numpy.ix_(indexes, indexes)] = imt_correlation
        return covariance


class TruncatedCrossIMTCorrelationModel(CrossIMTCorrelationModel):
    """Cross-IMT model able to sample truncated normal residuals."""

    matrix_dtype = float

    def __init__(self, truncation_level=99.):
        if truncation_level < 1E-9:
            truncation_level = 1E-9
        self.truncation_level = truncation_level
        self.distribution = stats.truncnorm(
            -truncation_level, truncation_level)
        self.cache = {}

    def _get_correlation_matrix(self, imts):
        key = tuple(imts)
        try:
            return self.cache[key]
        except KeyError:
            matrix = self.correlation_matrix(
                imts, dtype=self.matrix_dtype)
            self.cache[key] = matrix
            return matrix

    def get_inter_eps(self, imts, num_events, rng):
        """Return an ``M x E`` matrix of correlated event terms."""
        matrix = self._get_correlation_matrix(imts)
        return self._get_inter_eps_trunc_mvn(matrix, num_events, rng)

    def _get_inter_eps_trunc_mvn(self, matrix, num_events, rng):
        num_imts = len(matrix)
        mean = numpy.zeros(num_imts)
        bounds = numpy.full(num_imts, self.truncation_level)
        seed = int(rng.integers(0, numpy.iinfo(numpy.int32).max))
        correlation = numpy.array(matrix, copy=True)
        min_eigenvalue = numpy.linalg.eigvalsh(correlation).min()
        if (not numpy.isfinite(min_eigenvalue) or
                min_eigenvalue < 1E-8):
            correlation = corr_clipped(correlation, threshold=1E-8)
        try:
            samples = TruncatedMVN(
                mean, correlation, -bounds, bounds, seed=seed
            ).sample(num_events)
            if numpy.isfinite(samples).all():
                return samples
        except RuntimeError as exc:
            if 'not positive semi-definite' not in str(exc):
                raise
        correlation = corr_clipped(correlation, threshold=1E-6)
        return TruncatedMVN(
            mean, correlation, -bounds, bounds, seed=seed
        ).sample(num_events)
