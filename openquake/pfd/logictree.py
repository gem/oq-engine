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
FDHA logic-tree reader and end-branch enumerator (PR-5 of the oq-engine
integration plan, Workstream E).

The FDHA logic tree keeps the oq-pfdha NRML schema (decision D5): an NRML
0.4 ``<logicTree>`` whose ``uncertaintyType`` is one of the four model slots

    fdhaPrimarySRModel   -> primary_surf_rup
    fdhaPrimaryFDModel   -> primary_surf_displ
    fdhaSecondarySRModel -> secondary_surf_rup
    fdhaSecondaryFDModel -> secondary_surf_displ

plus the calculation-parameter slot ``fdhaCalcRSigma`` (an epistemic
alternative for ``[calculation] r_sigma_km``).  Each ``<uncertaintyModel>``
holds either a bare model class name or an oq-engine style ``[ClassName]``
INI block of validated constructor parameters; ``fdhaCalcRSigma`` holds a
bare non-negative float.

The XML is read through the engine's :mod:`openquake.hazardlib.nrml` reader
(the same reader used for the source-model and GMPE logic trees) and the
end branches are enumerated with the oq-pfdha ``applyToSources`` /
``applyToBranches`` / ``applyToStyle`` filter semantics.  This replaces the
oq-pfdha ``logic_tree/{types,enumerator,nrml_reader,param_parser}.py``
modules, whose output it reproduces.
"""
import ast
import configparser
import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from openquake.hazardlib import nrml
from openquake.pfd.adapter import style_from_rake


#: model slot for each FDHA model uncertainty type
FDHA_SLOTS_BY_UTYPE = {
    "fdhaPrimarySRModel": "primary_surf_rup",
    "fdhaPrimaryFDModel": "primary_surf_displ",
    "fdhaSecondarySRModel": "secondary_surf_rup",
    "fdhaSecondaryFDModel": "secondary_surf_displ",
}

#: the calculation-parameter uncertainty type and its pseudo-slot
CALC_SLOTS_BY_UTYPE = {"fdhaCalcRSigma": "calc_r_sigma"}
CALC_R_SIGMA_SLOT = "calc_r_sigma"
R_SIGMA_KM_KEY = "r_sigma_km"

FDHA_UNCERTAINTY_TYPES = frozenset(FDHA_SLOTS_BY_UTYPE) | frozenset(
    CALC_SLOTS_BY_UTYPE)

#: the four model slots a well-formed end branch must select
FDHA_MODEL_SLOTS = tuple(FDHA_SLOTS_BY_UTYPE.values())


@dataclass(frozen=True)
class ModelChoice:
    """One uncertaintyModel selection inside an end branch."""
    class_name: str
    params: Dict[str, Any]
    branch_id: str
    weight: float


@dataclass(frozen=True)
class EndBranch:
    """
    A fully-enumerated FDHA realization for one source.

    ``selections`` maps each slot name (the four model slots plus, when
    present, ``calc_r_sigma``) to a :class:`ModelChoice`.
    """
    source_id: str
    style: str
    weight: float
    selections: Dict[str, ModelChoice]

    @property
    def slots(self) -> Tuple[str, ...]:
        return tuple(sorted(self.selections))


def parse_uncertainty_model(text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parse the text of an ``<uncertaintyModel>`` element.

    :returns: ``(class_name, params)`` where ``params`` is empty for a bare
        class name and the parsed ``[ClassName]`` INI block otherwise.
    """
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Empty uncertaintyModel")
    if raw.startswith("[") and "]" in raw.splitlines()[0]:
        return _parse_ini_block(raw)
    if "\n" in raw:
        # tolerate wrapped text; a bare name is a single token
        raw = "".join(line.strip() for line in raw.splitlines() if line.strip())
    return raw, {}


def _parse_ini_block(raw: str) -> Tuple[str, Dict[str, Any]]:
    # NRML indents the block to the XML nesting depth, so strip every line
    # before handing it to configparser (values are single-line).
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    header = lines[0]
    if not (header.startswith("[") and header.endswith("]")):
        raise ValueError("INI block must start with [ClassName]")
    class_name = header[1:-1].strip()
    if not class_name:
        raise ValueError("Empty class name in INI header")

    cp = configparser.RawConfigParser()
    cp.optionxform = str
    cp.read_string("\n".join(lines))
    params: Dict[str, Any] = {}
    if cp.has_section(class_name):
        for k, v in cp.items(class_name):
            params[k] = _parse_value(v)
    return class_name, params


def parse_r_sigma_model(text: str) -> float:
    """
    Parse the ``<uncertaintyModel>`` of an ``fdhaCalcRSigma`` branch.

    The value is the two-sided mapping-accuracy sigma ``r_sigma_km`` of the
    Petersen et al. (2011) rupture-location term: a finite float ``>= 0``.
    Zero is legal and selects the boxcar ``W_p`` path.
    """
    raw = (text or "").strip()
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(
            "fdhaCalcRSigma: expected a single non-negative float (km) in "
            f"<uncertaintyModel>, got {raw!r}")
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(
            "fdhaCalcRSigma value must be a non-negative finite float (km); "
            f"got {raw!r}")
    return value


def _parse_value(value: str) -> Any:
    s = value.strip()
    if s == "":
        return ""
    try:
        return ast.literal_eval(s)
    except Exception:
        return s


@dataclass(frozen=True)
class _BranchSet:
    branch_set_id: str
    uncertainty_type: str
    apply_to_sources: Optional[str]
    apply_to_branches: Optional[str]
    apply_to_style: Optional[str]
    branches: Tuple[Tuple[str, str, str], ...]  # (branch_id, model, weight)


