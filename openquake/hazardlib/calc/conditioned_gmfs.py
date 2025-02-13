# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 GEM Foundation
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
https://github.com/usgs/shakemap/blob/main/shakemap/coremods/model.py

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
  redicted mean of the intensity at the target sites
phi_Y:
  predicted within-event standard deviation of the intensity at the target sites
tau_Y:
  predicted between-event standard deviation of the intensity at the target
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
from functools import partial
from dataclasses import dataclass

import numpy
from openquake.baselib import parallel
from openquake.hazardlib import correlation, cross_correlation
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.geo.geodetic import geodetic_distance

U32 = numpy.uint32
F32 = numpy.float32

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


class IterationLimitWarning(Warning):
    """
    Iteration limit reached without convergence
    """


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
            observed_imt_strs, cmaker, spatial_correl=None,
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
        self.spatial_correl = (spatial_correl or
                               correlation.JB2009CorrelationModel(clust))
        self.cross_correl_between = (
            cross_correl_between or cross_correlation.GodaAtkinson2009())
        self.cross_correl_within = cross_correlation.BakerJayaram2008()
        self.rupture = rupture
        self.sitecol = sitecol
        self.station_sitecol = station_sitecol
        self.station_data = station_data
        self.observed_imt_strs = observed_imt_strs
        observed_imtls = {imt_str: [0]
                          for imt_str in observed_imt_strs
                          if imt_str not in ["MMI", "PGV"]}
        self.observed_imts = sorted(map(from_string, observed_imtls))
        self.num_events = number_of_ground_motion_fields

    # parallelized
    def get_mea_tau_phi(self, h5):
        """
        :returns: a list of arrays [mea, sig, tau, phi]
        """
        return get_mean_covs(
            self.rupture, self.cmaker,
            self.station_sitecol, self.station_data,
            self.observed_imt_strs, self.sitecol, self.imts,
            self.spatial_correl, self.cross_correl_between, self.cross_correl_within,
            sigma=False, h5=h5)


@dataclass
class TempResult:
    """
    Temporary data structure used inside get_mean_covs
    """
    g: int
    m: int
    bracketed_imts: list
    conditioning_imts: list
    native_data_available: bool
    corr_HD_HD: numpy.ndarray = 0
    cov_WD_WD_inv: numpy.ndarray = 0
    D: numpy.ndarray = 0
    T_D: numpy.ndarray = 0
    zD: numpy.ndarray = 0


def _create_result(g, m, target_imt, observed_imts, station_data_filtered):
    # returns (g, m, conditioning_imts, bracketed_imts, native_data_available)

    native_data_available = False

    if target_imt in observed_imts:
        # Target IMT is present in the observed IMTs
        conditioning_imts = [target_imt]
        bracketed_imts = conditioning_imts
        native_data_available = True
    else:
        # Find where the target IMT falls in the list of observed IMTs
        all_imts = sorted(observed_imts + [target_imt])
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
        num_null_values = station_data_filtered[
            conditioning_imt.string + "_mean"].isna().sum()
        if num_null_values:
            raise ValueError(
                f"The station data contains {num_null_values}"
                f" null values for {target_imt.string}."
                " Please fill or discard these rows.")
    t = TempResult(g, m, bracketed_imts, conditioning_imts, native_data_available)
    return t


