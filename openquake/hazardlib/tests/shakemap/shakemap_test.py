import os.path
import unittest
import numpy
from openquake.hazardlib import geo, imt
from openquake.hazardlib.shakemap import (
    get_shakemap_array, get_sitecol_shakemap, to_gmfs, amplify_ground_shaking,
    spatial_correlation_array, spatial_covariance_array,
    cross_correlation_matrix, cholesky)

aae = numpy.testing.assert_almost_equal
F64 = numpy.float64
imts = [imt.from_string(x) for x in ['PGA', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']]
imt_dt = numpy.dtype([(str(imt), float) for imt in imts])
shakemap_dt = numpy.dtype([('lon', float), ('lat', float), ('val', imt_dt),
                           ('std', imt_dt), ('vs30', float)])
CDIR = os.path.dirname(__file__)


def mean_gmf(shakemap):
    gmfs = to_gmfs(
        shakemap, crosscorr='cross', site_effects=True, trunclevel=3,
        num_gmfs=10, seed=42)
    return [gmfs[..., i].mean() for i in range(len(imts))]


class ShakemapTestCase(unittest.TestCase):

    def test_gmfs(self):
        f1 = os.path.join(CDIR, 'ghorka_grid.xml')
        f2 = os.path.join(CDIR, 'ghorka_uncertainty.xml')
        array = get_shakemap_array(f1, f2)
        sitecol, shakemap = get_sitecol_shakemap(array)
        n = 4  # number of sites
        self.assertEqual(len(sitecol), n)
        gmf_by_imt = mean_gmf(shakemap)
        aae(gmf_by_imt, [0.0047045, 0.0184625, 0.0346171, 0.0175625])

    def test_amplify(self):
        res = amplify_ground_shaking(T=3.0, vs30=780, gmvs=[0.1, 0.2, 0.3])
        aae(res, [0.09832577, 0.19690711, 0.2958982])

        res = amplify_ground_shaking(T=0.3, vs30=780, gmvs=[0.1, 0.2, 0.3])
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
        scov = spatial_covariance_array([std[n] for n in imt_dt.names], sca)
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
            [(5.38409665, 3.9383686, 3.55435415, 4.37692394)] * 9, imt_dt)

        shakemap = numpy.zeros(9, shakemap_dt)  # 9 sites
        shakemap['lon'] = lons
        shakemap['lat'] = lats
        shakemap['vs30'] = numpy.array([301.17] * 9)
        shakemap['val'] = val
        shakemap['std'] = std
        gmfs = to_gmfs(
            shakemap, crosscorr='corr', site_effects=False, trunclevel=3,
            num_gmfs=2, seed=42)
        # shape (R, N, E, M)
        aae(gmfs[..., 0].sum(axis=1), [[0.3708301, 0.5671011]])  # PGA

        gmfs = to_gmfs(
            shakemap, crosscorr='cross', site_effects=True, trunclevel=3,
            num_gmfs=2, seed=42)
        aae(gmfs[..., 0].sum(axis=1), [[0.4101717, 0.6240185]])  # PGA
        aae(gmfs[..., 2].sum(axis=1), [[0.3946015, 0.5385107]])  # SA(1.0)
