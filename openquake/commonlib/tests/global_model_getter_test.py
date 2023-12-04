# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import unittest
import os
import numpy
from shapely import Point
from tempfile import mkstemp

from openquake.commonlib.global_model_getter import GlobalModelGetter


# A triangle intersecting ['AUT', 'CHE', 'DEU', 'FRA', 'ITA', 'LIE']
POLYGON_EXAMPLE = (
    'Polygon ((7.43382776637826836 49.91743762278053964,'
    ' 7.83778658614323476 44.7847843834139141,'
    ' 12.06747305191758102 48.08774179208040067,'
    ' 7.43382776637826836 49.91743762278053964))')


class GlobalModelGetterTestCase(unittest.TestCase):

    def test_spatial_index_storage_and_retrieval(self):
        sindex_path = mkstemp(prefix='sindex', suffix='.pickle')[1]
        sinfo_path = mkstemp(prefix='sinfo', suffix='.pickle')[1]
        # build and store index and data
        GlobalModelGetter(
            kind='global_risk',
            sindex_path=sindex_path,
            sinfo_path=sinfo_path,
            replace_sindex=True,
            replace_sinfo=True)
        # make sure that retrieveing index and data does not fail
        GlobalModelGetter(
            kind='global_risk',
            sindex_path=sindex_path,
            sinfo_path=sinfo_path,
            replace_sindex=False,
            replace_sinfo=False)
        # delete index and data
        os.remove(sindex_path)
        os.remove(sinfo_path)

    def test_spatial_index_in_memory(self):
        mg = GlobalModelGetter(kind='global_risk')
        # NOTE: the default predicate is 'intersects'
        self.assertEqual(
            mg.get_models_by_wkt(POLYGON_EXAMPLE),
            ['AUT', 'CHE', 'DEU', 'FRA', 'ITA', 'LIE'])
        self.assertEqual(
            mg.get_models_by_wkt(POLYGON_EXAMPLE, predicate='contains'),
            ['LIE'])
        self.assertEqual(
            mg.get_models_by_wkt('Point(6.733 62.361)'), ['NOR'])
        self.assertEqual(
            mg.get_models_by_wkt(mg.lonlat2wkt(6.733, 62.361)), ['NOR'])
        self.assertEqual(
            mg.get_nearest_model_by_lon_lat_sindex(9, 45), 'ITA')
        points = numpy.array([Point(9, 45), Point(6.733, 62.361)])
        self.assertEqual(
            mg.get_nearest_models_by_geoms_array(points),
            ['ITA', 'NOR'])
        self.assertEqual(
            mg.get_models_by_geoms_array(points),
            ['ITA', 'NOR'])
        numpy.testing.assert_array_equal(
            mg.get_nearest_models_by_geoms_array(
                points, return_indices_only=True),
            numpy.array([[0,  1], [99, 24]]))
        numpy.testing.assert_array_equal(
            mg.get_models_by_geoms_array(
                points, return_indices_only=True),
            numpy.array([[0,  1], [99, 24]]))
