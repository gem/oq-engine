# -*- encoding: utf-8 -*-
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

import getpass
import unittest
import mock

import numpy

from nose.plugins.attrib import attr

from django.contrib.gis.db import models as djm

from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface

from openquake.engine.calculators.hazard.classical import core as cls_core
from openquake.engine.calculators.hazard.scenario import core as scen_core
from openquake.engine.db import models

from openquake.engine.tests.utils import helpers


class HazardCalculationGeometryTestCase(unittest.TestCase):
    """Test special geometry handling in the HazardCalculation constructor."""

    def test_points_to_compute_none(self):
        hc = models.HazardCalculation.create()
        self.assertIsNone(hc.points_to_compute())

        hc = models.HazardCalculation.create(region=[(1, 2), (3, 4), (5, 6)])
        # There's no region grid spacing
        self.assertIsNone(hc.points_to_compute())

    def test_points_to_compute_region(self):
        lons = [
            6.761295081695822, 7.022590163391642,
            7.28388524508746, 7.54518032678328,
            7.806475408479099, 8.067770490174919,
            8.329065571870737, 6.760434846130313,
            7.020869692260623, 7.281304538390934,
            7.541739384521245, 7.802174230651555,
            8.062609076781865, 8.323043922912175,
            6.759582805761787, 7.019165611523571,
            7.278748417285356, 7.53833122304714,
            7.797914028808925, 8.057496834570708,
            8.317079640332492, 6.758738863707749,
            7.017477727415495, 7.276216591123242,
            7.534955454830988, 7.793694318538734,
            8.05243318224648, 8.311172045954226,
        ]

        lats = [
            46.5, 46.5,
            46.5, 46.5,
            46.5, 46.5,
            46.5, 46.320135678816236,
            46.320135678816236, 46.320135678816236,
            46.320135678816236, 46.320135678816236,
            46.320135678816236, 46.320135678816236,
            46.140271357632486, 46.140271357632486,
            46.140271357632486, 46.140271357632486,
            46.140271357632486, 46.140271357632486,
            46.140271357632486, 45.96040703644873,
            45.96040703644873, 45.96040703644873,
            45.96040703644873, 45.96040703644873,
            45.96040703644873, 45.96040703644873,
        ]

        hc = models.HazardCalculation.create(
            region=[(6.5, 45.8), (6.5, 46.5), (8.5, 46.5), (8.5, 45.8)],
            region_grid_spacing=20)
        mesh = hc.points_to_compute(save_sites=False)

        numpy.testing.assert_array_almost_equal(lons, mesh.lons)
        numpy.testing.assert_array_almost_equal(lats, mesh.lats)

    def test_points_to_compute_sites(self):
        lons = [6.5, 6.5, 8.5, 8.5]
        lats = [45.8, 46.5, 46.5, 45.8]
        hc = models.HazardCalculation.create(
            sites=[(6.5, 45.8), (6.5, 46.5), (8.5, 46.5), (8.5, 45.8)])

        mesh = hc.points_to_compute(save_sites=False)

        numpy.testing.assert_array_equal(lons, mesh.lons)
        numpy.testing.assert_array_equal(lats, mesh.lats)


class ProbabilisticRuptureTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        job = helpers.get_job(cfg)

        lt_model = models.LtSourceModel.objects.create(
            hazard_calculation=job.hazard_calculation, ordinal=0,
            sm_lt_path='foo')
        lt_rlz = models.LtRealization.objects.create(
            lt_model=lt_model, ordinal=0, gsim_lt_path='bar', weight=1)
        output = models.Output.objects.create(
            oq_job=job, display_name='test', output_type='ses')
        ses_coll = models.SESCollection.objects.create(
            output=output, lt_model=lt_rlz.lt_model, ordinal=0)

        self.mesh_lons = numpy.array(
            [0.1 * x for x in range(16)]).reshape((4, 4))
        self.mesh_lats = numpy.array(
            [0.2 * x for x in range(16)]).reshape((4, 4))
        self.mesh_depths = numpy.array(
            [0.3 * x for x in range(16)]).reshape((4, 4))

        sfs = SimpleFaultSurface(
            Mesh(self.mesh_lons, self.mesh_lats, self.mesh_depths))

        ps = PlanarSurface(
            10, 20, 30,
            Point(3.9, 2.2, 10), Point(4.90402718, 3.19634248, 10),
            Point(5.9, 2.2, 90), Point(4.89746275, 1.20365263, 90))

        trt = 'Active Shallow Crust'
        trt_model = models.TrtModel.objects.create(
            lt_model=lt_model,
            tectonic_region_type=trt,
            num_sources=0,
            num_ruptures=1,
            min_mag=5,
            max_mag=5,
            gsims=['testGSIM'])
        self.fault_rupture = models.ProbabilisticRupture.objects.create(
            ses_collection=ses_coll, magnitude=5, rake=0, surface=sfs,
            trt_model=trt_model, is_from_fault_source=True,
            is_multi_surface=False)
        self.source_rupture = models.ProbabilisticRupture.objects.create(
            ses_collection=ses_coll, magnitude=5, rake=0, surface=ps,
            trt_model=trt_model, is_from_fault_source=False,
            is_multi_surface=False)

    def test_fault_rupture(self):
        # Test loading a fault rupture from the DB, just to illustrate a use
        # case.
        # Also, we should that planar surface corner points are not valid and
        # are more or less disregarded for this type of rupture.
        fault_rupture = models.ProbabilisticRupture.objects.get(
            id=self.fault_rupture.id)
        self.assertIs(None, fault_rupture.top_left_corner)
        self.assertIs(None, fault_rupture.top_right_corner)
        self.assertIs(None, fault_rupture.bottom_right_corner)
        self.assertIs(None, fault_rupture.bottom_left_corner)

    def test_source_rupture(self):
        source_rupture = models.ProbabilisticRupture.objects.get(
            id=self.source_rupture.id)
        self.assertEqual((3.9, 2.2, 10.), source_rupture.top_left_corner)
        self.assertEqual((4.90402718, 3.19634248, 10.0),
                         source_rupture.top_right_corner)
        self.assertEqual((4.89746275, 1.20365263, 90.0),
                         source_rupture.bottom_left_corner)
        self.assertEqual((5.9, 2.2, 90.0), source_rupture.bottom_right_corner)


