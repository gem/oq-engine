# -*- coding: utf-8 -*-
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
from openquake import shapes
from openquake.calculators.hazard import general
from openquake.db import models
from openquake.job.config import ValidationException

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

        ret_val = general.store_site_model(inp, site_model)

        actual_site_model = models.SiteModel.objects.filter(
            input=inp.id).order_by('id')

        for i, exp in enumerate(exp_site_model):
            act = actual_site_model[i]

            self.assertAlmostEqual(exp['lon'], act.location.x)
            self.assertAlmostEqual(exp['lat'], act.location.y)
            self.assertAlmostEqual(exp['vs30'], act.vs30)
            self.assertEqual(exp['vs30_type'], act.vs30_type)
            self.assertAlmostEqual(exp['z1pt0'], act.z1pt0)
            self.assertAlmostEqual(exp['z2pt5'], act.z2pt5)

        # last, check that the `store_site_model` function returns all of the
        # newly-inserted records
        # an `equals` check just compares the ids
        for i, val in enumerate(ret_val):
            self.assertEqual(val, actual_site_model[i])

    def test_initialize_stores_site_model(self):
        job_ctxt = helpers.prepare_job_context(
            helpers.demo_file(
                'simple_fault_demo_hazard/config_with_site_model.gem'))

        calc = general.BaseHazardCalculator(job_ctxt)

        [site_model_input] = models.inputs4job(
            job_ctxt.oq_job.id, input_type='site_model')

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


class ValidateSiteModelTestCase(unittest.TestCase):
    """Tests for
    :function:`openquake.calculators.hazard.general.validate_site_model`.
    """

    @classmethod
    def setUpClass(cls):

        # This site model has five points, arranged in an X-shaped pattern:
        #
        #   a.....b
        #   .......
        #   ...c...
        #   .......
        #   d.....e
        cls.site_model_nodes = [
            models.SiteModel(location='POINT(-10 10)'),
            models.SiteModel(location='POINT(10 10)'),
            models.SiteModel(location='POINT(0 0)'),
            models.SiteModel(location='POINT(-10 -10)'),
            models.SiteModel(location='POINT(10 -10)'),
        ]

    def test_validate_site_model(self):
        sites_of_interest = [
            # NOTE(larsbutler): Some of the coordinates which are very close to
            # 10 or -10 have been set to 9.9999999 or -9.9999999 instead.
            #
            # This only applies to __longitude__ coordinate values.
            #
            # In theory, these cases should work (especially in the case of the
            # corners), but in reality this is not true. Probably this is due
            # to the combination of shapely, polygon, upsampling, and the
            # coordinates chosen for the test case.
            # Hopefully this test will serve to clearly document some of
            # the boundary conditions, and also where we can look if unexpected
            # errors occur.

            # the edges of the polygon
            # East edge
            shapes.Site(9.9999999, 0),
            # West edge
            shapes.Site(-9.9999999, 0),
            # NOTE: The values for the north and south edges were obtained by
            # trial and error.
            # North edge
            shapes.Site(0, 10.1507381),
            # South edge
            shapes.Site(0, -10.1507381),
            # the corners
            shapes.Site(-10, 10),
            shapes.Site(10, 10),
            shapes.Site(-10, -10),
            shapes.Site(10, -10),
            # a few points somewhere in the middle, which are obviously inside
            # the target area
            shapes.Site(0.0, 0.0),
            shapes.Site(-2.5, 2.5),
            shapes.Site(2.5, 2.5),
            shapes.Site(-2.5, -2.5),
            shapes.Site(2.5, -2.5),
        ]

        # this should work without raising any errors
        general.validate_site_model(self.site_model_nodes, sites_of_interest)

    def test_validate_site_model_invalid(self):
        test_cases = [
            # outside of the edges
            # East edge
            [shapes.Site(10.0000001, 0)],
            # West edge
            [shapes.Site(-10.0000001, 0)],
            # NOTE: The values for the north south edges were obtained by
            # trial and error.
            # North edge
            [shapes.Site(0, 10.1507382)],
            # South edge
            [shapes.Site(0, -10.1507382)],
            # outside of the corners
            # first corner (a)
            [shapes.Site(-10.0000001, 10)],
            [shapes.Site(-10, 10.0000001)],
            # second corner (b)
            [shapes.Site(10.0000001, 10)],
            [shapes.Site(10, 10.0000001)],
            # third corner (d)
            [shapes.Site(-10.0000001, -10)],
            [shapes.Site(-10, -10.0000001)],
            # fourth corner (e)
            [shapes.Site(10.0000001, -10)],
            [shapes.Site(10, -10.0000001)],
        ]

        for tc in test_cases:
            self.assertRaises(ValidationException, general.validate_site_model,
                              self.site_model_nodes, tc)

    def test_initialize_calls_validate(self):
        # Test make sure the calculator `initialize` calls
        # `validate_site_model`.
        job_ctxt = helpers.prepare_job_context(
            helpers.demo_file(
                'simple_fault_demo_hazard/config_with_site_model.gem'
            )
        )

        calc = general.BaseHazardCalculator(job_ctxt)
        patch_path = 'openquake.calculators.hazard.general.validate_site_model'

        with helpers.patch(patch_path) as validate_patch:
            calc.initialize()
            # validate_site_model itself is tested in another test
            # here, we just make sure it gets called
            self.assertEqual(1, validate_patch.call_count)


