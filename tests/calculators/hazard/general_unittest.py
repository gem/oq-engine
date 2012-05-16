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

from openquake import engine
from openquake.calculators.hazard import general
from openquake.db import models

from tests.utils import helpers


class StoreSiteModelTestCase(unittest.TestCase):

    def test_store_site_model(self):
        # Setup
        inp = models.Input(
            owner=models.OqUser.objects.get(id=1), path='fake_path',
            digest='fake_digest', input_type='site_model', size=0)
        inp.save()
        site_model = helpers.get_data_path('site_model.xml')

        exp_site_model = [
            dict(lon=-122.5, lat=37.5, vs30=800.0, vs30_type="measured",
                 z1pt0=100.0, z2pt5=5.0),
            dict(lon=-122.6, lat=37.6, vs30=801.0, vs30_type="measured",
                 z1pt0=101.0, z2pt5=5.1),
            dict(lon=-122.7, lat=37.7, vs30=802.0, vs30_type="measured",
                 z1pt0=102.0, z2pt5=5.2),
            dict(lon=-122.8, lat=37.8, vs30=803.0, vs30_type="measured",
                 z1pt0=103.0, z2pt5=5.3),
            dict(lon=-122.9, lat=37.9, vs30=804.0, vs30_type="measured",
                 z1pt0=104.0, z2pt5=5.4),
        ]

        # Function under test
        general.store_site_model(inp, site_model)

        # Expected results
        actual_site_model = models.SiteModel.objects.filter(
            input=inp.id).order_by('id')

        # The actual test
        for i, exp in enumerate(exp_site_model):
            act = actual_site_model[i]

            self.assertAlmostEqual(exp['lon'], act.location.x)
            self.assertAlmostEqual(exp['lat'], act.location.y)
            self.assertAlmostEqual(exp['vs30'], act.vs30)
            self.assertEqual(exp['vs30_type'], act.vs30_type)
            self.assertAlmostEqual(exp['z1pt0'], act.z1pt0)
            self.assertAlmostEqual(exp['z2pt5'], act.z2pt5)

    def test_initialize_stores_site_model(self):
        job = engine.prepare_job()
        cfg = helpers.demo_file(
            'simple_fault_demo_hazard/config_with_site_model.gem')
        job_profile, params, sections = engine.import_job_profile(
            cfg, job, force_inputs=True)

        job_ctxt = engine.JobContext(
            params, job.id, sections=sections, oq_job_profile=job_profile,
            oq_job=job)

        calc = general.BaseHazardCalculator(job_ctxt)
        [site_model_input] = models.inputs4job(job.id, input_type='site_model')
        site_model_nodes = models.SiteModel.objects.filter(
            input=site_model_input)

        # Test precondition: The site_model table shouldn't be populated yet.
        self.assertEqual(0, len(site_model_nodes))

        calc.initialize()

        # Now it should be populated.
        site_model_nodes = models.SiteModel.objects.filter(
            input=site_model_input)
        # It would be overkill to test the contents; just check that the number
        # of records is correct.
        self.assertEqual(2601, len(site_model_nodes))
