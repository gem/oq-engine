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

import os
import filecmp

from nose.plugins.attrib import attr
from qa_tests import _utils


class DisaggHazardCase1TestCase(_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'disagg')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        expected = os.path.join(os.path.dirname(__file__), 'expected_output')
        job = self.run_hazard(cfg, exports=['xml'])
        hc = job.hazard_calculation
        export_dir = os.path.join(hc.export_dir, 'calc_%d' % hc.id)
        dc = filecmp.dircmp(export_dir, expected)
        dc.report_full_close()
        # this is exporting several files in /tmp/disagg_case_2
        # as listed in job.ini
