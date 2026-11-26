# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2026 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import logging
import numpy
from scipy.stats import truncnorm
from scipy import interpolate

from openquake.baselib.general import CallableDict
from openquake.hazardlib import geo, imt, site
from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCorrelationModel)
from openquake.hazardlib.correlation_models.cross_imt.\
    no_cross_correlation import NoCrossCorrelation
from openquake.hazardlib.calc.gmf import (
    _ce_layout, _correlation_budget, _site_positions, _truncated_normals)
from openquake.hazardlib.correlation_models.circulant_embedding import (
    CirculantEmbeddingFactor, RegularGridLayout, _embedding_shape,
    _lag_distances, _spectral_root)

F32 = numpy.float32
F64 = numpy.float64
PCTG = 100  # percent of g, the gravity acceleration
MAX_GMV = 5.  # 5 g
MAX_PGV_GMV = 500.  # cm/s
NUM_VARIANCE_SAMPLES = 200_000  # see _between_variance_ratio


def spatial_correlation_array(dmatrix, imts, model, context=None):
    """
    :param dmatrix: distance matrix of shape (N, N)
    :param imts: M intensity measure types
    :param model: spatial correlation model
    :returns: array of shape (M, N, N)
    """
    n = len(dmatrix)
    if model is None:
        return numpy.repeat(
            numpy.eye(n)[numpy.newaxis], len(imts), axis=0)
    model.validate_imts(imts)
    corr = numpy.zeros((len(imts), n, n))
    for imti, imt_ in enumerate(imts):
        corr[imti] = model.correlation_matrix(
            dmatrix, imt_, context=context)
    return corr


def spatial_covariance_array(stddev, corrmatrices):
    """
    :param stddev: array of shape (M, N)
    :param corrmatrices: array of shape (M, N, N)
    :returns: an array of shape (M, N, N)
    """
    # this depends on sPGA, sSa03, sSa10, sSa30
    matrices = []

    for i, std in enumerate(stddev):
        covmatrix = numpy.multiply(corrmatrices[i], numpy.outer(std, std))
        matrices.append(covmatrix)

    return numpy.array(matrices)


def cross_correlation_matrix(imts, model):
    """
    :param imts: M intensity measure types
    :param model: cross-IMT correlation model
    :returns: an array of shape (M, M)
    """
    if model is None:
        return numpy.eye(len(imts))
    model.validate_imts(imts)
    return model.correlation_matrix(imts)


# not used since the ShakeMap does it already
def amplify_gmfs(imts, vs30s, gmfs):
    """
    Amplify the ground shaking depending on the vs30s
    """
    n = len(vs30s)
    out = [amplify_ground_shaking(im.period, vs30s[i], gmfs[m * n + i])
           for m, im in enumerate(imts) for i in range(n)]
    return numpy.array(out)


def amplify_ground_shaking(T, vs30, gmvs):
    """
    :param T: period
    :param vs30: velocity
    :param gmvs: ground motion values for the current site in units of g
    """
    gmvs[gmvs > MAX_GMV] = MAX_GMV  # accelerations > 5g are absurd
    interpolator = interpolate.interp1d(
        [0, 0.1, 0.2, 0.3, 0.4, 5],
        [(760 / vs30)**0.35,
         (760 / vs30)**0.35,
         (760 / vs30)**0.25,
         (760 / vs30)**0.10,
         (760 / vs30)**-0.05,
         (760 / vs30)**-0.05],
    ) if T <= 0.3 else interpolate.interp1d(
        [0, 0.1, 0.2, 0.3, 0.4, 5],
        [(760 / vs30)**0.65,
         (760 / vs30)**0.65,
         (760 / vs30)**0.60,
         (760 / vs30)**0.53,
         (760 / vs30)**0.45,
         (760 / vs30)**0.45],
    )
    return interpolator(gmvs) * gmvs


