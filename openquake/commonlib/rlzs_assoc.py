# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2019 GEM Foundation
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
import re
import logging
import operator
import collections
import numpy
from openquake.hazardlib import probability_map

MAX_INT = 2 ** 31 - 1
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
weight = operator.attrgetter('weight')
rlz_dt = numpy.dtype([
    ('branch_path', 'S200'), ('gsims', 'S100'), ('weight', F32)])


class LtRealization(object):
    """
    Composite realization build on top of a source model realization and
    a GSIM realization.
    """
    def __init__(self, ordinal, sm_lt_path, gsim_rlz, weight):
        self.ordinal = ordinal
        self.sm_lt_path = tuple(sm_lt_path)
        self.gsim_rlz = gsim_rlz
        self.weight = weight

    def __repr__(self):
        return '<%d,%s,w=%s>' % (self.ordinal, self.uid, self.weight)

    @property
    def gsim_lt_path(self):
        return self.gsim_rlz.lt_path

    @property
    def uid(self):
        """An unique identifier for effective realizations"""
        return '_'.join(self.sm_lt_path) + '~' + self.gsim_rlz.uid

    def __lt__(self, other):
        return self.ordinal < other.ordinal

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __ne__(self, other):
        return repr(self) != repr(other)

    def __hash__(self):
        return hash(repr(self))


class RlzsAssoc(object):
    """
    Realization association class. It should not be instantiated directly,
    but only via the method :meth:
    `openquake.commonlib.source.CompositeSourceModel.get_rlzs_assoc`.

    :attr realizations: list of :class:`LtRealization` objects
    :attr gsim_by_trt: list of dictionaries {trt: gsim}
    :attr rlzs_assoc: dictionary {src_group_id, gsim: rlzs}
    :attr rlzs_by_smodel: list of lists of realizations

    For instance, for the non-trivial logic tree in
    :mod:`openquake.qa_tests_data.classical.case_15`, which has 4 tectonic
    region types and 4 + 2 + 2 realizations, there are the following
    associations:

    (0, 'BooreAtkinson2008()') ['#0-SM1-BA2008_C2003', '#1-SM1-BA2008_T2002']
    (0, 'CampbellBozorgnia2008()') ['#2-SM1-CB2008_C2003', '#3-SM1-CB2008_T2002']
    (1, 'Campbell2003()') ['#0-SM1-BA2008_C2003', '#2-SM1-CB2008_C2003']
    (1, 'ToroEtAl2002()') ['#1-SM1-BA2008_T2002', '#3-SM1-CB2008_T2002']
    (2, 'BooreAtkinson2008()') ['#4-SM2_a3pt2b0pt8-BA2008']
    (2, 'CampbellBozorgnia2008()') ['#5-SM2_a3pt2b0pt8-CB2008']
    (3, 'BooreAtkinson2008()') ['#6-SM2_a3b1-BA2008']
    (3, 'CampbellBozorgnia2008()') ['#7-SM2_a3b1-CB2008']
    """
    def __init__(self, csm_info):
        self.seed = csm_info.seed
        self.csm_info = csm_info
        self.num_samples = csm_info.num_samples
        self.gsim_by_trt = []  # rlz.ordinal -> {trt: gsim}
        self.rlzs_by_smodel = {sm.ordinal: [] for sm in csm_info.source_models}

    def get_rlzs_by_gsim(self, trt_or_grp_id, sm_id=None):
        """
        :param trt_or_grp_id: a tectonic region type or a source group ID
        :param sm_id: source model ordinal (or None)
        :returns: a dictionary gsim -> rlzs
        """
        if isinstance(trt_or_grp_id, (int, U16, U32)):  # grp_id
            trt = self.csm_info.trt_by_grp[trt_or_grp_id]
            sm_id = self.csm_info.get_sm_by_grp()[trt_or_grp_id]
        else:  # assume TRT string
            trt = trt_or_grp_id
        acc = collections.defaultdict(list)
        if sm_id is None:  # full dictionary
            for rlz, gsim_by_trt in zip(self.realizations, self.gsim_by_trt):
                acc[gsim_by_trt[trt]].append(rlz.ordinal)
        else:  # dictionary for the selected source model
            for rlz in self.rlzs_by_smodel[sm_id]:
                gsim_by_trt = self.gsim_by_trt[rlz.ordinal]
                try:  # if there is a single TRT
                    [gsim] = gsim_by_trt.values()
                except ValueError:  # there is more than 1 TRT
                    gsim = gsim_by_trt[trt]
                acc[gsim].append(rlz.ordinal)
        return {gsim: numpy.array(acc[gsim], dtype=U16)
                for gsim in sorted(acc)}

    def by_grp(self):
        """
        :returns: a dictionary grp -> rlzis
        """
        dic = {}  # grp -> [(gsim_idx, rlzis), ...]
        for sm in self.csm_info.source_models:
            for sg in sm.src_groups:
                if not sg.eff_ruptures:
                    continue
                rlzs_by_gsim = self.get_rlzs_by_gsim(sg.trt, sm.ordinal)
                if not rlzs_by_gsim:
                    continue
                dic['grp-%02d' % sg.id] = numpy.array(
                    list(rlzs_by_gsim.values()))
        return dic

    def _init(self):
        """
        Finalize the initialization of the RlzsAssoc object by setting
        the (reduced) weights of the realizations.
        """
        if self.num_samples:
            assert len(self.realizations) == self.num_samples, (
                len(self.realizations), self.num_samples)
            for rlz in self.realizations:
                for k in rlz.weight.dic:
                    rlz.weight.dic[k] = 1. / self.num_samples
        else:
            tot_weight = sum(rlz.weight for rlz in self.realizations)
            if not tot_weight.is_one():
                # this may happen for rounding errors or because of the
                # logic tree reduction; we ensure the sum of the weights is 1
                for rlz in self.realizations:
                    rlz.weight = rlz.weight / tot_weight

    @property
    def realizations(self):
        """Flat list with all the realizations"""
        return sum(self.rlzs_by_smodel.values(), [])

    @property
    def weights(self):
        """Array with the weight of the realizations"""
        return numpy.array([rlz.weight for rlz in self.realizations])

    def combine_pmaps(self, pmap_by_grp):
        """
        :param pmap_by_grp: dictionary group string -> probability map
        :returns: a list of probability maps, one per realization
        """
        grp = list(pmap_by_grp)[0]  # pmap_by_grp must be non-empty
        num_levels = pmap_by_grp[grp].shape_y
        pmaps = [probability_map.ProbabilityMap(num_levels, 1)
                 for _ in self.realizations]
        array = self.by_grp()
        for grp in pmap_by_grp:
            for gsim_idx, rlzis in enumerate(array[grp]):
                pmap = pmap_by_grp[grp].extract(gsim_idx)
                for rlzi in rlzis:
                    pmaps[rlzi] |= pmap
        return pmaps

    def get_rlz(self, rlzstr):
        r"""
        Get a Realization instance for a string of the form 'rlz-\d+'
        """
        mo = re.match(r'rlz-(\d+)', rlzstr)
        if not mo:
            return
        return self.realizations[int(mo.group(1))]

    def _add_realizations(self, offset, lt_model, all_trts, gsim_rlzs):
        idx = numpy.arange(offset, offset + len(gsim_rlzs))
        rlzs = []
        for i, gsim_rlz in enumerate(gsim_rlzs):
            weight = float(lt_model.weight) * gsim_rlz.weight
            rlz = LtRealization(idx[i], lt_model.path, gsim_rlz, weight)
            self.gsim_by_trt.append(dict(zip(all_trts, gsim_rlz.value)))
            rlzs.append(rlz)
        self.rlzs_by_smodel[lt_model.ordinal] = rlzs

    def __repr__(self):
        pairs = []
        dic = {grp.id: self.get_rlzs_by_gsim(grp.id)
               for sm in self.csm_info.source_models
               for grp in sm.src_groups if grp.eff_ruptures}
        size = 0
        for grp_id, rlzs_by_gsim in dic.items():
            for gsim, rlzs in rlzs_by_gsim.items():
                size += 1
                if len(rlzs) > 10:  # short representation
                    rlzs = ['%d realizations' % len(rlzs)]
                pairs.append(('%s,%r' % (grp_id, repr(gsim)), rlzs))
        return '<%s(size=%d, rlzs=%d)\n%s>' % (
            self.__class__.__name__, size, len(self.realizations),
            '\n'.join('%s: %s' % pair for pair in pairs))


