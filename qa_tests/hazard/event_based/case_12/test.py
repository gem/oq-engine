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
import shutil
import tempfile

from nose.plugins.attrib import attr
from openquake.db import models
from qa_tests import _utils as qa_utils


class EventBasedHazardCase12TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'event_based')
    def test(self):
        result_dir = tempfile.mkdtemp()
        aaae = numpy.testing.assert_array_almost_equal

        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            expected_curve_poes = [0.75421006, 0.08098179, 0.00686616]

            job = self.run_hazard(cfg)

            # Test the poe values of the single curve:
            [curve] = models.HazardCurveData.objects.filter(
                hazard_curve__output__oq_job=job.id)

            aaae(expected_curve_poes, curve.poes, decimal=2)
        finally:
            shutil.rmtree(result_dir)
