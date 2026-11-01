import json

import h5py
import numpy
import pytest
from scipy.stats import truncnorm

from openquake.baselib import config
from openquake.hazardlib import geo, imt, site
from openquake.hazardlib.correlation_models.spatial_cross_imt import (
    loth_baker_2013)
from openquake.hazardlib.shakemap.gmfs import (
    to_gmfs, _loth_baker_residuals)
from openquake.hazardlib.shakemap.maps import get_sitecol_shakemap
from openquake.hazardlib.shakemap.parsers import get_array
from openquake.hazardlib.shakemap.realization import psd_factor


def _raw_correlation(model, distances, im1, im2):
    # ShakeMap's station covariance uses raw coefficients, including its
    # non-unit diagonal at some interpolated periods.
    b1, b2, b3 = (b[0, 1] for b in model.raw_coregionalization([im1, im2]))
    return (b1 * numpy.exp(-3 * distances / 20) +
            b2 * numpy.exp(-3 * distances / 70) + b3 * (distances == 0))


def _product(path, conditioned=True, sa_period=.3):
    # Write the actual upstream HDF layout, with two station IMTs and one
    # uncertain observation. Expected covariances use the Schur complement.
    model = loth_baker_2013.ShakeMapLothBaker2013()
    imts = [imt.PGA(), imt.SA(sa_period)]
    lons = numpy.array([-.01, .01, -.01, .01])
    lats = numpy.array([.01, .01, -.01, -.01])
    slons, slats = numpy.array([0., .01]), numpy.array([0., -.01])
    sphi, extra = numpy.array([.6, .7]), numpy.array([.15, 0.])
    dd = geo.geodetic.distance_matrix(slons, slats)
    yd = geo.geodetic.geodetic_distance(
        lons[:, None], lats[:, None], slons, slats)
    R_DD = numpy.array([[_raw_correlation(
        model, dd[i:i+1, j:j+1], im1, im2)[0, 0]
        for j, im2 in enumerate(imts)] for i, im1 in enumerate(imts)])
    W_DD = sphi[:, None] * R_DD * sphi + numpy.diag(extra ** 2)
    expected = {}
    config = {'extent': {'bounds': {'extent': [-.01, -.01, .01, .01]}},
              'interp': {'prediction_location': {'xres': .02, 'yres': .02}},
              'modeling': {'ccf': 'LB13'}}
    with h5py.File(path, 'w') as h5:
        h5['dictionaries/config'] = json.dumps(config)
        h5['arrays/vs30'] = numpy.full((2, 2), 400.)
        h5['arrays/imt_periods'] = [.01, sa_period]
        for i, im in enumerate(imts):
            phi = numpy.full(4, .6 + .1 * i)
            W_YY = model.correlation_block(
                geo.geodetic.distance_matrix(lons, lats), [im])
            W_YY *= phi[:, None] * phi
            R_YD = numpy.column_stack([_raw_correlation(
                model, yd[:, j:j+1], im, sim)[:, 0]
                for j, sim in enumerate(imts)])
            W_YD = phi[:, None] * R_YD * sphi
            if conditioned:
                W_YY -= W_YD @ numpy.linalg.solve(W_DD, W_YD.T)
                numpy.fill_diagonal(W_YY, numpy.maximum(numpy.diag(W_YY), 0))
                C = numpy.array([[.1, .05], [.2, -.1], [.05, .1], [0, 0]])
                sigma = numpy.array([[.4, .1], [.1, .3]])
                between = C @ sigma @ C.T
            else:
                C, sigma = numpy.array([]), numpy.array([])
                between = numpy.full((4, 4), .04)
            expected[str(im)] = W_YY + between
            group = h5.require_group(
                f'arrays/imts/GREATER_OF_TWO_HORIZONTAL/{im}')
            group['mean'] = numpy.full((2, 2), numpy.log(.1))
            group['phi'] = phi.reshape(2, 2)
            group['tau'] = numpy.sqrt(numpy.diag(between)).reshape(2, 2)
            group['std'] = numpy.sqrt(numpy.maximum(
                numpy.diag(expected[str(im)]), 0)).reshape(2, 2)
            group['C'], group['Sigma_HH_YD'] = C, sigma
            for name, values in (
                    ('sta_lons_rad', numpy.radians(slons)),
                    ('sta_lats_rad', numpy.radians(slats)),
                    ('sta_per_ix', numpy.array([0, 1])),
                    ('sta_phi', sphi), ('add_uncertainty', extra)):
                group[name] = values.reshape(1, -1) if conditioned else []
    return expected


