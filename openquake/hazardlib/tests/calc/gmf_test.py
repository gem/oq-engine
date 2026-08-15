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
from scipy import stats

from openquake.hazardlib.calc.gmf import F32, GmfComputer
from openquake.hazardlib.correlation_models.base import (
    CorrelationContext, ResidualComponent,
    SpatialCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.spatial.jayaram_baker_2009 import (
    JayaramBaker2009)
from openquake.hazardlib.imt import PGA, SA


class RecordingJointModel(SpatialCrossIMTCorrelationModel):
    calibrated_component = ResidualComponent.WITHIN_EVENT

    def factor(self, sites, imts, component=None, context=None,
               ensure_psd=True):
        self.call = sites, imts, component, context
        self.factor_calls = getattr(self, 'factor_calls', 0) + 1

        class Factor:
            @staticmethod
            def apply(samples):
                reshaped = samples.reshape(2, 2, samples.shape[-1])
                return (reshaped[::-1] * 2).reshape(samples.shape)

        return Factor()


def build_computer(model, seed=7):
    computer = GmfComputer.__new__(GmfComputer)
    computer.cmaker = SimpleNamespace(truncation_level_within=3)
    computer.M = 2
    computer.N = 2
    computer.rng = numpy.random.default_rng(seed)
    computer.within_dist = stats.truncnorm(-3, 3)
    computer.within_event_model = model
    computer.sites = range(2)
    computer.imts = [PGA(), SA(1.0)]
    computer.correlation_context = CorrelationContext(mag=6.5)
    computer._within_event_factor = None
    return computer


def draw_uncorrelated(seed, num_events):
    rng = numpy.random.default_rng(seed)
    distribution = stats.truncnorm(-3, 3)
    return numpy.asarray([
        distribution.rvs((2, num_events), rng).astype(F32)
        for _ in range(2)])


def test_joint_within_event_model_correlates_all_imts_and_sites():
    model = RecordingJointModel()
    computer = build_computer(model)
    samples = computer._draw_within_eps(3)

    numpy.testing.assert_allclose(samples, draw_uncorrelated(7, 3)[::-1] * 2)
    sites, imts, component, context = model.call
    assert sites is computer.sites
    assert imts is computer.imts
    assert component == ResidualComponent.WITHIN_EVENT
    assert context is computer.correlation_context
    assert samples.dtype == F32
    computer._draw_within_eps(1)
    assert model.factor_calls == 1


def test_spatial_model_preserves_the_existing_per_imt_sampling_path():
    computer = build_computer(JayaramBaker2009(False))
    numpy.testing.assert_array_equal(
        computer._draw_within_eps(3), draw_uncorrelated(7, 3))