class GetSiteModelTestCase(unittest.TestCase):

    def test_get_site_model(self):
        job = engine.prepare_job()
        site_model_inp = models.Input(
            owner=job.owner, digest='fake', path='fake',
            input_type='site_model', size=0
        )
        site_model_inp.save()

        # The link has not yet been made in the input2job table.
        self.assertIsNone(general.get_site_model(job.id))

        # Complete the link:
        models.Input2job(input=site_model_inp, oq_job=job).save()

        actual_site_model = general.get_site_model(job.id)
        self.assertEqual(site_model_inp, actual_site_model)

    def test_get_site_model_too_many_site_models(self):
        job = engine.prepare_job()
        site_model_inp1 = models.Input(
            owner=job.owner, digest='fake', path='fake',
            input_type='site_model', size=0
        )
        site_model_inp1.save()
        site_model_inp2 = models.Input(
            owner=job.owner, digest='fake', path='fake',
            input_type='site_model', size=0
        )
        site_model_inp2.save()

        # link both site models to the job:
        models.Input2job(input=site_model_inp1, oq_job=job).save()
        models.Input2job(input=site_model_inp2, oq_job=job).save()

        with self.assertRaises(RuntimeError) as assert_raises:
            general.get_site_model(job.id)

        self.assertEqual('Only 1 site model per job is allowed, found 2.',
                         assert_raises.exception.message)


class ClosestSiteModelTestCase(unittest.TestCase):

    def setUp(self):
        owner = engine.prepare_user('openquake')
        self.site_model_inp = models.Input(
            owner=owner, digest='fake', path='fake',
            input_type='site_model', size=0
        )
        self.site_model_inp.save()

    def test_get_closest_site_model_data_no_data(self):
        # We haven't yet linked any site model data to this input, so we
        # expect a result of `None`.
        self.assertIsNone(general.get_closest_site_model_data(
            self.site_model_inp, shapes.Site(0, 0))
        )

    def test_get_closest_site_model_data(self):
        # This test scenario is the following:
        # Site model data nodes arranged 2 degrees apart (longitudinally) along
        # the same parallel (indicated below by 'd' characters).
        #
        # The sites of interest are located at (-0.0000001, 0) and
        # (0.0000001, 0) (from left to right).
        # Sites of interest are indicated by 's' characters.
        #
        # To illustrate, a super high-tech nethack-style diagram:
        #
        # -1.........0.........1   V ← oh no, a vampire!
        #  d        s s        d

        sm1 = models.SiteModel(
            input=self.site_model_inp, vs30_type='measured', vs30=0.0000001,
            z1pt0=0.0000001, z2pt5=0.0000001, location='POINT(-1 0)'
        )
        sm1.save()
        sm2 = models.SiteModel(
            input=self.site_model_inp, vs30_type='inferred', vs30=0.0000002,
            z1pt0=0.0000002, z2pt5=0.0000002, location='POINT(1 0)'
        )
        sm2.save()

        # NOTE(larsbutler): I tried testing the site (0, 0), but the result
        # actually alternated between the the two site model nodes on each test
        # run. It's very strange indeed. It must be a PostGIS thing.
        # (Or we can blame the vampire.)
        #
        # Thus, I decided to not include this in my test case, since it caused
        # the test to intermittently fail.
        site1 = shapes.Site(-0.0000001, 0)
        site2 = shapes.Site(0.0000001, 0)

        res1 = general.get_closest_site_model_data(self.site_model_inp, site1)
        res2 = general.get_closest_site_model_data(self.site_model_inp, site2)

        self.assertEqual(sm1, res1)
        self.assertEqual(sm2, res2)


class SetJavaSiteParamsTestCase(unittest.TestCase):

    def test_set_java_site_parameters(self):
        jsite = shapes.Site(0, 0).to_java()
        sm_data = models.SiteModel(
            vs30=800.0, vs30_type='measured', z1pt0=10.0, z2pt5=15.0
        )

        general.set_java_site_parameters(jsite, sm_data)

        self.assertEqual(
            800.0, jsite.getParameter('Vs30').getValue().value
        )
        self.assertEqual(
            'measured', jsite.getParameter('Vs30 Type').getValue()
        )
        self.assertEqual(
            10.0, jsite.getParameter('Depth 1.0 km/sec').getValue().value
        )
        self.assertEqual(
            15.0, jsite.getParameter('Depth 2.5 km/sec').getValue().value
        )
