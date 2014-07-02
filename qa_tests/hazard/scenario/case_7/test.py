# Copyright (c) 2010-2014, GEM Foundation.
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

from openquake.engine import export
from openquake.engine.db import models
from qa_tests import _utils as qa_utils


class ScenarioHazardCase7TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id, 'gmf_scenario')
        gmfs = list(models.get_gmvs_per_site(output, 'PGA', sort=lambda x: x))
        realizations = 1e5
        first_value = 0.5
        second_value = 1.0
        gmfs_within_range_fst = qa_utils.count(first_value, gmfs[0], gmfs[1])
        gmfs_within_range_snd = qa_utils.count(second_value, gmfs[0], gmfs[1])

        self.assertAlmostEqual(gmfs_within_range_fst / realizations,
                               0.02, places=2)
        self.assertAlmostEqual(gmfs_within_range_snd / realizations,
                               0.002, places=3)
