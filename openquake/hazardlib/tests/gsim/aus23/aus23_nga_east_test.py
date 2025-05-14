# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
Module exports :class:`NGAEastAUS23Test`
"""
import unittest
import numpy as np

from openquake.hazardlib import contexts, valid
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib.gsim.mgmpe.stewart2020 import (
    stewart2020_linear_scaling)
from openquake.hazardlib.gsim.mgmpe.hashash2020 import (
    hashash2020_non_linear_scaling)


class NGAEastAUS23Test(unittest.TestCase):

    def test01(self):
        """
        Tests the calculation of ground motion with the modifiable GMM built
        for computing GM with AUS23 considering spatially variable Vs30
        """

        # Data for the original GMM
        fname = "NGA-East_Backbone_Model.geometric.3000.mps.hdf5"

        # Create context
        ctx = RuptureContext()
        mags = ['6.00']
        ctx.mag = 6.0
        ref_vs30 = 3000
        wimp = 0.8

        # Table GMM
        tgmm = valid.gsim(f'[NGAEastAUS2023GMPE]\ntable_relpath="{fname}"')

        # Modifiable GMM
        param = {'ref_vs30': ref_vs30, 'wimp': wimp, 'usgs': False}
        mgmm = valid.modified_gsim(tgmm, ceus2020_site_term=param)

        # Compute values on rock for PGA
        ctx.rjb = ctx.rrup = [20, 30, 40, 50, 60, 20, 30, 40, 50, 60]
        ctx.vs30 = np.ones_like(ctx.rjb) * ref_vs30
        ctx.sids = np.arange(len(ctx.vs30))
        imts = [PGA()]
        [mean_r], [_sigma_r], _, _ = contexts.get_mean_stds(
            tgmm, ctx, [imts[0]], mags=mags)

        # Compute values on rock for SA
        imts = [SA(0.2)]
        [mean_sa], [_sigma_sa], _, _ = contexts.get_mean_stds(
            tgmm, ctx, [imts[0]], mags=mags)

        # Compute linear term
        ctx.vs30[0:5] = np.ones((5)) * 400
        ctx.vs30[5:] = np.array([200, 300, 500, 600, 760])
        slin = stewart2020_linear_scaling(imts[0], ctx.vs30, wimp=wimp)

        # Compute the non-linear term
        snlin = hashash2020_non_linear_scaling(
            imts[0], ctx.vs30, np.exp(mean_r), ref_vs30)

        # Expected values
        expected = mean_sa + slin + snlin

        # Computed values
        [mean_comp], [_sigma_comp], _, _ = contexts.get_mean_stds(
            mgmm, ctx, [imts[0]], mags=mags)

        # Compute values on soil
        np.testing.assert_allclose(mean_comp, expected)


    def test02_usgs(self):
        """
        Tests the calculation of ground motion with the modifiable GMM built
        for computing GM with AUS23 considering spatially variable Vs30.
        In this case we use for the linear component the coefficients proposed
        by the USGS.
        """

        # Data for the original GMM
        fname = "NGA-East_Backbone_Model.geometric.3000.mps.hdf5"

        # Create context
        ctx = RuptureContext()
        mags = ['6.00']
        ctx.mag = 6.0
        ref_vs30 = 3000
        wimp = 0.8

        # Table GMM
        tgmm = valid.gsim(f'[NGAEastAUS2023GMPE]\ntable_relpath="{fname}"')

        # Modifiable GMM
        param = {'ref_vs30': ref_vs30, 'wimp': wimp, 'usgs': True}
        mgmm = valid.modified_gsim(tgmm, ceus2020_site_term=param)

        # Compute values on rock for PGA
        ctx.rjb = ctx.rrup = [20, 30, 40, 50, 60, 20, 30, 40, 50, 60]
        ctx.vs30 = np.ones_like(ctx.rjb) * ref_vs30
        ctx.sids = np.arange(len(ctx.vs30))
        imts = [PGA()]
        [mean_r], [_sigma_r], _, _ = contexts.get_mean_stds(
            tgmm, ctx, [imts[0]], mags=mags)

        # Compute values on rock for SA
        imts = [SA(0.1)]
        [mean_sa], [_sigma_sa], _, _ = contexts.get_mean_stds(
            tgmm, ctx, [imts[0]], mags=mags)

        # Compute linear term
        ctx.vs30[0:5] = np.ones((5)) * 400
        ctx.vs30[5:] = np.array([200, 300, 500, 600, 760])
        slin = stewart2020_linear_scaling(
            imts[0], ctx.vs30, wimp=wimp, usgs=True)

        # Compute the non-linear term
        snlin = hashash2020_non_linear_scaling(
            imts[0], ctx.vs30, np.exp(mean_r), ref_vs30)

        # Expected values
        expected = mean_sa + slin + snlin

        # Computed values
        [mean_comp], [_sigma_comp], _, _ = contexts.get_mean_stds(
            mgmm, ctx, [imts[0]], mags=mags)

        # Compute values on soil
        np.testing.assert_allclose(mean_comp, expected)

    def test03(self):
        """
        Tests the calculation with 1 site
        """

        # Data for the original GMM
        fname = "NGA-East_Backbone_Model.geometric.3000.mps.hdf5"

        # Create context
        ctx = RuptureContext()
        mags = ['6.00']
        ctx.mag = 6.0
        ref_vs30 = 3000
        wimp = 0.8

        # Table GMM
        tgmm = valid.gsim(f'[NGAEastAUS2023GMPE]\ntable_relpath="{fname}"')

        # Modifiable GMM
        param = {'ref_vs30': ref_vs30, 'wimp': wimp, 'usgs': False}
        mgmm = valid.modified_gsim(tgmm, ceus2020_site_term=param)

        # Compute values on rock for PGA
        ctx.rjb = ctx.rrup = [20]
        ctx.vs30 = np.ones_like(ctx.rjb) * ref_vs30
        ctx.sids = np.arange(len(ctx.vs30))
        imts = [PGA()]
        [_mean_r], [_sigma_r], _, _ = contexts.get_mean_stds(
            tgmm, ctx, [imts[0]], mags=mags)

        # Computed values
        [_mean_comp], [_sigma_comp], _, _ = contexts.get_mean_stds(
            mgmm, ctx, [imts[0]], mags=mags)

        # Compute values on soil
        # np.testing.assert_allclose(mean_comp, expected)
