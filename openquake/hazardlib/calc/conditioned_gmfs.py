# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 GEM Foundation
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
import numpy
import pandas
from openquake.baselib.python3compat import decode
from openquake.baselib.general import AccumDict
from openquake.hazardlib import correlation, cross_correlation
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.gmf import GmfComputer, exp
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.geo.geodetic import geodetic_distance
from openquake.hazardlib.gsim.base import ContextMaker

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
""" % self.gsim.__class__.__name_


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
    between-event terms have been conditioned upon the observations

    :param rupture:
        Rupture to calculate ground motion fields radiated from.

    :param :class:`openquake.hazardlib.site.SiteCollection` sitecol:
        a complete SiteCollection

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
        GmfComputer.__init__(
            self, rupture=rupture, sitecol=sitecol, cmaker=cmaker,
            correlation_model=spatial_correl,
            cross_correl=cross_correl_between,
            amplifier=amplifier, sec_perils=sec_perils)

        try:
            vs30_clustering = ground_motion_correlation_params[
                "vs30_clustering"]
        except KeyError:
            vs30_clustering = True
        self.spatial_correl = (spatial_correl or correlation.
                               JB2009CorrelationModel(vs30_clustering))
        self.cross_correl_between = (
            cross_correl_between or cross_correlation.GodaAtkinson2009())
        self.cross_correl_within = cross_correlation.BakerJayaram2008()
        observed_imtls = {imt_str: [0]
                          for imt_str in observed_imt_strs
                          if imt_str not in ["MMI", "PGV"]}
        self.observed_imts = sorted(
            [from_string(imt_str) for imt_str in observed_imtls])
        self.rupture = rupture
        self.target_sitecol = sitecol
        self.station_sitecol = station_sitecol
        self.station_data = station_data
        self.observed_imt_strs = observed_imt_strs
        self.num_events = number_of_ground_motion_fields

    def compute_all(self, scenario, sig_eps=None, max_iml=None):
        """
        :returns: (dict with fields eid, sid, gmv_X, ...), dt
        """
        min_iml = self.cmaker.min_iml
        rlzs_by_gsim = self.cmaker.gsims
        sids = self.target_sitecol.sids
        eid_rlz = self.ebrupture.get_eid_rlz(rlzs_by_gsim, scenario)
        mag = self.ebrupture.rupture.mag
        data = AccumDict(accum=[])
        rng = numpy.random.default_rng(self.seed)
        num_events = self.num_events
        num_gsims = len(rlzs_by_gsim)
        offsets = numpy.arange(num_events) * num_gsims
        for g, (gsim, rlzs) in enumerate(rlzs_by_gsim.items()):
            if num_events == 0:  # it may happen
                continue
            # NB: the trick for performance is to keep the call to
            # .compute outside of the loop over the realizations;
            # it is better to have few calls producing big arrays
            mean_covs = get_conditioned_mean_and_covariance(
                self.rupture, gsim, self.station_sitecol, self.station_data,
                self.observed_imt_strs, self.target_sitecol, self.imts,
                self.spatial_correl,
                self.cross_correl_between, self.cross_correl_within,
                self.cmaker.maximum_distance)

            array, sig, eps = self.compute(gsim, num_events, mean_covs, rng)
            M, N, E = array.shape  # sig and eps have shapes (M, E) instead

            # manage max_iml
            if max_iml is not None:
                for m, im in enumerate(self.cmaker.imtls):
                    if (array[m] > max_iml[m]).any():
                        for n in range(N):
                            bad = array[m, n] > max_iml[m]  # shape E
                            array[m, n, bad] = exp(mean_covs[0, g, m, n], im)

            # manage min_iml
            for n in range(N):
                for e in range(E):
                    if (array[:, n, e] < min_iml).all():
                        array[:, n, e] = 0
            array = array.transpose(1, 0, 2)  # from M, N, E to N, M, E
            n = 0
            for rlz in rlzs:
                eids = eid_rlz[eid_rlz['rlz'] == rlz]['eid'][0] + offsets
                for ei, eid in enumerate(eids):
                    gmfa = array[:, :, n + ei]  # shape (N, M)
                    if sig_eps is not None:
                        tup = tuple([eid, rlz] + list(sig[:, n + ei]) +
                                    list(eps[:, n + ei]))
                        sig_eps.append(tup)
                    items = []
                    for sp in self.sec_perils:
                        o = sp.compute(mag, zip(self.imts, gmfa.T), self.ctx)
                        for outkey, outarr in zip(sp.outputs, o):
                            items.append((outkey, outarr))
                    for i, gmv in enumerate(gmfa):
                        if gmv.sum() == 0:
                            continue
                        data["sid"].append(sids[i])
                        data["eid"].append(eid)
                        data["rlz"].append(rlz)  # used in compute_gmfs_curves
                        for m in range(M):
                            data[f"gmv_{m}"].append(gmv[m])
                        for outkey, outarr in items:
                            data[outkey].append(outarr[i])
                        # gmv can be zero due to the minimum_intensity, coming
                        # from the job.ini or from the vulnerability functions
                n += len(eids)
        return pandas.DataFrame(data)

    def compute(self, gsim, num_events, mean_covs, rng):
        """
        :param gsim: GSIM used to compute mean_stds
        :param num_events: the number of seismic events
        :param mean_covs: array of shape (4, M, N)
        :returns:
            a 32 bit array of shape (num_imts, num_sites, num_events) and
            two arrays with shape (num_imts, num_events): sig for tau
            and eps for the random part
        """
        M = len(self.imts)
        num_sids = mean_covs[0][self.imts[0].string].size
        result = numpy.zeros((M, num_sids, num_events), F32)
        sig = numpy.zeros((M, num_events), F32)  # same for all events
        eps = numpy.zeros((M, num_events), F32)  # not the same
        numpy.random.seed(self.seed)

        for m, im in enumerate(self.imts):
            mu_Y_yD = mean_covs[0][im.string]
            # cov_Y_Y_yD = mean_covs[1][im.string]
            cov_WY_WY_wD = mean_covs[2][im.string]
            cov_BY_BY_yD = mean_covs[3][im.string]
            try:
                result[m], sig[m], eps[m] = self._compute(
                    mu_Y_yD, cov_WY_WY_wD, cov_BY_BY_yD, im, num_events, rng)
            except Exception as exc:
                raise RuntimeError(
                    "(%s, %s, source_id=%r) %s: %s"
                    % (gsim, im, decode(self.source_id),
                       exc.__class__.__name__, exc)
                ).with_traceback(exc.__traceback__)
        if self.amplifier:
            self.amplifier.amplify_gmfs(
                self.ctx.ampcode, result, self.imts, self.seed)
        return result, sig, eps

    def _compute(self, mu_Y, cov_WY_WY, cov_BY_BY, imt, num_events, rng):
        if self.cmaker.truncation_level <= 1E-9:
            gmf = exp(mu_Y, imt)  # exponentiate unless imt == 'MMI'
            gmf = gmf.repeat(num_events, axis=1)
            inter_sig = 0
            inter_eps = numpy.zeros(num_events)
        else:
            cov_Y_Y = cov_WY_WY + cov_BY_BY
            gmf = exp(
                rng.multivariate_normal(
                    mu_Y.flatten(), cov_Y_Y, size=num_events,
                    check_valid="warn", tol=1e-5, method="eigh"),
                imt).T
            inter_sig = 0
            inter_eps = 0
        return gmf, inter_sig, inter_eps  # shapes (N, E), 1, E


# tested in openquake/hazardlib/tests/calc/conditioned_gmfs_test.py
def get_conditioned_mean_and_covariance(
        rupture, gsim, station_sitecol, station_data,
        observed_imt_strs, target_sitecol, target_imts,
        spatial_correl, cross_correl_between, cross_correl_within,
        maximum_distance):

    if gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == {StdDev.TOTAL}:
        if not (type(gsim).__name__ == "ModifiableGMPE"
                and "add_between_within_stds" in gsim.kwargs):
            raise NoInterIntraStdDevs(gsim)

    observed_imtls = {imt_str: [0] for imt_str in observed_imt_strs
                      if imt_str not in ["MMI", "PGV"]}
    observed_imts = sorted(from_string(imt_str) for imt_str in observed_imtls)

    # Generate the contexts and calculate the means and 
    # standard deviations at the *station* sites ("_D")
    cmaker_D = ContextMaker(
        rupture.tectonic_region_type, [gsim],
        dict(truncation_level=0, imtls=observed_imtls,
             maximum_distance=maximum_distance))

    # Generate the contexts and calculate the means and 
    # standard deviations at the *target* sites ("_Y")
    cmaker_Y = ContextMaker(
        rupture.tectonic_region_type, [gsim], dict(
            truncation_level=0, imtls={target_imts[0].string: [0]},
            maximum_distance=maximum_distance))

    gc_D = GmfComputer(rupture, station_sitecol, cmaker_D)
    gc_Y = GmfComputer(rupture, target_sitecol, cmaker_Y)

    gsim_idx = 0  # there is a single gsim
    mean_stds = cmaker_D.get_mean_stds([gc_D.ctx])[:, gsim_idx]
    # shape (4, M, N) where 4 means (mean, TOTAL, INTER_EVENT, INTRA_EVENT)
    # M is the number of IMTs, N the number of sites/distances

    station_locs_filtered = numpy.argwhere(
        numpy.isin(station_sitecol.sids, gc_D.ctx.sids)).ravel().tolist()
    station_sitecol_filtered = station_sitecol.filtered(station_locs_filtered)
    station_data_filtered = station_data.iloc[station_locs_filtered].copy()
    for i, o_imt in enumerate(observed_imts):
        im = o_imt.string
        station_data_filtered[im + "_median"] = mean_stds[0, i]
        station_data_filtered[im + "_sigma"] = mean_stds[1, i]
        station_data_filtered[im + "_tau"] = mean_stds[2, i]
        station_data_filtered[im + "_phi"] = mean_stds[3, i]

    # Target IMT is not PGA or SA: Currently not supported
    target_imts = [imt for imt in target_imts
                   if imt.period or imt.string == "PGA"]
    # build 4 dictionaries keyed by IMT
    meancovs = [{imt.string: None for imt in target_imts} for _ in range(4)]
    for target_imt in target_imts:
        set_meancovs(
            target_imt, cmaker_Y, gc_Y, target_sitecol,
            target_imts, observed_imts,
            station_data_filtered, station_sitecol_filtered,
            spatial_correl, cross_correl_within, cross_correl_between,
            meancovs)

    return meancovs


def set_meancovs(target_imt, cmaker_Y, gc_Y, target_sitecol,
                 target_imts, observed_imts,
                 station_data_filtered, station_sitecol_filtered,
                 spatial_correl, cross_correl_within, cross_correl_between,
                 meancovs):

    nss = len(station_sitecol_filtered)  # number of station sites
    [gsim] = cmaker_Y.gsims
    if hasattr(gsim, "gmpe"):
        gsim_name = gsim.gmpe.__class__.__name__
    else:
        gsim_name = gsim.__class__.__name__

    native_data_available = False

    imt = target_imt.string
    cmaker_Y.imtls = {imt: [0]}

    if target_imt in observed_imts:
        # Target IMT is present in the observed IMTs
        conditioning_imts = [target_imt]
        bracketed_imts = conditioning_imts
        native_data_available = True
    else:
        # Find where the target IMT falls in the list of observed IMTs
        all_imts = sorted(observed_imts + [target_imt])
        imt_idx = numpy.where(
            imt == numpy.array(all_imts)[:, 0])[0][0]
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
                f"null values for {imt}."
                "Please fill or discard these rows.")

    # Observations (recorded values at the stations)
    yD = numpy.log(
        station_data_filtered[
            [c_imt.string + "_mean" for c_imt in conditioning_imts]]
    ).values.reshape((-1, 1), order="F")

    # Additional sigma for the observations that are uncertain
    # These arise if the values for this particular IMT were not
    # directly recorded, but obtained by conversion equations or
    # cross-correlation functions
    var_addon_D = station_data_filtered[
        [c_imt.string + "_std" for c_imt in conditioning_imts]
    ].values.reshape((-1, 1), order="F") ** 2

    # Predicted mean at the observation points, from GSIM(s)
    mu_yD = station_data_filtered[
        [c_imt.string + "_median" for c_imt in conditioning_imts]
    ].values.reshape((-1, 1), order="F")
    # Predicted uncertainty components at the observation points
    # from GSIM(s)
    phi_D = station_data_filtered[
        [c_imt.string + "_phi" for c_imt in conditioning_imts]
    ].values.reshape((-1, 1), order="F")
    tau_D = station_data_filtered[
        [c_imt.string + "_tau" for c_imt in conditioning_imts]
    ].values.reshape((-1, 1), order="F")

    if native_data_available:
        T_D = tau_D
    else:
        # s = num_station_sites
        T_D = numpy.zeros(
            (len(conditioning_imts) * nss, len(bracketed_imts)))
        for i in range(len(conditioning_imts)):
            T_D[i * nss: (i + 1) * nss, i + 1] = tau_D[
                i * nss: (i + 1) * nss, 0]
    # The raw residuals
    zeta_D = yD - mu_yD

    # Compute the station data within-event covariance matrix
    rho_WD_WD = compute_spatial_cross_correlation_matrix(
        station_sitecol_filtered,
        station_sitecol_filtered,
        conditioning_imts,
        conditioning_imts,
        spatial_correl,
        cross_correl_within,
    )
    phi_D_flat = phi_D.flatten()
    cov_WD_WD = numpy.linalg.multi_dot(
        [numpy.diag(phi_D_flat), rho_WD_WD, numpy.diag(phi_D_flat)]
    )
    # Add on the additional variance of the residuals
    # for the cases where the station data is uncertain
    numpy.fill_diagonal(cov_WD_WD, numpy.diag(cov_WD_WD) + var_addon_D)

    # Get the (pseudo)-inverse of the station data within-event covariance
    # matrix
    cov_WD_WD_inv = numpy.linalg.pinv(cov_WD_WD)

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
    corr_HD_HD = cross_correl_between._get_correlation_matrix(
        bracketed_imts)

    # Using Bayes rule, compute the posterior distribution of the
    # normalized between-event residual H|YD=yD, employing
    # Engler et al. (2022), eqns B8 and B9 (also B18 and B19),
    # H|Y2=y2 is normally distributed with mean and covariance:
    cov_HD_HD_yD = numpy.linalg.pinv(
        numpy.linalg.multi_dot([T_D.T, cov_WD_WD_inv, T_D])
        + numpy.linalg.pinv(corr_HD_HD)
    )
    mu_HD_yD = numpy.linalg.multi_dot(
        [cov_HD_HD_yD, T_D.T, cov_WD_WD_inv, zeta_D])

    # Compute the distribution of the conditional between-event
    # residual B|Y2=y2
    mu_BD_yD = T_D @ mu_HD_yD
    cov_BD_BD_yD = numpy.linalg.multi_dot([T_D, cov_HD_HD_yD, T_D.T])

    # Get the nominal bias and its standard deviation as the means of the
    # conditional between-event residual mean and standard deviation
    nominal_bias_mean = numpy.mean(mu_BD_yD)
    nominal_bias_stddev = numpy.sqrt(numpy.mean(numpy.diag(cov_BD_BD_yD)))
    logging.info("GSIM: %s, IMT: %s, Nominal bias mean: %.3f, "
                 "Nominal bias stddev: %.3f",  gsim_name,
                 imt, nominal_bias_mean, nominal_bias_stddev)

    mean_stds = cmaker_Y.get_mean_stds([gc_Y.ctx])[:, 0]
    target_sites_filtered = numpy.argwhere(
        numpy.isin(target_sitecol.sids, gc_Y.ctx.sids)).ravel().tolist()
    target_sitecol_filtered = target_sitecol.filtered(
        target_sites_filtered)
    num_target_sites = len(target_sitecol_filtered)
    # (4, G, M, N): mean, StdDev.TOTAL, StdDev.INTER_EVENT,
    # StdDev.INTRA_EVENT; G gsims, M IMTs, N sites/distances

    # Predicted mean at the target sites, from GSIM(s)
    mu_Y = mean_stds[0, 0].reshape((-1, 1))
    # Predicted uncertainty components at the target sites, from GSIM(s)
    sigma_Y = mean_stds[1, 0].reshape((-1, 1))
    tau_Y = mean_stds[2, 0].reshape((-1, 1))
    phi_Y = mean_stds[3, 0].reshape((-1, 1))
    phi_Y_flat = phi_Y.flatten()

    # Compute the mean of the conditional between-event residual B|YD=yD
    # for the target sites
    mu_HN_yD = mu_HD_yD[0, None]
    mu_BY_yD = tau_Y @ mu_HN_yD

    # Compute the within-event covariance matrix for the
    # target sites and observation sites
    rho_WY_WD = compute_spatial_cross_correlation_matrix(
        target_sitecol_filtered,
        station_sitecol_filtered,
        [target_imt],
        conditioning_imts,
        spatial_correl,
        cross_correl_within,
    )
    cov_WY_WD = numpy.linalg.multi_dot(
        [numpy.diag(phi_Y_flat), rho_WY_WD, numpy.diag(phi_D_flat)]
    )

    rho_WD_WY = compute_spatial_cross_correlation_matrix(
        station_sitecol_filtered,
        target_sitecol_filtered,
        conditioning_imts,
        [target_imt],
        spatial_correl,
        cross_correl_within,
    )
    cov_WD_WY = numpy.linalg.multi_dot(
        [numpy.diag(phi_D_flat), rho_WD_WY, numpy.diag(phi_Y_flat)]
    )

    # Compute the within-event covariance matrix for the
    # target sites (apriori)
    rho_WY_WY = compute_spatial_cross_correlation_matrix(
        target_sitecol_filtered,
        target_sitecol_filtered,
        [target_imt],
        [target_imt],
        spatial_correl,
        cross_correl_within,
    )
    cov_WY_WY = numpy.linalg.multi_dot(
        [numpy.diag(phi_Y_flat), rho_WY_WY, numpy.diag(phi_Y_flat)]
    )

    # Compute the regression coefficient matrix [cov_WY_WD × cov_WD_WD_inv]
    RC = cov_WY_WD @ cov_WD_WD_inv

    # Compute the scaling matrix "C" for the conditioned between-event
    # covariance matrix
    if native_data_available:
        T_Y0 = tau_Y
    else:
        tau_zeros = numpy.zeros((num_target_sites, len(conditioning_imts)))
        T_Y0 = numpy.block([tau_Y, tau_zeros])
    C = T_Y0 - RC @ T_D

    # Compute the conditioned within-event covariance matrix
    # for the target sites
    cov_WY_WY_wD = cov_WY_WY - RC @ cov_WD_WY

    # Compute the "conditioned between-event" covariance matrix
    # for the target sites
    cov_BY_BY_yD = numpy.linalg.multi_dot([C, cov_HD_HD_yD, C.T])

    # Both conditioned covariance matrices can contain extremely
    # small negative values due to limitations of floating point
    # operations (~ -10^-17 to -10^-15), these are clipped to zero
    cov_WY_WY_wD = cov_WY_WY_wD.clip(min=0)
    cov_BY_BY_yD = cov_BY_BY_yD.clip(min=0)

    # Finally, compute the conditioned mean
    # of the ground motion at the target sites
    mu_Y_yD = mu_Y + mu_BY_yD + RC @ (zeta_D - mu_BD_yD)

    # And compute the conditional covariance
    # of the ground motion at the target sites
    cov_Y_Y_yD = cov_WY_WY_wD + cov_BY_BY_yD

    # Store the results in a dictionary keyed by target IMT
    # The four arrays below have different dimensions, so
    # unlike the regular gsim get_mean_std, a numpy ndarray
    # won't work well as the 4 components will be non-homogeneous
    meancovs[0][imt] = mu_Y_yD
    meancovs[1][imt] = cov_Y_Y_yD
    meancovs[2][imt] = cov_WY_WY_wD
    meancovs[3][imt] = cov_BY_BY_yD


def compute_spatial_cross_correlation_matrix(
        sitecol_1, sitecol_2, imt_list_1, imt_list_2,
        spatial_correl, cross_correl_within):
    # The correlation structure for IMs of differing types at differing
    # locations can be reasonably assumed as Markovian in nature, and we
    # assume here that the correlation between differing IMs at differing
    # locations is simply the product of the cross correlation of IMs i and j
    # at the same location and the spatial correlation due to the distance
    # between sites m and n. Can be refactored down the line to support direct
    # spatial cross-correlation models
    distance_matrix = geodetic_distance(
        sitecol_1.lons.reshape(sitecol_1.lons.shape + (1,)),
        sitecol_1.lats.reshape(sitecol_1.lats.shape + (1,)),
        sitecol_2.lons,
        sitecol_2.lats,
    )
    spatial_cross_correlation_matrix = numpy.block([[
        _compute_spatial_cross_correlation_matrix(
            distance_matrix, imt_1, imt_2, spatial_correl, cross_correl_within)
        for imt_2 in imt_list_2] for imt_1 in imt_list_1])
    return spatial_cross_correlation_matrix


def _compute_spatial_cross_correlation_matrix(
        distance_matrix, imt_1, imt_2,
        spatial_correl, cross_correl_within):
    if imt_1 == imt_2:
        # Since we have a single IMT, no cross-correlation terms to be computed
        spatial_correlation_matrix = spatial_correl._get_correlation_matrix(
            distance_matrix, imt_1
        )
        spatial_cross_correlation_matrix = spatial_correlation_matrix
    else:
        spatial_correlation_matrix_1 = spatial_correl._get_correlation_matrix(
            distance_matrix, imt_1
        )
        spatial_correlation_matrix_2 = spatial_correl._get_correlation_matrix(
            distance_matrix, imt_2
        )
        spatial_correlation_matrix = numpy.maximum(
            spatial_correlation_matrix_1, spatial_correlation_matrix_2
        )
        cross_corr_coeff = cross_correl_within.get_correlation(
            from_imt=imt_1, to_imt=imt_2
        )
        spatial_cross_correlation_matrix = (
            spatial_correlation_matrix * cross_corr_coeff)
    return spatial_cross_correlation_matrix


def clip_evals(x, value=0):  # threshold=0, value=0):
    evals, evecs = numpy.linalg.eigh(x)
    clipped = numpy.any(evals < value)
    x_new = numpy.dot(evecs * numpy.maximum(evals, value), evecs.T)
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
    that multiplication is defined elementwise. numpy.ma.array are allowed, but
    not matrices.
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
