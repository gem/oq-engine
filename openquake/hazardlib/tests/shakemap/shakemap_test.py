import os.path
import unittest
from unittest import mock
import numpy
from openquake.hazardlib import geo, imt, site
from openquake.hazardlib.correlation_models.cross_imt.baker_cornell_2006 import (
    BakerCornell2006)
from openquake.hazardlib.correlation_models.spatial_cross_imt.\
    loth_baker_2013 import LothBaker2013
from openquake.hazardlib.correlation_models.spatial.jayaram_baker_2009 import (
    JayaramBaker2009)
from openquake.hazardlib.shakemap.maps import \
    get_sitecol_shakemap
from openquake.hazardlib.shakemap.gmfs import (
    to_gmfs, amplify_ground_shaking,
    spatial_correlation_array, spatial_covariance_array,
    cross_correlation_matrix, cholesky, _correlate_residuals,
    _realization_residuals)

F64 = numpy.float64
imts = [imt.from_string(x)
        for x in ['PGA', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']]
imt_dt = numpy.dtype([(str(imt), float) for imt in imts])
shakemap_dt = numpy.dtype([('lon', float), ('lat', float), ('val', imt_dt),
                           ('std', imt_dt), ('vs30', float)])
CDIR = os.path.dirname(__file__)

spatial_model = JayaramBaker2009(vs30_clustering=True)
cross_imt_model = BakerCornell2006()
gmf_dict = {'kind': 'Silva&Horspool',
            'spatial_model': spatial_model,
            'cross_imt_model': cross_imt_model,
            'cholesky_limit': 10000}


def aae(x, y):
    numpy.testing.assert_almost_equal(x, y, decimal=4)


def mean_std(shakemap, vs30):
    gmf_dict.update({'kind': 'Silva&Horspool',
                     'spatial_model': spatial_model,
                     'cross_imt_model': cross_imt_model})
    _, gmfs = to_gmfs(
        shakemap, gmf_dict, vs30, truncation_level=3,
        num_gmfs=1000, seed=42, imts=['PGA', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)'])
    return gmfs.mean(axis=1), numpy.log(gmfs).std(axis=1)


class ShakemapTestCase(unittest.TestCase):

    def test_gmfs(self):
        # test uncertainty in zip
        f1 = os.path.join(CDIR, 'ghorka_grid.xml')
        f2 = os.path.join(CDIR, 'ghorka_uncertainty.zip')
        uridict = dict(kind='usgs_xml', grid_url=f1, uncertainty_url=f2)
        sitecol, shakemap, *_ = get_sitecol_shakemap(uridict, imt_dt.names)
        n = 4  # number of sites
        self.assertEqual(len(sitecol), n)
        gmf_by_imt, _ = mean_std(shakemap, shakemap['vs30'])
        aae(gmf_by_imt, [[0.006204, 0.0262588, 0.0497097, 0.023906],
                         [0.0069831, 0.0298023, 0.0602146, 0.0294691],
                         [0.0069507, 0.0296108, 0.0594237, 0.0286251],
                         [0.0080306, 0.034196, 0.0762079, 0.037936]])

    def test_circulant_embedding_strategy(self):
        lons = numpy.tile([0., 0.1, 0.2], 3)
        lats = numpy.repeat([0., 0.1, 0.2], 3)
        component_dt = numpy.dtype([
            ('lon', float), ('lat', float), ('val', imt_dt),
            ('std', imt_dt), ('phi', imt_dt), ('tau', imt_dt),
            ('vs30', float)])
        shakemap = numpy.zeros(9, component_dt)
        shakemap['lon'] = lons
        shakemap['lat'] = lats
        shakemap['val'] = (0.5, 0.6, 0.7, 0.8)
        shakemap['std'] = (0.5, 0.5, 0.5, 0.5)
        shakemap['phi'] = (0.4, 0.4, 0.4, 0.4)
        shakemap['tau'] = (0.3, 0.3, 0.3, 0.3)
        sites = site.SiteCollection.from_points(lons, lats)
        for correlation_strategy in (
                'cholesky_decomposition', 'circulant_embedding'):
            method = {
                'kind': 'Silva&Horspool',
                'spatial_model': spatial_model,
                'cross_imt_model': None,
                'cholesky_limit': 10000,
                'correlation_strategy': correlation_strategy,
                'sites': sites}
            _, gmfs = to_gmfs(
                shakemap, method, vs30=None, truncation_level=3,
                num_gmfs=8, seed=42, imts=['PGA', 'SA(0.3)'])
            self.assertEqual(gmfs.shape, (9, 8, 2))
            self.assertTrue(numpy.isfinite(gmfs).all())

    def test_zero_shakemap_uncertainty_skips_correlation(self):
        lons = numpy.tile([0., 0.1], 2)
        lats = numpy.repeat([0., 0.1], 2)
        shakemap = numpy.zeros(4, shakemap_dt)
        shakemap['lon'] = lons
        shakemap['lat'] = lats
        shakemap['val'] = (10., 20., 30., 40.)
        sites = site.SiteCollection.from_points(lons, lats)
        expected = numpy.tile([0.1, 0.2], (4, 1))
        for correlation_strategy in (
                'cholesky_decomposition', 'circulant_embedding'):
            method = {
                'kind': 'Silva&Horspool',
                'spatial_model': spatial_model,
                'cross_imt_model': None,
                'cholesky_limit': 10000,
                'correlation_strategy': correlation_strategy,
                'sites': sites}
            _, gmfs = to_gmfs(
                shakemap, method, vs30=None, truncation_level=3,
                num_gmfs=2, seed=42, imts=['PGA', 'SA(0.3)'])
            numpy.testing.assert_allclose(gmfs[:, 0], expected)

    def test_strategies_reproduce_spatial_correlation(self):
        # both factorizations must reproduce the target correlation
        lon, lat = numpy.meshgrid(numpy.arange(5) * 0.1,
                                  numpy.arange(5) * 0.1)
        lons, lats = lon.ravel(), lat.ravel()
        sites = site.SiteCollection.from_points(lons, lats)
        model = JayaramBaker2009(vs30_clustering=False)
        dmatrix = geo.geodetic.distance_matrix(lons, lats)
        target = spatial_correlation_array(dmatrix, imts[:1], model)[0]
        Z = numpy.random.default_rng(1).standard_normal((len(lons), 20000))
        for correlation_strategy in (
                'cholesky_decomposition', 'circulant_embedding'):
            residuals = _correlate_residuals(
                Z, imts[:1], sites, model, None, correlation_strategy,
                None, 10000, 3, 0)
            empirical = numpy.corrcoef(residuals)
            numpy.testing.assert_allclose(empirical, target, atol=0.05)

    def test_loth_baker_no_uncertainty_is_deterministic(self):
        # with truncation_level=0 the stored between-event components
        # must not add any noise: every event is the ShakeMap median
        names = ['PGA', 'SA(0.3)']
        N = 4
        imt_dt = [(name, float) for name in names]
        dt = numpy.dtype([
            ('lon', float), ('lat', float), ('vs30', float),
            ('val', imt_dt), ('std', imt_dt), ('phi', imt_dt),
            ('tau', imt_dt), ('CL', [(name, float, (3,)) for name in names])])
        shakemap = numpy.zeros(N, dt)
        shakemap['lon'] = [0., 0.1, 0., 0.1]
        shakemap['lat'] = [0., 0., 0.1, 0.1]
        shakemap['vs30'] = 400.
        for name in names:
            shakemap['val'][name] = [10., 20., 30., 40.]
            shakemap['std'][name] = .5
            shakemap['phi'][name] = .4
            shakemap['tau'][name] = .3
            shakemap['CL'][name][:, 0] = .3
        gmf_dict = {'kind': 'Silva&Horspool',
                    'spatial_model': LothBaker2013(),
                    'cross_imt_model': None,
                    'cholesky_limit': 10000}
        _, gmfs = to_gmfs(shakemap, gmf_dict, vs30=None, truncation_level=0,
                          num_gmfs=3, seed=42, imts=names)
        numpy.testing.assert_allclose(gmfs[:, 0], gmfs[:, 1])
        numpy.testing.assert_allclose(gmfs[:, 0], gmfs[:, 2])
        numpy.testing.assert_allclose(
            gmfs[:, 0], numpy.tile([0.1, 0.2, 0.3, 0.4], (2, 1)).T)

    def test_realization_residuals_variance(self):
        # the residual variance of each point must be phi^2 + |CL|^2,
        # i.e. the total variance stored by ShakeMap
        pair = [imt.from_string('PGA'), imt.from_string('SA(0.3)')]
        rng = numpy.random.default_rng(4)
        N, E = 6, 100_000
        lons = rng.uniform(0, 0.5, N)
        lats = rng.uniform(0, 0.5, N)
        dt = numpy.dtype([
            ('lon', float), ('lat', float),
            ('phi', [(str(im), float) for im in pair]),
            ('CL', [(str(im), float, (3,)) for im in pair])])
        shakemap = numpy.zeros(N, dt)
        shakemap['lon'] = lons
        shakemap['lat'] = lats
        for im in pair:
            shakemap['phi'][str(im)] = rng.uniform(0.2, 0.5, N)
            shakemap['CL'][str(im)][:, :1] = rng.uniform(-0.1, 0.1, (N, 1))
        Z = rng.standard_normal((N * len(pair), E))
        # a large truncation level gives untruncated between-event terms
        res = _realization_residuals(shakemap, pair, Z, 0, 99)
        variance = numpy.var(res, axis=1)
        expected = numpy.concatenate([
            shakemap['phi'][str(im)] ** 2 +
            (shakemap['CL'][str(im)] ** 2).sum(axis=1) for im in pair])
        numpy.testing.assert_allclose(variance, expected, rtol=0.03)

    def test_realization_residuals_correlation(self):
        # without between-event terms the residuals have the Loth and
        # Baker (2013) correlation between points and IMTs, whatever phi;
        # PGV is correlated through its SA(1.0) proxy
        ims = [imt.from_string(im) for im in ('PGA', 'SA(0.3)', 'PGV')]
        proxies = [imt.from_string(im)
                   for im in ('PGA', 'SA(0.3)', 'SA(1.0)')]
        # points along a parallel at 0, 5, 15, 40 and 100 km
        lons = numpy.array([0, 5, 15, 40, 100]) / 111.195
        lats = numpy.zeros_like(lons)
        N, E = len(lons), 200_000
        rng = numpy.random.default_rng(42)
        dt = numpy.dtype([
            ('lon', float), ('lat', float),
            ('phi', [(str(im), float) for im in ims]),
            ('CL', [(str(im), float, (1,)) for im in ims])])
        shakemap = numpy.zeros(N, dt)
        shakemap['lon'] = lons
        shakemap['lat'] = lats
        for im in ims:
            shakemap['phi'][str(im)] = rng.uniform(0.2, 0.8, N)
        Z = rng.standard_normal((N * len(ims), E))
        res = _realization_residuals(shakemap, ims, Z, 0, 99)
        dist = geo.geodetic.distance_matrix(lons, lats)
        expected = LothBaker2013().correlation_block(dist, proxies)
        numpy.testing.assert_allclose(
            numpy.corrcoef(res), expected, atol=0.01)

    def test_realization_residuals_many_points(self):
        # 2500 points and 5 IMTs exceed the old limit M * N <= 10000;
        # the sites associated to the same point share its residuals
        ims = [imt.from_string(im) for im in (
            'PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)')]
        lon, lat = numpy.meshgrid(numpy.arange(50) * .02,
                                  numpy.arange(50) * .02)
        lons = numpy.concatenate([lon.ravel(), [0., .5]])
        lats = numpy.concatenate([lat.ravel(), [0., .5]])
        N, E = len(lons), 3
        dt = numpy.dtype([
            ('lon', float), ('lat', float),
            ('phi', [(str(im), float) for im in ims]),
            ('CL', [(str(im), float, (1,)) for im in ims])])
        shakemap = numpy.zeros(N, dt)
        shakemap['lon'] = lons
        shakemap['lat'] = lats
        for im in ims:
            shakemap['phi'][str(im)] = .5
        Z = numpy.random.default_rng(42).standard_normal((N * 5, E))
        res = _realization_residuals(shakemap, ims, Z, 0, 3).reshape(5, N, E)
        self.assertTrue(numpy.isfinite(res).all())
        aae(res[:, 0], res[:, N - 2])  # the point (0, 0)
        aae(res[:, 25 * 50 + 25], res[:, N - 1])  # the point (.5, .5)

    def test_realization_residuals_memory_budget(self):
        shakemap = numpy.zeros(4, [
            ('lon', float), ('lat', float), ('phi', [('PGA', float)]),
            ('CL', [('PGA', float, (1,))])])
        shakemap['lon'] = [0, .1, .2, .3]
        with mock.patch('openquake.hazardlib.shakemap.gmfs.'
                        '_correlation_budget', return_value=100):
            with self.assertRaisesRegex(ValueError, 'correlated_gmf_gb'):
                _realization_residuals(
                    shakemap, [imt.from_string('PGA')],
                    numpy.zeros((4, 2)), 0, 3)

    def test_amplify(self):
        gmvs = numpy.array([0.1, 0.2, 0.3])
        res = amplify_ground_shaking(T=3.0, vs30=780, gmvs=gmvs)
        aae(res, [0.09832577, 0.19690711, 0.2958982])

        res = amplify_ground_shaking(T=0.3, vs30=780, gmvs=gmvs)
        aae(res, [0.09909498, 0.19870543, 0.29922175])

    def test_matrices(self):
        # distance matrix
        lons = numpy.array([84., 84., 84., 85.5, 85.5, 85.5, 87., 87., 87.])
        lats = numpy.array([26., 27.5, 29., 26., 27.5, 29., 26., 27.5, 29.])
        dmatrix = geo.geodetic.distance_matrix(lons, lats)
        aae(dmatrix.sum(), 18539.605)

        # spatial correlation
        sca = spatial_correlation_array(dmatrix, imts, spatial_model)
        aae(sca.sum(), 36.000370229)

        # spatial covariance
        std = numpy.array([(0.5, 0.52, 0.64, 0.73)] * 9, imt_dt)  # 9 sites
        scov = spatial_covariance_array([std[n] for n in imt_dt.names], sca)
        aae(scov.sum(), 13.166200147)

        # cross correlation
        ccor = cross_correlation_matrix(imts, cross_imt_model)
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
        gmf_dict.update({'kind': 'Silva&Horspool',
                         'spatial_model': spatial_model,
                         'cross_imt_model': None})
        self._check(shakemap, gmf_dict)

    def test_identity_matrices_without_models(self):
        distances = numpy.zeros((2, 2))
        numpy.testing.assert_array_equal(
            spatial_correlation_array(distances, imts, None),
            numpy.repeat(numpy.eye(2)[None], len(imts), axis=0))
        numpy.testing.assert_array_equal(
            cross_correlation_matrix(imts, None), numpy.eye(len(imts)))

    def test_no_uncertainty_preserves_shakemap(self):
        value_dt = numpy.dtype([('PGA', float), ('PGV', float)])
        dtype = numpy.dtype([
            ('lon', float), ('lat', float), ('val', value_dt),
            ('std', value_dt), ('vs30', float),
        ])
        shakemap = numpy.zeros(2, dtype)
        shakemap['val'] = [
            (10., 20.),
            (15., 25.),
        ]
        shakemap['std'] = [
            (.6, .7),
            (.6, .7),
        ]

        expected = numpy.array([
            [.10, 20.],
            [.15, 25.],
        ])
        methods = [
            {'kind': 'basic'},
            {'kind': 'Silva&Horspool', 'spatial_model': None,
             'cross_imt_model': None, 'cholesky_limit': 10000},
        ]
        for method in methods:
            for truncation_level in (0, 1E-9):
                _, gmfs = to_gmfs(
                    shakemap, method.copy(), vs30=None,
                    truncation_level=truncation_level,
                    num_gmfs=1, seed=42)
                numpy.testing.assert_array_equal(gmfs[:, 0], expected)

    def _check(self, shakemap, gmf_dict):
        _, gmfs = to_gmfs(
            shakemap, gmf_dict, vs30=None, truncation_level=3,
            num_gmfs=2, seed=42)
        # shape (N, E, M)
        aae(gmfs[..., 0].sum(axis=0), [0.4202056, 0.6426098])  # PGA

        gmf_dict.update({'kind': 'Silva&Horspool',
                         'spatial_model': spatial_model,
                         'cross_imt_model': cross_imt_model})
        _, gmfs = to_gmfs(
            shakemap, gmf_dict, vs30=shakemap['vs30'], truncation_level=3,
            num_gmfs=2, seed=42)
        aae(gmfs[..., 0].sum(axis=0), [0.5809818, 0.8790579])  # PGA
        aae(gmfs[..., 2].sum(axis=0), [0.605358, 0.8245417])  # SA(1.0)

        # disable spatial correlation
        gmf_dict.update({'kind': 'Silva&Horspool',
                         'spatial_model': None,
                         'cross_imt_model': None})
        _, gmfs = to_gmfs(
            shakemap, gmf_dict, vs30=None,
            truncation_level=3, num_gmfs=2, seed=42)
        # shape (N, E, M)
        aae(gmfs[..., 0].sum(axis=0), [0.4202077, 0.6426078])  # PGA

        _, gmfs = to_gmfs(
            shakemap, {'kind': 'basic'}, vs30=None,
            truncation_level=3, num_gmfs=2, seed=42)
        # shape (N, E, M)
        aae(gmfs[..., 0].sum(axis=0), [0.4202077, 0.6426078])  # PGA

        gmf_dict.update({'kind': 'Silva&Horspool',
                         'spatial_model': None,
                         'cross_imt_model': cross_imt_model})
        _, gmfs = to_gmfs(
            shakemap, gmf_dict, vs30=shakemap['vs30'],
            truncation_level=3, num_gmfs=2, seed=42)
        aae(gmfs[..., 0].sum(axis=0), [0.5809846, 0.8790549])  # PGA
        aae(gmfs[..., 2].sum(axis=0), [0.605358, 0.8245417])  # SA(1.0)

        # Zero standard deviations produce deterministic ShakeMap GMFs.
        shakemap['std'] = 0
        gmf_dict.update({'kind': 'Silva&Horspool',
                         'spatial_model': None,
                         'cross_imt_model': cross_imt_model})
        _, gmfs = to_gmfs(
            shakemap, gmf_dict, vs30=shakemap['vs30'],
            truncation_level=3, num_gmfs=2, seed=42)
        numpy.testing.assert_array_equal(gmfs[:, 0], gmfs[:, 1])

    def test_from_files(self):
        # files provided by Vitor Silva, without site amplification
        # test grid in zip
        f1 = os.path.join(CDIR, 'test_shaking.zip')
        f2 = os.path.join(CDIR, 'test_uncertainty.xml')
        uridict = dict(kind='usgs_xml', grid_url=f1, uncertainty_url=f2)
        sitecol, shakemap, *_ = get_sitecol_shakemap(uridict, imt_dt.names)
        n = 4  # number of sites
        self.assertEqual(len(sitecol), n)
        gmf_by_imt, std_by_imt = mean_std(shakemap, vs30=None)
        #                PGA,    SA(0.3), SA(1.0), SA(3.0)
        aae(gmf_by_imt, [[0.1168, 0.3057, 0.0356, 0.7958],
                         [0.2423, 0.6275, 0.037, 0.8191],
                         [0.3605, 0.7492, 0.038, 0.823],
                         [0.4631, 1.1679, 0.0369, 0.8003]])
        aae(std_by_imt, [[0.5922, 0.6724, 0.6325, 0.6446],
                         [0.6077, 0.6662, 0.6296, 0.6686],
                         [0.6146, 0.6749, 0.6714, 0.6614],
                         [0.5815, 0.646, 0.6491, 0.6603]])
        # NB: the spatial correlation matrix is highly degenerate
        # with 3 of 4 eigenvalues equal to zero, the numbers above are
        # not trustworthy

    def test_for_mmi(self):
        # test both files in one zip
        f1 = os.path.join(CDIR, 'ghorka_grid.zip')
        uridict = dict(kind='usgs_xml', grid_url=f1, uncertainty_url=None)

        sitecol, shakemap, *_ = get_sitecol_shakemap(uridict, ['MMI'])
        n = 4  # number of sites
        self.assertEqual(len(sitecol), n)

        _, gmfs = to_gmfs(shakemap, {'kind': 'mmi'}, None,
                          truncation_level=3, num_gmfs=1000, seed=42,
                          imts=['MMI'])

        gmf_by_imt = gmfs.mean(axis=1)
        std_by_imt = gmfs.std(axis=1)
        aae(gmf_by_imt, [[3.80704848],
                         [3.89791949],
                         [3.88040454],
                         [3.93584243]])
        aae(std_by_imt, [[0.71068558],
                         [0.72233552],
                         [0.72033749],
                         [0.69906908]])

    def test_missing_imts(self):
        f = os.path.join(CDIR, 'invalid_grid.xml')
        uridict = dict(kind='usgs_xml', grid_url=f, uncertainty_url=None)
        with self.assertRaises(RuntimeError) as ctx:
            get_sitecol_shakemap(uridict, ['PGA', 'SA(0.6)', 'SA(1.0)'])
        self.assertIn("The imts {'SA(0.6)'} are required", str(ctx.exception))
