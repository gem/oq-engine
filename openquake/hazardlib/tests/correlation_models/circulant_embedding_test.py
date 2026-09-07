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

from types import SimpleNamespace

import numpy
import pytest
from pyproj import Transformer

from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.circulant_embedding import (
    CirculantEmbeddingFactor, RegularGridLayout)
from openquake.hazardlib.correlation_models.spatial.jayaram_baker_2009 import (
    JayaramBaker2009)
from openquake.hazardlib.correlation_models.spatial_cross_imt.du_ning_2021 \
    import DuNing2021
from openquake.hazardlib.imt import PGA, SA


IMTS = [PGA(), SA(0.3)]


def geographic_grid(shape, missing=(), perturb=None):
    """Return rounded geographic coordinates for a UTM grid."""
    y, x = numpy.indices(shape)
    keep = numpy.ones(shape, dtype=bool)
    for row, column in missing:
        keep[row, column] = False
    x = 500_000 + x[keep] * 1_000
    y = 4_200_000 + y[keep] * 1_000
    transformer = Transformer.from_crs(32610, 4326, always_xy=True)
    lons, lats = transformer.transform(x, y)
    lons = numpy.round(lons, 5)
    lats = numpy.round(lats, 5)
    if perturb is not None:
        lons[0] += perturb
    order = numpy.arange(len(lons))[::-1]
    return SimpleNamespace(lons=lons[order], lats=lats[order]), order


def dense_covariance(model, imts, shape, spacing):
    """Return the ordinary covariance for every cell in a small grid."""
    y, x = numpy.indices(shape)
    coordinates = numpy.column_stack(
        (y.ravel() * spacing[0], x.ravel() * spacing[1]))
    distances = numpy.linalg.norm(
        coordinates[:, numpy.newaxis] - coordinates[numpy.newaxis, :],
        axis=-1)
    return model.correlation_block(
        distances, imts, component=ResidualComponent.WITHIN_EVENT)


@pytest.mark.parametrize('shape', [(2, 3), (2, 14)])
def test_exact_covariance(shape):
    # Applying the factor to an identity basis recovers its covariance
    # deterministically, without a Monte Carlo tolerance. The second grid
    # also exercises an odd FFT-efficient embedding dimension.
    model = DuNing2021()
    spacing = (2.0, 3.0)
    factor = CirculantEmbeddingFactor.build(
        model, IMTS, shape, spacing,
        ResidualComponent.WITHIN_EVENT)
    applied = factor.apply(numpy.eye(factor.input_size))
    actual = applied @ applied.T
    expected = dense_covariance(model, IMTS, shape, spacing)
    numpy.testing.assert_allclose(actual, expected, atol=2E-14)


def test_spatial_covariance():
    # A traditional spatial model becomes a block-diagonal multivariate
    # field, retaining independence between its different IMTs.
    model = JayaramBaker2009(False)
    shape = (2, 3)
    spacing = (2.0, 3.0)
    factor = CirculantEmbeddingFactor.build(
        model, IMTS, shape, spacing,
        ResidualComponent.WITHIN_EVENT)
    applied = factor.apply(numpy.eye(factor.input_size))
    actual = applied @ applied.T
    expected = dense_covariance(model, IMTS, shape, spacing)
    numpy.testing.assert_allclose(actual, expected, atol=2E-14)


def test_mask():
    # A filtered grid retains both the requested cell order and IMT-major
    # output ordering.
    model = DuNing2021()
    shape = (2, 3)
    full = CirculantEmbeddingFactor.build(model, IMTS, shape, 1.0)
    masked = CirculantEmbeddingFactor.build(
        model, IMTS, shape, 1.0, site_indices=[4, 0, 2])
    samples = numpy.arange(full.input_size * 2, dtype=float).reshape(
        full.input_size, 2)
    expected = full.apply(samples).reshape(len(IMTS), -1, 2)
    expected = expected[:, [4, 0, 2]].reshape(masked.output_size, 2)
    numpy.testing.assert_allclose(masked.apply(samples), expected)


