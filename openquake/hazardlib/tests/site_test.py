# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import pickle
import unittest
import tempfile

import numpy

from openquake.baselib import hdf5
from openquake.hazardlib.site import \
    Site, SiteCollection, FilteredSiteCollection
from openquake.hazardlib.geo.point import Point

assert_eq = numpy.testing.assert_equal


class SiteModelParam(object):
    def __init__(self):
        self.reference_vs30_value = 1.2
        self.reference_vs30_type = 'measured'
        self.reference_depth_to_1pt0km_per_sec = 3.4
        self.reference_depth_to_2pt5km_per_sec = 5.6
        self.reference_backarc = False


class SiteTestCase(unittest.TestCase):
    def _assert_creation(self, error=None, **kwargs):
        default_kwargs = {
            'location': Point(10, 20),
            'vs30': 10,
            'vs30measured': False,
            'z1pt0': 20,
            'z2pt5': 30,
            'backarc': True
        }
        default_kwargs.update(kwargs)
        kwargs = default_kwargs
        if error is not None:
            with self.assertRaises(ValueError) as ar:
                Site(**kwargs)
            self.assertEqual(str(ar.exception), error)
        else:
            site = Site(**kwargs)
            for attr in kwargs:
                self.assertEqual(getattr(site, attr), kwargs[attr])

    def test_wrong_vs30(self):
        error = 'vs30 must be positive'
        self._assert_creation(error=error, vs30=0)
        self._assert_creation(error=error, vs30=-1)

    def test_wrong_z1pt0(self):
        error = 'z1pt0 must be positive'
        self._assert_creation(error=error, z1pt0=0)
        self._assert_creation(error=error, z1pt0=-1)

    def test_wrong_z2pt5(self):
        error = 'z2pt5 must be positive'
        self._assert_creation(error=error, z2pt5=0)
        self._assert_creation(error=error, z2pt5=-1)

    def test_successful_creation(self):
        self._assert_creation()


class SiteCollectionCreationTestCase(unittest.TestCase):
    def test_from_sites(self):
        s1 = Site(location=Point(10, 20, 30),
                  vs30=1.2, vs30measured=True,
                  z1pt0=3.4, z2pt5=5.6, backarc=True)
        s2 = Site(location=Point(-1.2, -3.4, -5.6),
                  vs30=55.4, vs30measured=False,
                  z1pt0=66.7, z2pt5=88.9, backarc=False)
        cll = SiteCollection([s1, s2])
        assert_eq(cll.vs30, [1.2, 55.4])
        assert_eq(cll.vs30measured, [True, False])
        assert_eq(cll.z1pt0, [3.4, 66.7])
        assert_eq(cll.z2pt5, [5.6, 88.9])
        assert_eq(cll.mesh.lons, [10, -1.2])
        assert_eq(cll.mesh.lats, [20, -3.4])
        assert_eq(cll.mesh.depths, [30, -5.6])
        assert_eq(cll.backarc, [True, False])
        for arr in (cll.vs30, cll.z1pt0, cll.z2pt5):
            self.assertIsInstance(arr, numpy.ndarray)
            self.assertEqual(arr.flags.writeable, False)
            self.assertEqual(arr.dtype, float)
        for arr in (cll.vs30measured, cll.backarc):
            self.assertIsInstance(arr, numpy.ndarray)
            self.assertEqual(arr.flags.writeable, False)
            self.assertEqual(arr.dtype, bool)
        self.assertEqual(len(cll), 2)

        # test serialization to hdf5
        fd, fpath = tempfile.mkstemp(suffix='.hdf5')
        os.close(fd)
        with hdf5.File(fpath, 'w') as f:
            f['folder'] = dict(sitecol=cll, b=[2, 3])
            newcll = f['folder/sitecol']
            self.assertEqual(newcll, cll)
            self.assertEqual(list(f['folder/b']), [2, 3])
        os.remove(fpath)

    def test_from_points(self):
        lons = [10, -1.2]
        lats = [20, -3.4]
        depths = [30, -5.6]
        cll = SiteCollection.from_points(
            lons, lats, depths, SiteModelParam())
        assert_eq(cll.vs30, [1.2, 1.2])
        assert_eq(cll.vs30measured, [True, True])
        assert_eq(cll.z1pt0, [3.4, 3.4])
        assert_eq(cll.z2pt5, [5.6, 5.6])
        assert_eq(cll.mesh.lons, [10, -1.2])
        assert_eq(cll.mesh.lats, [20, -3.4])
        assert_eq(cll.mesh.depths, [30, -5.6])
        assert_eq(cll.backarc, [False, False])

        for arr in (cll.vs30, cll.z1pt0, cll.z2pt5):
            self.assertIsInstance(arr, numpy.ndarray)
            self.assertEqual(arr.dtype, float)
        for arr in (cll.vs30measured, cll.backarc):
            self.assertIsInstance(arr, numpy.ndarray)
            self.assertEqual(arr.flags.writeable, False)
            self.assertEqual(arr.dtype, bool)
        self.assertEqual(len(cll), 2)

        # test split_in_tiles
        tiles = cll.split_in_tiles(0)
        self.assertEqual(len(tiles), 1)

        tiles = cll.split_in_tiles(1)
        self.assertEqual(len(tiles), 1)

        tiles = cll.split_in_tiles(2)
        self.assertEqual(len(tiles), 2)