def create_result(g, m, target_imt, target_imts, observed_imts,
                  station_data, sitecol, station_sitecol,
                  compute_cov, cross_correl_between):
    """
    :returns: a TempResult
    """
    t = _create_result(g, m, target_imt, observed_imts, station_data)

    # Observations (recorded values at the stations)
    yD = numpy.log(
        station_data[
            [c_imt.string + "_mean" for c_imt in t.conditioning_imts]]
    ).values.reshape((-1, 1), order="F")

    # Additional sigma for the observations that are uncertain
    # These arise if the values for this particular IMT were not
    # directly recorded, but obtained by conversion equations or
    # cross-correlation functions
    var_addon_D = station_data[
        [c_imt.string + "_std" for c_imt in t.conditioning_imts]
    ].values.reshape((-1, 1), order="F") ** 2

    # Predicted mean at the observation points, from GSIM(s)
    mu_yD = station_data[
        [c_imt.string + "_median" for c_imt in t.conditioning_imts]
    ].values.reshape((-1, 1), order="F")
    # Predicted uncertainty components at the observation points
    # from GSIM(s)
    phi_D = station_data[
        [c_imt.string + "_phi" for c_imt in t.conditioning_imts]
    ].values.reshape((-1, 1), order="F")
    tau_D = station_data[
        [c_imt.string + "_tau" for c_imt in t.conditioning_imts]
    ].values.reshape((-1, 1), order="F")

    if t.native_data_available:
        t.T_D = tau_D
    else:
        nss = len(station_sitecol)  # number of station sites
        t.T_D = numpy.zeros(
            (len(t.conditioning_imts) * nss, len(t.bracketed_imts)))
        for i in range(len(t.conditioning_imts)):
            t.T_D[i * nss: (i + 1) * nss, i + 1] = tau_D[
                i * nss: (i + 1) * nss, 0]

    # The raw residuals
    t.zD = yD - mu_yD
    t.D = numpy.diag(phi_D.flatten())

    cov_WD_WD = compute_cov(station_sitecol, station_sitecol,
                            t.conditioning_imts, t.conditioning_imts, t.D, t.D)

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
    #     1.0 + numpy.linalg.multi_dot([tau_y2.T, cov_W2_W2_inv, tau_y2])
    # )
    # mu_H_y2 = numpy.linalg.multi_dot(
    #   [tau_y2.T, cov_W2_W2_inv, zeta]) * var_H_y2
    # The more generic equations B8 and B9 from Appendix B are used instead
    # requiring the computation of the covariance matrix Σ_HD_HD, which is
    # just the matrix of cross-correlations for the observed IMTs, since
    # H is the normalized between-event residual
    t.corr_HD_HD = cross_correl_between._get_correlation_matrix(
        t.bracketed_imts)
    return t


def compute_spatial_cross_covariance_matrix(
        spatial_correl, cross_correl_within, sites1, sites2,
        imts1, imts2, diag1, diag2):
    # The correlation structure for IMs of differing types at differing
    # locations can be reasonably assumed as Markovian in nature, and we
    # assume here that the correlation between differing IMs at differing
    # locations is simply the product of the cross correlation of IMs i and j
    # at the same location and the spatial correlation due to the distance
    # between sites m and n. Can be refactored down the line to support direct
    # spatial cross-correlation models
    distance_matrix = geodetic_distance(
        sites1.lons.reshape(sites1.lons.shape + (1,)),
        sites1.lats.reshape(sites1.lats.shape + (1,)),
        sites2.lons,
        sites2.lats)
    rho = numpy.block([[
        _compute_spatial_cross_correlation_matrix(
            distance_matrix, imt_1, imt_2, spatial_correl, cross_correl_within)
        for imt_2 in imts2] for imt_1 in imts1])
    return numpy.linalg.multi_dot([diag1, rho, diag2])


