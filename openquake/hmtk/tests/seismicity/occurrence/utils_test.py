# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
# 
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-

import os
import unittest
import numpy as np
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.occurrence.aki_maximum_likelihood import \
    AkiMaxLikelihood
import openquake.hmtk.seismicity.occurrence.utils as rec_utils

class RecurrenceTableTestCase(unittest.TestCase):
    """
    Unit tests for .
    """

    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

    def setUp(self):
        """
        """
        # Read initial dataset
        filename = os.path.join(self.BASE_DATA_PATH,
                                'completeness_test_cat.csv')
        test_data = np.genfromtxt(filename, delimiter=',', skip_header=1)
        # Create the catalogue A
        self.catalogueA = Catalogue.make_from_dict(
            {'year': test_data[:,3], 'magnitude': test_data[:,17]})

        # Read initial dataset
        filename = os.path.join(self.BASE_DATA_PATH,
                                'recurrence_test_cat_B.csv')
        test_data = np.genfromtxt(filename, delimiter=',', skip_header=1)
        # Create the catalogue A
        self.catalogueB = Catalogue.make_from_dict(
            {'year': test_data[:,3], 'magnitude': test_data[:,17]})

        # Read the verification table A
        filename = os.path.join(self.BASE_DATA_PATH,
                                'recurrence_table_test_A.csv')
        self.true_tableA = np.genfromtxt(filename, delimiter = ',')

        # Read the verification table A
        filename = os.path.join(self.BASE_DATA_PATH,
                                'recurrence_table_test_B.csv')
        self.true_tableB = np.genfromtxt(filename, delimiter = ',')

    def test_recurrence_table_A(self):
        """
        Basic recurrence table test
        """
        magnitude_interval = 0.1
        self.assertTrue( np.allclose(self.true_tableA,
            rec_utils.recurrence_table(self.catalogueA.data['magnitude'],
                                       magnitude_interval,
                                       self.catalogueA.data['year'])) )

    def test_recurrence_table_B(self):
        """
        Basic recurrence table test
        """
        magnitude_interval = 0.1
        self.assertTrue( np.allclose(self.true_tableB,
            rec_utils.recurrence_table(self.catalogueB.data['magnitude'],
                                       magnitude_interval,
                                       self.catalogueB.data['year'])) )

    def test_input_checks_raise_error(self):
        fake_completeness_table = np.zeros((10,10))
        catalogue = {}
        config = {}
        self.assertRaises(ValueError, rec_utils.input_checks, catalogue,
                config, fake_completeness_table)

    def test_input_checks_simple_input(self):
        completeness_table = [[1900, 2.0]]
        catalogue = Catalogue.make_from_dict(
            {'magnitude': [5.0, 6.0], 'year': [2000, 2000]})
        config = {}
        rec_utils.input_checks(catalogue, config, completeness_table)

    def test_input_checks_use_a_float_for_completeness(self):
        fake_completeness_table = 0.0
        catalogue = Catalogue.make_from_dict({'year': [1900]})
        config = {}
        rec_utils.input_checks(catalogue, config, fake_completeness_table)

    def test_input_checks_use_reference_magnitude(self):
        fake_completeness_table = 0.0
        catalogue = Catalogue.make_from_dict({'year': [1900]})
        config = {'reference_magnitude' : 3.0}
        cmag, ctime, ref_mag, dmag, _ = rec_utils.input_checks(catalogue,
                config, fake_completeness_table)
        self.assertEqual(3.0, ref_mag)

    def test_input_checks_sets_magnitude_interval(self):
        fake_completeness_table = 0.0
        catalogue = Catalogue.make_from_dict({'year': [1900]})
        config = {'magnitude_interval' : 0.1}
        cmag, ctime, ref_mag, dmag, _ = rec_utils.input_checks(catalogue,
                config, fake_completeness_table)
        self.assertEqual(0.1, dmag)


class TestSyntheticCatalogues(unittest.TestCase):
    '''
    Tests the synthetic catalogue functions
    '''
    def setUp(self):
        '''
        '''
        self.occur = AkiMaxLikelihood()

    def test_generate_magnitudes(self):
        '''
        Tests the openquake.hmtk.seismicity.occurence.utils function
        generate_trunc_gr_magnitudes
        '''
        bvals = []
        # Generate set of synthetic catalogues
        for _ in range(0, 100):
            mags = rec_utils.generate_trunc_gr_magnitudes(1.0, 4.0, 8.0, 1000)
            cat = Catalogue.make_from_dict(
                {'magnitude': mags,
                 'year': np.zeros(len(mags), dtype=int)})
            bvals.append(self.occur.calculate(cat)[0])
        bvals = np.array(bvals)
        self.assertAlmostEqual(np.mean(bvals), 1.0, 1)

    def test_generate_synthetic_catalogues(self):
        '''
        Tests the openquake.hmtk.seismicity.occurence.utils function
        generate_synthetic_magnitudes
        '''
        bvals = []
        # Generate set of synthetic catalogues
        for i in range(0, 100):
            cat1 = rec_utils.generate_synthetic_magnitudes(4.5, 1.0, 4.0, 8.0,
                                                           1000)
            bvals.append(self.occur.calculate(
                Catalogue.make_from_dict(cat1))[0])
        bvals = np.array(bvals)
        self.assertAlmostEqual(np.mean(bvals), 1.0, 1)


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")


class TestCompletenessCounts(unittest.TestCase):
    """
    Tests the counting of the number of events by completeness period
    """
    def setUp(self):
        cat_file = os.path.join(BASE_DATA_PATH, "synthetic_test_cat1.csv")
        raw_data = np.genfromtxt(cat_file, delimiter=",")
        neq = raw_data.shape[0]
        self.catalogue = Catalogue.make_from_dict({
            "eventID": raw_data[:, 0].astype(int),
            "year": raw_data[:, 1].astype(int),
            "dtime": raw_data[:, 2],
            "longitude": raw_data[:, 3],
            "latitude": raw_data[:, 4],
            "magnitude": raw_data[:, 5],
            "depth": raw_data[:, 6]})
        self.config = {"reference_magnitude": 3.0}
        self.completeness = np.array([[1990., 3.0],
                                      [1975., 4.0],
                                      [1960., 5.0],
                                      [1930., 6.0],
                                      [1910., 7.0]])

    def test_completeness_counts(self):
        """
        Assert that the correct counts are returned
        """
        expected_data = np.array([[3.25, 20.0, 1281.0],
                                  [3.75, 20.0,  468.0],
                                  [4.25, 35.0,  275.0],
                                  [4.75, 35.0,  116.0],
                                  [5.25, 50.0,   55.0],
                                  [5.75, 50.0,   17.0],
                                  [6.25, 80.0,   11.0],
                                  [6.75, 80.0,    2.0],
                                  [7.25,100.0,    1.0]])
        cent_mag, t_per, n_obs = rec_utils.get_completeness_counts(
            self.catalogue, self.completeness, 0.5)
        np.testing.assert_array_almost_equal(cent_mag, expected_data[:, 0])
        np.testing.assert_array_almost_equal(t_per, expected_data[:, 1])
        np.testing.assert_array_almost_equal(n_obs, expected_data[:, 2])
        self.assertEqual(self.catalogue.get_number_events(),
                         int(np.sum(n_obs)))
