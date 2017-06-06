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
import random

import h5py
import numpy

from openquake.baselib import hdf5, node
from openquake.baselib.python3compat import decode
from openquake.baselib.general import (
    groupby, group_array, block_splitter, writetmp)
from openquake.hazardlib import nrml, sourceconverter, InvalidFile
from openquake.commonlib import logictree


MAXWEIGHT = sourceconverter.MAXWEIGHT
MAX_INT = 2 ** 31 - 1
TWO16 = 2 ** 16
U16 = numpy.uint16
U32 = numpy.uint32
I32 = numpy.int32
F32 = numpy.float32

assoc_by_grp_dt = numpy.dtype(
    [('grp_id', U16),
     ('gsim_idx', U16),
     ('rlzis', h5py.special_dtype(vlen=U16))])


class LtRealization(object):
    """
    Composite realization build on top of a source model realization and
    a GSIM realization.
    """
    def __init__(self, ordinal, sm_lt_path, gsim_rlz, weight, sampleid):
        self.ordinal = ordinal
        self.sm_lt_path = tuple(sm_lt_path)
        self.gsim_rlz = gsim_rlz
        self.weight = weight
        self.sampleid = sampleid

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


class RlzsAssoc(collections.Mapping):
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
        self.num_samples = csm_info.num_samples
        self.rlzs_assoc = collections.defaultdict(list)
        self.gsim_by_trt = []  # rlz.ordinal -> {trt: gsim}
        self.rlzs_by_smodel = {sm.ordinal: [] for sm in csm_info.source_models}
        self.gsims_by_grp_id = {}
        self.sm_ids = {}
        self.samples = {}
        for sm in csm_info.source_models:
            for sg in sm.src_groups:
                self.sm_ids[sg.id] = sm.ordinal
                self.samples[sg.id] = sm.samples

    def _init(self):
        """
        Finalize the initialization of the RlzsAssoc object by setting
        the (reduced) weights of the realizations and the attribute
        gsims_by_grp_id.
        """
        if self.num_samples:
            assert len(self.realizations) == self.num_samples, (
                len(self.realizations), self.num_samples)
            for rlz in self.realizations:
                rlz.weight = 1. / self.num_samples
        else:
            tot_weight = sum(rlz.weight for rlz in self.realizations)
            if tot_weight == 0:
                raise ValueError('All realizations have zero weight??')
            elif abs(tot_weight - 1) > 1E-8:
                # this may happen for rounding errors or because of the
                # logic tree reduction; we ensure the sum of the weights is 1
                for rlz in self.realizations:
                    rlz.weight = rlz.weight / tot_weight

        self.gsims_by_grp_id = groupby(
            self.rlzs_assoc, operator.itemgetter(0),
            lambda group: sorted(gsim for grp_id, gsim in group))

    @property
    def realizations(self):
        """Flat list with all the realizations"""
        return sum(self.rlzs_by_smodel.values(), [])

    @property
    def weights(self):
        """Array with the weight of the realizations"""
        return numpy.array([rlz.weight for rlz in self.realizations])

    def get_rlz(self, rlzstr):
        """
        Get a Realization instance for a string of the form 'rlz-\d+'
        """
        mo = re.match('rlz-(\d+)', rlzstr)
        if not mo:
            return
        return self.realizations[int(mo.group(1))]

    def get_rlzs_by_gsim(self, grp_id):
        """
        Returns an orderd dictionary gsim > rlzs for the given grp_id
        """
        rlzs_by_gsim = collections.OrderedDict()
        for gid, gsim in sorted(self.rlzs_assoc):
            if gid == grp_id:
                rlzs_by_gsim[gsim] = self[gid, gsim]
        return rlzs_by_gsim

    def get_rlzs_by_grp_id(self):
        """
        Returns a dictionary grp_id > [sorted rlzs]
        """
        rlzs_by_grp_id = collections.defaultdict(set)
        for (grp_id, gsim), rlzs in self.rlzs_assoc.items():
            rlzs_by_grp_id[grp_id].update(rlzs)
        return {grp_id: sorted(rlzs)
                for grp_id, rlzs in rlzs_by_grp_id.items()}

    def _add_realizations(self, idx, lt_model, gsim_lt, gsim_rlzs):
        trts = gsim_lt.tectonic_region_types
        rlzs = []
        for i, gsim_rlz in enumerate(gsim_rlzs):
            weight = float(lt_model.weight) * float(gsim_rlz.weight)
            rlz = LtRealization(idx[i], lt_model.path, gsim_rlz, weight, i)
            self.gsim_by_trt.append(
                dict(zip(gsim_lt.all_trts, gsim_rlz.value)))
            for src_group in lt_model.src_groups:
                if src_group.trt in trts:
                    # ignore the associations to discarded TRTs
                    gs = gsim_lt.get_gsim_by_trt(gsim_rlz, src_group.trt)
                    self.rlzs_assoc[src_group.id, gs].append(rlz)
            rlzs.append(rlz)
        self.rlzs_by_smodel[lt_model.ordinal] = rlzs

    def extract(self, rlz_indices, csm_info):
        """
        Extract a RlzsAssoc instance containing only the given realizations.

        :param rlz_indices: a list of realization indices from 0 to R - 1
        """
        assoc = self.__class__(csm_info)
        if len(rlz_indices) == 1:
            realizations = [self.realizations[rlz_indices[0]]]
        else:
            realizations = operator.itemgetter(*rlz_indices)(self.realizations)
        rlzs_smpath = groupby(realizations, operator.attrgetter('sm_lt_path'))
        smodel_from = {sm.path: sm for sm in csm_info.source_models}
        for smpath, rlzs in rlzs_smpath.items():
            sm = smodel_from[smpath]
            trts = set(sg.trt for sg in sm.src_groups)
            assoc._add_realizations(
                [r.ordinal for r in rlzs], sm,
                csm_info.gsim_lt.reduce(trts), [rlz.gsim_rlz for rlz in rlzs])
        assoc._init()
        return assoc

    def get_assoc_by_grp(self):
        """
        :returns: a numpy array of dtype assoc_by_grp_dt
        """
        lst = []
        for grp_id, gsims in self.gsims_by_grp_id.items():
            for gsim_idx, gsim in enumerate(gsims):
                rlzis = numpy.array(
                    [rlz.ordinal for rlz in self.rlzs_assoc[grp_id, gsim]],
                    U16)
                lst.append((grp_id, gsim_idx, rlzis))
        return numpy.array(lst, assoc_by_grp_dt)

    def __iter__(self):
        return iter(self.rlzs_assoc)

    def __getitem__(self, key):
        return self.rlzs_assoc[key]

    def __len__(self):
        return len(self.rlzs_assoc)

    def __repr__(self):
        pairs = []
        for key in sorted(self.rlzs_assoc):
            rlzs = list(map(str, self.rlzs_assoc[key]))
            if len(rlzs) > 10:  # short representation
                rlzs = ['%d realizations' % len(rlzs)]
            pairs.append(('%s,%s' % key, rlzs))
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

    def get_info(self, sm_id):
        """
        Extract a CompositionInfo instance containing the single
        model of index `sm_id`.
        """
        sm = self.source_models[sm_id]
        num_samples = sm.samples if self.num_samples else 0
        return self.__class__(
            self.gsim_lt, self.seed, num_samples, [sm], self.tot_weight)

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

    def get_rlzs_assoc(self, count_ruptures=None):
        """
        Return a RlzsAssoc with fields realizations, gsim_by_trt,
        rlz_idx and trt_gsims.

        :param count_ruptures: a function src_group -> num_ruptures
        """
        assoc = RlzsAssoc(self)
        random_seed = self.seed
        idx = 0
        trtset = set(self.gsim_lt.tectonic_region_types)
        for i, smodel in enumerate(self.source_models):
            # collect the effective tectonic region types and ruptures
            trts = set()
            for sg in smodel.src_groups:
                if count_ruptures:
                    sg.eff_ruptures = count_ruptures(sg)
                if sg.eff_ruptures:
                    trts.add(sg.trt)
            # recompute the GSIM logic tree if needed
            if trtset != trts:
                before = self.gsim_lt.get_num_paths()
                gsim_lt = self.gsim_lt.reduce(trts)
                after = gsim_lt.get_num_paths()
                if count_ruptures and before > after:
                    logging.warn('Reducing the logic tree of %s from %d to %d '
                                 'realizations', smodel.name, before, after)
            else:
                gsim_lt = self.gsim_lt
            if self.num_samples:  # sampling
                # the int is needed on Windows to convert numpy.uint32 objects
                rnd = random.Random(int(random_seed + idx))
                rlzs = logictree.sample(gsim_lt, smodel.samples, rnd)
            else:  # full enumeration
                rlzs = logictree.get_effective_rlzs(gsim_lt)
            if rlzs:
                indices = numpy.arange(idx, idx + len(rlzs))
                idx += len(indices)
                assoc._add_realizations(indices, smodel, gsim_lt, rlzs)
            elif trts:
                logging.warn('No realizations for %s, %s',
                             '_'.join(smodel.path), smodel.name)
            if len(rlzs) > TWO16:
                raise ValueError(
                    'The source model %s has %d realizations, the maximum '
                    'is %d' % (smodel.name, len(rlzs), TWO16))
        # NB: realizations could be filtered away by logic tree reduction
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
        # populated by the split_sources method
        self.infos = {}

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
        idx = 0
        seed = int(self.source_model_lt.seed)  # avoids F32 issues on Windows
        for sm in self.source_models:
            src_groups = []
            for src_group in sm.src_groups:
                if self.source_model_lt.num_samples:
                    rnd = random.Random(seed + idx)
                    rlzs = logictree.sample(self.gsim_lt, sm.samples, rnd)
                    idx += len(rlzs)
                    for i, sg in enumerate(sm.src_groups):
                        sg.gsims = sorted(set(rlz.value[i] for rlz in rlzs))
                else:
                    for sg in sm.src_groups:
                        sg.gsims = sorted(self.gsim_lt.values[sg.trt])
                sources = []
                for src, sites in src_filter(src_group.sources):
                    sources.append(src)
                    weight += src.weight
                sg = copy.copy(src_group)
                sg.sources = sources
                src_groups.append(sg)
            newsm = logictree.SourceModel(
                sm.name, sm.weight, sm.path, src_groups,
                sm.num_gsim_paths, sm.ordinal, sm.samples)
            source_models.append(newsm)
        new = self.__class__(self.gsim_lt, self.source_model_lt, source_models)
        new.weight = weight
        return new

    @property
    def src_groups(self):
        """
        Yields the SourceGroups inside each source model.
        """
        for sm in self.source_models:
            for src_group in sm.src_groups:
                yield src_group

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
            for src in src_group:
                if kind == 'all':
                    sources.append(src)
                elif kind == 'light' and src.weight <= maxweight:
                    sources.append(src)
                elif kind == 'heavy' and src.weight > maxweight:
                    sources.append(src)
        return sources

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
        for src in self.get_sources():
            nr = src.num_ruptures
            src.serial = rup_serial[start:start + nr]
            start += nr

    def get_maxweight(self, concurrent_tasks):
        """
        Return an appropriate maxweight for use in the block_splitter
        """
        ct = concurrent_tasks or 1
        return max(math.ceil(self.weight / ct), MAXWEIGHT)

    def add_infos(self, sources):
        """
        Populate the .infos dictionary (grp_id, src_id) -> <SourceInfo>
        """
        for src in sources:
            self.infos[src.src_group_id, src.source_id] = SourceInfo(src)

    def split_sources(self, sources, src_filter, maxweight=MAXWEIGHT):
        """
        Split a set of sources of the same source group; light sources
        (i.e. with weight <= maxweight) are not split.

        :param sources: sources of the same source group
        :param src_filter: SourceFilter instance
        :param maxweight: weight used to decide if a source is light
        :yields: blocks of sources of weight around maxweight
        """
        light = [src for src in sources if src.weight <= maxweight]
        self.add_infos(light)
        for block in block_splitter(
                light, maxweight, weight=operator.attrgetter('weight')):
            yield block
        heavy = [src for src in sources if src.weight > maxweight]
        self.add_infos(heavy)
        for src in heavy:
            srcs = split_filter_source(src, src_filter)
            for block in block_splitter(
                    srcs, maxweight, weight=operator.attrgetter('weight')):
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


def split_filter_source(src, src_filter):
    """
    :param src: a source to split
    :param src_filter: a SourceFilter instance
    :returns: a list of split sources
    """
    has_serial = hasattr(src, 'serial')
    split_sources = []
    start = 0
    try:
        splits = split_map[src]  # read from the cache
    except KeyError:  # fill the cache
        splits = split_map[src] = list(sourceconverter.split_source(src))
        if len(splits) > 1:
            logging.info(
                'Splitting %s "%s" in %d sources', src.__class__.__name__,
                src.source_id, len(splits))
    for split in splits:
        if has_serial:
            nr = split.num_ruptures
            split.serial = src.serial[start:start + nr]
            start += nr
        if src_filter.get_close_sites(split) is not None:
            split_sources.append(split)
    return split_sources


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
