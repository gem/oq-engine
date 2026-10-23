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

from openquake.baselib import config
from openquake.baselib.general import CallableDict
from openquake.hazardlib import geo, imt
from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.circulant_embedding import (
    CirculantEmbeddingFactor, RegularGridLayout)

F32 = numpy.float32
PCTG = 100  # percent of g, the gravity acceleration
MAX_GMV = 5.  # 5 g
MAX_PGV_GMV = 500.  # cm/s


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


class _SeparableCorrelationModel:
    # Compose spatial and cross-IMT models for circulant embedding.
    SUPPORTS_CIRCULANT_EMBEDDING = True

    def __init__(self, spatial_model, cross_imt_model):
        self.spatial_model = spatial_model
        self.cross_imt_model = cross_imt_model

    def correlation_block(self, distances, imts1, imts2=None,
                          component=None, context=None):
        if imts2 is None:
            imts2 = imts1
        blocks = numpy.zeros((len(imts1) * len(distances),
                              len(imts2) * distances.shape[1]))
        for i, imt1 in enumerate(imts1):
            for j, imt2 in enumerate(imts2):
                if self.spatial_model is None:
                    spatial = (distances == 0).astype(float)
                else:
                    corr1 = self.spatial_model.correlation_matrix(
                        distances, imt1, context=context)
                    corr2 = self.spatial_model.correlation_matrix(
                        distances, imt2, context=context)
                    spatial = numpy.maximum(corr1, corr2)
                cross = (self.cross_imt_model.rho(
                    imt1, imt2, context=context)
                    if self.cross_imt_model else float(imt1 == imt2))
                row = slice(i * len(distances), (i + 1) * len(distances))
                col = slice(j * distances.shape[1],
                            (j + 1) * distances.shape[1])
                blocks[row, col] = spatial * cross
        return blocks


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
    complete = getattr(sites, 'complete', sites)
    try:
        layout = RegularGridLayout.from_sites(complete)
        site_indices = (layout.site_indices if complete is sites else
                        layout.site_indices[_site_positions(complete, sites)])
    except ValueError as complete_error:
        if complete is sites:
            raise
        logging.warning('Using selected sites for circulant embedding: %s',
                        complete_error)
        layout = RegularGridLayout.from_sites(sites)
        site_indices = layout.site_indices
    model = spatial_model
    if cross_imt_model is not None or model is None:
        model = _SeparableCorrelationModel(model, cross_imt_model)
    return CirculantEmbeddingFactor.build(
        model, imts, layout.grid_shape, layout.spacing,
        ResidualComponent.WITHIN_EVENT, context, site_indices)


def _site_positions(complete, selected):
    # Map selected site IDs to the row order of the complete grid.
    complete_sids = numpy.asarray(complete.sids)
    selected_sids = numpy.asarray(selected.sids)
    order = numpy.argsort(complete_sids)
    sorted_sids = complete_sids[order]
    positions = numpy.searchsorted(sorted_sids, selected_sids)
    if (numpy.any(positions == len(sorted_sids)) or
            numpy.any(sorted_sids[positions] != selected_sids)):
        raise ValueError('Selected sites are absent from the complete grid')
    return order[positions]


# Apply the selected spatial factorization to sampled residuals.
def _correlate_residuals(Z, imts, sites, spatial_model,
                         cross_imt_model, correlation_strategy, context,
                         cholesky_limit, truncation_level, seed):
    M, N = len(imts), len(sites.lons)
    if correlation_strategy == 'circulant_embedding':
        factor = _circulant_factor(
            sites, imts, spatial_model, cross_imt_model, context)
        budget = int(float(config.memory.correlated_gmf_gb) * 1024 ** 3)
        batch_size = factor.batch_size(budget)
        residuals = numpy.empty((factor.output_size, Z.shape[1]), F32)
        rng = numpy.random.default_rng(seed + 2)
        for start in range(0, Z.shape[1], batch_size):
            stop = min(start + batch_size, Z.shape[1])
            shape = (factor.input_size, stop - start)
            if truncation_level <= 1E-9:
                samples = numpy.zeros(shape)
            else:
                samples = truncnorm.rvs(
                    -truncation_level, truncation_level, loc=0, scale=1,
                    size=shape, random_state=rng)
            residuals[:, start:stop] = factor.apply(samples)
        return residuals
    if M * N > cholesky_limit:
        raise ValueError(CORRELATION_MATRIX_TOO_LARGE % (
            f'{M=} x {N=}', cholesky_limit))
    if sites is None:
        lons, lats = None, None
    else:
        lons, lats = sites.lons, sites.lats
    return _correlate_dense(
        Z, imts, spatial_model, cross_imt_model, context, lons, lats)


# Dense correlation path for arbitrary site geometry.
def _correlate_legacy(Z, imts, shakemap, spatial_model,
                      cross_imt_model, cholesky_limit, context):
    # Preserve the established dense covariance calculation for XML maps.
    M, N = len(imts), len(shakemap)
    if M * N > cholesky_limit:
        raise ValueError(CORRELATION_MATRIX_TOO_LARGE % (
            f'{M=} x {N=}', cholesky_limit))
    cross_corr = cross_correlation_matrix(imts, cross_imt_model)
    dmatrix = geo.geodetic.distance_matrix(
        shakemap['lon'], shakemap['lat'])
    spatial_corr = spatial_correlation_array(
        dmatrix, imts, spatial_model, context)
    eig, _ = numpy.linalg.eigh(spatial_corr[0])
    small_eig = (eig < 1E-6).sum()
    if small_eig:
        logging.warning('The spatial correlation matrix is degenerate, '
                        f'{small_eig} of {N} eigenvalues are zeros')
    stddev = [shakemap['std'][str(im)] for im in imts]
    for im, std in zip(imts, stddev):
        if std.sum() == 0:
            raise ValueError('Cannot decompose the spatial covariance '
                             'because stddev==0 for IMT=%s' % im.string)
    covariance = spatial_covariance_array(stddev, spatial_corr)
    return cholesky(covariance, cross_corr) @ Z


