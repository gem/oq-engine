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
import mock
import numpy

from collections import namedtuple
from nose.plugins.attrib import attr

from openquake.hazardlib.imt import PGA

from openquake.engine.db import models
from openquake.engine.calculators.hazard.event_based import core
from openquake.engine.utils import stats

from tests.utils import helpers


class EventBasedHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the core functionality of the event-based hazard calculator.
    """

    def setUp(self):
        self.cfg = helpers.get_data_path('event_based_hazard/job_2.ini')
        self.job = helpers.get_hazard_job(self.cfg, username=getpass.getuser())
        self.calc = core.EventBasedHazardCalculator(self.job)
        models.JobStats.objects.create(oq_job=self.job)

    def test_donot_save_trivial_gmf(self):
        gmf_set = mock.Mock()

        # setup two ground motion fields on a region made by three
        # locations. On the first two locations the values are
        # nonzero, in the third one is zero. Then, we will expect the
        # bulk inserter to add only two entries.
        gmvs = numpy.matrix([[1., 1.],
                             [1., 1.],
                             [0., 0.]])
        gmf_dict = {PGA: dict(rupture_ids=[1, 2], gmvs=gmvs)}

        fake_bulk_inserter = mock.Mock()
        with helpers.patch('openquake.engine.writer.BulkInserter') as m:
            m.return_value = fake_bulk_inserter
            core._save_gmfs(
                gmf_set, gmf_dict, [mock.Mock(), mock.Mock(), mock.Mock()], 1)
            self.assertEqual(2, fake_bulk_inserter.add_entry.call_count)

    def test_save_only_nonzero_gmvs(self):
        gmf_set = mock.Mock()

        gmvs = numpy.matrix([[0.0, 0, 1]])
        gmf_dict = {PGA: dict(rupture_ids=[1, 2, 3], gmvs=gmvs)}

        fake_bulk_inserter = mock.Mock()
        with helpers.patch('openquake.engine.writer.BulkInserter') as m:
            m.return_value = fake_bulk_inserter
            core._save_gmfs(
                gmf_set, gmf_dict, [mock.Mock()], 1)
            call_args = fake_bulk_inserter.add_entry.call_args_list[0][1]
            self.assertEqual([1], call_args['gmvs'])
            self.assertEqual([3], call_args['rupture_ids'])

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

    def test_initialize_gmf_db_records(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_gmf_db_records])

        outputs = models.Output.objects.filter(
            oq_job=self.job, output_type='gmf')
        self.assertEqual(2, len(outputs))

        lt_rlzs = models.LtRealization.objects.filter(hazard_calculation=hc)
        self.assertEqual(2, len(lt_rlzs))

        for rlz in lt_rlzs:
            gmf_sets = models.GmfSet.objects.filter(
                gmf_collection__lt_realization=rlz)
            self.assertEqual(hc.ses_per_logic_tree_path, len(gmf_sets))

            for gmf_set in gmf_sets:
                # The only metadata in a GmfSet is investigation time.
                self.assertEqual(
                    hc.investigation_time, gmf_set.investigation_time)

    def test_initialize_pr_data_with_gmf(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_gmf_db_records])

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
        self.patch_gmf = mock.patch(
            'openquake.hazardlib.calc.gmf.ground_motion_fields',
            mock.MagicMock())
        self.patch_save_rup = mock.patch(
            'openquake.engine.calculators.hazard.'
            'event_based.core._save_ses_rupture')
        self.patch_save_gmf = mock.patch(
            'openquake.engine.calculators.hazard.'
            'event_based.core._save_gmfs')
        self.patch_ses.start()
        self.patch_gmf.start()
        self.patch_save_rup.start()
        self.patch_save_gmf.start()

    def _unpatch_calc(self):
        "Remove the patches"
        self.patch_ses.stop()
        self.patch_gmf.stop()
        self.patch_save_rup.stop()
        self.patch_save_gmf.stop()

    @attr('slow')
    def test_complete_event_based_calculation_cycle(self):
        self._patch_calc()
        try:
            from openquake.hazardlib import calc
            from openquake.engine.calculators.hazard.event_based import core
            ses_mock = calc.stochastic.stochastic_event_set_poissonian
            gmf_mock = calc.gmf.ground_motion_fields
            save_rup_mock = core._save_ses_rupture
            save_gmf_mock = core._save_gmfs

            # run the calculation in process and check the outputs
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

            # Check that we have the right number of gmf_sets.
            # The correct number is (num_real * ses_per_logic_tree_path).
            gmf_sets = models.GmfSet.objects.filter(
                gmf_collection__output__oq_job=job.id,
                gmf_collection__lt_realization__isnull=False)
            # 2 realizations, 5 ses_per_logic_tree_path
            self.assertEqual(10, gmf_sets.count())

            # check that we called the right number of times the patched
            # functions: 40 = 2 Lt * 4 sources * 5 ses = 8 tasks * 5 ses
            self.assertEqual(ses_mock.call_count, 40)
            self.assertEqual(save_rup_mock.call_count, 80)  # 2 rupt per ses
            self.assertEqual(gmf_mock.call_count, 80)  # 2 ruptures per ses
            self.assertEqual(save_gmf_mock.call_count, 40)  # num_tasks * ses

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


class TaskArgGenTestCase(unittest.TestCase):
    Job = namedtuple('Job', 'id, hazard_calculation')
    HC = namedtuple('HazardCalculation', 'random_seed')
    Rlz = namedtuple('Realization', 'id')

    def test_task_arg_gen(self):
        random_seed = 793
        hc = self.HC(random_seed)
        job = self.Job(1066, hc)

        base_path = (
            'openquake.engine.calculators.hazard.general.BaseHazardCalculator'
        )
        calc = core.EventBasedHazardCalculator(job)

        # Set up mocks:
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
        get_pt_patch = helpers.patch(
            '%s.%s' % (base_path, '_get_point_source_ids')
        )
        get_pt_mock = get_pt_patch.start()
        get_pt_mock.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        # _get_source_ids
        get_src_patch = helpers.patch('%s.%s' % (base_path, '_get_source_ids'))
        get_src_mock = get_src_patch.start()
        get_src_mock.return_value = [100, 101, 102, 103, 104]

        expected = [
            (1066, [1, 2, 3, 4, 5], 5, 1715084553, 1),
            (1066, [6, 7, 8, 9, 10], 5, 1610237348, 2),
            (1066, [11], 5, 208009464, 3),
            (1066, [100, 101], 5, 61227963, 4),
            (1066, [102, 103], 5, 962290868, 5),
            (1066, [104], 5, 1851493799, 6),
            (1066, [1, 2, 3, 4, 5], 6, 1726414414, 7),
            (1066, [6, 7, 8, 9, 10], 6, 1251340915, 8),
            (1066, [11], 6, 1914465987, 9),
            (1066, [100, 101], 6, 824295930, 10),
            (1066, [102, 103], 6, 1698161031, 11),
            (1066, [104], 6, 1690626266, 12),
        ]

        try:
            actual = list(calc.task_arg_gen(block_size=2))
            self.assertEqual(expected, actual)
        finally:
            self.assertEqual(1, pt_src_block_size_mock.call_count)
            pt_src_block_size_mock.stop()
            pt_src_block_size_patch.stop()

            self.assertEqual(1, get_rlz_mock.call_count)
            get_rlz_mock.stop()
            get_rlz_patch.stop()

            self.assertEqual(2, get_pt_mock.call_count)
            get_pt_mock.stop()
            get_pt_patch.stop()

            self.assertEqual(2, get_src_mock.call_count)
            get_src_mock.stop()
            get_src_patch.stop()
