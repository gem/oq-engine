# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2019 GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Collection of tools for plotting descriptive statistics of a catalogue
"""
import os

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize

from openquake.hmtk.seismicity.occurrence.utils import get_completeness_counts


def build_filename(filename, filetype='png', resolution=300):
    """
    Uses the input properties to create the string of the filename

    :param str filename:
        Name of the file
    :param str filetype:
        Type of file
    :param int resolution:
        DPI resolution of the output figure
    """
    filevals = os.path.splitext(filename)
    if filevals[1]:
        filetype = filevals[1][1:]
    if not filetype:
        filetype = 'png'
    filename = filevals[0] + '.' + filetype

    if not resolution:
        resolution = 300
    return filename, filetype, resolution


def _save_image(fig, filename, filetype='png', resolution=300):
    """
    If filename is specified, saves the image
    :param str filename:
        Name of the file
    :param str filetype:
        Type of file
    :param int resolution:
        DPI resolution of the output figure
    """
    if filename:
        filename, filetype, resolution = build_filename(filename,
                                                        filetype,
                                                        resolution)
        fig.savefig(filename, dpi=resolution, format=filetype)
    else:
        pass


def _get_catalogue_bin_limits(catalogue, dmag):
    """
    Returns the magnitude bins corresponing to the catalogue
    """
    mag_bins = np.arange(
        float(np.floor(np.min(catalogue.data['magnitude']))) - dmag,
        float(np.ceil(np.max(catalogue.data['magnitude']))) + dmag,
        dmag)
    counter = np.histogram(catalogue.data['magnitude'], mag_bins)[0]
    idx = np.where(counter > 0)[0]
    mag_bins = mag_bins[idx[0]:(idx[-1] + 2)]
    return mag_bins


def plot_depth_histogram(
        catalogue, bin_width,
        normalisation=False, bootstrap=None, filename=None,
        figure_size=(8, 6), filetype='png', dpi=300, ax=None):
    """
    Creates a histogram of the depths in the catalogue

    :param catalogue:
        Earthquake catalogue as instance of :class:
        openquake.hmtk.seismicity.catalogue.Catalogue
    :param float bin_width:
        Width of the histogram for the depth bins
    :param bool normalisation:
        Normalise the histogram to give output as PMF (True) or count (False)
    :param int bootstrap:
        To sample depth uncertainty choose number of samples
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figure_size)
    else:
        fig = ax.get_figure()
    # Create depth range
    if len(catalogue.data['depth']) == 0:  # pylint: disable=len-as-condition
        raise ValueError('No depths reported in catalogue!')
    depth_bins = np.arange(0.,
                           np.max(catalogue.data['depth']) + bin_width,
                           bin_width)
    depth_hist = catalogue.get_depth_distribution(depth_bins,
                                                  normalisation,
                                                  bootstrap)
    ax.bar(depth_bins[:-1],
           depth_hist,
           width=0.95 * bin_width,
           edgecolor='k')
    ax.set_xlabel('Depth (km)')
    if normalisation:
        ax.set_ylabel('Probability Mass Function')
    else:
        ax.set_ylabel('Count')
    ax.set_title('Depth Histogram')

    _save_image(fig, filename, filetype, dpi)


def plot_magnitude_depth_density(
        catalogue, mag_int, depth_int,
        logscale=False, normalisation=False, bootstrap=None, filename=None,
        figure_size=(8, 6), filetype='png', dpi=300, ax=None):
    """
    Creates a density plot of the magnitude and depth distribution

    :param catalogue:
        Earthquake catalogue as instance of :class:
        openquake.hmtk.seismicity.catalogue.Catalogue
    :param float mag_int:
        Width of the histogram for the magnitude bins
    :param float depth_int:
        Width of the histogram for the depth bins
    :param bool logscale:
        Choose to scale the colours in a log-scale (True) or linear (False)
    :param bool normalisation:
        Normalise the histogram to give output as PMF (True) or count (False)
    :param int bootstrap:
        To sample magnitude and depth uncertainties choose number of samples
    """
    if len(catalogue.data['depth']) == 0:  # pylint: disable=len-as-condition
        raise ValueError('No depths reported in catalogue!')
    depth_bins = np.arange(0.,
                           np.max(catalogue.data['depth']) + depth_int,
                           depth_int)
    mag_bins = _get_catalogue_bin_limits(catalogue, mag_int)
    mag_depth_dist = catalogue.get_magnitude_depth_distribution(mag_bins,
                                                                depth_bins,
                                                                normalisation,
                                                                bootstrap)
    vmin_val = np.min(mag_depth_dist[mag_depth_dist > 0.])

    if ax is None:
        fig, ax = plt.subplots(figsize=figure_size)
    else:
        fig = ax.get_figure()

    if logscale:
        normaliser = LogNorm(vmin=vmin_val, vmax=np.max(mag_depth_dist))
    else:
        normaliser = Normalize(vmin=0, vmax=np.max(mag_depth_dist))

    im = ax.pcolor(mag_bins[:-1],
                   depth_bins[:-1],
                   mag_depth_dist.T,
                   norm=normaliser)
    ax.set_xlabel('Magnitude')
    ax.set_ylabel('Depth (km)')
    ax.set_xlim(mag_bins[0], mag_bins[-1])
    ax.set_ylim(depth_bins[0], depth_bins[-1])
    fig.colorbar(im, ax=ax)
    if normalisation:
        ax.set_title('Magnitude-Depth Density')
    else:
        ax.set_title('Magnitude-Depth Count')

    _save_image(fig, filename, filetype, dpi)