def cholesky(spatial_cov, cross_corr):
    """
    Decompose the spatial covariance and cross correlation matrices.

    :param spatial_cov: array of shape (M, N, N)
    :param cross_corr: array of shape (M, M)
    :returns: a triangular matrix of shape (M * N, M * N)
    """
    M, N = spatial_cov.shape[:2]
    cutoff = numpy.eye(N) * 1E-8  # avoid negative eigenvalues
    try:
        L = numpy.array([numpy.linalg.cholesky(spatial_cov[i] + cutoff)
                         for i in range(M)])
    except numpy.linalg.LinAlgError as exc:
        raise exc.__class__('%s: see https://docs.openquake.org/oq-engine/'
                            'advanced/shakemaps.html#correlation' % exc)
    LLT = []
    for i in range(M):
        row = [L[i] @ L[j].T * cross_corr[i, j] for j in range(M)]
        LLT.extend(numpy.array(row).transpose(1, 0, 2).reshape(N, M * N))

    big_cutoff = numpy.eye(M*N) * 1E-8  # avoid negative eigenvalues
    return numpy.linalg.cholesky(numpy.array(LLT) + big_cutoff)


calculate_gmfs = CallableDict()

CORRELATION_MATRIX_TOO_LARGE = '''\
You have a correlation matrix which is too large: %s > %d.
To avoid that, set a proper `region_grid_spacing` so that your exposure
involves less sites.'''


def _build_imt_scaling_vector(imts, shakemap_std, pctg_value):
    """
    Builds a column vector matching the flattened shape of the shakemap arrays,
    applying pctg_value scaling to acceleration IMTs and 1.0 to velocity (PGV).
    """
    # NOTE: dtype=float ensures the final gmfs to have max precision
    # floating-point accuracy. We might prefer instead to avoid specifying it,
    # so the default dtype would match the native precision of ShakeMap data.
    return numpy.array([
        numpy.full_like(
            shakemap_std[str(im)],
            1.0 if 'PGV' in str(im) else pctg_value,
            dtype=float)
        for im in imts
    ]).reshape(-1, 1)


def _spectral_sqrts(spatial_model, imts, shape, spacing, context):
    # Square roots of the spectra of the spatial correlations of the IMTs
    # on the periodic grid of the given shape, with shape (M, *shape), or
    # None if a spectrum is materially negative, i.e. the embedding is too
    # small; without a spatial model the sites are independent (flat
    # spectra). The tolerance is the one of _spectral_root
    if spatial_model is None:
        return numpy.ones((len(imts),) + shape)
    distances = _lag_distances(shape, spacing).reshape(-1, 1)
    sqrts = numpy.zeros((len(imts),) + shape)
    for m, im in enumerate(imts):
        rho = spatial_model.correlation_matrix(
            distances, im, context=context).reshape(shape)
        # the correlation is even on the torus, so its spectrum is real
        spectrum = numpy.fft.fft2(rho).real
        tolerance = (100 * numpy.finfo(float).eps * spectrum.size *
                     max(1., numpy.abs(spectrum).max()))
        if spectrum.min() < -tolerance:
            return None
        sqrts[m] = numpy.sqrt(numpy.maximum(spectrum, 0))
    return sqrts


def _coregionalized_factor(spatial_model, cross_imt_model, imts,
                           grid_shape, spacing, context, site_indices,
                           max_multiplier=8):
    # Circulant embedding of separate spatial and cross-IMT models, the
    # stationary analogue of the dense c_ij L_i L_j^T (see cholesky): at
    # every spatial frequency the cross-spectrum of the IMTs i and j is
    # c_ij sqrt(S_i S_j), S_i being the spectrum of the spatial correlation
    # of the IMT i. It is positive semidefinite by construction, being
    # D C D with D = diag(sqrt(S_i)), and it keeps the spatial correlation
    # of each IMT; the embedding is enlarged until every S_i is nonnegative
    if spatial_model is not None:
        spatial_model.validate_imts(imts)
    cross = cross_correlation_matrix(imts, cross_imt_model)
    indices = CirculantEmbeddingFactor._validate_indices(
        site_indices, grid_shape)
    M = len(imts)
    for multiplier in range(1, max_multiplier + 1):
        shape = _embedding_shape(grid_shape, multiplier)
        sqrts = _spectral_sqrts(spatial_model, imts, shape, spacing,
                                context)
        if sqrts is None:
            continue
        lags = numpy.zeros(shape + (M, M))
        for i in range(M):
            for j in range(i, M):
                lags[..., i, j] = lags[..., j, i] = cross[i, j] * (
                    numpy.fft.ifft2(sqrts[i] * sqrts[j]).real)
        minimum, root = _spectral_root(lags)
        if root is not None:
            return CirculantEmbeddingFactor(
                root, tuple(grid_shape), shape, M, indices, multiplier,
                minimum)
    raise ValueError(
        'The circulant embedding of the spatial correlation is not positive '
        f'semidefinite through multiplier {max_multiplier}')


