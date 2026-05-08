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
from dataclasses import dataclass
from collections import namedtuple

import psutil
import numpy
import pandas
from openquake.baselib import performance
from openquake.hazardlib.truncated_mvn import TruncatedMVN
from openquake.hazardlib import correlation, cross_correlation
from openquake.hazardlib.calc.gmf import GmfComputer, TRUNCATION_THRESHOLD
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.geo.geodetic import geodetic_distance

U32 = numpy.uint32
F32 = numpy.float32

Precomputed = namedtuple('Precomputed', 'ctx_Y ctx_D YY YD DY DD conditioners')


def get_precomputed(rupture, cmaker, inp):
    """
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

    YY = compute_distance_matrix(inp.sites_Y, inp.sites_Y)
    YD = compute_distance_matrix(inp.sites_Y, inp.sites_D)
    DY = compute_distance_matrix(inp.sites_D, inp.sites_Y)
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

    :param correlation_model:
        Instance of a spatial correlation model object. See
        :mod:`openquake.hazardlib.correlation`. Can be ``None``, in which
        case non-correlated ground motion fields are calculated.
        Correlation model is not used if ``truncation_level`` is zero.

    :param cross_correl:
        Instance of a cross correlation model object. See
        :mod:`openquake.hazardlib.cross_correlation`. Can be ``None``, in which
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
            observed_imts, cmaker, spatial_correl=None,
            cross_correl_between=None, ground_motion_correlation_params=None,
            number_of_ground_motion_fields=1, amplifier=None, sec_perils=()):
        assert len(station_data) == len(station_sitecol), (
            len(station_data), len(station_sitecol))
        GmfComputer.__init__(
            self, rupture=rupture, sitecol=sitecol, cmaker=cmaker,
            correlation_model=spatial_correl,
            cross_correl=cross_correl_between,
            amplifier=amplifier, sec_perils=sec_perils)

        clust = ground_motion_correlation_params.get("vs30_clustering", True)
        self.rupture = rupture

        # Target IMT must be PGA or SA
        target_imts = [imt for imt in self.imts
                       if imt.period or imt.string == "PGA"]

        self.inp = Input(
            sitecol, station_sitecol,
            target_imts, observed_imts, station_data,
            spatial_correl or correlation.JB2009CorrelationModel(clust),
            cross_correl_between or cross_correlation.GodaAtkinson2009(),
            cross_correlation.BakerJayaram2008())

    def _compute_mvn(self, mu_Y, cov_WY_WY, cov_BY_BY, E):
        N = len(cov_WY_WY)
        cutoff = numpy.eye(N) * self.cmaker.oq.correlation_cutoff
        # the cutoff is needed to remove negative eigenvalues
        if (self.cmaker.oq.truncated_mvn is False or
                self.cmaker.truncation_level == 99):
            # do not truncate
            cov_Y_Y = cov_WY_WY + cov_BY_BY + cutoff
            arr = self.rng.multivariate_normal(
                mu_Y.flatten(), cov_Y_Y, size=E,
                check_valid="raise", tol=1e-5, method="cholesky").T
            print(arr.shape)
            return arr

        # NB: truncated MVN is used in the scenario risk tests
        # conditioned_stations, case_21_stations, case_26_stations
        cov_WY_WY = cov_WY_WY + cutoff
        cov_BY_BY = cov_BY_BY + cutoff

        lb_w, ub_w = self.get_symmetric_bounds(cov_WY_WY, self.tlw)
        seed_w = int(self.rng.integers(0, numpy.iinfo(numpy.int32).max))

        z_w_truncated = TruncatedMVN(
            numpy.zeros(N), cov_WY_WY, lb_w, ub_w, seed=seed_w
        ).sample(E)

        lb_b, ub_b = self.get_symmetric_bounds(cov_BY_BY, self.tlb)
        seed_b = int(self.rng.integers(0, numpy.iinfo(numpy.int32).max))
        z_b_truncated = TruncatedMVN(
            numpy.zeros(N), cov_BY_BY, lb_b, ub_b, seed=seed_b
        ).sample(E)

        arr = mu_Y.flatten()[:, None] + z_w_truncated + z_b_truncated
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
    spatial_correl: object = 0
    cross_correl_between: object = 0
    cross_correl_within: object = 0


@dataclass
class TempResult:
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
    phi_D_diag: numpy.ndarray = 0
    T_D: numpy.ndarray = 0
    zeta_D: numpy.ndarray = 0


def _create_temp(g, m, target_imt, imts_D, sdata):
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
    t = TempResult(g, m, target_imt, bracketed_imts, conditioning_imts,
                   native_data_available)
    return t


def create_temp(g, m, target_imt, inp, mean_stds_D, DD):
    """
    :returns: a TempResult
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

    t = _create_temp(g, m, target_imt, inp.imts_D, sdata)

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
    ].values.reshape((-1, 1), order="F") ** 2

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
    t.phi_D_diag = numpy.diag(phi_D.flatten())

    cov_WD_WD = compute_spatial_cross_covariance_matrix(
        inp.spatial_correl, inp.cross_correl_within, DD,
        t.conditioning_imts, t.conditioning_imts, t.phi_D_diag, t.phi_D_diag)

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
    t.corr_HD_HD = inp.cross_correl_between._get_correlation_matrix(
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
        sites1.lons.reshape(sites1.lons.shape + (1,)),
        sites1.lats.reshape(sites1.lats.shape + (1,)),
        sites2.lons,
        sites2.lats)
    return distance_matrix.astype(F32)


