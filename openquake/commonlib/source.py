# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2017 GEM Foundation
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

from __future__ import division
import os
import re
import copy
import math
import logging
import operator
import collections
import numpy

from openquake.baselib import hdf5, node
from openquake.baselib.python3compat import decode
from openquake.baselib.general import (
    groupby, group_array, block_splitter, writetmp, AccumDict)
from openquake.hazardlib import (
    nrml, sourceconverter, InvalidFile, probability_map, stats)
from openquake.commonlib import logictree


MINWEIGHT = sourceconverter.MINWEIGHT
MAXWEIGHT = 4E6  # heuristic, set by M. Simionato
MAX_INT = 2 ** 31 - 1
TWO16 = 2 ** 16
U16 = numpy.uint16
U32 = numpy.uint32
I32 = numpy.int32
F32 = numpy.float32
weight = operator.attrgetter('weight')


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


def capitalize(words):
    """
    Capitalize words separated by spaces.
    """
    return ' '.join(w.capitalize() for w in decode(words).split(' '))


def _assert_equal_sources(nodes):
    if hasattr(nodes[0], 'source_id'):
        n0 = nodes[0]
        for n in nodes[1:]:
            n.assert_equal(n0, ignore=('id', 'src_group_id'))
    else:  # assume source nodes
        n0 = nodes[0].to_str()
        for n in nodes[1:]:
            eq = n.to_str() == n0
            if not eq:
                f0 = writetmp(n0)
                f1 = writetmp(n.to_str())
            assert eq, 'different parameters for source %s, run meld %s %s' % (
                n['id'], f0, f1)
    return nodes


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
        if isinstance(trt_or_grp_id, (int, U32)):  # grp_id
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
        return collections.OrderedDict(
            (gsim, numpy.array(acc[gsim], dtype=U16)) for gsim in sorted(acc))

    def by_grp(self):
        """
        :returns: a dictionary grp -> [(gsim_idx, rlzis), ...]
        """
        dic = {}  # grp -> [(gsim_idx, rlzis), ...]
        for sm in self.csm_info.source_models:
            for sg in sm.src_groups:
                if not sg.eff_ruptures:
                    continue
                rlzs_by_gsim = self.get_rlzs_by_gsim(sg.trt, sm.ordinal)
                if not rlzs_by_gsim:
                    continue
                dic['grp-%02d' % sg.id] = [
                    (gsim_idx, rlzs_by_gsim[gsim])
                    for gsim_idx, gsim in enumerate(rlzs_by_gsim)]
        return dic

    def _init(self):
        """
        Finalize the initialization of the RlzsAssoc object by setting
        the (reduced) weights of the realizations.
        """
        if self.num_samples:
            assert len(self.realizations) == self.num_samples, (
                len(self.realizations), self.num_samples)
            tot_weight = sum(rlz.weight for rlz in self.realizations)
            for rlz in self.realizations:
                rlz.weight /= tot_weight
        else:
            tot_weight = sum(rlz.weight for rlz in self.realizations)
            if tot_weight == 0:
                raise ValueError('All realizations have zero weight??')
            elif abs(tot_weight - 1) > 1E-8:
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
            for gsim_idx, rlzis in array[grp]:
                pmap = pmap_by_grp[grp].extract(gsim_idx)
                for rlzi in rlzis:
                    pmaps[rlzi] |= pmap
        return pmaps

    def compute_pmap_stats(self, pmap_by_grp, statfuncs):
        """
        :param pmap_by_grp: dictionary group string -> probability map
        :param statfuncs: a list of statistical functions
        :returns: a probability map containing all statistics
        """
        pmaps = self.combine_pmaps(pmap_by_grp)
        return stats.compute_pmap_stats(pmaps, statfuncs, self.weights)

    def get_rlz(self, rlzstr):
        """
        Get a Realization instance for a string of the form 'rlz-\d+'
        """
        mo = re.match('rlz-(\d+)', rlzstr)
        if not mo:
            return
        return self.realizations[int(mo.group(1))]

    def _add_realizations(self, offset, lt_model, all_trts, gsim_rlzs):
        idx = numpy.arange(offset, offset + len(gsim_rlzs))
        rlzs = []
        for i, gsim_rlz in enumerate(gsim_rlzs):
            weight = float(lt_model.weight) * float(gsim_rlz.weight)
            rlz = LtRealization(idx[i], lt_model.path, gsim_rlz, weight)
            self.gsim_by_trt.append(dict(zip(all_trts, gsim_rlz.value)))
            rlzs.append(rlz)
        self.rlzs_by_smodel[lt_model.ordinal] = rlzs

    def __len__(self):
        array = self.by_grp()  # TODO: remove this
        return sum(len(array[grp]) for grp in array)

    def __repr__(self):
        pairs = []
        dic = self.by_grp()
        for grp in sorted(dic):
            grp_id = int(grp[4:])
            gsims = self.csm_info.get_gsims(grp_id)
            for gsim_idx, rlzis in dic[grp]:
                if len(rlzis) > 10:  # short representation
                    rlzis = ['%d realizations' % len(rlzis)]
                pairs.append(('%s,%s' % (grp_id, gsims[gsim_idx]), rlzis))
        return '<%s(size=%d, rlzs=%d)\n%s>' % (
            self.__class__.__name__, len(self), len(self.realizations),
            '\n'.join('%s: %s' % pair for pair in pairs))


