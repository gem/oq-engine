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


import getpass
import unittest

import nhlib

from nhlib import geo as nhlib_geo
from nose.plugins.attrib import attr

from openquake import engine2
from openquake.calculators.hazard import general
from openquake.calculators.hazard import classical_core as cls_core
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

        # The convex hull of site model geometry
        # has zero area
        cls.site_model_degen_case = [
            models.SiteModel(location='POINT(0.0 0.0)'),
            models.SiteModel(location='POINT(0.0 0.1)'),
            models.SiteModel(location='POINT(0.0 0.2)')]

    def test_validate_site_model(self):
        sites_of_interest_case1 = [
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
            nhlib_geo.Point(9.9999999, 0),
            # West edge
            nhlib_geo.Point(-9.9999999, 0),
            # NOTE: The values for the north and south edges were obtained by
            # trial and error.
            # North edge
            nhlib_geo.Point(0, 10.1507381),
            # South edge
            nhlib_geo.Point(0, -10.1507381),
            # the corners
            nhlib_geo.Point(-10, 10),
            nhlib_geo.Point(10, 10),
            nhlib_geo.Point(-10, -10),
            nhlib_geo.Point(10, -10),
            # a few points somewhere in the middle, which are obviously inside
            # the target area
            nhlib_geo.Point(0.0, 0.0),
            nhlib_geo.Point(-2.5, 2.5),
            nhlib_geo.Point(2.5, 2.5),
            nhlib_geo.Point(-2.5, -2.5),
            nhlib_geo.Point(2.5, -2.5),
        ]

        sites_of_interest_case2 = [nhlib_geo.Point(0.0, 0.0),
                                    nhlib_geo.Point(0.0, 0.1),
                                    nhlib_geo.Point(0.0, 0.2)]

        mesh_case1 = nhlib_geo.Mesh.from_points_list(sites_of_interest_case1)
        mesh_case2 = nhlib_geo.Mesh.from_points_list(sites_of_interest_case2)

        # this should work without raising any errors
        general.validate_site_model(self.site_model_nodes, mesh_case1)
        general.validate_site_model(self.site_model_degen_case, mesh_case2)

    def test_validate_site_model_invalid(self):
        test_cases = [
            # outside of the edges
            # East edge
            [nhlib_geo.Point(10.0000001, 0)],
            # West edge
            [nhlib_geo.Point(-10.0000001, 0)],
            # NOTE: The values for the north south edges were obtained by
            # trial and error.
            # North edge
            [nhlib_geo.Point(0, 10.1507382)],
            # South edge
            [nhlib_geo.Point(0, -10.1507382)],
            # outside of the corners
            # first corner (a)
            [nhlib_geo.Point(-10.0000001, 10)],
            [nhlib_geo.Point(-10, 10.0000001)],
            # second corner (b)
            [nhlib_geo.Point(10.0000001, 10)],
            [nhlib_geo.Point(10, 10.0000001)],
            # third corner (d)
            [nhlib_geo.Point(-10.0000001, -10)],
            [nhlib_geo.Point(-10, -10.0000001)],
            # fourth corner (e)
            [nhlib_geo.Point(10.0000001, -10)],
            [nhlib_geo.Point(10, -10.0000001)],
        ]

        for tc in test_cases:
            mesh = nhlib_geo.Mesh.from_points_list(tc)
            self.assertRaises(RuntimeError, general.validate_site_model,
                              self.site_model_nodes, mesh)


class GetSiteModelTestCase(unittest.TestCase):

    @classmethod
    def _create_haz_calc(cls):
        params = {
            'base_path': 'a/fake/path',
            'calculation_mode': 'classical',
            'region': '1 1 2 2 3 3',
            'width_of_mfd_bin': '1',
            'rupture_mesh_spacing': '1',
            'area_source_discretization': '2',
            'investigation_time': 50,
            'truncation_level': 0,
            'maximum_distance': 200,
            'number_of_logic_tree_samples': 1,
            'intensity_measure_types_and_levels': dict(PGA=[1, 2, 3, 4]),
            'random_seed': 37,
        }
        owner = helpers.default_user()
        hc = engine2.create_hazard_calculation(owner, params, [])
        return hc

    def test_get_site_model(self):
        haz_calc = self._create_haz_calc()

        site_model_inp = models.Input(
            owner=haz_calc.owner, digest='fake', path='fake',
            input_type='site_model', size=0
        )
        site_model_inp.save()

        # The link has not yet been made in the input2haz_calc table.
        self.assertIsNone(general.get_site_model(haz_calc.id))

        # Complete the link:
        models.Input2hcalc(
            input=site_model_inp, hazard_calculation=haz_calc).save()

        actual_site_model = general.get_site_model(haz_calc.id)
        self.assertEqual(site_model_inp, actual_site_model)

    def test_get_site_model_too_many_site_models(self):
        haz_calc = self._create_haz_calc()

        site_model_inp1 = models.Input(
            owner=haz_calc.owner, digest='fake', path='fake',
            input_type='site_model', size=0
        )
        site_model_inp1.save()
        site_model_inp2 = models.Input(
            owner=haz_calc.owner, digest='fake', path='fake',
            input_type='site_model', size=0
        )
        site_model_inp2.save()

        # link both site models to the calculation:
        models.Input2hcalc(
            input=site_model_inp1, hazard_calculation=haz_calc).save()
        models.Input2hcalc(
            input=site_model_inp2, hazard_calculation=haz_calc).save()

        with self.assertRaises(RuntimeError) as assert_raises:
            general.get_site_model(haz_calc.id)

        self.assertEqual('Only 1 site model per job is allowed, found 2.',
                         assert_raises.exception.message)


