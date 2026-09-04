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
"""Local-kriging extension of grid simulation to off-grid stations.

The implementation follows the local-kriging method recommended by Bailey
et al. (2022). A station value is sampled conditionally on a small regular
grid neighborhood. Stations in the same grid box are sampled jointly;
conditional errors belonging to different boxes are treated as independent.
The latter is the approximation that makes the operation scalable.

For a spatial-cross-IMT model, the local conditional distribution includes
every IMT. This preserves cross-IMT covariance within each station and among
stations occupying the same grid box.

Bailey, M. D., Bandyopadhyay, S., Nychka, D. W., Thompson, E. M., and
Worden, C. B. (2022). Adapting conditional simulation using circulant
embedding for irregularly spaced spatial data. Stat, 11(1), e446.
https://doi.org/10.1002/sta4.446
"""

from dataclasses import dataclass

import numpy

from openquake.hazardlib.correlation_models.circulant_embedding import (
    GRID_TOLERANCE, RegularGridLayout)


def _distances(first, second):
    """Return Euclidean distances between two projected point arrays."""
    differences = first[:, numpy.newaxis] - second[numpy.newaxis, :]
    return numpy.linalg.norm(differences, axis=-1)


def _grid_points(layout, indices):
    """Return selected grid-cell coordinates in kilometres."""
    rows, columns = numpy.divmod(indices, layout.grid_shape[1])
    return numpy.column_stack(
        (rows * layout.spacing[0], columns * layout.spacing[1]))


def _covariance_root(covariance):
    """Return a real square root of a positive-semidefinite covariance."""
    covariance = (covariance + covariance.T) / 2
    eigenvalues, eigenvectors = numpy.linalg.eigh(covariance)
    scale = max(1.0, float(numpy.abs(eigenvalues).max()))
    tolerance = len(covariance) * numpy.finfo(float).eps * scale
    if eigenvalues.min() < -tolerance:
        raise ValueError(
            'The local conditional covariance is not positive semidefinite')
    return eigenvectors * numpy.sqrt(eigenvalues.clip(min=0))


def _neighborhood(box, order, shape):
    """Return flattened cells in a ``(2 * order)`` square neighborhood."""
    row, column = box
    rows = numpy.arange(row - order + 1, row + order + 1)
    columns = numpy.arange(column - order + 1, column + order + 1)
    if (rows.min() < 0 or columns.min() < 0 or
            rows.max() >= shape[0] or columns.max() >= shape[1]):
        raise ValueError(
            'The correlation grid does not contain the local-kriging '
            'neighborhood; expand it around the stations first')
    rr, cc = numpy.meshgrid(rows, columns, indexing='ij')
    return (rr * shape[1] + cc).reshape(-1)


@dataclass(frozen=True)
class LocalKrigingGroup:
    """Conditional sampler for stations occupying one grid box."""

    station_indices: numpy.ndarray
    grid_indices: numpy.ndarray
    weights: numpy.ndarray
    conditional_root: numpy.ndarray
    error_slice: slice


def _build_group(model, imts, layout, station_points, station_indices,
                 box, order, component, context, error_start):
    """Build one same-grid-box multivariate conditional distribution."""
    grid_indices = _neighborhood(box, order, layout.grid_shape)
    grid_points = _grid_points(layout, grid_indices)
    selected_stations = station_points[station_indices]
    grid_covariance = model.correlation_block(
        _distances(grid_points, grid_points), imts,
        component=component, context=context)
    cross_covariance = model.correlation_block(
        _distances(selected_stations, grid_points), imts, imts,
        component, context)
    station_covariance = model.correlation_block(
        _distances(selected_stations, selected_stations), imts,
        component=component, context=context)
    inverse = numpy.linalg.pinv(grid_covariance, hermitian=True)
    weights = cross_covariance @ inverse
    conditional = station_covariance - weights @ cross_covariance.T
    root = _covariance_root(conditional)
    error_stop = error_start + len(conditional)
    return LocalKrigingGroup(
        station_indices, grid_indices, weights, root,
        slice(error_start, error_stop))