def _gmfs(shakemap, names, model=True, truncation=99, count=100_000):
    # Exercise the public dispatcher, including generation of tau samples.
    method = {'kind': 'Silva&Horspool',
              'spatial_model': loth_baker_2013.LothBaker2013()
              if model else None,
              'cross_imt_model': None, 'cholesky_limit': 10000}
    return to_gmfs(shakemap, method, None, truncation, count, 42, names)[1]


@pytest.mark.parametrize('conditioned', [True, False])
def test_hdf_posterior_spatial_covariance(tmp_path, conditioned):
    path = tmp_path / 'shake_result.hdf'
    expected = _product(path, conditioned)
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    assert 'K' in shakemap.dtype.names
    names = list(expected)
    gmfs = _gmfs(shakemap, names)
    for i, name in enumerate(names):
        numpy.testing.assert_allclose(
            numpy.cov(numpy.log(gmfs[:, :, i])), expected[name], atol=.006)
    if not conditioned:
        model = loth_baker_2013.ShakeMapLothBaker2013()
        distances = geo.geodetic.distance_matrix(
            shakemap['lon'], shakemap['lat'])
        cross = .6 * .7 * model.correlation_block(
            distances, [imt.PGA()], [imt.SA(.3)])
        residuals = numpy.log(gmfs).transpose(2, 0, 1).reshape(8, -1)
        numpy.testing.assert_allclose(
            numpy.cov(residuals)[:4, 4:], cross, atol=.006)
    # The conditional means remain the supplied ShakeMap means.
    numpy.testing.assert_allclose(
        numpy.log(gmfs).mean(axis=1), numpy.log(.1), atol=.008)
    median = _gmfs(shakemap, names, truncation=0, count=3)
    numpy.testing.assert_allclose(median, .1)


def test_conditioning_survives_npy_filtering_and_association(tmp_path):
    path = tmp_path / 'shake_result.hdf'
    expected = _product(path)
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    cached = tmp_path / 'shake.npy'
    numpy.save(cached, shakemap)
    indices = [0, 3, 0]
    sites = site.SiteCollection.from_points(
        shakemap['lon'][indices] + numpy.array([.00001, .00002, .00003]),
        shakemap['lat'][indices])
    _, selected, _, names = get_sitecol_shakemap(
        {'kind': 'file_npy', 'fname': str(cached)}, ['SA(0.3)'], sites)
    assert selected['K'].dtype.names == ('SA(0.3)',)
    numpy.testing.assert_array_equal(
        selected['K']['SA(0.3)'], shakemap['K']['SA(0.3)'][indices])
    gmfs = _gmfs(selected, names)
    numpy.testing.assert_array_equal(gmfs[0], gmfs[2])
    numpy.testing.assert_allclose(
        numpy.cov(numpy.log(gmfs[:, :, 0])),
        expected['SA(0.3)'][numpy.ix_(indices, indices)], atol=.006)


def test_disabled_correlation_uses_total_sigma(tmp_path):
    path = tmp_path / 'shake_result.hdf'
    _product(path)
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    # Exercise a component with both within- and between-event uncertainty.
    gmfs = _gmfs(shakemap, ['PGA'], model=False)
    covariance = numpy.cov(numpy.log(gmfs[:, :, 0]))
    numpy.testing.assert_allclose(covariance, numpy.diag(
        shakemap['std']['PGA'] ** 2), atol=.006)


