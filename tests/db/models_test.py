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
import mock

import numpy

from nose.plugins.attrib import attr

from openquake.engine import engine
from openquake.engine.calculators.hazard.classical import core as cls_core
from openquake.engine.calculators.hazard.scenario import core as scen_core
from openquake.engine.db import models

from tests.utils import helpers
from tests.utils.helpers import get_data_path


class Inputs4HazCalcTestCase(unittest.TestCase):

    def test_no_inputs(self):
        self.assertEqual([], list(models.inputs4hcalc(-1)))

    def test_a_few_inputs(self):
        cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        params, files = engine.parse_config(open(cfg, 'r'))
        owner = helpers.default_user()
        hc = engine.create_hazard_calculation(
            owner.user_name, params, files
        )

        inputs = models.inputs4hcalc(hc.id)
        # We expect 3: the two logic trees and one source model
        self.assertEqual(3, inputs.count())

    def test_with_input_type(self):
        cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        params, files = engine.parse_config(open(cfg, 'r'))
        owner = helpers.default_user()
        hc = engine.create_hazard_calculation(
            owner.user_name, params, files
        )

        inputs = models.inputs4hcalc(
            hc.id, input_type='source_model_logic_tree'
        )
        self.assertEqual(1, inputs.count())


class Inputs4RiskCalcTestCase(unittest.TestCase):

    def test_no_inputs(self):
        self.assertEqual([], list(models.inputs4rcalc(-1)))

    def test_a_few_inputs(self):
        job, files = helpers.get_fake_risk_job(
            get_data_path('classical_psha_based_risk/job.ini'),
            get_data_path('simple_fault_demo_hazard/job.ini'))
        rc = job.risk_calculation


        inputs = models.inputs4rcalc(rc.id)
        self.assertEqual(2, inputs.count())

    def test_with_input_type(self):
        job, files = helpers.get_fake_risk_job(
            get_data_path('classical_psha_based_risk/job.ini'),
            get_data_path('simple_fault_demo_hazard/job.ini'))
        rc = job.risk_calculation

        inputs = models.inputs4rcalc(rc.id, input_type='exposure')
        self.assertEqual(1, inputs.count())


class HazardCalculationGeometryTestCase(unittest.TestCase):
    """Test special geometry handling in the HazardCalculation constructor."""

    def test_sites_from_wkt(self):
        # should succeed with no errors
        hjp = models.HazardCalculation(sites='MULTIPOINT(1 2, 3 4)')
        expected_wkt = (
            'MULTIPOINT (1.0000000000000000 2.0000000000000000,'
            ' 3.0000000000000000 4.0000000000000000)'
        )

        self.assertEqual(expected_wkt, hjp.sites.wkt)

    def test_sites_invalid_str(self):
        self.assertRaises(ValueError, models.HazardCalculation, sites='a 5')

    def test_sites_odd_num_of_coords_in_str_list(self):
        self.assertRaises(ValueError, models.HazardCalculation, sites='1 2, 3')

    def test_sites_valid_str_list(self):
        hjp = models.HazardCalculation(sites='1 2, 3 4')
        expected_wkt = (
            'MULTIPOINT (1.0000000000000000 2.0000000000000000,'
            ' 3.0000000000000000 4.0000000000000000)'
        )

        self.assertEqual(expected_wkt, hjp.sites.wkt)

    def test_region_from_wkt(self):
        hjp = models.HazardCalculation(region='POLYGON((1 2, 3 4, 5 6, 1 2))')
        expected_wkt = (
            'POLYGON ((1.0000000000000000 2.0000000000000000, '
            '3.0000000000000000 4.0000000000000000, '
            '5.0000000000000000 6.0000000000000000, '
            '1.0000000000000000 2.0000000000000000))'
        )

        self.assertEqual(expected_wkt, hjp.region.wkt)

    def test_region_invalid_str(self):
        self.assertRaises(
            ValueError, models.HazardCalculation,
            region='0, 0, 5a 5, 1, 3, 0, 0'
        )

    def test_region_odd_num_of_coords_in_str_list(self):
        self.assertRaises(
            ValueError, models.HazardCalculation, region='1 2, 3 4, 5 6, 1'
        )

    def test_region_valid_str_list(self):
        # note that the last coord (with closes the ring) can be ommitted
        # in this case
        hjp = models.HazardCalculation(region='1 2, 3 4, 5 6')
        expected_wkt = (
            'POLYGON ((1.0000000000000000 2.0000000000000000, '
            '3.0000000000000000 4.0000000000000000, '
            '5.0000000000000000 6.0000000000000000, '
            '1.0000000000000000 2.0000000000000000))'
        )

        self.assertEqual(expected_wkt, hjp.region.wkt)

    def test_points_to_compute_none(self):
        hc = models.HazardCalculation()
        self.assertIsNone(hc.points_to_compute())

        hc = models.HazardCalculation(region='1 2, 3 4, 5 6')
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

        hc = models.HazardCalculation(
            region='6.5 45.8, 6.5 46.5, 8.5 46.5, 8.5 45.8',
            region_grid_spacing=20)
        mesh = hc.points_to_compute(save_sites=False)

        numpy.testing.assert_array_almost_equal(lons, mesh.lons)
        numpy.testing.assert_array_almost_equal(lats, mesh.lats)

    def test_points_to_compute_sites(self):
        lons = [6.5, 6.5, 8.5, 8.5]
        lats = [45.8, 46.5, 46.5, 45.8]
        hc = models.HazardCalculation(
            sites='6.5 45.8, 6.5 46.5, 8.5 46.5, 8.5 45.8')

        mesh = hc.points_to_compute(save_sites=False)

        numpy.testing.assert_array_equal(lons, mesh.lons)
        numpy.testing.assert_array_equal(lats, mesh.lats)


class SESRuptureTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        job = helpers.get_hazard_job(cfg)

        lt_rlz = models.LtRealization.objects.create(
            hazard_calculation=job.hazard_calculation, ordinal=0, seed=0,
            sm_lt_path='foo', gsim_lt_path='bar', total_items=0)
        output = models.Output.objects.create(
            oq_job=job, owner=job.owner, display_name='test',
            output_type='ses')
        ses_coll = models.SESCollection.objects.create(
            output=output, lt_realization=lt_rlz)
        ses = models.SES.objects.create(
            ses_collection=ses_coll, investigation_time=50.0, ordinal=1)

        self.mesh_lons = numpy.array(
            [0.1 * x for x in range(16)]).reshape((4, 4))
        self.mesh_lats = numpy.array(
            [0.2 * x for x in range(16)]).reshape((4, 4))
        self.mesh_depths = numpy.array(
            [0.3 * x for x in range(16)]).reshape((4, 4))

        # planar surface coords
        self.ps_lons = [1, 3, 5, 7]
        self.ps_lats = [2, 4, 6, 8]
        self.ps_depths = [0.1, 0.2, 0.3, 0.4]

        self.fault_rupture = models.SESRupture.objects.create(
            ses=ses, old_magnitude=5, old_strike=0, old_dip=0, old_rake=0,
            old_tectonic_region_type='Active Shallow Crust',
            old_is_from_fault_source=True, old_lons=self.mesh_lons,
            old_is_multi_surface=False,
            old_lats=self.mesh_lats, old_depths=self.mesh_depths)
        self.source_rupture = models.SESRupture.objects.create(
            ses=ses, magnitude=5, old_strike=0, old_dip=0, old_rake=0,
            old_tectonic_region_type='Active Shallow Crust',
            old_is_from_fault_source=False, old_lons=self.ps_lons,
            old_is_multi_surface=False,
            old_lats=self.ps_lats, old_depths=self.ps_depths)

    def test_fault_rupture(self):
        # Test loading a fault rupture from the DB, just to illustrate a use
        # case.
        # Also, we should that planar surface corner points are not valid and
        # are more or less disregarded for this type of rupture.
        fault_rupture = models.SESRupture.objects.get(id=self.fault_rupture.id)
        self.assertIs(None, fault_rupture.top_left_corner)
        self.assertIs(None, fault_rupture.top_right_corner)
        self.assertIs(None, fault_rupture.bottom_right_corner)
        self.assertIs(None, fault_rupture.bottom_left_corner)

    def test_source_rupture(self):
        source_rupture = models.SESRupture.objects.get(
            id=self.source_rupture.id)
        self.assertEqual((1, 2, 0.1), source_rupture.top_left_corner)
        self.assertEqual((3, 4, 0.2), source_rupture.top_right_corner)
        self.assertEqual((5, 6, 0.3), source_rupture.bottom_left_corner)
        self.assertEqual((7, 8, 0.4), source_rupture.bottom_right_corner)

    def test__validate_planar_surface(self):
        source_rupture = models.SESRupture.objects.get(
            id=self.source_rupture.id)
        lons = source_rupture.lons
        lats = source_rupture.lats
        depths = source_rupture.depths

        # Should initially be valid
        source_rupture._validate_planar_surface()

        # If any of the coord attributes are a len != 4,
        # we should get an exception

        source_rupture.old_lons = [1, 2, 3]
        self.assertRaises(ValueError, source_rupture._validate_planar_surface)
        source_rupture.old_lons = lons

        source_rupture.old_lats = [1, 2, 3]
        self.assertRaises(ValueError, source_rupture._validate_planar_surface)
        source_rupture.old_lats = lats

        source_rupture.old_depths = [1, 2, 3]
        self.assertRaises(ValueError, source_rupture._validate_planar_surface)
        source_rupture.old_depths = depths


