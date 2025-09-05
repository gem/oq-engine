# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2025 GEM Foundation
#
#                `.......      `....     `..`...     `..`... `......
#                `..    `..  `..    `..  `..`. `..   `..     `..
#                `..    `..`..        `..`..`.. `..  `..     `..
#                `.......  `..        `..`..`..  `.. `..     `..
#                `..       `..        `..`..`..   `. `..     `..
#                `..         `..     `.. `..`..    `. ..     `..
#                `..           `....     `..`..      `..     `..
#
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding: utf-8

import os
import pathlib
import unittest
import numpy as np

from openquake._unc.bins import get_bins_from_params
from openquake.calculators.base import dcache
from openquake._unc.convolution import HistoGroup
from openquake._unc.dsg_mde import get_afes_from_dstore

# This file folder
TFF = pathlib.Path(__file__).parent.resolve()

# Testing
aae = np.testing.assert_almost_equal
aac = np.testing.assert_allclose
aeq = np.testing.assert_equal
PLOT = False


class HistogramMDETestCase(unittest.TestCase):

    def test_get_histograms(self):
        job_ini = os.path.join(TFF, 'data_calc', 'disaggregation',
                               'test_case01', 'job_a.ini')
        dstore = dcache.get(job_ini)
        binc, afes, weights, shapes = get_afes_from_dstore(
            dstore, 'Mag_Dist_Eps', 0)

        # Check the centers of the bins
        expected = np.array([5.0, 15, 25, 35, 45, 55, 65, 75, 85, 95, 110, 130,
                             150, 170, 190, 225, 275])
        aeq(binc['dst'], expected)
        expected = np.arange(6.45, 8.1, 0.1)
        aae(binc['mag'], expected)
        expected = np.arange(-3.5, 4., 1.0)
        aeq(binc['eps'], expected)

        # Get the histograms
        res = 10
        h = HistoGroup.new(afes.reshape(len(weights), -1), weights, res)

        # Check that the list of histograms has the same shape of the number of
        # bins composing the disaggregation matrix
        expected = len(binc['mag']) * len(binc['dst']) * len(binc['eps'])
        assert expected == len(h.pmfs)

        # Computing the mean and counting the M-D-e combinations with values
        # different than 0
        smm = 0.0
        cnt = 0.
        for ohi in h.pmfs:
            if ohi is not None:
                smm += np.sum(ohi)
                cnt += 1.

        # The sum of the histograms (which are normalised) must be equal to
        # the number of M-D-e combinations with values different than 0
        aae(smm, cnt, decimal=5)

        if PLOT:
            from bokeh.models import HoverTool
            from bokeh.plotting import figure, show
            p = figure(title="HistoGroup", x_axis_label='AfE',
                       tools=[HoverTool()],
                       y_axis_label='Normalised frequency',
                       x_axis_type="log", width=1200, height=600)
            d1 = afes.shape[0]
            d2 = afes.shape[1]
            d3 = afes.shape[2]
            for idx, (ohi, mpo, npo) in enumerate(
                    zip(h.pmfs, h.minpow, h.numpow)):
                if ohi is not None:
                    bins = get_bins_from_params(mpo, res, npo)
                    binc = bins[:-1] + np.diff(bins) / 2
                    col = tuple(np.random.randint(0, high=255, size=[3]))
                    # Get the indexes of the cell in the original 3D matrix
                    tmp = np.unravel_index(idx, ([d1, d2, d3]))
                    tmag = binc['mag'][tmp[0]]
                    tdst = binc['dst'][tmp[1]]
                    teps = binc['eps'][tmp[2]]
                    # Set the label with the values of magnitude, distance and
                    # epsilon
                    lab = f'[{tmag},{tdst},{teps}]'
                    p.line(binc, ohi, legend_label=lab, line_width=2, color=col)
            show(p)
