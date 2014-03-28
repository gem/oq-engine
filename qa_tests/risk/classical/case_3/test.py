# Copyright (c) 2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


from nose.plugins.attrib import attr

from qa_tests import risk

from openquake.engine.db import models


class ClassicalRiskCase3TestCase(
        risk.CompleteTestCase, risk.FixtureBasedQATestCase):
    hazard_calculation_fixture = "Classical PSHA - Loss fractions QA test"

    @attr('qa', 'risk', 'classical')
    def test(self):
        self._run_test()

    items_per_output = None

    def expected_output_data(self):
        b1 = models.Output.HazardMetadata(
            investigation_time=50.0,
            statistics=None, quantile=None,
            sm_path=('b1',), gsim_path=('b1',))

        values = self._csv('fractions', dtype="f4, f4, S3, f4, f4")

        return zip(
            [("loss_fraction", b1, None, None, "taxonomy", 0.1,
              "structural") + ('%.5f' % lon, '%.5f' % lat, taxonomy)
             for lon, lat, taxonomy, _loss, _fraction in values],
            [models.LossFractionData(absolute_loss=v) for v in values['f3']])
