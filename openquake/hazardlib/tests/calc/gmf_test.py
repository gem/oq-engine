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
from unittest import mock

import numpy
import pandas
import pytest
from pyproj import Transformer
from scipy import stats

from openquake.baselib.performance import Monitor
from openquake.hazardlib.calc.gmf import (
    F32, GmfComputer, _truncated_normals)
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.correlation_models.base import CorrelationContext
from openquake.hazardlib.correlation_models.circulant_embedding import (
    CirculantEmbeddingFactor)
from openquake.hazardlib.correlation_models.spatial.heresi_miranda_2019 \
    import HeresiMiranda2019
from openquake.hazardlib.correlation_models.spatial.jayaram_baker_2009 import (
    JayaramBaker2009)
from openquake.hazardlib.correlation_models.spatial_cross_imt.du_ning_2021 \
    import DuNing2021
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.source.rupture import EBRupture
from openquake.hazardlib.tests.calc import _conditioned_gmfs_test_data as data


IMTS = [PGA(), SA(0.3)]


def build_computer(sites, factor=None, seed=7):
    computer = GmfComputer.__new__(GmfComputer)
    computer.cmaker = SimpleNamespace(truncation_level_within=3)
    computer.M = len(IMTS)
    computer.N = len(sites)
    computer.rng = numpy.random.default_rng(seed)
    computer.within_dist = stats.truncnorm(-3, 3)
    computer.within_event_model = DuNing2021()
    computer.sites = sites
    computer.imts = IMTS
    computer.correlation_context = CorrelationContext(mag=6.5)
    computer._within_event_factor = None
    computer._ce_factor = factor
    computer._ce_checked = factor is not None
    return computer


def regular_sites(shape):
    y, x = numpy.indices(shape)
    transformer = Transformer.from_crs(32610, 4326, always_xy=True)
    lons, lats = transformer.transform(
        500_000 + x.ravel() * 1_000,
        4_200_000 + y.ravel() * 1_000)
    return SiteCollection.from_points(lons, lats)


def build_full_computer(num_events=5):
    """Return a small, fully operational CE GMF computer."""
    cmaker = simple_cmaker(
        [data.ZeroMeanGMM()], ['PGA', 'SA(0.3)'])
    cmaker.oq.calculation_mode = 'scenario'
    cmaker.gmf_mon = Monitor()
    cmaker.gid = numpy.array([0])
    ebr = EBRupture(
        data.RUP, source_id=0, trt_smr=0, n_occ=num_events,
        id=0, e0=0)
    ebr.seed = 7
    return GmfComputer(
        ebr, regular_sites((2, 3)), cmaker, DuNing2021())


def collect_batches(batch_size):
    computer = build_full_computer()
    with mock.patch('openquake.hazardlib.calc.gmf.CE_MIN_SITES', 1), \
            mock.patch.object(
                GmfComputer, '_ce_batch_size', return_value=batch_size):
        batches = list(computer.compute_all_batches())
    return pandas.concat([batch[0] for batch in batches]), batches


def test_ce_selection():
    complete = regular_sites((2, 3))
    sites = complete.filtered([4, 0, 2])
    computer = build_computer(sites)
    with mock.patch('openquake.hazardlib.calc.gmf.CE_MIN_SITES', 1):
        factor = computer._get_ce_factor()

    assert isinstance(factor, CirculantEmbeddingFactor)
    assert factor.grid_shape == (2, 3)
    assert factor.output_size == len(IMTS) * len(sites)
    numpy.testing.assert_array_equal(factor.site_indices, [4, 0, 2])


def test_ce_batches():
    # Event-major random draws make the result independent of how the
    # configured workspace divides the realizations into FFT batches.
    sites = regular_sites((2, 3))
    factor = CirculantEmbeddingFactor.build(
        DuNing2021(), IMTS, (2, 3), 1.0)
    fixed = factor.spectral_root.nbytes
    per_realization = factor.workspace_bytes_per_realization

    first = build_computer(sites, factor)
    with mock.patch(
            'openquake.hazardlib.calc.gmf._correlation_budget',
            return_value=fixed + 2 * per_realization):
        batches = first._draw_within_eps(5)

    second = build_computer(sites, factor)
    with mock.patch(
            'openquake.hazardlib.calc.gmf._correlation_budget',
            return_value=fixed + 5 * per_realization):
        single = second._draw_within_eps(5)

    numpy.testing.assert_allclose(batches, single, atol=1E-6)
    assert batches.shape == (len(IMTS), len(sites), 5)
    assert batches.dtype == F32


