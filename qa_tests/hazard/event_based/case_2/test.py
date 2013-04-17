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
import shutil
import tempfile

from nose.plugins.attrib import attr
from openquake.engine.db import models
from openquake.engine.export import hazard as hazard_export
from qa_tests import _utils as qa_utils


class EventBasedHazardCase2TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        result_dir = tempfile.mkdtemp()

        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            expected_curve_poes = [0.0095, 0.00076, 0.000097, 0.0]

            job = self.run_hazard(cfg)

            # Test the poe values of the single curve:
            [actual_curve] = models.HazardCurveData.objects.filter(
                hazard_curve__output__oq_job=job.id,
                hazard_curve__imt__isnull=False)

            self.assert_equals_var_tolerance(
                expected_curve_poes, actual_curve.poes
            )
        finally:
            shutil.rmtree(result_dir)