def plot_magnitude_time_scatter(
        catalogue, plot_error=False, fmt_string='o', filename=None,
        figure_size=(8, 6), filetype='png', dpi=300, ax=None):
    """
    Creates a simple scatter plot of magnitude with time

    :param catalogue:
        Earthquake catalogue as instance of :class:
        openquake.hmtk.seismicity.catalogue.Catalogue
    :param bool plot_error:
        Choose to plot error bars (True) or not (False)
    :param str fmt_string:
        Symbology of plot
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figure_size)
    else:
        fig = ax.get_figure()

    dtime = catalogue.get_decimal_time()
    # pylint: disable=len-as-condition
    if len(catalogue.data['sigmaMagnitude']) == 0:
        print('Magnitude Error is missing - neglecting error bars!')
        plot_error = False

    if plot_error:
        ax.errorbar(dtime,
                    catalogue.data['magnitude'],
                    xerr=None,
                    yerr=catalogue.data['sigmaMagnitude'],
                    fmt=fmt_string)
    else:
        ax.plot(dtime, catalogue.data['magnitude'], fmt_string)
    ax.set_xlabel('Year')
    ax.set_ylabel('Magnitude')
    ax.set_title('Magnitude-Time Plot')

    _save_image(fig, filename, filetype, dpi)


def plot_magnitude_time_density(
        catalogue, mag_int, time_int, completeness=None,
        normalisation=False, logscale=True, bootstrap=None, xlim=[], ylim=[],
        filename=None, figure_size=(8, 6), filetype='png', dpi=300, ax=None):
    """
    Creates a plot of magnitude-time density

    :param catalogue:
        Earthquake catalogue as instance of :class:
        openquake.hmtk.seismicity.catalogue.Catalogue
    :param float mag_int:
        Width of the histogram for the magnitude bins
    :param float time_int:
        Width of the histogram for the time bin (in decimal years)
    :param bool normalisation:
        Normalise the histogram to give output as PMF (True) or count (False)
    :param int bootstrap:
        To sample magnitude and depth uncertainties choose number of samples
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figure_size)
    else:
        fig = ax.get_figure()

    # Create the magnitude bins
    if isinstance(mag_int, (np.ndarray, list)):
        mag_bins = mag_int
    else:
        mag_bins = np.arange(
            np.min(catalogue.data['magnitude']),
            np.max(catalogue.data['magnitude']) + mag_int / 2.,
            mag_int)
    # Creates the time bins
    if isinstance(time_int, (np.ndarray, list)):
        time_bins = time_int
    else:
        time_bins = np.arange(
            float(np.min(catalogue.data['year'])),
            float(np.max(catalogue.data['year'])) + 1.,
            float(time_int))
    # Get magnitude-time distribution
    mag_time_dist = catalogue.get_magnitude_time_distribution(
        mag_bins,
        time_bins,
        normalisation,
        bootstrap)
    # Get smallest non-zero value
    vmin_val = np.min(mag_time_dist[mag_time_dist > 0.])
    # Create plot
    if logscale:
        norm_data = LogNorm(vmin=vmin_val, vmax=np.max(mag_time_dist))
    else:
        if normalisation:
            norm_data = Normalize(vmin=vmin_val, vmax=np.max(mag_time_dist))
        else:
            norm_data = Normalize(vmin=1.0, vmax=np.max(mag_time_dist))

    im = ax.pcolor(time_bins[:-1],
                   mag_bins[:-1],
                   mag_time_dist.T,
                   norm=norm_data)
    ax.set_xlabel('Time (year)')
    ax.set_ylabel('Magnitude')
    if len(xlim) == 2:
        ax.set_xlim(xlim[0], xlim[1])
    else:
        ax.set_xlim(time_bins[0], time_bins[-1])
    if len(ylim) == 2:
        ax.set_ylim(ylim[0], ylim[1])
    else:
        ax.set_ylim(mag_bins[0], mag_bins[-1] + (mag_bins[-1] - mag_bins[-2]))
    # Fix the title
    if normalisation:
        fig.colorbar(im, label='Event Density', shrink=0.9, ax=ax)
    else:
        fig.colorbar(im, label='Event Count', shrink=0.9, ax=ax)
    ax.grid(True)
    # Plot completeness
    if completeness is not None:
        _plot_completeness(ax, completeness, time_bins[0], time_bins[-1])

    _save_image(fig, filename, filetype, dpi)