# In scenario/case_21 one has
# target_imt = PGA = target_imts = observed_imts
# ctx_Y with 571 elements, like target_sitecol
# station_data has 140 elements like station_sitecol
# 18 sites are discarded
# the total sitecol has 571 + 140 + 18 = 729 sites
# NB: this is run in parallel
def get_mu_tau_phi(target_imt, gsim, mean_stds,
                   target_imts, observed_imts, station_data,
                   target_sitecol, station_sitecol, compute_cov, r, monitor):
    # Using Bayes rule, compute the posterior distribution of the
    # normalized between-event residual H|YD=yD, employing
    # Engler et al. (2022), eqns B8 and B9 (also B18 and B19),
    # H|Y2=y2 is normally distributed with mean and covariance:
    cov_HD_HD_yD = numpy.linalg.pinv(
        numpy.linalg.multi_dot([r.T_D.T, r.cov_WD_WD_inv, r.T_D])
        + numpy.linalg.pinv(r.corr_HD_HD))

    mu_HD_yD = numpy.linalg.multi_dot(
        [cov_HD_HD_yD, r.T_D.T, r.cov_WD_WD_inv, r.zD])

    # Compute the distribution of the conditional between-event
    # residual B|Y2=y2
    mu_BD_yD = r.T_D @ mu_HD_yD
    cov_BD_BD_yD = numpy.linalg.multi_dot([r.T_D, cov_HD_HD_yD, r.T_D.T])

    # Get the nominal bias and its standard deviation as the means of the
    # conditional between-event residual mean and standard deviation
    nominal_bias_mean = numpy.mean(mu_BD_yD)
    nominal_bias_stddev = numpy.sqrt(numpy.mean(numpy.diag(cov_BD_BD_yD)))

    msg = ("GSIM: %s, IMT: %s, Nominal bias mean: %.3f, Nominal bias stddev: %.3f"
           % (gsim.gmpe if hasattr(gsim, 'gmpe') else gsim,
              target_imt, nominal_bias_mean, nominal_bias_stddev))

    # Predicted mean at the target sites, from GSIM
    mu_Y = mean_stds[0, 0][:, None]

    # Predicted uncertainty components at the target sites, from GSIM
    tau_Y = mean_stds[2, 0][:, None]
    Y = numpy.diag(mean_stds[3, 0])

    # Compute the mean of the conditional between-event residual B|YD=yD
    # for the target sites; the shapes are (nsites, nstations),
    # (nstations, nsites), (nsites, nsites) respectively
    cov_WY_WD = compute_cov(target_sitecol, station_sitecol,
                            [target_imt], r.conditioning_imts, Y, r.D)
    cov_WD_WY = compute_cov(station_sitecol, target_sitecol,
                            r.conditioning_imts, [target_imt], r.D, Y)
    cov_WY_WY = compute_cov(target_sitecol, target_sitecol,
                            [target_imt], [target_imt], Y, Y)

    # Compute the regression coefficient matrix [cov_WY_WD × cov_WD_WD_inv]
    RC = cov_WY_WD @ r.cov_WD_WD_inv  # shape (nsites, nstations)

    # compute the mean, shape (nsites, 1)
    mu = mu_Y + tau_Y @ mu_HD_yD[0, None] + RC @ (r.zD - mu_BD_yD)

    # covariance matrices can contain extremely small negative values

    # Compute the conditioned within-event covariance matrix
    # for the target sites clipped to zero, shape (nsites, nsites)
    tau = (cov_WY_WY - RC @ cov_WD_WY).clip(min=0)

    # Compute the scaling matrix "C" for the conditioned between-event
    # covariance matrix
    if r.native_data_available:
        C = tau_Y - RC @ r.T_D
    else:
        zeros = numpy.zeros((len(target_sitecol), len(r.conditioning_imts)))
        C = numpy.block([tau_Y, zeros]) - RC @ r.T_D

    # Compute the conditioned between-event covariance matrix
    # for the target sites clipped to zero, shape (nsites, nsites)
    phi = numpy.linalg.multi_dot([C, cov_HD_HD_yD, C.T]).clip(min=0)
    return {(r.g, r.m): (mu, tau, phi, msg)}


