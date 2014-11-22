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
import tempfile

from nose.plugins.attrib import attr

from openquake.commonlib.tests import check_equal
from openquake.engine.db import models
from openquake.engine.export import core as hazard_export
from qa_tests import _utils as qa_utils
from qa_tests._utils import BaseQATestCase, compare_hazard_curve_with_csv
from openquake.qa_tests_data.classical import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8, case_9,
    case_10, case_11, case_12, case_13, case_14, case_15, case_16)

aaae = numpy.testing.assert_array_almost_equal


class ClassicalHazardCase1TestCase(qa_utils.BaseQATestCase):

    EXPECTED_PGA_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves sourceModelTreePath="b1" gsimTreePath="b1" IMT="PGA" investigationTime="1.0">
    <IMLs>1.000000000E-01 4.000000000E-01 6.000000000E-01</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>4.570134863E-01 5.862678774E-02 6.866164397E-03</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""

    EXPECTED_SA_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves sourceModelTreePath="b1" gsimTreePath="b1" IMT="SA" investigationTime="1.0" saPeriod="0.1" saDamping="5.0">
    <IMLs>1.000000000E-01 4.000000000E-01 6.000000000E-01</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>6.086747647E-01 3.308304637E-01 2.014712169E-01</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_1.__file__), 'job.ini')
        expected_curve_pga = [0.4570, 0.0587, 0.0069]
        expected_curve_sa = [
            0.608675003748, 0.330831513139, 0.201472214825
        ]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        curves = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id
        )

        [pga_curve] = curves.filter(hazard_curve__imt='PGA')
        numpy.testing.assert_array_almost_equal(
            expected_curve_pga, pga_curve.poes, decimal=4
        )

        [sa_curve] = curves.filter(
            hazard_curve__imt='SA', hazard_curve__sa_period=0.1
        )
        numpy.testing.assert_array_almost_equal(
            expected_curve_sa, sa_curve.poes, decimal=4
        )

        # Test the exports as well:
        exported_file = hazard_export.export(
            pga_curve.hazard_curve.output.id, result_dir)
        self.assert_xml_equal(
            StringIO.StringIO(self.EXPECTED_PGA_XML), exported_file)

        exported_file = hazard_export.export(
            sa_curve.hazard_curve.output.id, result_dir)
        self.assert_xml_equal(
            StringIO.StringIO(self.EXPECTED_SA_XML), exported_file)

        shutil.rmtree(result_dir)


class ClassicalHazardCase2TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_2.__file__), 'job.ini')
        expected_curve_poes = [0.0095, 0.00076, 0.000097, 0.0]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        [actual_curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes, actual_curve.poes, decimal=3)

        # Test the export as well:
        exported_file = hazard_export.export(
            actual_curve.hazard_curve.output.id, result_dir)
        check_equal(case_2.__file__, 'expected_hazard_curves.xml',
                    exported_file)
        shutil.rmtree(result_dir)


class ClassicalHazardCase3TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_3.__file__), 'job.ini')
        expected_curve_poes = [0.63212, 0.47291, 0.04084]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        [actual_curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes, actual_curve.poes, decimal=2)

        # Test the export as well:
        exported_file = hazard_export.export(
            actual_curve.hazard_curve.output.id, result_dir)
        check_equal(case_3.__file__, 'expected_hazard_curves.xml',
                    exported_file)

        shutil.rmtree(result_dir)


class ClassicalHazardCase4TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_4.__file__), 'job.ini')
        expected_curve_poes = [0.63212, 0.61186, 0.25110]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        [actual_curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes, actual_curve.poes, decimal=3)

        # Test the export as well:
        exported_file = hazard_export.export(
            actual_curve.hazard_curve.output.id, result_dir)
        check_equal(case_4.__file__, 'expected_hazard_curves.xml',
                    exported_file)

        shutil.rmtree(result_dir)


class ClassicalHazardCase5TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_5.__file__), 'job.ini')
        expected_curve_poes = [0.632120, 0.54811, 0.15241]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        [actual_curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes, actual_curve.poes, decimal=3)

        # Test the export as well:
        exported_file = hazard_export.export(
            actual_curve.hazard_curve.output.id, result_dir)
        check_equal(case_5.__file__, 'expected_hazard_curves.xml',
                    exported_file)

        shutil.rmtree(result_dir)