def accept_path(path, ref_path):
    """
    :param path: a logic tree path (list or tuple of strings)
    :param ref_path: reference logic tree path
    :returns: True if `path` is consistent with `ref_path`, False otherwise

    >>> accept_path(['SM2'], ('SM2', 'a3b1'))
    False
    >>> accept_path(['SM2', '@'], ('SM2', 'a3b1'))
    True
    >>> accept_path(['@', 'a3b1'], ('SM2', 'a3b1'))
    True
    >>> accept_path('@@', ('SM2', 'a3b1'))
    True
    """
    if len(path) != len(ref_path):
        return False
    for a, b in zip(path, ref_path):
        if a != '@' and a != b:
            return False
    return True


def get_rlzs_assoc(cinfo, sm_lt_path=None, trts=None):
    """
    :param cinfo: a :class:`openquake.commonlib.source.CompositionInfo`
    :param sm_lt_path: logic tree path tuple used to select a source model
    :param trts: tectonic region types to accept
    """
    assoc = RlzsAssoc(cinfo)
    offset = 0
    trtset = set(cinfo.gsim_lt.values)
    for smodel in cinfo.source_models:
        # discard source models with non-acceptable lt_path
        if sm_lt_path and not accept_path(smodel.path, sm_lt_path):
            continue

        # collect the effective tectonic region types and ruptures
        trts_ = set()
        for sg in smodel.src_groups:
            if sg.eff_ruptures:
                if (trts and sg.trt in trts) or not trts:
                    trts_.add(sg.trt)

        # recompute the GSIM logic tree if needed
        if trts_ != {'*'} and trtset != trts_:
            before = cinfo.gsim_lt.get_num_paths()
            gsim_lt = cinfo.gsim_lt.reduce(trts_)
            after = gsim_lt.get_num_paths()
            if sm_lt_path and before > after:
                # print the warning only when saving the logic tree,
                # i.e. when called with sm_lt_path in store_rlz_info
                logging.warning('Reducing the logic tree of %s from %d to %d '
                                'realizations', smodel.name, before, after)
            gsim_rlzs = list(gsim_lt)
            all_trts = list(gsim_lt.values)
        else:
            gsim_rlzs = list(cinfo.gsim_lt)
            all_trts = list(cinfo.gsim_lt.values)

        rlzs = cinfo._get_rlzs(smodel, gsim_rlzs, cinfo.seed + offset)
        assoc._add_realizations(offset, smodel, all_trts, rlzs)
        offset += len(rlzs)

    if assoc.realizations:
        assoc._init()
    return assoc