def get_me_ta_ph(cmaker, sdata, observed_imts, target_imts,
                 mean_stds_D, mean_stds_Y, target, station_filtered,
                 compute_cov, cross_correl_between, h5):
    G = len(cmaker.gsims)
    M = len(target_imts)
    N = mean_stds_Y.shape[-1]
    me = numpy.zeros((G, M, N, 1))
    ta = numpy.zeros((G, M, N, N))
    ph = numpy.zeros((G, M, N, N))
    smap = parallel.Starmap(get_mu_tau_phi, h5=h5)
    for g, gsim in enumerate(cmaker.gsims):
        if gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == {StdDev.TOTAL}:
            if not (type(gsim).__name__ == "ModifiableGMPE"
                    and "add_between_within_stds" in gsim.kwargs):
                raise NoInterIntraStdDevs(gsim)

        # NB: mu has shape (N, 1) and sig, tau, phi shape (N, N)
        # so, unlike the regular gsim get_mean_std, a numpy ndarray
        # won't work well as the 4 components will be non-homogeneous
        for m, o_imt in enumerate(observed_imts):
            im = o_imt.string
            sdata[im + "_median"] = mean_stds_D[0, g, m]
            sdata[im + "_sigma"] = mean_stds_D[1, g, m]
            sdata[im + "_tau"] = mean_stds_D[2, g, m]
            sdata[im + "_phi"] = mean_stds_D[3, g, m]
        for m, target_imt in enumerate(target_imts):
            result = create_result(
                g, m, target_imt, target_imts, observed_imts,
                sdata, target, station_filtered,
                compute_cov, cross_correl_between)
            smap.submit(
                (target_imt, gsim, mean_stds_Y[:, g], target_imts, observed_imts,
                 sdata, target, station_filtered, compute_cov, result))
    for (g, m), (mu, tau, phi, msg) in smap.reduce().items():
        me[g, m] = mu
        ta[g, m] = tau
        ph[g, m] = phi
        logging.info(msg)
    return me, ta, ph


# tested in openquake/hazardlib/tests/calc/conditioned_gmfs_test.py
def get_mean_covs(
        rupture, cmaker, station_sitecol, station_data, observed_imt_strs,
        target_sitecol, target_imts, spatial_correl, cross_correl_between,
        cross_correl_within, sigma=True, h5=None):
    """
    :returns: a list of arrays [mea, sig, tau, phi] or [mea, tau, phi]
    """
    if hasattr(rupture, 'rupture'):
        rupture = rupture.rupture

    observed_imtls = {imt_str: [0] for imt_str in observed_imt_strs
                      if imt_str not in ["MMI", "PGV"]}
    observed_imts = sorted(from_string(imt_str) for imt_str in observed_imtls)

    # Target IMT is not PGA or SA: Currently not supported
    target_imts = [imt for imt in target_imts
                   if imt.period or imt.string == "PGA"]

    # Generate the contexts and calculate the means and
    # standard deviations at the *station* sites ("_D")
    cmaker_D = cmaker.copy(imtls=observed_imtls)

    [ctx_D] = cmaker_D.get_ctx_iter([rupture], station_sitecol)
    mean_stds_D = cmaker_D.get_mean_stds([ctx_D])
    # shape (4, G, M, N) where 4 means (mean, sig, tau, phi)

    # Generate the contexts and calculate the means and 
    # standard deviations at the *target* sites ("_Y")
    cmaker_Y = cmaker.copy(imtls={target_imts[0].string: [0]})

    [ctx_Y] = cmaker_Y.get_ctx_iter([rupture], target_sitecol)
    mean_stds_Y = cmaker_D.get_mean_stds([ctx_Y])

    # filter sites
    target = target_sitecol.filter(
        numpy.isin(target_sitecol.sids, ctx_Y.sids))
    mask = numpy.isin(station_sitecol.sids, ctx_D.sids)
    station_filtered = station_sitecol.filter(mask)

    compute_cov = partial(compute_spatial_cross_covariance_matrix,
                          spatial_correl, cross_correl_within)
    me, ta, ph = get_me_ta_ph(
        cmaker, station_data[mask].copy(), observed_imts, target_imts,
        mean_stds_D, mean_stds_Y, target, station_filtered,
        compute_cov, cross_correl_between, h5)
    if sigma:
        return [me, ta + ph, ta, ph]
    else:
        # save memory since sigma = tau + phi is not needed
        return [me, ta, ph]


def _compute_spatial_cross_correlation_matrix(
        distance_matrix, imt_1, imt_2, spatial_correl, cross_correl_within):
    if imt_1 == imt_2:
        # since we have a single IMT, there are no cross-correlation terms
        spatial_correlation_matrix = spatial_correl._get_correlation_matrix(
            distance_matrix, imt_1)
        return spatial_correlation_matrix
    matrix1 = spatial_correl._get_correlation_matrix(distance_matrix, imt_1)
    matrix2 = spatial_correl._get_correlation_matrix(distance_matrix, imt_2)
    spatial_correlation_matrix = numpy.maximum(matrix1, matrix2)
    cross_corr_coeff = cross_correl_within.get_correlation(imt_1, imt_2)
    return spatial_correlation_matrix * cross_corr_coeff