class ClassicalHazardCase6TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_6.__file__), 'job.ini')
        expected_curve_poes = [0.86466, 0.82460, 0.36525]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        [actual_curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes, actual_curve.poes, decimal=2)

        # Test the export as well:
        exported_file = hazard_export.export(
            actual_curve.hazard_curve.output.id, result_dir)
        check_equal(case_6.__file__, 'expected_hazard_curves.xml',
                    exported_file)

        shutil.rmtree(result_dir)


class ClassicalHazardCase7TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_7.__file__), 'job.ini')
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
        check_equal(case_7.__file__, 'expected_b1.xml', exported_file_b1)

        exported_file_b2 = hazard_export.export(
            actual_curve_b2.hazard_curve.output.id, result_dir)
        check_equal(case_7.__file__, 'expected_b2.xml', exported_file_b2)

        # mean:
        exported_file_mean = hazard_export.export(
            mean_curve.hazard_curve.output.id, result_dir)
        check_equal(case_7.__file__, 'expected_mean.xml', exported_file_mean)

        shutil.rmtree(result_dir)


class ClassicalHazardCase8TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_8.__file__), 'job.ini')
        expected_curve_poes_b1_b2 = [0.095163, 0.012362, 0.002262, 0.0]
        expected_curve_poes_b1_b3 = [0.009950, 0.00076, 9.99995E-6, 0.0]
        expected_curve_poes_b1_b4 = [0.0009995, 4.5489E-5, 4.07365E-6, 0.0]

        job = self.run_hazard(cfg)

        # Test the poe values for the three curves:
        curve_b1_b2, curve_b1_b3, curve_b1_b4 = (
            models.HazardCurveData.objects
            .filter(hazard_curve__output__oq_job=job.id)
            .order_by('hazard_curve__lt_realization__lt_model__sm_lt_path')
        )

        # Sanity check, to make sure we have the curves ordered correctly:
        self.assertEqual(
            ['b1', 'b2'],
            curve_b1_b2.hazard_curve.lt_realization.sm_lt_path)
        self.assertEqual(
            ['b1', 'b3'],
            curve_b1_b3.hazard_curve.lt_realization.sm_lt_path)
        self.assertEqual(
            ['b1', 'b4'],
            curve_b1_b4.hazard_curve.lt_realization.sm_lt_path)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes_b1_b2, curve_b1_b2.poes, decimal=3)
        numpy.testing.assert_array_almost_equal(
            expected_curve_poes_b1_b3, curve_b1_b3.poes, decimal=3)
        numpy.testing.assert_array_almost_equal(
            expected_curve_poes_b1_b4, curve_b1_b4.poes, decimal=3)

        # Test the exports as well:
        exported_file_b1_b2 = hazard_export.export(
            curve_b1_b2.hazard_curve.output.id, result_dir)
        check_equal(case_8.__file__, 'expected_b1_b2.xml', exported_file_b1_b2)

        exported_file_b1_b3 = hazard_export.export(
            curve_b1_b3.hazard_curve.output.id, result_dir)
        check_equal(case_8.__file__, 'expected_b1_b3.xml', exported_file_b1_b3)

        exported_file_b1_b4 = hazard_export.export(
            curve_b1_b4.hazard_curve.output.id, result_dir)
        check_equal(case_8.__file__, 'expected_b1_b4.xml', exported_file_b1_b4)

        shutil.rmtree(result_dir)


