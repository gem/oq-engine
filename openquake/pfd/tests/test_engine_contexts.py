# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Exercise the PFD integration with the engine machinery: the PFD dummy
GSIM logic tree, ``get_full_lt`` composition with the source-model logic
tree, context building and the displacement rate kernel.
"""
import os
import unittest

import numpy

from openquake.commonlib.readinput import (
    get_oqparam, get_full_lt, get_composite_source_model, get_site_collection,
    get_gsim_lt)
from openquake.hazardlib.calc.displacement import calc_rates
from openquake.hazardlib.pfd_lt import PFDLogicTree
from openquake.pfd.adapter import LegacyModelAdapter, style_from_rake
from openquake.pfd.gsim import PFDGMPE, get_pfd_gsim_lt
from openquake.pfd.registry import get_available
from openquake.qa_tests_data.pfd import case_1

DATADIR = os.path.dirname(case_1.__file__)
TRT = 'Active Shallow Crust'


class EngineContextsTestCase(unittest.TestCase):

    def test_pfd_gsim_lt(self):
        # the PFD "gsim" logic tree is one no-op PFDGMPE per TRT
        glt = get_pfd_gsim_lt([TRT])
        self.assertEqual(glt.get_num_paths(), 1)
        [gsim] = list(glt.values[TRT])
        self.assertIsInstance(gsim, PFDGMPE)
        self.assertEqual(gsim.REQUIRES_DISTANCES,
                         frozenset({'rtor', 'x_l', 'rx'}))
        self.assertEqual(gsim.REQUIRES_RUPTURE_PARAMETERS,
                         frozenset({'mag', 'dip', 'rake', 'length'}))

    def test_full_lt(self):
        oq = get_oqparam(os.path.join(DATADIR, 'job.ini'))
        # get_gsim_lt returns the no-op PFDGMPE logic tree for displacement
        glt = get_gsim_lt(oq, [TRT])
        [gsim] = list(glt.values[TRT])
        self.assertIsInstance(gsim, PFDGMPE)
        flt = get_full_lt(oq)
        self.assertEqual(flt.get_num_paths(), 1)
        self.assertIsInstance(flt.extra_lt, PFDLogicTree)
        self.assertEqual(len(flt.extra_lt.branchsets), 4)
        [gsim] = list(flt.gsim_lt.values[TRT])
        self.assertIsInstance(gsim, PFDGMPE)
        # the PFD default maximum_distance is set
        self.assertEqual(oq.maximum_distance['default'][0][1], 10)

    def test_rates(self):
        oq = get_oqparam(os.path.join(DATADIR, 'job.ini'))
        csm = get_composite_source_model(oq)
        sitecol = get_site_collection(oq)
        cmakers = csm.get_cmakers()
        [src] = list(csm.src_groups[0])
        [branch] = csm.full_lt.extra_lt.enumerate(
            [(src.source_id.split(';')[0], style_from_rake(src.rake))])
        adapters = {}
        for slot, choice in branch.selections.items():
            cls = get_available(slot)[choice.class_name]
            ad = LegacyModelAdapter(cls(**choice.params), choice.params)
            adapters[ad.model_type] = ad
        self.assertEqual(sorted(adapters),
                         ['primary_fd', 'primary_sr',
                          'secondary_fd', 'secondary_sr'])
        ctxs = list(cmakers[0].get_ctxs(src, sitecol))
        self.assertTrue(ctxs)
        for field in ('rtor', 'x_l', 'length', 'occurrence_rate', 'sids'):
            self.assertIn(field, ctxs[0].dtype.names)
        imls = oq.imtls['Disp']
        rates, principal, distributed = calc_rates(
            ctxs, len(sitecol), adapters, imls,
            oq.r_threshold_km, oq.r_sigma_km)
        # the site is off the on-trace principal zone but inside the
        # distributed zone, as in oq-pfdha's hazard_curve_minimal
        self.assertEqual(principal.sum(), 0)
        self.assertTrue((distributed > 0).all())
        numpy.testing.assert_allclose(rates, distributed)
