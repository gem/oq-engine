# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
This module implements the process for conditioning ground motion
fields upon recorded strong motion station data or macroseismic
intensity observations described in Engler et al. (2022)
Engler, D. T., Worden, C. B., Thompson, E. M., & Jaiswal, K. S. (2022).
Partitioning Ground Motion Uncertainty When Conditioned on Station Data.
Bulletin of the Seismological Society of America, 112(2), 1060–1079.
https://doi.org/10.1785/0120210177

The USGS ShakeMap implementation of Engler et al. (2022) is described
in detail at: https://usgs.github.io/shakemap/manual4_0/tg_processing.html
and the bulk of the implementation code resides in the ShakeMap Model module:
https://code.usgs.gov/ghsc/esi/shakemap-modules/-/blob/main/src/shakemap_modules/coremods/model.py?

This implementation is intended for generating conditional random
ground motion fields for downstream use with the OpenQuake scenario
damage and loss calculators, such that users can provide a station
data file containing both seismic and macroseismic stations, where
and specify a list of target IMTs and list of sites for which the
OpenQuake engine will calculate the conditioned mean and covariance
of the ground shaking following Engler et al. (2022), and then
simulate the requested number of ground motion fields

Notation:

_D:
  subscript refers to the "Data" or observations
_Y:
  subscript refers to the target sites
yD:
  recorded values at the stations
var_addon_D:
  additional sigma for the observations that are uncertain,
  which might arise if the values for this particular IMT were not directly
  recorded, but obtained by conversion equations or cross-correlation functions
mu_yD:
  predicted mean intensity at the observation points, from the specified GMM(s)
phi_D:
  predicted within-event uncertainty at the observation points, from the
  specified GMM(s)
tau_D:
  predicted between-event uncertainty at the observation points, from the
  specified GMM(s)
zeta_D:
  raw residuals at the observation points
cov_WD_WD:
  station data within-event covariance matrix, with the additional
  variance of the residuals for the cases where the station data is uncertain
cov_WD_WD_inv:
  (pseudo)-inverse of the station data within-event covariance matrix
corr_HD_HD:
  cross-intensity measure correlations for the observed intensity measures
mu_HD_yD:
  posterior mean of the (normalized) between-event residual
cov_HD_HD_yD:
  posterior covariance of the (normalized) between-event residual
mu_BD_yD:
  posterior mean of the between-event residual
cov_BD_BD_yD:
  posterior covariance of the conditional between-event residual
nominal_bias_mean:
  mean of mu_BD_yD, useful as a single value measure of the event bias,
  particularly in the heteroscedastic case
nominal_bias_stddev:
  sqrt of the mean of cov_BD_BD_yD
mu_Y:
  predicted mean of the intensity at the target sites
phi_Y:
  predicted within-event standard deviation at the target sites
tau_Y:
  predicted between-event standard deviation at the target
  sites
mu_BY_yD:
  mean of the conditional between-event residual for the target sites
cov_WY_WD and cov_WD_WY:
   within-event covariance matrices for the target sites and observation sites
cov_WY_WY:
  apriori within-event covariance matrix for the target sites
RC:
  regression coefficient matrix ("RC" = cov_WY_WD × cov_WD_WD_inv)
C:
  scaling matrix for the conditioned between-event covariance matrix
cov_WY_WY_wD:
  conditioned within-event covariance matrix for the target sites
cov_BY_BY_yD:
  "conditioned between-event" covariance matrix for the target sites
mu_Y_yD:
  conditioned mean of the ground motion at the target sites
cov_Y_Y_yD:
  conditional covariance of the ground motion at the target sites
"""

import logging
from dataclasses import dataclass, replace
from collections import namedtuple

import psutil
import numpy
import pandas
from openquake.baselib import performance
from openquake.hazardlib.truncated_mvn import TruncatedMVN
from openquake.hazardlib.calc.gmf import GmfComputer, TRUNCATION_THRESHOLD
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCorrelationModel)
from openquake.hazardlib.correlation_models.cross_imt.baker_jayaram_2008 \
    import BakerJayaram2008
from openquake.hazardlib.correlation_models.cross_imt.goda_atkinson_2009 \
    import GodaAtkinson2009
from openquake.hazardlib.correlation_models.spatial.jayaram_baker_2009 \
    import JayaramBaker2009
from openquake.hazardlib.geo.geodetic import geodetic_distance

U32 = numpy.uint32
F32 = numpy.float32

Precomputed = namedtuple('Precomputed', 'ctx_Y ctx_D YY YD DY DD conditioners')
MAX_CONDITIONING_BLOCK_ELEMENTS = 8_000_000


def conditionable_imts(imts):
    """Return the IMTs supported by ground-motion conditioning."""
    return [imt for imt in imts if imt.string != 'MMI']


def get_precomputed(rupture, cmaker, inp, compute_covs=True):
    """
    :param compute_covs: build matrices required only for random fields
    :returns: (ctx_Y, ctx_D, dist)
    """
    if hasattr(rupture, 'rupture'):
        rupture = rupture.rupture

    # Generate the contexts for stations sites and target sites
    [ctx_D] = cmaker.get_ctxs([rupture], inp.sites_D)
    [ctx_Y] = cmaker.get_ctxs([rupture], inp.sites_Y)

    # filter sites
    mask_Y = numpy.isin(inp.sites_Y.sids, ctx_Y.sids)
    inp.sites_Y = inp.sites_Y.filter(mask_Y)
    mask_D = numpy.isin(inp.sites_D.sids, ctx_D.sids)
    inp.sites_D = inp.sites_D.filter(mask_D)
    inp.stations = inp.stations[mask_D].copy()

    if compute_covs:
        YY = compute_distance_matrix(inp.sites_Y, inp.sites_Y)
        DY = compute_distance_matrix(inp.sites_D, inp.sites_Y)
    else:
        YY = DY = None
    joint_model = not isinstance(
        inp.within_event_model, SpatialCorrelationModel)
    if compute_covs or not joint_model:
        YD = compute_distance_matrix(inp.sites_Y, inp.sites_D)
    else:
        YD = None
    DD = compute_distance_matrix(inp.sites_D, inp.sites_D)
    return Precomputed(ctx_Y, ctx_D, YY, YD, DY, DD, [])


class NoInterIntraStdDevs(Exception):
    def __init__(self, gsim):
        self.gsim = gsim

    def __str__(self):
        return """\