def test_layout():
    # Rounded and unordered geographic coordinates recover their projected
    # grid cells; an unoccupied interior cell remains part of the envelope.
    sites, order = geographic_grid((3, 4), missing=[(1, 2)])
    layout = RegularGridLayout.from_sites(sites)
    expected = numpy.delete(numpy.arange(12), 6)[order]

    assert layout.grid_shape == (3, 4)
    numpy.testing.assert_allclose(layout.spacing, (1, 1), rtol=1E-3)
    numpy.testing.assert_array_equal(layout.site_indices, expected)
    assert layout.maximum_error < 1
    assert layout.occupancy == 11 / 12

    rows, columns = layout.grid_coordinates(sites)
    actual = numpy.rint(rows).astype(int) * 4
    actual += numpy.rint(columns).astype(int)
    numpy.testing.assert_array_equal(actual, expected)


def test_expanded_layout():
    sites, _ = geographic_grid((3, 4))
    layout = RegularGridLayout.from_sites(sites)
    expanded = layout.expanded(sites, margin=2)

    assert expanded.grid_shape == (7, 8)
    rows, columns = expanded.grid_coordinates(sites)
    assert rows.min() > 1.99
    assert columns.min() > 1.99
    assert rows.max() < 4.01
    assert columns.max() < 5.01
    expected = numpy.rint(rows).astype(int) * 8
    expected += numpy.rint(columns).astype(int)
    numpy.testing.assert_array_equal(expanded.site_indices, expected)


def test_irregular_layout():
    sites, _ = geographic_grid((3, 4), perturb=0.002)
    with pytest.raises(ValueError, match='regular UTM grid'):
        RegularGridLayout.from_sites(sites)


def test_padding():
    # This physical extent is too short for the model's long-range
    # components at the minimal embedding size.
    factor = CirculantEmbeddingFactor.build(
        DuNing2021(), [PGA(), SA(0.3), SA(1.0), SA(3.0)],
        (12, 11), 10.0, max_multiplier=2)
    assert factor.embedding_multiplier == 2
    assert factor.minimum_eigenvalue >= 0


def test_indefinite():
    with pytest.raises(ValueError, match='not positive semidefinite'):
        CirculantEmbeddingFactor.build(
            DuNing2021(), [PGA(), SA(0.3), SA(1.0), SA(3.0)],
            (12, 11), 10.0, max_multiplier=1)


def test_input_shape():
    factor = CirculantEmbeddingFactor.build(
        DuNing2021(), IMTS, (2, 3), 1.0)
    with pytest.raises(ValueError, match='Expected samples with shape'):
        factor.apply(numpy.ones((factor.input_size - 1, 2)))


def test_batch_size():
    factor = CirculantEmbeddingFactor.build(
        DuNing2021(), IMTS, (2, 3), 1.0)
    fixed = factor.spectral_root.nbytes
    per_realization = factor.workspace_bytes_per_realization

    assert factor.batch_size(fixed + 3 * per_realization) == 3
    with pytest.raises(ValueError, match='requires at least'):
        factor.batch_size(fixed + per_realization - 1)


@pytest.mark.parametrize('kwargs, message', [
    ({'grid_shape': (2, 0)}, 'grid_shape values must be positive'),
    ({'spacing': (1, 0)}, 'spacing values must be positive'),
    ({'site_indices': [0, 0]}, 'must not contain duplicates'),
    ({'site_indices': [6]}, 'out-of-grid cell'),
])
def test_grid_validation(kwargs, message):
    arguments = dict(
        model=DuNing2021(), imts=IMTS, grid_shape=(2, 3), spacing=1.0)
    arguments.update(kwargs)
    with pytest.raises(ValueError, match=message):
        CirculantEmbeddingFactor.build(**arguments)
