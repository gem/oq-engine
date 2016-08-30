# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
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
import re
import copy
import math
import time
import logging
import operator
import collections
import random

import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import decode
from openquake.baselib.general import groupby, block_splitter, group_array
from openquake.hazardlib.site import Tile
from openquake.commonlib import logictree, sourceconverter
from openquake.commonlib import nrml, node, parallel

MAXWEIGHT = 200  # tuned by M. Simionato
MAX_INT = 2 ** 31 - 1
U16 = numpy.uint16
U32 = numpy.uint32
I32 = numpy.int32
F32 = numpy.float32


class LtRealization(object):
    """
    Composite realization build on top of a source model realization and
    a GSIM realization.
    """
    def __init__(self, ordinal, sm_lt_path, gsim_rlz, weight, sampleid):
        self.ordinal = ordinal
        self.sm_lt_path = sm_lt_path
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


class SourceModel(object):
    """
    A container of SourceGroup instances with some additional attributes
    describing the source model in the logic tree.
    """
    def __init__(self, name, weight, path, src_groups, num_gsim_paths, ordinal,
                 samples):
        self.name = name
        self.weight = weight
        self.path = path
        self.src_groups = src_groups
        self.num_gsim_paths = num_gsim_paths
        self.ordinal = ordinal
        self.samples = samples

    @property
    def num_sources(self):
        return sum(len(sg) for sg in self.src_groups)

    def get_skeleton(self):
        """
        Return an empty copy of the source model, i.e. without sources,
        but with the proper attributes for each SourceGroup contained within.
        """
        src_groups = [sourceconverter.SourceGroup(
            sg.trt, [], sg.min_mag, sg.max_mag, sg.id)
                      for sg in self.src_groups]
        return self.__class__(self.name, self.weight, self.path, src_groups,
                              self.num_gsim_paths, self.ordinal, self.samples)


def capitalize(words):
    """
    Capitalize words separated by spaces.

    >>> capitalize('active shallow crust')
    'Active Shallow Crust'
    """
    return ' '.join(w.capitalize() for w in words.split(' '))


class SourceModelParser(object):
    """
    A source model parser featuring a cache.

    :param converter:
        :class:`openquake.commonlib.source.SourceConverter` instance
    """
    def __init__(self, converter):
        self.converter = converter
        self.groups = {}  # cache fname -> groups
        self.fname_hits = collections.Counter()  # fname -> number of calls

    def parse_src_groups(self, fname, apply_uncertainties=None):
        """
        :param fname:
            the full pathname of the source model file
        :param apply_uncertainties:
            a function modifying the sources (or None)
        """
        try:
            groups = self.groups[fname]
        except KeyError:
            groups = self.groups[fname] = self.parse_groups(fname)
        # NB: deepcopy is *essential* here
        groups = [copy.deepcopy(g) for g in groups]
        for group in groups:
            for src in group:
                if apply_uncertainties:
                    apply_uncertainties(src)
                    src.num_ruptures = src.count_ruptures()
        self.fname_hits[fname] += 1
        return groups

    def parse_groups(self, fname):
        """
        Parse all the groups and return them ordered by number of sources.
        It does not count the ruptures, so it is relatively fast.

        :param fname:
            the full pathname of the source model file
        """
        return nrml.parse(fname, self.converter)


