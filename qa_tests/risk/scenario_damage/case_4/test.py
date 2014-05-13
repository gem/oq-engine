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


# FIXME(lp). This is a regression test meant to exercise the sd-imt
# logic in the SR calculator. Data has not been validated


class ScenarioDamageRiskCase4TestCase(risk.FixtureBasedQATestCase):
    output_type = 'gmf_scenario'
    hazard_calculation_fixture = 'Scenario Damage QA Test 4'

    @attr('qa', 'risk', 'scenario_damage')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        per_asset = models.DmgDistPerAsset.objects.filter(
            dmg_state__risk_calculation=job.risk_calculation).order_by(
            'exposure_data', 'dmg_state')
        totals = models.DmgDistTotal.objects.filter(
            dmg_state__risk_calculation=job.risk_calculation).order_by(
            'dmg_state')
        data = [[[m.mean, m.stddev] for m in per_asset],
                [[total.mean, total.stddev] for total in totals]]
        return data

    def expected_data(self):
        return [[[2839.99487945302, 260.107936318162],
                 [154.207170037728, 240.669053166515],
                 [5.79795050924058, 24.2361847686849],
                 [162.093574777342, 262.704324187903],
                 [436.941603707819, 294.180204333271],
                 [400.964821514838, 376.14843653929],
                 [506.964203111531, 645.131915664689],
                 [774.865676844215, 535.513668479813],
                 [718.170120044255, 744.033150727349]],
                [[3509.0526573419, 736.44555857085],
                 [1366.01445058976, 657.913617460034],
                 [1124.93289206833, 838.747142746392]]]