def _compute_spatial_cross_correlation_matrix(
        imt_1, imt_2, spatial_correl, cross_correl_within, distance_matrix):
    if imt_1 == imt_2:
        # since we have a single IMT, there are no cross-correlation terms
        return spatial_correl._get_correlation_matrix(distance_matrix, imt_1)
    matrix1 = spatial_correl._get_correlation_matrix(distance_matrix, imt_1)
    matrix2 = spatial_correl._get_correlation_matrix(distance_matrix, imt_2)
    spatial_correlation_matrix = numpy.maximum(matrix1, matrix2)
    cross_corr_coeff = cross_correl_within.get_correlation(imt_1, imt_2)
    return spatial_correlation_matrix * cross_corr_coeff


def compute_spatial_cross_covariance_matrix(
        spatial_correl, cross_correl_within, distance_matrix,
        imts1, imts2, diag1, diag2):
    # The correlation structure for IMs of differing types at differing
    # locations can be reasonably assumed as Markovian in nature, and we
    # assume here that the correlation between differing IMs at differing
    # locations is simply the product of the cross correlation of IMs i and j
    # at the same location and the spatial correlation due to the distance
    # between sites m and n. Can be refactored down the line to support direct
    # spatial cross-correlation models
    rho = numpy.block([[
        _compute_spatial_cross_correlation_matrix(
            imt_1, imt_2, spatial_correl, cross_correl_within, distance_matrix)
        for imt_2 in imts2] for imt_1 in imts1])
    return diag1 @ rho @ diag2


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
    def get_mu_tau_phi(self, m, target_imt, monitor):
        # NB: mean_stds matrices have shape (4, G=1, M=1, N)
        g, gsim, inp, mean_stds, mean_stds_D = self.args

        # build temporary matrices
        with monitor.shared['DD'] as DD:
            t = create_temp(g, m, target_imt, inp, mean_stds_D, DD)

        cov_HD_HD_yD = numpy.linalg.pinv(
            t.T_D.T @ t.cov_WD_WD_inv @ t.T_D + numpy.linalg.pinv(t.corr_HD_HD))

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
        mu_Y = mean_stds[0, 0, 0, :, numpy.newaxis]

        # Predicted uncertainty components at the target sites, from GSIM
        tau_Y = mean_stds[2, 0, 0, :, numpy.newaxis]
        phi_Y_diag = numpy.diag(mean_stds[3, 0, 0])

        # Compute the within-event covariance matrices for the
        # target sites and observation sites; the shapes are
        # (nsites, nstations) and (nstations, nsites) respectively
        with monitor.shared['YD'] as YD:
            cov_WY_WD = compute_spatial_cross_covariance_matrix(
                inp.spatial_correl, inp.cross_correl_within, YD,
                [t.imt], t.conditioning_imts, phi_Y_diag, t.phi_D_diag)

        with monitor.shared['DY'] as DY:
            cov_WD_WY = compute_spatial_cross_covariance_matrix(
                inp.spatial_correl, inp.cross_correl_within, DY,
                t.conditioning_imts, [t.imt], t.phi_D_diag, phi_Y_diag)

        # Compute the regression coefficient matrix [cov_WY_WD × cov_WD_WD_inv]
        RC = cov_WY_WD @ t.cov_WD_WD_inv  # shape (nsites, nstations)

        # # Compute the mean of the conditional between-event residual B|YD=yD
        # # for the target sites
        # mu_HN_yD = mu_HD_yD[0, None]
        # mu_BY_yD = tau_Y @ mu_HN_yD

        # Compute the conditioned mean of the ground motion
        # at the target sites; shape (nsites, 1)
        mu_Y_yD = mu_Y + tau_Y @ mu_HD_yD[0, None] + RC @ (t.zeta_D - mu_BD_yD)

        # Compute the within-event covariance matrix for the
        # target sites (apriori) (nsites, nsites)

        with monitor.shared['YY'] as YY:
            cov_WY_WY = compute_spatial_cross_covariance_matrix(
                inp.spatial_correl, inp.cross_correl_within, YY,
                [t.imt], [t.imt], phi_Y_diag, phi_Y_diag)

        # Both conditioned covariance matrices can contain extremely
        # small negative values due to limitations of floating point
        # operations (~ -10^-17 to -10^-15), these are clipped to zero

        # Compute the conditioned within-event covariance matrix
        # for the target sites clipped to zero, shape (nsites, nsites)
        cov_WY_WY_wD = (cov_WY_WY - RC @ cov_WD_WY).clip(min=0)

        # Compute the scaling matrix "C" for the conditioned between-event
        # covariance matrix
        if t.native_data_available:
            C = tau_Y - RC @ t.T_D
        else:
            zeros = numpy.zeros((len(inp.sites_Y), len(t.conditioning_imts)))
            C = numpy.block([tau_Y, zeros]) - RC @ t.T_D

        # Compute the conditioned between-event covariance matrix
        # for the target sites clipped to zero, shape (nsites, nsites)
        cov_BY_BY_yD = (C @ cov_HD_HD_yD @ C.T).clip(min=0)
        return mu_Y_yD, cov_WY_WY_wD, cov_BY_BY_yD, msg


