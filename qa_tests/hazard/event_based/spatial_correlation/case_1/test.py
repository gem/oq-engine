# Copyright (c) 2010-2013, GEM Foundation.
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
from openquake.engine.db import models
from qa_tests import _utils as qa_utils
from qa_tests.hazard.event_based.spatial_correlation import _utils as sc_utils


class EBHazardSpatialCorrelCase1TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

        job = self.run_hazard(cfg)

        import nose; nose.tools.set_trace()