class ParseImtTestCase(unittest.TestCase):
    """
    Tests the parse_imt utility function
    """
    def test_sa(self):
        hc_im_type, sa_period, sa_damping = models.parse_imt("SA(0.1)")
        self.assertEqual("SA", hc_im_type)
        self.assertEqual(0.1, sa_period)
        self.assertEqual(models.DEFAULT_SA_DAMPING, sa_damping)

    def test_pga(self):
        hc_im_type, sa_period, sa_damping = models.parse_imt("PGA")
        self.assertEqual("PGA", hc_im_type)
        self.assertEqual(None, sa_period)
        self.assertEqual(None, sa_damping)


class GmfsPerSesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg = helpers.get_data_path('event_based_hazard/job.ini')
        job = helpers.get_hazard_job(cfg)
        rlz1 = models.LtRealization.objects.create(
            hazard_calculation=job.hazard_calculation,
            ordinal=1, seed=1, weight=None,
            sm_lt_path="test_sm", gsim_lt_path="test_gsim",
            is_complete=False, total_items=1, completed_items=1)
        rlz2 = models.LtRealization.objects.create(
            hazard_calculation=job.hazard_calculation,
            ordinal=2, seed=1, weight=None,
            sm_lt_path="test_sm", gsim_lt_path="test_gsim",
            is_complete=False, total_items=1, completed_items=1)
        ses_coll1 = models.SESCollection.objects.create(
            output=models.Output.objects.create_output(
                job, "Test SES Collection 1", "ses"),
            lt_realization=rlz1)
        ses_coll2 = models.SESCollection.objects.create(
            output=models.Output.objects.create_output(
                job, "Test SES Collection 2", "ses"),
            lt_realization=rlz2)
        gmf_data1 = helpers.create_gmf_data_records(job, rlz1, ses_coll1)[0]
        points = [(15.3, 38.22), (15.7, 37.22),
                  (15.4, 38.09), (15.56, 38.1), (15.2, 38.2)]
        gmf_data2 = helpers.create_gmf_data_records(
            job, rlz2, ses_coll2, points)[0]
        cls.gmf_coll1 = gmf_data1.gmf
        cls.parent_coll = models.Gmf.objects.create(
            output=models.Output.objects.create_output(
                job, "Test Hazard output", "complete_lt_gmf"))
        cls.ruptures1 = tuple(gmf_data1.rupture_ids)
        cls.ruptures2 = tuple(gmf_data2.rupture_ids)
        cls.investigation_time = job.hazard_calculation.investigation_time

    def test_branch_lt(self):
        all_gmfs = list(self.gmf_coll1.get_gmfs_per_ses(orderby=True))
        self.assertEqual(len(all_gmfs), 1)
        gmfs = all_gmfs[0]
        expected = """\
GMFsPerSES(investigation_time=%f, stochastic_event_set_id=%d,
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=%d
<X= 15.31000, Y= 38.22500, GMV=0.1000000>
<X= 15.48000, Y= 38.09100, GMV=0.1000000>
<X= 15.48100, Y= 38.25000, GMV=0.1000000>
<X= 15.56500, Y= 38.17000, GMV=0.1000000>
<X= 15.71000, Y= 37.22500, GMV=0.1000000>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=%d
<X= 15.31000, Y= 38.22500, GMV=0.2000000>
<X= 15.48000, Y= 38.09100, GMV=0.2000000>
<X= 15.48100, Y= 38.25000, GMV=0.2000000>
<X= 15.56500, Y= 38.17000, GMV=0.2000000>
<X= 15.71000, Y= 37.22500, GMV=0.2000000>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=%d
<X= 15.31000, Y= 38.22500, GMV=0.3000000>
<X= 15.48000, Y= 38.09100, GMV=0.3000000>
<X= 15.48100, Y= 38.25000, GMV=0.3000000>
<X= 15.56500, Y= 38.17000, GMV=0.3000000>
<X= 15.71000, Y= 37.22500, GMV=0.3000000>))""" % (
            (self.investigation_time, gmfs.stochastic_event_set_id) +
            self.ruptures1)
        self.assertEqual(str(gmfs), expected)

    def test_complete_lt(self):
        all_gmfs = list(self.parent_coll.get_gmfs_per_ses(orderby=True))
        self.assertEqual(len(all_gmfs), 1)
        gmfs = all_gmfs[0]
        expected = """\
GMFsPerSES(investigation_time=100.000000, stochastic_event_set_id=1,
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=%d
<X= 15.31000, Y= 38.22500, GMV=0.1000000>
<X= 15.48000, Y= 38.09100, GMV=0.1000000>
<X= 15.48100, Y= 38.25000, GMV=0.1000000>
<X= 15.56500, Y= 38.17000, GMV=0.1000000>
<X= 15.71000, Y= 37.22500, GMV=0.1000000>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=%d
<X= 15.31000, Y= 38.22500, GMV=0.2000000>
<X= 15.48000, Y= 38.09100, GMV=0.2000000>
<X= 15.48100, Y= 38.25000, GMV=0.2000000>
<X= 15.56500, Y= 38.17000, GMV=0.2000000>
<X= 15.71000, Y= 37.22500, GMV=0.2000000>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=%d
<X= 15.31000, Y= 38.22500, GMV=0.3000000>
<X= 15.48000, Y= 38.09100, GMV=0.3000000>
<X= 15.48100, Y= 38.25000, GMV=0.3000000>
<X= 15.56500, Y= 38.17000, GMV=0.3000000>
<X= 15.71000, Y= 37.22500, GMV=0.3000000>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=%s
<X= 15.20000, Y= 38.20000, GMV=0.1000000>
<X= 15.30000, Y= 38.22000, GMV=0.1000000>
<X= 15.40000, Y= 38.09000, GMV=0.1000000>
<X= 15.56000, Y= 38.10000, GMV=0.1000000>
<X= 15.70000, Y= 37.22000, GMV=0.1000000>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=%s
<X= 15.20000, Y= 38.20000, GMV=0.2000000>
<X= 15.30000, Y= 38.22000, GMV=0.2000000>
<X= 15.40000, Y= 38.09000, GMV=0.2000000>
<X= 15.56000, Y= 38.10000, GMV=0.2000000>
<X= 15.70000, Y= 37.22000, GMV=0.2000000>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=%s
<X= 15.20000, Y= 38.20000, GMV=0.3000000>
<X= 15.30000, Y= 38.22000, GMV=0.3000000>
<X= 15.40000, Y= 38.09000, GMV=0.3000000>
<X= 15.56000, Y= 38.10000, GMV=0.3000000>
<X= 15.70000, Y= 37.22000, GMV=0.3000000>))""" % (
            self.ruptures1 + self.ruptures2)
        self.assertEqual(str(gmfs), expected)


