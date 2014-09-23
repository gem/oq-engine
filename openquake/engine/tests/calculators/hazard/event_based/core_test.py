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


import os
import getpass
import unittest
import mock
import numpy

from nose.plugins.attrib import attr

from openquake.hazardlib.imt import PGA
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.complex_fault import ComplexFaultSurface
from openquake.hazardlib.gsim import get_available_gsims

from openquake.engine.db import models
from openquake.engine.calculators.hazard.event_based import core

from openquake.engine.tests.calculators.hazard.event_based \
    import _pp_test_data as test_data
from openquake.engine.tests.utils import helpers


def make_mock_points(n):
    points = []
    for _ in range(n):
        point = mock.Mock()
        point.wkt2d = 'XXX'
        points.append(point)
    return points


def make_site_coll(lon, lat, n):
    assert n <= 1000
    sites = []
    for i in range(n):
        site = Site(Point(lon - float(i) / 1000, lat),
                    800., 'measured', 50., 2.5, i)
        sites.append(site)
    return SiteCollection(sites)


class FakeRupture(object):
    def __init__(self, id, trt, mag=5.0, rake=90.):
        self.hypocenter = Point(17.788328, -77.219496, 7.8125)
        lons = numpy.array(
            [-78.18106621, -78.18013243, -78.17919864, -78.15399318,
             -78.15305962, -78.15212606])
        lats = numpy.array(
            [15.615, 15.615, 15.615, 15.56553731,
             15.56553731,  15.56553731])
        self.surface = ComplexFaultSurface(Mesh(lons, lats, None))
        self.mag = mag
        self.rake = rake
        self.id = id
        self.site_indices = None


class GmfCalculatorTestCase(unittest.TestCase):
    """Tests for the routines used by the event-based hazard calculator"""

    # test a case with 5 sites and 2 ruptures
    def test_compute_gmf(self):
        hc = mock.Mock()
        hc.ground_motion_correlation_model = None
        hc.truncation_level = None
        hc.maximum_distance = 200.

        trt = 'Subduction Interface'
        gsim = get_available_gsims()['AkkarBommer2010']()
        num_sites = 5
        site_coll = make_site_coll(-78, 15.5, num_sites)
        rup_id, rup_seed = 42, 44
        rup = FakeRupture(rup_id, trt)
        pga = PGA()
        rlz = mock.Mock()
        rlz.id = 1
        calc = core.GmfCalculator(
            [pga], [gsim], trt_model_id=1, truncation_level=3)
        calc.calc_gmfs(site_coll, rup, [(rup.id, rup_seed)])
        expected_rups = {
            ('AkkarBommer2010', 'PGA', 0): [rup_id],
            ('AkkarBommer2010', 'PGA', 1): [rup_id],
            ('AkkarBommer2010', 'PGA', 2): [rup_id],
            ('AkkarBommer2010', 'PGA', 3): [rup_id],
            ('AkkarBommer2010', 'PGA', 4): [rup_id],
        }
        expected_gmvs = {
            ('AkkarBommer2010', 'PGA', 0): [0.1027847118266612],
            ('AkkarBommer2010', 'PGA', 1): [0.02726361912605336],
            ('AkkarBommer2010', 'PGA', 2): [0.0862595971325641],
            ('AkkarBommer2010', 'PGA', 3): [0.04727148908077005],
            ('AkkarBommer2010', 'PGA', 4): [0.04750575818347277],
        }
        numpy.testing.assert_equal(calc.ruptures_per_site, expected_rups)
        for i, gmvs in expected_gmvs.iteritems():
            numpy.testing.assert_allclose(gmvs, expected_gmvs[i])

        # 5 curves (one per each site) for 3 levels, 1 IMT
        [(gname, [curves])] = calc.to_haz_curves(
            site_coll.sids, dict(PGA=[0.03, 0.04, 0.05]),
            invest_time=50., num_ses=10)
        self.assertEqual(gname, 'AkkarBommer2010')
        numpy.testing.assert_array_almost_equal(
            curves,
            [[0.09516258, 0.09516258, 0.09516258],  # curve site1
             [0.00000000, 0.00000000, 0.00000000],  # curve site2
             [0.09516258, 0.09516258, 0.09516258],  # curve site3
             [0.09516258, 0.09516258, 0.00000000],  # curve site4
             [0.09516258, 0.09516258, 0.00000000],  # curve site5
             ])


class EventBasedHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the core functionality of the event-based hazard calculator.
    """

    def setUp(self):
        self.cfg = helpers.get_data_path('event_based_hazard/job_2.ini')
        self.job = helpers.get_job(self.cfg, username=getpass.getuser())
        self.calc = core.EventBasedHazardCalculator(self.job)
        hc = self.job.hazard_calculation
        hc._site_collection = make_site_coll(0, 0, n=5)
        models.JobStats.objects.create(oq_job=self.job)

    @unittest.skip  # temporarily skipped
    def test_donot_save_trivial_gmf(self):
        ses = mock.Mock()

        # setup two ground motion fields on a region made by three
        # locations. On the first two locations the values are
        # nonzero, in the third one is zero. Then, we will expect the
        # cache inserter to add only two entries.
        gmvs = numpy.matrix([[1., 1.],
                             [1., 1.],
                             [0., 0.]])
        gmf_dict = {PGA: dict(rupture_ids=[1, 2], gmvs=gmvs)}
        points = make_mock_points(3)
        with helpers.patch('openquake.engine.writer.CacheInserter') as m:
            core._save_gmfs(
                ses, gmf_dict, points)
            self.assertEqual(2, m.add.call_count)

    @unittest.skip  # temporarily skipped
    def test_save_only_nonzero_gmvs(self):
        ses = mock.Mock()

        gmvs = numpy.matrix([[0.0, 0, 1]])
        gmf_dict = {PGA: dict(rupture_ids=[1, 2, 3], gmvs=gmvs)}

        points = make_mock_points(1)
        with helpers.patch('openquake.engine.writer.CacheInserter') as m:
            core._save_gmfs(ses, gmf_dict, points)
            self.assertEqual(1, m.add.call_count)

    def test_initialize_ses_db_records(self):
        hc = self.job.hazard_calculation
        self.calc.pre_execute()

        outputs = models.Output.objects.filter(
            oq_job=self.job, output_type='ses')
        # there is a single source model realization in this test
        self.assertEqual(1, len(outputs))

        ses_coll = models.SESCollection.objects.get(
            lt_model__hazard_calculation=self.job)
        self.assertEqual(hc.ses_per_logic_tree_path, len(ses_coll))
        for ses in ses_coll:
            # The only metadata in in the SES is investigation time.
            self.assertEqual(hc.investigation_time, ses.investigation_time)

    @attr('slow')
    def test_complete_event_based_calculation_cycle(self):
        # run the calculation in process (to easy debugging)
        # and check the outputs
        with mock.patch.dict(os.environ, {'OQ_NO_DISTRIBUTE': '1'}):
            job = helpers.run_job(self.cfg)
        hc = job.hazard_calculation
        [rlz1, rlz2] = models.LtRealization.objects.filter(
            lt_model__hazard_calculation=job)

        # check that the parameters are read correctly from the files
        self.assertEqual(hc.ses_per_logic_tree_path, 5)

        # check that we generated the right number of ruptures
        # (this is fixed if the seeds are fixed correctly)
        num_ruptures = models.SESRupture.objects.filter(
            rupture__ses_collection__output__oq_job=job.id).count()
        self.assertEqual(num_ruptures, 94)

        num_gmf1 = models.GmfData.objects.filter(
            gmf__lt_realization=rlz1).count()

        num_gmf2 = models.GmfData.objects.filter(
            gmf__lt_realization=rlz2).count()

        # check that we generated the same number of rows in GmfData
        # for both realizations
        self.assertEqual(num_gmf1, num_gmf2)
        # check that the number of tasks is a multiple of
        # 242 = 121 sites * 2 IMTs
        self.assertEqual(num_gmf1 % 242, 0)

        # Now check for the correct number of hazard curves:
        curves = models.HazardCurve.objects.filter(output__oq_job=job)
        # ((2 IMTs * 2 rlz) + (2 IMTs * (1 mean + 2 quantiles))) = 10
        # + 6 multi-imt curves (3 quantiles + 1 mean + 2 rlz)
        self.assertEqual(15, curves.count())

        # Finally, check for the correct number of hazard maps:
        maps = models.HazardMap.objects.filter(output__oq_job=job)
        # ((2 poes * 2 realizations * 2 IMTs)
        # + (2 poes * 2 IMTs * (1 mean + 2 quantiles))) = 20
        self.assertEqual(20, maps.count())

    def test_task_arg_gen(self):
        self.calc.pre_execute()
        # this is also testing the splitting of fault sources
        expected = [  # source_id, seed
            ('3-0', 540589706),
            ('3-1', 721420855),
            ('3-2', 1007747341),
            ('3-3', 573154379),
            ('3-4', 1310571686),
            ('3-5', 2015354266),
            ('3-6', 425466075),
            ('3-7', 41871302),
            ('3-8', 930268948),
            ('3-9', 1920723121),
            ('4-0', 1760832373),
            ('4-1', 736921862),
            ('4-2', 754518695),
            ('4-3', 1135503673),
            ('4-4', 31299080),
            ('4-5', 277795359),
            ('4-6', 598901721),
            ('4-7', 85073212),
            ('4-8', 782936146),
            ('4-9', 536916930)
        ]

        # utility to present the generated arguments in a nicer way
        def process_args(arg_gen):
            for args in arg_gen:
                # args is (job_id, sitecol, src_seed_pairs, ...)
                for src, seed in args[2]:
                    if src.__class__.__name__ != 'PointSource':
                        yield src.source_id, seed

        actual = list(process_args(self.calc.task_arg_gen()))
        self.assertEqual(expected, actual)


class GmvsToHazCurveTestCase(unittest.TestCase):
    """
    Tests for
    :func:`openquake.engine.calculators.hazard.event_based.\
post_processing.gmvs_to_haz_curve`.
    """

    def test_gmvs_to_haz_curve_site_1(self):
        expected_poes = [0.63578, 0.39347, 0.07965]
        imls = [0.01, 0.1, 0.2]
        gmvs = test_data.SITE_1_GMVS
        invest_time = 1.0  # years
        duration = 1000.0  # years

        actual_poes = core.gmvs_to_haz_curve(gmvs, imls, invest_time, duration)
        numpy.testing.assert_array_almost_equal(
            expected_poes, actual_poes, decimal=6)

    def test_gmvs_to_haz_curve_case_2(self):
        expected_poes = [0.63578, 0.28609, 0.02664]
        imls = [0.01, 0.1, 0.2]
        gmvs = test_data.SITE_2_GMVS
        invest_time = 1.0  # years
        duration = 1000.0  # years

        actual_poes = core.gmvs_to_haz_curve(gmvs, imls, invest_time, duration)
        numpy.testing.assert_array_almost_equal(
            expected_poes, actual_poes, decimal=6)


class UnknownGsimTestCase(unittest.TestCase):
    # the case where the source model contains a TRT which does not
    # exist in the gsim_logic_tree file
    def test(self):
        cfg = helpers.get_data_path('bad_gsim/job.ini')
        job = helpers.get_job(cfg, username=getpass.getuser())
        calc = core.EventBasedHazardCalculator(job)
        with self.assertRaises(ValueError) as ctxt:
            calc.initialize_sources()
        errmsg = str(ctxt.exception)
        assert errmsg.startswith(
            "Found in 'source_model.xml' a tectonic region type "
            "'Active Shallow Crust' inconsistent with the ones"), errmsg
