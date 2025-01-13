# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Module :mod: 'openquake.hmtk.plotting.seismicity.completeness.plot_stepp_1971'
creates plot to illustrate outcome of Stepp (1972) method for completeness
analysis
"""
import os.path
import itertools

import numpy as np
import matplotlib.pyplot as plt

# markers which can be filled or empty
VALID_MARKERS = [
    "s",
    "o",
    "^",
    "D",
    "p",
    "h",
    "8",
    "*",
    "d",
    "v",
    "<",
    ">",
    "H",
]


def create_stepp_plot(
    model, figure_size=(8, 6), filename=None, filetype="png", dpi=300, ax=None
):
    """
    Creates the classic Stepp (1972) plots for a completed Stepp analysis,
    and exports the figure to a file.

    :param model:
        Completed Stepp (1972) analysis as instance of :class:
        `openquake.hmtk.seismicity.completeness.comp_stepp_1971.Stepp1971`
    :param string filename:
        Name of output file
    :param string filetype:
        Type of file (from list supported by matplotlib)
    :param int dpi:
        Resolution (dots per inch) of output file
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figure_size)
    else:
        fig = ax.get_figure()

    if filename and os.path.exists(filename):
        raise IOError("File already exists!")

    # get colours from current axes: thus user can set up before calling
    prop_cycler = ax._get_lines.prop_cycler
    prop_cyclers = itertools.tee(itertools.cycle(prop_cycler), 3)
    marker_cyclers = itertools.tee(itertools.cycle(VALID_MARKERS), 3)

    # plot observed Sigma lambda
    for i, (min_mag, max_mag) in enumerate(
        zip(model.magnitude_bin[:-1], model.magnitude_bin[1:])
    ):
        label = "(%g, %g]: %d" % (
            min_mag,
            max_mag,
            model.completeness_table[i, 0],
        )
        colour = next(prop_cyclers[0])["color"]
        ax.loglog(
            model.time_values,
            model.sigma[:, i],
            linestyle="none",
            marker=next(marker_cyclers[0]),
            markersize=3,
            markerfacecolor=colour,
            markeredgecolor=colour,
            label=label,
        )

    # plot expected Poisson rate
    for i in range(0, len(model.magnitude_bin) - 1):
        ax.loglog(
            model.time_values,
            model.model_line[:, i],
            color=next(prop_cyclers[1])["color"],
            linewidth=0.5,
        )

    # mark breaks from expected rate
    for i in range(0, len(model.magnitude_bin) - 1):
        colour = next(prop_cyclers[2])["color"]
        if np.any(np.isnan(model.model_line[:, i])):
            continue
        xmarker = model.end_year - model.completeness_table[i, 0]
        knee = model.model_line[:, i] > 0.0
        ymarker = 10.0 ** np.interp(
            np.log10(xmarker),
            np.log10(model.time_values[knee]),
            np.log10(model.model_line[knee, i]),
        )
        ax.loglog(
            xmarker,
            ymarker,
            marker=next(marker_cyclers[2]),
            markerfacecolor="white",
            markeredgecolor=colour,
        )

    ax.legend(loc="lower left", frameon=False, fontsize="small")
    ax.set_xlabel("Time (years)")
    ax.set_ylabel("$\\sigma_{\\lambda} = \\sqrt{\\lambda} / \\sqrt{T}$")
    ax.autoscale(enable=True, axis="both", tight=True)

    # save figure to file
    if filename is not None:
        fig.savefig(filename, dpi=dpi, format=filetype)
