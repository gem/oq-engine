# Copyright (c) 2010-2012, GEM Foundation.
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


# TODO(lp). This is a regression test that checks for the presence of
# the results
class EventBasedRiskCase3TestCase(risk.End2EndRiskQATestCase):
    hazard_cfg = os.path.join(os.path.dirname(__file__), 'job_haz.ini')
    risk_cfg = os.path.join(os.path.dirname(__file__), 'job_risk.ini')

    output_type = "gmf"

    @noseattr('qa', 'risk', 'event_based', 'e2e')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        loss_fraction = models.LossFraction.objects.get(
            variable='magnitude_distance',
            output__oq_job=job)

        fractions = [fractions
                     for fractions in loss_fraction.iteritems()]

        return [node[0] for node in fractions]

    def expected_data(self):
        return [80.838823, 29.386172], [80.988823, 29.611172]
