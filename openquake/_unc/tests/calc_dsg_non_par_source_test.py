# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding: utf-8

import os
import pathlib
import unittest
import numpy as np

from openquake.calculators.base import dcache
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
        # Single source disaggregation
        job_ini = os.path.join(TFF, 'data_calc', 'disaggregation',
                               'test_case_non_param', 'jobD.ini')
        dstore = dcache.get(job_ini)
        oqp = dstore['oqparam']
        rmap = dstore['best_rlzs'][0]
        expct = dstore['disagg-rlzs/Mag'][0, :, 0, 0, :]
        weights = dstore['weights'][:][rmap]
        mags = dstore['disagg-bins/Mag'][:]
        mean = dstore['disagg-stats/Mag'][0, :, 0, 0, :]
        mean = np.squeeze(mean)

        # Computing the mean disaggregation in `oute`
        oute = np.zeros((expct.shape[0]))
        idxe = []
        cnt = 0
        for imag in range(expct.shape[0]):
            poes = expct[imag, :]
            poes[poes > 0.99999] = 0.99999
            afes = -np.log(1.-poes) / oqp.investigation_time
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