class ClosestSiteModelTestCase(unittest.TestCase):

    def setUp(self):
        owner = engine2.prepare_user('openquake')
        self.site_model_inp = models.Input(
            owner=owner, digest='fake', path='fake',
            input_type='site_model', size=0
        )
        self.site_model_inp.save()

    def test_get_closest_site_model_data_no_data(self):
        # We haven't yet linked any site model data to this input, so we
        # expect a result of `None`.
        self.assertIsNone(general.get_closest_site_model_data(
            self.site_model_inp, nhlib_geo.Point(0, 0))
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
        point1 = nhlib_geo.Point(-0.0000001, 0)
        point2 = nhlib_geo.Point(0.0000001, 0)

        res1 = general.get_closest_site_model_data(self.site_model_inp, point1)
        res2 = general.get_closest_site_model_data(self.site_model_inp, point2)

        self.assertEqual(sm1, res1)
        self.assertEqual(sm2, res2)


class GetSiteCollectionTestCase(unittest.TestCase):

    @attr('slow')
    def test_get_site_collection_with_site_model(self):
        cfg = helpers.demo_file(
            'simple_fault_demo_hazard/job_with_site_model.ini')
        job = helpers.get_hazard_job(cfg)
        calc = cls_core.ClassicalHazardCalculator(job)

        # Bootstrap the `site_data` table:
        calc.initialize_sources()
        calc.initialize_site_model()

        site_coll = general.get_site_collection(job.hazard_calculation)
        # Since we're using a pretty big site model, it's a bit excessive to
        # check each and every value.
        # Instead, we'll just test that the lenth of each site collection attr
        # is equal to the number of points of interest in the calculation.
        expected_len = len(job.hazard_calculation.points_to_compute())

        self.assertEqual(expected_len, len(site_coll))
        self.assertEqual(expected_len, len(site_coll.vs30))
        self.assertEqual(expected_len, len(site_coll.vs30measured))
        self.assertEqual(expected_len, len(site_coll.z1pt0))
        self.assertEqual(expected_len, len(site_coll.z2pt5))

    def test_get_site_collection_with_reference_parameters(self):
        cfg = helpers.demo_file(
            'simple_fault_demo_hazard/job.ini')
        job = helpers.get_hazard_job(cfg, username=getpass.getuser())

        site_coll = general.get_site_collection(job.hazard_calculation)

        # all of the parameters should be the same:
        self.assertTrue((site_coll.vs30 == 760).all())
        self.assertTrue((site_coll.vs30measured).all())
        self.assertTrue((site_coll.z1pt0 == 5).all())
        self.assertTrue((site_coll.z2pt5 == 100).all())

        # just for sanity, make sure the meshes are correct (the locations)
        job_mesh = job.hazard_calculation.points_to_compute()
        self.assertTrue((job_mesh.lons == site_coll.mesh.lons).all())
        self.assertTrue((job_mesh.lats == site_coll.mesh.lats).all())


class ImtsToNhlibTestCase(unittest.TestCase):
    """
    Tests for
    :func:`openquake.calculators.hazard.general.im_dict_to_nhlib`.
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
            nhlib.imt.SA(0.1, models.DEFAULT_SA_DAMPING): [0.1, 0.2],
            nhlib.imt.SA(0.025, models.DEFAULT_SA_DAMPING): [0.2, 0.3],
            nhlib.imt.IA(): [0.3, 0.4],
            nhlib.imt.RSD(): [0.4, 0.5],
            nhlib.imt.MMI(): [0.5, 0.6],
        }

        actual = general.im_dict_to_nhlib(imts_in)
        self.assertEqual(len(expected), len(actual))

        for exp_imt, exp_imls in expected.items():
            act_imls = actual[exp_imt]
            self.assertEqual(exp_imls, act_imls)


class Bug1098154TestCase(unittest.TestCase):
    """
    A test to directly address
    https://bugs.launchpad.net/openquake/+bug/1098154. See the bug description
    for more info.
    """

    @attr('slow')
    def test(self):
        cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')

        retcode = helpers.run_hazard_job_sp(
            cfg, silence=True, force_inputs=False
        )
        self.assertEqual(0, retcode)
        job = models.OqJob.objects.latest('id')
        job_stats = models.JobStats.objects.get(oq_job=job)
        self.assertEqual(236, job_stats.num_tasks)

        # As the bug description explains, run the same job a second time and
        # check the task count. It should not grow.
        retcode = helpers.run_hazard_job_sp(
            cfg, silence=True, force_inputs=False
        )
        self.assertEqual(0, retcode)
        job = models.OqJob.objects.latest('id')
        job_stats = models.JobStats.objects.get(oq_job=job)
        self.assertEqual(236, job_stats.num_tasks)