class ClassicalHazardCase9TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_9.__file__), 'job.ini')
        expected_curve_poes_b1_b2 = [0.00995, 0.00076, 9.7E-5, 0.0]
        expected_curve_poes_b1_b3 = [0.00995, 0.00076, 0.000104, 0.0]

        job = self.run_hazard(cfg)

        # Test the poe values for the two curves:
        curve_b1_b2, curve_b1_b3 = models.HazardCurveData.objects \
            .filter(hazard_curve__output__oq_job=job.id) \
            .order_by('hazard_curve__lt_realization__lt_model__sm_lt_path')

        # Sanity check, to make sure we have the curves ordered correctly:
        self.assertEqual(
            ['b1', 'b2'],
            curve_b1_b2.hazard_curve.lt_realization.sm_lt_path)
        self.assertEqual(
            ['b1', 'b3'],
            curve_b1_b3.hazard_curve.lt_realization.sm_lt_path)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes_b1_b2, curve_b1_b2.poes, decimal=4)
        numpy.testing.assert_array_almost_equal(
            expected_curve_poes_b1_b3, curve_b1_b3.poes, decimal=4)

        # Test the exports as well:
        exported_file_b1_b2 = hazard_export.export(
            curve_b1_b2.hazard_curve.output.id, result_dir)
        check_equal(case_9.__file__, 'expected_b1_b2.xml', exported_file_b1_b2)

        exported_file_b1_b3 = hazard_export.export(
            curve_b1_b3.hazard_curve.output.id, result_dir)
        check_equal(case_9.__file__, 'expected_b1_b3.xml', exported_file_b1_b3)
        shutil.rmtree(result_dir)


class ClassicalHazardCase10TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_10.__file__), 'job.ini')
        expected_curve_poes_b1_b2 = [0.00995, 0.00076, 9.7E-5, 0.0]
        expected_curve_poes_b1_b3 = [0.043, 0.0012, 7.394E-5, 0.0]

        job = self.run_hazard(cfg)

        # Test the poe values for the two curves:
        curve_b1_b2, curve_b1_b3 = models.HazardCurveData.objects\
            .filter(hazard_curve__output__oq_job=job.id)\
            .order_by('hazard_curve__lt_realization__lt_model__sm_lt_path')

        # Sanity check, to make sure we have the curves ordered correctly:
        self.assertEqual(
            ['b1', 'b2'],
            curve_b1_b2.hazard_curve.lt_realization.sm_lt_path)
        self.assertEqual(
            ['b1', 'b3'],
            curve_b1_b3.hazard_curve.lt_realization.sm_lt_path)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes_b1_b2, curve_b1_b2.poes, decimal=4)
        numpy.testing.assert_array_almost_equal(
            expected_curve_poes_b1_b3, curve_b1_b3.poes, decimal=4)

        # Test the exports as well:
        exported_file_b1_b2 = hazard_export.export(
            curve_b1_b2.hazard_curve.output.id, result_dir)
        check_equal(case_10.__file__, 'expected_b1_b2.xml',
                    exported_file_b1_b2)

        exported_file_b1_b3 = hazard_export.export(
            curve_b1_b3.hazard_curve.output.id, result_dir)
        check_equal(case_10.__file__, 'expected_b1_b3.xml',
                    exported_file_b1_b3)

        shutil.rmtree(result_dir)


