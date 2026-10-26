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
"""Shared site and rupture inputs for CanadaSHM6 regression tests."""
import numpy as np

from openquake.hazardlib import contexts


def make_context(mag, vs30, rjb, rrup, hypo_depth):
    """Build a context containing the inputs used by the CanadaSHM6 GMMs."""
    ctx = contexts.RuptureContext()
    ctx.mag = mag
    ctx.rake = 0.
    ctx.dip = 90.
    ctx.width = 12.
    ctx.ztor = 1.
    ctx.hypo_depth = hypo_depth
    ctx.is_aftershock = False
    ctx.crjb = 0.
    ctx.vs30 = np.array(vs30, dtype=float)
    ctx.vs30measured = ctx.vs30 >= 1100.
    ctx.z1pt0 = np.full(len(vs30), -999.)
    ctx.backarc = np.zeros(len(vs30), dtype=bool)
    ctx.rjb = np.array(rjb, dtype=float)
    ctx.rrup = np.array(rrup, dtype=float)
    ctx.rhypo = np.hypot(ctx.rjb, hypo_depth)
    ctx.rx = np.full(len(vs30), -5.)
    ctx.ry0 = np.zeros(len(vs30))
    ctx.sids = np.arange(len(vs30))
    return ctx
