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
from unittest import mock

import pytest

from openquake.baselib.node import Node
from openquake.hazardlib import lt, logictree
from openquake.hazardlib.pfd_lt import PFDLogicTree
from openquake.hazardlib.lt import LogicTreeError


def parse_model(text, utype="fdhaPrimarySRModel"):
    return lt.parse_uncertainty(
        utype, Node("uncertaintyModel", text=text), "lt.xml")


def parse_sigma(text):
    return lt.parse_uncertainty(
        "fdhaCalcRSigma", Node("uncertaintyModel", text=text), "lt.xml")


def toml_block(cls, **params):
    body = "\n".join(
        f'            {k} = {_toml_value(v)}' for k, v in params.items())
    return f"\n            [{cls}]\n{body}\n          "


def _toml_value(value):
    return f'"{value}"' if isinstance(value, str) else str(value)


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


def rlz_selections(tree, rlzs, source_id, style):
    """
    :returns: the (weight, selections) of each realization for the given
        source, as computed by the displacement calculator
    """
    return [(rlz.weight, tree.selections_for(rlz.lt_path, source_id, style))
            for rlz in rlzs]


def selections(tree, source_id, style):
    """
    :returns: the (weight, selections) of each realization of the tree
    """
    return rlz_selections(tree, tree.get_realizations(), source_id, style)


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
# reading, realizations and selections
# --------------------------------------------------------------------------
def test_unknown_utype_rejected(tmp_path):
    path = write(tmp_path, branchset(
        "bs1", "gmpeModel", [("B1", "BooreAtkinson2008", 1.0)]))
    with pytest.raises(LogicTreeError, match="unknown PFD uncertaintyType"):
        PFDLogicTree(path)


def test_weights_must_sum_to_one(tmp_path):
    path = write(tmp_path, branchset(
        "bs1", "fdhaPrimarySRModel", [
            ("B1a", "MossRoss2011PrimarySR", 0.7),
            ("B1b", "Takao2013PrimarySR", 0.2)]))
    with pytest.raises(LogicTreeError, match="weights sum"):
        PFDLogicTree(path)


def test_single_chain(tmp_path):
    tree = PFDLogicTree(write(tmp_path, *full_chain()))
    [(weight, sel)] = selections(tree, "src1", "reverse")
    assert weight == 1.0
    assert sorted(sel) == ["primary_surf_displ", "primary_surf_rup",
                           "secondary_surf_displ", "secondary_surf_rup"]
    assert sel["primary_surf_rup"].class_name == "Youngs2003PrimarySR"
    assert sel["primary_surf_displ"].params == {
        "style": "normal", "norm_disp_type": "AD"}
    assert sel["secondary_surf_rup"].params == {
        "version": 3, "style": "all"}


def test_two_branches_and_weights(tmp_path):
    path = write(
        tmp_path,
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1a", "MossRoss2011PrimarySR", 0.7),
            ("B1b", "Takao2013PrimarySR", 0.3)]),
        branchset("bs2", "fdhaPrimaryFDModel", [
            ("B2", "MossRoss2011PrimaryFD", 1.0)],
            applyToBranches="B1a B1b"))
    pairs = selections(PFDLogicTree(path), "src1", "strike-slip")
    assert [sel["primary_surf_rup"].branch_id for _, sel in pairs] == [
        "B1a", "B1b"]
    assert [weight for weight, _ in pairs] == [0.7, 0.3]


def test_get_num_paths(tmp_path):
    assert PFDLogicTree(write(tmp_path, *full_chain())).get_num_paths() == 1
    path = write(
        tmp_path,
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1a", "MossRoss2011PrimarySR", 0.7),
            ("B1b", "Takao2013PrimarySR", 0.3)]),
        branchset("bs2", "fdhaPrimaryFDModel", [
            ("B2", "MossRoss2011PrimaryFD", 1.0)],
            applyToBranches="B1a B1b"))
    tree = PFDLogicTree(path)
    assert tree.get_num_paths() == 2
    rlzs = tree.get_realizations()
    assert [r.weight for r in rlzs] == [0.7, 0.3]