class PrepGeometryTestCase(unittest.TestCase):

    def test__prep_geometry(self):
        the_input = {
            # with commas between every value
            'sites': '-1.1, -1.2, 1.3, 0.0',
            # with no commas
            'region': '-1 1 1 1 1 -1 -1 -1',
            # with randomly placed commas
            'region_constraint': (
            '-0.5 0.5 0.0, 2.0 0.5 0.5, 0.5 -0.5 -0.5, -0.5'),
            'something': 'else',
        }

        expected = {
            'sites': 'MULTIPOINT(-1.1 -1.2, 1.3 0.0)',
            'region': (
                'POLYGON((-1.0 1.0, 1.0 1.0, 1.0 -1.0, -1.0 -1.0, -1.0 1.0))'),
            'region_constraint': (
                'POLYGON((-0.5 0.5, 0.0 2.0, 0.5 0.5, 0.5 -0.5, -0.5 -0.5, '
                '-0.5 0.5))'),
            'something': 'else',
        }

        self.assertEqual(expected, models._prep_geometry(the_input))


class GetSiteCollectionTestCase(unittest.TestCase):

    @attr('slow')
    def test_get_site_collection_with_site_model(self):
        cfg = helpers.get_data_path(
            'simple_fault_demo_hazard/job_with_site_model.ini')
        job = helpers.get_hazard_job(cfg)
        calc = cls_core.ClassicalHazardCalculator(job)

        # Bootstrap the `hazard_site` table:
        calc.initialize_sources()
        calc.initialize_site_model()

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

    def test_get_site_collection_with_reference_parameters(self):
        cfg = helpers.get_data_path('scenario_hazard/job.ini')
        job = helpers.get_hazard_job(cfg, username=getpass.getuser())
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
