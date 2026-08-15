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

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Protocol, runtime_checkable

import numpy
from scipy import stats

from openquake.hazardlib.correlation_utils import corr_clipped, cov_nearest
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
    values: Mapping[str, object] = field(default_factory=dict)


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

    name = ''
    calibrated_component = None
    supported_imts = None
    imc = None
    damping = None
    required_context = ()

    def validate(self):
        """Validate model parameters after construction."""

    def validate_imts(self, imts):
        """Raise when an IMT is outside the model's declared scope."""
        if self.supported_imts is None:
            return
        unsupported = sorted({imt.name for imt in imts
                              if imt.name not in self.supported_imts})
        if unsupported:
            raise ValueError(
                f'{self.name or self.__class__.__name__} does not support '
                f'{", ".join(unsupported)}')

    def _get_component(self, component=None):
        if component is None:
            return self.calibrated_component
        try:
            component = ResidualComponent(component)
        except ValueError as exc:
            allowed = ', '.join(item.value for item in ResidualComponent)
            raise ValueError(
                f'Unknown residual component {component!r}; use {allowed}'
            ) from exc
        if (self.calibrated_component is not None and
                component != self.calibrated_component):
            raise ValueError(
                f'{self.name or self.__class__.__name__} provides '
                f'{self.calibrated_component.value} correlation, not '
                f'{component.value}')
        return component


class SpatialCrossIMTCorrelationModel(CorrelationModel):
    """Correlation over a joint, IMT-major vector of sites and IMTs."""

    def covariance(self, sites, imts, component=None, context=None):
        """Return a covariance matrix with shape ``(M*N, M*N)``."""
        raise NotImplementedError

    def factor(self, sites, imts, component=None, context=None,
               ensure_psd=True):
        """Return the default dense factorization of :meth:`covariance`.

        The fast path attempts Cholesky decomposition directly. A covariance
        repair is performed only when decomposition fails and ``ensure_psd``
        is true. Models with efficient structured factorizations should
        override this method.
        """
        covariance = self.covariance(sites, imts, component, context)
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
        """Return an ``N x N`` same-IMT spatial correlation matrix."""
        self._get_component(component)
        legacy = type(self)._get_correlation_matrix
        if legacy is SpatialCorrelationModel._get_correlation_matrix:
            raise NotImplementedError
        return legacy(self, sites, imt)

    def _get_correlation_matrix(self, sites, imt):
        implementation = type(self).correlation_matrix
        if implementation is SpatialCorrelationModel.correlation_matrix:
            raise NotImplementedError
        return implementation(self, sites, imt)

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


class CrossIMTCorrelationModel(SpatialCrossIMTCorrelationModel):
    """Cross-IMT correlation at a single site."""

    def rho(self, from_imt, to_imt, component=None, context=None):
        """Return the correlation between two IMTs."""
        self._get_component(component)
        legacy = type(self).get_correlation
        if legacy is CrossIMTCorrelationModel.get_correlation:
            raise NotImplementedError
        return legacy(self, from_imt, to_imt)

    def get_correlation(self, from_imt, to_imt):
        """Compatibility alias for :meth:`rho`."""
        implementation = type(self).rho
        if implementation is CrossIMTCorrelationModel.rho:
            raise NotImplementedError
        return implementation(self, from_imt, to_imt)

    def correlation_matrix(self, imts, component=None, context=None,
                           dtype=float):
        """Return an ``M x M`` cross-IMT correlation matrix."""
        self._get_component(component)
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