def test_get_num_paths_with_sampling(tmp_path):
    tree = PFDLogicTree(write(tmp_path, *full_chain()), num_samples=5)
    assert tree.get_num_paths() == 5
    assert len(tree.get_realizations()) == 1
    assert len(tree.sample(5, seed=7)) == 5


def test_apply_to_branches_filter(tmp_path):
    path = write(
        tmp_path,
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1a", "MossRoss2011PrimarySR", 0.5),
            ("B1b", "Takao2013PrimarySR", 0.5)]),
        # applies only under B1a: the B1b branch must not carry a FD selection
        branchset("bs2", "fdhaPrimaryFDModel", [
            ("B2", "MossRoss2011PrimaryFD", 1.0)], applyToBranches="B1a"))
    by_id = {sel["primary_surf_rup"].branch_id: sel for _, sel in
             selections(PFDLogicTree(path), "src1", "strike-slip")}
    assert "primary_surf_displ" in by_id["B1a"]
    assert "primary_surf_displ" not in by_id["B1b"]


def test_apply_to_style_filter(tmp_path):
    path = write(tmp_path, branchset(
        "bs1", "fdhaPrimarySRModel", [("B1", "Moss2013PrimarySR", 1.0)],
        applyToStyle="reverse"))
    tree = PFDLogicTree(path)
    assert selections(tree, "src1", "reverse")[0][1]
    assert selections(tree, "src1", "normal")[0][1] == {}


def test_apply_to_sources_filter(tmp_path):
    path = write(tmp_path, branchset(
        "bs1", "fdhaPrimarySRModel", [("B1", "Moss2013PrimarySR", 1.0)],
        applyToSources="src1"))
    tree = PFDLogicTree(path)
    assert selections(tree, "src1", "normal")[0][1]
    assert selections(tree, "src2", "normal")[0][1] == {}


def test_calc_r_sigma_branch(tmp_path):
    path = write(
        tmp_path,
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1", "MossRoss2011PrimarySR", 1.0)]),
        branchset("bs_sigma", "fdhaCalcRSigma", [
            ("SIG0", "0", 0.4), ("SIG2", "2", 0.6)]))
    pairs = selections(PFDLogicTree(path), "src1", "normal")
    assert [weight for weight, _ in pairs] == [0.4, 0.6]
    assert pairs[0][1]["calc_r_sigma"].params == {"r_sigma_km": 0.0}
    assert pairs[1][1]["calc_r_sigma"].params == {"r_sigma_km": 2.0}


def test_check_r_sigma_conflict(tmp_path):
    tree = PFDLogicTree(write(tmp_path, *full_chain()))
    tree.check_r_sigma_conflict(None)  # no scalar -> fine
    tree.check_r_sigma_conflict(1.0)  # no fdhaCalcRSigma branchset -> fine

    path2 = write(tmp_path, *full_chain(), branchset(
        "bs_sigma", "fdhaCalcRSigma", [("SIG", "1", 1.0)]))
    tree2 = PFDLogicTree(path2)
    tree2.check_r_sigma_conflict(None)  # r_sigma_km not in the job.ini
    for r_sigma_km in (1.0, 0.0):  # also an explicit zero is a conflict
        with pytest.raises(LogicTreeError, match="both"):
            tree2.check_r_sigma_conflict(r_sigma_km)


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
    tree = PFDLogicTree(path)
    array, attrs = tree.__toh5__()
    tree2 = object.__new__(PFDLogicTree)
    tree2.__fromh5__(array, attrs)
    for source in [("src1", "reverse"), ("src1", "normal"),
                   ("src2", "reverse")]:
        assert selections(tree, *source) == selections(tree2, *source)


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
    assert (selections(direct, "src1", "reverse") ==
            selections(wrapped, "src1", "reverse"))


# --------------------------------------------------------------------------
# sampling, as done by FullLogicTree (the weights are set by FullLogicTree)
# --------------------------------------------------------------------------
def test_sampling_counts(tmp_path):
    path = write(tmp_path, branchset("bs1", "fdhaPrimarySRModel", [
        ("B1a", "MossRoss2011PrimarySR", 0.7),
        ("B1b", "Takao2013PrimarySR", 0.3)]))
    n = 2000
    rlzs = PFDLogicTree(path).sample(n, seed=42)
    assert len(rlzs) == n
    counts = collections.Counter(rlz.lt_path for rlz in rlzs)
    assert set(counts) == {("B1a",), ("B1b",)}
    assert 0.6 < counts["B1a", ] / n < 0.8  # weight 0.7


