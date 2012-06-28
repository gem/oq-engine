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


class ClassicalHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the basic functions of the classical hazard calculator
    (pre_execute, execute, etc.).
    """

    def test_initialize_site_model(self):
        cfg = helpers.demo_file(
            'simple_fault_demo_hazard/job_with_site_model.ini')
        job = helpers.get_hazard_job(cfg)

        calc = core_next.ClassicalHazardCalculator(job)

        calc.initialize_site_model()
        # If the site model isn't valid for the calculation geometry, a
        # `RuntimeError` should be raised here

        # Okay, it's all good. Now check the count of the site model records.
        [site_model_inp] = models.inputs4hcalc(
            job.hazard_calculation.id, input_type='site_model')
        sm_nodes = models.SiteModel.objects.filter(input=site_model_inp)

        self.assertEqual(2601, len(sm_nodes))

        num_pts_to_compute = len(
            calc.job.hazard_calculation.points_to_compute())

        # The site model is good. Now test that `site_data` was computed.
        # For now, just test the lengths of the site data collections:
        self.assertEqual(num_pts_to_compute, len(calc.site_data.lons))
        self.assertEqual(num_pts_to_compute, len(calc.site_data.lats))
        self.assertEqual(num_pts_to_compute, len(calc.site_data.vs30s))
        self.assertEqual(num_pts_to_compute, len(calc.site_data.vs30_measured))
        self.assertEqual(num_pts_to_compute, len(calc.site_data.z1pt0s))
        self.assertEqual(num_pts_to_compute, len(calc.site_data.z2pt5s))

    def test_initialize_site_model_no_site_model(self):
        cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')
        job = helpers.get_hazard_job(cfg)

        calc = core_next.ClassicalHazardCalculator(job)

        patch_path = 'openquake.calculators.hazard.general.store_site_model'
        with helpers.patch(patch_path) as store_sm_patch:
            calc.initialize_site_model()
            # We should never try to store a site model in this case.
            self.assertEqual(0, store_sm_patch.call_count)

    def test_initalize_sources(self):
        cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')
        job = helpers.get_hazard_job(cfg)

        calc = core_next.ClassicalHazardCalculator(job)

        calc.initialize_sources()

        # The source model logic tree for this configuration has only 1 source
        # model:
        [source] = models.inputs4hcalc(
            job.hazard_calculation.id, input_type='source')

        parsed_sources = models.ParsedSource.objects.filter(input=source)
        # This source model contains 118 sources:
        self.assertEqual(118, len(parsed_sources))

        # Finally, check the Src2ltsrc linkage:
        [smlt] = models.inputs4hcalc(
            job.hazard_calculation.id, input_type='lt_source')
        [src2ltsrc] = models.Src2ltsrc.objects.filter(
            hzrd_src=source, lt_src=smlt)
        # Make sure the `filename` is exactly as it apprears in the logic tree.
        # This is import for the logic tree processing we need to do later on.
        self.assertEqual('dissFaultModel.xml', src2ltsrc.filename)
