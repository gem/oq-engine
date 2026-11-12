import json
import os

import h5py
import numpy
import pytest
from scipy.stats import truncnorm

from openquake.baselib import config
from openquake.hazardlib import geo, imt, site
from openquake.hazardlib.correlation_models.spatial_cross_imt import (
    loth_baker_2013)
from openquake.hazardlib.correlation_models.cross_imt.\
    abrahamson_et_al_2014 import AbrahamsonEtAl2014BetweenEvent
from openquake.hazardlib.correlation_models.cross_imt.\
    full_cross_correlation import FullCrossCorrelation
from openquake.hazardlib.correlation_models.cross_imt.\
    no_cross_correlation import NoCrossCorrelation
from openquake.hazardlib.shakemap.gmfs import (
    to_gmfs, _loth_baker_residuals, _between_residuals)
from openquake.hazardlib.shakemap.maps import get_sitecol_shakemap
from openquake.hazardlib.shakemap.parsers import (
    get_array, get_array_usgs_id, save_shakemap, ShakeMapProductError)
from openquake.hazardlib.shakemap import parsers
from openquake.hazardlib.shakemap.realization import (
    psd_factor, get_metadata, station_conditioning, conditioning_stations)

F32 = numpy.float32
DATA = os.path.join(os.path.dirname(__file__), 'data')


def _raw_correlation(model, distances, im1, im2):
    # ShakeMap's station covariance uses raw coefficients, including its
    # non-unit diagonal at some interpolated periods.
    b1, b2, b3 = (b[0, 1] for b in model.raw_coregionalization([im1, im2]))
    return (b1 * numpy.exp(-3 * distances / 20) +
            b2 * numpy.exp(-3 * distances / 70) + b3 * (distances == 0))


def _product(path, conditioned=True, sa_period=.3):
    # Write the actual upstream HDF layout, with two station IMTs and one
    # uncertain observation. Expected covariances use the Schur complement.
    # As in the real products periods, sigmas and the between-event arrays
    # are float32; the station coordinates are kept in double precision so
    # that a station can coincide with a grid point.
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
        h5['arrays/imt_periods'] = numpy.array([.01, sa_period], F32)
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
            group['phi'] = phi.reshape(2, 2).astype(F32)
            group['tau'] = numpy.sqrt(
                numpy.diag(between)).reshape(2, 2).astype(F32)
            group['std'] = numpy.sqrt(numpy.maximum(
                numpy.diag(expected[str(im)]), 0)).reshape(2, 2).astype(F32)
            group['C'] = C.astype(F32)
            group['Sigma_HH_YD'] = sigma.astype(F32)
            for name, values in (
                    ('sta_lons_rad', numpy.radians(slons)),
                    ('sta_lats_rad', numpy.radians(slats)),
                    ('sta_per_ix', numpy.array([0, 1])),
                    ('sta_phi', sphi.astype(F32)),
                    ('add_uncertainty', extra.astype(F32))):
                group[name] = values.reshape(1, -1) if conditioned else []
    return expected


def _gmfs(shakemap, names, model=True, truncation=99, count=100_000,
          between_event_model=None):
    # Exercise the public dispatcher, including generation of tau samples.
    method = {'kind': 'Silva&Horspool',
              'spatial_model': loth_baker_2013.LothBaker2013()
              if model else None,
              'cross_imt_model': None, 'cholesky_limit': 10000,
              'between_event_model': between_event_model}
    return to_gmfs(shakemap, method, None, truncation, count, 42, names)[1]


@pytest.mark.parametrize('conditioned', [True, False])
def test_hdf_posterior_spatial_covariance(tmp_path, conditioned):
    path = tmp_path / 'shake_result.hdf'
    expected = _product(path, conditioned)
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    stations = get_metadata(shakemap, 'stations')
    assert len(stations) == (4 if conditioned else 0)  # 2 per IMT
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


@pytest.mark.parametrize('conditioned', [True, False])
def test_hdf_between_event_correlation(tmp_path, conditioned):
    # a between-event model correlates the event terms of the IMTs without
    # changing the posterior of each IMT; without stations the stored
    # between-event factors have rank one and get the model correlation
    path = tmp_path / 'shake_result.hdf'
    expected = _product(path, conditioned)
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    imts = [imt.PGA(), imt.SA(.3)]
    model = AbrahamsonEtAl2014BetweenEvent()
    rho = model.correlation_matrix(imts)[0, 1]
    assert rho > .5
    independent = _between_residuals(shakemap, imts, 100_000, 42, 99, None)
    correlated = _between_residuals(shakemap, imts, 100_000, 42, 99, model)
    for indep, corr in zip(independent, correlated):
        numpy.testing.assert_allclose(
            numpy.cov(corr), numpy.cov(indep), atol=.003)
    tau = [numpy.sqrt((shakemap['CL'][str(im)].astype(float) ** 2).sum(
        axis=1)) for im in imts]
    cross = numpy.cov(numpy.vstack(correlated))[:4, 4:]
    if conditioned:  # up to the model correlation, with the same sign
        bound = rho * tau[0] * tau[1]  # the last point has no tau
        assert (numpy.diag(cross)[:3] > .1 * bound[:3]).all()
        assert (numpy.diag(cross) < bound + .003).all()
    else:
        numpy.testing.assert_allclose(cross, rho * .04, atol=.003)
        # through the public dispatcher, with the within-event correlation
        gmfs = _gmfs(shakemap, list(expected), between_event_model=model)
        residuals = numpy.log(gmfs).transpose(2, 0, 1).reshape(8, -1)
        within = .6 * .7 * loth_baker_2013.ShakeMapLothBaker2013(
            ).correlation_block(geo.geodetic.distance_matrix(
                shakemap['lon'], shakemap['lat']), [imt.PGA()], [imt.SA(.3)])
        numpy.testing.assert_allclose(
            numpy.cov(residuals)[:4, 4:], within + rho * .04, atol=.006)
        for i, name in enumerate(expected):
            numpy.testing.assert_allclose(
                numpy.cov(numpy.log(gmfs[:, :, i])), expected[name],
                atol=.006)