def circulant_embedding_feasible(sites):
    """
    :returns: True if the sites, or their complete grid, can be laid out
              on a regular correlation grid for circulant embedding
    """
    complete = getattr(sites, 'complete', sites)
    for candidate in (complete, sites):
        try:
            RegularGridLayout.from_sites(candidate)
        except ValueError:
            continue
        return True
    return False


# Factorize a regular-grid correlation field and retain only selected sites.
def _circulant_factor(sites, imts, spatial_model,
                      cross_imt_model, context):
    if (spatial_model is not None and
            not spatial_model.SUPPORTS_CIRCULANT_EMBEDDING):
        raise ValueError(
            f'{spatial_model.__class__.__name__} does not support '
            'circulant_embedding')
    # the complete grid or, if it is not regular, the selected sites, as in
    # GmfComputer._get_ce_factor
    grid_sites, layout = _ce_layout(sites)
    site_indices = layout.site_indices[_site_positions(grid_sites, sites)]
    # the joint models ignore the cross-IMT model, as in _correlate_dense
    if _is_joint_model(spatial_model) or (
            spatial_model is not None and cross_imt_model is None):
        return CirculantEmbeddingFactor.build(
            spatial_model, imts, layout.grid_shape, layout.spacing,
            ResidualComponent.WITHIN_EVENT, context, site_indices)
    return _coregionalized_factor(
        spatial_model, cross_imt_model, imts, layout.grid_shape,
        layout.spacing, context, site_indices)


# Apply the selected spatial factorization to sampled residuals.
def _correlate_residuals(Z, imts, sites, spatial_model,
                         cross_imt_model, correlation_strategy, context,
                         cholesky_limit, truncation_level, seed):
    M, N = len(imts), len(sites.lons)
    if correlation_strategy == 'circulant_embedding':
        factor = _circulant_factor(
            sites, imts, spatial_model, cross_imt_model, context)
        batch_size = factor.batch_size(_correlation_budget())
        residuals = numpy.empty((factor.output_size, Z.shape[1]), F32)
        rng = numpy.random.default_rng(seed + 2)
        for start in range(0, Z.shape[1], batch_size):
            stop = min(start + batch_size, Z.shape[1])
            shape = (factor.input_size, stop - start)
            if truncation_level <= 1E-9:
                samples = numpy.zeros(shape)
            else:
                # in place, as in the scenario calculator: truncnorm.rvs
                # would need ~25 times the memory of the samples
                samples = _truncated_normals(shape, truncation_level, rng)
            residuals[:, start:stop] = factor.apply(samples)
        return residuals
    if M * N > cholesky_limit:
        raise ValueError(CORRELATION_MATRIX_TOO_LARGE % (
            f'{M=} x {N=}', cholesky_limit))
    return _correlate_dense(
        Z, imts, sites, spatial_model, cross_imt_model, context)


# Dense correlation path for arbitrary site geometry.
def _spatial_correlation(dmatrix, imts, spatial_model, context):
    # spatial_correlation_array, warning if the matrix of the first IMT is
    # degenerate, for instance for coincident sites
    spatial_corr = spatial_correlation_array(
        dmatrix, imts, spatial_model, context)
    eig, _ = numpy.linalg.eigh(spatial_corr[0])
    small_eig = (eig < 1E-6).sum()
    if small_eig:
        logging.warning('The spatial correlation matrix is degenerate, '
                        f'{small_eig} of {len(dmatrix)} eigenvalues are '
                        'zeros')
    return spatial_corr