class FloatFieldTestCase(unittest.TestCase):
    def test_truncate_small_numbers(self):
        # workaround a postgres error "out of range for type double precision"
        self.assertEqual(djm.FloatField().get_prep_value(1e-301), 0)


class GetSiteCollectionTestCase(unittest.TestCase):

    @attr('slow')
    def test_get_site_collection_with_site_model(self):
        cfg = helpers.get_data_path(
            'simple_fault_demo_hazard/job_with_site_model.ini')
        job = helpers.get_job(cfg)
        models.JobStats.objects.create(oq_job=job)
        calc = cls_core.ClassicalHazardCalculator(job)

        # Bootstrap the `hazard_site` table:
        calc.initialize_site_model()
        calc.initialize_sources()

        site_coll = job.hazard_calculation.site_collection
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

    def test_site_collection_and_ses_collection(self):
        cfg = helpers.get_data_path('scenario_hazard/job.ini')
        job = helpers.get_job(cfg, username=getpass.getuser())
        models.JobStats.objects.create(oq_job=job)

        calc = scen_core.ScenarioHazardCalculator(job)
        calc.initialize_site_model()
        site_coll = job.hazard_calculation.site_collection

        # all of the parameters should be the same:
        self.assertTrue((site_coll.vs30 == 760).all())
        self.assertTrue((site_coll.vs30measured).all())
        self.assertTrue((site_coll.z1pt0 == 100).all())
        self.assertTrue((site_coll.z2pt5 == 5).all())

        # just for sanity, make sure the meshes are correct (the locations)
        job_mesh = job.hazard_calculation.points_to_compute()
        self.assertTrue((job_mesh.lons == site_coll.mesh.lons).all())
        self.assertTrue((job_mesh.lats == site_coll.mesh.lats).all())

        # test SESCollection
        calc.initialize_sources()
        calc.create_ruptures()
        ses_coll = models.SESCollection.objects.get(
            output__oq_job=job, output__output_type='ses')
        expected_tags = [
            'scenario-0000000000',
            'scenario-0000000001',
            'scenario-0000000002',
            'scenario-0000000003',
            'scenario-0000000004',
            'scenario-0000000005',
            'scenario-0000000006',
            'scenario-0000000007',
            'scenario-0000000008',
            'scenario-0000000009',
        ]
        expected_seeds = [
            511025145, 1168723362, 794472670, 1296908407, 1343724121,
            140722153, 28278046, 1798451159, 556958504, 503221907]
        for ses in ses_coll:  # there is a single ses
            self.assertEqual(ses.ordinal, 1)
            for ses_rup, tag, seed in zip(ses, expected_tags, expected_seeds):
                self.assertEqual(ses_rup.ses_id, 1)
                self.assertEqual(ses_rup.tag, tag)
                self.assertEqual(ses_rup.seed, seed)


class LossFractionTestCase(unittest.TestCase):
    def test_display_taxonomy_value(self):
        lf = models.LossFraction(variable="taxonomy")
        rc = mock.Mock()

        self.assertEqual("RC", lf.display_value("RC", rc))

    def test_display_magnitude_distance_value(self):
        rc = mock.Mock()
        rc.mag_bin_width = 2
        rc.distance_bin_width = 10

        lf = models.LossFraction(variable="magnitude_distance")

        self.assertEqual("12.0000,14.0000|300.0000,310.0000",
                         lf.display_value("6, 30", rc))
        self.assertEqual("14.0000,16.0000|210.0000,220.0000",
                         lf.display_value("7, 21", rc))
        self.assertEqual("0.0000,2.0000|0.0000,10.0000",
                         lf.display_value("0, 0", rc))

    def test_display_coordinate_value(self):
        rc = mock.Mock()
        rc.coordinate_bin_width = 0.5

        lf = models.LossFraction(variable="coordinate")

        self.assertEqual("3.0000,3.5000|15.0000,15.5000",
                         lf.display_value("6, 30", rc))
        self.assertEqual("3.5000,4.0000|10.5000,11.0000",
                         lf.display_value("7, 21", rc))
        self.assertEqual("0.0000,0.5000|0.0000,0.5000",
                         lf.display_value("0.0, 0.0", rc))