def test_conditioning_survives_npy_filtering_and_association(tmp_path):
    path = tmp_path / 'shake_result.hdf'
    expected = _product(path)
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    cached = tmp_path / 'shake.npy'
    save_shakemap(cached, shakemap)
    indices = [0, 3, 0]
    sites = site.SiteCollection.from_points(
        shakemap['lon'][indices] + numpy.array([.00001, .00002, .00003]),
        shakemap['lat'][indices])
    _, selected, _, names = get_sitecol_shakemap(
        {'kind': 'file_npy', 'fname': str(cached)}, ['SA(0.3)'], sites)
    # only the stations of the selected IMT are kept
    stations = get_metadata(shakemap, 'stations')
    numpy.testing.assert_array_equal(
        get_metadata(selected, 'stations'),
        stations[stations['imt'] == b'SA(0.3)'])
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
    # reading does not depend on the budget, since the station correction
    # is computed only when sampling, for the sites of the calculation
    path = tmp_path / 'shake_result.hdf'
    _product(path)
    monkeypatch.setitem(config.memory, 'correlated_gmf_gb', 1E-9)
    shakemap = get_array(kind='shake_result_hdf', fname=str(path))
    with pytest.raises(ValueError, match='correlated_gmf_gb'):
        _gmfs(shakemap, ['PGA'], count=2)


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
    uri = {'kind': 'shake_result_hdf', 'fname': str(path)}
    shakemap = get_array(**uri)
    assert conditioning_stations(shakemap) is None
    _gmfs(shakemap, ['PGA'], count=2)
    assert 'approximation without conditioning' in caplog.text
    # the stations of the other IMTs are kept if PGA is not required
    _, shakemap, _, _ = get_sitecol_shakemap(uri, ['SA(0.3)'])
    assert len(conditioning_stations(shakemap)) == 2


def test_unused_imt_without_posterior_components(tmp_path, caplog):
    # an IMT without phi, tau and the between-event arrays (here an MMI
    # group with only mean and std) disables the posterior sampling only
    # if it is required
    path = tmp_path / 'shake_result.hdf'
    _product(path)
    with h5py.File(path, 'r+') as h5:
        group = h5.require_group('arrays/imts/GREATER_OF_TWO_HORIZONTAL/MMI')
        group['mean'] = numpy.full((2, 2), 5.)
        group['std'] = numpy.full((2, 2), .5, F32)
    uri = {'kind': 'shake_result_hdf', 'fname': str(path)}
    _, shakemap, _, _ = get_sitecol_shakemap(uri, ['PGA', 'SA(0.3)'])
    assert {'phi', 'tau', 'CL'} <= set(shakemap.dtype.names)
    assert len(get_metadata(shakemap, 'stations')) == 4
    _, shakemap, _, _ = get_sitecol_shakemap(uri, ['PGA', 'MMI'])
    assert not {'phi', 'tau', 'CL'} & set(shakemap.dtype.names)
    assert get_metadata(shakemap, 'stations') is None
    assert 'The ShakeMap has no phi for MMI' in caplog.text


@pytest.mark.parametrize('strategy', ['circulant_embedding',
                                      'cholesky_decomposition'])
def test_lothbaker_without_posterior_components(tmp_path, strategy):
    # without the stored between-event factors (XML products, incomplete
    # shake_result.hdf products) LothBaker2013 keeps the cross-IMT
    # correlation of the residuals, also with the dense factorization
    path = tmp_path / 'shake_result.hdf'
    _product(path, conditioned=False)
    with h5py.File(path, 'r+') as h5:  # only std, as in the XML products
        del h5['arrays/imts/GREATER_OF_TWO_HORIZONTAL/PGA/phi']
        del h5['arrays/imts/GREATER_OF_TWO_HORIZONTAL/PGA/tau']
    sitecol, shakemap, _, names = get_sitecol_shakemap(
        {'kind': 'shake_result_hdf', 'fname': str(path)}, ['PGA', 'SA(0.3)'])
    assert not {'phi', 'tau', 'CL'} & set(shakemap.dtype.names)
    model = loth_baker_2013.LothBaker2013()
    method = {'kind': 'Silva&Horspool', 'spatial_model': model,
              'cross_imt_model': None, 'cholesky_limit': 10000,
              'correlation_strategy': strategy, 'sites': sitecol}
    gmfs = to_gmfs(shakemap, method, None, 99, 50_000, 42, names)[1]
    residuals = numpy.log(gmfs)
    corr = [numpy.corrcoef(res[:, 0], res[:, 1])[0, 1] for res in residuals]
    expected = model.correlation_block(
        numpy.zeros((1, 1)), [imt.PGA()], [imt.SA(.3)])[0, 0]
    assert expected > .5
    numpy.testing.assert_allclose(corr, expected, atol=.02)


