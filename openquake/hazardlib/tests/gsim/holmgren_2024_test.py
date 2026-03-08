# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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

import numpy as np

from openquake.hazardlib import contexts
from openquake.hazardlib.gsim.holmgren_2024 import HolmgrenEtAl2024
from openquake.hazardlib.imt import PGA, PGV, SA


class TestHolmgrenEtAl2024:
    def test_compute(self):
        gsim = HolmgrenEtAl2024()

        ctx = contexts.RuptureContext()
        ctx.sids = np.array([0, 1, 2], dtype=np.uint32)
        ctx.mag = np.array([5.0, 6.0, 6.8])
        ctx.rhypo = np.array([10.0, 45.0, 120.0])
        ctx.vs30 = np.array([300.0, 760.0, 1200.0])

        imts = [PGA(), SA(0.2), SA(1.0), PGV()]
        mean, sig, tau, phi = contexts.get_mean_stds(gsim, ctx, imts)

        exp_mean = np.array([
            [-2.4501225075, -3.0389228279, -3.6793047761],
            [-1.8968595968, -2.1487463653, -2.9908991524],
            [-3.9455062179, -4.3901562654, -5.0733165055],
            [1.1872070189, 0.6955553302, 0.2237199308],
        ])
        exp_sig = np.array([
            [0.7516, 0.6280, 0.5745],
            [0.7419, 0.6373, 0.5927],
            [0.6751, 0.62765, 0.6117],
            [0.6921, 0.60985, 0.5726],
        ])

        np.testing.assert_allclose(mean, exp_mean, rtol=0.0, atol=1e-10)
        np.testing.assert_allclose(sig, exp_sig, rtol=0.0, atol=1e-10)
        np.testing.assert_allclose(tau, 0.0, rtol=0.0, atol=0.0)
        np.testing.assert_allclose(phi, 0.0, rtol=0.0, atol=0.0)

    def test_experimental(self):
        assert HolmgrenEtAl2024.experimental is True
