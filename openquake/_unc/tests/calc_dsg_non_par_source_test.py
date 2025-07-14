# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding: utf-8

import os
import pathlib
import unittest
import numpy as np

from openquake.commonlib import datastore
from openquake._unc.hcurves_dist import get_stats

from openquake._unc.hazard_pmf import get_hazard_pmf
from openquake._unc.hazard_pmf import afes_matrix_from_dstore

from openquake._unc.tests.calc_dsg_single_source_test import (
    plot_comparison)

# This file folder
TFF = pathlib.Path(__file__).parent.resolve()

# Testing
aae = np.testing.assert_almost_equal
aac = np.testing.assert_allclose

# Options
PLOTTING = 0


class SingleSourceTestCase(unittest.TestCase):

    def test_m_convolution_source_b(self):
        """ Convolution m test case """

        tpath = os.path.join(TFF, 'data_calc', 'disaggregation',
                             'test_case_non_param')

        # Single source disaggregation
        fname = os.path.join(tpath, 'out', 'calc_1884.hdf5')
        dstore = datastore.read(fname)
        oqp = dstore['oqparam']
        rmap = dstore.get('best_rlzs', None)[:][0]
        expct = dstore.get('disagg-rlzs/Mag', None)[0, :, 0, 0, :]
        weights = dstore.get('weights', None)[:]
        weights = weights[rmap]
        mags = dstore.get('disagg-bins/Mag', None)[:]
        mean = dstore.get('disagg-stats/Mag', None)[0, :, 0, 0, :]
        mean = np.squeeze(mean)

        # Computing the mean disaggregation in `oute`
        oute = np.zeros((expct.shape[0]))
        idxe = []
        cnt = 0
        for imag in range(expct.shape[0]):
            poes = expct[imag, :]
            poes[poes > 0.99999] = 0.99999
            afes = -np.log(1.-poes)/oqp.investigation_time
            tmp = np.sum(afes*weights)
            oute[imag] = tmp
            if tmp > 0.0:
                idxe.append(cnt)
            cnt += 1

        # Set parameters
        imt = 'PGA'
        atype = 'm'
        iii = np.arange(0, expct.shape[-1])

        # Read realizations
        _, afes, weights = afes_matrix_from_dstore(
                dstore, imtstr=imt, info=False, idxs=iii, atype=atype)

        # Get histogram
        res = 300
        his, min_pow, num_pow = get_hazard_pmf(afes, samples=res,
                                               weights=weights)
        hists, hists_idxs = get_stats([-1, 0.50], his, min_pow, num_pow)

        # Check the sum
        aac(np.sum(oute[idxe]), np.sum(hists[:, 0]), atol=1e-7, rtol=1e-3)
        afes = -np.log(1.-mean)/oqp.investigation_time
        aac(np.sum(oute[idxe]), np.sum(afes), atol=1e-7, rtol=1e-3)

        print('')
        print('AfE from OQ rlzs  :', np.sum(oute[idxe]))
        print('AfE from unc hist :', np.sum(hists[:, 0]))
        print('AfE from OQ mean  :', np.sum(afes))

        # Check the values between what computed by processing realizations and
        # histograms
        aac(hists[:, 0], oute[idxe], atol=1e-5, rtol=1e-3)

        # ---------------------------------------------------------------------
        # Plot results
        if PLOTTING:
            plot_comparison(hists, oute, idxe, mags, mean, oqp)
