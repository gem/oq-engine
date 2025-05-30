# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding: utf-8

import os
import pathlib
import unittest
import numpy as np

from openquake._unc.bins import get_bins_from_params
from openquake.commonlib.datastore import read as read_dstore
from openquake._unc.dtypes.dsg_mde import get_afes_from_dstore, get_histograms

# This file folder
TFF = pathlib.Path(__file__).parent.resolve()

# Testing
aae = np.testing.assert_almost_equal
aac = np.testing.assert_allclose
aeq = np.testing.assert_equal

PLOT = False


class HistogramMDETestCase(unittest.TestCase):

    def test_read_dstore(self):

        # Define fname of the .hdf5 file
        fname = os.path.join(TFF, 'data_calc', 'disaggregation', 'test_case01',
                             'out_a', 'calc_1978.hdf5')

        # Read datastore
        dstore = read_dstore(fname)
        binc, afes, weights, shapes = get_afes_from_dstore(dstore, 'PGA')

        # Check the centers of the bins
        expected = np.array([5.0, 15, 25, 35, 45, 55, 65, 75, 85, 95, 110, 130,
                             150, 170, 190, 225, 275])
        aeq(binc['dst'], expected)
        expected = np.arange(6.45, 8.1, 0.1)
        aae(binc['mag'], expected)
        expected = np.arange(-3.5, 4., 1.0)
        aeq(binc['eps'], expected)

    def test_get_histograms(self):

        # This test reads the disaggregation results in a datastore and
        # computes an histogram of the PoEs in each bin

        # Define fname of the .hdf5 file
        fname = os.path.join(TFF, 'data_calc', 'disaggregation', 'test_case01',
                             'out_a', 'calc_1978.hdf5')

        # Read datastore
        dstore = read_dstore(fname)
        mdebinc, afes, weights, shapes = get_afes_from_dstore(dstore, 'PGA')

        # Get the histograms
        res = 10
        ohis, min_powers, num_powers = get_histograms(afes, weights, res)

        # Check that the list of histograms has the same shape of the number of
        # bins composing the disaggregation matrix
        expected = (len(mdebinc['mag']) * len(mdebinc['dst']) *
                    len(mdebinc['eps']))
        self.assertTrue(expected == len(ohis))

        # Computing the mean and counting the M-D-e combinations with values
        # different than 0
        smm = 0.0
        cnt = 0.
        for ohi in ohis:
            if ohi is not None:
                smm += np.sum(ohi)
                cnt += 1.

        # The sum of the histograms (which are normalised) must be equal to
        # the number of M-D-e combinations with values different than 0
        self.assertEqual(smm, cnt)

        if PLOT:
            from bokeh.models import HoverTool
            from bokeh.plotting import figure, show
            p = figure(title="Histograms", x_axis_label='AfE',
                       tools=[HoverTool()],
                       y_axis_label='Normalised frequency',
                       x_axis_type="log", width=1200, height=600)
            d1 = afes.shape[0]
            d2 = afes.shape[1]
            d3 = afes.shape[2]
            for idx, (ohi, mpo, npo) in enumerate(zip(ohis, min_powers, num_powers)):
                if ohi is not None:
                    bins = get_bins_from_params(mpo, res, npo)
                    binc = bins[:-1] + np.diff(bins) / 2
                    col = tuple(np.random.randint(0, high=255, size=[3]))
                    # Get the indexes of the cell in the original 3D matrix
                    tmp = np.unravel_index(idx, ([d1, d2, d3]))
                    tmag = mdebinc['mag'][tmp[0]]
                    tdst = mdebinc['dst'][tmp[1]]
                    teps = mdebinc['eps'][tmp[2]]
                    # Set the label with the values of magnitude, distance and
                    # epsilon
                    lab = f'[{tmag},{tdst},{teps}]'
                    p.line(binc, ohi, legend_label=lab, line_width=2, color=col)
            show(p)
