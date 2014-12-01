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

from openquake.engine.calculators.hazard.classical import core
from openquake.engine.db import models
from openquake.engine.tests.utils import helpers


class ClassicalHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the main methods of the classical hazard calculator.
    """

    def setUp(self):
        self.job, self.calc = self._setup_a_new_calculator()
        models.JobStats.objects.create(oq_job=self.job)

    def _setup_a_new_calculator(self):
        cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        job = helpers.get_job(cfg, username=getpass.getuser())
        calc = core.ClassicalHazardCalculator(job)
        return job, calc

    @attr('slow')
    def test_complete_calculation_workflow(self):
        # Test the calculation workflow, from pre_execute through clean_up
        hc = self.job.get_oqparam()

        self.calc.pre_execute()

        # Update job status to move on to the execution phase.
        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()
        self.calc.execute()

        # after filtering there are 74 sources
        self.assertEqual(len(list(self.calc.composite_model.sources)), 74)

        self.job.status = 'post_executing'
        self.job.save()
        self.calc.post_execute()

        lt_rlzs = models.LtRealization.objects.filter(
            lt_model__hazard_calculation=self.job)

        self.assertEqual(2, len(lt_rlzs))

        # Now we test that the htemp results were copied to the final location
        # in `hzrdr.hazard_curve` and `hzrdr.hazard_curve_data`.
        for rlz in lt_rlzs:

            # get hazard curves for this realization
            [pga_curves] = models.HazardCurve.objects.filter(
                lt_realization=rlz.id, imt='PGA')
            [sa_curves] = models.HazardCurve.objects.filter(
                lt_realization=rlz.id, imt='SA', sa_period=0.025)

            # check that the multi-hazard-curve outputs have been
            # created for this realization

            self.assertEqual(
                1,
                models.HazardCurve.objects.filter(
                    lt_realization=rlz.id, imt=None, statistics=None).count())

            # In this calculation, we have 120 sites of interest.
            # We should have exactly that many curves per realization
            # per IMT.
            pga_curve_data = models.HazardCurveData.objects.filter(
                hazard_curve=pga_curves.id)
            self.assertEqual(120, len(pga_curve_data))
            sa_curve_data = models.HazardCurveData.objects.filter(
                hazard_curve=sa_curves.id)
            self.assertEqual(120, len(sa_curve_data))

        # test post processing
        self.job.status = 'post_processing'
        self.job.save()
        self.calc.post_process()

        # Test for the correct number of mean/quantile curves
        self.assertEqual(
            1,
            models.HazardCurve.objects.filter(
                output__oq_job=self.job,
                lt_realization__isnull=True, statistics="mean",
                imt="PGA").count())
        self.assertEqual(
            1,
            models.HazardCurve.objects.filter(
                output__oq_job=self.job,
                lt_realization__isnull=True, statistics="mean",
                imt="SA", sa_period=0.025).count())
        self.assertEqual(
            1,
            models.HazardCurve.objects.filter(
                output__oq_job=self.job,
                lt_realization__isnull=True, statistics="mean",
                imt=None).count())

        for quantile in hc.quantile_hazard_curves:
            self.assertEqual(
                1,
                models.HazardCurve.objects.filter(
                    lt_realization__isnull=True, statistics="quantile",
                    output__oq_job=self.job,
                    quantile=quantile,
                    imt="PGA").count())
            self.assertEqual(
                1,
                models.HazardCurve.objects.filter(
                    lt_realization__isnull=True, statistics="quantile",
                    output__oq_job=self.job,
                    quantile=quantile,
                    imt="SA", sa_period=0.025).count())
            self.assertEqual(
                1,
                models.HazardCurve.objects.filter(
                    lt_realization__isnull=True, statistics="quantile",
                    output__oq_job=self.job,
                    quantile=quantile,
                    imt=None).count())

        # Test for the correct number of maps.
        # The expected count is:
        # (num_poes * num_imts * num_rlzs)
        # +
        # (num_poes * num_imts * (1 mean + num_quantiles))
        # Thus:
        # (2 * 2 * 2) + (2 * 2 * (1 + 2)) = 20
        hazard_maps = models.HazardMap.objects.filter(output__oq_job=self.job)
        self.assertEqual(20, hazard_maps.count())

        # test for the correct number of UH Spectra:
        # The expected count is:
        # (num_hazard_maps_PGA_or_SA / num_poes)
        # (20 / 2) = 10
        uhs = models.UHS.objects.filter(output__oq_job=self.job)
        self.assertEqual(10, uhs.count())
        # Now test the number of curves in each UH Spectra
        # It should be equal to the number of sites (120)
        for u in uhs:
            self.assertEqual(120, u.uhsdata_set.count())

        self.job.status = 'clean_up'
        self.job.save()

        # now test the hazard calculation can be removed
        self.job.delete(using='admin')


def update_result_matrix(current, new):
    return 1 - (1 - current) * (1 - new)


class HelpersTestCase(unittest.TestCase):
    """
    Tests for helper functions in the classical hazard calculator core module.
    """

    def test_update_result_matrix_with_scalars(self):
        init = 0.0
        result = update_result_matrix(init, 0.2)
        # The first time we apply this formula on a 0.0 value,
        # result is equal to the first new value we apply.
        self.assertAlmostEqual(0.2, result)

        result = update_result_matrix(result, 0.3)
        self.assertAlmostEqual(0.44, result)

    def test_update_result_matrix_numpy_arrays(self):
        init = numpy.zeros((4, 4))
        first = numpy.array([0.2] * 16).reshape((4, 4))

        result = update_result_matrix(init, first)
        numpy.testing.assert_allclose(first, result)

        second = numpy.array([0.3] * 16).reshape((4, 4))
        result = update_result_matrix(result, second)

        expected = numpy.array([0.44] * 16).reshape((4, 4))
        numpy.testing.assert_allclose(expected, result)


class NoSourcesTestCase(unittest.TestCase):
    # using a small maximum distance of 1 km, so that no sources are found
    def test(self):
        cfg = helpers.get_data_path('classical_job.ini')
        with mock.patch.dict(os.environ, {'OQ_NO_DISTRIBUTE': '1'}):
            with self.assertRaises(RuntimeError):
                helpers.run_job(cfg, maximum_distance=1)
