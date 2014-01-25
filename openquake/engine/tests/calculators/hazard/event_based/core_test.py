# Copyright (c) 2010-2013, GEM Foundation.
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
from openquake.hazardlib.source.rupture import Rupture
from openquake.hazardlib.site import Site
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.complex_fault import ComplexFaultSurface
from openquake.hazardlib.source.complex_fault import ComplexFaultSource
from openquake.hazardlib.gsim import get_available_gsims

from openquake.engine.db import models
from openquake.engine.calculators.hazard.event_based import core

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
    return models.SiteCollection(sites)


class FakeRupture(object):
    def __init__(self, id, trt, mag=5.0, rake=90.):
        hypocenter = Point(17.788328, -77.219496, 7.8125)
        lons = numpy.array(
            [-78.18106621, -78.18013243, -78.17919864, -78.15399318,
             -78.15305962, -78.15212606])
        lats = numpy.array(
            [15.615, 15.615, 15.615, 15.56553731,
             15.56553731,  15.56553731])
        surface = ComplexFaultSurface(Mesh(lons, lats, None))
        self.rupture = Rupture(mag, rake, trt, hypocenter,
                               surface, ComplexFaultSource)
        self.id = id


class EventBasedHazardTestCase(unittest.TestCase):
    """Tests for the routines used by the event-based hazard calculator"""

    # test a case with 5 sites and 2 ruptures
    def test_compute_gmf(self):
        hc = mock.Mock()
        hc.ground_motion_correlation_model = None
        hc.truncation_level = None
        hc.maximum_distance = 200.

        gsim = get_available_gsims()['AkkarBommer2010']()
        site_coll = make_site_coll(-78, 15.5, n=5)
        params = dict(truncation_level=3,
                      correl_model=None,
                      maximum_distance=200)
        trt = 'Subduction Interface'
        rupture_ids = range(2)
        ruptures = [FakeRupture(i, trt) for i in rupture_ids]
        rupture_seeds = rupture_ids
        pga = PGA()
        gmv_dict, rup_dict = core._compute_gmf(
            params, [pga], {trt: gsim}, site_coll, ruptures, rupture_seeds)
        expected_rups = {
            (pga, 0): rupture_ids,
            (pga, 1): rupture_ids,
            (pga, 2): rupture_ids,
            (pga, 3): rupture_ids,
            (pga, 4): rupture_ids,
        }
        expected_gmvs = {
            (pga, 0): [0.122149047040728, 0.0813899249039753],
            (pga, 1): [0.0541662667863476, 0.02136369236082],
            (pga, 2): [0.0772246502768338, 0.0226182956091826],
            (pga, 3): [0.166062666449449, 0.0164127269047494],
            (pga, 4): [0.133588538354143, 0.0529987707352876]
        }
        numpy.testing.assert_equal(rup_dict, expected_rups)
        for i, gmvs in expected_gmvs.iteritems():
            numpy.testing.assert_allclose(gmvs, expected_gmvs[i])


class EventBasedHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the core functionality of the event-based hazard calculator.
    """

    def setUp(self):
        self.cfg = helpers.get_data_path('event_based_hazard/job_2.ini')
        self.job = helpers.get_hazard_job(self.cfg, username=getpass.getuser())
        self.calc = core.EventBasedHazardCalculator(self.job)
        hc_id = self.job.hazard_calculation.id
        models.SiteCollection.cache[hc_id] = make_site_coll(0, 0, n=5)
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
        self.assertEqual(2, len(outputs))

        # With this job configuration, we have 2 logic tree realizations.
        lt_rlzs = models.LtRealization.objects.filter(hazard_calculation=hc)
        self.assertEqual(2, len(lt_rlzs))

        for rlz in lt_rlzs:
            sess = models.SES.objects.filter(
                ses_collection__lt_realization=rlz)
            self.assertEqual(hc.ses_per_logic_tree_path, len(sess))

            for ses in sess:
                # The only metadata in in the SES is investigation time.
                self.assertEqual(hc.investigation_time, ses.investigation_time)

    @attr('slow')
    def test_complete_event_based_calculation_cycle(self):
        # run the calculation in process (to easy debugging)
        # and check the outputs
        os.environ['OQ_NO_DISTRIBUTE'] = '1'
        try:
            job = helpers.run_hazard_job(self.cfg)
        finally:
            del os.environ['OQ_NO_DISTRIBUTE']
        hc = job.hazard_calculation
        rlz1, rlz2 = models.LtRealization.objects.filter(
            hazard_calculation=hc.id).order_by('ordinal')

        # check that the parameters are read correctly from the files
        self.assertEqual(hc.ses_per_logic_tree_path, 5)

        # check that we generated the right number of ruptures
        # (this is fixed if the seeds are fixed correctly)
        num_ruptures = models.SESRupture.objects.filter(
            ses__ses_collection__output__oq_job=job.id).count()
        self.assertEqual(num_ruptures, 196)

        # check that we generated the right number of rows in GmfData
        # 242 = 121 sites * 2 IMTs
        num_gmf1 = models.GmfData.objects.filter(
            gmf__lt_realization=rlz1, task_no=0).count()
        num_gmf2 = models.GmfData.objects.filter(
            gmf__lt_realization=rlz2, task_no=0).count()
        self.assertEqual(num_gmf1, 242)
        self.assertEqual(num_gmf2, 242)

        # Now check for the correct number of hazard curves:
        curves = models.HazardCurve.objects.filter(output__oq_job=job)
        # ((2 IMTs * 2 real) + (2 IMTs * (1 mean + 2 quantiles))) = 10
        # + 3 mean and quantiles multi-imt curves
        self.assertEqual(13, curves.count())

        # Finally, check for the correct number of hazard maps:
        maps = models.HazardMap.objects.filter(output__oq_job=job)
        # ((2 poes * 2 realizations * 2 IMTs)
        # + (2 poes * 2 IMTs * (1 mean + 2 quantiles))) = 20
        self.assertEqual(20, maps.count())

    def test_task_arg_gen(self):
        hc = self.job.hazard_calculation

        self.calc.initialize_sources()
        self.calc.initialize_realizations()

        [rlz1, rlz2] = models.LtRealization.objects.filter(
            hazard_calculation=hc).order_by('id')

        # create the ses collections
        self.calc.initialize_ses_db_records(rlz1)
        self.calc.initialize_ses_db_records(rlz2)

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
            ('4', 1760832373),
            ('3-0', 895150922),
            ('3-1', 1886047353),
            ('3-2', 2111769094),
            ('3-3', 1463337750),
            ('3-4', 1752507064),
            ('3-5', 27028211),
            ('3-6', 670491262),
            ('3-7', 390011773),
            ('3-8', 249942775),
            ('3-9', 1808974579),
            ('4', 644370012),
        ]

        # utility to present the generated arguments in a nicer way
        def process_args(arg_gen):
            for job_id, ss, rlz in arg_gen:
                for src, seed in ss:
                    if src.__class__.__name__ != 'PointSource':
                        yield src.source_id, seed

        actual = list(process_args(self.calc.task_arg_gen()))
        self.assertEqual(expected, actual)
