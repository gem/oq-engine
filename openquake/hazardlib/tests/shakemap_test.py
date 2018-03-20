import unittest
import numpy
from openquake.baselib.general import writetmp
from openquake.hazardlib import geo
from openquake.hazardlib.shakemapconverter import example_pga, example_sa
from openquake.hazardlib.shakemap import (
    get_sitecol_shakemap, to_gmfs, amplify_ground_shaking,
    spatial_correlation_array, spatial_covariance_array,
    cross_correlation_matrix, cholesky)

aae = numpy.testing.assert_almost_equal
F32 = numpy.float32
imts = ['PGA', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']
imt_dt = numpy.dtype([(imt, float) for imt in imts])
shakemap_dt = numpy.dtype([('lon', float), ('lat', float), ('val', imt_dt),
                           ('std', imt_dt), ('vs30', float)])


def mean_gmf(shakemap):
    gmfs = to_gmfs(
        shakemap, site_effects=True, trunclevel=3, num_gmfs=10, seed=42)
    return gmfs.mean(axis=1)


class ShakemapTestCase(unittest.TestCase):

    def _test_pga(self):
        sitecol, shakemap = get_sitecol_shakemap(writetmp(example_pga))
        n = 3  # number of sites
        self.assertEqual(len(sitecol), n)
        gmf = mean_gmf(shakemap)
        aae(gmf, [1.0294671, 1.0483357, 0.6757492])

    def test_sa(self):
        f1 = writetmp(example_pga)
        f2 = writetmp(example_sa)
        array = get_shakemap_array(f1, f2)
        sitecol, shakemap = get_sitecol_shakemap(writetmp(example_sa))
        n = 4  # number of sites
        self.assertEqual(len(sitecol), n)
        gmf = mean_gmf(shakemap)
        aae(gmf, [])

    def _test_amplify(self):
        res = amplify_ground_shaking(T=3.0, vs30=780, imls=[0.1, 0.2, 0.3])
        aae(res, [0.09832577, 0.19690711, 0.2958982])

        res = amplify_ground_shaking(T=0.3, vs30=780, imls=[0.1, 0.2, 0.3])
        aae(res, [0.09909498, 0.19870543, 0.29922175])

    def test_matrices(self):

        # distance matrix
        lons = numpy.array([84., 84., 84., 85.5, 85.5, 85.5, 87., 87., 87.])
        lats = numpy.array([26., 27.5, 29., 26., 27.5, 29., 26., 27.5, 29.])
        dmatrix = geo.geodetic.distance_matrix(lons, lats)
        aae(dmatrix.sum(), 18539.6131407)

        # spatial correlation
        sca = spatial_correlation_array(dmatrix, imts, 'spatial')
        aae(sca.sum(), 36.000370229)

        # spatial covariance
        std = numpy.array([(0.5, 0.52, 0.64, 0.73)] * 9, imt_dt)  # 9 sites
        scov = spatial_covariance_array(std, imts, sca)
        aae(scov.sum(), 13.166200147)

        # cross correlation
        ccor = cross_correlation_matrix(imts, 'cross')
        aae(ccor.sum(), 10.49124788)

        # cholesky decomposition
        L = cholesky(scov, ccor)
        self.assertEqual(L.shape, (36, 36))
        aae(L.sum(), 30.5121263)

        # intensity
        val = numpy.array(
            [(-5.38409665, -3.9383686, -3.55435415, -4.37692394)] * 9, imt_dt)

        shakemap = numpy.zeros(9, shakemap_dt)
        shakemap['lon'] = lons
        shakemap['lat'] = lats
        shakemap['vs30'] = numpy.array([301.17] * 9)
        shakemap['val'] = val
        shakemap['std'] = std
        gmfs = to_gmfs(
            shakemap, site_effects=False, trunclevel=3, num_gmfs=2, seed=42)
        aae(gmfs.sum(axis=0), [0.5537324, 0.7915186])

        gmfs = to_gmfs(
            shakemap, site_effects=True, trunclevel=3, num_gmfs=2, seed=42)
        aae(gmfs.sum(axis=0), [0.7394071, 1.0639163])
