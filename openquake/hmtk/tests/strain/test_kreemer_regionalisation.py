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
Test functions for applying the regionalisation of Kreemer et al. (2003):
'''
import os
import unittest
import numpy as np
from linecache import getlines
from openquake.hmtk.strain.geodetic_strain import GeodeticStrain
from openquake.hmtk.strain.regionalisation.kreemer_regionalisation import (
    _build_kreemer_cell, KreemerRegionalisation)

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'strain_data')
KREEMER_2POLY_FILE = 'kreemer_2poly_sample.txt'
KREEMER_2REG_FILE = os.path.join(BASE_DATA_PATH,
                                 'kreemer_2poly_sample_2types.txt')
KREEMER_POLY_SAMPLE = getlines(os.path.join(BASE_DATA_PATH,
                                            KREEMER_2POLY_FILE))


class TestBuildKreemerCell(unittest.TestCase):
    def setUp(self):
        self.data = KREEMER_POLY_SAMPLE

    def test_build_kreemer_polygon(self):
        expected_output_1 = np.array([[179.4, -66.],
                                      [180., -66.],
                                      [180., -65.5],
                                      [179.4, -65.5],
                                      [179.4, -66.]])

        expected_output_2 = np.array([[180., -66.],
                                      [180.6, -66.],
                                      [180.6, -65.5],
                                      [180., -65.5],
                                      [180., -66.]])
        print(self.data)
        np.testing.assert_array_almost_equal(expected_output_1,
                                             _build_kreemer_cell(self.data, 0))

        np.testing.assert_array_almost_equal(expected_output_2,
                                             _build_kreemer_cell(self.data, 6))


class TestKreemerRegionalisation(unittest.TestCase):
    '''
    Class to test the Kreemer Regionalisation
    '''
    def setUp(self):
        self.reader = None
        self.model = None

    def test_simple_instantiation(self):
        # Tests the basic instantiation with a filename and nothing more
        filename = 'a filename'
        expected_dict = {'filename': filename,
                         'strain': None}
        self.reader = KreemerRegionalisation(filename)
        self.assertDictEqual(expected_dict, self.reader.__dict__)

    def test_point_in_tectonic_region(self):
        # Basic check to ensure that a point is correctly identified as being
        # inside the regional polygon
        # Setup Model
        polygon = {'long_lims': [-1.0, 1.0],
                   'lat_lims': [-1.0, 1.0],
                   'area': 1.0,
                   'region_type': 'XXX'}

        self.model = GeodeticStrain()
        self.model.data = {
            'longitude': np.array([-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]),
            'latitude': np.array([-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]),
            'region': np.zeros(7, dtype='|S3'),
            'area': np.zeros(7, dtype=float),
            'exx': np.zeros(7, dtype=float)}

        self.reader = KreemerRegionalisation('a filename')
        self.reader.strain = self.model
        self.reader._point_in_tectonic_region(polygon)
        expected_region = [b'', b'XXX', b'XXX', b'XXX', b'XXX', b'', b'']
        for iloc in range(0, 7):
            self.assertEqual(
                expected_region[iloc], self.reader.strain.data['region'][iloc])
        np.testing.assert_array_almost_equal(
            self.reader.strain.data['area'],
            np.array([0., 1., 1., 1., 1., 0., 0.]))

    def test_define_kreemer_regionalisation(self):
        # Tests the function to retrieve the polygons from the regionalisation
        # file in the format defined by Corner Kreemer
        self.reader = KreemerRegionalisation(KREEMER_2POLY_FILE)
        expected_output = [{'area': 1.0,
                            'cell': None,
                            'lat_lims': np.array([-66., -65.5]),
                            'long_lims': np.array([179.4, 180.]),
                            'region_type': 'R'},
                           {'area': 1.0,
                            'cell': None,
                            'lat_lims': np.array([-66., -65.5]),
                            'long_lims': np.array([-180., -179.4]),
                            'region_type': 'R'}]
        simple_polygons = self.reader.define_kreemer_regionalisation()
        for iloc, polygon in enumerate(simple_polygons):
            for key in polygon.keys():
                if key in ['lat_lims', 'long_lims']:
                    self.assertListEqual(polygon[key].tolist(),
                                         expected_output[iloc][key].tolist())
                else:
                    self.assertEqual(polygon[key], expected_output[iloc][key])

    def test_full_regionalisation_workflow(self):
        # Tests the function to apply the full Kreemer regionalisation workflow
        # using a simple 2 polygon case
        self.reader = KreemerRegionalisation(KREEMER_2REG_FILE)
        self.model = GeodeticStrain()
        self.model.data = {'longitude': np.array([179.7, -179.7, 10.0]),
                           'latitude': np.array([-65.7, -65.7, 10.0]),
                           'exx': 1E-9 * np.ones(3),
                           'eyy': 1E-9 * np.ones(3),
                           'exy': 1E-9 * np.ones(3)}
        self.model = self.reader.get_regionalisation(self.model)
        np.testing.assert_array_equal(self.model.data['region'],
                                      np.array([b'R', b'C', b'IPL']))
        np.testing.assert_array_equal(self.model.data['area'],
                                      np.array([1., 5., np.nan]))