def clip_evals(x, value=0):
    evals, evecs = numpy.linalg.eigh(x)  # totally dominates the performance
    clipped = numpy.any(evals < value)
    x_new = evecs * numpy.maximum(evals, value) @ evecs.T
    return x_new, clipped


def cov2corr(cov, return_std=False):
    """
    Function to convert a covariance matrix to a correlation matrix

    Function from statsmodels.stats.moment_helpers

    Parameters
    ----------
    cov : array_like, 2d
        covariance matrix, see Notes

    Returns
    -------
    corr : ndarray (subclass)
        correlation matrix
    return_std : bool
        If this is true then the standard deviation is also returned.
        By default only the correlation matrix is returned.

    Notes
    -----
    This function does not convert subclasses of ndarrays. This requires that
    division is defined elementwise. numpy.ma.array and numpy.matrix are
    allowed.
    """
    cov = numpy.asanyarray(cov)
    std_ = numpy.sqrt(numpy.diag(cov))
    corr = cov / numpy.outer(std_, std_)
    if return_std:
        return corr, std_
    else:
        return corr


def corr2cov(corr, std):
    """
    Convert a correlation matrix to a covariance matrix given the
    standard deviation. Function from statsmodels.stats.moment_helpers.

    Parameters
    ----------
    corr : array_like, 2d
        correlation matrix, see Notes
    std : array_like, 1d
        standard deviation

    Returns
    -------
    cov : ndarray (subclass)
        covariance matrix

    Notes
    -----
    This function does not convert subclasses of ndarrays. This requires
    that multiplication is defined elementwise. numpy.ma.array are allowed,
    but not matrices.
    """
    corr = numpy.asanyarray(corr)
    std_ = numpy.asanyarray(std)
    cov = corr * numpy.outer(std_, std_)
    return cov


def corr_nearest(corr, threshold=1e-15, n_fact=100):
    """
    Find the nearest correlation matrix that is positive semi-definite.

    The function iteratively adjust the correlation matrix by clipping the
    eigenvalues of a difference matrix. The diagonal elements are set to one.

    Function from statsmodels.stats.correlation_tools

    Parameters
    ----------
    corr : ndarray, (k, k)
        initial correlation matrix
    threshold : float
        clipping threshold for smallest eigenvalue, see Notes
    n_fact : int or float
        factor to determine the maximum number of iterations. The maximum
        number of iterations is the integer part of the number of columns in
        the correlation matrix times n_fact.

    Returns
    -------
    corr_new : ndarray, (optional)
        corrected correlation matrix

    Notes
    -----
    The smallest eigenvalue of the corrected correlation matrix is
    approximately equal to the ``threshold``.
    If the threshold=0, then the smallest eigenvalue of the correlation matrix
    might be negative, but zero within a numerical error, for example in the
    range of -1e-16.

    Assumes input correlation matrix is symmetric.

    Stops after the first step if correlation matrix is already positive
    semi-definite or positive definite, so that smallest eigenvalue is above
    threshold. In this case, the returned array is not the original, but
    is equal to it within numerical precision.

    See Also
    --------
    corr_clipped
    cov_nearest
    """
    k_vars = corr.shape[0]
    if k_vars != corr.shape[1]:
        raise ValueError("matrix is not square")

    diff = numpy.zeros(corr.shape)
    x_new = corr.copy()
    diag_idx = numpy.arange(k_vars)

    for ii in range(int(len(corr) * n_fact)):
        x_adj = x_new - diff
        x_psd, clipped = clip_evals(x_adj, value=threshold)
        if not clipped:
            x_new = x_psd
            break
        diff = x_psd - x_adj
        x_new = x_psd.copy()
        x_new[diag_idx, diag_idx] = 1
    else:
        raise IterationLimitWarning

    return x_new


