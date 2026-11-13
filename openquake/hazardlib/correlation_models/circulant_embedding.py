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
from math import prod

import numpy
from openquake.baselib.geolibs import pyproj
from scipy.fft import next_fast_len
from scipy.spatial import cKDTree


MAX_GRID_CELL_RATIO = numpy.inf
GRID_TOLERANCE = 0.01


EPS = 1E-10

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


def _local_crs(lons, lats):
    """Return a transverse Mercator projection centred on the sites."""
    latitude = float(numpy.median(lats))
    if not -80 <= latitude <= 84:
        raise ValueError('Circulant embedding requires sites within the '
                         'latitude range [-80, 84]')
    # No zone boundaries: the central meridian is the middle of the extent.
    # The scale error is about 0.07% at 400 km from the central meridian.
    central = (float(numpy.min(lons)) + float(numpy.max(lons))) / 2
    return (f'+proj=tmerc +lon_0={central:.6f} +k=1 +datum=WGS84 '
            '+units=m +no_defs')


def _grid_spacing(x, y):
    """Estimate the projected spacing from nearest neighbours."""
    coordinates = numpy.column_stack((x, y))
    distances = cKDTree(coordinates).query(
        coordinates, k=2, workers=1)[0][:, 1]
    distances = distances[numpy.isfinite(distances) & (distances > 0)]
    if not len(distances):
        raise ValueError('Cannot determine the correlation grid spacing')
    return float(numpy.median(distances))


def _metric_crs(crs):
    # Covariance distances below assume projected coordinates in metres.
    try:
        projection = pyproj.CRS.from_user_input(crs)
    except pyproj.exceptions.CRSError as exc:
        raise ValueError('Invalid correlation grid projection') from exc
    if (not projection.is_projected or any(
            not numpy.isclose(axis.unit_conversion_factor, 1)
            for axis in projection.axis_info[:2])):
        raise ValueError('Correlation grid projection must use metres')
    return projection


