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
"""CE sampling at requested locations, independent of the GMM site model.

Du--Ning's nugget is independent between distinct locations, but correlated
across IMTs. It must be sampled at those locations rather than interpolated
from grid cells. Only the continuous part is extended by local kriging.
The cross-box conditional-error approximation is checked separately from
the exact regular-grid covariance; it is not an exact off-grid sampler.
"""
from dataclasses import dataclass
from types import SimpleNamespace

import numpy
from openquake.baselib.geolibs import pyproj
from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.circulant_embedding import (
    CirculantEmbeddingFactor, RegularGridLayout, _local_crs, _metric_crs)
from openquake.hazardlib.correlation_models.local_kriging import (
    LocalKrigingFactor, covariance_root)
from openquake.hazardlib.correlation_models.spatial_cross_imt.du_ning_2021 \
    import (DuNing2021, DuNing2021Interpolated, _NUGGET, _SHORT_SILL,
            _SHORT_RANGE, _LONG_SILL, _LONG_RANGE)
from openquake.hazardlib.geo.regular_grid import _check_coordinates


OUTPUT_GRID_SPACING = 0.25  # km
KRIGING_ORDER = 4
DENSE_SITE_LIMIT = 500


def _covariance_buffers(model, num_imts1, num_imts2, copies=6):
    # The seven-PC evaluator has scalar-site buffers as well as cross-IMT
    # output buffers. Counting only M-by-M matrices underestimates PGA-only
    # calculations and conditioning on a small number of observed IMTs.
    pairs = num_imts1 * num_imts2
    buffers = copies * pairs
    if model.__class__ in (DuNing2021, DuNing2021Interpolated):
        buffers = max(buffers, pairs + 48)
    return buffers


def nugget_covariance(model, imts1, imts2=None):
    """Return the exact Du--Ning same-location cross-IMT nugget."""
    if imts2 is None:
        imts2 = imts1
    return (model._coefficients(imts1) * _NUGGET) @ (
        model._coefficients(imts2).T)


@dataclass(frozen=True)
class ContinuousDuNing:
    """The original covariance with its independent nugget removed."""

    model: DuNing2021Interpolated

    def correlation_block(self, distances, imts1, imts2=None,
                          component=None, context=None):
        if imts2 is None:
            imts2 = imts1
        full = self.model.correlation_block(
            distances, imts1, imts2, component, context)
        nugget = nugget_covariance(self.model, imts1, imts2)
        blocks = full.reshape(len(imts1), distances.shape[0],
                              len(imts2), distances.shape[1])
        # Only zero-distance blocks contain a nugget. Avoid two additional
        # full lag tensors when preparing a large embedding.
        rows, columns = numpy.nonzero(distances == 0)
        for row, column in zip(rows, columns):
            blocks[:, row, :, column] -= nugget
        return full


@dataclass(frozen=True)
class ContinuousPrincipalComponent:
    """One published PC's short- and long-range continuous covariance."""

    short_sill: float
    short_range: float
    long_sill: float
    long_range: float
    CE_EVALUATION_BUFFERS = 8

    def correlation_block(self, distances, imts1, imts2=None,
                          component=None, context=None):
        short = self.short_sill * numpy.exp(-3 * distances / self.short_range)
        long = self.long_sill * numpy.exp(-3 * distances / self.long_range)
        return short + long


@dataclass(frozen=True)
class ContinuousGridFactor:
    """Mix seven independent scalar CE fields with the published loadings.

    This is exactly the same continuous grid covariance as factoring its
    cross-IMT spectrum. Scalar factors avoid retaining M-by-M spectra and
    can use different embedding extents for different PC ranges.
    """

    factors: tuple
    coefficients: numpy.ndarray

    @classmethod
    def build(cls, model, imts, layout, context=None, memory_budget=None):
        factors = []
        retained = 0
        for parameters in zip(_SHORT_SILL, _SHORT_RANGE,
                              _LONG_SILL, _LONG_RANGE):
            kernel = ContinuousPrincipalComponent(*parameters)
            budget = (None if memory_budget is None
                      else memory_budget - retained)
            indices = None if not factors else factors[0].site_indices
            factor = CirculantEmbeddingFactor.build(
                kernel, imts[:1], layout.grid_shape, layout.spacing,
                ResidualComponent.WITHIN_EVENT, context, indices,
                max_multiplier=16, memory_budget=budget)
            factors.append(factor)
            retained += factor.nbytes
        return cls(tuple(factors), model._coefficients(imts))

    @property
    def input_size(self):
        return sum(factor.input_size for factor in self.factors)

    @property
    def output_size(self):
        return len(self.coefficients) * self.factors[0].output_size

    @property
    def nbytes(self):
        return (sum(factor.nbytes for factor in self.factors) +
                self.coefficients.nbytes)

    @property
    def workspace_bytes_per_realization(self):
        return (sum(factor.workspace_bytes_per_realization
                    for factor in self.factors) + 16 * self.output_size)

    def apply(self, samples):
        """Mix independent PC fields without storing all seven grid fields."""
        if samples.ndim != 2 or samples.shape[0] != self.input_size:
            raise ValueError('Unexpected principal-component sample shape')
        events = samples.shape[1]
        output = numpy.zeros((len(self.coefficients),
                              self.factors[0].output_size, events))
        start = 0
        for k, factor in enumerate(self.factors):
            stop = start + factor.input_size
            fields = factor.apply(samples[start:stop])
            output += self.coefficients[:, k, None, None] * fields[None]
            start = stop
        return output.reshape(self.output_size, events)


