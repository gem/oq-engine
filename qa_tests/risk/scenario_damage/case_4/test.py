# Copyright (c) 2013, GEM Foundation.
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

import os

from nose.plugins.attrib import attr

from qa_tests import risk
from openquake.engine.db import models


# FIXME(lp). This is a regression test meant to exercise the sd-imt
# logic in the SR calculator. Data has not been validated


class ScenarioDamageRiskCase4TestCase(risk.End2EndRiskQATestCase):
    hazard_cfg = os.path.join(os.path.dirname(__file__), 'job_haz.ini')
    risk_cfg = os.path.join(os.path.dirname(__file__), 'job_damage.ini')

    @attr('qa', 'risk', 'scenario_damage', 'e2e')
    def test(self):
        self._run_test()

    def hazard_id(self):
        return models.Output.objects.latest('last_update').id

    def actual_data(self, job):
        per_asset = models.DmgDistPerAsset.objects.filter(
            dmg_state__risk_calculation=job.risk_calculation).order_by(
                'exposure_data', 'dmg_state')
        totals = models.DmgDistTotal.objects.filter(
            dmg_state__risk_calculation=job.risk_calculation).order_by(
                'dmg_state')
        return [[[m.mean, m.stddev] for m in per_asset],
                [[total.mean, total.stddev] for total in totals]]

    def expected_data(self):
        return [[[2799.26279971, 306.41197996],
                 [191.56511947, 277.20434751],
                 [9.17208082, 37.90451501],
                 [161.567248004, 261.144050148],
                 [428.700628134, 290.748630861],
                 [409.732123862, 378.117407054],
                 [612.243296942, 686.028439527],
                 [791.579191092, 530.835496],
                 [596.177511966, 704.389085655]],
                [[3573.07334466, 788.370392374],
                 [1411.84493869, 670.785311947],
                 [1015.08171665, 801.413598684]]]
