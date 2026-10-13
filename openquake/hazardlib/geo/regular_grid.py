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
"""Complete rectangular UTM grids compatible with circulant embedding."""
import logging

import numpy
from pyproj import Transformer

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
    """Enclose locations in a complete, axis-aligned square UTM grid.

    ``spacing`` and ``padding`` are in kilometres. Padding defaults to one
    grid spacing. Bounds are snapped outward to multiples of the spacing
    from the UTM origin. Rows run west to east, ordered south to north.
    Longitude/latitude coordinates are rounded to five decimals, matching
    the site-model CSV writer, and validated with the engine's CE detector.
    """
    from openquake.hazardlib.correlation_models.circulant_embedding import (
        RegularGridLayout, _utm_crs)

    if spacing is None or not numpy.isfinite(spacing) or spacing <= 0:
        raise ValueError('Grid spacing must be finite and positive')
    if padding is None:
        padding = spacing
    if not numpy.isfinite(padding) or padding < 0:
        raise ValueError('Grid padding must be finite and nonnegative')
    lons, lats = numpy.asarray(mesh.lons).ravel(), numpy.asarray(
        mesh.lats).ravel()
    _check_coordinates(lons, lats)
    # Share CE's zone and hemisphere convention, not per-point UTM zones.
    crs = _utm_crs(lons, lats)
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
    if _utm_crs(lons, lats) != crs:
        raise ValueError('Grid sites select a different UTM zone or '
                         'hemisphere; adjust the input extent or spacing')
    grid = Mesh(lons, lats)
    layout = RegularGridLayout.from_sites(grid)
    logging.info('Regular UTM grid EPSG:%d: %d rows x %d columns, '
                 '%g km spacing, %d sites', layout.crs,
                 *layout.grid_shape, spacing, len(lons))
    return grid
