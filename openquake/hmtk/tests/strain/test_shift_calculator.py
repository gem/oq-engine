# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

'''
Test suite for the class htmk.strain.shift.Shift, the class to implement the
SHIFT methodology for calculating activity rates from geodetic strain
'''
import os
import unittest
import numpy as np
from openquake.hmtk.parsers.strain.strain_csv_parser import ReadStrainCsv
from openquake.hmtk.strain.strain_utils import moment_function
from openquake.hmtk.strain.geodetic_strain import GeodeticStrain
from openquake.hmtk.strain.shift import Shift, BIRD_GLOBAL_PARAMETERS

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'strain_data')
STRAIN_FILE = os.path.join(BASE_DATA_PATH, 'simple_strain_values.csv')


class TestShift(unittest.TestCase):
    '''
    Test suite for the class openquake.hmtk.strain.shift.Shift
    '''
    def setUp(self):
        self.model = None
        self.strain_model = GeodeticStrain()

    def test_basic_instantiation(self):
        # Tests the basic instantiation of the SHIFT class
        # Instantiatiation with float
        self.model = Shift(5.0)
        np.testing.assert_array_almost_equal(self.model.target_magnitudes,
                                             np.array([5.0]))
        self.assertEqual(self.model.number_magnitudes, 1)
        # Instantiation with a numpy array
        self.model = Shift(np.arange(5., 8., 0.5))
        np.testing.assert_array_almost_equal(self.model.target_magnitudes,
                                             np.arange(5., 8., 0.5))
        self.assertEqual(self.model.number_magnitudes, 6)
        # Instantiation with  list
        self.model = Shift([5., 6., 7., 8.])
        np.testing.assert_array_almost_equal(self.model.target_magnitudes,
                                             np.array([5., 6., 7., 8.]))
        self.assertEqual(self.model.number_magnitudes, 4)
        # Otherwise raise an error
        with self.assertRaises(ValueError) as ae:
            self.model = Shift(None)
        self.assertEqual(str(ae.exception),
                         'Minimum magnitudes must be float, list or array')
        # Check regionalisation - assuming defaults
        self.model = Shift(5.0)
        for region in self.model.regionalisation.keys():
            self.assertDictEqual(BIRD_GLOBAL_PARAMETERS[region],
                                 self.model.regionalisation[region])
        np.testing.assert_array_almost_equal(np.log10(self.model.base_rate),
                                             np.array([-20.74610902]))

    def test_reclassify_with_bird_data(self):
        # Tests the re-classification from the Kreemer classification (C, O, S,
        # R and IPL) to the Bird & Liu (2007) classification:
        # Region Type               Kreemer Code   Bird Code
        # Intraplate                   IPL            IPL
        # Subduction                    S             SUB
        # Oceanic                       O             OCB
        # Continental Transform         C             CTF
        # Continental Convergent        C             CCB
        # Continental Rift              C             CRB
        # Rigde (e1h & e2h > 0.)        R             OSRnor (Normal spreading)
        # Ridge (e1h == 0.)             R             OSRnor
        # Ridge ((e1h * e2h < 0) and
        #         (e1h + e2h >= 0)      R             OSRnor/OTFmed
        # Ridge ((e1h * e2h < 0) and
        #         (e1h + e2h < 0)       R             OCB/OTFmed
        # Ridge (any other)             R             OCB
        self.model = Shift(5.0)
        self.strain_model.data = {
            # IPL SUB OCB CCB   CRB  CTF  CTF  OSRn OSRn  OSR1  OSR2 OCB
            'err': np.array([0., 0., 0., 1.0, -1.0, 0.1, -0.1, 0.0, 0.0,  0.0,
                             0.0, 0.0]),
            'e1h': np.array([0., 0., 0., 0.0, -1.0, 0.0, -1.0, 1.0, 0.0, -1.0,
                            -1.0, -1.0]),
            'e2h': np.array([0., 0., 0., 1.0,  0.0, 1.0,  0.0, 1.0, 0.0,  2.0,
                             0.5, -1.0]),
            'region': np.array(['IPL', 'S', 'O', 'C', 'C', 'C', 'C', 'R', 'R',
                                'R', 'R', 'R'], dtype='a13')}

        self.model.strain = self.strain_model
        expected_regions = [b'IPL', b'SUB', b'OCB', b'CCB', b'CRB', b'CTF',
                            b'CTF', b'OSRnor', b'OSRnor', b'OSR_special_1',
                            b'OSR_special_2', b'OCB']
        # Apply Bird Classification
        self.model._reclassify_Bird_regions_with_data()
        self.assertListEqual(expected_regions,
                             self.model.strain.data['region'].tolist())

    def test_continuum_seismicity(self):
        # Tests the function openquake.hmtk.strain.shift.Shift.continuum_seismicity -
        # the python implementation of the Subroutine Continuum Seismicity
        # from the Fortran 90 code GSRM.f90
        self.strain_model = GeodeticStrain()
        # Define a simple strain model
        test_data = {'longitude': np.zeros(3, dtype=float),
                     'latitude': np.zeros(3, dtype=float),
                     'exx': np.array([1E-9, 1E-8, 1E-7]),
                     'eyy': np.array([5E-10, 5E-9, 5E-8]),
                     'exy': np.array([2E-9, 2E-8, 2E-7])}
        self.strain_model.get_secondary_strain_data(test_data)
        self.model = Shift([5.66, 6.66])
        threshold_moment = moment_function(np.array([5.66, 6.66]))

        expected_rate = np.array([[-14.43624419, -22.48168502],
                                  [-13.43624419, -21.48168502],
                                  [-12.43624419, -20.48168502]])
        np.testing.assert_array_almost_equal(
            expected_rate,
            np.log10(self.model.continuum_seismicity(
                threshold_moment,
                self.strain_model.data['e1h'],
                self.strain_model.data['e2h'],
                self.strain_model.data['err'],
                BIRD_GLOBAL_PARAMETERS['OSRnor'])))

    def test_calculate_activity_rate(self):
        # Tests for the calculation of the activity rate. At this point
        # this is really a circular test - an independent test would be
        # helpful in future!
        parser0 = ReadStrainCsv(STRAIN_FILE)
        self.strain_model = parser0.read_data()
        self.model = Shift([5.0])
        self.model.calculate_activity_rate(self.strain_model)

        expected_rate = np.array([
            [5.66232696e-14], [5.66232696e-14],
            [5.66232696e-14], [5.66232696e-14], [2.73091764e-12],
            [2.80389274e-12], [2.88207458e-12], [6.11293721e-12],
            [8.19834427e-12], [6.55082175e-12], [7.90822653e-11],
            [7.85391610e-11], [8.12633607e-11], [7.66785657e-11],
            [4.07359524e-11], [2.16914046e-10], [4.74341943e-10],
            [1.99907599e-10], [3.55861556e-11], [1.69536101e-10],
            [1.69884622e-10], [1.70233341e-10], [5.06642764e-10]])

        np.testing.assert_array_almost_equal(
            np.log10(expected_rate),
            np.log10(self.model.strain.seismicity_rate))
