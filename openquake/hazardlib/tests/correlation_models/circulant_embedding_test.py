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

import numpy
import pytest

from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.circulant_embedding import (
    CirculantEmbeddingFactor)
from openquake.hazardlib.correlation_models.spatial_cross_imt.du_ning_2021 \
    import DuNing2021
from openquake.hazardlib.imt import PGA, SA


IMTS = [PGA(), SA(0.3)]


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