LENGTH = 256

source_model_dt = numpy.dtype([
    ('name', hdf5.vstr),
    ('weight', F32),
    ('path', hdf5.vstr),
    ('num_rlzs', U32),
    ('samples', U32),
])

src_group_dt = numpy.dtype(
    [('grp_id', U32),
     ('trti', U16),
     ('effrup', I32),
     ('sm_id', U32)])


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


class CompositionInfo(object):
    """
    An object to collect information about the composition of
    a composite source model.

    :param source_model_lt: a SourceModelLogicTree object
    :param source_models: a list of SourceModel instances
    """
    @classmethod
    def fake(cls, gsimlt=None):
        """
        :returns:
            a fake `CompositionInfo` instance with the given gsim logic tree
            object; if None, builds automatically a fake gsim logic tree
        """
        weight = 1
        gsim_lt = gsimlt or logictree.GsimLogicTree.from_('FromFile')
        fakeSM = logictree.SourceModel(
            'fake', weight,  'b1',
            [sourceconverter.SourceGroup('*', eff_ruptures=1)],
            gsim_lt.get_num_paths(), ordinal=0, samples=1)
        return cls(gsim_lt, seed=0, num_samples=0, source_models=[fakeSM],
                   tot_weight=0)

    def __init__(self, gsim_lt, seed, num_samples, source_models, tot_weight):
        self.gsim_lt = gsim_lt
        self.seed = seed
        self.num_samples = num_samples
        self.source_models = source_models
        self.tot_weight = tot_weight
        self.init()

    def init(self):
        self.trt_by_grp = self.grp_trt()
        if self.num_samples:
            self.seed_samples_by_grp = {}
            seed = self.seed
            for sm in self.source_models:
                for grp in sm.src_groups:
                    self.seed_samples_by_grp[grp.id] = seed, sm.samples
                seed += sm.samples

    @property
    def gsim_rlzs(self):
        """
        Build and cache the gsim logic tree realizations
        """
        try:
            return self._gsim_rlzs
        except AttributeError:
            self._gsim_rlzs = list(self.gsim_lt)
            return self._gsim_rlzs

    def get_gsims(self, grp_id):
        """
        Get the GSIMs associated with the given group
        """
        trt = self.trt_by_grp[grp_id]
        if self.num_samples:  # sampling
            seed, samples = self.seed_samples_by_grp[grp_id]
            numpy.random.seed(seed)
            idxs = numpy.random.choice(len(self.gsim_rlzs), samples)
            rlzs = [self.gsim_rlzs[i] for i in idxs]
        else:  # full enumeration
            rlzs = None
        return self.gsim_lt.get_gsims(trt, rlzs)

    def get_info(self, sm_id):
        """
        Extract a CompositionInfo instance containing the single
        model of index `sm_id`.
        """
        sm = self.source_models[sm_id]
        num_samples = sm.samples if self.num_samples else 0
        return self.__class__(
            self.gsim_lt, self.seed, num_samples, [sm], self.tot_weight)

    def get_samples_by_grp(self):
        """
        :returns: a dictionary src_group_id -> source_model.samples
        """
        return {sg.id: sm.samples for sm in self.source_models
                for sg in sm.src_groups}

    def __getnewargs__(self):
        # with this CompositionInfo instances will be unpickled correctly
        return self.seed, self.num_samples, self.source_models

    def __toh5__(self):
        trts = sorted(set(src_group.trt for sm in self.source_models
                          for src_group in sm.src_groups))
        trti = {trt: i for i, trt in enumerate(trts)}
        data = []
        for sm in self.source_models:
            for src_group in sm.src_groups:
                # the number of effective realizations is set by get_rlzs_assoc
                data.append((src_group.id, trti[src_group.trt],
                             src_group.eff_ruptures, sm.ordinal))
        lst = [(sm.name, sm.weight, '_'.join(sm.path),
                sm.num_gsim_paths, sm.samples)
               for i, sm in enumerate(self.source_models)]
        return (dict(
            sg_data=numpy.array(data, src_group_dt),
            sm_data=numpy.array(lst, source_model_dt)),
                dict(seed=self.seed, num_samples=self.num_samples,
                     trts=hdf5.array_of_vstr(trts),
                     gsim_lt_xml=str(self.gsim_lt),
                     gsim_fname=self.gsim_lt.fname,
                     tot_weight=self.tot_weight))

    def __fromh5__(self, dic, attrs):
        # TODO: this is called more times than needed, maybe we should cache it
        sg_data = group_array(dic['sg_data'], 'sm_id')
        sm_data = dic['sm_data']
        vars(self).update(attrs)
        self.gsim_fname = decode(self.gsim_fname)
        if self.gsim_fname.endswith('.xml'):
            trts = sorted(self.trts)
            if 'gmpe_table' in self.gsim_lt_xml:
                # the canadian gsims depends on external files which are not
                # in the datastore; I am storing the path to the original
                # file so that the external files can be found; unfortunately,
                # this means that copying the datastore on a different machine
                # and exporting from there works only if the gsim_fname and all
                # the external files are copied in the exact same place
                self.gsim_lt = logictree.GsimLogicTree(self.gsim_fname, trts)
            else:
                # regular case: read the logic tree from self.gsim_lt_xml,
                # so that you do not need to copy anything except the datastore
                tmp = writetmp(self.gsim_lt_xml, suffix='.xml')
                self.gsim_lt = logictree.GsimLogicTree(tmp, trts)
        else:  # fake file with the name of the GSIM
            self.gsim_lt = logictree.GsimLogicTree.from_(self.gsim_fname)
        self.source_models = []
        for sm_id, rec in enumerate(sm_data):
            tdata = sg_data[sm_id]
            srcgroups = [
                sourceconverter.SourceGroup(
                    self.trts[trti], id=grp_id, eff_ruptures=effrup)
                for grp_id, trti, effrup, sm_id in tdata if effrup]
            path = tuple(str(decode(rec['path'])).split('_'))
            trts = set(sg.trt for sg in srcgroups)
            num_gsim_paths = self.gsim_lt.reduce(trts).get_num_paths()
            sm = logictree.SourceModel(
                rec['name'], rec['weight'], path, srcgroups,
                num_gsim_paths, sm_id, rec['samples'])
            self.source_models.append(sm)
        self.init()
        try:
            os.remove(tmp)  # gsim_lt file
        except NameError:  # tmp is defined only in the regular case, see above
            pass

    def get_num_rlzs(self, source_model=None):
        """
        :param source_model: a SourceModel instance (or None)
        :returns: the number of realizations per source model (or all)
        """
        if source_model is None:
            return sum(self.get_num_rlzs(sm) for sm in self.source_models)
        if self.num_samples:
            return source_model.samples
        trts = set(sg.trt for sg in source_model.src_groups)
        return self.gsim_lt.reduce(trts).get_num_paths()

    def get_rlzs_assoc(self, count_ruptures=None,
                       sm_lt_path=None, trts=None):
        """
        :param count_ruptures: function src_group_id -> num_ruptures
        :param sm_lt_path: logic tree path tuple used to select a source model
        :param gsim_lt_path: gsim logic tree path tuple
        :param trts: tectonic region types to accept
        """
        assoc = RlzsAssoc(self)
        offset = 0
        trtset = set(self.gsim_lt.tectonic_region_types)
        for smodel in self.source_models:
            # discard source models with non-acceptable lt_path
            if sm_lt_path and not accept_path(smodel.path, sm_lt_path):
                continue

            # collect the effective tectonic region types and ruptures
            trts_ = set()
            for sg in smodel.src_groups:
                if count_ruptures:
                    sg.eff_ruptures = count_ruptures(sg.id)
                if sg.eff_ruptures:
                    if (trts and sg.trt in trts) or not trts:
                        trts_.add(sg.trt)

            # recompute the GSIM logic tree if needed
            if trtset != trts_:
                before = self.gsim_lt.get_num_paths()
                gsim_lt = self.gsim_lt.reduce(trts_)
                after = gsim_lt.get_num_paths()
                if count_ruptures and before > after:
                    logging.warn('Reducing the logic tree of %s from %d to %d '
                                 'realizations', smodel.name, before, after)
                gsim_rlzs = list(gsim_lt)
                all_trts = gsim_lt.all_trts
            else:
                gsim_rlzs = self.gsim_rlzs
                all_trts = self.gsim_lt.all_trts

            rlzs = self._get_rlzs(smodel, gsim_rlzs, self.seed + offset)
            assoc._add_realizations(offset, smodel, all_trts, rlzs)
            offset += len(rlzs)

        if assoc.realizations:
            assoc._init()
        return assoc

    def get_source_model(self, src_group_id):
        """
        Return the source model for the given src_group_id
        """
        for smodel in self.source_models:
            for src_group in smodel.src_groups:
                if src_group.id == src_group_id:
                    return smodel

    def get_grp_ids(self, sm_id):
        """
        :returns: a list of source group IDs for the given source model ID
        """
        return [sg.id for sg in self.source_models[sm_id].src_groups]

    def get_sm_by_rlz(self, realizations):
        """
        :returns: a dictionary rlz -> source model name
        """
        dic = {}
        for sm in self.source_models:
            for rlz in realizations:
                if rlz.sm_lt_path == sm.path:
                    dic[rlz] = sm.name
        return dic

    def get_sm_by_grp(self):
        """
        :returns: a dictionary grp_id -> sm_id
        """
        return {grp.id: sm.ordinal for sm in self.source_models
                for grp in sm.src_groups}

    def grp_trt(self):
        """
        :returns: a dictionary grp_id -> TRT string
        """
        dic = {}
        for smodel in self.source_models:
            for src_group in smodel.src_groups:
                dic[src_group.id] = src_group.trt
        return dic

    def _get_rlzs(self, smodel, all_rlzs, seed):
        if self.num_samples:
            # NB: the weights are considered when combining the results, not
            # when sampling, therefore there are no weights in the function
            # numpy.random.choice below
            numpy.random.seed(seed)
            idxs = numpy.random.choice(len(all_rlzs), smodel.samples)
            rlzs = [all_rlzs[idx] for idx in idxs]
        else:  # full enumeration
            rlzs = logictree.get_effective_rlzs(all_rlzs)
        if len(rlzs) > TWO16:
            raise ValueError(
                'The source model %s has %d realizations, the maximum '
                'is %d' % (smodel.name, len(rlzs), TWO16))
        return rlzs

    def __repr__(self):
        info_by_model = collections.OrderedDict()
        for sm in self.source_models:
            info_by_model[sm.path] = (
                '_'.join(map(decode, sm.path)),
                decode(sm.name),
                [sg.id for sg in sm.src_groups],
                sm.weight,
                self.get_num_rlzs(sm))
        summary = ['%s, %s, grp=%s, weight=%s: %d realization(s)' % ibm
                   for ibm in info_by_model.values()]
        return '<%s\n%s>' % (
            self.__class__.__name__, '\n'.join(summary))