def sampling_layout(sites, spacing=OUTPUT_GRID_SPACING, order=KRIGING_ORDER,
                    crs=None):
    """Enclose output locations with coordinate-only kriging neighbourhoods."""
    lons, lats = numpy.asarray(sites.lons), numpy.asarray(sites.lats)
    _check_coordinates(lons, lats)
    if not numpy.isfinite(spacing) or spacing <= 0:
        raise ValueError('Internal grid spacing must be finite and positive')
    crs = crs or getattr(sites, 'grid_crs', None) or _local_crs(lons, lats)
    projection = pyproj.Transformer.from_crs(
        4326, _metric_crs(crs), always_xy=True)
    x, y = projection.transform(lons, lats)
    step = spacing * 1000
    lower = numpy.floor([numpy.min(y) / step, numpy.min(x) / step]) - order
    upper = numpy.ceil([numpy.max(y) / step, numpy.max(x) / step]) + order
    shape = numpy.maximum(upper - lower + 1, numpy.ceil(64 / spacing))
    if (not numpy.isfinite(shape).all() or
            numpy.any((shape - 1) * spacing > 2000)):
        raise ValueError('Internal correlation grid exceeds 2000 km per axis')
    # No coordinate arrays or full-grid index vector are needed here.
    return RegularGridLayout(
        tuple(shape.astype(int)), (spacing, spacing),
        numpy.empty(0, dtype=numpy.int64), str(crs), tuple(lower * step), 0.)


@dataclass(frozen=True)
class OutputSitesFactor:
    """Continuous-grid, local-error and same-location nugget factors."""

    ce: ContinuousGridFactor
    local: LocalKrigingFactor
    nugget_root: numpy.ndarray
    inverse: numpy.ndarray

    @classmethod
    def build(cls, model, imts, sites, context=None, memory_budget=None,
              layout=None):
        """Build only for the validated interpolated Du--Ning model."""
        if model.__class__ is not DuNing2021Interpolated:
            raise ValueError('Irregular CE output sites are validated only '
                             'for DuNing2021Interpolated')
        coordinates, inverse = numpy.unique(
            numpy.column_stack((sites.lons, sites.lats)),
            axis=0, return_inverse=True)
        unique = SimpleNamespace(lons=coordinates[:, 0],
                                 lats=coordinates[:, 1],
                                 grid_crs=getattr(sites, 'grid_crs', None))
        if layout is None:
            layout = sampling_layout(unique)
        continuous = ContinuousDuNing(model)
        component = ResidualComponent.WITHIN_EVENT
        # The local setup precedes CE, so its actual retained storage can be
        # reserved before allocating or enlarging the spectral embedding.
        local = LocalKrigingFactor.build(
            continuous, imts, layout, unique, KRIGING_ORDER,
            component, context, memory_budget=memory_budget)
        nugget = covariance_root(nugget_covariance(model, imts))
        reserve = local.nbytes + nugget.nbytes + inverse.nbytes
        budget = None if memory_budget is None else memory_budget - reserve
        ce = ContinuousGridFactor.build(model, imts, layout, context, budget)
        factor = cls(ce, local, nugget, inverse)
        if memory_budget is not None:
            factor.batch_size(memory_budget)
        return factor

    @property
    def input_size(self):
        return (self.ce.input_size + self.local.error_size +
                self.local.num_imts * self.local.num_stations)

    @property
    def output_size(self):
        return self.local.num_imts * len(self.inverse)

    @property
    def nbytes(self):
        return (self.ce.nbytes + self.local.nbytes +
                self.nugget_root.nbytes + self.inverse.nbytes)

    @property
    def workspace_bytes_per_realization(self):
        return (self.ce.workspace_bytes_per_realization +
                16 * (self.local.error_size + self.output_size) +
                16 * self.local.num_imts * self.local.num_stations)

    def batch_size(self, memory_budget):
        """Bound all sampling arrays as well as the retained factors."""
        required = self.nbytes + self.workspace_bytes_per_realization
        if memory_budget < required:
            raise ValueError(f'Irregular CE requires at least {required} '
                             f'workspace bytes; budget is {memory_budget}')
        return max(1, int(memory_budget - self.nbytes) //
                   self.workspace_bytes_per_realization)

    def apply(self, samples):
        """Return fields at the requested locations in IMT-major order."""
        samples = numpy.asarray(samples)
        if samples.ndim != 2 or samples.shape[0] != self.input_size:
            raise ValueError(
                f'Expected samples with shape ({self.input_size}, E), '
                f'got {samples.shape}')
        events = samples.shape[1]
        first = self.ce.input_size
        second = first + self.local.error_size
        grid = self.ce.apply(samples[:first]).reshape(
            self.local.num_imts, -1, events)
        fields = self.local.apply(grid, samples[first:second])
        nugget = self.nugget_root @ samples[second:].reshape(
            self.local.num_imts, -1)
        fields += nugget.reshape(fields.shape)
        return fields[:, self.inverse].reshape(self.output_size, events)
