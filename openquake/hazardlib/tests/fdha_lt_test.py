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

"""Tests for the PFD logic tree in :mod:`openquake.hazardlib.pfd_lt`."""
import collections

import pytest

from openquake.baselib.node import Node
from openquake.hazardlib import lt
from openquake.hazardlib.pfd_lt import PFDLogicTree
from openquake.hazardlib.lt import LogicTreeError


def parse_model(text, utype="fdhaPrimarySRModel"):
    return lt.parse_uncertainty(
        utype, Node("uncertaintyModel", text=text), "lt.xml")


def parse_sigma(text):
    return lt.parse_uncertainty(
        "fdhaCalcRSigma", Node("uncertaintyModel", text=text), "lt.xml")


def toml_block(cls, **params):
    body = "\n".join(f"            {k} = {v}" for k, v in params.items())
    return f"\n            [{cls}]\n{body}\n          "


def branchset(bsid, utype, branches, **attrs):
    attrs_str = "".join(f' {k}="{v}"' for k, v in attrs.items())
    brs = "".join(
        f'        <logicTreeBranch branchID="{bid}">'
        f'<uncertaintyModel>{model}</uncertaintyModel>'
        f'<uncertaintyWeight>{weight}</uncertaintyWeight>'
        f'</logicTreeBranch>\n'
        for bid, model, weight in branches)
    return (f'      <logicTreeBranchSet branchSetID="{bsid}" '
            f'uncertaintyType="{utype}"{attrs_str}>\n{brs}'
            f'      </logicTreeBranchSet>\n')


def write(tmp_path, *branchsets):
    body = "".join(branchsets)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">\n'
           '  <logicTree logicTreeID="lt">\n'
           f'{body}'
           '  </logicTree>\n</nrml>\n')
    path = tmp_path / "lt.xml"
    path.write_text(xml)
    return str(path)


def full_chain():
    """The minimal four-slot chain (one branch each)."""
    return (
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1", toml_block("Youngs2003PrimarySR", style="all"), 1.0)]),
        branchset("bs2", "fdhaPrimaryFDModel", [
            ("B2", toml_block("Youngs2003PrimaryFD", style="normal",
                       norm_disp_type="AD"), 1.0)],
            applyToBranches="B1"),
        branchset("bs3", "fdhaSecondarySRModel", [
            ("B3", toml_block("Youngs2003SecondarySR", version=3, style="all"),
             1.0)], applyToBranches="B2"),
        branchset("bs4", "fdhaSecondaryFDModel", [
            ("B4", toml_block("Youngs2003SecondaryFD", style="normal"), 1.0)],
            applyToBranches="B3"),
    )


# --------------------------------------------------------------------------
# parameter parsing
# --------------------------------------------------------------------------
def test_parse_plain_class_name():
    assert parse_model("Youngs2003PrimarySR") == (
        "Youngs2003PrimarySR", {})


def test_parse_toml_block_types():
    cls, params = parse_model(toml_block(
        "Moss2024PrimaryFD", version="MD", completeness="all",
        pixel_size=50, fractions=[0.1, 0.9]))
    assert cls == "Moss2024PrimaryFD"
    assert params == {"version": "MD", "completeness": "all",
                      "pixel_size": 50, "fractions": [0.1, 0.9]}


def test_parse_toml_block_numeric_version_stays_int():
    _cls, params = parse_model(toml_block("X", version=3))
    assert params["version"] == 3 and isinstance(params["version"], int)


@pytest.mark.parametrize("text,expected", [("0", 0.0), ("2.5", 2.5),
                                           (" 10 ", 10.0)])
def test_parse_r_sigma_valid(text, expected):
    assert parse_sigma(text) == expected


@pytest.mark.parametrize("text", ["", "key = 1", "-1", "nan", "inf", "1 2"])
def test_parse_r_sigma_rejects(text):
    with pytest.raises(LogicTreeError):
        parse_sigma(text)


# --------------------------------------------------------------------------
# reading and enumeration
# --------------------------------------------------------------------------
def test_unknown_utype_rejected(tmp_path):
    path = write(tmp_path, branchset(
        "bs1", "gmpeModel", [("B1", "BooreAtkinson2008", 1.0)]))
    with pytest.raises(LogicTreeError, match="unknown FDHA uncertaintyType"):
        PFDLogicTree(path)


def test_weights_must_sum_to_one(tmp_path):
    path = write(tmp_path, branchset(
        "bs1", "fdhaPrimarySRModel", [
            ("B1a", "MossRoss2011PrimarySR", 0.7),
            ("B1b", "Takao2013PrimarySR", 0.2)]))
    with pytest.raises(LogicTreeError, match="weights sum"):
        PFDLogicTree(path)