class CompositeSourceModel(collections.Sequence):
    """
    :param source_model_lt:
        a :class:`openquake.commonlib.logictree.SourceModelLogicTree` instance
    :param source_models:
        a list of :class:`openquake.hazardlib.sourceconverter.SourceModel`
        tuples
    """
    def __init__(self, gsim_lt, source_model_lt, source_models):
        self.gsim_lt = gsim_lt
        self.source_model_lt = source_model_lt
        self.source_models = source_models
        self.source_info = ()
        self.split_map = {}
        self.weight = 0
        self.info = CompositionInfo(
            gsim_lt, self.source_model_lt.seed,
            self.source_model_lt.num_samples,
            [sm.get_skeleton() for sm in self.source_models],
            self.weight)
        # dictionary src_group_id, source_id -> SourceInfo,
        # populated by the .split_in_blocks method
        self.infos = {}
        try:
            dupl_sources = self.check_dupl_sources()
        except AssertionError:
            # different sources with the same ID
            self.has_dupl_sources = 0
        else:
            self.has_dupl_sources = len(dupl_sources)

    def get_model(self, sm_id):
        """
        Extract a CompositeSourceModel instance containing the single
        model of index `sm_id`.
        """
        sm = self.source_models[sm_id]
        if self.source_model_lt.num_samples:
            self.source_model_lt.num_samples = sm.samples
        new = self.__class__(self.gsim_lt, self.source_model_lt, [sm])
        new.sm_id = sm_id
        new.weight = sum(src.weight for sg in sm.src_groups
                         for src in sg.sources)
        return new

    def filter(self, src_filter):
        """
        Generate a new CompositeSourceModel by filtering the sources on
        the given site collection.

        :param sitecol: a SiteCollection instance
        :para src_filter: a SourceFilter instance
        """
        source_models = []
        weight = 0
        for sm in self.source_models:
            src_groups = []
            for src_group in sm.src_groups:
                sources = []
                for src in src_group.sources:
                    if hasattr(src, '__iter__'):  # MultiPointSource
                        sources.extend(src)
                    else:
                        sources.append(src)
                sg = copy.copy(src_group)
                sg.sources = []
                for src, sites in src_filter(sources):
                    sg.sources.append(src)
                    weight += src.weight
                src_groups.append(sg)
            newsm = logictree.SourceModel(
                sm.name, sm.weight, sm.path, src_groups,
                sm.num_gsim_paths, sm.ordinal, sm.samples)
            source_models.append(newsm)
        new = self.__class__(self.gsim_lt, self.source_model_lt, source_models)
        new.weight = weight
        new.src_filter = src_filter
        return new

    @property
    def src_groups(self):
        """
        Yields the SourceGroups inside each source model.
        """
        for sm in self.source_models:
            for src_group in sm.src_groups:
                yield src_group

    def check_dupl_sources(self):  # used in print_csm_info
        """
        Extracts duplicated sources, i.e. sources with the same source_id in
        different source groups. Raise an exception if there are sources with
        the same ID which are not duplicated.

        :returns: a list of list of sources, ordered by source_id
        """
        dd = collections.defaultdict(list)
        for src_group in self.src_groups:
            for src in src_group:
                try:
                    srcid = src.source_id
                except AttributeError:  # src is a Node object
                    srcid = src['id']
                dd[srcid].append(src)
        return [_assert_equal_sources(srcs)
                for srcid, srcs in sorted(dd.items()) if len(srcs) > 1]

    def gen_mutex_groups(self):
        """
        Yield groups of mutually exclusive sources
        """
        for sg in self.src_groups:
            if sg.src_interdep == 'mutex':
                yield sg

    def get_sources(self, kind='all', maxweight=None):
        """
        Extract the sources contained in the source models by optionally
        filtering and splitting them, depending on the passed parameters.
        """
        if kind != 'all':
            assert kind in ('light', 'heavy') and maxweight is not None, (
                kind, maxweight)
        sources = []
        for src_group in self.src_groups:
            if src_group.src_interdep == 'indep':
                for src in src_group:
                    if kind == 'all':
                        sources.append(src)
                    elif kind == 'light' and src.weight <= maxweight:
                        sources.append(src)
                    elif kind == 'heavy' and src.weight > maxweight:
                        sources.append(src)
        return sources

    def get_sources_by_trt(self, optimize_same_id_sources=False):
        """
        Build a dictionary TRT string -> sources. Sources of kind "mutex"
        (if any) are silently discarded.
        """
        acc = AccumDict(accum=[])
        for sm in self.source_models:
            for grp in sm.src_groups:
                if grp.src_interdep != 'mutex':
                    acc[grp.trt].extend(grp)
        if optimize_same_id_sources is False:
            return acc
        # extract a single source from multiple sources with the same ID
        dic = {}
        weight = 0
        for trt in acc:
            dic[trt] = []
            for grp in groupby(acc[trt], lambda x: x.source_id).values():
                src = grp[0]
                weight += src.weight
                if len(grp) > 1 and not isinstance(src.src_group_id, list):
                    # src.src_group_id could be a list because grouped in a
                    # previous step (this may happen in presence of tiles)
                    src.src_group_id = [s.src_group_id for s in grp]
                dic[trt].append(src)
        self.weight = weight
        return dic

    def get_num_sources(self):
        """
        :returns: the total number of sources in the model
        """
        return sum(len(src_group) for src_group in self.src_groups)

    def init_serials(self):
        """
        Generate unique seeds for each rupture with numpy.arange.
        This should be called only in event based calculators
        """
        n = sum(sg.tot_ruptures() for sg in self.src_groups)
        rup_serial = numpy.arange(n, dtype=numpy.uint32)
        start = 0
        for sg in self.src_groups:
            for src in sg:
                nr = src.num_ruptures
                src.serial = rup_serial[start:start + nr]
                start += nr

    def get_maxweight(self, concurrent_tasks):
        """
        Return an appropriate maxweight for use in the block_splitter
        """
        ct = concurrent_tasks or 1
        mw = math.ceil(self.weight / ct)
        if mw < MINWEIGHT:
            mw = MINWEIGHT
        elif mw > MAXWEIGHT:
            mw = MAXWEIGHT
        return mw

    def add_infos(self, sources):
        """
        Populate the .infos dictionary (grp_id, src_id) -> <SourceInfo>
        """
        for src in sources:
            for grp_id in src.src_group_ids:
                self.infos[grp_id, src.source_id] = SourceInfo(src)

    def split_in_blocks(self, maxweight, sources):
        """
        Split a set of sources in blocks of weight up to maxweight; heavy
        sources (i.e. with weight > maxweight) are split.

        :param maxweight: maximum weight of a block
        :param sources: sources of the same source group
        :yields: blocks of sources of weight around maxweight
        """
        sources.sort(key=weight)

        # yield light sources in blocks
        light = [src for src in sources if src.weight <= maxweight]
        for block in block_splitter(light, maxweight, weight):
            yield block

        # yield heavy sources in blocks
        heavy = [src for src in sources if src.weight > maxweight]
        for src in heavy:
            srcs = [s for s in split_source(src)
                    if self.src_filter.get_close_sites(s) is not None]
            for block in block_splitter(srcs, maxweight, weight):
                yield block

    def __repr__(self):
        """
        Return a string representation of the composite model
        """
        models = ['%d-%s-%s,w=%s [%d src_group(s)]' % (
            sm.ordinal, sm.name, '_'.join(sm.path), sm.weight,
            len(sm.src_groups)) for sm in self.source_models]
        return '<%s\n%s>' % (self.__class__.__name__, '\n'.join(models))

    def __getitem__(self, i):
        """Return the i-th source model"""
        return self.source_models[i]

    def __iter__(self):
        """Return an iterator over the underlying source models"""
        return iter(self.source_models)

    def __len__(self):
        """Return the number of underlying source models"""
        return len(self.source_models)


