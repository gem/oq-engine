# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2013, GEM Foundation, G. Weatherill, M. Pagani,
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
# The software Hazard Modeller's Toolkit (hmtk) provided herein
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
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-

"""

"""

import unittest
import numpy as np
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.utils import spherical_to_cartesian
from hmtk.seismicity.catalogue import Catalogue
from hmtk.seismicity.utils import decimal_time

class CatalogueTestCase(unittest.TestCase):
    """
    Unit tests for the Catalogue class
    """
    def setUp(self):
        self.data_array = np.array([
                               [1900, 5.00], # E
                               [1910, 6.00], # E
                               [1920, 7.00], # I
                               [1930, 5.00], # E
                               [1970, 5.50], # I
                               [1960, 5.01], # I
                               [1960, 6.99], # I
                               ])
        self.mt_table = np.array([[1920, 7.0],
                                  [1940, 6.0],
                                  [1950, 5.5],
                                  [1960, 5.0],
                                ])

    def test_load_from_array(self):
        """
        Tests the creation of a catalogue from an array and a key list
        """
        cat = Catalogue()
        cat.load_from_array(['year','magnitude'], self.data_array)
        self.assertTrue(np.allclose(cat.data['magnitude'],self.data_array[:,1]))
        self.assertTrue(np.allclose(cat.data['year'],
                                    self.data_array[:,0].astype(int)))

    def test_load_to_array(self):
        """
        Tests the creation of a catalogue from an array and a key list
        """
        cat = Catalogue()
        cat.load_from_array(['year','magnitude'], self.data_array)
        data = cat.load_to_array(['year','magnitude'])
        self.assertTrue(np.allclose(data, self.data_array))

    def test_catalogue_mt_filter(self):
        """
        Tests the catalogue magnitude-time filter
        """
        cat = Catalogue()
        cat.load_from_array(['year','magnitude'], self.data_array)
        cat.data['eventID'] = np.arange(0, 7)
        cat.catalogue_mt_filter(self.mt_table)
        mag = np.array([7.0, 5.5, 5.01, 6.99])
        yea = np.array([1920, 1970, 1960, 1960])
        self.assertTrue(np.allclose(cat.data['magnitude'],mag))
        self.assertTrue(np.allclose(cat.data['year'],yea))


    def test_get_decimal_time(self):
        '''
        Tests the decimal time function. The function itself is tested in
        tests.seismicity.utils so only minimal testing is undertaken here to
        ensure coverage
        '''
        time_dict = {'year': np.array([1990, 2000]),
                     'month': np.array([3, 9]),
                     'day': np.ones(2, dtype=int),
                     'hour': np.ones(2, dtype=int),
                     'minute': np.ones(2, dtype=int),
                     'second': np.ones(2, dtype=float)}
        expected_dec_time = decimal_time(time_dict['year'],
                                         time_dict['month'],
                                         time_dict['day'],
                                         time_dict['hour'],
                                         time_dict['minute'],
                                         time_dict['second'])

        cat = Catalogue()
        for key in ['year', 'month', 'day', 'hour', 'minute', 'second']:
            cat.data[key] = np.copy(time_dict[key])
        np.testing.assert_array_almost_equal(expected_dec_time,
                                             cat.get_decimal_time())

    def test_hypocentres_as_mesh(self):
        '''
        Tests the function to render the hypocentres to a
        nhlib.geo.mesh.Mesh object.
        '''
        cat = Catalogue()
        cat.data['longitude'] = np.array([2., 3.])
        cat.data['latitude'] = np.array([2., 3.])
        cat.data['depth'] = np.array([2., 3.])
        self.assertTrue(isinstance(cat.hypocentres_as_mesh(), Mesh))

    def test_hypocentres_to_cartesian(self):
        '''
        Tests the function to render the hypocentres to a cartesian array.
        The invoked function nhlib.geo.utils.spherical_to_cartesian is
        tested as part of the nhlib suite. The test here is included for
        coverage
        '''

        cat = Catalogue()
        cat.data['longitude'] = np.array([2., 3.])
        cat.data['latitude'] = np.array([2., 3.])
        cat.data['depth'] = np.array([2., 3.])
        expected_data = spherical_to_cartesian(cat.data['longitude'],
                                               cat.data['latitude'],
                                               cat.data['depth'])
        model_output = cat.hypocentres_to_cartesian()
        np.testing.assert_array_almost_equal(expected_data, model_output)

    def test_purge_catalogue(self):
        '''
        Tests the function to purge the catalogue of invalid events
        '''
        cat1 = Catalogue()
        cat1.data['eventID'] = np.array([100, 101, 102], dtype=int)
        cat1.data['magnitude'] = np.array([4., 5., 6.], dtype=float)
        cat1.data['Agency'] = ['XXX', 'YYY', 'ZZZ']

        flag_vector = np.array([False, True, False])
        cat1.purge_catalogue(flag_vector)
        np.testing.assert_array_almost_equal(cat1.data['magnitude'],
                                             np.array([5.]))
        np.testing.assert_array_equal(cat1.data['eventID'],
                                             np.array([101]))
        self.assertListEqual(cat1.data['Agency'], ['YYY'])