def agg_prob(acc, prob):
    """Aggregation function for probabilities"""
    return 1. - (1. - acc) * (1. - prob)


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
        self.rlzs_by_smodel = [[] for _ in range(len(csm_info.source_models))]
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
            assert len(self.realizations) == self.num_samples
            for rlz in self.realizations:
                rlz.weight = 1. / self.num_samples
        else:
            tot_weight = sum(rlz.weight for rlz in self.realizations)
            if tot_weight == 0:
                raise ValueError('All realizations have zero weight??')
            elif abs(tot_weight - 1) > 1E-12:  # allow for rounding errors
                logging.warn('Some source models are not contributing, '
                             'weights are being rescaled')
            for rlz in self.realizations:
                rlz.weight = rlz.weight / tot_weight

        self.gsims_by_grp_id = groupby(
            self.rlzs_assoc, operator.itemgetter(0),
            lambda group: sorted(gsim for grp_id, gsim in group))

    @property
    def realizations(self):
        """Flat list with all the realizations"""
        return sum(self.rlzs_by_smodel, [])

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
        Returns an OrderedDict gsim -> rlzs with attributes .realizations,
        .sm_id, .samples and .seed.
        """
        rlzs = set()
        rlzs_by_gsim = collections.OrderedDict()
        for gsim in self.gsims_by_grp_id[grp_id]:
            rlzs_by_gsim[gsim] = self[grp_id, str(gsim)]
            rlzs.update(rlzs_by_gsim[gsim])
        rlzs_by_gsim.realizations = sorted(rlzs)
        rlzs_by_gsim.sm_id = self.sm_ids[grp_id]
        rlzs_by_gsim.samples = self.samples[grp_id]
        rlzs_by_gsim.seed = self.seed
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

    # used in riskinput
    def combine(self, results, agg=agg_prob):
        """
        :param results: a dictionary (src_group_id, gsim) -> floats
        :param agg: an aggregation function
        :returns: a dictionary rlz -> aggregated floats

        Example: a case with tectonic region type T1 with GSIMS A, B, C
        and tectonic region type T2 with GSIMS D, E.

        >> assoc = RlzsAssoc(CompositionInfo([], []))
        >> assoc.rlzs_assoc = {
        ... ('T1', 'A'): ['r0', 'r1'],
        ... ('T1', 'B'): ['r2', 'r3'],
        ... ('T1', 'C'): ['r4', 'r5'],
        ... ('T2', 'D'): ['r0', 'r2', 'r4'],
        ... ('T2', 'E'): ['r1', 'r3', 'r5']}
        ...
        >> results = {
        ... ('T1', 'A'): 0.01,
        ... ('T1', 'B'): 0.02,
        ... ('T1', 'C'): 0.03,
        ... ('T2', 'D'): 0.04,
        ... ('T2', 'E'): 0.05,}
        ...
        >> combinations = assoc.combine(results, operator.add)
        >> for key, value in sorted(combinations.items()): print key, value
        r0 0.05
        r1 0.06
        r2 0.06
        r3 0.07
        r4 0.07
        r5 0.08

        You can check that all the possible sums are performed:

        r0: 0.01 + 0.04 (T1A + T2D)
        r1: 0.01 + 0.05 (T1A + T2E)
        r2: 0.02 + 0.04 (T1B + T2D)
        r3: 0.02 + 0.05 (T1B + T2E)
        r4: 0.03 + 0.04 (T1C + T2D)
        r5: 0.03 + 0.05 (T1C + T2E)

        In reality, the `.combine` method is used with hazard_curves and
        the aggregation function is the `agg_curves` function, a composition of
        probability, which however is close to the sum for small probabilities.
        """
        ad = {rlz: 0 for rlz in self.realizations}
        for key, value in results.items():
            for rlz in self.rlzs_assoc[key]:
                ad[rlz] = agg(ad[rlz], value)
        return ad

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
        fakeSM = SourceModel(
            'fake', weight,  'b1',
            [sourceconverter.SourceGroup('*', eff_ruptures=1)],
            gsim_lt.get_num_paths(), ordinal=0, samples=1)
        return cls(gsim_lt, seed=0, num_samples=0, source_models=[fakeSM])

    def __init__(self, gsim_lt, seed, num_samples, source_models):
        self.gsim_lt = gsim_lt
        self.seed = seed
        self.num_samples = num_samples
        self.source_models = source_models

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
                     gsim_fname=self.gsim_lt.fname))

    def __fromh5__(self, dic, attrs):
        sg_data = group_array(dic['sg_data'], 'sm_id')
        sm_data = dic['sm_data']
        vars(self).update(attrs)
        if self.gsim_fname.endswith('.xml'):
            self.gsim_lt = logictree.GsimLogicTree(
                self.gsim_fname, sorted(self.trts))
        else:  # fake file with the name of the GSIM
            self.gsim_lt = logictree.GsimLogicTree.from_(self.gsim_fname)
        self.source_models = []
        for sm_id, rec in enumerate(sm_data):
            tdata = sg_data[sm_id]
            srcgroups = [
                sourceconverter.SourceGroup(
                    self.trts[trti], id=grp_id, eff_ruptures=effrup)
                for grp_id, trti, effrup, sm_id in tdata if effrup]
            path = tuple(rec['path'].split('_'))
            trts = set(sg.trt for sg in srcgroups)
            num_gsim_paths = self.gsim_lt.reduce(trts).get_num_paths()
            sm = SourceModel(rec['name'], rec['weight'], path, srcgroups,
                             num_gsim_paths, sm_id, rec['samples'])
            self.source_models.append(sm)

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

    # FIXME: this is called several times, both in .init and in .send_sources
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
                             b'_'.join(smodel.path), smodel.name)
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

    def get_trt(self, src_group_id):
        """
        Return the TRT string for the given src_group_id
        """
        for smodel in self.source_models:
            for src_group in smodel.src_groups:
                if src_group.id == src_group_id:
                    return src_group.trt

    def __repr__(self):
        info_by_model = collections.OrderedDict()
        for sm in self.source_models:
            info_by_model[sm.path] = (
                '_'.join(map(decode, sm.path)),
                decode(sm.name),
                [sg.id for sg in sm.src_groups],
                sm.weight,
                self.get_num_rlzs(sm))
        summary = ['%s, %s, trt=%s, weight=%s: %d realization(s)' % ibm
                   for ibm in info_by_model.values()]
        return '<%s\n%s>' % (
            self.__class__.__name__, '\n'.join(summary))


class CompositeSourceModel(collections.Sequence):
    """
    :param source_model_lt:
        a :class:`openquake.commonlib.logictree.SourceModelLogicTree` instance
    :param source_models:
        a list of :class:`openquake.commonlib.source.SourceModel` tuples
    """
    def __init__(self, gsim_lt, source_model_lt, source_models,
                 set_weight=True):
        self.gsim_lt = gsim_lt
        self.source_model_lt = source_model_lt
        self.source_models = source_models
        self.source_info = ()  # set by the SourceFilterSplitter
        self.split_map = {}
        if set_weight:
            self.set_weights()
        # must go after set_weights to have the correct .num_ruptures
        self.info = CompositionInfo(
            gsim_lt, self.source_model_lt.seed,
            self.source_model_lt.num_samples,
            [sm.get_skeleton() for sm in self.source_models])

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

    def set_weights(self):
        """
        Update the attributes .weight and src.num_ruptures for each TRT model
        .weight of the CompositeSourceModel.
        """
        self.weight = self.filtered_weight = 0
        for src_group in self.src_groups:
            weight = 0
            num_ruptures = 0
            for src in src_group:
                weight += src.weight
                num_ruptures += src.num_ruptures
            src_group.weight = weight
            src_group.sources = sorted(
                src_group, key=operator.attrgetter('source_id'))
            self.weight += weight

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
    for blevel in nrml.read(smlt).logicTree:
        with node.context(smlt, blevel):
            for bset in blevel:
                for br in bset:
                    smfname = br.uncertaintyModel.text
                    if smfname:
                        yield smfname


# ########################## SourceManager ########################### #

def source_info_iadd(self, other):
    assert self.src_group_id == other.src_group_id
    assert self.source_id == other.source_id
    return self.__class__(
        self.src_group_id, self.source_id, self.source_class, self.weight,
        self.sources, self.filter_time + other.filter_time,
        self.split_time + other.split_time,
        self.cum_calc_time + other.cum_calc_time,
        max(self.max_calc_time, other.max_calc_time),
        self.num_tasks + other.num_tasks,
    )

SourceInfo = collections.namedtuple(
    'SourceInfo', 'src_group_id source_id source_class weight sources '
    'filter_time split_time cum_calc_time max_calc_time num_tasks')
SourceInfo.__iadd__ = source_info_iadd

source_info_dt = numpy.dtype([
    ('src_group_id', numpy.uint32),    # 0
    ('source_id', (bytes, 100)),       # 1
    ('source_class', (bytes, 30)),     # 2
    ('weight', numpy.float32),         # 3
    ('split_num', numpy.uint32),       # 4
    ('filter_time', numpy.float32),    # 5
    ('split_time', numpy.float32),     # 6
    ('cum_calc_time', numpy.float32),  # 7
    ('max_calc_time', numpy.float32),  # 8
    ('num_tasks', numpy.uint32),       # 9
])


def split_filter(src, sites, max_dist, random_seed):
    """
    :param src: an heavy source
    :param sites: the sites affected by the source
    :param max_dist: maximum distance for the current TRT
    :random_seed: used only for event based calculations
    :returns:
        a list [(src, sites, split_sources, filter_time, split_time), ...]
    """
    t0 = time.time()
    split_sources = []
    start = 0
    for ss in sourceconverter.split_source(src):
        if random_seed:
            nr = ss.num_ruptures
            ss.serial = src.serial[start:start + nr]
            start += nr
        ss.id = src.id
        s = ss.filter_sites_by_distance_to_source(max_dist, sites)
        if s is not None:
            split_sources.append(ss)
    return [(src, sites, split_sources, 0, time.time() - t0)]


class SourceManager(object):
    """
    Manager associated to a CompositeSourceModel instance.
    Filter and split sources and send them to the worker tasks.
    """
    def __init__(self, csm, maximum_distance, concurrent_tasks,
                 dstore, monitor, random_seed=None,
                 filter_sources=True, num_tiles=1):
        self.csm = csm
        self.maximum_distance = maximum_distance
        self.concurrent_tasks = concurrent_tasks or 1
        self.random_seed = random_seed
        self.dstore = dstore
        self.monitor = monitor
        self.filter_sources = filter_sources
        self.num_tiles = num_tiles
        self.rlzs_assoc = csm.info.get_rlzs_assoc()
        self.infos = {}  # src_group_id, source_id -> SourceInfo tuple

        self.maxweight = math.ceil(csm.weight / self.concurrent_tasks)
        if num_tiles > 1:
            self.maxweight = max(self.maxweight / num_tiles, MAXWEIGHT)
        logging.info('Instantiated SourceManager with maxweight=%.1f',
                     self.maxweight)
        if random_seed is not None:
            # generate unique seeds for each rupture with numpy.arange
            n = sum(sg.tot_ruptures() for sg in self.csm.src_groups)
            rup_serial = numpy.arange(n, dtype=numpy.uint32)
            start = 0
            for src in self.csm.get_sources():
                nr = src.num_ruptures
                src.serial = rup_serial[start:start + nr]
                start += nr

    def gen_blocks(self, srcs_times, tiles):
        """
        :param srcs_times:
            a 5-uple (src, sites, split_sources, filter_time, split_time)
        :param tiles:
            a list of :class:`openquake.hazardlib.site.Tile` objects
        :yields:
            pairs (sources, sitecol)
        """
        light = [[] for tile in tiles]
        for src, sites, sources, filter_time, split_time in srcs_times:
            if sources:  # heavy
                for block in block_splitter(sources, self.maxweight,
                                            operator.attrgetter('weight')):
                    yield block, sites
            else:
                light[sites].append(src)  # sites here is a tile index
            info = SourceInfo(src.src_group_id, src.source_id,
                              src.__class__.__name__,
                              src.weight, len(sources),
                              filter_time, split_time, 0, 0, 0)
            key = (src.src_group_id, src.source_id)
            if key in self.infos:
                self.infos[key] += info
            else:
                self.infos[key] = info
        # light
        for srcs, tile in zip(light, tiles):
            for block in block_splitter(
                    srcs, self.maxweight,
                    operator.attrgetter('weight'),
                    operator.attrgetter('src_group_id')):
                yield block, tile.sitecol

    def gen_args(self, sitecol, tiles):
        """
        Yield (sources, sites, rlzs_assoc, monitor) by
        looping on the tiles and on the source blocks.
        """
        for args_per_tile in self._gen_args_light(tiles):
            for args in args_per_tile:
                yield args
        for args in self._gen_args_heavy(sitecol):
            yield args

    def _gen_args(self, srcs_times, tiles):
        if not srcs_times:
            return
        mon = self.monitor.new()
        nblocks = 0
        nsources = 0
        for block, sites in self.gen_blocks(srcs_times, tiles):
            grp_id = block[0].src_group_id
            rlzs_by_gsim = self.rlzs_assoc.get_rlzs_by_gsim(grp_id)
            nsources += len(block)
            nblocks += 1
            yield block, sites, rlzs_by_gsim, mon
        logging.info('Sent %d sources in %d tasks(s)', nsources, nblocks)

    def _gen_args_light(self, tiles):
        filter_mon = self.monitor('filtering sources')
        tiles = [Tile(tile, self.maximum_distance) for tile in tiles]
        if self.filter_sources and self.num_tiles == 1:
            logging.info('Filtering light sources')
        sources = self.csm.get_sources('light', self.maxweight)
        for i, tile in enumerate(tiles):
            data = []
            for src in sources:
                with filter_mon:
                    ok = src in tile
                if ok:
                    data.append((src, i, [], filter_mon.dt, 0))
                self.csm.filtered_weight += src.weight
            filter_mon.flush()
            if len(tiles) > 1:
                logging.info('Got %d light source(s) from tile %d',
                             len(data), i + 1)
            yield self._gen_args(data, tiles)

    def _gen_args_heavy(self, sitecol):
        sources = self.csm.get_sources('heavy', self.maxweight)
        data = []
        for src in sources:
            self.csm.filtered_weight += src.weight
            sites = src.filter_sites_by_distance_to_source(
                self.maximum_distance[src.tectonic_region_type], sitecol)
            if sites is not None:
                max_dist = self.maximum_distance[src.tectonic_region_type]
                data.append((src, sites, max_dist, self.random_seed))
        if len(data) == 1:
            srcs_times = split_filter(*data[0])
        else:
            srcs_times = parallel.starmap(split_filter, data).reduce(acc=[])
        return self._gen_args(srcs_times, [sitecol])

    def pre_store_source_info(self, dstore):
        """
        Save the `source_info` array and its attributes in the datastore.

        :param dstore: the datastore
        """
        attrs = dstore.hdf5['composite_source_model'].attrs
        attrs['weight'] = self.csm.weight
        attrs['filtered_weight'] = self.csm.filtered_weight

        if self.infos:
            values = list(self.infos.values())
            values.sort(
                key=lambda info: info.filter_time + info.split_time,
                reverse=True)
            dstore['source_info'] = numpy.array(values, source_info_dt)
            attrs = dstore['source_info'].attrs
            attrs['maxweight'] = self.maxweight
            self.infos.clear()
