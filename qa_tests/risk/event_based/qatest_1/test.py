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


from nose.plugins.attrib import attr as noseattr

from qa_tests import risk

from openquake.engine.db import models


class EventBaseQATestCase1(risk.CompleteTestCase,
                           risk.LogicTreeBasedTestCase,
                           risk.End2EndRiskQATestCase):
    hazard_cfg = os.path.join(os.path.dirname(__file__), 'job_haz.ini')
    risk_cfg = os.path.join(os.path.dirname(__file__), 'job_risk.ini')

    @noseattr('qa', 'risk', 'event_based', 'e2e')
    def test(self):
        self._run_test()

    def expected_output_containers(self):
        return []