class TestGetDistributions(unittest.TestCase):
    """
    Class to test the hmtk.seismicity.catalogue.Catalogue methods to
    determine depth distribution, magnitude-depth distribution,
    and magnitude-time distribution
    """
    def setUp(self):
        """
        """
        self.catalogue = Catalogue()


    def test_depth_distribution_no_depth_error(self):
        """
        Checks to ensure error is raised when no depths are found in catalogue
        """
        depth_bins = np.arange(0., 60., 10.)
        self.catalogue.data['depth'] = np.array([])
        with self.assertRaises(ValueError) as ae:
            self.catalogue.get_depth_distribution(depth_bins)
        self.assertEqual(ae.exception.message,
                         'Depths missing in catalogue')

    def test_depth_distribution_simple(self):
        """
        Tests the calculation of the depth histogram with no uncertainties
        """
        # Without normalisation
        self.catalogue.data['depth'] = np.arange(5., 50., 5.)
        depth_bins = np.arange(0., 60., 10.)
        expected_array = np.array([1., 2., 2., 2., 2.])
        np.testing.assert_array_almost_equal(
            expected_array,
            self.catalogue.get_depth_distribution(depth_bins))
        # With normalisation
        np.testing.assert_array_almost_equal(
            expected_array / np.sum(expected_array),
            self.catalogue.get_depth_distribution(depth_bins,
                                                  normalisation=True))

    def test_depth_distribution_uncertainties(self):
        """
        Tests the depth distribution with uncertainties
        """
        # Without normalisation
        self.catalogue.data['depth'] = np.arange(5., 50., 5.)
        self.catalogue.data['depthError'] = 3. * np.ones_like(
            self.catalogue.data['depth'])
        depth_bins = np.arange(-10., 70., 10.)
        expected_array = np.array([0., 1.5, 2., 2., 2., 1.5, 0.])
        hist_array = self.catalogue.get_depth_distribution(depth_bins,
                                                           bootstrap=1000)
        array_diff = np.round(hist_array, 1) - expected_array
        self.assertTrue(np.all(np.fabs(array_diff) < 0.2))
        # With normalisation
        expected_array = np.array([0., 0.16, 0.22, 0.22, 0.22, 0.16, 0.01])
        hist_array = self.catalogue.get_depth_distribution(depth_bins,
                                                           normalisation=True,
                                                           bootstrap=1000)
        array_diff = np.round(hist_array, 2) - expected_array
        self.assertTrue(np.all(np.fabs(array_diff) < 0.03))



