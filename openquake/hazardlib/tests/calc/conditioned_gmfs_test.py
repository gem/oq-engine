# The Hazard Library
# Copyright (C) 2023 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Test cases 01–10 are based on the verification tests described in the
USGS ShakeMap 4.1 Manual.
Ref: Worden, C. B., E. M. Thompson, M. Hearne, and D. J. Wald (2020). 
ShakeMap Manual Online: technical manual, user’s guide, and software guide, 
U.S. Geological Survey. DOI: https://doi.org/10.5066/F7D21VPQ, see
https://usgs.github.io/shakemap/manual4_0/tg_verification.html`.
"""
import unittest

import numpy

from openquake.hazardlib.calc.conditioned_gmfs import get_ms_and_sids
from openquake.hazardlib.tests.calc import \
    _conditioned_gmfs_test_data as test_data

aac = numpy.testing.assert_allclose

def get_mean_covs(rup, gmm, *args):
    ms, sids = get_ms_and_sids(rup, [gmm], *args)
    return ms[gmm]


class SetUSGSTestCase(unittest.TestCase):
    def test_case_01(self):
        case_name = "test_case_01"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE01_STATION_SITECOL
        station_data = test_data.CASE01_STATION_DATA
        observed_imt_strs = test_data.CASE01_OBSERVED_IMTS
        target_sitecol = test_data.CASE01_TARGET_SITECOL
        target_imts = test_data.CASE01_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_mean_covs(
            rupture, gmm, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within,
            maximum_distance)
        mu = mean_covs[0][target_imts[0].string].flatten()
        sig = numpy.sqrt(numpy.diag(mean_covs[1][target_imts[0].string]))
        aac(numpy.zeros_like(mu), mu)
        numpy.testing.assert_almost_equal(numpy.min(sig), 0)
        assert numpy.max(sig) > 0.8 and numpy.max(sig) < 1.0
        plot_test_results(target_sitecol.lons, mu, sig, target_imts[0].string,
                          case_name)
        
    def test_case_02(self):
        case_name = "test_case_02"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE02_STATION_SITECOL
        station_data = test_data.CASE02_STATION_DATA
        observed_imt_strs = test_data.CASE02_OBSERVED_IMTS
        target_sitecol = test_data.CASE02_TARGET_SITECOL
        target_imts = test_data.CASE02_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_mean_covs(
            rupture, gmm, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within,
            maximum_distance)
        mu = mean_covs[0][target_imts[0].string].flatten()
        sig = numpy.sqrt(numpy.diag(mean_covs[1][target_imts[0].string]))
        aac(numpy.min(mu), -1, rtol=1e-4)
        aac(numpy.max(mu), 1, rtol=1e-4)
        aac(numpy.min(numpy.abs(mu)), 0, atol=1e-4)
        aac(numpy.min(sig), 0, atol=1e-4)
        assert numpy.max(sig) > 0.8 and numpy.max(sig) < 1.0
        plot_test_results(target_sitecol.lons, mu, sig, target_imts[0].string,
                          case_name)

    def test_case_03(self):
        case_name = "test_case_03"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE03_STATION_SITECOL
        station_data = test_data.CASE03_STATION_DATA
        observed_imt_strs = test_data.CASE03_OBSERVED_IMTS
        target_sitecol = test_data.CASE03_TARGET_SITECOL
        target_imts = test_data.CASE03_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_mean_covs(
            rupture, gmm, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within,
            maximum_distance)
        mu = mean_covs[0][target_imts[0].string].flatten()
        sig = numpy.sqrt(numpy.diag(mean_covs[1][target_imts[0].string]))
        aac(numpy.min(mu), 0.36, rtol=1e-4)
        aac(numpy.max(mu), 1, rtol=1e-4)
        aac(numpy.min(sig), 0, rtol=1e-4)
        aac(numpy.max(sig), numpy.sqrt(0.8704), rtol=1e-4)
        plot_test_results(target_sitecol.lons, mu, sig, target_imts[0].string,
                          case_name)

    def test_case_04(self):
        case_name = "test_case_04"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE04_STATION_SITECOL
        station_data = test_data.CASE04_STATION_DATA
        observed_imt_strs = test_data.CASE04_OBSERVED_IMTS
        target_sitecol = test_data.CASE04_TARGET_SITECOL
        target_imts = test_data.CASE04_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_mean_covs(
            rupture, gmm, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within,
            maximum_distance)
        mu = mean_covs[0][target_imts[0].string].flatten()
        sig = numpy.sqrt(numpy.diag(mean_covs[1][target_imts[0].string]))
        aac(numpy.min(mu), 0.36, rtol=1e-4)
        aac(numpy.max(mu), 1)
        aac(numpy.min(sig), 0, atol=1e-4)
        aac(numpy.max(sig), numpy.sqrt(0.8704), rtol=1e-4)
        plot_test_results(target_sitecol.lons, mu, sig, target_imts[0].string,
                          case_name)

    def test_case_04b(self):
        case_name = "test_case_04b"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE04B_STATION_SITECOL
        station_data = test_data.CASE04_STATION_DATA
        observed_imt_strs = test_data.CASE04_OBSERVED_IMTS
        target_sitecol = test_data.CASE04_TARGET_SITECOL
        target_imts = test_data.CASE04_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_mean_covs(
            rupture, gmm, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within,
            maximum_distance)
        mu = mean_covs[0][target_imts[0].string].flatten()
        sig = numpy.sqrt(numpy.diag(mean_covs[1][target_imts[0].string]))
        aac(numpy.min(mu), 0.52970, rtol=1e-4)
        aac(numpy.max(mu), 1)
        aac(numpy.min(sig), 0, atol=1e-4)
        aac(numpy.max(sig), 0.89955, rtol=1e-4)
        plot_test_results(target_sitecol.lons, mu, sig, target_imts[0].string,
                          case_name)

    def test_case_05(self):
        case_name = "test_case_05"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE05_STATION_SITECOL
        station_data = test_data.CASE05_STATION_DATA
        observed_imt_strs = test_data.CASE05_OBSERVED_IMTS
        target_sitecol = test_data.CASE05_TARGET_SITECOL
        target_imts = test_data.CASE05_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_mean_covs(
            rupture, gmm, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within,
            maximum_distance)
        mu = mean_covs[0][target_imts[0].string].flatten()
        sig = numpy.sqrt(numpy.diag(mean_covs[1][target_imts[0].string]))
        aac(numpy.zeros_like(mu), mu, atol=1e-4)
        aac(numpy.min(sig), 0, atol=1e-4)
        aac(numpy.max(sig), numpy.sqrt(0.8704), rtol=1e-4)
        plot_test_results(target_sitecol.lons, mu, sig, target_imts[0].string,
                          case_name)

    def test_case_06(self):
        case_name = "test_case_06"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE06_STATION_SITECOL
        station_data = test_data.CASE06_STATION_DATA
        observed_imt_strs = test_data.CASE06_OBSERVED_IMTS
        target_sitecol = test_data.CASE06_TARGET_SITECOL
        target_imts = test_data.CASE06_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_mean_covs(
            rupture, gmm, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within,
            maximum_distance)
        mu = mean_covs[0][target_imts[0].string].flatten()
        sig = numpy.sqrt(numpy.diag(mean_covs[1][target_imts[0].string]))
        plot_test_results(target_sitecol.lons, mu, sig, target_imts[0].string,
                          case_name)

    def test_case_07(self):
        case_name = "test_case_07"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE07_STATION_SITECOL
        station_data = test_data.CASE07_STATION_DATA
        observed_imt_strs = test_data.CASE07_OBSERVED_IMTS
        target_sitecol = test_data.CASE07_TARGET_SITECOL
        target_imts = test_data.CASE07_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_mean_covs(
            rupture, gmm, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within,
            maximum_distance)
        mu = [mu[0][0] for mu in mean_covs[0].values()]
        sig = numpy.sqrt([var[0][0] for var in mean_covs[1].values()])
        periods = [imt.period for imt in target_imts]
        plot_test_results_spectra(periods, mu, sig, case_name)

    def test_case_08(self):
        case_name = "test_case_08"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE08_STATION_SITECOL
        station_data_list = test_data.CASE08_STATION_DATA_LIST
        observed_imt_strs = test_data.CASE08_OBSERVED_IMTS
        target_sitecol = test_data.CASE08_TARGET_SITECOL
        target_imts = test_data.CASE08_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        std_addon_d = test_data.CASE08_STD_ADDON_D
        bias_mean = test_data.CASE08_BD_YD
        conditioned_mean_obs = test_data.CASE08_MU_YD_OBS
        conditioned_std_obs = test_data.CASE08_SIG_YD_OBS
        conditioned_std_far = test_data.CASE08_SIG_YD_FAR
        mus = []
        sigs = []
        for i, station_data in enumerate(station_data_list):
            mean_covs = get_mean_covs(
                rupture, gmm, station_sitecol, station_data,
                observed_imt_strs, target_sitecol, target_imts,
                spatial_correl, cross_correl_between, cross_correl_within,
                maximum_distance)
            mu = mean_covs[0][target_imts[0].string].flatten()
            sig = numpy.sqrt(numpy.diag(mean_covs[1][target_imts[0].string]))
            aac(numpy.min(mu), bias_mean[i], rtol=1e-4)
            aac(numpy.max(mu), conditioned_mean_obs[i], rtol=1e-4)
            aac(numpy.min(sig), conditioned_std_obs[i], rtol=1e-4)
            aac(numpy.max(sig), conditioned_std_far[i], rtol=1e-4)
            mus.append(mu)
            sigs.append(sig)
        plot_test_results_multi(target_sitecol.lons, mus, sigs, std_addon_d,
                                target_imts[0].string, case_name)

    def test_case_09(self):
        case_name = "test_case_09"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE09_STATION_SITECOL
        station_data = test_data.CASE09_STATION_DATA
        observed_imt_strs = test_data.CASE09_OBSERVED_IMTS
        target_sitecol = test_data.CASE09_TARGET_SITECOL
        target_imts = test_data.CASE09_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_mean_covs(
            rupture, gmm, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within,
            maximum_distance)
        mu = mean_covs[0][target_imts[0].string].flatten()
        sig = numpy.sqrt(numpy.diag(mean_covs[1][target_imts[0].string]))
        plot_test_results(target_sitecol.lons, mu, sig, target_imts[0].string,
                          case_name)

    def test_case_10(self):
        case_name = "test_case_10"
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE10_STATION_SITECOL
        station_data = test_data.CASE10_STATION_DATA
        observed_imt_strs = test_data.CASE10_OBSERVED_IMTS
        target_sitecol = test_data.CASE10_TARGET_SITECOL
        target_imts = test_data.CASE10_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_mean_covs(
            rupture, gmm, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within,
            maximum_distance)
        mu = mean_covs[0][target_imts[0].string].flatten()
        sig = numpy.sqrt(numpy.diag(mean_covs[1][target_imts[0].string]))
        plot_test_results(target_sitecol.lons, mu, sig, target_imts[0].string,
                          case_name)


# Functions useful for debugging purposes. Recreates the plots on
# https://usgs.github.io/shakemap/manual4_0/tg_verification.html
# Original code is from the ShakeMap plotting modules 
# XTestPlot, XTestPlotSpectra, and XTestPlotMulti:
# https://github.com/usgs/shakemap/blob/main/shakemap/coremods/xtestplot.py
# https://github.com/usgs/shakemap/blob/main/shakemap/coremods/xtestplot_spectra.py
# https://github.com/usgs/shakemap/blob/main/shakemap/coremods/xtestplot_multi.py
def plot_test_results(lons, means, stds, target_imt, case_name):
    return  # remove the return to enable debug plotting
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, sharex=True, figsize=(10, 8))
    plt.subplots_adjust(hspace=0.1)
    ax[0].plot(lons, means, color="k", label="mean")
    ax[0].plot(
        lons, means + stds, "--b", label="mean +/- stddev"
    )
    ax[0].plot(lons, means - stds, "--b")
    ax[1].plot(lons, stds, "-.r", label="stddev")
    plt.xlabel("Longitude")
    ax[0].set_ylabel(f"Mean ln({target_imt}) (g)")
    ax[1].set_ylabel(f"Stddev ln({target_imt}) (g)")
    ax[0].legend(loc="best")
    ax[1].legend(loc="best")
    ax[0].set_title(case_name)
    ax[0].grid()
    ax[1].grid()
    ax[1].set_ylim(bottom=0)
    plt.show()


def plot_test_results_spectra(periods, means, stds, case_name):
    return  # remove the return to show the plot
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, sharex=True, figsize=(10, 8))
    plt.subplots_adjust(hspace=0.1)
    ax[0].semilogx(periods, means, color="k", label="mean")
    ax[0].semilogx(
        periods, means + stds, "--b", label="mean +/- stddev"
    )
    ax[0].semilogx(periods, means - stds, "--b")
    ax[1].semilogx(periods, stds, "-.r", label="stddev")
    plt.xlabel("Period (s)")
    ax[0].set_ylabel("Mean ln(SA) (g)")
    ax[1].set_ylabel("Stddev ln(SA) (g)")
    ax[0].legend(loc="best")
    ax[1].legend(loc="best")
    ax[0].set_title(case_name)
    ax[0].grid()
    ax[1].grid()
    ax[1].set_ylim(bottom=0)
    plt.show()


def plot_test_results_multi(lons, means_list, stds_list, std_addon, target_imt,
                            case_name):
    return  # remove the return to show the plot
    import matplotlib.pyplot as plt
    colors = ["k", "b", "g", "r", "c", "m"]
    fig, ax = plt.subplots(2, sharex=True, figsize=(10, 8))
    plt.subplots_adjust(hspace=0.1)
    for i in range(len(means_list)):
        means = means_list[i]
        stds = stds_list[i]
        ax[0].plot(lons, means, color=colors[i],
                   label=r"$\sigma_\epsilon = %.2f$" % std_addon[i])
        ax[1].plot(lons, stds, "-.", color=colors[i],
                   label=r"$\sigma_\epsilon = %.2f$" % std_addon[i])
    plt.xlabel("Longitude")
    ax[0].set_ylabel(f"Mean ln({target_imt}) (g)")
    ax[1].set_ylabel(f"Stddev ln({target_imt}) (g)")
    ax[0].legend(loc="best")
    ax[1].legend(loc="best")
    ax[0].set_title(case_name)
    ax[0].grid()
    ax[1].grid()
    ax[1].set_ylim(bottom=0)
    plt.show()
