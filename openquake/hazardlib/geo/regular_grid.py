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
"""Build complete rectangular grids for circulant embedding (CE).

Input locations are transformed to one local transverse Mercator coordinate
reference system, centred on the middle of their longitude extent, as used by
the CE grid detector. Their projected bounds are expanded and snapped outward
to multiples of the requested spacing. Equal steps along the easting and northing axes then define a square
lattice, including all cells in its enclosing rectangle. Coordinates are
transformed back to longitude and latitude, rounded for site-model CSV output,
and checked with the CE detector.

CE reuses the covariance for each row/column offset throughout the grid, so
that offset must represent the same Cartesian displacement everywhere. The
engine's existing geographic grid builders step along parallels and meridians;
even with kilometre spacing, these do not generally form an axis-aligned
lattice. The transverse Mercator projection is this implementation's choice of
planar geometry, not a requirement of CE itself. Its Euclidean distances
approximate distances on the Earth's surface, so the projection must be
suitable for the area being modeled.
"""
import logging

import numpy
from pyproj import Transformer

from openquake.hazardlib.correlation_models.circulant_embedding import (
    RegularGridLayout, _local_crs)
from openquake.hazardlib.geo.mesh import Mesh

MAX_GRID_CELLS = 2_000_000
MAX_GRID_EXTENT = 2_000  # km per projected axis


def _check_coordinates(lons, lats):
    if not len(lons) or len(lons) != len(lats):
        raise ValueError('Grid bounds require matching, nonempty coordinates')
    if not (numpy.isfinite(lons).all() and numpy.isfinite(lats).all()):
        raise ValueError('Grid coordinates must be finite')
    if numpy.any(numpy.abs(lons) > 180):
        raise ValueError('Longitude must be within [-180, 180]')
    if numpy.any((lats < -80) | (lats > 84)):
        raise ValueError('Grid lies outside the UTM latitude range [-80, 84]')
    if numpy.ptp(lons) > 180:
        raise ValueError('Antimeridian-crossing grids are not supported')


def regular_grid(mesh, spacing, padding=None):
    """Enclose locations in a complete, axis-aligned square grid.

    ``spacing`` and ``padding`` are in kilometres. ``padding`` extends each
    side of the input's projected bounds and defaults to one grid spacing.
    It defines the requested site-grid extent, not CE computational padding.
    Bounds are snapped outward to multiples of the spacing from the projected
    origin. Rows run west to east, ordered south to north.
    Longitude/latitude coordinates are rounded to five decimals, matching
    the site-model CSV writer, and validated with the engine's CE detector.
    """
    if spacing is None or not numpy.isfinite(spacing) or spacing <= 0:
        raise ValueError('Grid spacing must be finite and positive')
    if padding is None:
        padding = spacing
    if not numpy.isfinite(padding) or padding < 0:
        raise ValueError('Grid padding must be finite and nonnegative')
    lons, lats = numpy.asarray(mesh.lons).ravel(), numpy.asarray(
        mesh.lats).ravel()
    _check_coordinates(lons, lats)
    # One projection for the whole grid, shared with the CE detector
    crs = _local_crs(lons, lats)
    projection = Transformer.from_crs(4326, crs, always_xy=True)
    if len(lons) == 1:
        x, y = projection.transform(float(lons[0]), float(lats[0]))
        x, y = numpy.array([x]), numpy.array([y])
    else:
        x, y = projection.transform(lons, lats)
    step, margin = spacing * 1000, padding * 1000
    lower = numpy.floor((numpy.array([min(x), min(y)]) - margin) / step)
    upper = numpy.ceil((numpy.array([max(x), max(y)]) + margin) / step)
    dimensions = upper - lower + 1
    # Check limits before allocating coordinate arrays for the rectangle.
    if (not numpy.isfinite(dimensions).all() or
            numpy.prod(dimensions) > MAX_GRID_CELLS or
            numpy.any((dimensions - 1) * spacing > MAX_GRID_EXTENT)):
        raise ValueError(f'Grid exceeds {MAX_GRID_CELLS:,} candidate cells '
                         f'or {MAX_GRID_EXTENT:,} km per axis')
    nx, ny = dimensions.astype(int)
    xx, yy = numpy.meshgrid((lower[0] + numpy.arange(nx)) * step,
                           (lower[1] + numpy.arange(ny)) * step)
    lons, lats = Transformer.from_crs(crs, 4326, always_xy=True).transform(
        xx.ravel(), yy.ravel())
    lons, lats = numpy.round(lons, 5), numpy.round(lats, 5)
    _check_coordinates(lons, lats)
    coordinates = numpy.column_stack([lons, lats])
    if len(numpy.unique(coordinates, axis=0)) != len(lons):
        raise ValueError('Duplicate grid cells after coordinate rounding; '
                         'increase the grid spacing')
    grid = Mesh(lons, lats)
    layout = RegularGridLayout.from_sites(grid, crs=crs)
    logging.info('Regular grid %s: %d rows x %d columns, '
                 '%g km spacing, %d sites', layout.crs,
                 *layout.grid_shape, spacing, len(lons))
    return grid