def test_enumerate_single_chain(tmp_path):
    lt = PFDLogicTree(write(tmp_path, *full_chain()))
    [eb] = lt.enumerate([("src1", "reverse")])
    assert eb.source_id == "src1"
    assert eb.style == "reverse"
    assert eb.weight == 1.0
    assert eb.slots == ("primary_surf_displ", "primary_surf_rup",
                        "secondary_surf_displ", "secondary_surf_rup")
    assert eb.selections["primary_surf_rup"].class_name == "Youngs2003PrimarySR"
    assert eb.selections["primary_surf_displ"].params == {
        "style": "normal", "norm_disp_type": "AD"}
    assert eb.selections["secondary_surf_rup"].params == {
        "version": 3, "style": "all"}


def test_enumerate_two_branches_and_weights(tmp_path):
    path = write(
        tmp_path,
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1a", "MossRoss2011PrimarySR", 0.7),
            ("B1b", "Takao2013PrimarySR", 0.3)]),
        branchset("bs2", "fdhaPrimaryFDModel", [
            ("B2", "MossRoss2011PrimaryFD", 1.0)],
            applyToBranches="B1a B1b"))
    branches = PFDLogicTree(path).enumerate([("src1", "strike-slip")])
    assert [b.selections["primary_surf_rup"].branch_id for b in branches] == [
        "B1a", "B1b"]
    assert [b.weight for b in branches] == [0.7, 0.3]


def test_apply_to_branches_filter(tmp_path):
    path = write(
        tmp_path,
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1a", "MossRoss2011PrimarySR", 0.5),
            ("B1b", "Takao2013PrimarySR", 0.5)]),
        # applies only under B1a: the B1b branch must not carry a FD selection
        branchset("bs2", "fdhaPrimaryFDModel", [
            ("B2", "MossRoss2011PrimaryFD", 1.0)], applyToBranches="B1a"))
    by_id = {b.selections["primary_surf_rup"].branch_id: b
             for b in PFDLogicTree(path).enumerate(
                 [("src1", "strike-slip")])}
    assert "primary_surf_displ" in by_id["B1a"].selections
    assert "primary_surf_displ" not in by_id["B1b"].selections


def test_apply_to_style_filter(tmp_path):
    path = write(tmp_path, branchset(
        "bs1", "fdhaPrimarySRModel", [("B1", "Moss2013PrimarySR", 1.0)],
        applyToStyle="reverse"))
    lt = PFDLogicTree(path)
    assert lt.enumerate([("src1", "reverse")])[0].selections
    assert lt.enumerate([("src1", "normal")])[0].selections == {}


def test_apply_to_sources_filter(tmp_path):
    path = write(tmp_path, branchset(
        "bs1", "fdhaPrimarySRModel", [("B1", "Moss2013PrimarySR", 1.0)],
        applyToSources="src1"))
    branches = PFDLogicTree(path).enumerate(
        [("src1", "normal"), ("src2", "normal")])
    assert branches[0].selections and branches[1].selections == {}


def test_calc_r_sigma_branch(tmp_path):
    path = write(
        tmp_path,
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1", "MossRoss2011PrimarySR", 1.0)]),
        branchset("bs_sigma", "fdhaCalcRSigma", [
            ("SIG0", "0", 0.4), ("SIG2", "2", 0.6)]))
    branches = PFDLogicTree(path).enumerate([("src1", "normal")])
    assert [b.weight for b in branches] == [0.4, 0.6]
    assert branches[0].selections["calc_r_sigma"].params == {"r_sigma_km": 0.0}
    assert branches[1].selections["calc_r_sigma"].params == {"r_sigma_km": 2.0}


def test_check_r_sigma_conflict(tmp_path):
    lt = PFDLogicTree(write(tmp_path, *full_chain()))
    branches = lt.enumerate([("src1", "normal")])
    lt.check_r_sigma_conflict(None, branches)  # no scalar -> fine

    path2 = write(tmp_path, *full_chain(), branchset(
        "bs_sigma", "fdhaCalcRSigma", [("SIG", "1", 1.0)]))
    lt2 = PFDLogicTree(path2)
    branches2 = lt2.enumerate([("src1", "normal")])
    with pytest.raises(LogicTreeError, match="both"):
        lt2.check_r_sigma_conflict(1.0, branches2)

