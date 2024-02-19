import os.path
import unittest
import numpy
from openquake.hazardlib import geo, imt
from openquake.hazardlib.shakemap.maps import \
    get_sitecol_shakemap
from openquake.hazardlib.shakemap.gmfs import (
    to_gmfs, amplify_ground_shaking,
    spatial_correlation_array, spatial_covariance_array,
    cross_correlation_matrix, cholesky)

aae = numpy.testing.assert_almost_equal
F64 = numpy.float64
imts = [imt.from_string(x)
        for x in ['PGA', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)']]
imt_dt = numpy.dtype([(str(imt), float) for imt in imts])
shakemap_dt = numpy.dtype([('lon', float), ('lat', float), ('val', imt_dt),
                           ('std', imt_dt), ('vs30', float)])
CDIR = os.path.dirname(__file__)

gmf_dict = {'kind': 'Silva&Horspool',
            'spatialcorr': 'yes',
            'crosscorr': 'yes',
            'cholesky_limit': 10000}


def mean_std(shakemap, vs30):
    gmf_dict.update({'kind': 'Silva&Horspool',
                     'spatialcorr': 'yes', 'crosscorr': 'yes'})
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
        aae(gmf_by_imt, [[0.0062040, 0.0262588, 0.0497097, 0.0239060],
                         [0.0069831, 0.0298023, 0.0602146, 0.0294691],
                         [0.0069507, 0.0296108, 0.0594237, 0.0286251],
                         [0.0080306, 0.0341960, 0.0762080, 0.0379360]])

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
        aae(dmatrix.sum(), 18539.6131407)

        # spatial correlation
        sca = spatial_correlation_array(dmatrix, imts, 'yes')
        aae(sca.sum(), 36.000370229)

        # spatial covariance
        std = numpy.array([(0.5, 0.52, 0.64, 0.73)] * 9, imt_dt)  # 9 sites
        scov = spatial_covariance_array([std[n] for n in imt_dt.names], sca)
        aae(scov.sum(), 13.166200147)

        # cross correlation
        ccor = cross_correlation_matrix(imts, 'yes')
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
                         'spatialcorr': 'yes', 'crosscorr': 'no'})
        _, gmfs = to_gmfs(
            shakemap, gmf_dict, vs30=None, truncation_level=3,
            num_gmfs=2, seed=42)
        # shape (N, E, M)
        aae(gmfs[..., 0].sum(axis=0), [0.4202056, 0.6426098])  # PGA

        gmf_dict.update({'kind': 'Silva&Horspool',
                         'spatialcorr': 'yes', 'crosscorr': 'yes'})
        _, gmfs = to_gmfs(
            shakemap, gmf_dict, vs30=shakemap['vs30'], truncation_level=3,
            num_gmfs=2, seed=42)
        aae(gmfs[..., 0].sum(axis=0), [0.5809818, 0.8790579])  # PGA
        aae(gmfs[..., 2].sum(axis=0), [0.6053580, 0.8245417])  # SA(1.0)

        # disable spatial correlation
        gmf_dict.update({'kind': 'Silva&Horspool',
                         'spatialcorr': 'no', 'crosscorr': 'no'})
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
                         'spatialcorr': 'no', 'crosscorr': 'yes'})
        _, gmfs = to_gmfs(
            shakemap, gmf_dict, vs30=shakemap['vs30'],
            truncation_level=3, num_gmfs=2, seed=42)
        aae(gmfs[..., 0].sum(axis=0), [0.5809846, 0.8790549])  # PGA
        aae(gmfs[..., 2].sum(axis=0), [0.6053580, 0.8245417])  # SA(1.0)

        # set stddev to zero
        shakemap['std'] = 0
        with self.assertRaises(ValueError) as ctx:
            gmf_dict.update({'kind': 'Silva&Horspool',
                             'spatialcorr': 'no', 'crosscorr': 'yes'})
            to_gmfs(shakemap, gmf_dict, vs30=shakemap['vs30'],
                    truncation_level=3, num_gmfs=2, seed=42)
        self.assertIn('stddev==0 for IMT=PGA', str(ctx.exception))

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
        #                 PGA,       SA(0.3),   SA(1.0),   SA(3.0)
        aae(gmf_by_imt, [[0.1168263, 0.3056736, 0.0356231, 0.7957914],
                         [0.2422977, 0.6275377, 0.0369565, 0.8191154],
                         [0.3604619, 0.7492331, 0.0380028, 0.8229756],
                         [0.4631292, 1.1679310, 0.0369009, 0.8002559]])
        aae(std_by_imt, [[0.5922380, 0.6723980, 0.6325073, 0.6445988],
                         [0.6077153, 0.6661571, 0.6296381, 0.668559],
                         [0.6146356, 0.6748830, 0.6714424, 0.6613612],
                         [0.5815353, 0.6460007, 0.6491335, 0.6603457]])

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
            get_sitecol_shakemap(uridict, ['PGA', 'PSA03', 'PSA10'])
        self.assertIn("Missing ['PSA03', 'PSA10']", str(ctx.exception))
