

import numpy.testing as npt
import unittest

from openquake.hazardlib.gsim.mgmpe.dummy import Dummy


class DummyTestCase(unittest.TestCase):

    def test_get_sitecollection_a(self):
        """ Simple case """
        sc = Dummy.get_site_collection(2)
        self.assertEqual(len(sc.lons), 2)

    def test_get_sitecollection_b(self):
        """ Assigning Vs30 """
        sc = Dummy.get_site_collection(3, vs30=760)
        npt.assert_almost_equal(sc.vs30, [760, 760, 760])
