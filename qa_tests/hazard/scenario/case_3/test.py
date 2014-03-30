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
import numpy
from nose.plugins.attrib import attr
from numpy.testing import assert_almost_equal

from openquake.engine import export
from openquake.engine.db import models
from qa_tests import _utils as qa_utils


# job.ini contains intensity_measure_types = PGA, SA(0.1)
class ScenarioHazardCase3TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id)
        actual = map(numpy.median, models.get_gmvs_per_site(output, 'PGA'))
        expected_medians_pga = [0.48155582, 0.21123045, 0.14484586]
        assert_almost_equal(actual, expected_medians_pga, decimal=2)

        actual = map(numpy.median, models.get_gmvs_per_site(output, 'SA(0.1)'))
        expected_medians_sa = [0.93913177, 0.40880148, 0.2692668]
        assert_almost_equal(actual, expected_medians_sa, decimal=2)
