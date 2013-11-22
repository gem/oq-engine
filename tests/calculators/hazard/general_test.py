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
import mock
import openquake.hazardlib

from collections import namedtuple

from openquake.hazardlib import geo as hazardlib_geo

from openquake.engine import engine
from openquake.engine.calculators.hazard import general
from openquake.engine.utils import get_calculator_class
from openquake.engine.db import models

from tests.utils import helpers


class StoreSiteModelTestCase(unittest.TestCase):

    def test_store_site_model(self):
        # Setup
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

        job = models.OqJob.objects.create(user_name="openquake")
        ids = general.store_site_model(job, site_model)

        actual_site_model = models.SiteModel.objects.filter(
            job=job).order_by('id')

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
        for i, s in enumerate(ids):
            self.assertEqual(s, actual_site_model[i].id)


class ValidateSiteModelTestCase(unittest.TestCase):
    """Tests for
    :function:`openquake.engine.calculators.hazard.general.\
validate_site_model`.
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
            hazardlib_geo.Point(9.9999999, 0),
            # West edge
            hazardlib_geo.Point(-9.9999999, 0),
            # NOTE: The values for the north and south edges were obtained by
            # trial and error.
            # North edge
            hazardlib_geo.Point(0, 10.1507381),
            # South edge
            hazardlib_geo.Point(0, -10.1507381),
            # the corners
            hazardlib_geo.Point(-10, 10),
            hazardlib_geo.Point(10, 10),
            hazardlib_geo.Point(-10, -10),
            hazardlib_geo.Point(10, -10),
            # a few points somewhere in the middle, which are obviously inside
            # the target area
            hazardlib_geo.Point(0.0, 0.0),
            hazardlib_geo.Point(-2.5, 2.5),
            hazardlib_geo.Point(2.5, 2.5),
            hazardlib_geo.Point(-2.5, -2.5),
            hazardlib_geo.Point(2.5, -2.5),
        ]

        sites_of_interest_case2 = [hazardlib_geo.Point(0.0, 0.0),
                                   hazardlib_geo.Point(0.0, 0.1),
                                   hazardlib_geo.Point(0.0, 0.2)]

        mesh_case1 = hazardlib_geo.Mesh.from_points_list(
            sites_of_interest_case1)
        mesh_case2 = hazardlib_geo.Mesh.from_points_list(
            sites_of_interest_case2)

        # this should work without raising any errors
        general.validate_site_model(self.site_model_nodes, mesh_case1)
        general.validate_site_model(self.site_model_degen_case, mesh_case2)

    def test_validate_site_model_invalid(self):
        test_cases = [
            # outside of the edges
            # East edge
            [hazardlib_geo.Point(10.0000001, 0)],
            # West edge
            [hazardlib_geo.Point(-10.0000001, 0)],
            # NOTE: The values for the north south edges were obtained by
            # trial and error.
            # North edge
            [hazardlib_geo.Point(0, 10.1507382)],
            # South edge
            [hazardlib_geo.Point(0, -10.1507382)],
            # outside of the corners
            # first corner (a)
            [hazardlib_geo.Point(-10.0000001, 10)],
            [hazardlib_geo.Point(-10, 10.0000001)],
            # second corner (b)
            [hazardlib_geo.Point(10.0000001, 10)],
            [hazardlib_geo.Point(10, 10.0000001)],
            # third corner (d)
            [hazardlib_geo.Point(-10.0000001, -10)],
            [hazardlib_geo.Point(-10, -10.0000001)],
            # fourth corner (e)
            [hazardlib_geo.Point(10.0000001, -10)],
            [hazardlib_geo.Point(10, -10.0000001)],
        ]

        for tc in test_cases:
            mesh = hazardlib_geo.Mesh.from_points_list(tc)
            self.assertRaises(RuntimeError, general.validate_site_model,
                              self.site_model_nodes, mesh)


class ClosestSiteModelTestCase(unittest.TestCase):

    def setUp(self):
        self.hc = models.HazardCalculation.objects.create(
            maximum_distance=200,
            calculation_mode="classical",
            inputs={'site_model': ['fake']})
        self.job = models.OqJob.objects.create(
            user_name="openquake", hazard_calculation=self.hc)

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
            job=self.job, vs30_type='measured', vs30=0.0000001,
            z1pt0=0.0000001, z2pt5=0.0000001, location='POINT(-1 0)'
        )
        sm1.save()
        sm2 = models.SiteModel(
            job=self.job, vs30_type='inferred', vs30=0.0000002,
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
        point1 = hazardlib_geo.Point(-0.0000001, 0)
        point2 = hazardlib_geo.Point(0.0000001, 0)

        res1 = self.hc.get_closest_site_model_data(point1)
        res2 = self.hc.get_closest_site_model_data(point2)

        self.assertEqual(sm1, res1)
        self.assertEqual(sm2, res2)


class ImtsToHazardlibTestCase(unittest.TestCase):
    """
    Tests for
    :func:`openquake.engine.calculators.hazard.general.im_dict_to_hazardlib`.
    """

    def test_im_dict_to_hazardlib(self):
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
            openquake.hazardlib.imt.PGA(): [1, 2],
            openquake.hazardlib.imt.PGV(): [2, 3],
            openquake.hazardlib.imt.PGD(): [3, 4],
            openquake.hazardlib.imt.SA(0.1, models.DEFAULT_SA_DAMPING): [
                0.1, 0.2],
            openquake.hazardlib.imt.SA(0.025, models.DEFAULT_SA_DAMPING): [
                0.2, 0.3],
            openquake.hazardlib.imt.IA(): [0.3, 0.4],
            openquake.hazardlib.imt.RSD(): [0.4, 0.5],
            openquake.hazardlib.imt.MMI(): [0.5, 0.6],
        }

        actual = general.im_dict_to_hazardlib(imts_in)
        self.assertEqual(len(expected), len(actual))

        for exp_imt, exp_imls in expected.items():
            act_imls = actual[exp_imt]
            self.assertEqual(exp_imls, act_imls)


class ParseRiskModelsTestCase(unittest.TestCase):
    def test(self):
        # check that if risk models are provided, then the ``points to
        # compute`` and the imls are got from there

        username = helpers.default_user()

        job = engine.prepare_job(username)

        cfg = helpers.get_data_path('classical_job-sd-imt.ini')
        params = engine.parse_config(open(cfg, 'r'))

        haz_calc = engine.create_calculation(models.HazardCalculation, params)
        haz_calc = models.HazardCalculation.objects.get(id=haz_calc.id)
        job.hazard_calculation = haz_calc
        job.is_running = True
        job.save()

        base_path = ('openquake.engine.calculators.hazard.classical.core'
                     '.ClassicalHazardCalculator')
        init_src_patch = helpers.patch(
            '%s.%s' % (base_path, 'initialize_sources'))
        init_sm_patch = helpers.patch(
            '%s.%s' % (base_path, 'initialize_site_model'))
        init_rlz_patch = helpers.patch(
            '%s.%s' % (base_path, 'initialize_realizations'))
        patches = (init_src_patch, init_sm_patch, init_rlz_patch)

        mocks = [p.start() for p in patches]

        get_calculator_class(
            'hazard',
            job.hazard_calculation.calculation_mode)(job).pre_execute()

        self.assertEqual([(1.0, -1.0), (0.0, 0.0)],
                         [(point.latitude, point.longitude)
                          for point in haz_calc.points_to_compute()])
        self.assertEqual(['PGA'], haz_calc.get_imts())

        self.assertEqual(
            3, haz_calc.oqjob.exposuremodel.exposuredata_set.count())

        for i, m in enumerate(mocks):
            m.stop()
            patches[i].stop()

        return job


class TaskArgGenTestCase(unittest.TestCase):
    """
    Tests for the default implementation of the hazard calc task arg generator.

    The default implementation splits the calculation into blocks of sources.
    """

    Job = namedtuple('Job', 'id hazard_calculation')
    Rlz = namedtuple('Realization', 'id')

    def test_task_arg_gen(self):
        # Test the logic of `BaseHazardCalculator.task_arg_gen`.
        job = self.Job(1776, mock.Mock())

        base_path = (
            'openquake.engine.calculators.hazard.general.BaseHazardCalculator'
        )
        calc = general.BaseHazardCalculator(job)

        # Set up mocks:
        # ltp
        ltp_patch = mock.patch(
            'openquake.engine.input.logictree.LogicTreeProcessor.from_hc')
        ltp_mock = ltp_patch.start()
        ltp_mock.return_value = mock.Mock()

        # point_source_block_size
        pt_src_block_size_patch = helpers.patch(
            '%s.%s' % (base_path, 'point_source_block_size')
        )
        pt_src_block_size_mock = pt_src_block_size_patch.start()
        pt_src_block_size_mock.return_value = 5

        # _get_realizations
        get_rlz_patch = helpers.patch(
            '%s.%s' % (base_path, '_get_realizations')
        )
        get_rlz_mock = get_rlz_patch.start()
        get_rlz_mock.return_value = [self.Rlz(5), self.Rlz(6)]

        # _get_point_source_ids

        for rlz in 5, 6:
            calc.sources_per_rlz[rlz, 'point'] = [
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            calc.sources_per_rlz[rlz, 'other'] = [100, 101, 102, 103, 104]

        expected = [
            (1776, [1, 2, 3, 4, 5], 5),
            (1776, [6, 7, 8, 9, 10], 5),
            (1776, [11], 5),
            (1776, [100, 101], 5),
            (1776, [102, 103], 5),
            (1776, [104], 5),
            (1776, [1, 2, 3, 4, 5], 6),
            (1776, [6, 7, 8, 9, 10], 6),
            (1776, [11], 6),
            (1776, [100, 101], 6),
            (1776, [102, 103], 6),
            (1776, [104], 6),
        ]

        expected = [exp + (ltp_mock.return_value,) for exp in expected]

        try:
            actual = list(calc.task_arg_gen(block_size=2))
            self.assertEqual(expected, actual)
            self.assertEqual(1, pt_src_block_size_mock.call_count)
            self.assertEqual(1, get_rlz_mock.call_count)
        finally:
            pt_src_block_size_mock.stop()
            pt_src_block_size_patch.stop()
            get_rlz_mock.stop()
            get_rlz_patch.stop()
            ltp_patch.stop()
