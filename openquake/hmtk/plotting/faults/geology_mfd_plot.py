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

"""

import numpy as np
import matplotlib.pyplot as plt
from openquake.hmtk.faults.fault_models import RecurrenceBranch
from openquake.hmtk.plotting.seismicity.catalogue_plots import _save_image


#
# def _get_occurence_array(mmin, bin_width, occurrence):
#    """
#    Returns the incremental and cumulative recurrence
#    """
#    mags = mmin + np.cumsum(bin_width * np.ones(len(occurrence))) - bin_width
#    cumulative = np.array([np.sum(occurrence[iloc:])
#                           for iloc in range(0, len(occurrence))])
#    return np.column_stack([mags, occurrence, cumulative])
#

def plot_recurrence_models(
        configs, area, slip, msr, rake,
        shear_modulus=30.0, disp_length_ratio=1.25E-5, msr_sigma=0.,
        figure_size=(8, 6), filename=None, filetype='png', dpi=300, ax=None):
    """
    Plots a set of recurrence models

    :param list configs:
        List of configuration dictionaries
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figure_size)
    else:
        fig = ax.get_figure()

    for config in configs:
        model = RecurrenceBranch(area, slip, msr, rake, shear_modulus,
                                 disp_length_ratio, msr_sigma, weight=1.0)
        model.get_recurrence(config)
        occurrence = model.recurrence.occur_rates
        cumulative = np.array([np.sum(occurrence[iloc:])
                               for iloc in range(0, len(occurrence))])
        if 'AndersonLuco' in config['Model_Name']:
            flt_label = config['Model_Name'] + ' - ' + config['Model_Type'] +\
                ' Type'
        else:
            flt_label = config['Model_Name']
        flt_color = np.random.uniform(0.1, 1.0, 3)
        ax.semilogy(model.magnitudes, cumulative, '-', label=flt_label,
                    color=flt_color, linewidth=2.)
        ax.semilogy(model.magnitudes, model.recurrence.occur_rates, '--',
                    color=flt_color, linewidth=2.)

    ax.set_xlabel('Magnitude')
    ax.set_ylabel('Annual Rate')
    ax.legend(bbox_to_anchor=(1.1, 1.0))
    _save_image(fig, filename, filetype, dpi)