def read_logic_tree(filename: str) -> List[Tuple[_BranchSet, ...]]:
    """
    Read an FDHA logic tree into a list of branching levels, each a tuple of
    branch sets.  ``uncertaintyType`` values outside the FDHA vocabulary are
    rejected up front.
    """
    root = nrml.read(filename)
    try:
        lt = root.logicTree
    except AttributeError:
        raise ValueError(f"{filename}: missing <logicTree> element")

    levels: List[Tuple[_BranchSet, ...]] = []
    for bl in lt.getnodes('logicTreeBranchingLevel'):
        bsets = []
        for bs in bl.getnodes('logicTreeBranchSet'):
            utype = bs.get('uncertaintyType', '')
            if utype not in FDHA_UNCERTAINTY_TYPES:
                raise ValueError(
                    f"{filename}: unknown FDHA uncertaintyType {utype!r}; "
                    f"expected one of {sorted(FDHA_UNCERTAINTY_TYPES)}")
            branches = []
            for br in bs.getnodes('logicTreeBranch'):
                try:
                    model = br.uncertaintyModel
                    weight = br.uncertaintyWeight
                except AttributeError:
                    raise ValueError(
                        f"{filename}: branch {br.get('branchID')!r} is "
                        "missing uncertaintyModel/uncertaintyWeight")
                branches.append(
                    (br.get('branchID', ''), model.text or '', weight.text or ''))
            bsets.append(_BranchSet(
                branch_set_id=bs.get('branchSetID', ''),
                uncertainty_type=utype,
                apply_to_sources=bs.get('applyToSources'),
                apply_to_branches=bs.get('applyToBranches'),
                apply_to_style=bs.get('applyToStyle'),
                branches=tuple(branches)))
        levels.append(tuple(bsets))
    return levels


def _branchset_applies(bs: _BranchSet, source_id: str, style: str,
                       chosen_ids: set) -> bool:
    if bs.apply_to_style is not None and bs.apply_to_style != style:
        return False
    if bs.apply_to_sources is not None:
        if source_id not in set(bs.apply_to_sources.split()):
            return False
    if bs.apply_to_branches is not None:
        if not (chosen_ids & set(bs.apply_to_branches.split())):
            return False
    return True


def _check_weights(bs: _BranchSet, filename: str) -> None:
    total = 0.0
    for _bid, _model, w in bs.branches:
        try:
            total += float(w)
        except (TypeError, ValueError):
            raise ValueError(
                f"{filename}: branch set {bs.branch_set_id!r} has a "
                f"non-numeric weight {w!r}")
    if abs(total - 1.0) > 1e-9:
        raise ValueError(
            f"{filename}: branch set {bs.branch_set_id!r} weights sum to "
            f"{total}, not 1.0 (FDLT-001)")


def enumerate_end_branches(
        filename: str,
        sources: Iterable[Tuple[str, float]]) -> List[EndBranch]:
    """
    Enumerate the FDHA end branches for the given sources.

    :param filename: the FDHA logic-tree XML
    :param sources: iterable of ``(source_id, rake)`` pairs; the rake fixes
        the faulting style used by ``applyToStyle`` filters
    :returns: one :class:`EndBranch` per (source, branch combination)
    """
    levels = read_logic_tree(filename)
    for level in levels:
        for bs in level:
            _check_weights(bs, filename)

    end_branches: List[EndBranch] = []
    for source_id, rake in sources:
        style = style_from_rake(rake)
        partials: List[Tuple[Dict[str, ModelChoice], set, float]] = [
            ({}, set(), 1.0)]
        for level in levels:
            for bs in level:
                nxt = []
                for selections, chosen_ids, weight in partials:
                    if not _branchset_applies(bs, source_id, style, chosen_ids):
                        nxt.append((selections, chosen_ids, weight))
                        continue
                    slot = FDHA_SLOTS_BY_UTYPE.get(bs.uncertainty_type)
                    calc_slot = CALC_SLOTS_BY_UTYPE.get(bs.uncertainty_type)
                    for bid, model, raw_weight in bs.branches:
                        try:
                            w = float(raw_weight)
                        except (TypeError, ValueError):
                            w = float('nan')
                        if calc_slot is not None:
                            choice = ModelChoice(
                                class_name=R_SIGMA_KM_KEY,
                                params={R_SIGMA_KM_KEY:
                                        parse_r_sigma_model(model)},
                                branch_id=bid, weight=w)
                            key = calc_slot
                        else:
                            class_name, params = parse_uncertainty_model(model)
                            choice = ModelChoice(
                                class_name=class_name, params=params,
                                branch_id=bid, weight=w)
                            key = slot
                        new_sel = dict(selections)
                        new_sel[key] = choice
                        nxt.append((new_sel, chosen_ids | {bid}, weight * w))
                partials = nxt
        for selections, _ids, weight in partials:
            end_branches.append(EndBranch(
                source_id=source_id, style=style, weight=weight,
                selections=selections))
    return end_branches


def check_r_sigma_conflict(r_sigma_km: Optional[float],
                           end_branches: Iterable[EndBranch]) -> None:
    """
    Reject a scalar ``[calculation] r_sigma_km`` combined with an
    ``fdhaCalcRSigma`` logic-tree branch up front: the two would fight over
    the same parameter.  Either pin it in the job.ini or vary it in the
    logic tree, not both.
    """
    if r_sigma_km is None:
        return
    if any(CALC_R_SIGMA_SLOT in eb.selections for eb in end_branches):
        raise ValueError(
            "r_sigma_km is set both as a scalar [calculation] parameter and "
            "as an fdhaCalcRSigma logic-tree branch; remove one of the two")