def _correlate_legacy(Z, imts, shakemap, spatial_model,
                      cross_imt_model, cholesky_limit, context):
    # The dense calculation of the engine before shake_result.hdf, kept for
    # the ShakeMaps without tau sampled with separate spatial and cross-IMT
    # models: it factorizes the covariance, so it returns residuals in ln
    # units
    M, N = len(imts), len(shakemap)
    if M * N > cholesky_limit:
        raise ValueError(CORRELATION_MATRIX_TOO_LARGE % (
            f'{M=} x {N=}', cholesky_limit))
    cross_corr = cross_correlation_matrix(imts, cross_imt_model)
    dmatrix = geo.geodetic.distance_matrix(
        shakemap['lon'], shakemap['lat'])
    spatial_corr = _spatial_correlation(
        dmatrix, imts, spatial_model, context)
    stddev = [shakemap['std'][str(im)] for im in imts]
    for im, std in zip(imts, stddev):
        if std.sum() == 0:
            raise ValueError('Cannot decompose the spatial covariance '
                             'because stddev==0 for IMT=%s' % im.string)
    covariance = spatial_covariance_array(stddev, spatial_corr)

    # Cholesky Decomposition: L @ Z contains ln-unit residuals
    return cholesky(covariance, cross_corr) @ Z


def _is_joint_model(model):
    # True for the within-event models correlating sites and IMTs jointly,
    # like LothBaker2013, which have no separate spatial correlation
    return model is not None and not isinstance(
        model, SpatialCorrelationModel)


def _correlate_dense(Z, imts, sites, spatial_model, cross_imt_model,
                     context):
    # Dense correlation for the unit-variance residuals of the points; the
    # joint models use their own factorization, as in GmfComputer
    if _is_joint_model(spatial_model):
        return spatial_model.factor(
            sites, imts, ResidualComponent.WITHIN_EVENT, context).apply(Z)
    dmatrix = geo.geodetic.distance_matrix(sites.lons, sites.lats)
    cross_corr = cross_correlation_matrix(imts, cross_imt_model)
    spatial_corr = _spatial_correlation(
        dmatrix, imts, spatial_model, context)
    return cholesky(spatial_corr, cross_corr) @ Z


def _separate_between_terms(shakemap, imts, spatial_model):
    # True if the between-event terms are sampled separately, i.e. there
    # is a within-event model and the ShakeMap (a shake_result.hdf
    # product) stores tau for all the IMTs
    if spatial_model is None or 'tau' not in shakemap.dtype.names:
        return False
    if all(numpy.isfinite(shakemap['tau'][str(im)]).all() for im in imts):
        return True
    logging.warning('The ShakeMap has no tau for some IMTs: the '
                    'between-event terms are not sampled separately')
    return False


def _between_variance_ratio(imts, truncation_level, between_event_model):
    # Ratio, for each IMT, between the variance of the between-event terms
    # actually sampled and the variance of the truncated within-event
    # samples. The independent terms have the exact variance of their
    # truncated normal (the ratio is 1 for the same truncation level); the
    # other between-event models truncate the IMTs jointly, which reduces
    # the marginal variances further (by up to ~25% at truncation level 1),
    # so their variances are estimated once, with a fixed seed, from
    # NUM_VARIANCE_SAMPLES draws (~0.1 s)
    within_var = truncnorm(-truncation_level, truncation_level).var()
    if isinstance(between_event_model, NoCrossCorrelation):
        return numpy.full(len(imts),
                          between_event_model.distribution.var() / within_var)
    eps = between_event_model.get_inter_eps(
        imts, NUM_VARIANCE_SAMPLES, numpy.random.default_rng(42))
    return eps.var(axis=1) / within_var


