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


import numpy
import unittest

from openquake import engine
from openquake import java
from openquake.calculators.hazard.uhs.core import UHSCalculator
from openquake.calculators.hazard.uhs.core import compute_uhs
from openquake.calculators.hazard.uhs.core import compute_uhs_task
from openquake.calculators.hazard.uhs.core import write_uh_spectra
from openquake.calculators.hazard.uhs.core import write_uhs_spectrum_data
from openquake.db.models import Output
from openquake.db.models import SiteModel
from openquake.db.models import UhSpectra
from openquake.db.models import UhSpectrum
from openquake.db.models import UhSpectrumData
from openquake.java import list_to_jdouble_array
from openquake.shapes import Site
from openquake.utils import stats

from tests.utils import helpers


UHS_DEMO_CONFIG_FILE = helpers.demo_file('uhs/config.gem')


class UHSBaseTestCase(unittest.TestCase):
    """Shared functionality for UHS test cases."""

    # Used for mocking
    UHS_CORE_MODULE = 'openquake.calculators.hazard.uhs.core'

    def setUp(self):
        self.job = engine.prepare_job()
        self.job_profile, params, sections = engine.import_job_profile(
            UHS_DEMO_CONFIG_FILE, self.job)

        self.job_ctxt = engine.JobContext(
            params, self.job.id, sections=sections,
            serialize_results_to=['db'], oq_job_profile=self.job_profile,
            oq_job=self.job)
        self.job_ctxt.to_kvs()
        self.job_id = self.job_ctxt.job_id


class UHSCoreTestCase(UHSBaseTestCase):
    """Tests for core UHS tasks and other functions."""

    # Sample UHS result data
    UHS_RESULTS = [
        (0.1, [0.2774217067746703,
               0.32675005743942004,
               0.05309858927852786]),
        (0.02, [0.5667404129191248,
                0.6185688023781438,
                0.11843417899553109])]

    def test_compute_uhs(self):
        # Test the :function:`openquake.hazard.uhs.core.compute_uhs`
        # function. This function makes use of the Java `UHSCalculator` and
        # performs the main UHS computation.

        # The results of the computation are a sequence of Java `UHSResult`
        # objects.
        the_job = helpers.job_from_file(UHS_DEMO_CONFIG_FILE)

        site = Site(0.0, 0.0)

        helpers.store_hazard_logic_trees(the_job)

        uhs_results = compute_uhs(the_job, site)

        for i, result in enumerate(uhs_results):
            poe = result.getPoe()
            uhs = result.getUhs()

            self.assertEquals(self.UHS_RESULTS[i][0], poe)
            self.assertTrue(numpy.allclose(self.UHS_RESULTS[i][1],
                                           [x.value for x in uhs]))

    def test_compute_uhs_with_site_model(self):
        the_job = helpers.prepare_job_context(
            helpers.demo_file('uhs/config_with_site_model.gem'))
        the_job.to_kvs()

        site = Site(0, 0)

        helpers.store_hazard_logic_trees(the_job)

        get_sm_patch = helpers.patch(
            'openquake.calculators.hazard.general.get_site_model')
        get_closest_patch = helpers.patch(
            'openquake.calculators.hazard.general.get_closest_site_model_data')
        compute_patch = helpers.patch(
            'openquake.calculators.hazard.uhs.core._compute_uhs')

        get_sm_mock = get_sm_patch.start()
        get_closest_mock = get_closest_patch.start()
        compute_mock = compute_patch.start()

        get_closest_mock.return_value = SiteModel(
            vs30=800, vs30_type='measured', z1pt0=100, z2pt5=200)
        try:
            import nose; nose.tools.set_trace()
            compute_uhs(the_job, site)

            import nose; nose.tools.set_trace()
            self.assertEqual(1, get_sm_mock.call_count)
            self.assertEqual(1, get_closest_mock.call_count)
            self.assertEqual(1, compute_mock.call_count)
        finally:
            get_sm_patch.stop()
            get_closest_patch.stop()
            compute_patch.stop()



    def test_write_uh_spectra(self):
        # Test the writing of the intial database records for UHS results.
        # The function under test (`write_uh_spectra`) should write:
        #   - 1 uiapi.output record
        #   - 1 hzrdr.uh_spectra record
        #   - 1 hzrdr.uh_spectrum record per PoE defined in the oq_job_profile

        # Call the function under test:
        write_uh_spectra(self.job_ctxt)

        # Now check that the expected records were indeed created.
        output = Output.objects.get(oq_job=self.job.id)
        self.assertEqual('uh_spectra', output.output_type)

        uh_spectra = UhSpectra.objects.get(output=output.id)
        self.assertEqual(
            self.job_profile.investigation_time, uh_spectra.timespan)
        self.assertEqual(
            self.job_profile.realizations, uh_spectra.realizations)
        self.assertEqual(self.job_profile.uhs_periods, uh_spectra.periods)

        uh_spectrums = UhSpectrum.objects.filter(uh_spectra=uh_spectra.id)
        # We just want to make sure there is one record in hzrdr.uh_spectrum
        # per PoE.
        self.assertEqual(
            set(self.job_profile.poes), set([x.poe for x in uh_spectrums]))

    def test_write_uhs_spectrum_data(self):
        # Test `write_uhs_spectrum_data`.

        # To start with, we need to write the 'container' records for the UHS
        # results:
        write_uh_spectra(self.job_ctxt)

        uhs_results = []  # The results we want to write to HDF5
        uhs_result = java.jvm().JClass('org.gem.calc.UHSResult')

        # Build up a result list that we can pass to the function under test:
        for poe, uhs in self.UHS_RESULTS:
            uhs_results.append(uhs_result(poe, list_to_jdouble_array(uhs)))

        realization = 0
        test_site = Site(0.0, 0.0)

        # Call the function under test
        write_uhs_spectrum_data(
            self.job_ctxt, realization, test_site, uhs_results)

        uhs_data = UhSpectrumData.objects.filter(
            uh_spectrum__uh_spectra__output__oq_job=(
            self.job.id))

        self.assertEqual(len(self.UHS_RESULTS), len(uhs_data))
        self.assertTrue(all([x.realization == 0 for x in uhs_data]))

        uhs_results_dict = dict(self.UHS_RESULTS)  # keyed by PoE
        for uhs_datum in uhs_data:
            self.assertTrue(
                numpy.allclose(uhs_results_dict[uhs_datum.uh_spectrum.poe],
                               uhs_datum.sa_values))
            self.assertEqual(test_site.point.to_wkt(), uhs_datum.location.wkt)

    def test_compute_uhs_task_calls_compute_and_write(self):
        # The celery task `compute_uhs_task` basically just calls a few other
        # functions to do the calculation and write results. Those functions
        # have their own test coverage; in this test, we just want to make
        # sure they get called.

        cmpt_uhs = '%s.%s' % (self.UHS_CORE_MODULE, 'compute_uhs')
        write_uhs_data = '%s.%s' % (self.UHS_CORE_MODULE,
                                    'write_uhs_spectrum_data')
        with helpers.patch(cmpt_uhs) as compute_mock:
            with helpers.patch(write_uhs_data) as write_mock:
                # Call the function under test as a normal function, not a
                # @task:
                compute_uhs_task(self.job_id, 0, Site(0.0, 0.0))

                self.assertEqual(1, compute_mock.call_count)
                self.assertEqual(1, write_mock.call_count)


