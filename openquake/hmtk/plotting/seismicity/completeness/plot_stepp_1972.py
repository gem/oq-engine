# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
# 
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

#!/usr/bin/env python

'''
Module :mod: 'openquake.hmtk.plotting.seismicity.completeness.plot_stepp_1971'
creates plot to illustrate outcome of Stepp (1972) method for completeness
analysis
'''
import os.path
import numpy as np
import matplotlib.pyplot as plt

valid_markers = ['*', '+', '1', '2', '3', '4', '8', '<', '>', 'D', 'H', '^',
                 '_', 'd', 'h', 'o', 'p', 's', 'v', 'x', '|']

DEFAULT_SIZE = (8., 6.)
DEFAULT_OFFSET = (1.3, 1.0)


def create_stepp_plot(model, filename, filetype='png', filedpi=300):
    '''
    Creates the classic Stepp (1972) plots for a completed Stepp analysis,
    and exports the figure to a file.

    :param model:
        Completed Stepp (1972) analysis as instance of :class:
        'openquake.hmtk.seismicity.completeness.comp_stepp_1971.Stepp1971'
    :param string filename:
        Name of output file
    :param string filetype:
        Type of file (from list supported by matplotlib)
    :param int filedpi:
        Resolution (dots per inch) of output file
    '''
    plt.figure(figsize=DEFAULT_SIZE)
    if os.path.exists(filename):
        raise IOError('File already exists!')

    legend_list = [(str(model.magnitude_bin[iloc] + 0.01) + ' - ' +
                   str(model.magnitude_bin[iloc + 1])) for iloc in range(0,
                   len(model.magnitude_bin) - 1)]

    rgb_list = []
    marker_vals = []
    # Get marker from valid list
    while len(valid_markers) < len(model.magnitude_bin):
        valid_markers.append(valid_markers)

    marker_sampler = np.arange(0, len(valid_markers), 1)
    np.random.shuffle(marker_sampler)
    # Get colour for each bin
    for value in range(0, len(model.magnitude_bin) - 1):
        rgb_samp = np.random.uniform(0., 1., 3)
        rgb_list.append((rgb_samp[0], rgb_samp[1], rgb_samp[2]))
        marker_vals.append(valid_markers[marker_sampler[value]])
    # Plot observed Sigma lambda
    for iloc in range(0, len(model.magnitude_bin) - 1):
        plt.loglog(model.time_values,
                   model.sigma[:, iloc],
                   linestyle='None',
                   marker=marker_vals[iloc],
                   color=rgb_list[iloc])

    lgd = plt.legend(legend_list, bbox_to_anchor=DEFAULT_OFFSET)
    plt.grid(True)
    # Plot expected Poisson rate
    for iloc in range(0, len(model.magnitude_bin) - 1):
        plt.loglog(model.time_values,
                   model.model_line[:, iloc],
                   linestyle='-',
                   marker='None',
                   color=rgb_list[iloc])
        plt.xlim(model.time_values[0] / 2., 2. * model.time_values[-1])
        xmarker = model.end_year - model.completeness_table[iloc, 0]
        id0 = model.model_line[:, iloc] > 0.
        ymarker = 10.0 ** np.interp(np.log10(xmarker),
                                    np.log10(model.time_values[id0]),
                                    np.log10(model.model_line[id0, iloc]))
        plt.loglog(xmarker, ymarker, 'ks')
    plt.xlabel('Time (years)', fontsize=15)
    plt.ylabel("$\\sigma_{\\lambda} = \\sqrt{\\lambda} / \\sqrt{T}$",
               fontsize=15)
    # Save figure to file
    plt.tight_layout()
    plt.savefig(filename, dpi=filedpi, format=filetype,
                bbox_extra_artists=(lgd,), bbox_inches="tight")
