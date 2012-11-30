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

import numpy
import os

from nose.plugins.attrib import attr
from openquake.db import models
from qa_tests import _utils as qa_utils
from qa_tests.hazard.disagg.case_1 import _test_data as test_data


class DisaggHazardCase1TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'disagg')
    def test(self):
        aaae = numpy.testing.assert_array_almost_equal
        # TODO(LB): This is a temporary test case which tests for stability
        # until we can write proper QA tests.

        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

        job = self.run_hazard(cfg)

        results = models.DisaggResult.objects.filter(output__oq_job=job)

        poe_002_pga = results.filter(imt='PGA', poe=0.02)
        rlz1, rlz2 = poe_002_pga.order_by('lt_realization')

        aaae(test_data.RLZ_1_POE_002_PGA, rlz1.matrix)
        aaae(test_data.RLZ_2_POE_002_PGA, rlz2.matrix)

        poe_002_sa = results.filter(imt='SA', poe=0.02)
        rlz1, rlz2 = poe_002_sa.order_by('lt_realization')

        aaae(test_data.RLZ_1_POE_002_SA, rlz1.matrix)
        aaae(test_data.RLZ_2_POE_002_SA, rlz2.matrix)

        poe_01_pga = results.filter(imt='PGA', poe=0.1)
        rlz1, rlz2 = poe_01_pga.order_by('lt_realization')

        aaae(test_data.RLZ_1_POE_01_PGA, rlz1.matrix)
        aaae(test_data.RLZ_2_POE_01_PGA, rlz2.matrix)

        poe_01_sa= results.filter(imt='SA', poe=0.1)
        rlz1, rlz2 = poe_01_sa.order_by('lt_realization')

        aaae(test_data.RLZ_1_POE_01_SA, rlz1.matrix)
        aaae(test_data.RLZ_2_POE_01_SA, rlz2.matrix)