def corr_clipped(corr, threshold=1e-15):
    """
    Find a near correlation matrix that is positive semi-definite

    This function clips the eigenvalues, replacing eigenvalues smaller than
    the threshold by the threshold. The new matrix is normalized, so that the
    diagonal elements are one.
    Compared to corr_nearest, the distance between the original correlation
    matrix and the positive definite correlation matrix is larger, however,
    it is much faster since it only computes eigenvalues once.

    Function from statsmodels.stats.correlation_tools

    Parameters
    ----------
    corr : ndarray, (k, k)
        initial correlation matrix
    threshold : float
        clipping threshold for smallest eigenvalue, see Notes

    Returns
    -------
    corr_new : ndarray, (optional)
        corrected correlation matrix


    Notes
    -----
    The smallest eigenvalue of the corrected correlation matrix is
    approximately equal to the ``threshold``. In examples, the
    smallest eigenvalue can be by a factor of 10 smaller than the threshold,
    e.g. threshold 1e-8 can result in smallest eigenvalue in the range
    between 1e-9 and 1e-8.
    If the threshold=0, then the smallest eigenvalue of the correlation matrix
    might be negative, but zero within a numerical error, for example in the
    range of -1e-16.

    Assumes input correlation matrix is symmetric. The diagonal elements of
    returned correlation matrix is set to ones.

    If the correlation matrix is already positive semi-definite given the
    threshold, then the original correlation matrix is returned.

    ``cov_clipped`` is 40 or more times faster than ``cov_nearest`` in simple
    example, but has a slightly larger approximation error.

    See Also
    --------
    corr_nearest
    cov_nearest
    """
    x_new, clipped = clip_evals(corr, value=threshold)
    if not clipped:
        return corr

    # cov2corr
    x_std = numpy.sqrt(numpy.diag(x_new))
    x_new = x_new / x_std / x_std[:, None]
    return x_new


def cov_nearest(cov, method="clipped", threshold=1e-15, n_fact=100,
                return_all=False):
    """
    Find the nearest covariance matrix that is positive (semi-) definite

    This leaves the diagonal, i.e. the variance, unchanged

    Function from statsmodels.stats.correlation_tools

    Parameters
    ----------
    cov : ndarray, (k,k)
        initial covariance matrix
    method : str
        if "clipped", then the faster but less accurate ``corr_clipped`` is
        used.if "nearest", then ``corr_nearest`` is used
    threshold : float
        clipping threshold for smallest eigen value, see Notes
    n_fact : int or float
        factor to determine the maximum number of iterations in
        ``corr_nearest``. See its doc string
    return_all : bool
        if False (default), then only the covariance matrix is returned.
        If True, then correlation matrix and standard deviation are
        additionally returned.

    Returns
    -------
    cov_ : ndarray
        corrected covariance matrix
    corr_ : ndarray, (optional)
        corrected correlation matrix
    std_ : ndarray, (optional)
        standard deviation


    Notes
    -----
    This converts the covariance matrix to a correlation matrix. Then, finds
    the nearest correlation matrix that is positive semidefinite and converts
    it back to a covariance matrix using the initial standard deviation.

    The smallest eigenvalue of the intermediate correlation matrix is
    approximately equal to the ``threshold``.
    If the threshold=0, then the smallest eigenvalue of the correlation matrix
    might be negative, but zero within a numerical error, for example in the
    range of -1e-16.

    Assumes input covariance matrix is symmetric.

    See Also
    --------
    corr_nearest
    corr_clipped
    """
    cov_, std_ = cov2corr(cov, return_std=True)
    if method == "clipped":
        corr_ = corr_clipped(cov_, threshold=threshold)
    else:  # method == 'nearest'
        corr_ = corr_nearest(cov_, threshold=threshold, n_fact=n_fact)

    cov_ = corr2cov(corr_, std_)

    if return_all:
        return cov_, corr_, std_
    else:
        return cov_
