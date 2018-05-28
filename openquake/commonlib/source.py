# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2018 GEM Foundation
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
import os
import re
import copy
import math
import time
import logging
import operator
import collections
import numpy

from openquake.baselib import performance, hdf5, node
from openquake.baselib.python3compat import decode
from openquake.baselib.general import (
    groupby, group_array, gettemp, AccumDict, random_filter)
from openquake.hazardlib import (
    nrml, source, sourceconverter, InvalidFile, probability_map, stats)
from openquake.hazardlib.gsim.gmpe_table import GMPETable
from openquake.commonlib import logictree


MINWEIGHT = source.MINWEIGHT
MAX_INT = 2 ** 31 - 1
U16 = numpy.uint16
U32 = numpy.uint32
I32 = numpy.int32
F32 = numpy.float32
weight = operator.attrgetter('weight')
rlz_dt = numpy.dtype([
    ('branch_path', 'S200'), ('gsims', 'S100'), ('weight', F32)])


def split_sources(srcs):
    """
    :param srcs: sources
    :returns: a pair (split sources, split time)
    """
    sources = []
    split_time = {}  # src_id -> dt
    for src in srcs:
        t0 = time.time()
        splits = list(src)
        split_time[src.source_id] = time.time() - t0
        sources.extend(splits)
        if len(splits) > 1:
            has_serial = hasattr(src, 'serial')
            start = 0
            for i, split in enumerate(splits):
                split.source_id = '%s:%s' % (src.source_id, i)
                split.src_group_id = src.src_group_id
                split.ngsims = src.ngsims
                if has_serial:
                    nr = split.num_ruptures
                    split.serial = src.serial[start:start + nr]
                    start += nr
    return sources, split_time


def gsim_names(rlz):
    """
    Names of the underlying GSIMs separated by spaces
    """
    return ' '.join(str(v) for v in rlz.gsim_rlz.value)


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
                f0 = gettemp(n0)
                f1 = gettemp(n.to_str())
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
     ('totrup', I32),
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


def get_totrup(data):
    """
    :param data: a record with a field `totrup`, possibily missing
    """
    try:
        totrup = data['totrup']
    except ValueError:  # engine older than 2.9
        totrup = 0
    return totrup