def test_between_event_model_without_phi(tmp_path):
    # with tau but without phi the between-event terms are still sampled
    # with the selected model, the within-event sigma being
    # sqrt(std^2 - tau^2)
    path = tmp_path / 'shake_result.hdf'
    _product(path, conditioned=False)  # phi = .6, .7 and tau = .2
    with h5py.File(path, 'r+') as h5:
        del h5['arrays/imts/GREATER_OF_TWO_HORIZONTAL/PGA/phi']
    sitecol, shakemap, _, names = get_sitecol_shakemap(
        {'kind': 'shake_result_hdf', 'fname': str(path)}, ['PGA', 'SA(0.3)'])
    assert 'tau' in shakemap.dtype.names
    assert not {'phi', 'CL'} & set(shakemap.dtype.names)
    model = loth_baker_2013.LothBaker2013()
    rho = model.correlation_block(
        numpy.zeros((1, 1)), [imt.PGA()], [imt.SA(.3)])[0, 0]
    for between, rho_b in [(NoCrossCorrelation(), 0),
                           (FullCrossCorrelation(), 1)]:
        method = {'kind': 'Silva&Horspool', 'spatial_model': model,
                  'cross_imt_model': None, 'cholesky_limit': 10000,
                  'correlation_strategy': 'circulant_embedding',
                  'sites': sitecol, 'between_event_model': between}
        gmfs = to_gmfs(shakemap, method, None, 99, 50_000, 42, names)[1]
        cov = [numpy.cov(res[:, 0], res[:, 1])[0, 1]
               for res in numpy.log(gmfs)]
        numpy.testing.assert_allclose(
            cov, rho * .6 * .7 + rho_b * .04, atol=.006)


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


def test_real_product_reconstructs_conditional_variance(caplog):
    # a 10x10 window of the us6000t7uu product (shakemap-modules 1.1.16),
    # where the stations reduce the variance the most, with all of its
    # 512 PGA and 514 SA(1.0) stations; the products store float32 values,
    # including the periods: SA(0.01) used to be rejected by LothBaker2013
    fname = os.path.join(DATA, 'us6000t7uu_shake_result.hdf')
    shakemap = get_array(kind='shake_result_hdf', fname=fname)
    stations = get_metadata(shakemap, 'stations')
    for im, period in (('PGA', .01), ('SA(1.0)', 1.)):
        phi = shakemap['phi'][im]
        K = station_conditioning(
            shakemap['lon'], shakemap['lat'], period, phi,
            stations[stations['imt'] == im.encode()])
        tau2 = (shakemap['CL'][im].astype(numpy.float64) ** 2).sum(axis=1)
        expected = shakemap['std'][im].astype(numpy.float64) ** 2 - tau2
        # the stations reduce the prior within-event variance up to 60%
        assert (expected / phi ** 2).min() < .4
        numpy.testing.assert_allclose(
            phi ** 2 - (K ** 2).sum(axis=1), expected, atol=1E-3 * .3)
    gmfs = _gmfs(shakemap, ['PGA', 'SA(1.0)'], count=20_000)
    for i, im in enumerate(['PGA', 'SA(1.0)']):
        numpy.testing.assert_allclose(
            numpy.log(gmfs[:, :, i]).var(axis=1),
            shakemap['std'][im] ** 2, rtol=.05)
    assert 'reproduces the ShakeMap' not in caplog.text


def _fallback(monkeypatch, exc):
    # get_array_usgs_id with a failing shake_result.hdf and a grid.xml
    xml = numpy.zeros(2, [('lon', float), ('lat', float)])

    def get_array(kind, **kw):
        if kind == 'shake_result_hdf':
            raise exc
        return xml
    monkeypatch.setattr(parsers, 'get_array', get_array)
    contents = {'download/shake_result.hdf': {'url': 'hdf'},
                'download/grid.xml': {'url': 'xml'}}
    return get_array_usgs_id('usgs_id', 'us0', contents)


def test_unusable_product_falls_back_to_xml_with_a_note(monkeypatch):
    array = _fallback(monkeypatch, ShakeMapProductError('unsupported'))
    assert get_metadata(array, 'note') == (
        'shake_result.hdf not used: unsupported')


def test_errors_are_not_hidden_by_the_xml_fallback(monkeypatch):
    with pytest.raises(ValueError, match='a bug'):
        _fallback(monkeypatch, ValueError('a bug'))
