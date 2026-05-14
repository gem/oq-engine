# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
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

import unittest

from openquake.hazardlib.aspect_ratio import (MagDepAspectRatio,
                                              build_aspect_ratio_node)

class MagDepAratioTestCase(unittest.TestCase):
    """
    Check that each expression type available in MagDepAratio
    provides the expected results.
    """
    def test_linear_piecewise(self):
        # Two-point function: Mw4->1.0, Mw7->2.0
        points = [(4.0, 1.0), (7.0, 2.0)]
        # Below min, midpoint, non-midpoint interp, above max
        mags = [3.0, 5.5, 6.25, 8.0]
        expected = [1.0, 1.5, 1.75, 2.0]
        for m, exp in zip(mags, expected):
            self.assertAlmostEqual(
                MagDepAspectRatio("linear_piecewise", points).get(m),
                exp, msg=f"mag={m}")


class BuildAspectRatioNodeTestCase(unittest.TestCase):
    """
    Check that aspect ratios can be written back to XML nodes.
    """
    def test_scalar_produces_rupt_aspect_ratio_node(self):
        # A regular float should work as usual
        node = build_aspect_ratio_node(1.5)
        self.assertEqual(node.tag, 'ruptAspectRatio')
        self.assertEqual(node.text, 1.5)

    def test_mag_dep_produces_aspect_ratio_function_node(self):
        # MagDepAspectRatio instance produces an aspectRatioFunction XML node
        rar = MagDepAspectRatio("linear_piecewise", [(4.0, 1.0), (7.0, 2.0)])
        node = build_aspect_ratio_node(rar)
        self.assertEqual(node.tag, 'aspectRatioFunction')
        repr_tags = [n.tag for n in node.nodes]
        self.assertIn('type', repr_tags)
        self.assertIn('mag_points', repr_tags)
        # Check func type
        type_node = next(n for n in node.nodes if n.tag == 'type')
        self.assertEqual(type_node.text, 'linear_piecewise')
        # Check the (mag, aratio) pairs
        points_node = next(n for n in node.nodes if n.tag == 'mag_points')
        self.assertEqual(len(points_node.nodes), 2)
        self.assertEqual(points_node.nodes[0].attrib['mag'], 4.0)
        self.assertEqual(points_node.nodes[1].attrib['aratio'], 2.0)