class ClassicalHazardCase11TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        current = case_11.__file__
        result_dir = tempfile.mkdtemp()
        aaae = numpy.testing.assert_array_almost_equal

        cfg = os.path.join(os.path.dirname(current), 'job.ini')
        expected_curve_poes_b1_b2 = [0.0055, 0.00042, 5.77E-5, 0.0]
        expected_curve_poes_b1_b3 = [0.00995, 0.00076, 9.7E-5, 0.0]
        expected_curve_poes_b1_b4 = [0.018, 0.0013, 0.00014, 0.0]

        expected_mean_poes = [0.01067, 0.0008, 9.774E-5, 0.0]

        expected_q0_1_poes = [0.0055, 0.00042, 5.77E-5, 0.0]
        expected_q0_9_poes = [0.013975, 0.00103, 0.0001185, 0.0]

        job = self.run_hazard(cfg)

        # Test the poe values for the two curves:
        curve_b1_b2, curve_b1_b3, curve_b1_b4 = (
            models.HazardCurveData.objects
            .filter(hazard_curve__output__oq_job=job.id,
                    hazard_curve__lt_realization__isnull=False)
            .order_by(
                'hazard_curve__lt_realization__lt_model__sm_lt_path'))

        # Sanity check, to make sure we have the curves ordered correctly:
        self.assertEqual(
            ['b1', 'b2'],
            curve_b1_b2.hazard_curve.lt_realization.sm_lt_path)
        self.assertEqual(
            ['b1', 'b3'],
            curve_b1_b3.hazard_curve.lt_realization.sm_lt_path)
        self.assertEqual(
            ['b1', 'b4'],
            curve_b1_b4.hazard_curve.lt_realization.sm_lt_path)

        aaae(expected_curve_poes_b1_b2, curve_b1_b2.poes, decimal=4)
        aaae(expected_curve_poes_b1_b3, curve_b1_b3.poes, decimal=4)
        aaae(expected_curve_poes_b1_b4, curve_b1_b4.poes, decimal=4)

        # Test the mean curve:
        [mean_curve] = models.HazardCurveData.objects\
            .filter(hazard_curve__output__oq_job=job.id,
                    hazard_curve__statistics='mean')
        aaae(expected_mean_poes, mean_curve.poes, decimal=4)

        # Test the quantile curves:
        quantile_0_1_curve, quantile_0_9_curve = \
            models.HazardCurveData.objects.filter(
                hazard_curve__output__oq_job=job.id,
                hazard_curve__statistics='quantile'
            ).order_by('hazard_curve__quantile')
        aaae(expected_q0_1_poes, quantile_0_1_curve.poes, decimal=4)
        aaae(expected_q0_9_poes, quantile_0_9_curve.poes, decimal=4)

        # Test the exports as well:
        exported_file_b1_b2 = hazard_export.export(
            curve_b1_b2.hazard_curve.output.id, result_dir)
        check_equal(current, 'expected_b1_b2.xml', exported_file_b1_b2)

        exported_file_b1_b3 = hazard_export.export(
            curve_b1_b3.hazard_curve.output.id, result_dir)
        check_equal(current, 'expected_b1_b3.xml', exported_file_b1_b3)

        exported_file_b1_b4 = hazard_export.export(
            curve_b1_b4.hazard_curve.output.id, result_dir)
        check_equal(current, 'expected_b1_b4.xml', exported_file_b1_b4)

        exported_file_mean = hazard_export.export(
            mean_curve.hazard_curve.output.id, result_dir)
        check_equal(current, 'expected_mean.xml', exported_file_mean)

        q01_file = hazard_export.export(
            quantile_0_1_curve.hazard_curve.output.id, result_dir)
        check_equal(current, 'expected_quantile_0_1.xml', q01_file)

        q09_file = hazard_export.export(
            quantile_0_9_curve.hazard_curve.output.id, result_dir)
        check_equal(current, 'expected_quantile_0_9.xml', q09_file)

        shutil.rmtree(result_dir)


class ClassicalHazardCase12TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()
        aaae = numpy.testing.assert_array_almost_equal

        cfg = os.path.join(os.path.dirname(case_12.__file__), 'job.ini')
        expected_curve_poes = [0.75421006, 0.08098179, 0.00686616]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        [curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id)

        aaae(expected_curve_poes, curve.poes, decimal=2)

        # Test the exports as well:
        exported_file = hazard_export.export(
            curve.hazard_curve.output.id, result_dir)
        check_equal(case_12.__file__, 'expected_hazard_curves.xml',
                    exported_file)

        shutil.rmtree(result_dir)


# this test is described in https://bugs.launchpad.net/oq-engine/+bug/1226061
# the CSV files with the expected hazard_curves were provided by Damiano
class ClassicalHazardCase13TestCase(BaseQATestCase):

    CURRENTDIR = os.path.dirname(case_13.__file__)

    @attr('qa', 'hazard', 'classical')
    def test(self):
        cfg = os.path.join(self.CURRENTDIR, 'job.ini')
        job = self.run_hazard(cfg)

        lt_paths = [
            ['aFault_aPriori_D2.1', 'BooreAtkinson2008'],
            ['aFault_aPriori_D2.1', 'ChiouYoungs2008'],
            ['bFault_stitched_D2.1_Char', 'BooreAtkinson2008'],
            ['bFault_stitched_D2.1_Char', 'ChiouYoungs2008']]

        csvdir = os.path.join(self.CURRENTDIR, 'expected_results')
        for sm_path, gsim_path in lt_paths:

            fname = '%s_%s_expected_curves_PGA.dat' % (sm_path, gsim_path)
            compare_hazard_curve_with_csv(
                job, [sm_path], [gsim_path], 'PGA', None, None,
                os.path.join(csvdir, fname), ' ', rtol=0.3)

            fname = '%s_%s_expected_curves_SA02.dat' % (sm_path, gsim_path)
            compare_hazard_curve_with_csv(
                job, [sm_path], [gsim_path], 'SA', 0.2, 5.0,
                os.path.join(csvdir, fname), ' ', rtol=0.3)


