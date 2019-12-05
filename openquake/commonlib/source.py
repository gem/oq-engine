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

import copy
import operator
import collections
import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import decode
from openquake.baselib.general import groupby, group_array, AccumDict
from openquake.hazardlib import source, sourceconverter, contexts
from openquake.commonlib import logictree
from openquake.commonlib.rlzs_assoc import get_rlzs_assoc


MINWEIGHT = source.MINWEIGHT
MAX_INT = 2 ** 31 - 1
U16 = numpy.uint16
U32 = numpy.uint32
I32 = numpy.int32
F32 = numpy.float32

rlz_dt = numpy.dtype([
    ('ordinal', U32),
    ('branch_path', hdf5.vstr),
    ('weight', F32)
])

source_model_dt = numpy.dtype([
    ('name', hdf5.vstr),
    ('weight', F32),
    ('path', hdf5.vstr),
    ('num_rlzs', U32),
    ('samples', U32),
])

src_group_dt = numpy.dtype(
    [('grp_id', U32),
     ('name', hdf5.vstr),
     ('trti', U16),
     ('effrup', I32),
     ('totrup', I32),
     ('sm_id', U32)])


def capitalize(words):
    """
    Capitalize words separated by spaces.
    """
    return ' '.join(w.capitalize() for w in decode(words).split(' '))


