# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import logging
import numpy
import pandas
from scipy.stats import truncnorm
from scipy import interpolate

from openquake.commonlib import readinput
from openquake.hazardlib import imt, correlation
from openquake.hazardlib.cross_correlation import BakerJayaram2008
from openquake.hazardlib.geo.geodetic import geodetic_distance
from openquake.hazardlib import read_input, valid
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.site import SiteCollection

F32 = numpy.float32

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

    vs30_clustering = oqparam.ground_motion_correlation_params["vs30_clustering"]

    observed_imtls = {
        imt_str: [0] for imt_str in observed_imt_strs if imt_str not in ["MMI", "PGV"]
    }
    observed_imts = sorted([imt.from_string(imt_str) for imt_str in observed_imtls])
    cmaker = ContextMaker(
        rupture.tectonic_region_type,
        [gmm],
        dict(truncation_level=0, imtls=observed_imtls),
    )
    spatial_correl = oqparam.ground_motion_correlation_model
    cross_correl = oqparam.cross_correl
    rupture.rup_id = oqparam.ses_seed
    gc = GmfComputer(rupture, station_sitecol, cmaker)
    mean_stds = cmaker.get_mean_stds([gc.ctx])[:, 0]
    # (4, G, M, N): mean, StdDev.TOTAL, StdDev.INTER_EVENT, StdDev.INTRA_EVENT; G gsims, M IMTs, N sites/distances
    for i, imt_i in enumerate(observed_imts):
        station_data.loc[:, (imt_i.string, "median")] = mean_stds[0, i, :]
        station_data.loc[:, (imt_i.string, "sigma")] = mean_stds[1, i, :]
        station_data.loc[:, (imt_i.string, "tau")] = mean_stds[2, i, :]
        station_data.loc[:, (imt_i.string, "phi")] = mean_stds[3, i, :]

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
            native_data_available = True
        else:
            # Find where the target IMT falls in the list of observed IMTs
            all_imts = sorted(observed_imts + [target_imt])
            imt_idx = numpy.where(target_imt == numpy.array(all_imts))[0][0]
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

        # Check if the station data for the IMTs shortlisted for conditioning contains NaNs
        for conditioning_imt in conditioning_imts:
            num_null_values = station_data[conditioning_imt.string]["mean"].isna().sum()
            if num_null_values:
                raise ValueError(
                    f"The station data contains {num_null_values}"
                    f"null values for {target_imt.string}."
                    "Please fill or discard these rows."
                )

        if native_data_available:
            # Observations (recorded values at the stations)
            yD = numpy.log(station_data[target_imt.string]["mean"]).values.reshape(
                (-1, 1)
            )
            # Additional sigma for the observations that are uncertain
            # These arise if the values for this particular IMT were not
            # directly recorded, but obtained by conversion equations or
            # cross-correlation functions
            var_addon_D = (
                station_data[target_imt.string]["std"].values.reshape((-1, 1)) ** 2
            )

            # Predicted mean at the observation points, from GMM(s)
            mu_yD = station_data[target_imt.string]["median"].values.reshape(-1, 1)
            # Predicted uncertainty components at the observation points, from GMM(s)
            phi_D = station_data[target_imt.string].phi.values.reshape(-1, 1)
            tau_D = station_data[target_imt.string].tau.values.reshape(-1, 1)

            # The raw residuals
            zeta_D = yD - mu_yD

            # Compute the station data within-event covariance matrix
            rho_WD_WD = compute_spatial_cross_correlation_matrix(
                [station_sitecol],
                [target_imt],
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
            corr_HD_HD = cross_correl._get_correlation_matrix(conditioning_imts)

            # Using Bayes rule, compute the posterior distribution of the
            # normalized between-event residual H|YD=yD, employing
            # Engler et al. (2022), eqns B8 and B9 (also B18 and B19),
            # H|Y2=y2 is normally distributed with mean and covariance:
            cov_HD_HD_yD = numpy.linalg.pinv(
                numpy.linalg.multi_dot([tau_D.T, cov_WD_WD_inv, tau_D])
                + numpy.linalg.pinv(corr_HD_HD)
            )
            mu_HD_yD = numpy.linalg.multi_dot(
                [cov_HD_HD_yD, tau_D.T, cov_WD_WD_inv, zeta_D]
            )

            # Compute the distribution of the conditional between-event residual B|Y2=y2
            mu_BD_yD = tau_D @ mu_HD_yD
            cov_BD_BD_yD = numpy.sqrt(
                numpy.diag(numpy.linalg.multi_dot([tau_D, cov_HD_HD_yD, tau_D.T]))
            )

            # Get the nominal bias and its variance as the means of the
            # conditional between-event residual mean and covariance
            nominal_bias_mean = numpy.mean(mu_BD_yD)
            nominal_bias_variance = numpy.mean(cov_BD_BD_yD)

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
            mu_BY_yD = tau_Y @ mu_HD_yD

            # Compute the within-event covariance matrix for the
            # target sites and observation sites
            rho_WY_WD = compute_spatial_cross_correlation_matrix(
                [target_sitecol, station_sitecol],
                [target_imt],
                vs30_clustering,
            )
            cov_WY_WD = numpy.linalg.multi_dot(
                [numpy.diag(phi_Y_flat), rho_WY_WD, numpy.diag(phi_D_flat)]
            )

            rho_WD_WY = compute_spatial_cross_correlation_matrix(
                [station_sitecol, target_sitecol],
                [target_imt],
                vs30_clustering,
            )
            cov_WD_WY = numpy.linalg.multi_dot(
                [numpy.diag(phi_D_flat), rho_WD_WY, numpy.diag(phi_Y_flat)]
            )

            # Compute the within-event covariance matrix for the
            # target sites (apriori)
            rho_WY_WY = compute_spatial_cross_correlation_matrix(
                [target_sitecol],
                [target_imt],
                vs30_clustering,
            )
            cov_WY_WY = numpy.linalg.multi_dot(
                [numpy.diag(phi_Y_flat), rho_WY_WY, numpy.diag(phi_Y_flat)]
            )

            # Compute the regression coefficient matrix [cov_WY_WD × cov_WD_WD_inv]
            RC = cov_WY_WD @ cov_WD_WD_inv

            # Compute the scaling matrix "C" for the conditioned between-event
            # covariance matrix
            C = tau_Y - RC @ tau_D

            # Compute the conditioned within-event covariance matrix
            # for the target sites
            cov_WY_WY_wD = cov_WY_WY - RC @ cov_WD_WY

            # Finally, compute the conditioned mean
            # of the ground motion at the target sites
            mu_Y_yD = mu_Y + mu_BY_yD + RC @ (zeta_D - mu_BD_yD)

            # And the conditional covariance
            # of the ground motion at the target sites
            cov_Y_Y_yD = cov_WY_WY_wD + numpy.linalg.multi_dot([C, cov_HD_HD_yD, C.T])

            breakpoint()
        else:
            # No native data available at the stations
            continue


def compute_spatial_cross_correlation_matrix(
    sitecol_list, imt_list, vs30_clustering=False
):
    # The correlation structure for IMs of differing types at differing locations
    # can be reasonably assumed as Markovian in nature, and we assume here that
    # the correlation between differing IMs at differing locations is simply the
    # product of the cross correlation of IMs i and j at the same location
    # and the spatial correlation due to the distance between sites m and n
    # Can be refactored down the line to support direct spatial cross-correlation
    # models
    if len(sitecol_list) == 1:
        distance_matrix = geodetic_distance(
            sitecol_list[0].lons.reshape(sitecol_list[0].lons.shape + (1,)),
            sitecol_list[0].lats.reshape(sitecol_list[0].lats.shape + (1,)),
            sitecol_list[0].lons,
            sitecol_list[0].lats,
        )
    else:
        distance_matrix = geodetic_distance(
            sitecol_list[0].lons.reshape(sitecol_list[0].lons.shape + (1,)),
            sitecol_list[0].lats.reshape(sitecol_list[0].lats.shape + (1,)),
            sitecol_list[1].lons,
            sitecol_list[1].lats,
        )

    if len(imt_list) == 1:
        # Since we have a single IMT, no cross-correlation terms to be computed
        spatial_correlation_matrix = correlation.jbcorrelation(
            distance_matrix, imt_list[0], vs30_clustering
        )
        spatial_cross_correlation_matrix = spatial_correlation_matrix
    else:
        spatial_correlation_matrix_1 = correlation.jbcorrelation(
            distance_matrix, imt_list[0], vs30_clustering
        )
        spatial_correlation_matrix_2 = correlation.jbcorrelation(
            distance_matrix, imt_list[1], vs30_clustering
        )
        spatial_correlation_matrix = numpy.maximum(
            spatial_correlation_matrix_1, spatial_correlation_matrix_2
        )
        cross_correlation = BakerJayaram2008.get_cross_correlation(
            imt_list[0], imt_list[1]
        )
        spatial_cross_correlation_matrix = numpy.block(
            [
                [
                    spatial_correlation_matrix,
                    spatial_correlation_matrix * cross_correlation,
                ],
                [
                    spatial_correlation_matrix * cross_correlation,
                    spatial_correlation_matrix,
                ],
            ]
        )
    return spatial_cross_correlation_matrix


if __name__ == "__main__":
    job_ini = "examples/puebla/job_rupture_Melgar_et_al_2018.ini"
    main(job_ini)