def test_truncated_normals():
    # The low-memory inverse-CDF draw is equivalent to SciPy's sampler.
    expected = stats.truncnorm(-3, 3).rvs(
        (3, 4), numpy.random.default_rng(9))
    actual = _truncated_normals(
        (3, 4), 3, numpy.random.default_rng(9))
    numpy.testing.assert_allclose(actual, expected, atol=1E-15)


def test_gmf_batches():
    # Changing the output batch size must not change seeded realizations.
    single, one_batch = collect_batches(5)
    chunked, three_batches = collect_batches(2)

    assert [len(batch[0]) for batch in three_batches] == [12, 12, 6]
    assert [batch[2] for batch in three_batches] == [False, False, True]
    assert one_batch[0][2]
    numpy.testing.assert_array_equal(single.eid, chunked.eid)
    numpy.testing.assert_array_equal(single.sid, chunked.sid)
    numpy.testing.assert_array_equal(single.rlz, chunked.rlz)
    numpy.testing.assert_allclose(
        single[['PGA', 'SA(0.3)']], chunked[['PGA', 'SA(0.3)']])
    numpy.testing.assert_array_equal(
        chunked.eid, numpy.repeat(numpy.arange(5), 6))


def test_empty_gsim():
    # An event-based rupture can have no events assigned to one GSIM.
    class OtherGMM(data.ZeroMeanGMM):
        pass

    gsims = {
        data.ZeroMeanGMM(): numpy.array([0]),
        OtherGMM(): numpy.array([1])}
    cmaker = simple_cmaker(gsims, ['PGA', 'SA(0.3)'])
    cmaker.oq.calculation_mode = 'event_based'
    cmaker.gmf_mon = Monitor()
    cmaker.gid = numpy.array([0, 1])
    ebr = EBRupture(
        data.RUP, source_id=0, trt_smr=0, n_occ=1, id=0, e0=0)
    ebr.seed = 7
    computer = GmfComputer(
        ebr, regular_sites((2, 3)), cmaker, DuNing2021())
    get_eps = computer.between_event_model.get_inter_eps

    def reject_empty(imts, num_events, rng):
        assert num_events
        return get_eps(imts, num_events, rng)

    with mock.patch('openquake.hazardlib.calc.gmf.CE_MIN_SITES', 1), \
            mock.patch.object(
                computer.between_event_model, 'get_inter_eps',
                side_effect=reject_empty):
        batches = list(computer.compute_all_batches())

    assert len(batches) == 1
    assert len(batches[0][0]) == 6


def test_ce_scaled_once():
    # CE returns normalized correlated residuals, so the target-site phi is
    # applied afterward and the legacy spatial factor must not run again.
    computer = GmfComputer.__new__(GmfComputer)
    computer.cmaker = SimpleNamespace(
        oq=SimpleNamespace(mea_tau_phi=False),
        truncation_level_within=3,
        truncation_level_between=3)
    computer.within_event_model = JayaramBaker2009(False)
    computer._ce_factor = object()
    computer.between_eps = numpy.zeros((2, 1), F32)
    computer.sig = numpy.zeros((2, 1), F32)
    mean = numpy.zeros(2, F32)
    tau = numpy.zeros(2, F32)
    phi = numpy.array([0.5, 1.5], F32)
    within_eps = numpy.array([[1.0, 2.0], [3.0, 4.0]], F32)
    gsim = SimpleNamespace(DEFINED_FOR_STANDARD_DEVIATION_TYPES={
        StdDev.INTER_EVENT, StdDev.INTRA_EVENT})

    with mock.patch.object(
            computer.within_event_model, 'apply_correlation',
            side_effect=AssertionError('correlated twice')):
        gmfs = computer._compute(
            (mean, numpy.ones(2, F32), tau, phi), 0, PGA(), gsim,
            within_eps, numpy.array([0, 1]))

    numpy.testing.assert_allclose(
        gmfs, numpy.exp(phi[:, numpy.newaxis] * within_eps))


def test_memory_guard():
    computer = build_computer(regular_sites((2, 3)))
    computer.within_event_model = HeresiMiranda2019()
    with mock.patch(
            'openquake.hazardlib.calc.gmf._correlation_budget',
            return_value=1):
        with pytest.raises(ValueError, match='not enabled'):
            computer._get_ce_factor()
