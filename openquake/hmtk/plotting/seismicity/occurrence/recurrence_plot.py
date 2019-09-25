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
Simple plots for the recurrence model
"""

import numpy as np
import matplotlib.pyplot as plt
from openquake.hmtk.plotting.seismicity.catalogue_plots import _save_image
from openquake.hmtk.seismicity.occurrence.utils import get_completeness_counts
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD
from openquake.hazardlib.mfd.evenly_discretized import EvenlyDiscretizedMFD
from openquake.hazardlib.mfd.youngs_coppersmith_1985 import\
    YoungsCoppersmith1985MFD


def _get_recurrence_model(input_model):
    """
    Returns the annual and cumulative recurrence rates predicted by the
    recurrence model
    """
    if not isinstance(input_model, (TruncatedGRMFD,
                                    EvenlyDiscretizedMFD,
                                    YoungsCoppersmith1985MFD)):
        raise ValueError('Recurrence model not recognised')
    # Get model annual occurrence rates
    annual_rates = input_model.get_annual_occurrence_rates()
    annual_rates = np.array([[val[0], val[1]] for val in annual_rates])
    # Get cumulative rates
    cumulative_rates = np.array([np.sum(annual_rates[iloc:, 1])
                                 for iloc in range(0, len(annual_rates), 1)])
    return annual_rates, cumulative_rates


def _check_completeness_table(completeness, catalogue):
    """
    Generates the completeness table according to different instances
    """
    if isinstance(completeness, np.ndarray) and np.shape(completeness)[1] == 2:
        return completeness
    elif isinstance(completeness, float):
        return np.array([[float(np.min(catalogue.data['year'])),
                          completeness]])
    elif completeness is None:
        return np.array([[float(np.min(catalogue.data['year'])),
                          np.min(catalogue.data['magnitude'])]])
    else:
        raise ValueError('Completeness representation not recognised')


def plot_recurrence_model(
        input_model, catalogue, completeness, dmag=0.1, filename=None,
        figure_size=(8, 6), filetype='png', dpi=300, ax=None):
    """
    Plot a calculated recurrence model over an observed catalogue, adjusted for
    time-varying completeness
    """
    annual_rates, cumulative_rates = _get_recurrence_model(input_model)

    # Get observed annual recurrence
    if not catalogue.end_year:
        catalogue.update_end_year()
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

    ax.semilogy(cent_mag, obs_rates, 'bo')
    ax.semilogy(annual_rates[:, 0], annual_rates[:, 1], 'b-')
    ax.semilogy(cent_mag, cum_obs_rates, 'rs')
    ax.semilogy(annual_rates[:, 0], cumulative_rates, 'r-')
    ax.grid(which='both')
    ax.set_xlabel('Magnitude')
    ax.set_ylabel('Annual Rate')
    ax.legend(['Observed Incremental Rate',
               'Model Incremental Rate',
               'Observed Cumulative Rate',
               'Model Cumulative Rate'])
    ax.tick_params(labelsize=12)
    _save_image(fig, filename, filetype, dpi)


def plot_trunc_gr_model(
        aval, bval, min_mag, max_mag, dmag,
        catalogue=None, completeness=None, filename=None,
        figure_size=(8, 6), filetype='png', dpi=300, ax=None):
    """
    Plots a Gutenberg-Richter model
    """
    input_model = TruncatedGRMFD(min_mag, max_mag, dmag, aval, bval)
    if not catalogue:
        # Plot only the modelled recurrence
        annual_rates, cumulative_rates = _get_recurrence_model(input_model)

        if ax is None:
            fig, ax = plt.subplots(figsize=figure_size)
        else:
            fig = ax.get_figure()

        ax.semilogy(annual_rates[:, 0], annual_rates[:, 1], 'b-')
        ax.semilogy(annual_rates[:, 0], cumulative_rates, 'r-')
        ax.xlabel('Magnitude')
        ax.set_ylabel('Annual Rate')
        ax.set_legend(['Incremental Rate', 'Cumulative Rate'])
        _save_image(fig, filename, filetype, dpi)

    else:
        completeness = _check_completeness_table(completeness, catalogue)
        plot_recurrence_model(
            input_model, catalogue, completeness, dmag, filename=filename,
            figure_size=figure_size, filetype=filetype, dpi=dpi, ax=ax)
