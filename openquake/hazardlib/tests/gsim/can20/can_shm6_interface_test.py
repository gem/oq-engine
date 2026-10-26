# Copyright (C) 2014-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
CanadaSHM6 interface regression tests.

The inputs and expected values were NOT supplied by the GSIM authors.
"""
import unittest

import numpy as np

from openquake.hazardlib import contexts
from openquake.hazardlib.gsim.can20 import can_shm6_interface as interface
from openquake.hazardlib.imt import PGA, PGV, SA


def make_context(mag, vs30, rjb, rrup):
    ctx = contexts.RuptureContext()
    ctx.mag = mag
    ctx.rake = 0.
    ctx.vs30 = np.array(vs30, dtype=float)
    ctx.z1pt0 = np.full(len(vs30), -999.)
    ctx.backarc = np.zeros(len(vs30), dtype=bool)
    ctx.rjb = np.array(rjb, dtype=float)
    ctx.rrup = np.array(rrup, dtype=float)
    ctx.sids = np.arange(len(vs30))
    return ctx


# Blocks: log mean, total sigma, tau and phi (where supported).
# Rows: PGA, SA(0.1), SA(1.0), PGV. Columns: Vs30 = 180, 760, 2000 m/s.
EXPECTED = {
    'AbrahamsonEtAl2015SInter': np.array([
        [[-1.3653230925, -2.4333528518, -3.8668645766],
         [-1.1536331949, -1.8337428192, -3.2722774775],
         [-0.9083782381, -2.5669785410, -4.4448667851],
         [3.3221380748, 1.8969927208, 0.2145069530]],
        [[0.7400000000, 0.7400000000, 0.7400000000],
         [0.7400000000, 0.7400000000, 0.7400000000],
         [0.7400000000, 0.7400000000, 0.7400000000],
         [0.7400000000, 0.7400000000, 0.7400000000]],
        [[0.4300000000, 0.4300000000, 0.4300000000],
         [0.4300000000, 0.4300000000, 0.4300000000],
         [0.4300000000, 0.4300000000, 0.4300000000],
         [0.4300000000, 0.4300000000, 0.4300000000]],
        [[0.6000000000, 0.6000000000, 0.6000000000],
         [0.6000000000, 0.6000000000, 0.6000000000],
         [0.6000000000, 0.6000000000, 0.6000000000],
         [0.6000000000, 0.6000000000, 0.6000000000]]]),
    'ZhaoEtAl2006SInterCascadia': np.array([
        [[-1.7521217865, -3.0384649755, -4.9231215124],
         [-1.3780662891, -2.3827911526, -4.3442524044],
         [-0.8229593178, -2.7164650405, -4.0900581039],
         [3.5990316580, 2.0910301458, 0.9048142426]],
        [[0.6779970501, 0.6779970501, 0.6779970501],
         [0.8025241429, 0.8025241429, 0.8025241429],
         [0.7343248600, 0.7343248600, 0.7343248600],
         [0.7585487071, 0.7585487071, 0.7585487071]],
        [[0.3080000000, 0.3080000000, 0.3080000000],
         [0.4030000000, 0.4030000000, 0.4030000000],
         [0.3280000000, 0.3280000000, 0.3280000000],
         [0.3588648025, 0.3588648025, 0.3588648025]],
        [[0.6040000000, 0.6040000000, 0.6040000000],
         [0.6940000000, 0.6940000000, 0.6940000000],
         [0.6570000000, 0.6570000000, 0.6570000000],
         [0.6682905016, 0.6682905016, 0.6682905016]]]),
    'AtkinsonMacias2009': np.array([
        [[-0.9940280482, -2.4468786196, -4.1548800721],
         [-0.5788910504, -1.8152611503, -3.7642402296],
         [-0.6956591887, -2.2685711945, -3.6666657430],
         [4.1100859077, 2.2991894891, 1.2763437803]],
        [[0.5526204223, 0.5526204223, 0.5526204223],
         [0.6216979751, 0.6216979751, 0.6216979751],
         [0.6677496770, 0.6677496770, 0.6677496770],
         [0.6867083944, 0.6867083944, 0.6867083944]]]),
    'GhofraniAtkinson2014Cascadia': np.array([
        [[-1.8363885972, -2.9487380774, -4.2255446892],
         [-1.3149258888, -2.1662614937, -3.3748668583],
         [-1.1556198682, -2.8198089163, -4.1641959556],
         [3.0156907295, 2.0056667453, 0.9224193735]],
        [[0.7945486844, 0.7945486844, 0.7945486844],
         [0.9072434478, 0.9072434478, 0.9072434478],
         [0.6322366014, 0.6322366014, 0.6322366014],
         [0.5500672898, 0.5500672898, 0.5500672898]],
        [[0.4513066782, 0.4513066782, 0.4513066782],
         [0.5041508133, 0.5041508133, 0.5041508133],
         [0.2664585059, 0.2664585059, 0.2664585059],
         [0.3177567428, 0.3177567428, 0.3177567428]],
        [[0.6539341664, 0.6539341664, 0.6539341664],
         [0.7542696010, 0.7542696010, 0.7542696010],
         [0.5733436882, 0.5733436882, 0.5733436882],
         [0.4490040931, 0.4490040931, 0.4490040931]]])}


class CanadaSHM6InterfaceTestCase(unittest.TestCase):

    def setUp(self):
        self.imts = [PGA(), SA(0.1), SA(1.0), PGV()]
        self.ctx = make_context(
            7.5, [180., 760., 2000.], [5., 60., 180.], [30., 80., 200.])
        self.ctx.backarc = np.array([False, True, False])

    def test_mean_and_standard_deviations(self):
        for name, expected in EXPECTED.items():
            with self.subTest(gsim=name):
                gmm = getattr(interface, 'CanadaSHM6_Interface_' + name)()
                result = contexts.get_mean_stds(gmm, self.ctx, self.imts)
                # Atkinson-Macias defines total sigma only
                result = result[:len(expected)]
                np.testing.assert_allclose(result, expected, rtol=0, atol=1e-8)
