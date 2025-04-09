# The Hazard Library
# Copyright (C) 2014-2025 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import os
import pandas as pd
import numpy as np

from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.tests.gsim.mgmpe.dummy import new_ctx
from openquake.hazardlib import valid
from openquake.hazardlib.gsim import utils_chapman_guo_2021 as utils


aae = np.testing.assert_almost_equal

PSAS = os.path.join(os.path.dirname(__file__), '..', '..',
                  'gsim', 'chapman_guo_2021_psa_ratios.csv')

# PSA ratios to be retrieved from Chapman and Guo (2021) tables
exp = [np.array([-0.34285433, -0.53569485, -1.75992894]), # SA(0.2)
       np.array([ 0.42077671,  0.35287453, -0.25338147]), # SA(1.0)
       np.array([0.75953187, 0.76129675, 0.69775816])]    # SA(2.0)


class ChapmanGuo2021TestCase(unittest.TestCase):
    """
    Check execution and correctness of values for the retrieval of the
    PSA ratios from the Chapman and Guo (2021) tables for given combinations
    of mag, rrup, z_sed (sediment depth) and IMT.
    """
    def test_chapman_guo_psa_ratios(self):
        
        # NGAEast GMM with Chapman and Guo (2021) Coastal Plains site amp
        # which requires z_sed site param
        ngaeast_mod = valid.gsim('[NGAEastUSGSGMPE]\n'
                                 'gmpe_table="nga_east_usgs_17.hdf5"\n'
                                 'z_sed_scaling="true"\n'
                                 'coastal_plains_site_amp="true"')
        
        # Make the ctx
        imts = ['SA(0.2)', 'SA(1.0)', 'SA(2.0)']
        mags = [6.0, 6.0, 6.0]
        oqp = {'imtls': {k: [] for k in imts},
               'mags': [f'{k:.2f}' for k in mags]}
        cmaker = simple_cmaker([ngaeast_mod], imts, **oqp)                       
        ctx = new_ctx(cmaker, 3)
        ctx.dip = 90.
        ctx.rake = 0.
        ctx.z_sed = np.array([1.5, 2.50, 14.50])
        ctx.rrup = np.array([50., 100., 200.])
        ctx.vs30 = np.array([800., 400., 200.])

        # Load the csv
        df = pd.read_csv(PSAS)

        # Get the PSA values for the ctx
        obs = []
        for imt in imts:

            # Table of PSA ratios per mag, rrup, z_sed
            psa_df = utils.get_psa_df(df, imt)

            # Retrieve PSA ratios in log space for given ctx
            psa_ratios = utils.get_psa_ratio(ctx, imt, psa_df)

            # Store into single array
            obs.append(psa_ratios)

        # Check observed matches expected
        aae(obs, exp)