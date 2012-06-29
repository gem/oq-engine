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

from openquake.db import models
from openquake.calculators.hazard.classical import core_next

from tests.utils import helpers


class ClassicalHazardCalculatorPreExecuteTestCase(unittest.TestCase):
    """
    Tests for everything which needs to run during the `pre_execute` phase.
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

        # The site model is good. Now test that `site_data` was computed.
        # For now, just test the lengths of the site data collections:
        self.assertEqual(num_pts_to_compute, len(self.calc.site_data.lons))
        self.assertEqual(num_pts_to_compute, len(self.calc.site_data.lats))
        self.assertEqual(num_pts_to_compute, len(self.calc.site_data.vs30s))
        self.assertEqual(
            num_pts_to_compute, len(self.calc.site_data.vs30_measured))
        self.assertEqual(num_pts_to_compute, len(self.calc.site_data.z1pt0s))
        self.assertEqual(num_pts_to_compute, len(self.calc.site_data.z2pt5s))

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