def test_h5_roundtrip(tmp_path):
    """__toh5__/__fromh5__ preserve branches, filters and calc parameters."""
    path = write(
        tmp_path,
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1", toml_block("Youngs2003PrimarySR", style="all"), 1.0)],
            applyToSources="src1", applyToStyle="reverse"),
        branchset("bs2", "fdhaPrimaryFDModel", [
            ("B2", toml_block("Youngs2003PrimaryFD", style="normal",
                              norm_disp_type="AD"), 1.0)],
            applyToBranches="B1"),
        branchset("bs_sigma", "fdhaCalcRSigma", [
            ("SIG0", "0", 0.4), ("SIG2", "2", 0.6)]))
    lt = PFDLogicTree(path)
    array, attrs = lt.__toh5__()
    lt2 = object.__new__(PFDLogicTree)
    lt2.__fromh5__(array, attrs)
    for source in [("src1", "reverse"), ("src1", "normal"),
                   ("src2", "reverse")]:
        r1 = lt.enumerate([source])
        r2 = lt2.enumerate([source])
        assert [(r.source_id, r.style, r.weight, r.slots, r.selections)
                for r in r1] == \
               [(r.source_id, r.style, r.weight, r.slots, r.selections)
                for r in r2]


def write_wrapped(tmp_path, *branchsets):
    body = "".join(
        f'    <logicTreeBranchingLevel branchingLevelID="bl{i}">\n{bs}'
        f'    </logicTreeBranchingLevel>\n'
        for i, bs in enumerate(branchsets))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">\n'
           '  <logicTree logicTreeID="lt">\n'
           f'{body}'
           '  </logicTree>\n</nrml>\n')
    path = tmp_path / "lt_wrapped.xml"
    path.write_text(xml)
    return str(path)


def test_branching_level_accepted(tmp_path):
    """The legacy <logicTreeBranchingLevel> wrapper is accepted via bsnodes."""
    direct = PFDLogicTree(write(tmp_path, *full_chain()))
    wrapped = PFDLogicTree(write_wrapped(tmp_path, *full_chain()))
    r1 = direct.enumerate([("src1", "reverse")])
    r2 = wrapped.enumerate([("src1", "reverse")])
    assert [(r.weight, r.selections, r.slots) for r in r1] == \
           [(r.weight, r.selections, r.slots) for r in r2]


def test_sampling_counts_and_weights(tmp_path):
    path = write(tmp_path, branchset("bs1", "fdhaPrimarySRModel", [
        ("B1a", "MossRoss2011PrimarySR", 0.7),
        ("B1b", "Takao2013PrimarySR", 0.3)]))
    n = 2000
    branches = PFDLogicTree(
        path, seed=42, num_samples=n).enumerate([("src1", "normal")])
    assert len(branches) == n
    assert all(abs(b.weight - 1.0 / n) < 1e-12 for b in branches)
    counts = collections.Counter(
        b.selections["primary_surf_rup"].branch_id for b in branches)
    assert set(counts) == {"B1a", "B1b"}
    assert 0.6 < counts["B1a"] / n < 0.8  # weight 0.7


def test_sampling_deterministic(tmp_path):
    path = write(tmp_path, branchset("bs1", "fdhaPrimarySRModel", [
        ("B1a", "MossRoss2011PrimarySR", 0.7),
        ("B1b", "Takao2013PrimarySR", 0.3)]))
    a = PFDLogicTree(path, seed=7, num_samples=50).enumerate([("s", "normal")])
    b = PFDLogicTree(path, seed=7, num_samples=50).enumerate([("s", "normal")])
    c = PFDLogicTree(path, seed=8, num_samples=50).enumerate([("s", "normal")])
    assert [r.selections for r in a] == [r.selections for r in b]
    assert [r.selections for r in a] != [r.selections for r in c]


def test_sampling_respects_apply_to_branches(tmp_path):
    path = write(
        tmp_path,
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1a", "MossRoss2011PrimarySR", 0.5),
            ("B1b", "Takao2013PrimarySR", 0.5)]),
        branchset("bs2", "fdhaPrimaryFDModel", [
            ("B2", "MossRoss2011PrimaryFD", 1.0)], applyToBranches="B1a"))
    for r in PFDLogicTree(path, seed=1, num_samples=50).enumerate(
            [("src1", "normal")]):
        sr = r.selections["primary_surf_rup"].branch_id
        assert ("primary_surf_displ" in r.selections) == (sr == "B1a")


def test_sampling_h5_roundtrip(tmp_path):
    path = write(tmp_path, branchset("bs1", "fdhaPrimarySRModel", [
        ("B1a", "MossRoss2011PrimarySR", 0.7),
        ("B1b", "Takao2013PrimarySR", 0.3)]))
    lt1 = PFDLogicTree(path, seed=5, num_samples=20,
                       sampling_method='late_weights')
    array, attrs = lt1.__toh5__()
    lt2 = object.__new__(PFDLogicTree)
    lt2.__fromh5__(array, attrs)
    assert (lt2.seed, lt2.num_samples, lt2.sampling_method) == (
        5, 20, 'late_weights')
    assert [r.selections for r in lt1.enumerate([("s", "normal")])] == \
           [r.selections for r in lt2.enumerate([("s", "normal")])]
