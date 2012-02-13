# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


import h5py
import numpy
import os
import tempfile
import unittest

from openquake import engine
from openquake import java
from openquake.java import list_to_jdouble_array
from openquake.shapes import Site
from openquake.db.models import OqCalculation
from openquake.db.models import Output
from openquake.db.models import UhSpectra
from openquake.db.models import UhSpectrum
from openquake.db.models import UhSpectrumData
from openquake.utils import stats
from openquake.calculators.hazard.uhs.core import compute_uhs
from openquake.calculators.hazard.uhs.core import compute_uhs_task
from openquake.calculators.hazard.uhs.core import touch_result_file
from openquake.calculators.hazard.uhs.core import write_uh_spectra
from openquake.calculators.hazard.uhs.core import write_uhs_spectrum_data

from tests.utils import helpers


UHS_DEMO_CONFIG_FILE = helpers.demo_file('uhs/config.gem')


class UHSBaseTestCase(unittest.TestCase):
    """Shared functionality for UHS test cases."""

    # Used for mocking
    UHS_CORE_MODULE = 'openquake.calculators.hazard.uhs.core'

    def setUp(self):
        # Create OqJobProfile, OqCalculation, and CalculationProxy objects
        # which can be used for several of the tests:
        self.job_profile, params, sections = engine.import_job_profile(
            UHS_DEMO_CONFIG_FILE)
        self.calculation = OqCalculation(
            owner=self.job_profile.owner,
            oq_job_profile=self.job_profile)
        self.calculation.save()

        self.calc_proxy = engine.CalculationProxy(
            params, self.calculation.id, sections=sections,
            serialize_results_to=['db'], oq_job_profile=self.job_profile,
            oq_calculation=self.calculation)


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

    def test_touch_result_file(self):
        # Call the :function:`openquake.hazard.uhs.core.touch_result_file` and
        # verify that the result file is properly created with the correct
        # number of datasets.

        # We also want to verify the name (since it is associated with a
        # specific site of interest) as well as the size and datatype of each
        # dataset.
        _, path = tempfile.mkstemp()

        fake_job_id = 1  # The job_id doesn't matter in this test.
        sites = [Site(-122.000, 38.113), Site(-122.114, 38.113)]
        n_samples = 4
        n_periods = 3

        with helpers.patch('openquake.utils.tasks.get_running_calculation'):
            touch_result_file(fake_job_id, path, sites, n_samples, n_periods)

        # Does the resulting file exist?
        self.assertTrue(os.path.exists(path))

        # Read the file and check the names, sizes, and datatypes of each
        # dataset.
        with h5py.File(path, 'r') as h5_file:
            # There should be exactly 2 datasets.
            self.assertEquals(2, len(h5_file))

            for site in sites:
                ds_name = 'lon:%s-lat:%s' % (site.longitude, site.latitude)
                ds = h5_file.get(ds_name)
                self.assertIsNotNone(ds)
                self.assertEquals(numpy.float64, ds.dtype)
                self.assertEquals((n_samples, n_periods), ds.shape)

        # Clean up the test file.
        os.unlink(path)

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

    def test_write_uh_spectra(self):
        # Test the writing of the intial database records for UHS results.
        # The function under test (`write_uh_spectra`) should write:
        #   - 1 uiapi.output record
        #   - 1 hzrdr.uh_spectra record
        #   - 1 hzrdr.uh_spectrum record per PoE defined in the oq_job_profile

        # Call the function under test:
        write_uh_spectra(self.calc_proxy)

        # Now check that the expected records were indeed created.
        output = Output.objects.get(oq_calculation=self.calculation.id)
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
        write_uh_spectra(self.calc_proxy)

        uhs_results = []  # The results we want to write to HDF5
        uhs_result = java.jvm().JClass('org.gem.calc.UHSResult')

        # Build up a result list that we can pass to the function under test:
        for poe, uhs in self.UHS_RESULTS:
            uhs_results.append(uhs_result(poe, list_to_jdouble_array(uhs)))

        realization = 0
        test_site = Site(0.0, 0.0)

        # Call the function under test
        write_uhs_spectrum_data(
            self.calc_proxy, realization, test_site, uhs_results)

        uhs_data = UhSpectrumData.objects.filter(
            uh_spectrum__uh_spectra__output__oq_calculation=(
            self.calculation.id))

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
                compute_uhs_task(self.calc_proxy.job_id, 0, Site(0.0, 0.0))

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
                    self.calc_proxy.job_id, 'h', 'compute_uhs_task', 'i')

                # First, check that the counter for `compute_uhs_task` is
                # `None`:
                self.assertIsNone(get_counter())

                realization = 0
                site = Site(0.0, 0.0)
                compute_uhs_task(self.calc_proxy.job_id, realization, site)
                self.assertEqual(1, get_counter())

                compute_uhs_task(self.calc_proxy.job_id, realization, site)
                self.assertEqual(2, get_counter())
