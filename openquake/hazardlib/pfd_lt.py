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
PFD (Probabilistic Fault Displacement) logic tree.

The PFD logic tree is an NRML 0.4 ``<logicTree>`` whose ``uncertaintyType``
is one of the four model slots plus the ``fdhaCalcRSigma`` calculation
parameter, with ``<logicTreeBranchSet>`` elements directly under
``<logicTree>`` (the obsolete ``<logicTreeBranchingLevel>`` wrapper is
rejected).  Like :class:`openquake.hazardlib.logictree.SourceModelLogicTree`
it is source-oriented (``applyToSources`` / ``applyToBranches`` /
``applyToStyle``), so it lives in its own module rather than in
:mod:`openquake.hazardlib.gsim_lt`; the ``<uncertaintyModel>`` values are
parsed by :data:`openquake.hazardlib.lt.parse_uncertainty`.
"""
import json
from dataclasses import dataclass

from openquake.baselib.node import context
from openquake.hazardlib import lt, nrml
from openquake.hazardlib.gsim_lt import InvalidLogicTree
from openquake.hazardlib.logictree import branches_to_h5, h5_to_branches


FDHA_SLOTS_BY_UTYPE = {
    "fdhaPrimarySRModel": "primary_surf_rup",
    "fdhaPrimaryFDModel": "primary_surf_displ",
    "fdhaSecondarySRModel": "secondary_surf_rup",
    "fdhaSecondaryFDModel": "secondary_surf_displ",
}
CALC_SLOTS_BY_UTYPE = {"fdhaCalcRSigma": "calc_r_sigma"}
CALC_R_SIGMA_SLOT = "calc_r_sigma"
R_SIGMA_KM_KEY = "r_sigma_km"
FDHA_UNCERTAINTY_TYPES = frozenset(FDHA_SLOTS_BY_UTYPE) | frozenset(
    CALC_SLOTS_BY_UTYPE)


@dataclass
class FdhaModelChoice:
    """One uncertaintyModel selection inside a PFD realization."""
    class_name: str
    params: dict
    branch_id: str
    weight: float


@dataclass
class PFDBranch:
    """
    A fully-enumerated FDHA realization for one source.

    ``selections`` maps each slot name (the four model slots plus, when
    present, ``calc_r_sigma``) to a :class:`FdhaModelChoice`.
    """
    source_id: str
    style: str
    weight: float
    selections: dict

    @property
    def slots(self):
        return tuple(sorted(self.selections))


@dataclass
class _FdhaBranchSet:
    branch_set_id: str
    uncertainty_type: str
    apply_to_sources: str
    apply_to_branches: str
    apply_to_style: str
    branches: tuple


def _fdha_branchset_applies(bs, source_id, style, chosen_ids):
    if bs.apply_to_style is not None and bs.apply_to_style != style:
        return False
    if bs.apply_to_sources is not None:
        if source_id not in set(bs.apply_to_sources.split()):
            return False
    if bs.apply_to_branches is not None:
        if not (chosen_ids & set(bs.apply_to_branches.split())):
            return False
    return True


class PFDLogicTree(object):
    """
    Reader and realization enumerator for FDHA-style logic trees.

    The XML schema is the oq-pfdha one (decision D5), modernised to put the
    ``<logicTreeBranchSet>`` elements directly under ``<logicTree>``: the
    legacy ``<logicTreeBranchingLevel>`` wrapper is obsolete for FDHA and is
    rejected (it is still supported for regular GSIM/source-model trees).
    Each branch set carries one of the four model slots or
    ``fdhaCalcRSigma``; ``<uncertaintyModel>`` is a bare model class name or
    an oq-engine style ``[ClassName]`` TOML block.  End branches are
    enumerated per source with the oq-pfdha ``applyToSources`` /
    ``applyToBranches`` / ``applyToStyle`` semantics.
    """

    def __init__(self, fname):
        self.filename = fname
        self._ltnode = nrml.read(fname).logicTree
        self.branchsets = self._parse()

    def _parse(self):
        branchsets = []
        for branchset in self._ltnode:
            tag = branchset.tag
            if tag.endswith('logicTreeBranchingLevel'):
                raise InvalidLogicTree(
                    '%s: <logicTreeBranchingLevel> is obsolete for FDHA '
                    'logic trees; put <logicTreeBranchSet> directly under '
                    '<logicTree>' % self.filename)
            if not tag.endswith('logicTreeBranchSet'):
                raise InvalidLogicTree(
                    '%s: unexpected <%s> under <logicTree>'
                    % (self.filename, tag))
            utype = branchset['uncertaintyType']
            if utype not in FDHA_UNCERTAINTY_TYPES:
                raise InvalidLogicTree(
                    '%s: unknown FDHA uncertaintyType %r; expected one '
                    'of %s' % (self.filename, utype,
                               sorted(FDHA_UNCERTAINTY_TYPES)))
            branches = []
            for branch in branchset:
                with context(self.filename, branch):
                    try:
                        model = branch.uncertaintyModel
                        weight = branch.uncertaintyWeight
                    except AttributeError:
                        raise InvalidLogicTree(
                            '%s: branch %r is missing uncertaintyModel/'
                            'uncertaintyWeight'
                            % (self.filename, branch.get('branchID')))
                    value = lt.parse_uncertainty(utype, model, self.filename)
                branches.append((branch.get('branchID', ''), value,
                                 weight.text or ''))
            bset = _FdhaBranchSet(
                branch_set_id=branchset.get('branchSetID', ''),
                uncertainty_type=utype,
                apply_to_sources=branchset.get('applyToSources'),
                apply_to_branches=branchset.get('applyToBranches'),
                apply_to_style=branchset.get('applyToStyle'),
                branches=tuple(branches))
            self._check_weights(bset)
            branchsets.append(bset)
        return branchsets

    def _check_weights(self, bs):
        total = 0.0
        for _bid, _model, w in bs.branches:
            try:
                total += float(w)
            except (TypeError, ValueError):
                raise InvalidLogicTree(
                    '%s: branch set %r has a non-numeric weight %r'
                    % (self.filename, bs.branch_set_id, w))
        if abs(total - 1.0) > 1e-9:
            raise InvalidLogicTree(
                '%s: branch set %r weights sum to %s, not 1.0 (FDLT-001)'
                % (self.filename, bs.branch_set_id, total))

    def enumerate(self, sources):
        """
        :param sources: iterable of ``(source_id, style)`` pairs, style one
            of 'normal' / 'reverse' / 'strike-slip' (used by applyToStyle)
        :returns: one :class:`PFDBranch` per (source, branch combination)
        """
        realizations = []
        for source_id, style in sources:
            partials = [({}, set(), 1.0)]
            for bs in self.branchsets:
                nxt = []
                for selections, chosen_ids, weight in partials:
                    if not _fdha_branchset_applies(
                            bs, source_id, style, chosen_ids):
                        nxt.append((selections, chosen_ids, weight))
                        continue
                    slot = FDHA_SLOTS_BY_UTYPE.get(bs.uncertainty_type)
                    calc_slot = CALC_SLOTS_BY_UTYPE.get(bs.uncertainty_type)
                    for bid, value, raw_weight in bs.branches:
                        try:
                            w = float(raw_weight)
                        except (TypeError, ValueError):
                            w = float('nan')
                        if calc_slot is not None:
                            choice = FdhaModelChoice(
                                R_SIGMA_KM_KEY,
                                {R_SIGMA_KM_KEY: value}, bid, w)
                            key = calc_slot
                        else:
                            class_name, params = value
                            choice = FdhaModelChoice(
                                class_name, params, bid, w)
                            key = slot
                        new_sel = dict(selections)
                        new_sel[key] = choice
                        nxt.append(
                            (new_sel, chosen_ids | {bid}, weight * w))
                partials = nxt
            for selections, _ids, weight in partials:
                realizations.append(PFDBranch(
                    source_id, style, weight, selections))
        return realizations

    def __toh5__(self):
        """
        Serialize with the shared :func:`branches_to_h5` helper (the same
        layout used by
        :class:`openquake.hazardlib.logictree.SourceModelLogicTree`).
        """
        bsetdict = {
            bs.branch_set_id: dict(
                uncertaintyType=bs.uncertainty_type,
                applyToSources=bs.apply_to_sources,
                applyToBranches=bs.apply_to_branches,
                applyToStyle=bs.apply_to_style)
            for bs in self.branchsets}
        branches = [(bs.branch_set_id, bid, bs.uncertainty_type, value, weight)
                    for bs in self.branchsets
                    for bid, value, weight in bs.branches]
        array, attrs = branches_to_h5(branches, bsetdict)
        attrs['filename'] = self.filename
        return array, attrs

    def __fromh5__(self, array, attrs):
        """
        Restore a PFD logic tree serialized by :meth:`__toh5__`.
        """
        self.filename = attrs['filename']
        self.bsetdict = json.loads(attrs['bsetdict'])
        utypes, rows = h5_to_branches(array)
        branchsets = []
        for bsid, grows in rows.items():
            dic = self.bsetdict[bsid]
            branchsets.append(_FdhaBranchSet(
                branch_set_id=bsid,
                uncertainty_type=utypes[bsid],
                apply_to_sources=dic.get('applyToSources'),
                apply_to_branches=dic.get('applyToBranches'),
                apply_to_style=dic.get('applyToStyle'),
                branches=tuple((bid, value, str(weight))
                               for bid, value, weight in grows)))
        self.branchsets = branchsets

    def check_r_sigma_conflict(self, r_sigma_km, realizations):
        """
        Reject a scalar ``[calculation] r_sigma_km`` combined with an
        ``fdhaCalcRSigma`` logic-tree branch: the two would fight over the
        same parameter.  Either pin it in the job.ini or vary it in the
        logic tree, not both.
        """
        if r_sigma_km is None:
            return
        if any(CALC_R_SIGMA_SLOT in eb.selections for eb in realizations):
            raise InvalidLogicTree(
                'r_sigma_km is set both as a scalar [calculation] parameter '
                'and as an fdhaCalcRSigma logic-tree branch; remove one of '
                'the two')
