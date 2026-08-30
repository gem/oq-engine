# The Hazard Library
# Copyright (C) 2026 GEM Foundation
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
"""Circulant embedding for stationary multivariate Gaussian fields.

The implementation follows the block-circulant construction described by
Chan and Wood (1999). It embeds the requested rectangular grid in a larger
periodic grid, factorizes the small cross-IMT spectral covariance at each
Fourier mode, and applies those factors with real FFTs.

References
----------
Chan, G., and Wood, A. T. A. (1999). Simulation of stationary Gaussian
vector fields. Statistics and Computing, 9, 265-268.
https://doi.org/10.1023/A:1008903804954

Dietrich, C. R., and Newsam, G. N. (1993). A fast and exact method for
multidimensional Gaussian stochastic simulations. Water Resources Research,
29(8), 2861-2869. https://doi.org/10.1029/93WR01070
"""

from dataclasses import dataclass

import numpy
from scipy.fft import next_fast_len


def _pair(value, name, cast):
    """Return a validated pair of grid parameters."""
    if numpy.isscalar(value):
        value = (value, value)
    if len(value) != 2:
        raise ValueError(f'{name} must contain two values')
    pair = tuple(cast(item) for item in value)
    if any(item <= 0 for item in pair):
        raise ValueError(f'{name} values must be positive')
    return pair


def _embedding_shape(grid_shape, multiplier):
    """Return FFT-efficient dimensions for a periodic embedding."""
    return tuple(next_fast_len(max(1, 2 * multiplier * (size - 1)))
                 for size in grid_shape)


def _lag_distances(shape, spacing):
    """Return distances from the origin on the periodic grid."""
    ny, nx = shape
    y = numpy.minimum(numpy.arange(ny), ny - numpy.arange(ny))
    x = numpy.minimum(numpy.arange(nx), nx - numpy.arange(nx))
    return numpy.hypot(
        y[:, numpy.newaxis] * spacing[0],
        x[numpy.newaxis, :] * spacing[1])


def _covariance_lags(model, imts, shape, spacing, component, context):
    """Return cross-IMT covariance blocks for all periodic lags."""
    distances = _lag_distances(shape, spacing)
    num_imts = len(imts)
    blocks = model.correlation_block(
        distances.reshape(-1, 1), imts, imts, component, context)
    return blocks.reshape(num_imts, -1, num_imts).transpose(
        1, 0, 2).reshape(*shape, num_imts, num_imts)


def _spectral_root(covariance_lags):
    """Return the Hermitian square root at every Fourier mode."""
    spectrum = numpy.fft.rfft2(covariance_lags, axes=(0, 1))
    transpose = spectrum.swapaxes(-1, -2).conj()
    scale = max(1.0, float(numpy.abs(spectrum).max()))
    tolerance = 100 * numpy.finfo(float).eps * scale
    if not numpy.allclose(spectrum, transpose, rtol=1E-12,
                          atol=tolerance):
        raise ValueError(
            'The embedded spectral covariance is not Hermitian')
    spectrum = (spectrum + transpose) / 2
    eigenvalues, eigenvectors = numpy.linalg.eigh(spectrum)
    minimum = float(eigenvalues.min())
    tolerance *= numpy.prod(covariance_lags.shape[:2])
    if minimum < -tolerance:
        return minimum, None
    eigenvalues = numpy.maximum(eigenvalues, 0)
    scaled_vectors = (
        eigenvectors * numpy.sqrt(eigenvalues)[..., numpy.newaxis, :])
    root = scaled_vectors @ eigenvectors.swapaxes(-1, -2).conj()
    return minimum, root


@dataclass(frozen=True)
class CirculantEmbeddingFactor:
    """FFT factorization of an IMT-major regular-grid covariance.

    Use :meth:`build` to construct a positive-semidefinite periodic
    embedding. :meth:`apply` accepts a two-dimensional array containing one
    white-noise vector per column and returns fields in IMT-major order.
    """

    spectral_root: numpy.ndarray
    grid_shape: tuple
    embedded_shape: tuple
    num_imts: int
    site_indices: numpy.ndarray
    embedding_multiplier: int
    minimum_eigenvalue: float

    @classmethod
    def build(cls, model, imts, grid_shape, spacing, component=None,
              context=None, site_indices=None, max_multiplier=8):
        """Build an embedding, enlarging it until its spectrum is PSD."""
        grid_shape = _pair(grid_shape, 'grid_shape', int)
        spacing = _pair(spacing, 'spacing', float)
        if not imts:
            raise ValueError('At least one IMT is required')
        if max_multiplier < 1:
            raise ValueError('max_multiplier must be positive')
        indices = cls._validate_indices(site_indices, grid_shape)
        minimum = numpy.nan
        for multiplier in range(1, max_multiplier + 1):
            embedded_shape = _embedding_shape(grid_shape, multiplier)
            covariance_lags = _covariance_lags(
                model, imts, embedded_shape, spacing, component, context)
            minimum, root = _spectral_root(covariance_lags)
            if root is not None:
                return cls(
                    root, grid_shape, embedded_shape, len(imts), indices,
                    multiplier, minimum)
        raise ValueError(
            'The circulant embedding is not positive semidefinite through '
            f'multiplier {max_multiplier}; minimum eigenvalue is '
            f'{minimum:g}')

    @staticmethod
    def _validate_indices(site_indices, grid_shape):
        """Return flattened output-cell indices in their requested order."""
        size = numpy.prod(grid_shape)
        if site_indices is None:
            return numpy.arange(size)
        indices = numpy.asarray(site_indices)
        if indices.ndim != 1 or not numpy.issubdtype(
                indices.dtype, numpy.integer):
            raise ValueError('site_indices must be a one-dimensional '
                             'integer array')
        if len(numpy.unique(indices)) != len(indices):
            raise ValueError('site_indices must not contain duplicates')
        if numpy.any(indices < 0) or numpy.any(indices >= size):
            raise ValueError('site_indices contains an out-of-grid cell')
        return indices.astype(numpy.int64, copy=False)

    @property
    def input_size(self):
        """Number of independent values required for each realization."""
        return self.num_imts * numpy.prod(self.embedded_shape)

    @property
    def output_size(self):
        """Number of correlated values returned for each realization."""
        return self.num_imts * len(self.site_indices)

    def apply(self, samples):
        """Apply the embedding to columns of independent normal values."""
        samples = numpy.asarray(samples)
        if samples.ndim != 2 or samples.shape[0] != self.input_size:
            raise ValueError(
                f'Expected samples with shape ({self.input_size}, E), got '
                f'{samples.shape}')
        num_events = samples.shape[1]
        white = samples.reshape(
            self.num_imts, *self.embedded_shape, num_events)
        white = white.transpose(3, 1, 2, 0)
        transformed = numpy.fft.rfft2(white, axes=(1, 2))
        correlated = numpy.einsum(
            'yxij,eyxj->eyxi', self.spectral_root, transformed)
        fields = numpy.fft.irfft2(
            correlated, s=self.embedded_shape, axes=(1, 2))
        ny, nx = self.grid_shape
        fields = fields[:, :ny, :nx].reshape(
            num_events, ny * nx, self.num_imts)
        fields = fields[:, self.site_indices]
        return fields.transpose(2, 1, 0).reshape(
            self.output_size, num_events)