def _within_between_stds(shakemap, imts, has_tau, var_ratio=None):
    # Return the within- and between-event standard deviations of shape
    # (M, N); without tau the within-event residuals have the total
    # conditional std and there are no separate between-event terms.
    # With tau, which in shake_result.hdf is conditional on the stations
    # (unlike phi, the prior one, which is not used), the within-event
    # variance is the conditional total variance minus the variance of
    # the between-event terms actually sampled, i.e. tau^2 times var_ratio
    # (see _between_variance_ratio) in units of the variance of the
    # truncated within-event samples, so that the marginal variance std^2
    # of ShakeMap is preserved (reduced by the truncation, as for all the
    # residuals) and nothing is counted twice; tau is clipped to std to
    # absorb the float32 rounding
    std = numpy.array([shakemap['std'][str(im)] for im in imts], F64)
    if not has_tau:
        return std, None
    tau = numpy.minimum(
        numpy.array([shakemap['tau'][str(im)] for im in imts], F64), std)
    if var_ratio is None:
        var_ratio = numpy.ones(len(imts))
    within_var = std ** 2 - var_ratio[:, None] * tau ** 2
    return numpy.sqrt(numpy.maximum(within_var, 0)), tau


def _active_imts(shakemap, imts, correlated):
    # Indices of the correlated IMTs with a nonzero ShakeMap uncertainty
    active = [i for i in correlated
              if numpy.any(shakemap['std'][str(imts[i])])]
    skipped = [str(imts[i]) for i in correlated if i not in active]
    if skipped:
        logging.warning(
            'No ShakeMap uncertainty for %s; those IMTs are '
            'deterministic and will not be spatially correlated',
            ', '.join(skipped))
    if not active:
        logging.warning(
            'ShakeMap uncertainty is zero; spatial correlation was skipped')
    return active


def _imt_rows(active, N):
    # Rows of the active IMTs in the arrays of shape (M * N, E): a slice if
    # they are contiguous (the usual case), so that indexing gives views
    # and not copies of the arrays
    if active == list(range(active[0], active[-1] + 1)):
        return slice(active[0] * N, (active[-1] + 1) * N)
    return numpy.concatenate([
        numpy.arange(i * N, (i + 1) * N) for i in active])


def _independent_gmfs(mu, Z, total_std, scale, rows=slice(None)):
    # GMFs of the given rows, with residuals independent in space and
    # across IMTs, having the total conditional std of the ShakeMap
    return mu[rows] * numpy.exp(Z[rows] * total_std[rows]) / scale[rows]


