# Copyright (c) 2013, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.

import numpy
import unittest

from openquake.risklib import scientific as sci


class EvenlySpacedLRTestCase(unittest.TestCase):
    """
    Tests for :func:`openquake.risklib.scientific._evenly_spaced_loss_ratios`.
    """

    def test__evenly_spaced_loss_ratios(self):
        lrs = [0.0, 0.1, 0.2, 0.4, 1.2]
        es_lrs = sci._evenly_spaced_loss_ratios(lrs, steps=5)
        expected = [0.0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18,
                    0.2, 0.24000000000000002, 0.28, 0.32, 0.36, 0.4, 0.56,
                    0.72, 0.8799999999999999, 1.04, 1.2]
        numpy.testing.assert_allclose(es_lrs, expected)

    def test__evenly_spaced_loss_ratios_prepend_0(self):
        # We expect a 0.0 to be prepended to the LRs before spacing them
        lrs = [0.1, 0.2, 0.4, 1.2]
        es_lrs = sci._evenly_spaced_loss_ratios(lrs, steps=5)
        expected = [0.0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18,
                    0.2, 0.24000000000000002, 0.28, 0.32, 0.36, 0.4, 0.56,
                    0.72, 0.8799999999999999, 1.04, 1.2]
        numpy.testing.assert_allclose(es_lrs, expected)

    def test__evenly_spaced_loss_ratios_append_1(self):
        lrs = [0.0, 0.5]
        es_lrs = sci._evenly_spaced_loss_ratios(lrs, steps=2)
        expected = [0.0, 0.25, 0.5, 0.75, 1.0]
        numpy.testing.assert_allclose(es_lrs, expected)
