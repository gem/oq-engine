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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
PFD (Probabilistic Fault Displacement) logic tree.

The PFD logic tree is an NRML 0.4 ``<logicTree>`` whose ``uncertaintyType``
is one of the four model slots plus the ``fdhaCalcRSigma`` calculation
parameter, with the ``<logicTreeBranchSet>`` elements directly under
``<logicTree>`` or wrapped in the legacy ``<logicTreeBranchingLevel>``
(both accepted through ``gsim_lt.bsnodes``).  Like
:class:`openquake.hazardlib.logictree.SourceModelLogicTree` it is
source-oriented (``applyToSources`` / ``applyToBranches`` /
``applyToStyle``) and it is built on the generic
:class:`openquake.hazardlib.lt.Branch`/:class:`~openquake.hazardlib.lt.
BranchSet` structures, so it exposes a ``root_branchset`` and its number of
paths is ``count_paths(root_branchset.branches)``.  The
``<uncertaintyModel>`` values are parsed by
:data:`openquake.hazardlib.lt.parse_uncertainty`.
"""
from dataclasses import dataclass

from openquake.baselib.node import context
from openquake.hazardlib import lt, nrml
from openquake.hazardlib.gsim_lt import bsnodes
from openquake.hazardlib.logictree import check_branchset_weights


PFD_SLOTS_BY_UTYPE = {
    "fdhaPrimarySRModel": "primary_surf_rup",
    "fdhaPrimaryFDModel": "primary_surf_displ",
    "fdhaSecondarySRModel": "secondary_surf_rup",
    "fdhaSecondaryFDModel": "secondary_surf_displ",
}
CALC_SLOTS_BY_UTYPE = {"fdhaCalcRSigma": "calc_r_sigma"}
CALC_R_SIGMA_SLOT = "calc_r_sigma"
R_SIGMA_KM_KEY = "r_sigma_km"
PFD_UNCERTAINTY_TYPES = frozenset(PFD_SLOTS_BY_UTYPE) | frozenset(
    CALC_SLOTS_BY_UTYPE)


def _noop(utype, source, value):
    """The PFD model choices never modify a source, like 'dummy'."""


# tell lt.BranchSet that the PFD uncertainty types are admissible
for _utype in PFD_UNCERTAINTY_TYPES:
    lt.apply_uncertainty[_utype] = _noop


@dataclass
class PfdModelChoice:
    """One uncertaintyModel selection inside a PFD realization."""
    class_name: str
    params: dict
    branch_id: str
    weight: float


@dataclass
class PFDBranch:
    """
    A fully-enumerated PFD realization for one source.

    ``selections`` maps each slot name (the four model slots plus, when
    present, ``calc_r_sigma``) to a :class:`PfdModelChoice`.
    """
    source_id: str
    style: str
    weight: float
    selections: dict

    @property
    def slots(self):
        return tuple(sorted(self.selections))


def _choice(utype, branch_id, value, weight):
    """
    :returns: ``(slot, PfdModelChoice)`` for an ``lt.Branch`` value
    """
    calc_slot = CALC_SLOTS_BY_UTYPE.get(utype)
    if calc_slot is not None:
        return calc_slot, PfdModelChoice(
            R_SIGMA_KM_KEY, {R_SIGMA_KM_KEY: value}, branch_id, weight)
    slot = PFD_SLOTS_BY_UTYPE[utype]
    class_name, params = value
    return slot, PfdModelChoice(class_name, params, branch_id, weight)


class PFDLogicTree(lt.ExtraLogicTree):
    """
    Reader and realization enumerator for PFD-style logic trees.

    The XML schema is the oq-pfdha one (decision D5).  The
    ``<logicTreeBranchSet>`` elements may sit directly under ``<logicTree>``
    or be wrapped in a ``<logicTreeBranchingLevel>``: both are accepted,
    through the same ``gsim_lt.bsnodes`` helper used by
    ``SourceModelLogicTree``.  Each branch set carries one of the four model
    slots or ``fdhaCalcRSigma``; ``<uncertaintyModel>`` is a bare model
    class name or an oq-engine style ``[ClassName]`` TOML block.  End
    branches are enumerated per source with the oq-pfdha ``applyToSources``
    / ``applyToBranches`` / ``applyToStyle`` semantics.
    """

    def __init__(self, fname, seed=0, num_samples=0,
                 sampling_method='early_weights'):
        self.filename = fname
        self.seed = seed
        self.num_samples = num_samples
        self.sampling_method = sampling_method
        self._ltnode = nrml.read(fname).logicTree
        self.bsetdict = {}  # branchset ID -> attributes, see _parse
        self.branchsets = self._parse()
        if self.branchsets:
            # attach the child branchsets to the branches via applyToBranches
            lt.attach_branches(self)
        # NB: applyToSources and applyToStyle are per source and do not
        # affect the global number of paths
        self.set_num_paths()

    def selections_for(self, lt_path, source_id, style):
        """
        :param lt_path: tuple of end-branch IDs (a realization path)
        :param source_id: the source id
        :param style: the faulting style of the source
        :returns: the selections applicable to the given source, i.e. the
            global path filtered by ``applyToSources``/``applyToStyle``
        """
        branchdic = {br.branch_id: (bs, br)
                     for bs in self.branchsets for br in bs.branches}
        chosen_ids = set(lt_path)
        selections = {}
        for bid in lt_path:
            pair = branchdic.get(bid)
            if pair is None:
                continue
            bs, br = pair
            if not self._applies(bs, source_id, style, chosen_ids):
                continue
            slot, choice = _choice(
                bs.uncertainty_type, br.branch_id, br.value, br.weight)
            selections[slot] = choice
        return selections

    def _parse(self):
        branchsets = []
        for bsno, node in enumerate(self._ltnode):
            # bsnodes accepts either a <logicTreeBranchSet> directly or
            # wrapped in a <logicTreeBranchingLevel>, like
            # SourceModelLogicTree
            for branchset in bsnodes(self.filename, node):
                utype = branchset['uncertaintyType']
                if utype not in PFD_UNCERTAINTY_TYPES:
                    raise lt.LogicTreeError(
                        branchset, self.filename,
                        'unknown PFD uncertaintyType %r; expected one of %s'
                        % (utype, sorted(PFD_UNCERTAINTY_TYPES)))
                filters = lt.parse_filters(branchset.attrib)
                bset = lt.BranchSet(utype, filters, ordinal=len(branchsets))
                bset.id = branchset.get('branchSetID', '')
                # the attributes are stored in the datastore, see __toh5__
                self.bsetdict[bset.id] = {
                    key: val for key, val in branchset.attrib.items()
                    if key != 'branchSetID'}
                raw_branches = []
                for branch in branchset:
                    with context(self.filename, branch):
                        try:
                            model = branch.uncertaintyModel
                            weight = branch.uncertaintyWeight
                        except AttributeError:
                            raise lt.LogicTreeError(
                                branch, self.filename,
                                'branch %r is missing uncertaintyModel/'
                                'uncertaintyWeight' % branch.get('branchID'))
                        value = lt.parse_uncertainty(
                            utype, model, self.filename)
                    raw_branches.append(
                        (branch.get('branchID', ''), value, weight.text or ''))
                check_branchset_weights(
                    None, self.filename, bset.id,
                    [raw for _bid, _value, raw in raw_branches])
                for bid, value, raw_weight in raw_branches:
                    bset.branches.append(
                        lt.Branch(bid, value, float(raw_weight), bset.id))
                branchsets.append(bset)
        return branchsets

    def _applies(self, bs, source_id, style, chosen_ids):
        filters = bs.filters
        ats = filters.get('applyToSources')
        if ats is not None and source_id not in ats:
            return False
        atb = filters.get('applyToBranches')
        if atb is not None and not (chosen_ids & set(atb)):
            return False
        ats_style = filters.get('applyToStyle')
        if ats_style is not None and ats_style != style:
            return False
        return True

    def enumerate(self, sources):
        """
        Enumerate the PFD realizations for the given sources.

        :param sources: iterable of ``(source_id, style)`` pairs, style one
            of 'normal' / 'reverse' / 'strike-slip' (used by applyToStyle)
        :returns: one :class:`PFDBranch` per (source, realization).  With
            ``num_samples`` the realizations are Monte-Carlo sampled, else
            all the branch combinations are enumerated with their product
            weight.
        """
        sources = list(sources)
        if self.num_samples:
            return self._sample(sources)
        return self._enumerate(sources)

    def _sample(self, sources):
        # Monte-Carlo sampling, one realization per draw.  The branch sets
        # are walked in document order so applyToBranches filtering sees the
        # branch IDs chosen for the same draw.  Following the engine
        # convention, early_* weights are homogeneous (1/num_samples) and
        # late_* weights are the product of the sampled branch weights.
        realizations = []
        n_bsets = len(self.branchsets)
        for i, (source_id, style) in enumerate(sources):
            probs = lt.random((self.num_samples, n_bsets), self.seed + i,
                              self.sampling_method)
            for s in range(self.num_samples):
                selections = {}
                chosen_ids = set()
                late_weight = 1.0
                for b, bs in enumerate(self.branchsets):
                    if not self._applies(bs, source_id, style, chosen_ids):
                        continue
                    [br] = lt.sample(bs.branches, [float(probs[s, b])],
                                     self.sampling_method)
                    slot, choice = _choice(
                        bs.uncertainty_type, br.branch_id, br.value, br.weight)
                    selections[slot] = choice
                    chosen_ids.add(br.branch_id)
                    late_weight *= br.weight
                if self.sampling_method.startswith('early'):
                    weight = 1.0 / self.num_samples
                else:
                    weight = late_weight
                realizations.append(PFDBranch(
                    source_id, style, weight, selections))
        return realizations

    def _enumerate(self, sources):
        realizations = []
        for source_id, style in sources:
            partials = [({}, set(), 1.0)]
            for bs in self.branchsets:
                nxt = []
                for selections, chosen_ids, weight in partials:
                    if not self._applies(bs, source_id, style, chosen_ids):
                        nxt.append((selections, chosen_ids, weight))
                        continue
                    for br in bs.branches:
                        slot, choice = _choice(
                            bs.uncertainty_type, br.branch_id, br.value,
                            br.weight)
                        new_sel = dict(selections)
                        new_sel[slot] = choice
                        nxt.append((new_sel, chosen_ids | {br.branch_id},
                                    weight * br.weight))
                partials = nxt
            for selections, _ids, weight in partials:
                realizations.append(PFDBranch(
                    source_id, style, weight, selections))
        return realizations

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
            raise lt.LogicTreeError(
                None, self.filename,
                'r_sigma_km is set both as a scalar [calculation] parameter '
                'and as an fdhaCalcRSigma logic-tree branch; remove one of '
                'the two')