@dataclass(frozen=True)
class LocalKrigingFactor:
    """Map regular-grid fields and local errors to station fields."""

    layout: RegularGridLayout
    num_imts: int
    num_stations: int
    on_grid_stations: numpy.ndarray
    on_grid_cells: numpy.ndarray
    groups: tuple
    error_size: int

    @classmethod
    def build(cls, model, imts, layout, stations, order=4,
              component=None, context=None):
        """Build fourth-order local conditionals by default."""
        if not isinstance(layout, RegularGridLayout):
            raise TypeError('layout must be a RegularGridLayout')
        if not isinstance(order, (int, numpy.integer)) or order < 1:
            raise ValueError('order must be a positive integer')
        if not imts:
            raise ValueError('At least one IMT is required')

        rows, columns = layout.grid_coordinates(stations)
        rounded_rows = numpy.rint(rows)
        rounded_columns = numpy.rint(columns)
        on_grid = (
            (numpy.abs(rows - rounded_rows) <= GRID_TOLERANCE) &
            (numpy.abs(columns - rounded_columns) <= GRID_TOLERANCE))
        on_grid_stations = numpy.flatnonzero(on_grid)
        on_grid_rows = rounded_rows[on_grid].astype(int)
        on_grid_columns = rounded_columns[on_grid].astype(int)
        if (numpy.any(on_grid_rows < 0) or
                numpy.any(on_grid_rows >= layout.grid_shape[0]) or
                numpy.any(on_grid_columns < 0) or
                numpy.any(on_grid_columns >= layout.grid_shape[1])):
            raise ValueError('An on-grid station lies outside the grid')
        on_grid_cells = (
            on_grid_rows * layout.grid_shape[1] + on_grid_columns)

        station_points = numpy.column_stack(
            (rows * layout.spacing[0], columns * layout.spacing[1]))
        boxes = {}
        for station_index in numpy.flatnonzero(~on_grid):
            box = (int(numpy.floor(rows[station_index])),
                   int(numpy.floor(columns[station_index])))
            boxes.setdefault(box, []).append(station_index)

        groups = []
        error_start = 0
        for box, indices in sorted(boxes.items()):
            station_indices = numpy.asarray(indices, dtype=numpy.int64)
            group = _build_group(
                model, imts, layout, station_points, station_indices,
                box, order, component, context, error_start)
            groups.append(group)
            error_start = group.error_slice.stop
        return cls(
            layout, len(imts), len(rows), on_grid_stations,
            on_grid_cells, tuple(groups), error_start)

    def apply(self, grid_fields, errors):
        """Return IMT-major station fields for one or more realizations."""
        grid_fields = numpy.asarray(grid_fields)
        errors = numpy.asarray(errors)
        grid_size = numpy.prod(self.layout.grid_shape)
        if (grid_fields.ndim != 3 or
                grid_fields.shape[:2] != (self.num_imts, grid_size)):
            raise ValueError(
                'Expected grid fields with shape '
                f'({self.num_imts}, {grid_size}, E)')
        num_events = grid_fields.shape[2]
        if errors.shape != (self.error_size, num_events):
            raise ValueError(
                f'Expected local errors with shape '
                f'({self.error_size}, {num_events})')

        result = numpy.empty(
            (self.num_imts, self.num_stations, num_events),
            dtype=numpy.result_type(grid_fields, errors))
        result[:, self.on_grid_stations] = grid_fields[
            :, self.on_grid_cells]
        for group in self.groups:
            local_grid = grid_fields[:, group.grid_indices].reshape(
                -1, num_events)
            local_errors = errors[group.error_slice]
            values = (group.weights @ local_grid +
                      group.conditional_root @ local_errors)
            result[:, group.station_indices] = values.reshape(
                self.num_imts, len(group.station_indices), num_events)
        return result
