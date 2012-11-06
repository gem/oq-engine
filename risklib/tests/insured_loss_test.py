# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import numpy

from risklib.models import input

from risklib.insured_loss import (
    _insurance_boundaries_defined, compute_insured_losses)


class InsuredLossesTestCase(unittest.TestCase):
    def setUp(self):
        self.losses = numpy.array([72.23120833,
                                   410.55950159, 180.02423357, 171.02684563,
                                   250.77079384, 39.45861103, 114.54372035,
                                   288.28653452, 473.38307021, 488.47447798,
                                   ])

    def test_insurance_boundaries_defined(self):
        asset = input.Asset("a14", "a taxonomy", None, None, 1, 700, 300)
        self.assertTrue(_insurance_boundaries_defined(asset))

        asset.ins_limit = None
        self.assertRaises(RuntimeError, _insurance_boundaries_defined, asset)

        asset.ins_limit = 700
        asset.deductible = None
        self.assertRaises(RuntimeError, _insurance_boundaries_defined, asset)

    def test_compute_insured_losses(self):
        asset = input.Asset("a14", "a taxonomy", None, None, 1, 300, 150)

        expected = numpy.array([
            0, 300, 180.02423357, 171.02684563,
            250.77079384, 0, 0, 288.28653452, 300, 300,
            ])

        self.assertTrue(numpy.allclose(expected,
            compute_insured_losses(asset, self.losses)))