@dataclass(frozen=True)
class RegularGridLayout:
    """Map geographic sites to the regular lattice used by CE.

    ``from_sites`` uses an explicit or recorded projection when available.
    Otherwise it tries local transverse Mercator and neighbouring UTM zones,
    fitting and validating the same axis-aligned lattice in each case.
    ``site_indices`` maps the original site order to flattened grid cells;
    holes remain unused cells in the enclosing rectangle.

    CE constructs stationary covariance lags from Euclidean distances between
    lattice cells. A fixed row/column offset must have the same displacement
    everywhere, giving the repeated covariance structure required by the FFT.
    Geographic grids built along parallels and meridians do not generally
    satisfy this condition. Substituting geographic pairwise distances would
    in general lose that structure, rather than merely change the projection.

    The projection is a local planar approximation to surface geometry, not
    an intrinsic requirement of CE; another suitable planar projection would
    require consistent support throughout grid detection and sampling. The
    covariance sampled here uses projected distances, not exact geodesic
    distances.

    ``grid_shape`` and ``spacing`` follow row/column order, with spacing in
    kilometres. ``projected_origin`` is northing/easting in metres, ``crs`` is
    a projection specification accepted by pyproj, and ``maximum_error`` is
    the largest distance in metres between an input site and its fitted
    lattice position.
    """

    grid_shape: tuple
    spacing: tuple
    site_indices: numpy.ndarray
    crs: str
    projected_origin: tuple
    maximum_error: float

    @classmethod
    def from_sites(cls, sites, max_cell_ratio=MAX_GRID_CELL_RATIO, crs=None):
        """Recover the original lattice, including sparse subsets."""
        lons = numpy.asarray(sites.lons, dtype=numpy.float64)
        lats = numpy.asarray(sites.lats, dtype=numpy.float64)
        if not len(lons) or len(lons) != len(lats):
            raise ValueError('Correlation grid requires matching coordinates')
        if not numpy.isfinite(lons).all() or not numpy.isfinite(lats).all():
            raise ValueError('Correlation grid coordinates must be finite')
        recorded = getattr(sites, 'grid_crs', None)
        if crs is not None or recorded:
            crs = crs if crs is not None else recorded
            hints = None
            if recorded and _metric_crs(crs).equals(_metric_crs(recorded)):
                hints = (getattr(sites, 'grid_spacing', None),
                         getattr(sites, 'grid_origin', None))
            return cls._projected(lons, lats, crs, max_cell_ratio, hints)
        # Existing site files were often prepared in UTM, without metadata.
        # Try the local projection first, then the median UTM zone and its
        # neighbours; changing the projection never relaxes the fit tolerance.
        candidates = [_local_crs(lons, lats)]
        zone = min(60, int((numpy.median(lons) + 180) // 6) + 1)
        base = 32600 if numpy.median(lats) >= 0 else 32700
        candidates.extend(f'EPSG:{base + z}' for z in
                          (zone, zone - 1, zone + 1) if 1 <= z <= 60)
        failures = []
        for candidate in candidates:
            try:
                return cls._projected(lons, lats, candidate, max_cell_ratio)
            except ValueError as exc:
                failures.append(exc)
        raise failures[0]

    @classmethod
    def _projected(cls, lons, lats, crs, max_cell_ratio, hints=None):
        # Fit in one metric CRS, or use a lattice retained before filtering.
        transformer = pyproj.Transformer.from_crs(
            4326, _metric_crs(crs), always_xy=True)
        x, y = transformer.transform(lons, lats)
        if not numpy.isfinite(x).all() or not numpy.isfinite(y).all():
            raise ValueError('Correlation grid projection is not finite')
        if hints and hints[0] is not None and hints[1] is not None:
            spacing_y, spacing_x = numpy.asarray(hints[0]) * 1000
            y0, x0 = hints[1]
        else:
            if len(lons) < 4:
                raise ValueError('Circulant embedding requires at least '
                                 'four grid sites')
            initial = _grid_spacing(x, y)
            ix = numpy.rint((x - x.min()) / initial).astype(numpy.int64)
            iy = numpy.rint((y - y.min()) / initial).astype(numpy.int64)
            if numpy.ptp(ix) == 0 or numpy.ptp(iy) == 0:
                raise ValueError('Correlation grid requires two rows and '
                                 'columns')
            spacing_x, x0 = numpy.polyfit(ix, x, 1)
            spacing_y, y0 = numpy.polyfit(iy, y, 1)
            ix = numpy.rint((x - x0) / spacing_x).astype(numpy.int64)
            iy = numpy.rint((y - y0) / spacing_y).astype(numpy.int64)
            spacing_x, x0 = numpy.polyfit(ix, x, 1)
            spacing_y, y0 = numpy.polyfit(iy, y, 1)
        if min(spacing_x, spacing_y) <= 0:
            raise ValueError('Correlation grid spacing must be positive')
        ix = numpy.rint((x - x0) / spacing_x).astype(numpy.int64)
        iy = numpy.rint((y - y0) / spacing_y).astype(numpy.int64)
        errors = numpy.hypot(
            x - (x0 + ix * spacing_x), y - (y0 + iy * spacing_y))
        tolerance = max(2.0, max(spacing_x, spacing_y) * GRID_TOLERANCE)
        if errors.max() > tolerance:
            raise ValueError(
                'Sites do not form an axis-aligned regular grid; '
                f'maximum coordinate error is {errors.max():g} m')
        minimum_x, minimum_y = ix.min(), iy.min()
        ix, iy = ix - minimum_x, iy - minimum_y
        nx, ny = max(2, int(ix.max()) + 1), max(2, int(iy.max()) + 1)
        indices = iy * nx + ix
        if len(numpy.unique(indices)) != len(indices):
            raise ValueError('Multiple sites occupy one correlation grid cell')
        if nx * ny > max_cell_ratio * len(indices):
            raise ValueError(
                'The enclosing correlation grid contains more '
                f'than {max_cell_ratio:g} cells per occupied site')
        return cls(
            (ny, nx), (float(spacing_y / 1000), float(spacing_x / 1000)),
            indices, str(crs),
            (float(y0 + minimum_y * spacing_y),
             float(x0 + minimum_x * spacing_x)), float(errors.max()))

    def cropped(self, indices):
        """Enclose selected cells without changing their projection or step."""
        rows, columns = numpy.divmod(indices, self.grid_shape[1])
        low_y, low_x = int(rows.min()), int(columns.min())
        shape = (max(2, int(rows.max()) - low_y + 1),
                 max(2, int(columns.max()) - low_x + 1))
        origin = (self.projected_origin[0] + low_y * self.spacing[0] * 1000,
                  self.projected_origin[1] + low_x * self.spacing[1] * 1000)
        return type(self)(
            shape, self.spacing, (rows - low_y) * shape[1] + columns - low_x,
            self.crs, origin, self.maximum_error)

    def grid_coordinates(self, sites):
        """Return fractional row and column coordinates for ``sites``."""
        transformer = pyproj.Transformer.from_crs(
            4326, self.crs, always_xy=True)
        if len(sites.lons) == 1:
            x, y = transformer.transform(
                float(sites.lons[0]), float(sites.lats[0]))
            x = numpy.array([x])
            y = numpy.array([y])
        else:
            x, y = transformer.transform(sites.lons, sites.lats)
        origin_y, origin_x = self.projected_origin
        spacing_y, spacing_x = self.spacing
        rows = (numpy.asarray(y) - origin_y) / (spacing_y * 1000)
        columns = (numpy.asarray(x) - origin_x) / (spacing_x * 1000)
        return rows, columns

    def expanded(self, sites, margin):
        """Return a grid enlarged around ``sites`` by ``margin`` cells."""
        if not isinstance(margin, (int, numpy.integer)) or margin < 0:
            raise ValueError('margin must be a non-negative integer')
        rows, columns = self.grid_coordinates(sites)
        rounded_rows = numpy.rint(rows)
        rounded_columns = numpy.rint(columns)
        rows = numpy.where(
            numpy.abs(rows - rounded_rows) <= GRID_TOLERANCE,
            rounded_rows, rows)
        columns = numpy.where(
            numpy.abs(columns - rounded_columns) <= GRID_TOLERANCE,
            rounded_columns, columns)
        if not len(rows):
            return self

        ny, nx = self.grid_shape
        lower_y = min(0, int(numpy.floor(rows.min())) - margin)
        lower_x = min(0, int(numpy.floor(columns.min())) - margin)
        upper_y = max(ny - 1, int(numpy.ceil(rows.max())) + margin)
        upper_x = max(nx - 1, int(numpy.ceil(columns.max())) + margin)
        if (lower_y, lower_x, upper_y, upper_x) == (
                0, 0, ny - 1, nx - 1):
            return self

        old_rows, old_columns = numpy.divmod(self.site_indices, nx)
        new_nx = upper_x - lower_x + 1
        indices = ((old_rows - lower_y) * new_nx +
                   old_columns - lower_x)
        spacing_y, spacing_x = self.spacing
        origin_y, origin_x = self.projected_origin
        origin = (origin_y + lower_y * spacing_y * 1000,
                  origin_x + lower_x * spacing_x * 1000)
        return type(self)(
            (upper_y - lower_y + 1, new_nx), self.spacing,
            indices, self.crs, origin, self.maximum_error)

    @property
    def occupancy(self):
        """Return the fraction of enclosing grid cells containing a site."""
        return len(self.site_indices) / numpy.prod(self.grid_shape)


def _embedding_shape(grid_shape, multiplier):
    """Return FFT-efficient dimensions for a periodic embedding."""
    # Twice the target extent prevents periodic wrap-around from changing
    # any covariance within the original grid. A nearby fast length makes
    # the transforms cheaper without changing that guarantee.
    return tuple(next_fast_len(max(1, 2 * multiplier * (size - 1)))
                 for size in grid_shape)


def _lag_distances(shape, spacing):
    """Return distances from the origin on the periodic grid."""
    ny, nx = shape
    # Each coordinate uses its shortest displacement around the torus. This
    # produces the first block row of the block-circulant covariance.
    y = numpy.minimum(numpy.arange(ny), ny - numpy.arange(ny))
    x = numpy.minimum(numpy.arange(nx), nx - numpy.arange(nx))
    return numpy.hypot(
        y[:, numpy.newaxis] * spacing[0],
        x[numpy.newaxis, :] * spacing[1])


def _covariance_lags(model, imts, shape, spacing, component, context):
    """Return cross-IMT covariance blocks for all periodic lags."""
    distances = _lag_distances(shape, spacing)
    num_imts = len(imts)
    # correlation_block returns IMT-major rows for every lag against one
    # origin site. Move the lag dimension first to obtain one M x M block at
    # every embedded grid cell.
    blocks = model.correlation_block(
        distances.reshape(-1, 1), imts, imts, component, context)
    return blocks.reshape(num_imts, -1, num_imts).transpose(
        1, 0, 2).reshape(*shape, num_imts, num_imts)


def _spectral_root(covariance_lags):
    # Factor bounded strips; full-size eigenvector temporaries can otherwise
    # exceed the retained factor by several times on large scenario grids.
    # A block-circulant covariance is diagonal in space after the FFT. What
    # remains at each frequency is only a small cross-IMT covariance matrix.
    spectrum = numpy.fft.rfft2(covariance_lags, axes=(0, 1))
    step = max(1, 65536 // spectrum.shape[1])
    scale = max(1.0, max(float(numpy.abs(spectrum[i:i + step]).max())
                         for i in range(0, len(spectrum), step)))
    tolerance = 100 * numpy.finfo(float).eps * scale
    # Check before averaging so a genuinely asymmetric model is not silently
    # hidden as numerical roundoff.
    # FFT roundoff accumulates with the number of embedded cells. Only values
    # within that scale-aware tolerance may be clipped; a material negative
    # value requires a larger embedding.
    eigen_tolerance = tolerance * prod(covariance_lags.shape[:2])
    minimum = numpy.inf
    # Form V sqrt(Lambda) V* once so every realization needs only one small
    # matrix-vector multiplication at each frequency.
    for start in range(0, len(spectrum), step):
        block = spectrum[start:start + step]
        transpose = block.swapaxes(-1, -2).conj()
        if not numpy.allclose(block, transpose, rtol=EPS, atol=tolerance):
            raise ValueError('The embedded spectral covariance is not '
                             'Hermitian')
        eigenvalues, eigenvectors = numpy.linalg.eigh((block + transpose) / 2)
        minimum = min(minimum, float(eigenvalues.min()))
        if minimum < -eigen_tolerance:
            return minimum, None
        scaled = eigenvectors * numpy.sqrt(
            eigenvalues.clip(min=0))[..., numpy.newaxis, :]
        block[:] = scaled @ eigenvectors.swapaxes(-1, -2).conj()
    return minimum, spectrum


def _embedding_bytes(shape, num_imts, output_sites):
    # Conservative peak setup/sampling bytes, before allocating a grid.
    cells = prod(shape)
    # Covariance lags, FFT storage, model evaluation temporaries and bounded
    # eigensolver strips. Drawing also retains the factor and FFT workspace.
    setup = 8 * cells * (4 * num_imts ** 2 + 40)
    sampling = (16 * shape[0] * (shape[1] // 2 + 1) * num_imts ** 2 +
                32 * cells * num_imts + 8 * output_sites * num_imts)
    return max(setup, sampling)


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
              context=None, site_indices=None, max_multiplier=8,
              memory_budget=None):
        """Build an embedding, enlarging it until its spectrum is PSD."""
        grid_shape = _pair(grid_shape, 'grid_shape', int)
        spacing = _pair(spacing, 'spacing', float)
        if not imts:
            raise ValueError('At least one IMT is required')
        if max_multiplier < 1:
            raise ValueError('max_multiplier must be positive')
        num_sites = (prod(grid_shape) if site_indices is None
                     else len(site_indices))
        minimum = numpy.nan
        for multiplier in range(1, max_multiplier + 1):
            # Extending the periodic domain reduces artificial interaction
            # across its boundary while preserving the requested covariance.
            embedded_shape = _embedding_shape(grid_shape, multiplier)
            required = _embedding_bytes(embedded_shape, len(imts), num_sites)
            if memory_budget is not None and required > memory_budget:
                raise ValueError('The circulant embedding requires at least '
                                 f'{required} workspace bytes; configured '
                                 f'budget is {int(memory_budget)} bytes')
            covariance_lags = _covariance_lags(
                model, imts, embedded_shape, spacing, component, context)
            minimum, root = _spectral_root(covariance_lags)
            if root is not None:
                indices = cls._validate_indices(site_indices, grid_shape)
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
        return int(self.num_imts * numpy.prod(self.embedded_shape))

    @property
    def output_size(self):
        """Number of correlated values returned for each realization."""
        return self.num_imts * len(self.site_indices)

    @property
    def nbytes(self):
        """Bytes retained by the spectral factor and output-cell mapping."""
        return self.spectral_root.nbytes + self.site_indices.nbytes

    @property
    def workspace_bytes_per_realization(self):
        """Conservative FFT workspace estimate for one realization."""
        return 32 * self.input_size + 8 * self.output_size

    def batch_size(self, memory_budget):
        """Return how many realizations fit in the workspace budget."""
        memory_budget = int(memory_budget)
        available = memory_budget - self.nbytes
        required = self.workspace_bytes_per_realization
        if available < required:
            raise ValueError(
                'The circulant embedding requires at least '
                f'{self.nbytes + required} workspace bytes')
        return max(1, available // required)

    def apply(self, samples):
        """Apply the embedding to columns of independent normal values."""
        samples = numpy.asarray(samples)
        if samples.ndim != 2 or samples.shape[0] != self.input_size:
            raise ValueError(
                f'Expected samples with shape ({self.input_size}, E), got '
                f'{samples.shape}')
        num_events = samples.shape[1]
        # Convert IMT-major columns to (event, y, x, IMT), leaving the last
        # axis ready for the small spectral matrix multiplication below.
        white = samples.reshape(
            self.num_imts, *self.embedded_shape, num_events)
        white = white.transpose(3, 1, 2, 0)
        transformed = numpy.fft.rfft2(white, axes=(1, 2))
        # Correlate the IMTs independently at every spatial frequency.
        correlated = numpy.einsum(
            'yxij,eyxj->eyxi', self.spectral_root, transformed)
        del transformed
        fields = numpy.fft.irfft2(
            correlated, s=self.embedded_shape, axes=(1, 2))
        del correlated
        nx = self.grid_shape[1]
        # Discard the periodic padding, apply the optional spatial mask, and
        # restore the IMT-major ordering expected by the GMF calculators.
        rows, columns = numpy.divmod(self.site_indices, nx)
        fields = fields[:, rows, columns, :]
        return fields.transpose(2, 1, 0).reshape(
            self.output_size, num_events)