def get_field(data, field, default):
    """
    :param data: a record with a field `field`, possibily missing
    """
    try:
        return data[field]
    except ValueError:  # field missing in old engines
        return default


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
        gsim_lt = gsimlt or logictree.GsimLogicTree.from_('[FromFile]')
        fakeSM = logictree.LtSourceModel(
            'scenario', weight,  'b1',
            [sourceconverter.SourceGroup('*', eff_ruptures=1)],
            gsim_lt.get_num_paths(), ordinal=0, samples=1)
        return cls(gsim_lt, seed=0, num_samples=0, source_models=[fakeSM],
                   min_mag=0, max_mag=0)

    get_rlzs_assoc = get_rlzs_assoc

    def __init__(self, gsim_lt, seed, num_samples, source_models,
                 min_mag, max_mag):
        self.gsim_lt = gsim_lt
        self.seed = seed
        self.num_samples = num_samples
        self.source_models = source_models
        self.min_mag = min_mag
        self.max_mag = max_mag
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

    def get_info(self, sm_id):
        """
        Extract a CompositionInfo instance containing the single
        model of index `sm_id`.
        """
        sm = self.source_models[sm_id]
        num_samples = sm.samples if self.num_samples else 0
        return self.__class__(self.gsim_lt, self.seed, num_samples, [sm])

    def classify_gsim_lt(self, source_model):
        """
        :returns: (kind, num_paths), where kind is trivial, simple, complex
        """
        trts = set(sg.trt for sg in source_model.src_groups if sg.eff_ruptures)
        gsim_lt = self.gsim_lt.reduce(trts)
        num_branches = list(gsim_lt.get_num_branches().values())
        num_paths = gsim_lt.get_num_paths()
        num_gsims = '(%s)' % ','.join(map(str, num_branches))
        multi_gsim_trts = sum(1 for num_gsim in num_branches if num_gsim > 1)
        if multi_gsim_trts == 0:
            return "trivial" + num_gsims, num_paths
        elif multi_gsim_trts == 1:
            return "simple" + num_gsims, num_paths
        else:
            return "complex" + num_gsims, num_paths

    def get_samples_by_grp(self):
        """
        :returns: a dictionary src_group_id -> source_model.samples
        """
        return {grp.id: sm.samples for sm in self.source_models
                for grp in sm.src_groups}

    def get_rlzs_by_gsim_grp(self, sm_lt_path=None, trts=None):
        """
        :returns: a dictionary src_group_id -> gsim -> rlzs
        """
        self.rlzs_assoc = self.get_rlzs_assoc(sm_lt_path, trts)
        dic = {grp.id: self.rlzs_assoc.get_rlzs_by_gsim(grp.id)
               for sm in self.source_models for grp in sm.src_groups}
        return dic

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
                sg_data.append((src_group.id, src_group.name,
                                trti[src_group.trt], src_group.eff_ruptures,
                                src_group.tot_ruptures, sm.ordinal))
        return (dict(
            gsim_lt=self.gsim_lt,
            sg_data=numpy.array(sg_data, src_group_dt),
            sm_data=numpy.array(sm_data, source_model_dt)),
                dict(seed=self.seed, num_samples=self.num_samples,
                     trts=hdf5.array_of_vstr(sorted(trti)),
                     min_mag=self.min_mag, max_mag=self.max_mag))

    def __fromh5__(self, dic, attrs):
        # TODO: this is called more times than needed, maybe we should cache it
        sg_data = group_array(dic['sg_data'], 'sm_id')
        sm_data = dic['sm_data']
        vars(self).update(attrs)
        self.gsim_lt = dic['gsim_lt']
        self.source_models = []
        for sm_id, rec in enumerate(sm_data):
            tdata = sg_data[sm_id]
            srcgroups = [
                sourceconverter.SourceGroup(
                    self.trts[data['trti']], id=data['grp_id'],
                    name=get_field(data, 'name', ''),
                    eff_ruptures=data['effrup'],
                    tot_ruptures=get_field(data, 'totrup', 0))
                for data in tdata]
            path = tuple(str(decode(rec['path'])).split('_'))
            sm = logictree.LtSourceModel(
                rec['name'], rec['weight'], path, srcgroups,
                rec['num_rlzs'], sm_id, rec['samples'])
            self.source_models.append(sm)
        self.init()

    def get_num_rlzs(self, source_model=None):
        """
        :param source_model: a LtSourceModel instance (or None)
        :returns: the number of realizations per source model (or all)
        """
        if source_model is None:
            return sum(self.get_num_rlzs(sm) for sm in self.source_models)
        if self.num_samples:
            return source_model.samples
        trts = set(sg.trt for sg in source_model.src_groups if sg.eff_ruptures)
        if sum(sg.eff_ruptures for sg in source_model.src_groups) == 0:
            return 0
        return self.gsim_lt.reduce(trts).get_num_paths()

    @property
    def rlzs(self):
        """
        :returns: an array of realizations
        """
        tups = [(r.ordinal, r.uid, r.weight['weight'])
                for r in self.get_rlzs_assoc().realizations]
        return numpy.array(tups, rlz_dt)

    def update_eff_ruptures(self, count_ruptures):
        """
        :param count_ruptures: function or dict src_group_id -> num_ruptures
        """
        for smodel in self.source_models:
            for sg in smodel.src_groups:
                sg.eff_ruptures = (count_ruptures(sg.id)
                                   if callable(count_ruptures)
                                   else count_ruptures.get(sg.id, 0))

    def get_source_model(self, src_group_id):
        """
        :returns: the source model for the given src_group_id
        """
        for smodel in self.source_models:
            for src_group in smodel.src_groups:
                if src_group.id == src_group_id:
                    return smodel

    def get_gsims_by_trt(self):
        """
        :returns: a dictionary trt -> sorted gsims
        """
        if self.num_samples:
            gsims_by_trt = AccumDict(accum=set())
            for sm in self.source_models:
                rlzs = self.gsim_lt.sample(sm.samples, self.seed + sm.ordinal)
                for t, trt in enumerate(self.gsim_lt.values):
                    gsims_by_trt[trt].update([rlz.value[t] for rlz in rlzs])
        else:
            gsims_by_trt = self.gsim_lt.values
        return {trt: sorted(gsims) for trt, gsims in gsims_by_trt.items()}

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
        :returns: a dictionary grp_id -> group attribute
        """
        dic = {}
        for smodel in self.source_models:
            for src_group in smodel.src_groups:
                dic[src_group.id] = getattr(src_group, name)
        return dic

    def __repr__(self):
        info_by_model = {}
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


class CompositeSourceModel(collections.abc.Sequence):
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
        min_mags, max_mags = [], []
        for sm in source_models:
            for sg in sm.src_groups:
                for src in sg:
                    if hasattr(src, 'get_min_max_mag'):
                        m1, m2 = src.get_min_max_mag()
                        min_mags.append(m1)
                        max_mags.append(m2)
        self.info = CompositionInfo(
            gsim_lt, self.source_model_lt.seed,
            self.source_model_lt.num_samples,
            [sm.get_skeleton() for sm in self.source_models],
            min(min_mags) if min_mags else 0,
            max(max_mags) if max_mags else 0)

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
        return self.__class__(self.gsim_lt, self.source_model_lt, smodels)

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
        return new

    # used only by UCERF
    def new(self, sources_by_grp):
        """
        Generate a new CompositeSourceModel from the given dictionary.

        :param sources_by_group: a dictionary grp_id -> sources
        :returns: a new CompositeSourceModel instance
        """
        source_models = []
        for sm in self.source_models:
            src_groups = []
            for src_group in sm.src_groups:
                sg = copy.copy(src_group)
                sg.sources = sorted(sources_by_grp.get(sg.id, []),
                                    key=operator.attrgetter('id'))
                src_groups.append(sg)
            newsm = logictree.LtSourceModel(
                sm.names, sm.weight, sm.path, src_groups,
                sm.num_gsim_paths, sm.ordinal, sm.samples)
            source_models.append(newsm)
        new = self.__class__(self.gsim_lt, self.source_model_lt, source_models)
        new.info.update_eff_ruptures(new.get_num_ruptures())
        return new

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

    def get_sources(self, kind='all'):
        """
        Extract the sources contained in the source models by optionally
        filtering and splitting them, depending on the passed parameter.
        """
        assert kind in ('all', 'indep', 'mutex'), kind
        sources = []
        for sm in self.source_models:
            for src_group in sm.src_groups:
                if kind in ('all', src_group.src_interdep):
                    for src in src_group:
                        if sm.samples > 1:
                            src.samples = sm.samples
                        sources.append(src)
        return sources

    def get_trt_sources(self, optimize_dupl=False):
        """
        :param optimize_dupl: if True change src_group_id to a list
        :returns: a list of triples [(trt, group of sources, atomic flag)]
        """
        atomic = []
        acc = AccumDict(accum=[])
        for sm in self.source_models:
            for grp in sm.src_groups:
                if grp and grp.atomic:
                    atomic.append((grp.trt, grp, True))
                elif grp:
                    acc[grp.trt].extend(grp)
        if not acc:
            return atomic
        elif not optimize_dupl:
            # for UCERF or for event_based
            return atomic + [kv + (False,) for kv in acc.items()]
        # extract a single source from multiple sources with the same ID
        dic = {}
        key = operator.attrgetter('source_id', 'checksum')
        for trt in acc:
            dic[trt] = []
            for srcs in groupby(acc[trt], key).values():
                src = srcs[0]
                # src.src_group_id can be a list if get_sources_by_trt was
                # called before
                if len(srcs) > 1 and not isinstance(src.src_group_id, list):
                    src.src_group_id = [s.src_group_id for s in srcs]
                dic[trt].append(src)
        return atomic + [kv + (False,) for kv in dic.items()]

    def get_num_ruptures(self):
        """
        :returns: the number of ruptures per source group ID
        """
        return {grp.id: sum(src.num_ruptures for src in grp)
                for grp in self.src_groups}

    def init_serials(self, ses_seed):
        """
        Generate unique seeds for each rupture with numpy.arange.
        This should be called only in event based calculators
        """
        sources = self.get_sources()
        serial = ses_seed
        for src in sources:
            nr = src.num_ruptures
            src.serial = serial
            serial += nr

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