@calculate_gmfs.add('Silva&Horspool')
def calculate_gmfs_sh(kind, shakemap, imts, Z, mu, spatial_model,
                      cross_imt_model, cholesky_limit,
                      correlation_strategy='cholesky_decomposition',
                      sites=None, context=None, truncation_level=3,
                      correlation_seed=0, between_event_model=None):
    """
    Implementation of paper by Silva and Horspool 2019
    https://onlinelibrary.wiley.com/doi/abs/10.1002/eqe.3154?af=R

    The conditional medians and standard deviations of the ShakeMap are
    preserved, while the spatial and cross-IMT dependence is imposed by
    the selected correlation models. This is an approximation, since the
    station-conditioned covariance is not available in the ShakeMap
    products. When tau is available (shake_result.hdf) the between-event
    terms are sampled separately, see _within_between_stds.

    :param shakemap: site coordinates with median ShakeMap values
    :param imts: list of required imts
    :param Z: truncated standard normal samples of shape (M * N, E)
    :param mu: ShakeMap medians of shape (M * N, E)
    :param spatial_model: spatial (or spatial cross-IMT) correlation model
        of the within-event residuals
    :param cross_imt_model: cross-IMT correlation model
    :param cholesky_limit: maximum M * N for a dense factorization
    :param correlation_strategy: cholesky_decomposition or
        circulant_embedding
    :param sites: site collection of the ShakeMap points, if any
    :param context: CorrelationContext of the rupture, if any
    :param truncation_level: truncation level of the samples
    :param correlation_seed: seed of the correlated samples
    :param between_event_model: cross-IMT model of the between-event
        terms, if any; otherwise they are independent across IMTs
    :returns: gmfs of shape (M * N, E)
    """
    correlated = [i for i, im in enumerate(imts) if hasattr(im, 'period')]
    N = len(shakemap)
    total_std = numpy.array([
        shakemap['std'][str(im)] for im in imts]).reshape(-1, 1)
    scale = _build_imt_scaling_vector(imts, shakemap['std'], PCTG)
    if (truncation_level <= 1E-9 or not correlated or
            spatial_model is None and cross_imt_model is None):
        # median-only or independent total-residual sampling
        return _independent_gmfs(mu, Z, total_std, scale)
    active = _active_imts(shakemap, imts, correlated)
    if not active:
        return _independent_gmfs(mu, Z, total_std, scale)
    corr_imts = [imts[i] for i in active]
    rows = _imt_rows(active, N)
    # only the rows of the IMTs not correlated are sampled independently,
    # the others are computed below
    result = numpy.empty_like(mu)
    independent = numpy.ones(len(mu), bool)
    independent[rows] = False
    if independent.any():
        result[independent] = _independent_gmfs(
            mu, Z, total_std, scale, independent)
    has_tau = _separate_between_terms(shakemap, corr_imts, spatial_model)
    if (correlation_strategy == 'cholesky_decomposition' and
            not has_tau and not _is_joint_model(spatial_model)):
        residuals = _correlate_legacy(
            Z[rows], corr_imts, shakemap, spatial_model, cross_imt_model,
            cholesky_limit, context)
        # mu contains the ShakeMap medians, residuals are in ln units
        result[rows] = mu[rows] * numpy.exp(residuals) / scale[rows]
        return result
    logging.info(
        'Imposing the correlation of %s on the conditional ShakeMap '
        'medians and standard deviations', ', '.join(
            model.__class__.__name__ for model in (
                spatial_model, cross_imt_model) if model is not None))
    if sites is None:
        sites = site.SiteCollection.from_points(
            shakemap['lon'], shakemap['lat'])
    # without a model the event terms are independent across IMTs and
    # truncated as the within-event samples, as in GmfComputer
    between_event_model = between_event_model or NoCrossCorrelation(
        truncation_level)
    # unit-variance within-event residuals, scaled by their conditional std
    residuals = _correlate_residuals(
        Z[rows], corr_imts, sites, spatial_model, cross_imt_model,
        correlation_strategy, context, cholesky_limit,
        truncation_level, correlation_seed)
    var_ratio = _between_variance_ratio(
        corr_imts, truncation_level, between_event_model) if has_tau else None
    within, tau = _within_between_stds(
        shakemap, corr_imts, has_tau, var_ratio)
    residuals *= within.reshape(-1, 1)
    if has_tau:  # the event terms of shape (M, E), spatially uniform
        eps = between_event_model.get_inter_eps(
            corr_imts, Z.shape[1],
            numpy.random.default_rng(correlation_seed + 5))
        residuals += (tau[:, :, None] * eps[:, None, :]).reshape(
            -1, Z.shape[1])
    result[rows] = mu[rows] * numpy.exp(residuals) / scale[rows]
    return result


@calculate_gmfs.add('basic')
def calculate_gmfs_basic(kind, shakemap, imts, Z, mu):
    """
    Basic calculation method to sample data from shakemap values

    :param shakemap: site coordinates with median ShakeMap values
    :param imts: list of required imts
    :returns: F(Z, mu) to calculate gmfs
    """
    # create vector with std values of shape (N*M, 1)
    sig = numpy.array([shakemap['std'][str(im)] for im in imts]).reshape(-1, 1)

    scale = _build_imt_scaling_vector(imts, shakemap['std'], PCTG)

    # mu contains the ShakeMap medians; Z * sig contains ln-unit residuals
    return mu * numpy.exp(Z * sig) / scale


