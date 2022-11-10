# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 GEM Foundation
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

import sys

import numpy
import pandas
from openquake.commonlib import readinput
from openquake.hazardlib import correlation, cross_correlation, imt, valid
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.geo.geodetic import geodetic_distance
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.site import SiteCollection

# This module implements the process for conditioning ground motion
# fields upon recorded strong motion station data or macroseismic
# intensity observations described in Engler et al. (2022)
# Engler, D. T., Worden, C. B., Thompson, E. M., & Jaiswal, K. S. (2022).
# Partitioning Ground Motion Uncertainty When Conditioned on Station Data.
# Bulletin of the Seismological Society of America, 112(2), 1060–1079.
# https://doi.org/10.1785/0120210177
#
# The USGS ShakeMap implementation of Engler et al. (2022) is described
# in detail at: https://usgs.github.io/shakemap/manual4_0/tg_processing.html
# and the bulk of the implementation code resides in the ShakeMap Model module:
# https://github.com/usgs/shakemap/blob/main/shakemap/coremods/model.py
#
# This implementation is intended for generating conditional random
# ground motion fields for downstream use with the OpenQuake scenario
# damage and loss calculators, such that users can provide a station
# data file containing both seismic and macroseismic stations, where
# and specify a list of target IMTs and list of sites for which the
# OpenQuake engine will calculate the conditioned mean and covariance
# of the ground shaking following Engler et al. (2022), and then
# simulate the requested number of ground motion fields

# Notation:
# K: number of target sites at which ground motion is to be estimated
# L: number of recording stations with ground motion observations
# _D: subscript denoting data
# _N: subscript denoting "native" data, for the target IMT
# _NN: subscript denoting "nonnative" data, other IMTs at the stations
# M: number of nonnative IMTs used in the conditioning process
# Y_N: station data for the target IMT
# Y_NN: station data for the 'M' nonnative IMTs
# y2 = observations
# φ = phi = within-event standard deviation
# τ = tau = between-event standard deviation
# Η (capital Greek η, not Latin H) = normalized between-event residual
# δB = between-event residual, or bias


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
        self,
        rupture,
        sitecol,
        cmaker,
        correlation_model=None,
        cross_correl=None,
        amplifier=None,
        sec_perils=(),
    ):
        GmfComputer.__init__(
            self,
            rupture,
            sitecol,
            cmaker,
            correlation_model,
            cross_correl,
            amplifier,
            sec_perils,
        )