split_map = {}  # src -> split sources


def split_source(src):
    """
    :param src: a source to split
    :returns: a list of split sources
    """
    has_serial = hasattr(src, 'serial')
    start = 0
    try:
        splits = split_map[src]  # read from the cache
    except KeyError:  # fill the cache
        splits = split_map[src] = list(sourceconverter.split_source(src))
        if len(splits) > 1:
            logging.debug(
                'Splitting %s "%s" in %d sources', src.__class__.__name__,
                src.source_id, len(splits))
    for split in splits:
        if has_serial:
            nr = split.num_ruptures
            split.serial = src.serial[start:start + nr]
            start += nr
        yield split


def collect_source_model_paths(smlt):
    """
    Given a path to a source model logic tree or a file-like, collect all of
    the soft-linked path names to the source models it contains and return them
    as a uniquified list (no duplicates).

    :param smlt: source model logic tree file
    """
    n = nrml.read(smlt)
    try:
        blevels = n.logicTree
    except:
        raise InvalidFile('%s is not a valid source_model_logic_tree_file'
                          % smlt)
    for blevel in blevels:
        with node.context(smlt, blevel):
            for bset in blevel:
                for br in bset:
                    smfname = br.uncertaintyModel.text.strip()
                    if smfname:
                        yield smfname


# ########################## SourceManager ########################### #

class SourceInfo(object):
    dt = numpy.dtype([
        ('grp_id', numpy.uint32),          # 0
        ('source_id', (bytes, 100)),       # 1
        ('source_class', (bytes, 30)),     # 2
        ('num_ruptures', numpy.uint32),    # 3
        ('calc_time', numpy.float32),      # 4
        ('num_sites', numpy.uint32),       # 5
        ('num_split',  numpy.uint32),      # 6
    ])

    def __init__(self, src, calc_time=0, num_split=0):
        self.grp_id = src.src_group_id
        self.source_id = src.source_id
        self.source_class = src.__class__.__name__
        self.num_ruptures = src.num_ruptures
        self.num_sites = getattr(src, 'nsites', 0)
        self.calc_time = calc_time
        self.num_split = num_split
