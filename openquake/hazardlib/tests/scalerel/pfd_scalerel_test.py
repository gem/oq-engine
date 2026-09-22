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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Tests for the fault-displacement scaling relations folded into
:mod:`openquake.hazardlib.scalerel` (PR-2 of the oq-engine integration plan).

The values are pinned to the oq-pfdha library outputs and to the published
coefficients, and the width relations are cross-checked against the
``TAB1`` coefficient table of Mammarella et al. (2024) as implemented in
:mod:`openquake.pfd.primary_surf_rup.mammarella2024`.
"""
import pytest

from openquake.hazardlib import valid
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.scalerel.thingbaijam2017 import Thingbaijam2017
from openquake.hazardlib.scalerel.leonard2010 import Leonard2010
from openquake.hazardlib.scalerel.leonard2014 import (
    Leonard2014_SCR, Leonard2014_Interplate)
from openquake.pfd.primary_surf_rup.mammarella2024 import TAB1


# ---------------------------------------------------------------------------
# WC1994 AD/MD (Wells & Coppersmith 1994, Table 2B)
# ---------------------------------------------------------------------------
def test_wc1994_average_displacement():
    sr = WC1994()
    # values pinned to the oq-pfdha WellsCoppersmith1994
    assert sr.get_average_displacement(6.5, "all") == pytest.approx(
        0.48417236758409893, rel=1e-12)
    assert sr.get_average_displacement(6.5, "strike-slip") == pytest.approx(
        0.3388441561392027, rel=1e-12)
    assert sr.get_average_displacement(6.5, "normal") == pytest.approx(
        0.4415704473533121, rel=1e-12)
    ad, sigma = sr.get_average_displacement(6.5, "all", return_sigma=True)
    assert sigma == pytest.approx(0.36, rel=1e-12)


def test_wc1994_maximum_displacement():
    sr = WC1994()
    assert sr.get_maximum_displacement(6.5, "all") == pytest.approx(
        0.7413102413009177, rel=1e-12)
    assert sr.get_maximum_displacement(6.5, "strike-slip") == pytest.approx(
        0.46238102139926035, rel=1e-12)
    md, sigma = sr.get_maximum_displacement(6.5, "all", return_sigma=True)
    assert sigma == pytest.approx(0.42, rel=1e-12)


def test_wc1994_reverse_falls_back_to_all():
    """oq-pfdha uses the all-rake relation for the reverse style."""
    sr = WC1994()
    assert sr.get_average_displacement(6.5, "reverse") == pytest.approx(
        sr.get_average_displacement(6.5, "all"), rel=1e-12)
    assert sr.get_maximum_displacement(6.5, "reverse") == pytest.approx(
        sr.get_maximum_displacement(6.5, "all"), rel=1e-12)


def test_wc1994_displacement_from_rake():
    """The style-string API and the hazardlib rake API agree."""
    sr = WC1994()
    assert sr.get_average_displacement(6.5, rake=0.0) == pytest.approx(
        sr.get_average_displacement(6.5, "strike-slip"), rel=1e-12)
    assert sr.get_average_displacement(6.5, rake=90.0) == pytest.approx(
        sr.get_average_displacement(6.5, "reverse"), rel=1e-12)


def test_wc1994_surface_rupture_length_style_api():
    sr = WC1994()
    assert sr.get_surface_rupture_length(6.5, "strike-slip") == pytest.approx(
        18.197008586099827, rel=1e-12)
    assert sr.get_surface_rupture_length(6.5, "reverse") == pytest.approx(
        17.179083871575877, rel=1e-12)
    # the style API agrees with the rake API
    assert sr.get_surface_rupture_length(6.5, "strike-slip") == pytest.approx(
        sr.get_surface_rupture_length(6.5, rake=0.0), rel=1e-12)


# ---------------------------------------------------------------------------
# Thingbaijam et al. (2017)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("style,expected,sigma", [
    ("strike-slip", 0.39355007545577764, 0.227),
    ("reverse", 0.5963483198341264, 0.149),
    ("normal", 0.3447466065731491, 0.195),
])
def test_thingbaijam2017_average_displacement(style, expected, sigma):
    sr = Thingbaijam2017()
    ad, got_sigma = sr.get_average_displacement(6.5, style, return_sigma=True)
    assert ad == pytest.approx(expected, rel=1e-12)
    assert got_sigma == pytest.approx(sigma, rel=1e-12)


# ---------------------------------------------------------------------------
# Mammarella et al. (2024) Table 1 coverage
#
# TAB1 columns are [MSR, SoF, a, b, W_sigma]; SoF 3/4/5 are normal,
# reverse and strike-slip.  MSR 0/1 are the Leonard (2014) interplate and
# stable-continental-region width relations with ``b = 2.5`` and forward
# form ``m = a + b*log10(W)``; MSR 2 is Thingbaijam et al. (2017) with
# ``log10(W) = a + b*m``.  This is the "ensure Thingbaijam2017 (and the
# Leonard 2014 widths) cover Mammarella2024PrimarySR" acceptance check.
# ---------------------------------------------------------------------------
SOF_TO_RAKE = {3: -90.0, 4: 90.0, 5: 0.0}
MSR_TO_CLASS = {
    0: Leonard2014_Interplate,
    1: Leonard2014_SCR,
    2: Thingbaijam2017,
}


@pytest.mark.parametrize("row", [tuple(r) for r in TAB1],
                         ids=lambda r: "MSR%d-SoF%d" % (r[0], r[1]))
def test_mammarella_table1_width_coverage(row):
    msr, sof, a, b, w_sigma = (int(row[0]), int(row[1]),
                               float(row[2]), float(row[3]), float(row[4]))
    sr = MSR_TO_CLASS[msr]()
    rake = SOF_TO_RAKE[sof]
    mag = 6.5
    value = sr.get_median_width(mag, rake)
    if msr in (0, 1):
        expected = 10.0 ** ((mag - a) / b)
    else:
        expected = 10.0 ** (a + b * mag)
    assert value == pytest.approx(expected, rel=1e-12)
    assert sr.get_std_dev_width(mag, rake) == pytest.approx(w_sigma, rel=1e-12)


# ---------------------------------------------------------------------------
# Leonard (2010) dip-slip relations
# ---------------------------------------------------------------------------
def test_leonard2010_dip_slip():
    sr = Leonard2010()
    ad, sigma = sr.get_average_displacement(6.5, "reverse", return_sigma=True)
    assert ad == pytest.approx(0.3805825935566178, rel=1e-12)
    assert sigma == pytest.approx(0.23, rel=1e-12)
    length, sigma = sr.get_rupture_length(6.5, return_sigma=True)
    assert length == pytest.approx(22.3872113856834, rel=1e-12)
    assert sigma == pytest.approx(0.23, rel=1e-12)


# ---------------------------------------------------------------------------
# Resolution through the engine's magnitude-scale-relationship machinery
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", [
    "WC1994", "Thingbaijam2017", "Leonard2010",
    "Leonard2014_SCR", "Leonard2014_Interplate"])
def test_resolvable_via_valid_mag_scale_rel(name):
    sr = valid.mag_scale_rel(name)
    assert type(sr).__name__ == name
    # the FD relations are exposed by name to the logic-tree/oqparam layer
    assert hasattr(sr, "get_median_area")