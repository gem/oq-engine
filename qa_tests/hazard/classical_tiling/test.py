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

import StringIO
import numpy
import os
import shutil
import filecmp
import tempfile

from nose.plugins.attrib import attr

from openquake.commonlib.tests import check_equal
from openquake.engine.db import models
from openquake.engine.export import core as hazard_export
from qa_tests import _utils as qa_utils
from qa_tests._utils import BaseQATestCase, compare_hazard_curve_with_csv
from openquake.qa_tests_data.classical_tiling import case_1

aaae = numpy.testing.assert_array_almost_equal

   
def assert_equal_files(dcmp):
    for name in dcmp.diff_files:
        raise AssertionError("diff_file %s found in %s and %s" %
                             (name, dcmp.left, dcmp.right))
    for sub_dcmp in dcmp.subdirs.values():
        assert_equal_files(sub_dcmp)


class ClassicalTilingCase1TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        cwd = os.path.dirname(case_1.__file__)

        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(cwd, 'job.ini')
        expected = os.path.join(cwd, 'expected')
        job = self.run_hazard(cfg, exports='csv')
        export_dir = os.path.join(
            job.get_param('export_dir'), 'calc_%d' % job.id)

        # compare the directories and print a report
        dc = filecmp.dircmp(expected, export_dir)
        dc.report_full_closure()

        assert_equal_files(dc)

        shutil.rmtree(result_dir)