def _correlate_dense(Z, imts, spatial_model, cross_imt_model,
                     context, lons=None, lats=None):
    N = Z.shape[0] // len(imts)
    cross_corr = cross_correlation_matrix(imts, cross_imt_model)
    if lons is None:
        lons = numpy.zeros(N)
        lats = numpy.arange(N, dtype=float) * 1E-9
    dmatrix = geo.geodetic.distance_matrix(lons, lats)
    spatial_corr = spatial_correlation_array(
        dmatrix, imts, spatial_model, context)
    eig, _ = numpy.linalg.eigh(spatial_corr[0])
    small_eig = (eig < 1E-6).sum()
    if small_eig:
        logging.warning('The spatial correlation matrix is degenerate, '
                        f'{small_eig} of {N} eigenvalues are zeros')
    return cholesky(spatial_corr, cross_corr) @ Z


@calculate_gmfs.add('Silva&Horspool')
def calculate_gmfs_sh(kind, shakemap, imts, Z, mu, spatial_model,
                      cross_imt_model, cholesky_limit,
                      correlation_strategy='cholesky_decomposition',
                      sites=None, context=None, tau_Z=None,
                      truncation_level=3, correlation_seed=0):
    # Implement the ShakeMap spatial correlation sampling.
    correlated = [i for i, im in enumerate(imts) if hasattr(im, 'period')]
    N = len(shakemap)
    total_std = numpy.array([
        shakemap['std'][str(im)] for im in imts]).reshape(-1, 1)
    components = {'phi', 'tau'} <= set(shakemap.dtype.names)
    std_field = 'phi' if components else 'std'
    scale = _build_imt_scaling_vector(imts, shakemap['std'], PCTG)
    result = mu * numpy.exp(Z * total_std) / scale
    if not correlated or truncation_level <= 1E-9:
        return result
    tau_present = 'tau' in shakemap.dtype.names and tau_Z is not None
    active = [i for i in correlated if (
        numpy.any(shakemap[std_field][str(imts[i])]) or
        (tau_present and numpy.any(shakemap['tau'][str(imts[i])])))]
    if len(active) != len(correlated):
        skipped = [str(imts[i]) for i in correlated if i not in active]
        if skipped:
            logging.warning(
                'No ShakeMap uncertainty for %s; those IMTs are '
                'deterministic and will not be spatially correlated',
                ', '.join(skipped))
    if not active:
        logging.warning(
            'ShakeMap uncertainty is zero; spatial correlation was skipped')
        return result
    corr_imts = [imts[i] for i in active]
    row_indices = numpy.concatenate([
        numpy.arange(i * N, (i + 1) * N) for i in active])
    corr_Z = Z[row_indices]
    if (correlation_strategy == 'cholesky_decomposition' and
            not components):
        residuals = _correlate_legacy(
            corr_Z, corr_imts, shakemap, spatial_model, cross_imt_model,
            cholesky_limit, context)
        result[row_indices] = mu[row_indices] * numpy.exp(
            residuals) / scale[row_indices]
        return result
    if sites is None:
        sites = type('Sites', (), {
            'lons': shakemap['lon'], 'lats': shakemap['lat']})()
    residuals = _correlate_residuals(
        corr_Z, corr_imts, sites, spatial_model, cross_imt_model,
        correlation_strategy, context, cholesky_limit,
        truncation_level, correlation_seed)
    corr_stds = numpy.array([
        shakemap[std_field][str(im)] for im in corr_imts]).reshape(-1, 1)
    residuals *= corr_stds
    if tau_present:
        tau = numpy.array([
            shakemap['tau'][str(im)] for im in corr_imts])
        tau_samples = numpy.repeat(
            tau_Z[active, numpy.newaxis, :], N, axis=1).reshape(
                len(corr_imts) * N, -1)
        residuals += tau.reshape(-1, 1) * tau_samples
    corr_mu = mu[row_indices]
    corr_scale = scale[row_indices]
    result[row_indices] = corr_mu * numpy.exp(
        residuals) / corr_scale
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
        Z = truncnorm.rvs(
            -truncation_level, truncation_level, loc=0, scale=1,
            size=(M * N, num_gmfs), random_state=seed)

    # build array of median values of shape (M*N, E)
    mu = numpy.array([numpy.ones(num_gmfs) * shakemap['val'][str(imt)][j]
                      for imt in imts for j in range(N)])

    # assemble dictionary for the calculation of the gmfs
    gmf_dict.update({'shakemap': shakemap, 'imts': imts, 'Z': Z, 'mu': mu})
    if gmf_dict.get('kind') == 'Silva&Horspool':
        gmf_dict.update(
            truncation_level=truncation_level, correlation_seed=seed)
    if ('tau' in shakemap.dtype.names and
            gmf_dict.get('kind') == 'Silva&Horspool'):
        if truncation_level <= 1E-9:
            tau_Z = numpy.zeros((M, num_gmfs))
        else:
            tau_Z = truncnorm.rvs(
                -truncation_level, truncation_level, loc=0, scale=1,
                size=(M, num_gmfs), random_state=seed + 1)
        gmf_dict['tau_Z'] = tau_Z

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
