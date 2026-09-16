# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Regression tests for the ``scaling_model`` parameter of Youngs2003PrimaryFD.

Historical bug: logic trees could set ``scaling_model`` on a
``[Youngs2003PrimaryFD]`` uncertaintyModel block, but the model never
accepted the parameter - the adapter's signature filtering dropped it
silently, so ANY value (including ones the model cannot honour, e.g.
``LEONARD2010``) ran as the hardcoded Wells & Coppersmith (1994) relation.

The fix wires ``scaling_model`` as a validated constructor parameter
(default ``"WC1994"``, the only implemented relation and the one used by
Youngs et al. 2003) with an optional call-time override, and makes
``_instantiate_model`` propagate constructor errors instead of degrading
them to a warning + silently-zero hazard.
"""

import numpy as np
import pytest

from openquake.pfd.primary_surf_displ.youngs2003 import Youngs2003PrimaryFD


D = np.array([0.01, 0.1, 1.0])
XL = np.array([0.25])
MAG = 6.5


def test_default_is_wc1994_and_unchanged():
    """Default construction == explicit WC1994 == pre-fix behaviour."""
    p_default = Youngs2003PrimaryFD().get_prob(
        D, XL, MAG, style="all", norm_disp_type="AD")
    p_explicit = Youngs2003PrimaryFD(scaling_model="WC1994").get_prob(
        D, XL, MAG, style="all", norm_disp_type="AD")
    np.testing.assert_array_equal(p_default, p_explicit)
    # sanity: probabilities decrease with displacement level
    assert np.all(np.diff(p_default[:, 0]) < 0)


def test_case_insensitive():
    m = Youngs2003PrimaryFD(scaling_model="wc1994")
    assert m.scaling_model == "WC1994"


def test_invalid_scaling_model_raises_at_construction():
    with pytest.raises(ValueError, match="scaling_model"):
        Youngs2003PrimaryFD(scaling_model="LEONARD2010")
    with pytest.raises(ValueError, match="scaling_model"):
        Youngs2003PrimaryFD(scaling_model="THINGBAIJAM2017")


def test_invalid_scaling_model_raises_at_call_time():
    m = Youngs2003PrimaryFD()
    with pytest.raises(ValueError, match="scaling_model"):
        m.get_prob(D, XL, MAG, style="all", norm_disp_type="AD",
                   scaling_model="LEONARD2010")


def test_valid_call_time_override_is_noop():
    m = Youngs2003PrimaryFD()
    p1 = m.get_prob(D, XL, MAG, style="all", norm_disp_type="AD")
    p2 = m.get_prob(D, XL, MAG, style="all", norm_disp_type="AD",
                    scaling_model="WC1994")
    np.testing.assert_array_equal(p1, p2)

