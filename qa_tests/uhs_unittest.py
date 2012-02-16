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


import numpy
import unittest

from openquake.db.models import OqCalculation
from openquake.db.models import UhSpectra
from openquake.db.models import UhSpectrum
from openquake.db.models import UhSpectrumData
from openquake.shapes import Site

from tests.utils.helpers import demo_file
from tests.utils.helpers import run_job


class UniformHazardSpectraQATest(unittest.TestCase):
    """End-to-end QA test for the UHS hazard calculator."""

    UHS_DEMO_CONFIG = demo_file('uhs/config.gem')

    EXP_RESULTS_FILES = {
        0.1: demo_file('uhs/expectedResults/uhs_0.1.dat'),
        0.02: demo_file('uhs/expectedResults/uhs_0.02.dat'),
    }

    def _load_expected_results(self):
        """Load expected test data from the provided tables.

        Data will be loaded in the following format::

            {0.02: {'periods': [0.025, 0.45, 2.5],
                    'sa_values': [0.5667404129191248,
                                  0.6185688023781438,
                                  0.11843417899553109]},
             0.1: {'periods': [0.025, 0.45, 2.5],
                   'sa_values': [0.2774217067746703,
                                 0.32675005743942004,
                                 0.05309858927852786]}}

        Dict keys are PoE values.
        """
        exp_data = dict()

        for poe, path in self.EXP_RESULTS_FILES.items():

            periods = []
            sa_values = []
            for line in open(path, 'r').readlines():
                line = line.strip()
                period, sa_value = line.split()
                periods.append(float(period))
                sa_values.append(float(sa_value))
            exp_data[poe] = dict(periods=periods, sa_values=sa_values)

        return exp_data

    def test_uhs(self):
        # Kick off the engine and run the UHS demo calculation.
        # When that's done, query the database and check the UHS results.

        exp_results = self._load_expected_results()
        exp_site = Site(0.0, 0.0)  # This calculation operates on a single site

        run_job(self.UHS_DEMO_CONFIG)

        calculation = OqCalculation.objects.latest('id')

        uh_spectra = UhSpectra.objects.get(
            output__oq_calculation=calculation.id)

        self.assertEqual(1, uh_spectra.realizations)

        for poe, data in exp_results.items():
            uh_spectrum = UhSpectrum.objects.get(poe=poe,
                                                 uh_spectra=uh_spectra.id)
            uh_spectrum_data = UhSpectrumData.objects.get(
                uh_spectrum=uh_spectrum.id)

            self.assertTrue(numpy.allclose(data['sa_values'],
                                          uh_spectrum_data.sa_values))
            self.assertTrue(numpy.allclose(data['periods'],
                            uh_spectra.periods))
            self.assertEqual(0, uh_spectrum_data.realization)
            self.assertEqual(exp_site.point.to_wkt(),
                             uh_spectrum_data.location.wkt)
