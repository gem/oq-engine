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

"""
Module :module:`openquake.unc.tests.calc_multisite_test` tests the
convolution approach with a set of sites
"""

import tempfile
import pathlib
import unittest
import numpy as np
import h5py

#from openquake._unc.hcurves_dist import from_matrix
from openquake._unc.propagate_uncertainties import propagate
from openquake._unc.analysis import Analysis

# This file folder
TFF = pathlib.Path(__file__).parent.resolve()

# Testing
aae = np.testing.assert_almost_equal
aac = np.testing.assert_allclose

# Options
PLOTTING = False


class SiteProcessingTest(unittest.TestCase):

    def test_process_sites(self):

        # Read the configuration file and create the analysis object
        fname = 'analysis.xml'
        fname = TFF / 'data_calc' / 'test_case03' / fname
        analysis = Analysis.read(str(fname))

        # Check the sites
        common_imts, site_mtx = analysis.get_imts_sites()

        # Check imts
        expected = {'SA(1.0)', 'SA(0.3)', 'PGA'}
        msg = 'The dictionay of common IMTs is wrong'
        self.assertEqual(expected, common_imts, msg)

        # Check site mtx
        expected = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0])
        msg = 'Site IDs for source b are wrong'
        np.testing.assert_array_equal(expected, site_mtx[:, 2], msg)

        # Check site mtx
        expected = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        msg = 'Site IDs for source b are wrong'
        np.testing.assert_array_equal(expected, site_mtx[:, 3], msg)

class CalculationMultiSiteTestCase01(unittest.TestCase):
    """
    Test the convolution approach for a set of sites
    """

    def test_multisites(self):
        """ Multisites """

        # Configuration file name
        fname = 'test_case03_multi_convolution.ini'
        fname = TFF / 'data_calc' / fname

        # Add temporary output file
        _, fname_out = tempfile.mkstemp(suffix='.hdf5')
        # conf['analysis']['output_hdf5_file'] = fname_out
        # conf['analysis']['conf_file_path'] = str(TFF / 'data_calc')

        # Run analysis
        tmpdir = tempfile.mkdtemp()
        h, _ = propagate(str(fname), override_folder_out=tmpdir)

        breakpoint()

        # site, stat_type, imt
        sidxs = [1, 2, 3]
        hc_mea = {}
        dstore = h5py.File(str(h5_fname), 'r')
        for i in sidxs:
            hc_mea[i] = dstore['hcurves-stats'][:][i, 0, 0, :]
        dstore.close()

        # Check results
        fres = h5py.File(fname_out, 'r')
        his = {}
        minp = {}
        nump = {}
        for i in sidxs:
            #his[i] = from_matrix(fres[f'PGA/{i}/his'][:])
            minp[i] = fres[f'PGA/{i}/min_pow'][:]
            nump[i] = fres[f'PGA/{i}/num_pow'][:]

        i = 1
        res_conv, _ = h.get_stats([-1, 0.50], his[i], minp[i], nump[i])
        expected = -np.log(1 - hc_mea[i])
        aac(expected, res_conv[:, 0], atol=1e-4)

        fres.close()