@ calculate_gmfs.add('mmi')
def calculate_gmfs_mmi(kind, shakemap, imts, Z, mu):
    """
    Basic calculation method to sample data from shakemap values
    given mmi intensities.

    :param shakemap: site coordinates with shakemap values
    :param imts: list of required imts
    :returns: F(Z, mu) to calculate gmfs
    """
    try:
        # create vector with std values
        sig = numpy.array(shakemap['std']['MMI']).flatten()
    except ValueError as e:
        raise ValueError('No stds for MMI intensities supplied, only %s' %
                         ', '.join(shakemap['std'].dtype.names)) from e

    # multiply Z and sig column-wise and add mean
    return (Z.T * sig).T + mu


def to_gmfs(shakemap, gmf_dict, vs30, truncation_level,
            num_gmfs, seed, imts=None):
    """
    :param shakemap: site coordinates with shakemap values
    :param gmf_dict: a dictionary key -> arrays
    :param vs30: an array of vs30 values used to amplify or None
    :param truncation_level: truncation level (float)
    :param num_gmfs: E, amount of gmfs to generate
    :param seed: seed for generating numbers
    :param imts: list of IMT-strings for which gmfs are generated
    :returns: list of IMT-objects, array of GMFs of shape (N, E, M)
    """
    # create list of imts
    if imts is None or len(imts) == 0:
        imts = [imt.from_string(im) for im in shakemap['std'].dtype.names]
    else:
        imts = [imt.from_string(im)
                for im in imts if im in shakemap['std'].dtype.names]

    # assign iterators
    M = len(imts)       # Number of imts
    N = len(shakemap)   # number of sites

    # A zero truncation_level in the job file is converted to 1E-9 by OqParam.
    # Treat as exact zero so that a no-uncertainty GMF reproduces the ShakeMap
    # grid.xml field.
    if truncation_level <= 1E-9:
        Z = numpy.zeros((M * N, num_gmfs))
    else:
        # as in the scenario and event based calculators, the normal
        # samples are truncated before being correlated, so the variance
        # of the residuals is reduced by the variance of the truncated
        # normal (0.29, 0.77 and 0.97 for truncation levels 1, 2 and 3)
        # while the correlation coefficients are preserved; they are
        # drawn in place, with the same numbers as truncnorm.rvs with
        # random_state=seed, which would need ~25 times the memory
        Z = _truncated_normals((M * N, num_gmfs), truncation_level,
                               numpy.random.RandomState(seed))

    # build array of median values of shape (M*N, E)
    vals = numpy.concatenate(
        [shakemap['val'][str(imt)] for imt in imts]).astype(float)
    mu = numpy.repeat(vals[:, None], num_gmfs, axis=1)

    # assemble dictionary for the calculation of the gmfs; the random
    # streams are: seed for Z, seed + 2 for circulant embedding and
    # seed + 5 for the between-event terms
    gmf_dict.update({'shakemap': shakemap, 'imts': imts, 'Z': Z, 'mu': mu})
    if gmf_dict.get('kind') == 'Silva&Horspool':
        gmf_dict.update(
            truncation_level=truncation_level, correlation_seed=seed)

    # execute the calculation
    gmfs = calculate_gmfs(gmf_dict.pop('kind'), **gmf_dict)

    # apply site effects
    if vs30 is not None:
        assert len(vs30) == len(shakemap), (len(vs30), len(shakemap))
        logging.info('Amplifying GMFs')
        gmfs = amplify_gmfs(imts, vs30, gmfs)

    # Reshape the output to (N, E, M) prior to the checks
    out_gmfs = gmfs.reshape((M, N, num_gmfs)).transpose(1, 2, 0)

    # Validate suspiciously large values per IMT
    for i, im in enumerate(imts):
        imt_str = str(im)
        imt_gmf_max = out_gmfs[:, :, i].max()
        if imt_str != 'PGV':
            if imt_gmf_max > MAX_GMV:
                logging.warning(
                    'There are suspiciously large GMVs for %s of %.2fg',
                    imt_str, imt_gmf_max)
        elif imt_gmf_max > MAX_PGV_GMV:
            logging.warning(
                'There are suspiciously large GMVs for PGV of %.2f cm/s',
                imt_gmf_max)

    return imts, out_gmfs