def build_precomputed(rupture, cmaker, inp):
    """
    :param rupture: hazardlib rupture
    :param cmaker: ContextMaker
    :param inp: Input with sites, imts, stations and correlation params
    :return: Precomputed(ctx_Y, ctx_D, YY, YD, DY, DD, mtp_args) tuple
    """
    pre = get_precomputed(rupture, cmaker, inp)
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
        cm_Y = cmaker.copy(imtls={inp.imts_Y[0].string: [0]}, gsims=gdict)
        mean_stds_Y = cm_Y.get_mean_stds([pre.ctx_Y])  # fast enough
        pre.conditioners.append(Conditioner(
            g, gsim, inp, mean_stds_Y, mean_stds_D))
    return pre


# TODO: switch to 32 bit floats
def getMNE(computer, conditioner, monitor):
    """
    Run the conditioner object and returns meaMNE
    """
    E = computer.E // len(computer.gsims)  # events per realization
    MNE = numpy.zeros((computer.M, computer.N, E + 1), float)
    g = conditioner.g
    for m, imt in enumerate(conditioner.inp.imts_Y):
        mu, ta, ph, _msg = conditioner.get_mu_tau_phi(m, imt, monitor)
        if max(computer.tlw, computer.tlb) <= TRUNCATION_THRESHOLD:
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
    me = numpy.zeros((G, M, N, 1))
    ta = numpy.zeros((G, M, N, N))
    ph = numpy.zeros((G, M, N, N))
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