You cannot use the conditioned ground shaking module with the GSIM %s,
that defines only the total standard deviation. If you wish to use the
conditioned ground shaking module you have to select a GSIM that provides
the inter and intra event standard deviations, or use the ModifiableGMPE
with `add_between_within_stds.with_betw_ratio`.
""" % self.gsim.__class__.__name__


class ConditionedGmfComputer(GmfComputer):
    """
    Given an earthquake rupture, and intensity observations from
    recording station data, the conditioned ground motion field computer
    computes ground shaking over a set of sites, by randomly sampling a
    ground shaking intensity model whose mean and within-event and
    between-event terms have been conditioned upon the observations.

    NB: using truncation_level = 0 totally disables the random part
    and the generated GMFs become deterministic (equal for all events).

    :param rupture:
        Rupture to calculate ground motion fields radiated from.

    :param :class:`openquake.hazardlib.site.SiteCollection` target_sitecol:
        the hazard sites excluding the stations

    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance

    :param within_event_model:
        Instance of a within-event correlation model object. See
        :mod:`openquake.hazardlib.correlation_models`. Can be ``None``, in which
        case non-correlated ground motion fields are calculated.
        Correlation model is not used if ``truncation_level`` is zero.

    :param between_event_model:
        Instance of a between-event correlation model object. See
        :mod:`openquake.hazardlib.correlation_models`. Can be ``None``, in which
        case non-cross-correlated ground motion fields are calculated.

    :param amplifier:
        None or an instance of Amplifier

    :param sec_perils:
        Tuple of secondary perils. See
        :mod:`openquake.hazardlib.sep`. Can be ``None``, in which
        case no secondary perils need to be evaluated.
    """
    def __init__(
            self, rupture, sitecol, station_sitecol, station_data,
            observed_imts, cmaker, within_event_model=None,
            between_event_model=None, within_event_correlation_params=None,
            number_of_ground_motion_fields=1, amplifier=None, sec_perils=(),
            **legacy):
        aliases = {
            'spatial_correl': 'within_event_model',
            'cross_correl_between': 'between_event_model',
            'ground_motion_correlation_params':
            'within_event_correlation_params'}
        values = {
            'within_event_model': within_event_model,
            'between_event_model': between_event_model,
            'within_event_correlation_params':
            within_event_correlation_params}
        for old_name, new_name in aliases.items():
            if old_name in legacy:
                if values[new_name] is not None:
                    raise TypeError(f'Pass only {new_name}')
                values[new_name] = legacy.pop(old_name)
        if legacy:
            raise TypeError('Unknown arguments: %s' % sorted(legacy))
        within_event_model = values['within_event_model']
        between_event_model = values['between_event_model']
        within_event_correlation_params = (
            values['within_event_correlation_params'] or {})
        assert len(station_data) == len(station_sitecol), (
            len(station_data), len(station_sitecol))
        GmfComputer.__init__(
            self, rupture=rupture, sitecol=sitecol, cmaker=cmaker,
            within_event_model=within_event_model,
            between_event_model=between_event_model,
            amplifier=amplifier, sec_perils=sec_perils)

        clust = within_event_correlation_params.get(
            "vs30_clustering", True)
        self.rupture = rupture

        target_imts = conditionable_imts(self.imts)

        self.inp = Input(
            sitecol, station_sitecol,
            target_imts, observed_imts, station_data,
            within_event_model or JayaramBaker2009(clust),
            between_event_model or GodaAtkinson2009(),
            BakerJayaram2008(), self.correlation_context)

    def _compute_mvn(self, mu_Y, cov_WY_WY, cov_BY_BY, E):
        rng = numpy.random.default_rng(self.seed)
        N = len(cov_WY_WY)
        cutoff = F32(self.cmaker.oq.correlation_cutoff)
        cutoff *= numpy.eye(N, dtype=F32)
        # NB: the cutoff is needed to remove negative eigenvalues
        if (self.cmaker.oq.truncated_mvn is False or
                self.cmaker.truncation_level == 99):
            # do not truncate
            cov_Y_Y = cov_WY_WY + cov_BY_BY + cutoff
            # eig0, _ = numpy.linalg.eigh(cov_WY_WY + cov_BY_BY)
            # eig, _ = numpy.linalg.eigh(cov_Y_Y)
            arr = rng.multivariate_normal(
                mu_Y.flatten(), cov_Y_Y, size=E,
                check_valid="raise", tol=1e-5, method="cholesky").T
            return arr

        # NB: truncated MVN is used in the scenario risk tests
        # conditioned_stations, case_21_stations, case_26_stations
        cov_WY_WY = cov_WY_WY + cutoff
        cov_BY_BY = cov_BY_BY + cutoff

        lb_w, ub_w = self.get_symmetric_bounds(cov_WY_WY, self.tlw)
        seed_w = int(rng.integers(0, numpy.iinfo(numpy.int32).max))

        z_w_truncated = TruncatedMVN(
            numpy.zeros(N, F32), cov_WY_WY, F32(lb_w), F32(ub_w), seed=seed_w
        ).sample(E)

        lb_b, ub_b = self.get_symmetric_bounds(cov_BY_BY, self.tlb)
        seed_b = int(rng.integers(0, numpy.iinfo(numpy.int32).max))
        z_b_truncated = TruncatedMVN(
            numpy.zeros(N, F32), cov_BY_BY, F32(lb_b), F32(ub_b), seed=seed_b
        ).sample(E)

        arr = mu_Y.flatten()[:, numpy.newaxis] + z_w_truncated + z_b_truncated
        return arr


@dataclass
class Input:
    """
    Container for the conditioned GMFs parameters
    """
    sites_Y: list = ()
    sites_D: list = ()
    imts_Y: list = ()
    imts_D: list = ()
    stations: pandas.DataFrame = ()
    within_event_model: object = 0
    between_event_model: object = 0
    separable_cross_imt_model: object = 0
    correlation_context: object = None


@dataclass
class StationConditioning:
    """All-IMT station system used by joint Gaussian conditioning."""
    residual_D: numpy.ndarray
    observed_imts: tuple
    latent_imts: tuple
    observation_mask: numpy.ndarray
    observed_imt_indices: numpy.ndarray
    full_phi_D: numpy.ndarray
    phi_D: numpy.ndarray
    tau_D: numpy.ndarray
    A_D: numpy.ndarray
    between_correlation: numpy.ndarray
    covariance_DD: numpy.ndarray
    covariance_DD_inv: numpy.ndarray

    def solve(self, right_hand_side):
        """Apply the precomputed station covariance pseudoinverse."""
        return self.covariance_DD_inv @ right_hand_side


def build_station_conditioning(inp, mean_stds_D, DD):
    """Build the small joint covariance system at observation sites."""
    imts_D = tuple(inp.imts_D)
    num_stations = len(inp.sites_D)
    observed = numpy.array([
        numpy.log(inp.stations[imt.string + '_mean'].to_numpy(float))
        for imt in imts_D])
    observation_stddev = numpy.array([
        inp.stations[imt.string + '_std'].to_numpy(float)
        for imt in imts_D])
    valid = numpy.isfinite(observed) & numpy.isfinite(observation_stddev)
    valid = valid.reshape(-1)
    if not valid.any():
        raise ValueError('The station data contains no usable observations')

    predicted = numpy.asarray(mean_stds_D[0, 0], dtype=numpy.float64)
    tau = numpy.asarray(mean_stds_D[2, 0], dtype=numpy.float64)
    phi = numpy.asarray(mean_stds_D[3, 0], dtype=numpy.float64)
    residual_D = (observed - predicted).reshape(-1)[valid]
    tau_D = tau.reshape(-1)[valid]
    phi_D = phi.reshape(-1)[valid]

    latent_imts = tuple(dict.fromkeys([*inp.imts_Y, *imts_D]))
    latent_index = {imt: i for i, imt in enumerate(latent_imts)}
    observed_imt_indices = numpy.repeat(
        [latent_index[imt] for imt in imts_D], num_stations)[valid]
    A_D = numpy.zeros(
        (len(residual_D), len(latent_imts)), dtype=numpy.float64)
    A_D[numpy.arange(len(residual_D)), observed_imt_indices] = tau_D

    full_phi = phi.reshape(-1)
    within_DD = compute_within_event_covariance_matrix(
        inp.within_event_model, inp.separable_cross_imt_model, DD,
        imts_D, imts_D, full_phi, full_phi,
        inp.correlation_context)
    within_DD = numpy.asarray(within_DD, dtype=numpy.float64)
    within_DD = within_DD[numpy.ix_(valid, valid)]
    observation_variance = observation_stddev.reshape(-1)[valid] ** 2
    numpy.fill_diagonal(
        within_DD, numpy.diag(within_DD) + observation_variance)

    between_correlation = numpy.asarray(
        inp.between_event_model.correlation_matrix(latent_imts),
        dtype=numpy.float64)
    covariance_DD = within_DD + A_D @ between_correlation @ A_D.T
    covariance_DD_inv = numpy.linalg.pinv(covariance_DD, hermitian=True)
    return StationConditioning(
        residual_D, imts_D, latent_imts, valid, observed_imt_indices,
        full_phi, phi_D, tau_D, A_D, between_correlation, covariance_DD,
        covariance_DD_inv)


@dataclass
class JointConditioning:
    """Dense reference representation of an all-IMT target posterior."""
    mean_Y: numpy.ndarray
    covariance_YY: numpy.ndarray
    covariance_YD: numpy.ndarray
    station: StationConditioning

    def mean_covariance(self):
        mean = self.mean_Y + self.covariance_YD @ self.station.solve(
            self.station.residual_D)
        if self.covariance_YY is None:
            return mean, None
        solved_DY = self.station.solve(self.covariance_YD.T)
        covariance = self.covariance_YY - self.covariance_YD @ solved_DY
        covariance = (covariance + covariance.T) / 2
        return mean, covariance

    def condition(self, unconditional_Y, unconditional_D):
        """Apply Matheron substitution to unconditional prior samples."""
        correction = self.station.solve(
            self.station.residual_D[:, None] - unconditional_D)
        return (self.mean_Y[:, None] + unconditional_Y +
                self.covariance_YD @ correction)

    def sample(self, rng, num_events, cutoff=0):
        """Draw an exact dense Gaussian posterior reference sample."""
        covariance_YY = self.covariance_YY.copy()
        numpy.fill_diagonal(
            covariance_YY, numpy.diag(covariance_YY) + cutoff)
        prior = numpy.block([
            [covariance_YY, self.covariance_YD],
            [self.covariance_YD.T, self.station.covariance_DD]])
        prior = (prior + prior.T) / 2
        factor = numpy.linalg.cholesky(prior)
        samples = factor @ rng.standard_normal(
            (len(prior), num_events))
        num_targets = len(self.mean_Y)
        return self.condition(
            samples[:num_targets], samples[num_targets:])


def build_joint_conditioning(inp, mean_stds_Y, station, YY, YD):
    """Build a dense all-IMT target prior and target-station block."""
    imts_Y = tuple(inp.imts_Y)
    num_targets = len(inp.sites_Y)
    mean_Y = numpy.asarray(
        mean_stds_Y[0, 0], dtype=numpy.float64).reshape(-1)
    tau_Y = numpy.asarray(
        mean_stds_Y[2, 0], dtype=numpy.float64).reshape(-1)
    phi_Y = numpy.asarray(
        mean_stds_Y[3, 0], dtype=numpy.float64).reshape(-1)

    latent_index = {imt: i for i, imt in enumerate(station.latent_imts)}
    target_imt_indices = numpy.repeat(
        [latent_index[imt] for imt in imts_Y], num_targets)
    A_Y = numpy.zeros(
        (len(mean_Y), len(station.latent_imts)), dtype=numpy.float64)
    A_Y[numpy.arange(len(mean_Y)), target_imt_indices] = tau_Y

    if YY is None:
        within_YY = None
    else:
        within_YY = compute_within_event_covariance_matrix(
            inp.within_event_model, inp.separable_cross_imt_model, YY,
            imts_Y, imts_Y, phi_Y, phi_Y, inp.correlation_context)
    within_YD = compute_within_event_covariance_matrix(
        inp.within_event_model, inp.separable_cross_imt_model, YD,
        imts_Y, station.observed_imts, phi_Y,
        station.full_phi_D,
        inp.correlation_context)
    within_YD = numpy.asarray(within_YD, dtype=numpy.float64)
    within_YD = within_YD[:, station.observation_mask]

    between = station.between_correlation
    if within_YY is None:
        covariance_YY = None
    else:
        covariance_YY = numpy.asarray(within_YY, dtype=numpy.float64)
        covariance_YY += A_Y @ between @ A_Y.T
    covariance_YD = within_YD + A_Y @ between @ station.A_D.T
    return JointConditioning(
        mean_Y, covariance_YY, covariance_YD, station)


def conditioned_mean_in_chunks(
        inp, mean_stds_Y, station,
        max_block_elements=MAX_CONDITIONING_BLOCK_ELEMENTS):
    """Compute the exact all-IMT posterior mean in target-site chunks."""
    M = len(inp.imts_Y)
    N = len(inp.sites_Y)
    D = len(inp.sites_D)
    J = len(inp.imts_D)
    chunk_size = max(1, max_block_elements // (M * J * D))
    mean = numpy.empty((M, N), dtype=numpy.float64)
    for start in range(0, N, chunk_size):
        stop = min(start + chunk_size, N)
        site_ids = inp.sites_Y.sids[start:stop]
        sites_Y = inp.sites_Y.filtered(site_ids)
        chunk_inp = replace(inp, sites_Y=sites_Y)
        chunk_stats = mean_stds_Y[:, :, :, start:stop]
        distances = compute_distance_matrix(sites_Y, inp.sites_D)
        joint = build_joint_conditioning(
            chunk_inp, chunk_stats, station, None, distances)
        chunk_mean, _ = joint.mean_covariance()
        mean[:, start:stop] = chunk_mean.reshape(M, stop - start)
    return mean


@dataclass
class DResult:
    """
    Temporary data structure used inside get_mean_covs
    """
    g: int
    m: int
    imt: str
    bracketed_imts: list
    conditioning_imts: list
    native_data_available: bool
    corr_HD_HD: numpy.ndarray = 0
    cov_WD_WD_inv: numpy.ndarray = 0
    phi_D: numpy.ndarray = 0
    T_D: numpy.ndarray = 0
    zeta_D: numpy.ndarray = 0


def _createD(g, m, target_imt, imts_D, sdata):
    # returns (g, m, conditioning_imts, bracketed_imts, native_data_available)

    native_data_available = False

    if target_imt in imts_D:
        # Target IMT is present in the observed IMTs
        conditioning_imts = [target_imt]
        bracketed_imts = conditioning_imts
        native_data_available = True
    else:
        # Find where the target IMT falls in the list of observed IMTs
        all_imts = sorted(imts_D + [target_imt])
        imt_idx = numpy.where(
            target_imt.string == numpy.array(all_imts)[:, 0])[0][0]
        if imt_idx == 0:
            # Target IMT is outside the range of the observed IMT periods
            # and its period is lower than the lowest available in the
            # observed IMTs
            conditioning_imts = [all_imts[1]]
        elif imt_idx == len(all_imts) - 1:
            # Target IMT is outside the range of the observed IMT periods
            # and its period is higher than the highest available in the
            # observed IMTs
            conditioning_imts = [all_imts[-2]]
        else:
            # Target IMT is within the range of the observed IMT periods
            # and its period falls between two periods in the observed IMTs
            conditioning_imts = [all_imts[imt_idx - 1],
                                 all_imts[imt_idx + 1]]
        bracketed_imts = [target_imt] + conditioning_imts

    # Check if the station data for the IMTs shortlisted for conditioning
    # contains NaNs
    for conditioning_imt in conditioning_imts:
        num_null_values = sdata[
            conditioning_imt.string + "_mean"].isna().sum()
        if num_null_values:
            raise ValueError(
                f"The station data contains {num_null_values}"
                f" null values for {target_imt.string}."
                " Please fill or discard these rows.")
    t = DResult(g, m, target_imt, bracketed_imts, conditioning_imts,
                native_data_available)
    return t


def createD(g, m, target_imt, inp, mean_stds_D, DD):
    """
    :returns: a DResult object containing correlation matrices of size DxD
    """
    sdata = {}
    for im, ms in zip(inp.imts_D, mean_stds_D.transpose(2, 0, 1, 3)):
        sdata[im.string + "_mean"] = inp.stations[im.string + "_mean"]
        sdata[im.string + "_std"] = inp.stations[im.string + "_std"]
        sdata[im.string + "_median"] = ms[0, 0]
        sdata[im.string + "_sigma"] = ms[1, 0]
        sdata[im.string + "_tau"] = ms[2, 0]
        sdata[im.string + "_phi"] = ms[3, 0]
    sdata = pandas.DataFrame(sdata)
    t = _createD(g, m, target_imt, inp.imts_D, sdata)

    # Observations (recorded values at the stations)
    yD = numpy.log(
        sdata[[c_imt.string + "_mean" for c_imt in t.conditioning_imts]]
    ).values.reshape((-1, 1), order="F")

    # Additional sigma for the observations that are uncertain
    # These arise if the values for this particular IMT were not
    # directly recorded, but obtained by conversion equations or
    # cross-correlation functions
    var_addon_D = sdata[
        [c_imt.string + "_std" for c_imt in t.conditioning_imts]
    ].values.reshape(-1, order="F") ** 2

    # Predicted mean at the observation points, from GSIM(s)
    mu_yD = sdata[
        [c_imt.string + "_median" for c_imt in t.conditioning_imts]
    ].values.reshape((-1, 1), order="F")
    # Predicted uncertainty components at the observation points
    # from GSIM(s)
    phi_D = sdata[
        [c_imt.string + "_phi" for c_imt in t.conditioning_imts]
    ].values.reshape((-1, 1), order="F")
    tau_D = sdata[
        [c_imt.string + "_tau" for c_imt in t.conditioning_imts]
    ].values.reshape((-1, 1), order="F")

    if t.native_data_available:
        t.T_D = tau_D
    else:
        nss = len(inp.sites_D)  # number of station sites
        t.T_D = numpy.zeros(
            (len(t.conditioning_imts) * nss, len(t.bracketed_imts)))
        for i in range(len(t.conditioning_imts)):
            t.T_D[i * nss: (i + 1) * nss, i + 1] = tau_D[
                i * nss: (i + 1) * nss, 0]

    # The raw residuals
    t.zeta_D = yD - mu_yD
    t.phi_D = phi_D.flatten()

    cov_WD_WD = compute_within_event_covariance_matrix(
        inp.within_event_model, inp.separable_cross_imt_model, DD,
        t.conditioning_imts, t.conditioning_imts, t.phi_D, t.phi_D,
        inp.correlation_context)

    # Add on the additional variance of the residuals
    # for the cases where the station data is uncertain
    numpy.fill_diagonal(cov_WD_WD, numpy.diag(cov_WD_WD) + var_addon_D)

    # Get the (pseudo)-inverse of the station data within-event covariance
    # matrix
    t.cov_WD_WD_inv = numpy.linalg.pinv(cov_WD_WD)

    # # The normalized between-event residual and its variance (for the
    # # observation points)
    # # Engler et al. (2022) equations 12 and 13; assumes between event
    # # residuals are perfectly cross-correlated
    # var_H_y2 = 1.0 / (
    #     1.0 + tau_y2.T @ cov_W2_W2_inv @ tau_y2
    # )
    # mu_H_y2 = tau_y2.T @ cov_W2_W2_inv @ zeta * var_H_y2
    # The more generic equations B8 and B9 from Appendix B are used instead
    # requiring the computation of the covariance matrix Σ_HD_HD, which is
    # just the matrix of cross-correlations for the observed IMTs, since
    # H is the normalized between-event residual
    t.corr_HD_HD = inp.between_event_model.correlation_matrix(
        t.bracketed_imts)
    return t


def compute_distance_matrix(sites1, sites2):
    """
    :param sites1: N1 sites
    :param sites2: N2 sites
    :returns:
       a matrix of shape N1 x N2 of float32 distances (~37 GB for 100k sites)
    """
    avail_gb = psutil.virtual_memory().available / 1024**3
    req_gb = len(sites1) * len(sites2) * 8 / 1024**3
    if req_gb > avail_gb:
        raise MemoryError('The distance_matrix of shape (%d, %d) is too large!'
                          % (len(sites1), len(sites2)))
    distance_matrix = geodetic_distance(
        sites1.lons.reshape(-1, 1), sites1.lats.reshape(-1, 1),
        sites2.lons, sites2.lats)
    return distance_matrix


# called only by _get_separable_correlation_matrix
def _get_separable_correlation_block(
        imt_1, imt_2, spatial_model, cross_imt_model, distance_matrix):
    if imt_1 == imt_2:
        # since we have a single IMT, there are no cross-correlation terms
        return spatial_model.correlation_matrix(distance_matrix, imt_1)
    matrix1 = spatial_model.correlation_matrix(distance_matrix, imt_1)
    matrix2 = spatial_model.correlation_matrix(distance_matrix, imt_2)
    spatial_correlation_matrix = numpy.maximum(matrix1, matrix2)
    cross_corr_coeff = cross_imt_model.rho(imt_1, imt_2)
    return spatial_correlation_matrix * F32(cross_corr_coeff)


def _get_separable_correlation_matrix(
        spatial_model, cross_imt_model, distance_matrix, imts1, imts2):
    # The correlation structure for IMs of differing types at differing
    # locations can be reasonably assumed as Markovian in nature, and we
    # assume here that the correlation between differing IMs at differing
    # locations is simply the product of the cross correlation of IMs i and j
    # at the same location and the spatial correlation due to the distance
    # between sites m and n. This branch retains that historical approximation
    # for spatial-only models.
    rho = [[_get_separable_correlation_block(
        imt_1, imt_2, spatial_model, cross_imt_model, distance_matrix)
            for imt_2 in imts2] for imt_1 in imts1]
    return numpy.block(rho)


def compute_within_event_covariance_matrix(
        within_event_model, separable_cross_imt_model, distance_matrix,
        imts1, imts2, stddev1, stddev2, context=None):
    """Return a scaled within-event covariance block.

    Spatial-only models retain the historical separable approximation.
    Joint models supply the spatial cross-IMT correlation directly.
    """
    if isinstance(within_event_model, SpatialCorrelationModel):
        covariance = _get_separable_correlation_matrix(
            within_event_model, separable_cross_imt_model,
            distance_matrix, imts1, imts2)
    else:
        covariance = within_event_model.correlation_block(
            distance_matrix, imts1, imts2,
            ResidualComponent.WITHIN_EVENT, context)
    expected = (
        len(imts1) * distance_matrix.shape[0],
        len(imts2) * distance_matrix.shape[1])
    if covariance.shape != expected:
        raise ValueError(
            f'Expected within-event correlation shape {expected}, got '
            f'{covariance.shape}')
    covariance = numpy.array(covariance, dtype=F32, copy=True)
    covariance *= stddev1.astype(F32)[:, numpy.newaxis]
    covariance *= stddev2.astype(F32)[numpy.newaxis, :]
    return covariance


# In scenario/case_21 one has
# target_imt = PGA = imts_Y = imts_D
# ctx_Y with 571 elements, like target_sitecol
# station_data has 140 elements like station_sitecol
# 18 sites are discarded
# the total sitecol has 571 + 140 + 18 = 729 sites
# NB: this is run in parallel
class Conditioner:
    def __init__(self, g, gsim, inp, mean_stds, mean_stds_D):
        self.args = (g, gsim, inp, mean_stds, mean_stds_D)

    @property
    def g(self):
        return self.args[0]

    @property
    def gsim(self):
        return self.args[1]

    @property
    def inp(self):
        return self.args[2]

    @property
    def mean_stds_Y(self):
        return self.args[3]

    @property
    def mean_stds_D(self):
        return self.args[4]

    # Using Bayes rule, compute the posterior distribution of the
    # normalized between-event residual H|YD=yD, employing
    # Engler et al. (2022), eqns B8 and B9 (also B18 and B19),
    # H|Y2=y2 is normally distributed with mean and covariance
    def get_mu_tau_phi(self, m, target_imt, monitor, compute_covs=True):
        # NB: mean_stds matrices have shape (4, 1, M, N)
        g, gsim, inp, mean_stds, mean_stds_D = self.args

        # build temporary matrices of shape DD (#stations)
        with monitor.shared['DD'] as DD:
            t = createD(g, m, target_imt, inp, mean_stds_D, DD)

        cov_HD_HD_yD = numpy.linalg.pinv(
            t.T_D.T @ t.cov_WD_WD_inv @ t.T_D +
            numpy.linalg.pinv(t.corr_HD_HD))

        mu_HD_yD = cov_HD_HD_yD @ t.T_D.T @ t.cov_WD_WD_inv @ t.zeta_D

        # Compute the distribution of the conditional between-event
        # residual B|Y2=y2
        mu_BD_yD = t.T_D @ mu_HD_yD
        cov_BD_BD_yD = t.T_D @ cov_HD_HD_yD @ t.T_D.T

        # Get the nominal bias and its standard deviation as the means of the
        # conditional between-event residual mean and standard deviation
        nominal_bias_mean = numpy.mean(mu_BD_yD)
        nominal_bias_stddev = numpy.sqrt(numpy.mean(numpy.diag(cov_BD_BD_yD)))

        msg = ("GSIM: %s, IMT: %s, Nominal bias mean: %.3f, "
               "Nominal bias stddev: %.3f" % (
                   gsim.gmpe if hasattr(gsim, 'gmpe') else gsim,
                   t.imt, nominal_bias_mean, nominal_bias_stddev))

        # Predicted mean at the target sites, from GSIM
        mu_Y = mean_stds[0, 0, m, :, numpy.newaxis]

        # Predicted uncertainty components at the target sites, from GSIM
        tau_Y = mean_stds[2, 0, m, :, numpy.newaxis]
        phi_Y = mean_stds[3, 0, m]

        # Compute the within-event covariance matrices for the
        # target sites and observation sites; the shapes are
        # (nsites, nstations) and (nstations, nsites) respectively
        with monitor.shared['YD'] as YD:
            cov_WY_WD = compute_within_event_covariance_matrix(
                inp.within_event_model, inp.separable_cross_imt_model, YD,
                [t.imt], t.conditioning_imts, phi_Y, t.phi_D,
                inp.correlation_context)

        # Compute the regression coefficient matrix [cov_WY_WD × cov_WD_WD_inv]
        RC = cov_WY_WD @ t.cov_WD_WD_inv  # shape (nsites, nstations)

        # Compute the conditioned mean of the ground motion
        # at the target sites; shape (nsites, 1)
        mu_Y_yD = (mu_Y + tau_Y @ mu_HD_yD[0, numpy.newaxis] +
                   RC @ (t.zeta_D - mu_BD_yD)).astype(F32)

        if not compute_covs:
            return mu_Y_yD, None, None, msg

        cov_WY_WY_wD, cov_BY_BY_yD = _compute_target_covs(
            t, inp, phi_Y, tau_Y, RC, cov_HD_HD_yD, monitor)
        return mu_Y_yD, cov_WY_WY_wD, cov_BY_BY_yD, msg


def _compute_target_covs(
        t, inp, phi_Y, tau_Y, RC, cov_HD_HD_yD, monitor):
    """Compute the covariance matrices required for random fields."""
    with monitor.shared['DY'] as DY:
        cov_WD_WY = compute_within_event_covariance_matrix(
            inp.within_event_model, inp.separable_cross_imt_model, DY,
            t.conditioning_imts, [t.imt], t.phi_D, phi_Y,
            inp.correlation_context)

    # This is the dominant piece, both in time and memory.
    with (monitor.shared['YY'] as YY,
          monitor('computing cov_Y_Y', measuremem=True)):
        cov_WY_WY = compute_within_event_covariance_matrix(
            inp.within_event_model, inp.separable_cross_imt_model, YY,
            [t.imt], [t.imt], phi_Y, phi_Y,
            inp.correlation_context)

        # Conditioned within-event covariance, clipped to zero.
        cov_WY_WY_wD = (cov_WY_WY - RC @ cov_WD_WY).clip(
            min=0).astype(F32)

        # Scaling matrix for the conditioned between-event covariance.
        if t.native_data_available:
            C = (tau_Y - RC @ t.T_D).astype(F32)
        else:
            N = len(inp.sites_Y)
            zeros = numpy.zeros((N, len(t.conditioning_imts)), F32)
            C = (numpy.block([tau_Y, zeros]) - RC @ t.T_D).astype(F32)

        # Conditioned between-event covariance, clipped to zero.
        cov_BY_BY_yD = (C @ cov_HD_HD_yD.astype(F32) @ C.T).clip(min=0)
    return cov_WY_WY_wD, cov_BY_BY_yD


def build_precomputed(rupture, cmaker, inp, compute_covs=True):
    """
    :param rupture: hazardlib rupture
    :param cmaker: ContextMaker
    :param inp: Input with sites, imts, stations and correlation params
    :param compute_covs: build matrices required only for random fields
    :return: Precomputed(ctx_Y, ctx_D, YY, YD, DY, DD, mtp_args) tuple
    """
    pre = get_precomputed(rupture, cmaker, inp, compute_covs)
    for g, gsim in enumerate(cmaker.gsims):
        if gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == {StdDev.TOTAL}:
            if not (type(gsim).__name__ == "ModifiableGMPE"
                    and "add_between_within_stds" in gsim.kwargs):
                raise NoInterIntraStdDevs(gsim)

        # NB: there are relatively few stations, so cm.get_mean_stds([ctx_D])
        # is fast and done sequentially, while ctx_Y is done in parallel
        gdict = {gsim: cmaker.gsims[gsim]}
        cm_D = cmaker.copy(imtls={im.string: [0] for im in inp.imts_D},
                           gsims=gdict)
        mean_stds_D = cm_D.get_mean_stds([pre.ctx_D])
        cm_Y = cmaker.copy(
            imtls={imt.string: [0] for imt in inp.imts_Y}, gsims=gdict)
        mean_stds_Y = cm_Y.get_mean_stds([pre.ctx_Y])  # fast enough
        pre.conditioners.append(Conditioner(
            g, gsim, inp, mean_stds_Y, mean_stds_D))
    return pre


def use_joint_conditioning(computer):
    """Return whether the exact joint Gaussian path is applicable."""
    joint_model = not isinstance(
        computer.inp.within_event_model, SpatialCorrelationModel)
    gaussian = (computer.cmaker.oq.truncated_mvn is False or
                (computer.tlw == 99 and computer.tlb == 99))
    return joint_model and gaussian


def conditioned_joint(computer, conditioner, monitor, compute_covs):
    """Return jointly conditioned Gaussian fields for every target IMT."""
    with monitor.shared['DD'] as DD:
        station = build_station_conditioning(
            conditioner.inp, conditioner.mean_stds_D, DD)
    if compute_covs:
        with monitor.shared['YD'] as YD:
            with monitor.shared['YY'] as YY:
                joint = build_joint_conditioning(
                    conditioner.inp, conditioner.mean_stds_Y,
                    station, YY, YD)

    E = computer.E // len(computer.cmaker.gsims)
    M = len(conditioner.inp.imts_Y)
    N = len(conditioner.inp.sites_Y)
    if M != computer.M:
        raise ValueError('MMI cannot be combined with conditioned GMFs')
    MNE = numpy.zeros((M, N, E + 1), F32)
    if compute_covs:
        mean, _covariance = joint.mean_covariance()
        rng = numpy.random.default_rng(computer.seed)
        samples = joint.sample(
            rng, E, computer.cmaker.oq.correlation_cutoff)
        MNE[:, :, :E] = samples.reshape(M, N, E)
    else:
        mean = conditioned_mean_in_chunks(
            conditioner.inp, conditioner.mean_stds_Y, station)
        MNE[:, :, :E] = mean[:, :, None]
    MNE[:, :, E] = mean.reshape(M, N)
    return {conditioner.g: MNE}


def conditioned(computer, conditioner, monitor):
    """
    Run the conditioner object and returns meaMNE
    """
    E = computer.E // len(computer.cmaker.gsims)
    MNE = numpy.zeros((computer.M, computer.N, E + 1), F32)
    g = conditioner.g
    compute_covs = max(computer.tlw, computer.tlb) > TRUNCATION_THRESHOLD
    if use_joint_conditioning(computer):
        return conditioned_joint(
            computer, conditioner, monitor, compute_covs)
    for m, imt in enumerate(conditioner.inp.imts_Y):
        mu, ta, ph, _msg = conditioner.get_mu_tau_phi(
            m, imt, monitor, compute_covs)
        if not compute_covs:
            MNE[m, :, :E] = mu.repeat(E, axis=1)
        else:
            MNE[m, :, :E] = computer._compute_mvn(mu, ta, ph, E)
        MNE[m, :, E] = mu[:, 0]  # shape (N, 1) -> N
    return {g: MNE}


# used only in openquake/hazardlib/tests/calc/conditioned_gmfs_test.py
def get_mean_covs(rupture, cmaker, inp, sigma=True):
    """
    :returns: a list of arrays [mea, sig, tau, phi] or [mea, tau, phi]
    """
    pre = build_precomputed(rupture, cmaker, inp)
    G = len(cmaker.gsims)
    M = len(inp.imts_Y)
    N = len(pre.ctx_Y)
    me = numpy.zeros((G, M, N, 1), F32)
    ta = numpy.zeros((G, M, N, N), F32)
    ph = numpy.zeros((G, M, N, N), F32)
    monitor = performance.Monitor()
    monitor.set_shared(YY=pre.YY, YD=pre.YD, DY=pre.DY, DD=pre.DD)
    for cond in pre.conditioners:
        for m, imt in enumerate(inp.imts_Y):
            mu, tau, phi, msg = cond.get_mu_tau_phi(m, imt, monitor)
            me[cond.g, m] = mu
            ta[cond.g, m] = tau
            ph[cond.g, m] = phi
            logging.info(msg)
    if sigma:
        return [me, ta + ph, ta, ph]
    else:
        # save memory since sigma = tau + phi is not needed
        return [me, ta, ph]
