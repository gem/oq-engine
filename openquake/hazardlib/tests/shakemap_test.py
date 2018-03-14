import unittest
import numpy
from openquake.baselib.general import writetmp
from openquake.hazardlib.shakemapconverter import example_pga, example_sa
from openquake.hazardlib.shakemap import get_sitecol_shakemap, to_gmfs

aae = numpy.testing.assert_almost_equal
F32 = numpy.float32


def mean_gmf(shakemap):
    gmfs = to_gmfs(
        shakemap, site_effects=True, trunclevel=3, num_gmfs=10, seed=42)
    return gmfs.mean(axis=1)


class ShakemapTestCase(unittest.TestCase):

    def test_pga(self):
        sitecol, shakemap = get_sitecol_shakemap(writetmp(example_pga))
        n = 3  # number of sites
        self.assertEqual(len(sitecol), n)
        gmf = mean_gmf(shakemap)
        aae(gmf, [1.0294671, 1.0483357, 0.6757492])

    def _test_sa(self):
        sitecol, shakemap = get_sitecol_shakemap(writetmp(example_sa))
        n = 4  # number of sites
        self.assertEqual(len(sitecol), n)
        gmf = mean_gmf(shakemap)
        aae(gmf, [])
