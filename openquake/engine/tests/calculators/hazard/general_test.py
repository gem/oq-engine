# -*- coding: utf-8 -*-
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


import unittest
import mock

from openquake.hazardlib import geo as hazardlib_geo
from openquake.commonlib import readini

from openquake.engine import engine
from openquake.engine.calculators.hazard import general
from openquake.engine.utils import get_calculator_class
from openquake.engine.db import models

from openquake.engine.tests.utils import helpers


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


class ParseRiskModelsTestCase(unittest.TestCase):
    def test(self):
        # check that if risk models are provided, then the ``points to
        # compute`` and the imls are got from there

        username = helpers.default_user()

        job = engine.prepare_job(username)

        cfg = helpers.get_data_path('classical_job-sd-imt.ini')
        params = readini.parse_config(open(cfg, 'r'))

        haz_calc = engine.create_calculation(models.HazardCalculation, params)
        haz_calc = models.HazardCalculation.objects.get(id=haz_calc.id)
        job.hazard_calculation = haz_calc
        job.is_running = True
        job.save()

        calc = get_calculator_class(
            'hazard',
            job.hazard_calculation.calculation_mode)(job)
        calc.parse_risk_models()

        self.assertEqual([(1.0, -1.0), (0.0, 0.0)],
                         [(point.latitude, point.longitude)
                          for point in haz_calc.points_to_compute()])
        self.assertEqual(['PGA'], haz_calc.get_imts())

        self.assertEqual(
            3, haz_calc.oqjob.exposuremodel.exposuredata_set.count())

        return job


class InitializeSourcesTestCase(unittest.TestCase):
    # this is a based on a demo with 3 realizations, 2 sources and 2 sites
    @classmethod
    def setUpClass(cls):
        cfg = helpers.get_data_path(
            'calculators/hazard/classical/haz_map_test_job.ini')
        job = helpers.get_job(cfg)
        models.JobStats.objects.create(oq_job=job)
        hc = job.hazard_calculation
        cls.calc = get_calculator_class('hazard', hc.calculation_mode)(job)
        cls.calc.initialize_site_model()
        assert len(hc.site_collection) == 2, len(hc.site_collection)

    def test_filtering_sources(self):
        self.calc.initialize_sources()
        m1, m2, m3 = models.LtSourceModel.objects.filter(
            hazard_calculation=self.calc.hc)
        self.assertEqual(
            [m1.get_num_sources(), m2.get_num_sources(), m3.get_num_sources()],
            [2, 2, 2])
        self.calc.process_sources()
        self.assertEqual(
            [m1.get_num_sources(), m2.get_num_sources(), m3.get_num_sources()],
            [1, 1, 1])


class NonEmptyQuantileTestCase(unittest.TestCase):
    # you cannot compute the quantiles if there is only 1 realization
    def test(self):
        cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        with mock.patch('openquake.engine.logs.LOG.warn') as warn:
            helpers.run_job(cfg, number_of_logic_tree_samples=1,
                            quantile_hazard_curves='0.1 0.2',
                            hazard_maps=None, uniform_hazard_spectra=None)
        msg = warn.call_args[0][0]
        self.assertEqual(
            msg, 'There is only one realization, the configuration'
            ' parameter quantile_hazard_curves should not be set')
