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
import tempfile
import shutil
from nose.plugins.attrib import attr
from numpy.testing import assert_almost_equal

from openquake import export
from qa_tests import _utils as qa_utils


class ScenarioHazardCase1TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id)

        actual = list(qa_utils.get_medians(output, 'PGA'))
        expected_medians = [0.48155582, 0.21123045, 0.14484586]

        assert_almost_equal(actual, expected_medians, decimal=2)

    @attr('qa', 'hazard', 'scenario')
    def test_export(self):
        result_dir = tempfile.mkdtemp()

        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            job = self.run_hazard(cfg)
            [output] = export.core.get_outputs(job.id)
            [exported_file] = export.hazard.export(
                output.id, result_dir)
            self.assertEqual(open(exported_file).read().count('\n'), 314)
        finally:
            shutil.rmtree(result_dir)