# this test is described in https://bugs.launchpad.net/oq-engine/+bug/1226102
# the CSV files with the expected hazard_curves were provided by Damiano
class ClassicalHazardCase14TestCase(BaseQATestCase):

    CURRENTDIR = os.path.dirname(case_14.__file__)

    @attr('qa', 'hazard', 'classical')
    def test(self):
        cfg = os.path.join(self.CURRENTDIR, 'job.ini')
        job = self.run_hazard(cfg)

        compare_hazard_curve_with_csv(
            job, ['simple_fault'], ['AbrahamsonSilva2008'],
            'PGA', None, None,
            os.path.join(self.CURRENTDIR, 'AS2008_expected_curves.dat'), ' ',
            rtol=0.01)

        compare_hazard_curve_with_csv(
            job, ['simple_fault'], ['CampbellBozorgnia2008'],
            'PGA', None, None,
            os.path.join(self.CURRENTDIR, 'CB2008_expected_curves.dat'), ' ',
            rtol=0.01)


# this test is described in https://bugs.launchpad.net/oq-engine/+bug/1226061
# the CSV files with the expected hazard_curves were provided by Damiano
class ClassicalHazardCase15TestCase(BaseQATestCase):

    CURRENTDIR = os.path.dirname(case_15.__file__)

    @attr('qa', 'hazard', 'classical')
    def test(self):
        cfg = os.path.join(self.CURRENTDIR, 'job.ini')
        job = self.run_hazard(cfg)

        lt_paths = [
            [['SM1'], ['BA2008', 'C2003']],
            [['SM1'], ['BA2008', 'T2002']],
            [['SM1'], ['CB2008', 'C2003']],
            [['SM1'], ['CB2008', 'T2002']],
            [['SM2', 'a3pt2b0pt8'], ['BA2008']],
            [['SM2', 'a3pt2b0pt8'], ['CB2008']],
            [['SM2', 'a3b1'], ['BA2008']],
            [['SM2', 'a3b1'], ['CB2008']],
        ]

        csvdir = os.path.join(self.CURRENTDIR, 'expected_results')
        j = '_'.join
        for sm_path, gsim_path in lt_paths:

            fname = 'PGA/hazard_curve-smltp_%s-gsimltp_%s.csv' % (
                j(sm_path), j(gsim_path))
            compare_hazard_curve_with_csv(
                job, sm_path, gsim_path, 'PGA', None, None,
                os.path.join(csvdir, fname), ' ', rtol=1e-7)

            fname = 'SA-0.1/hazard_curve-smltp_%s-gsimltp_%s.csv' % (
                j(sm_path), j(gsim_path))
            compare_hazard_curve_with_csv(
                job, sm_path, gsim_path, 'SA', 0.1, 5.0,
                os.path.join(csvdir, fname), ' ', rtol=1e-7)


# NB: this is a regression test to make sure that the sampling
# works well even for huge source model logic trees, since
# in the past we had issues, https://bugs.launchpad.net/oq-engine/+bug/1312020
class ClassicalHazardCase16TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        expected_mean_poes = [0.327905527354, 0.324717826053, 0.316179020913]
        expected_q0_1_poes = [0.198642855479, 0.19587955512, 0.188594171735]
        expected_q0_9_poes = [0.585553284108, 0.581083306028, 0.568977776502]

        job = self.run_hazard(
            os.path.join(os.path.dirname(case_16.__file__), 'job.ini'))

        # mean
        [mean_curve] = models.HazardCurveData.objects \
            .filter(hazard_curve__output__oq_job=job.id,
                    hazard_curve__statistics='mean')
        aaae(expected_mean_poes, mean_curve.poes, decimal=7)

        # quantiles
        quantile_0_1_curve, quantile_0_9_curve = \
            models.HazardCurveData.objects.filter(
                hazard_curve__output__oq_job=job.id,
                hazard_curve__statistics='quantile').order_by(
                'hazard_curve__quantile')
        aaae(expected_q0_1_poes, quantile_0_1_curve.poes, decimal=7)
        aaae(expected_q0_9_poes, quantile_0_9_curve.poes, decimal=7)
