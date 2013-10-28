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


import os
import getpass
import unittest
import itertools
import mock
import numpy

from nose.plugins.attrib import attr

from openquake.hazardlib.imt import PGA

from openquake.engine.db import models
from openquake.engine.calculators.hazard.event_based import core
from openquake.engine.utils import stats

from tests.utils import helpers


def make_mock_points(n):
    points = []
    for _ in range(n):
        point = mock.Mock()
        point.wkt2d = 'XXX'
        points.append(point)
    return points


class EventBasedHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the core functionality of the event-based hazard calculator.
    """

    def setUp(self):
        self.cfg = helpers.get_data_path('event_based_hazard/job_2.ini')
        self.job = helpers.get_hazard_job(self.cfg, username=getpass.getuser())
        self.calc = core.EventBasedHazardCalculator(self.job)
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

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_ses_db_records])

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

    def test_initialize_pr_data_with_ses(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_ses_db_records])

        ltr1, ltr2 = models.LtRealization.objects.filter(
            hazard_calculation=hc).order_by("id")

        ltr1.completed_items = 12
        ltr1.save()

        self.calc.initialize_pr_data()

        total = stats.pk_get(self.calc.job.id, "nhzrd_total")
        self.assertEqual(ltr1.total_items + ltr2.total_items, total)
        done = stats.pk_get(self.calc.job.id, "nhzrd_done")
        self.assertEqual(ltr1.completed_items + ltr2.completed_items, done)

    def test_initialize_pr_data_with_gmf(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_ses_db_records])

        ltr1, ltr2 = models.LtRealization.objects.filter(
            hazard_calculation=hc).order_by("id")

        ltr1.completed_items = 13
        ltr1.save()

        self.calc.initialize_pr_data()

        total = stats.pk_get(self.calc.job.id, "nhzrd_total")
        self.assertEqual(ltr1.total_items + ltr2.total_items, total)
        done = stats.pk_get(self.calc.job.id, "nhzrd_done")
        self.assertEqual(ltr1.completed_items + ltr2.completed_items, done)

    def test_initialize_complete_lt_ses_db_records_branch_enum(self):
        # Set hazard_calculation.number_of_logic_tree_samples = 0
        # This indicates that the `end-branch enumeration` method should be
        # used to carry out the calculation.

        # This test was added primarily for branch coverage (in the case of end
        # branch enum) for the method `initialize_complete_lt_ses_db_records`.
        hc = self.job.hazard_calculation
        hc.number_of_logic_tree_samples = 0

        self.calc.initialize_sources()
        self.calc.initialize_realizations()

        self.calc.initialize_complete_lt_ses_db_records()

        complete_lt_ses = models.SES.objects.get(
            ses_collection__output__oq_job=self.job.id,
            ses_collection__output__output_type='complete_lt_ses',
            ordinal=None)

        self.assertEqual(250.0, complete_lt_ses.investigation_time)
        self.assertIsNone(complete_lt_ses.ordinal)

    def _patch_calc(self):
        """
        Patch the stochastic functions and the save-to-db functions in the
        calculator to make the test faster and independent on the stochastic
        number generator
        """
        rupture1 = mock.Mock()
        rupture1.tectonic_region_type = 'Active Shallow Crust'
        rupture2 = mock.Mock()
        rupture2.tectonic_region_type = 'Active Shallow Crust'
        self.patch_ses = mock.patch(
            'openquake.hazardlib.calc.stochastic.'
            'stochastic_event_set_poissonian',
            mock.MagicMock(return_value=[rupture1, rupture2]))
        self.patch_save_rup = mock.patch(
            'openquake.engine.calculators.hazard.'
            'event_based.core._save_ses_ruptures',
            mock.MagicMock(return_value=[1, 2]))
        self.patch_ses.start()
        self.patch_save_rup.start()

    def _unpatch_calc(self):
        "Remove the patches"
        self.patch_ses.stop()
        self.patch_save_rup.stop()

    @attr('slow')
    def test_complete_event_based_calculation_cycle(self):
        self._patch_calc()
        try:
            from openquake.hazardlib import calc
            from openquake.engine.calculators.hazard.event_based import core
            ses_mock = calc.stochastic.stochastic_event_set_poissonian
            save_rup_mock = core._save_ses_ruptures

            # run the calculation in process (to easy debugging)
            # and check the outputs; notice that since the save_ses
            # part is mocked the gmf won't be computed
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

            # check that we called the right number of times the patched
            # functions: 40 = 2 Lt * 4 sources * 5 ses = 8 tasks * 5 ses
            self.assertEqual(ses_mock.call_count, 40)
            self.assertEqual(save_rup_mock.call_count, 40)  # 2 rupt per ses

            # Check the complete logic tree SES
            complete_lt_ses = models.SES.objects.get(
                ses_collection__output__oq_job=job.id,
                ses_collection__output__output_type='complete_lt_ses',
                ordinal=None)

            # Test the computed `investigation_time`
            # 2 lt realizations * 5 ses_per_logic_tree_path * 50.0 years
            self.assertEqual(500.0, complete_lt_ses.investigation_time)

            self.assertIsNone(complete_lt_ses.ordinal)

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
        finally:
            self._unpatch_calc()

    def test_task_arg_gen(self):
        hc = self.job.hazard_calculation

        self.calc.initialize_sources()
        self.calc.initialize_realizations()

        [rlz1, rlz2] = models.LtRealization.objects.filter(
            hazard_calculation=hc).order_by('id')

        [s1, s2, s3, s4, s5] = self.calc.initialize_ses_db_records(rlz1)
        [t1, t2, t3, t4, t5] = self.calc.initialize_ses_db_records(rlz2)

        expected = [  # sources, ses_id, seed
            ([1], s1, [1711655216]),
            ([1], s2, [1038305917]),
            ([1], s3, [836289861]),
            ([1], s4, [1781144172]),
            ([1], s5, [1869241528]),
            ([2], s1, [215682727]),
            ([2], s2, [1101399957]),
            ([2], s3, [2054512780]),
            ([2], s4, [1550095676]),
            ([2], s5, [1537531637]),
            ([3], s1, [834081132]),
            ([3], s2, [2109160433]),
            ([3], s3, [1527803099]),
            ([3], s4, [1876252834]),
            ([3], s5, [1712942246]),
            ([4], s1, [219667398]),
            ([4], s2, [332999334]),
            ([4], s3, [1017801655]),
            ([4], s4, [1577927432]),
            ([4], s5, [1810736590]),
            ([1], t1, [745519017]),
            ([1], t2, [2107357950]),
            ([1], t3, [1305437041]),
            ([1], t4, [75519567]),
            ([1], t5, [179387370]),
            ([2], t1, [1653492095]),
            ([2], t2, [176278337]),
            ([2], t3, [777508283]),
            ([2], t4, [718002527]),
            ([2], t5, [1872666256]),
            ([3], t1, [796266430]),
            ([3], t2, [646033314]),
            ([3], t3, [289567826]),
            ([3], t4, [1964698790]),
            ([3], t5, [613832594]),
            ([4], t1, [1858181087]),
            ([4], t2, [195127891]),
            ([4], t3, [1761641849]),
            ([4], t4, [259827383]),
            ([4], t5, [1464146382]),
        ]

        # utilities to present the generated arguments in a nicer way
        dic = {}
        counter = itertools.count(1)

        def src_no(src_id):
            try:
                return dic[src_id]
            except KeyError:
                dic[src_id] = counter.next()
                return dic[src_id]

        def process_args(arg_gen):
            for job_id, source_ids, ses, task_seed in arg_gen:
                yield map(src_no, source_ids), ses, task_seed

        actual = list(process_args(self.calc.task_arg_gen()))
        self.assertEqual(expected, actual)