def main(job_params):
    oqparam = readinput.get_oqparam(job_ini)
    rupture = readinput.get_rupture(oqparam)
    gmm = valid.gsim(oqparam.gsim)
    target_imts = [imt.from_string(imt_str) for imt_str in oqparam.imtls]

    target_sitecol = readinput.get_site_collection(oqparam)
    num_target_sites = len(target_sitecol)

    station_data, observed_imt_strs = readinput.get_station_data(oqparam)
    station_sites = SiteCollection.from_points(
        lons=station_data.index.get_level_values(1),
        lats=station_data.index.get_level_values(2),
    )
    station_sitemodel = station_sites.assoc(target_sitecol, assoc_dist=0.1)
    station_sitecol = SiteCollection.from_points(
        lons=station_data.index.get_level_values(1),
        lats=station_data.index.get_level_values(2),
        sitemodel=station_sitemodel,
    )
    num_station_sites = len(station_sitecol)

    truncation_level = oqparam.truncation_level
    num_gmfs = oqparam.number_of_ground_motion_fields

    observed_imtls = {
        imt_str: [0] for imt_str in observed_imt_strs if imt_str not in ["MMI", "PGV"]
    }
    observed_imts = sorted([imt.from_string(imt_str) for imt_str in observed_imtls])
    cmaker = ContextMaker(
        rupture.tectonic_region_type,
        [gmm],
        dict(truncation_level=0, imtls=observed_imtls),
    )
    try:
        vs30_clustering = oqparam.ground_motion_correlation_params["vs30_clustering"]
    except KeyError:
        vs30_clustering = True
    spatial_correl = (
        oqparam.ground_motion_correlation_model
        or correlation.JB2009CorrelationModel(vs30_clustering)
    )
    cross_correl_between = oqparam.cross_correl or cross_correlation.GodaAtkinson2009()
    cross_correl_within = cross_correlation.BakerJayaram2008()
    cross_correl_total = cross_correlation.BakerJayaram2008()
    rupture.rup_id = oqparam.ses_seed
    gc = GmfComputer(rupture, station_sitecol, cmaker)
    mean_stds = cmaker.get_mean_stds([gc.ctx])[:, 0]
    # (4, G, M, N): mean, StdDev.TOTAL, StdDev.INTER_EVENT, StdDev.INTRA_EVENT; G gsims, M IMTs, N sites/distances
    for i, imt_i in enumerate(observed_imts):
        station_data.loc[:, (imt_i.string, "median")] = mean_stds[0, i, :]
        station_data.loc[:, (imt_i.string, "sigma")] = mean_stds[1, i, :]
        station_data.loc[:, (imt_i.string, "tau")] = mean_stds[2, i, :]
        station_data.loc[:, (imt_i.string, "phi")] = mean_stds[3, i, :]

    mu_Y_yD_dict = {target_imt.string: None for target_imt in target_imts}
    cov_Y_Y_yD_dict = {target_imt.string: None for target_imt in target_imts}

    # Proceed with each IMT in the target IMTs one by one
    # select the minimal number of IMTs observed at the stations
    # for each target IMT
    for target_imt in target_imts:
        native_data_available = False

        # Handle various cases differently depending on the
        # target IMT in question, and whether it is present
        # in the observed IMTs or not
        if not (target_imt.period or target_imt.string == "PGA"):
            # Target IMT is not PGA or SA: Currently not supported
            print(f"Conditioned gmfs not available for {target_imt.string}")
            continue
        elif target_imt in observed_imts:
            # Target IMT is present in the observed IMTs
            conditioning_imts = [target_imt]
            bracketed_imts = conditioning_imts
            native_data_available = True
        else:
            # Find where the target IMT falls in the list of observed IMTs
            all_imts = sorted(observed_imts + [target_imt])
            imt_idx = numpy.where(target_imt.string == numpy.array(all_imts)[:, 0])[0][
                0
            ]
            if imt_idx == 0:
                # Target IMT is outside the range of the observed IMT periods
                # and its period is lower than the lowest available in the observed IMTs
                conditioning_imts = [all_imts[1]]
            elif imt_idx == len(all_imts):
                # Target IMT is outside the range of the observed IMT periods
                # and its period is higher than the highest available in the observed IMTs
                conditioning_imts = [all_imts[-2]]
            else:
                # Target IMT is within the range of the observed IMT periods
                # and its period falls between two periods in the observed IMTs
                conditioning_imts = [all_imts[imt_idx - 1], all_imts[imt_idx + 1]]
            bracketed_imts = [target_imt] + conditioning_imts

        # Check if the station data for the IMTs shortlisted for conditioning contains NaNs
        for conditioning_imt in conditioning_imts:
            num_null_values = station_data[conditioning_imt.string]["mean"].isna().sum()
            if num_null_values:
                raise ValueError(
                    f"The station data contains {num_null_values}"
                    f"null values for {target_imt.string}."
                    "Please fill or discard these rows."
                )

        # Observations (recorded values at the stations)
        yD = station_data[
            [(c_imt.string, "mean") for c_imt in conditioning_imts]
        ].values.reshape((-1, 1), order="F")
        # Additional sigma for the observations that are uncertain
        # These arise if the values for this particular IMT were not
        # directly recorded, but obtained by conversion equations or
        # cross-correlation functions
        var_addon_D = (
            station_data[
                [(c_imt.string, "std") for c_imt in conditioning_imts]
            ].values.reshape((-1, 1), order="F")
            ** 2
        )

        # Predicted mean at the observation points, from GMM(s)
        mu_yD = station_data[
            [(c_imt.string, "median") for c_imt in conditioning_imts]
        ].values.reshape((-1, 1), order="F")
        # Predicted uncertainty components at the observation points, from GMM(s)
        phi_D = station_data[
            [(c_imt.string, "phi") for c_imt in conditioning_imts]
        ].values.reshape((-1, 1), order="F")
        tau_D = station_data[
            [(c_imt.string, "tau") for c_imt in conditioning_imts]
        ].values.reshape((-1, 1), order="F")

        if native_data_available:
            T_D = tau_D
        else:
            T_D = numpy.zeros(
                (len(conditioning_imts) * num_station_sites, len(bracketed_imts))
            )
            for i in range(len(conditioning_imts)):
                T_D[i * num_station_sites : (i + 1) * num_station_sites, i + 1] = tau_D[
                    i * num_station_sites : (i + 1) * num_station_sites, 0
                ]
        # The raw residuals
        zeta_D = yD - mu_yD

        # Compute the station data within-event covariance matrix
        rho_WD_WD = compute_spatial_cross_correlation_matrix(
            station_sitecol,
            station_sitecol,
            conditioning_imts,
            conditioning_imts,
            spatial_correl,
            cross_correl_within,
            vs30_clustering,
        )
        phi_D_flat = phi_D.flatten()
        cov_WD_WD = numpy.linalg.multi_dot(
            [numpy.diag(phi_D_flat), rho_WD_WD, numpy.diag(phi_D_flat)]
        )

        # Add on the additional variance of the residuals
        # for the cases where the station data is uncertain
        numpy.fill_diagonal(cov_WD_WD, numpy.diag(cov_WD_WD) + var_addon_D)

        # Get the (pseudo)-inverse of the station data within-event covariance matrix
        cov_WD_WD_inv = numpy.linalg.pinv(cov_WD_WD)

        # # The normalized between-event residual and its variance (for the observation points)
        # # Engler et al. (2022) equations 12 and 13; assumes between event residuals
        # # are perfectly cross-correlated
        # var_H_y2 = 1.0 / (
        #     1.0 + numpy.linalg.multi_dot([tau_y2.T, cov_W2_W2_inv, tau_y2])
        # )
        # mu_H_y2 = numpy.linalg.multi_dot([tau_y2.T, cov_W2_W2_inv, zeta]) * var_H_y2

        # The more generic equations B8 and B9 from Appendix B are used instead
        # requiring the computation of the covariance matrix Σ_HD_HD, which is
        # just the matrix of cross-correlations for the observed IMTs, since
        # H is the normalized between-event residual
        corr_HD_HD = cross_correl_between._get_correlation_matrix(bracketed_imts)

        # Using Bayes rule, compute the posterior distribution of the
        # normalized between-event residual H|YD=yD, employing
        # Engler et al. (2022), eqns B8 and B9 (also B18 and B19),
        # H|Y2=y2 is normally distributed with mean and covariance:
        cov_HD_HD_yD = numpy.linalg.pinv(
            numpy.linalg.multi_dot([T_D.T, cov_WD_WD_inv, T_D])
            + numpy.linalg.pinv(corr_HD_HD)
        )
        mu_HD_yD = numpy.linalg.multi_dot([cov_HD_HD_yD, T_D.T, cov_WD_WD_inv, zeta_D])

        # Compute the distribution of the conditional between-event residual B|Y2=y2
        mu_BD_yD = T_D @ mu_HD_yD
        cov_BD_BD_yD = numpy.sqrt(
            numpy.diag(numpy.linalg.multi_dot([T_D, cov_HD_HD_yD, T_D.T]))
        )

        # Get the nominal bias and its variance as the means of the
        # conditional between-event residual mean and covariance
        nominal_bias_mean = numpy.mean(mu_BD_yD)
        nominal_bias_stddev = numpy.sqrt(numpy.mean(cov_BD_BD_yD))
        print(
            target_imt.string,
            "Nominal bias (mean): ",
            "{:.3f}".format(nominal_bias_mean),
        )

        # From the GMMs, get the mean and stddevs at the target sites
        cmaker = ContextMaker(
            rupture.tectonic_region_type,
            [gmm],
            dict(truncation_level=0, imtls={target_imt.string: [0]}),
        )
        gc = GmfComputer(rupture, target_sitecol, cmaker)
        mean_stds = cmaker.get_mean_stds([gc.ctx])[:, 0]
        # (4, G, M, N): mean, StdDev.TOTAL, StdDev.INTER_EVENT, StdDev.INTRA_EVENT; G gsims, M IMTs, N sites/distances

        # Predicted mean at the target sites, from GMM(s)
        mu_Y = mean_stds[0, 0].reshape((-1, 1))
        # Predicted uncertainty components at the target sites, from GMM(s)
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
            target_sitecol,
            station_sitecol,
            [target_imt],
            conditioning_imts,
            spatial_correl,
            cross_correl_within,
            vs30_clustering,
        )
        cov_WY_WD = numpy.linalg.multi_dot(
            [numpy.diag(phi_Y_flat), rho_WY_WD, numpy.diag(phi_D_flat)]
        )

        rho_WD_WY = compute_spatial_cross_correlation_matrix(
            station_sitecol,
            target_sitecol,
            conditioning_imts,
            [target_imt],
            spatial_correl,
            cross_correl_within,
            vs30_clustering,
        )
        cov_WD_WY = numpy.linalg.multi_dot(
            [numpy.diag(phi_D_flat), rho_WD_WY, numpy.diag(phi_Y_flat)]
        )

        # Compute the within-event covariance matrix for the
        # target sites (apriori)
        rho_WY_WY = compute_spatial_cross_correlation_matrix(
            target_sitecol,
            target_sitecol,
            [target_imt],
            [target_imt],
            spatial_correl,
            cross_correl_within,
            vs30_clustering,
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

        # Finally, compute the conditioned mean
        # of the ground motion at the target sites
        mu_Y_yD = mu_Y + mu_BY_yD + RC @ (zeta_D - mu_BD_yD)

        # And compute the conditional covariance
        # of the ground motion at the target sites
        cov_Y_Y_yD = cov_WY_WY_wD + numpy.linalg.multi_dot([C, cov_HD_HD_yD, C.T])

        # Store the results in a dictionary keyed by target IMT
        mu_Y_yD_dict[target_imt.string] = mu_Y_yD
        cov_Y_Y_yD_dict[target_imt.string] = cov_Y_Y_yD

    # Ground motion simulation
    rng = numpy.random.default_rng()
    if truncation_level == 0:
        df = pandas.DataFrame(columns=["custom_site_id", "lon", "lat", "vs30", "PGA"])
        df["custom_site_id"] = numpy.char.decode(target_sitecol.custom_site_id)
        df["lon"] = target_sitecol.lons
        df["lat"] = target_sitecol.lats
        df["vs30"] = target_sitecol.vs30
        for target_imt in target_imts:
            df[target_imt.string] = numpy.exp(mu_Y_yD_dict[target_imt.string])
    else:
        gmfs = {target_imt.string: None for target_imt in target_imts}
        for target_imt in target_imts:
            gmfs[target_imt.string] = rng.multivariate_normal(
                mu_Y_yD_dict[target_imt.string],
                cov_Y_Y_yD_dict[target_imt.string],
                size=num_gmfs,
                check_valid="warn",
                tol=1e-5,
                method="cholesky",
            )

    # Temporary: write the median gmf dataframe to csv
    df.set_index("custom_site_id").to_csv("median-gmf.csv")


def compute_spatial_cross_correlation_matrix(
    sitecol_1,
    sitecol_2,
    imt_list_1,
    imt_list_2,
    spatial_correl,
    cross_correl_within,
    vs30_clustering=False,
):
    # The correlation structure for IMs of differing types at differing locations
    # can be reasonably assumed as Markovian in nature, and we assume here that
    # the correlation between differing IMs at differing locations is simply the
    # product of the cross correlation of IMs i and j at the same location
    # and the spatial correlation due to the distance between sites m and n
    # Can be refactored down the line to support direct spatial cross-correlation
    # models
    distance_matrix = geodetic_distance(
        sitecol_1.lons.reshape(sitecol_1.lons.shape + (1,)),
        sitecol_1.lats.reshape(sitecol_1.lats.shape + (1,)),
        sitecol_2.lons,
        sitecol_2.lats,
    )
    spatial_cross_correlation_matrix = numpy.block(
        [
            [
                _compute_spatial_cross_correlation_matrix(
                    distance_matrix,
                    imt_1,
                    imt_2,
                    spatial_correl,
                    cross_correl_within,
                    vs30_clustering,
                )
                for imt_2 in imt_list_2
            ]
            for imt_1 in imt_list_1
        ]
    )
    return spatial_cross_correlation_matrix


def _compute_spatial_cross_correlation_matrix(
    distance_matrix,
    imt_1,
    imt_2,
    spatial_correl,
    cross_correl_within,
    vs30_clustering=False,
):
    if imt_1 == imt_2:
        # Since we have a single IMT, no cross-correlation terms to be computed
        spatial_correlation_matrix = correlation.jbcorrelation(
            distance_matrix, imt_1, vs30_clustering
        )
        spatial_cross_correlation_matrix = spatial_correlation_matrix
    else:
        spatial_correlation_matrix_1 = correlation.jbcorrelation(
            distance_matrix, imt_1, vs30_clustering
        )
        spatial_correlation_matrix_2 = correlation.jbcorrelation(
            distance_matrix, imt_2, vs30_clustering
        )
        spatial_correlation_matrix = numpy.maximum(
            spatial_correlation_matrix_1, spatial_correlation_matrix_2
        )
        cross_corr_coeff = cross_correl_within.get_correlation(
            from_imt=imt_1, to_imt=imt_2
        )
        spatial_cross_correlation_matrix = spatial_correlation_matrix * cross_corr_coeff
    return spatial_cross_correlation_matrix


if __name__ == "__main__":
    args = sys.argv[1:]
    job_ini = args[0]
    main(job_ini)
