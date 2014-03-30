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

from nose.plugins.attrib import attr as noseattr

from qa_tests import risk


class ScenarioOccupantsQATestCase1(risk.FixtureBasedQATestCase):
    output_type = "gmf_scenario"
    hazard_calculation_fixture = 'Scenario QA Test for occupants'

    @noseattr('qa', 'risk', 'scenario')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        latest_loss_map = job.output_set.filter(
            output_type="loss_map", loss_map__loss_type="fatalities").latest(
                'last_update').loss_map
        latest_aggregated = job.output_set.filter(
            output_type="aggregate_loss",
            aggregate_loss__loss_type="fatalities").latest(
                'last_update').aggregate_loss

        return [(d.value, d.std_dev)
                for d in latest_loss_map.lossmapdata_set.all().order_by(
                'asset_ref')] + [
                    (latest_aggregated.mean, latest_aggregated.std_dev)]

    def expected_data(self):
        return [(0.40754604, 0.14661467),
                (1.27516318,  0.91571143),
                (1.4329613, 0.92721498)] + [(3.11983577,  1.10750248)]

# For NIGHT:

# Asset 1
# Mean: 0.8981603187500
# Std Dev: 0.479301017326327

# Asset 2
# Mean: 1.67389744650000
# Std Dev: 1.64243715167681

# Asset 3
# Mean: 1.60533374061429
# Std Dev: 1.13698143346693

# Mean: 4.1774
# Std Dev: 3.1036