class SiteCollectionFilterTestCase(unittest.TestCase):
    SITES = [
        Site(location=Point(10, 20, 30), vs30=1.2, vs30measured=True,
             z1pt0=3, z2pt5=5),
        Site(location=Point(11, 12, 13), vs30=55.4, vs30measured=False,
             z1pt0=6, z2pt5=8),
        Site(location=Point(0, 2, 0), vs30=2, vs30measured=True,
             z1pt0=9, z2pt5=17),
        Site(location=Point(1, 1, 3), vs30=4, vs30measured=False,
             z1pt0=22, z2pt5=11)
    ]

    def test_filter(self):
        col = SiteCollection(self.SITES)
        filtered = col.filter(numpy.array([True, False, True, False]))
        self.assertIsInstance(filtered, FilteredSiteCollection)
        arreq = numpy.testing.assert_array_equal
        arreq(filtered.vs30, [1.2, 2])
        arreq(filtered.vs30measured, [True, True])
        arreq(filtered.z1pt0, [3, 9])
        arreq(filtered.z2pt5, [5, 17])
        arreq(filtered.mesh.lons, [10, 0])
        arreq(filtered.mesh.lats, [20, 2])
        arreq(filtered.mesh.depths, [30, 0])
        arreq(filtered.sids, [0, 2])

        filtered = col.filter(numpy.array([False, True, True, True]))
        self.assertIsInstance(filtered, FilteredSiteCollection)
        arreq(filtered.vs30, [55.4, 2, 4])
        arreq(filtered.vs30measured, [False, True, False])
        arreq(filtered.z1pt0, [6, 9, 22])
        arreq(filtered.z2pt5, [8, 17, 11])
        arreq(filtered.mesh.lons, [11, 0, 1])
        arreq(filtered.mesh.lats, [12, 2, 1])
        arreq(filtered.mesh.depths, [13, 0, 3])

        # test serialization to hdf5
        fd, fpath = tempfile.mkstemp(suffix='.hdf5')
        os.close(fd)
        with hdf5.File(fpath, 'w') as f:
            f['sitecol'] = filtered
            saved = f['sitecol']
            self.assertEqual(saved, filtered)
        os.remove(fpath)

    def test_filter_all_out(self):
        col = SiteCollection(self.SITES)
        filtered = col.filter(numpy.zeros(len(self.SITES), bool))
        self.assertIs(filtered, None)

    def test_filter_all_in(self):
        col = SiteCollection(self.SITES)
        filtered = col.filter(numpy.ones(len(self.SITES), bool))
        self.assertIs(filtered, col)

    def test_double_filter(self):
        col = SiteCollection(self.SITES)
        filtered = col.filter(numpy.array([True, False, True, True]))
        filtered2 = filtered.filter(numpy.array([False, True, False]))
        arreq = numpy.testing.assert_array_equal
        arreq(filtered2.vs30, [2])
        arreq(filtered2.vs30measured, [True])
        arreq(filtered2.z1pt0, [9])
        arreq(filtered2.z2pt5, [17])
        arreq(filtered2.mesh.lons, [0])
        arreq(filtered2.mesh.lats, [2])
        arreq(filtered2.mesh.depths, [0])
        arreq(filtered.indices, [0, 2, 3])
        arreq(filtered2.indices, [2])
        filtered2 = filtered.filter(numpy.array([True, False, True]))
        arreq(filtered2.indices, [0, 3])


class SiteCollectionIterTestCase(unittest.TestCase):

    def test(self):
        s1 = Site(location=Point(10, 20),
                  vs30=1.2, vs30measured=True,
                  z1pt0=3.4, z2pt5=5.6)
        s2 = Site(location=Point(-1.2, -3.4),
                  vs30=55.4, vs30measured=False,
                  z1pt0=66.7, z2pt5=88.9)
        cll = SiteCollection([s1, s2])

        cll_sites = list(cll)
        for i, s in enumerate([s1, s2]):
            self.assertEqual(s, cll_sites[i])

    def test_depths_go_to_zero(self):
        # Depth information is zero when a :class:`Site`
        # contains only (lon, lat)
        s1 = Site(location=Point(10, 20),
                  vs30=1.2, vs30measured=True,
                  z1pt0=3.4, z2pt5=5.6)
        s2 = Site(location=Point(-1.2, -3.4),
                  vs30=55.4, vs30measured=False,
                  z1pt0=66.7, z2pt5=88.9)
        cll = SiteCollection([s1, s2])

        cll_sites = list(cll)
        exp_s1 = Site(location=Point(10, 20, 0.0),
                      vs30=1.2, vs30measured=True,
                      z1pt0=3.4, z2pt5=5.6)
        exp_s2 = Site(location=Point(-1.2, -3.4, 0.0),
                      vs30=55.4, vs30measured=False,
                      z1pt0=66.7, z2pt5=88.9)

        for i, s in enumerate([exp_s1, exp_s2]):
            self.assertEqual(s, cll_sites[i])

        # test equality of site collections
        sc = SiteCollection([exp_s1, exp_s2])
        self.assertEqual(cll, sc)

        # test nonequality of site collections
        # (see https://github.com/gem/oq-hazardlib/pull/403)
        sc._vs30 = numpy.array([numpy.nan, numpy.nan])
        self.assertNotEqual(cll, sc)


class SitePickleTestCase(unittest.TestCase):
    # Tests for pickling Sites.

    def test_dumps_and_loads(self):
        point = Point(1, 2, 3)
        site1 = Site(point, 760.0, True, 100.0, 5.0)
        site2 = pickle.loads(pickle.dumps(site1))
        self.assertEqual(site1, site2)