class UHSTaskProgressIndicatorTestCase(UHSBaseTestCase):
    """Tests progress indicator behavior for UHS @task functions."""

    def test_compute_uhs_task_pi(self):
        # Test that progress indicators are working properly for
        # `compute_uhs_task`.

        # Mock out the two 'heavy' functions called by this task;
        # we don't need to do these and we don't want to waste the cycles.
        cmpt_uhs = '%s.%s' % (self.UHS_CORE_MODULE, 'compute_uhs')
        write_uhs_data = '%s.%s' % (self.UHS_CORE_MODULE,
                                    'write_uhs_spectrum_data')
        with helpers.patch(cmpt_uhs):
            with helpers.patch(write_uhs_data):

                get_counter = lambda: stats.get_counter(
                    self.job_id, 'h', 'compute_uhs_task', 'i')

                # First, check that the counter for `compute_uhs_task` is
                # `None`:
                self.assertIsNone(get_counter())

                realization = 0
                site = Site(0.0, 0.0)
                # execute the task as a plain old function
                compute_uhs_task(self.job_id, realization, site)
                self.assertEqual(1, get_counter())

                compute_uhs_task(self.job_id, realization, site)
                self.assertEqual(2, get_counter())

    def test_compute_uhs_task_pi_failure_counter(self):
        # Same as the previous test, except that we want to make sure task
        # failure counters are properly incremented if a task fails.

        cmpt_uhs = '%s.%s' % (self.UHS_CORE_MODULE, 'compute_uhs')
        with helpers.patch(cmpt_uhs) as compute_mock:

            # We want to force a failure to occur in the task:
            compute_mock.side_effect = RuntimeError('Mock exception')

            get_counter = lambda: stats.get_counter(
                self.job_id, 'h', 'compute_uhs_task-failures', 'i')

            # The counter should start out empty:
            self.assertIsNone(get_counter())

            # tasks_args: job_id, realization, site
            task_args = (self.job_id, 0, Site(0.0, 0.0))
            self.assertRaises(RuntimeError, compute_uhs_task, *task_args)
            self.assertEqual(1, get_counter())

            # Create two more failures:
            self.assertRaises(RuntimeError, compute_uhs_task, *task_args)
            self.assertRaises(RuntimeError, compute_uhs_task, *task_args)
            self.assertEqual(3, get_counter())


class UHSCalculatorTestCase(UHSBaseTestCase):
    """Tests for :class:`openquake.calculators.hazard.uhs.core.UHSCalculator`.
    """

    def test_initialize(self):
        # Test that `initialize` sets the task total counter with the correct
        # value
        # First, check that the total counter doesn't exist.
        task_total = lambda: stats.get_counter(
            self.job_id, 'h', 'uhs:tasks', 't')
        self.assertIsNone(task_total())

        calc = UHSCalculator(self.job_ctxt)

        calc.initialize()

        # In this test file, there is only 1 realization and 1 site.
        # So, the expected total is 1.
        self.assertEqual(1, task_total())

    def test_pre_execute(self):
        # Simply tests that `pre_execute` calls `write_uh_spectra`.
        # That's all for now.
        calc = UHSCalculator(self.job_ctxt)

        with helpers.patch(
            '%s.write_uh_spectra' % self.UHS_CORE_MODULE) as write_mock:
            calc.pre_execute()
            self.assertEqual(1, write_mock.call_count)

    def test_post_execute(self):
        calc = UHSCalculator(self.job_ctxt)

        expected_call_args = ((self.job_id,), {})

        with helpers.patch(
            'openquake.utils.stats.delete_job_counters') as del_mock:
            calc.post_execute()
            self.assertEqual(1, del_mock.call_count)
            self.assertEqual(expected_call_args, del_mock.call_args)
