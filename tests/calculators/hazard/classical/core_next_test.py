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


import unittest

import nhlib.imt

from openquake.db import models
from openquake.calculators.hazard.classical import core_next

from tests.utils import helpers


class ClassicalHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the main methods of the classical hazard calculator.
    """

    def setUp(self):
        cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')
        self.job = helpers.get_hazard_job(cfg)
        self.calc = core_next.ClassicalHazardCalculator(self.job)

    def test_pre_execute(self):
        # Most of the pre-execute functionality is implement in other methods.
        # For this test, just make sure each method gets called.
        base_path = ('openquake.calculators.hazard.classical.core_next'
                     '.ClassicalHazardCalculator')
        init_src_patch = helpers.patch(
            '%s.%s' % (base_path, 'initialize_sources'))
        init_sm_patch = helpers.patch(
            '%s.%s' % (base_path, 'initialize_site_model'))
        init_rlz_patch = helpers.patch(
            '%s.%s' % (base_path, 'initialize_realizations'))
        patches = (init_src_patch, init_sm_patch, init_rlz_patch)

        mocks = [p.start() for p in patches]

        self.calc.pre_execute()

        for m in mocks:
            self.assertEqual(1, m.call_count)
            m.stop()

    def test_initalize_sources(self):
        self.calc.initialize_sources()

        # The source model logic tree for this configuration has only 1 source
        # model:
        [source] = models.inputs4hcalc(
            self.job.hazard_calculation.id, input_type='source')

        parsed_sources = models.ParsedSource.objects.filter(input=source)
        # This source model contains 118 sources:
        self.assertEqual(118, len(parsed_sources))

        # Finally, check the Src2ltsrc linkage:
        [smlt] = models.inputs4hcalc(
            self.job.hazard_calculation.id, input_type='lt_source')
        [src2ltsrc] = models.Src2ltsrc.objects.filter(
            hzrd_src=source, lt_src=smlt)
        # Make sure the `filename` is exactly as it apprears in the logic tree.
        # This is import for the logic tree processing we need to do later on.
        self.assertEqual('dissFaultModel.xml', src2ltsrc.filename)

    def test_initialize_site_model(self):
        # we need a slightly different config file for this test
        cfg = helpers.demo_file(
            'simple_fault_demo_hazard/job_with_site_model.ini')
        self.job = helpers.get_hazard_job(cfg)
        self.calc = core_next.ClassicalHazardCalculator(self.job)

        self.calc.initialize_site_model()
        # If the site model isn't valid for the calculation geometry, a
        # `RuntimeError` should be raised here

        # Okay, it's all good. Now check the count of the site model records.
        [site_model_inp] = models.inputs4hcalc(
            self.job.hazard_calculation.id, input_type='site_model')
        sm_nodes = models.SiteModel.objects.filter(input=site_model_inp)

        self.assertEqual(2601, len(sm_nodes))

        num_pts_to_compute = len(
            self.job.hazard_calculation.points_to_compute())

        [site_data] = models.SiteData.objects.filter(
            hazard_calculation=self.job.hazard_calculation.id)

        # The site model is good. Now test that `site_data` was computed.
        # For now, just test the lengths of the site data collections:
        self.assertEqual(num_pts_to_compute, len(site_data.lons))
        self.assertEqual(num_pts_to_compute, len(site_data.lats))
        self.assertEqual(num_pts_to_compute, len(site_data.vs30s))
        self.assertEqual(num_pts_to_compute, len(site_data.vs30_measured))
        self.assertEqual(num_pts_to_compute, len(site_data.z1pt0s))
        self.assertEqual(num_pts_to_compute, len(site_data.z2pt5s))

    def test_initialize_site_model_no_site_model(self):
        patch_path = 'openquake.calculators.hazard.general.store_site_model'
        with helpers.patch(patch_path) as store_sm_patch:
            self.calc.initialize_site_model()
            # We should never try to store a site model in this case.
            self.assertEqual(0, store_sm_patch.call_count)

    def test_initialize_realizations(self):
        # We need initalize sources first (read logic trees, parse sources,
        # etc.)
        self.calc.initialize_sources()

        # No realizations yet:
        ltrs = models.LtRealization.objects.filter(
            hazard_calculation=self.job.hazard_calculation.id)
        self.assertEqual(0, len(ltrs))

        self.calc.initialize_realizations()

        # We expect 2 logic tree realizations
        ltr1, ltr2 = models.LtRealization.objects.filter(
            hazard_calculation=self.job.hazard_calculation.id)

        # Check each ltr contents, just to be thorough.
        self.assertEqual(0, ltr1.ordinal)
        self.assertEqual(23, ltr1.seed)
        self.assertFalse(ltr1.is_complete)
        self.assertEqual(['b1'], ltr1.sm_lt_path)
        self.assertEqual(['b1'], ltr1.gsim_lt_path)
        self.assertEqual(118, ltr1.total_sources)
        self.assertEqual(0, ltr1.completed_sources)

        self.assertEqual(1, ltr2.ordinal)
        self.assertEqual(1685488378, ltr2.seed)
        self.assertFalse(ltr2.is_complete)
        self.assertEqual(['b1'], ltr2.sm_lt_path)
        self.assertEqual(['b1'], ltr2.gsim_lt_path)
        self.assertEqual(118, ltr2.total_sources)
        self.assertEqual(0, ltr2.completed_sources)


        for ltr in (ltr1, ltr2):
            # Now check that we have source_progress records for each
            # realization.
            # Since the logic for his sample calculation only contains a single
            # source model, both samples will have the number of
            # source_progress records (that is, 1 record per source).
            src_prog = models.SourceProgress.objects.filter(
                lt_realization=ltr.id)
            self.assertEqual(118, len(src_prog))
            self.assertFalse(any([x.is_complete for x in src_prog]))

            # Check that hazard curve progress records were properly
            # initialized:
            [hc_prog_pga] = models.HazardCurveProgress.objects.filter(
                lt_realization=ltr.id, imt="PGA")
            self.assertEqual((28, 15), hc_prog_pga.result_matrix.shape)
            self.assertTrue((hc_prog_pga.result_matrix == 0).all())

            [hc_prog_sa] = models.HazardCurveProgress.objects.filter(
                lt_realization=ltr.id, imt="SA(0.025)")
            self.assertEqual((28, 19), hc_prog_sa.result_matrix.shape)
            self.assertTrue((hc_prog_sa.result_matrix == 0).all())

    def test_execute(self):
        self.calc.pre_execute()

        # Update job status to move on to the execution phase.
        self.job.status = 'executing'
        self.job.save()
        import nose; nose.tools.set_trace()
        self.calc.execute()
        import nose; nose.tools.set_trace()


class ImtsToNhlibTestCase(unittest.TestCase):
    """
    Tests for
    :func:`openquake.calculators.hazard.classical.core_next.im_dict_to_nhlib`.
    """

    def test_im_dict_to_nhlib(self):
        imts_in = {
            'PGA': [1, 2],
            'PGV': [2, 3],
            'PGD': [3, 4],
            'SA(0.1)': [0.1, 0.2],
            'SA(0.025)': [0.2, 0.3],
            'IA': [0.3, 0.4],
            'RSD': [0.4, 0.5],
            'MMI': [0.5, 0.6],
        }

        expected = {
            nhlib.imt.PGA(): [1, 2],
            nhlib.imt.PGV(): [2, 3],
            nhlib.imt.PGD(): [3, 4],
            nhlib.imt.SA(0.1, core_next.DEFAULT_SA_DAMPING): [0.1, 0.2],
            nhlib.imt.SA(0.025, core_next.DEFAULT_SA_DAMPING): [0.2, 0.3],
            nhlib.imt.IA(): [0.3, 0.4],
            nhlib.imt.RSD(): [0.4, 0.5],
            nhlib.imt.MMI(): [0.5, 0.6],
        }

        actual = core_next.im_dict_to_nhlib(imts_in)
        self.assertEqual(len(expected), len(actual))

        for i, (exp_imt, exp_imls) in enumerate(expected.items()):
            act_imls = actual[exp_imt]
            self.assertEqual(exp_imls, act_imls)