def test_conditioned_covariance_at_finite_truncation(tmp_path):
    path = tmp_path / 'shake_result.hdf'
    expected = _product(path)
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    gmfs = _gmfs(shakemap, ['PGA'], truncation=3)
    numpy.testing.assert_allclose(
        numpy.cov(numpy.log(gmfs[:, :, 0])),
        expected['PGA'] * truncnorm.var(-3, 3), atol=.006)


def test_noiseless_station_with_rounded_correlation(tmp_path):
    path = tmp_path / 'shake_result.hdf'
    expected = _product(path, sa_period=1.)
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    gmfs = _gmfs(shakemap, ['SA(1.0)'])
    numpy.testing.assert_allclose(gmfs[3], .1)
    numpy.testing.assert_allclose(numpy.cov(numpy.log(gmfs[:, :, 0])),
                                  expected['SA(1.0)'], atol=.006)


def test_station_conditioning_memory_budget(tmp_path, monkeypatch):
    path = tmp_path / 'shake_result.hdf'
    _product(path)
    monkeypatch.setitem(config.memory, 'correlated_gmf_gb', 1E-9)
    with pytest.raises(ValueError, match='conditioning exceeds'):
        get_array(kind='shake_result_hdf', fname=str(path))


def test_duplicate_noiseless_stations(tmp_path):
    path = tmp_path / 'shake_result.hdf'
    expected = _product(path)
    with h5py.File(path, 'r+') as h5:
        for group in h5['arrays/imts/GREATER_OF_TWO_HORIZONTAL'].values():
            for name in ('sta_lons_rad', 'sta_lats_rad', 'sta_per_ix',
                         'sta_phi', 'add_uncertainty'):
                values = group[name][()].reshape(-1)
                del group[name]
                group[name] = numpy.append(values, values[-1])
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    gmfs = _gmfs(shakemap, ['PGA'])
    numpy.testing.assert_allclose(numpy.cov(numpy.log(gmfs[:, :, 0])),
                                  expected['PGA'], atol=.006)


def test_unsupported_conditioning_model_fails_clearly(tmp_path):
    path = tmp_path / 'shake_result.hdf'
    _product(path)
    with h5py.File(path, 'r+') as h5:
        config = json.loads(h5['dictionaries/config'][()])
        config['modeling']['ccf'] = 'UnknownModel'
        del h5['dictionaries/config']
        h5['dictionaries/config'] = json.dumps(config)
    with pytest.raises(ValueError, match='Unsupported.*conditioning model'):
        get_array(kind='shake_result_hdf', fname=str(path))


def test_incomplete_station_arrays_warn(tmp_path, caplog):
    path = tmp_path / 'shake_result.hdf'
    _product(path)
    with h5py.File(path, 'r+') as h5:
        del h5['arrays/imts/GREATER_OF_TWO_HORIZONTAL/PGA/sta_phi']
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    assert 'K' not in shakemap.dtype.names
    _gmfs(shakemap, ['PGA'], count=2)
    assert 'approximation without conditioning' in caplog.text


def test_interpolated_periods_preserve_correlation_and_unit_variance():
    imts = [imt.SA(p) for p in numpy.linspace(.01, 10, 25)]
    samples = numpy.random.default_rng(42).standard_normal((25, 150_000))
    residuals = _loth_baker_residuals(
        numpy.zeros(1), numpy.zeros(1), imts, samples, 42, 99)
    expected = loth_baker_2013.ShakeMapLothBaker2013().correlation_block(
        numpy.zeros((1, 1)), imts)
    numpy.testing.assert_allclose(
        numpy.cov(residuals[:, 0]), expected, atol=.012)


def test_indefinite_covariance_is_not_silently_clipped():
    with pytest.raises(ValueError, match='not positive semidefinite'):
        psd_factor(numpy.array([[1., 2.], [2., 1.]]))
