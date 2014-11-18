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

import numpy
import os
import shutil
import tempfile

from nose.plugins.attrib import attr
from openquake.engine.db import models
from openquake.engine.export import core as hazard_export
from openquake.commonlib.tests import check_equal
from qa_tests import _utils as qa_utils


class ClassicalHazardCase7TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            expected_curve_poes_b1 = [0.86466, 0.82460, 0.36525]
            expected_curve_poes_b2 = [0.63212, 0.61186, 0.25110]
            expected_mean_poes = [0.794898, 0.760778, 0.331005]

            job = self.run_hazard(cfg)

            # Test the poe values for the two curves.
            actual_curve_b1, actual_curve_b2 = (
                models.HazardCurveData.objects
                .filter(hazard_curve__output__oq_job=job.id,
                        hazard_curve__lt_realization__isnull=False)
                .order_by('hazard_curve__lt_realization__lt_model__sm_lt_path')
            )

            # Sanity check, to make sure we have the curves ordered correctly:
            self.assertEqual(
                ['b1'], actual_curve_b1.hazard_curve.lt_realization.sm_lt_path)
            self.assertEqual(
                ['b2'], actual_curve_b2.hazard_curve.lt_realization.sm_lt_path)

            numpy.testing.assert_array_almost_equal(
                expected_curve_poes_b1, actual_curve_b1.poes, decimal=3)

            numpy.testing.assert_array_almost_equal(
                expected_curve_poes_b2, actual_curve_b2.poes, decimal=3)

            # Test the mean curve:
            [mean_curve] = models.HazardCurveData.objects\
                .filter(hazard_curve__output__oq_job=job.id,
                        hazard_curve__statistics='mean')
            numpy.testing.assert_array_almost_equal(
                expected_mean_poes, mean_curve.poes, decimal=3)

            # Test the exports as well:
            exported_file_b1 = hazard_export.export(
                actual_curve_b1.hazard_curve.output.id, result_dir)
            check_equal(__file__, 'expected_b1.xml', exported_file_b1)

            exported_file_b2 = hazard_export.export(
                actual_curve_b2.hazard_curve.output.id, result_dir)
            check_equal(__file__, 'expected_b2.xml', exported_file_b2)

            # mean:
            exported_file_mean = hazard_export.export(
                mean_curve.hazard_curve.output.id, result_dir)
            check_equal(__file__, 'expected_mean.xml',
                           exported_file_mean)
        except:
            raise
        else:
            shutil.rmtree(result_dir)