def _plot_completeness(ax, comw, start_time, end_time):
    '''
    Adds completeness intervals to a plot
    '''
    comw = np.array(comw)
    comp = np.column_stack([np.hstack([end_time, comw[:, 0], start_time]),
                            np.hstack([comw[0, 1], comw[:, 1], comw[-1, 1]])])
    ax.step(comp[:-1, 0], comp[1:, 1], linestyle='-',
            where="post", linewidth=3, color='brown')


def get_completeness_adjusted_table(catalogue, completeness, dmag,
                                    offset=1.0E-5, end_year=None, plot=False,
                                    figure_size=(8, 6), filename=None,
                                    filetype='png', dpi=300, ax=None):
    """
    Counts the number of earthquakes in each magnitude bin and normalises
    the rate to annual rates, taking into account the completeness
    """
    if not end_year:
        end_year = catalogue.end_year
    # Find the natural bin limits
    mag_bins = _get_catalogue_bin_limits(catalogue, dmag)
    obs_time = end_year - completeness[:, 0] + 1.
    obs_rates = np.zeros_like(mag_bins)
    durations = np.zeros_like(mag_bins)
    n_comp = np.shape(completeness)[0]
    for iloc in range(n_comp):
        low_mag = completeness[iloc, 1]
        comp_year = completeness[iloc, 0]
        if iloc == (n_comp - 1):
            idx = np.logical_and(
                catalogue.data['magnitude'] >= low_mag - offset,
                catalogue.data['year'] >= comp_year)
            high_mag = mag_bins[-1]
            obs_idx = mag_bins >= (low_mag - offset)
        else:
            high_mag = completeness[iloc + 1, 1]
            mag_idx = np.logical_and(
                catalogue.data['magnitude'] >= low_mag - offset,
                catalogue.data['magnitude'] < (high_mag - offset))

            idx = np.logical_and(mag_idx,
                                 catalogue.data['year'] >= (comp_year - offset))
            obs_idx = np.logical_and(mag_bins >= (low_mag - offset),
                                     mag_bins < (high_mag + offset))
        temp_rates = np.histogram(catalogue.data['magnitude'][idx],
                                  mag_bins[obs_idx])[0]
        temp_rates = temp_rates.astype(float) / obs_time[iloc]
        obs_rates[obs_idx[:-1]] = temp_rates
        durations[obs_idx[:-1]] = obs_time[iloc]
    selector = np.where(obs_rates > 0.)[0]
    mag_bins = mag_bins[selector]
    obs_rates = obs_rates[selector]
    durations = durations[selector]
    # Get cumulative rates
    cum_rates = np.array([sum(obs_rates[iloc:])
                          for iloc in range(0, len(obs_rates))])
    if plot:
        plt.figure(figsize=figure_size)
        plt.semilogy(mag_bins + dmag / 2., obs_rates, "bo",
                     label="Incremental")
        plt.semilogy(mag_bins + dmag / 2., cum_rates, "rs",
                     label="Cumulative")
        plt.xlabel("Magnitude (M)", fontsize=16)
        plt.ylabel("Annual Rate", fontsize=16)
        plt.grid(True)
        plt.legend(fontsize=16)
        if filename:
            plt.savefig(filename, format=filetype, dpi=dpi,
                        bbox_inches="tight")
    return np.column_stack([mag_bins, durations, obs_rates, cum_rates,
                            np.log10(cum_rates)])


def plot_observed_recurrence(
        catalogue, completeness, dmag, end_year=None, filename=None,
        figure_size=(8, 6), filetype='png', dpi=300, ax=None):
    """
    Plots the observed recurrence taking into account the completeness
    """
    # Get completeness adjusted recurrence table
    if isinstance(completeness, float):
        # Unique completeness
        completeness = np.array([[np.min(catalogue.data['year']),
                                  completeness]])
    if not end_year:
        end_year = catalogue.update_end_year()
    catalogue.data["dtime"] = catalogue.get_decimal_time()
    cent_mag, t_per, n_obs = get_completeness_counts(catalogue,
                                                     completeness,
                                                     dmag)
    obs_rates = n_obs / t_per
    cum_obs_rates = np.array([np.sum(obs_rates[i:])
                              for i in range(len(obs_rates))])

    if ax is None:
        fig, ax = plt.subplots(figsize=figure_size)
    else:
        fig = ax.get_figure()

    ax.semilogy(cent_mag, obs_rates, 'bo', label="Incremental")
    ax.semilogy(cent_mag, cum_obs_rates, 'rs', label="Cumulative")
    ax.set_xlim([cent_mag[0] - 0.1, cent_mag[-1] + 0.1])
    ax.set_xlabel('Magnitude')
    ax.set_ylabel('Annual Rate')
    ax.legend()
    _save_image(fig, filename, filetype, dpi)