class CompositionInfo(object):
    """
    An object to collect information about the composition of
    a composite source model.

    :param source_model_lt: a SourceModelLogicTree object
    :param source_models: a list of LtSourceModel instances
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
        fakeSM = logictree.LtSourceModel(
            'scenario', weight,  'b1',
            [sourceconverter.SourceGroup('*', eff_ruptures=1)],
            gsim_lt.get_num_paths(), ordinal=0, samples=1)
        return cls(gsim_lt, seed=0, num_samples=0, source_models=[fakeSM],
                   totweight=0)

    def __init__(self, gsim_lt, seed, num_samples, source_models, totweight=0):
        self.gsim_lt = gsim_lt
        self.seed = seed
        self.num_samples = num_samples
        self.source_models = source_models
        self.tot_weight = totweight
        self.init()

    def init(self):
        self.trt_by_grp = self.grp_by("trt")
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

    def trt2i(self):
        """
        :returns: trt -> trti
        """
        trts = sorted(set(src_group.trt for sm in self.source_models
                          for src_group in sm.src_groups))
        return {trt: i for i, trt in enumerate(trts)}

    def __toh5__(self):
        # save csm_info/sg_data, csm_info/sm_data in the datastore
        trti = self.trt2i()
        sg_data = []
        sm_data = []
        for sm in self.source_models:
            trts = set(sg.trt for sg in sm.src_groups)
            num_gsim_paths = self.gsim_lt.reduce(trts).get_num_paths()
            sm_data.append((sm.names, sm.weight, '_'.join(sm.path),
                            num_gsim_paths, sm.samples))
            for src_group in sm.src_groups:
                sg_data.append((src_group.id, trti[src_group.trt],
                                src_group.eff_ruptures, src_group.tot_ruptures,
                                sm.ordinal))
        return (dict(
            sg_data=numpy.array(sg_data, src_group_dt),
            sm_data=numpy.array(sm_data, source_model_dt)),
                dict(seed=self.seed, num_samples=self.num_samples,
                     trts=hdf5.array_of_vstr(sorted(trti)),
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
            # otherwise it would look in the current directory
            GMPETable.GMPE_DIR = os.path.dirname(self.gsim_fname)
            trts = sorted(self.trts)
            tmp = gettemp(self.gsim_lt_xml, suffix='.xml')
            self.gsim_lt = logictree.GsimLogicTree(tmp, trts)
        else:  # fake file with the name of the GSIM
            self.gsim_lt = logictree.GsimLogicTree.from_(self.gsim_fname)
        self.source_models = []
        for sm_id, rec in enumerate(sm_data):
            tdata = sg_data[sm_id]
            srcgroups = [
                sourceconverter.SourceGroup(
                    self.trts[data['trti']], id=data['grp_id'],
                    eff_ruptures=data['effrup'], tot_ruptures=get_totrup(data))
                for data in tdata if data['effrup']]
            path = tuple(str(decode(rec['path'])).split('_'))
            trts = set(sg.trt for sg in srcgroups)
            sm = logictree.LtSourceModel(
                rec['name'], rec['weight'], path, srcgroups,
                rec['num_rlzs'], sm_id, rec['samples'])
            self.source_models.append(sm)
        self.init()
        try:
            os.remove(tmp)  # gsim_lt file
        except NameError:  # tmp is defined only in the regular case, see above
            pass

    def get_num_rlzs(self, source_model=None):
        """
        :param source_model: a LtSourceModel instance (or None)
        :returns: the number of realizations per source model (or all)
        """
        if source_model is None:
            return sum(self.get_num_rlzs(sm) for sm in self.source_models)
        if self.num_samples:
            return source_model.samples
        trts = set(sg.trt for sg in source_model.src_groups)
        return self.gsim_lt.reduce(trts).get_num_paths()

    @property
    def rlzs(self):
        """
        :returns: an array of realizations
        """
        realizations = self.get_rlzs_assoc().realizations
        return numpy.array(
            [(r.uid, gsim_names(r), r.weight) for r in realizations], rlz_dt)

    def update_eff_ruptures(self, count_ruptures):
        """
        :param count_ruptures: function or dict src_group_id -> num_ruptures
        """
        for smodel in self.source_models:
            for sg in smodel.src_groups:
                sg.eff_ruptures = (count_ruptures(sg.id)
                                   if callable(count_ruptures)
                                   else count_ruptures[sg.id])

    def get_rlzs_assoc(self, sm_lt_path=None, trts=None):
        """
        :param sm_lt_path: logic tree path tuple used to select a source model
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
                if sg.eff_ruptures:
                    if (trts and sg.trt in trts) or not trts:
                        trts_.add(sg.trt)

            # recompute the GSIM logic tree if needed
            if trtset != trts_:
                before = self.gsim_lt.get_num_paths()
                gsim_lt = self.gsim_lt.reduce(trts_)
                after = gsim_lt.get_num_paths()
                if sm_lt_path and before > after:
                    # print the warning only when saving the logic tree,
                    # i.e. when called with sm_lt_path in store_source_info
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

    def get_sm_by_grp(self):
        """
        :returns: a dictionary grp_id -> sm_id
        """
        return {grp.id: sm.ordinal for sm in self.source_models
                for grp in sm.src_groups}

    def grp_by(self, name):
        """
        :returns: a dictionary grp_id -> TRT string
        """
        dic = {}
        for smodel in self.source_models:
            for src_group in smodel.src_groups:
                dic[src_group.id] = getattr(src_group, name)
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
        return rlzs

    def __repr__(self):
        info_by_model = collections.OrderedDict()
        for sm in self.source_models:
            info_by_model[sm.path] = (
                '_'.join(map(decode, sm.path)),
                decode(sm.names),
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
    def __init__(self, gsim_lt, source_model_lt, source_models,
                 optimize_same_id):
        self.gsim_lt = gsim_lt
        self.source_model_lt = source_model_lt
        self.source_models = source_models
        self.optimize_same_id = optimize_same_id
        self.source_info = ()
        self.info = CompositionInfo(
            gsim_lt, self.source_model_lt.seed,
            self.source_model_lt.num_samples,
            [sm.get_skeleton() for sm in self.source_models])
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

    def split_all(self):
        """
        Split all sources in the composite source model.

        :param samples_factor: if given, sample the sources
        :returns: a dictionary source_id -> split_time
        """
        sample_factor = os.environ.get('OQ_SAMPLE_SOURCES')
        ngsims = {trt: len(gs) for trt, gs in self.gsim_lt.values.items()}
        split_time = AccumDict()
        for sm in self.source_models:
            for src_group in sm.src_groups:
                self.add_infos(src_group)
                for src in src_group:
                    split_time[src.source_id] = 0
                    src.ngsims = ngsims[src.tectonic_region_type]
                if getattr(src_group, 'src_interdep', None) != 'mutex':
                    # mutex sources cannot be split
                    srcs, stime = split_sources(src_group)
                    for src in src_group:
                        s = src.source_id
                        self.infos[s].split_time = stime[s]
                    if sample_factor:
                        # debugging tip to reduce the size of a calculation
                        # OQ_SAMPLE_SOURCES=.01 oq engine --run job.ini
                        # will run a computation 100 times smaller
                        srcs = random_filter(srcs, float(sample_factor))
                    src_group.sources = srcs
                    split_time += stime
        return split_time

    def grp_by_src(self):
        """
        :returns: a new CompositeSourceModel with one group per source
        """
        smodels = []
        grp_id = 0
        for sm in self.source_models:
            src_groups = []
            smodel = sm.__class__(sm.names, sm.weight, sm.path, src_groups,
                                  sm.num_gsim_paths, sm.ordinal, sm.samples)
            for sg in sm.src_groups:
                for src in sg.sources:
                    src.src_group_id = grp_id
                    src_groups.append(
                        sourceconverter.SourceGroup(
                            sg.trt, [src], name=src.source_id, id=grp_id))
                    grp_id += 1
            smodels.append(smodel)
        return self.__class__(self.gsim_lt, self.source_model_lt, smodels,
                              self.optimize_same_id)

    def get_model(self, sm_id):
        """
        Extract a CompositeSourceModel instance containing the single
        model of index `sm_id`.
        """
        sm = self.source_models[sm_id]
        if self.source_model_lt.num_samples:
            self.source_model_lt.num_samples = sm.samples
        new = self.__class__(self.gsim_lt, self.source_model_lt, [sm],
                             self.optimize_same_id)
        new.sm_id = sm_id
        return new

    def filter(self, src_filter, monitor=performance.Monitor()):
        """
        Generate a new CompositeSourceModel by filtering the sources on
        the given site collection.

        :param src_filter: a SourceFilter instance
        :param monitor: a Monitor instance
        :returns: a new CompositeSourceModel instance
        """
        sources_by_grp = src_filter.pfilter(self.get_sources(), monitor)
        source_models = []
        for sm in self.source_models:
            src_groups = []
            for src_group in sm.src_groups:
                sg = copy.copy(src_group)
                sg.sources = sources_by_grp.get(sg.id, [])
                src_groups.append(sg)
            newsm = logictree.LtSourceModel(
                sm.names, sm.weight, sm.path, src_groups,
                sm.num_gsim_paths, sm.ordinal, sm.samples)
            source_models.append(newsm)
        new = self.__class__(self.gsim_lt, self.source_model_lt, source_models,
                             self.optimize_same_id)
        return new

    def get_weight(self, weight):
        """
        :param weight: source weight function
        :returns: total weight of the source model
        """
        tot_weight = 0
        for srcs in self.get_sources_by_trt().values():
            tot_weight += sum(map(weight, srcs))
        for grp in self.gen_mutex_groups():
            tot_weight += sum(map(weight, grp))
        self.info.tot_weight = tot_weight
        return tot_weight

    @property
    def src_groups(self):
        """
        Yields the SourceGroups inside each source model.
        """
        for sm in self.source_models:
            for src_group in sm.src_groups:
                yield src_group

    def get_nonparametric_sources(self):
        """
        :returns: list of non parametric sources in the composite source model
        """
        return [src for sm in self.source_models
                for src_group in sm.src_groups
                for src in src_group if hasattr(src, 'data')]

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

    def get_sources(self, kind='all'):
        """
        Extract the sources contained in the source models by optionally
        filtering and splitting them, depending on the passed parameter.
        """
        assert kind in ('all', 'indep', 'mutex'), kind
        sources = []
        for src_group in self.src_groups:
            if kind in ('all', src_group.src_interdep):
                sources.extend(src_group)
        return sources

    def get_sources_by_trt(self):
        """
        Build a dictionary TRT string -> sources. Sources of kind "mutex"
        (if any) are silently discarded.
        """
        acc = AccumDict(accum=[])
        for sm in self.source_models:
            for grp in sm.src_groups:
                if grp.src_interdep != 'mutex':
                    acc[grp.trt].extend(grp)
        if self.optimize_same_id is False:
            return acc
        # extract a single source from multiple sources with the same ID
        dic = {}
        for trt in acc:
            dic[trt] = []
            for grp in groupby(acc[trt], lambda x: x.source_id).values():
                src = grp[0]
                # src.src_group_id can be a list if get_sources_by_trt was
                # called before
                if len(grp) > 1 and not isinstance(src.src_group_id, list):
                    src.src_group_id = [s.src_group_id for s in grp]
                dic[trt].append(src)
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
        n = sum(sg.tot_ruptures for sg in self.src_groups)
        rup_serial = numpy.arange(n, dtype=numpy.uint32)
        start = 0
        for sg in self.src_groups:
            for src in sg:
                nr = src.num_ruptures
                src.serial = rup_serial[start:start + nr]
                start += nr

    def get_maxweight(self, weight, concurrent_tasks, minweight=MINWEIGHT):
        """
        Return an appropriate maxweight for use in the block_splitter
        """
        totweight = self.get_weight(weight)
        ct = concurrent_tasks or 1
        mw = math.ceil(totweight / ct)
        return max(mw, minweight)

    def add_infos(self, sources):
        """
        Populate the .infos dictionary src_id -> <SourceInfo>
        """
        for src in sources:
            info = SourceInfo(src)
            self.infos[info.source_id] = info

    def get_floating_spinning_factors(self):
        """
        :returns: (floating rupture factor, spinning rupture factor)
        """
        data = []
        for src in self.get_sources():
            if hasattr(src, 'hypocenter_distribution'):
                data.append(
                    (len(src.hypocenter_distribution.data),
                     len(src.nodal_plane_distribution.data)))
        if not data:
            return numpy.array([1, 1])
        return numpy.array(data).mean(axis=0)

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
                    smfname = ' '.join(br.uncertaintyModel.text.split())
                    if smfname:
                        yield smfname


# ########################## SourceManager ########################### #

class SourceInfo(object):
    dt = numpy.dtype([
        ('source_id', (bytes, 100)),       # 0
        ('source_class', (bytes, 30)),     # 1
        ('num_ruptures', numpy.uint32),    # 2
        ('calc_time', numpy.float32),      # 3
        ('split_time', numpy.float32),     # 4
        ('num_sites', numpy.float32),      # 5
        ('num_split',  numpy.uint32),      # 6
        ('events', numpy.uint32),          # 7
    ])

    def __init__(self, src, calc_time=0, split_time=0, num_split=0):
        self.source_id = src.source_id.rsplit(':', 1)[0]
        self.source_class = src.__class__.__name__
        self.num_ruptures = src.num_ruptures
        self.num_sites = 0  # set later on
        self.calc_time = calc_time
        self.split_time = split_time
        self.num_split = num_split
        self.events = 0  # set in event based