class TestMagnitudeDepthDistribution(unittest.TestCase):
    """
    Tests the method for generating the magnitude depth distribution
    """
    def setUp(self):
        """
        """
        self.catalogue = Catalogue()
        x, y = np.meshgrid(np.arange(5., 50., 10.), np.arange(5.5, 9.0, 1.))
        nx, ny = np.shape(x)
        self.catalogue.data['depth'] = (x.reshape([nx * ny, 1])).flatten()
        self.catalogue.data['magnitude'] = (y.reshape([nx * ny, 1])).flatten()

    def test_depth_distribution_no_depth_error(self):
        """
        Checks to ensure error is raised when no depths are found in catalogue
        """
        depth_bins = np.arange(0., 60., 10.)
        self.catalogue.data['depth'] = np.array([])
        with self.assertRaises(ValueError) as ae:
            self.catalogue.get_depth_distribution(depth_bins)
        self.assertEqual(ae.exception.message,
                         'Depths missing in catalogue')

    def test_distribution_no_uncertainties(self):
        """
        Tests the magnitude-depth distribution without uncertainties
        """
        # Without normalisation
        depth_bins = np.arange(0., 60., 10.)
        mag_bins = np.arange(5., 10., 1.)
        expected_array = np.ones([len(mag_bins) - 1, len(depth_bins) - 1],
                                 dtype=float)
        np.testing.assert_array_almost_equal(
            expected_array,
            self.catalogue.get_magnitude_depth_distribution(mag_bins,
                                                            depth_bins))
        # With normalisation
        np.testing.assert_array_almost_equal(
            expected_array / np.sum(expected_array),
            self.catalogue.get_magnitude_depth_distribution(mag_bins,
                depth_bins, normalisation=True))

    def test_mag_depth_distribution_uncertainties(self):
        """
        Tests the magnitude depth distribution with uncertainties
        """
        self.catalogue.data['depthError'] = 3.0 * np.ones_like(
            self.catalogue.data['depth'])
        self.catalogue.data['sigmaMagnitude'] = 0.1 * np.ones_like(
            self.catalogue.data['sigmaMagnitude'])

        # Extend depth bins to test that no negative depths are being returned
        depth_bins = np.arange(-10., 70., 10.)
        mag_bins = np.arange(5., 10., 1.)
        expected_array = np.array([[0., 1., 1., 1., 1., 1., 0.],
                                   [0., 1., 1., 1., 1., 1., 0.],
                                   [0., 1., 1., 1., 1., 1., 0.],
                                   [0., 1., 1., 1., 1., 1., 0.]])
        test_array = self.catalogue.get_magnitude_depth_distribution(
            mag_bins, depth_bins)
        array_diff = expected_array - np.round(test_array, 1)
        self.assertTrue(np.all(np.fabs(array_diff) < 0.2))
        # Check to make sure first columns is all zeros
        np.testing.assert_array_almost_equal(test_array[:, 0],
                                             np.zeros(4, dtype=float))


class TestMagnitudeTimeDistribution(unittest.TestCase):
    """
    Simple class to test the magnitude time density distribution
    """
    def setUp(self):
        """
        """
        self.catalogue = Catalogue()
        x, y = np.meshgrid(np.arange(1915., 2010., 10.),
                           np.arange(5.5, 9.0, 1.0))


        nx, ny = np.shape(x)
        self.catalogue.data['magnitude'] = (y.reshape([nx * ny, 1])).flatten()
        x = (x.reshape([nx * ny, 1])).flatten()
        self.catalogue.data['year'] = x.astype(int)
        self.catalogue.data['month'] = np.ones_like(x, dtype=int)
        self.catalogue.data['day'] = np.ones_like(x, dtype=int)
        self.catalogue.data['hour'] = np.ones_like(x, dtype=int)
        self.catalogue.data['minute'] = np.ones_like(x, dtype=int)
        self.catalogue.data['second'] = np.ones_like(x, dtype=float)


    def test_magnitide_time_distribution_no_uncertainties(self):
        """
        Tests the magnitude-depth distribution without uncertainties
        """
        mag_range = np.arange(5., 10., 1.)
        time_range = np.arange(1910., 2020., 10.)
        # Without normalisation
        expected_array = np.ones([len(time_range) - 1, len(mag_range) - 1],
                                 dtype=float)
        np.testing.assert_array_almost_equal(expected_array,
            self.catalogue.get_magnitude_time_distribution(mag_range,
                                                           time_range))
        # With Normalisation
        np.testing.assert_array_almost_equal(
            expected_array / np.sum(expected_array),
            self.catalogue.get_magnitude_time_distribution(mag_range,
                                                           time_range,
                                                           normalisation=True))