def test_sampling_deterministic(tmp_path):
    path = write(tmp_path, branchset("bs1", "fdhaPrimarySRModel", [
        ("B1a", "MossRoss2011PrimarySR", 0.7),
        ("B1b", "Takao2013PrimarySR", 0.3)]))
    tree = PFDLogicTree(path)
    a = [rlz.lt_path for rlz in tree.sample(50, seed=7)]
    b = [rlz.lt_path for rlz in tree.sample(50, seed=7)]
    c = [rlz.lt_path for rlz in tree.sample(50, seed=8)]
    assert a == b
    assert a != c


@pytest.mark.parametrize('method', [
    'early_weights', 'early_latin', 'late_weights', 'late_latin'])
def test_sampling_respects_apply_to_branches(tmp_path, method):
    path = write(
        tmp_path,
        branchset("bs1", "fdhaPrimarySRModel", [
            ("B1a", "MossRoss2011PrimarySR", 0.7),
            ("B1b", "Takao2013PrimarySR", 0.3)]),
        branchset("bs2", "fdhaPrimaryFDModel", [
            ("B2a", "MossRoss2011PrimaryFD", 0.25),
            ("B2b", "Youngs2003PrimaryFD", 0.75)], applyToBranches="B1a"))
    tree = PFDLogicTree(path)
    n = 2000
    # Conditional sampling must walk only selected branches, without first
    # enumerating the population, and must omit dummy IDs from extra paths.
    with mock.patch.object(tree, 'get_realizations',
                           side_effect=AssertionError):
        rlzs = tree.sample(n, seed=1, sampling_method=method)
    weights = {('B1a', 'B2a'): .175, ('B1a', 'B2b'): .525, ('B1b',): .3}
    proposals = {('B1a', 'B2a'): .25, ('B1a', 'B2b'): .25, ('B1b',): .5}
    for i, rlz in enumerate(rlzs):
        assert rlz.ordinal == i
        assert rlz.value == '~'.join(rlz.lt_path)
        expected = (1. / n if method.startswith('early') else
                    weights[rlz.lt_path] / proposals[rlz.lt_path])
        assert rlz.weight == pytest.approx(expected)
    # Late sampling chooses uniformly at each branchset, including the root
    # whose two branches have different numbers of complete paths below them.
    frequency = sum(r.lt_path[0] == 'B1a' for r in rlzs) / n
    assert frequency == pytest.approx(
        .7 if method.startswith('early') else .5, abs=.04)
    weighted = sum(r.weight for r in rlzs if r.lt_path[0] == 'B1a')
    assert weighted / sum(r.weight for r in rlzs) == pytest.approx(.7, abs=.04)
    pairs = rlz_selections(tree, rlzs, "src1", "normal")
    for _, sel in pairs:
        sr = sel["primary_surf_rup"].branch_id
        assert ("primary_surf_displ" in sel) == (sr == "B1a")
    full = logictree.FullLogicTree.fake()
    full.extra_lt = tree
    combined = full.sample(n, seed=1, sampling_method=method)
    for path, weight in weights.items():
        got = sum(r.weight[-1] for r in combined
                  if r.extra_rlz.lt_path == path)
        assert got == pytest.approx(weight, abs=.04)


def test_sampling_h5_roundtrip(tmp_path):
    path = write(tmp_path, branchset("bs1", "fdhaPrimarySRModel", [
        ("B1a", "MossRoss2011PrimarySR", 0.7),
        ("B1b", "Takao2013PrimarySR", 0.3)]))
    tree1 = PFDLogicTree(path, seed=5, num_samples=20,
                         sampling_method='late_weights')
    array, attrs = tree1.__toh5__()
    tree2 = object.__new__(PFDLogicTree)
    tree2.__fromh5__(array, attrs)
    assert (tree2.seed, tree2.num_samples, tree2.sampling_method) == (
        5, 20, 'late_weights')
    assert ([rlz.lt_path for rlz in tree1.sample(20, tree1.seed)] ==
            [rlz.lt_path for rlz in tree2.sample(20, tree2.seed)])
