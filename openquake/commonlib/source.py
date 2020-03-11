# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2020 GEM Foundation
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

import operator
import collections
import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import decode
from openquake.baselib.general import groupby, AccumDict
from openquake.hazardlib import source, sourceconverter
from openquake.commonlib import logictree


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
    ('samples', U32),
    ('offset', U32),
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
        return '<%d,%s,w=%s>' % (self.ordinal, self.pid, self.weight)

    @property
    def gsim_lt_path(self):
        return self.gsim_rlz.lt_path

    @property
    def pid(self):
        """An unique identifier for effective realizations"""
        return '_'.join(self.sm_lt_path) + '~' + self.gsim_rlz.pid

    def __lt__(self, other):
        return self.ordinal < other.ordinal

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __ne__(self, other):
        return repr(self) != repr(other)

    def __hash__(self):
        return hash(repr(self))


class FullLogicTree(object):
    """
    An object to collect information about the composition of
    a composite source model.

    :param source_model_lt: a SourceModelLogicTree object
    :param source_models: a list of Realization instances
    """
    @classmethod
    def fake(cls, gsimlt=None):
        """
        :returns:
            a fake `FullLogicTree` instance with the given gsim logic tree
            object; if None, builds automatically a fake gsim logic tree
        """
        gsim_lt = gsimlt or logictree.GsimLogicTree.from_('[FromFile]')
        fakeSM = logictree.Realization(
            'scenario', weight=1,  ordinal=0, lt_path='b1', samples=1)
        info = object.__new__(cls)
        info.source_model_lt = logictree.SourceModelLogicTree.fake()
        info.gsim_lt = gsim_lt
        info.sm_rlzs = [fakeSM]
        return info

    def __init__(self, source_model_lt, gsim_lt):
        self.source_model_lt = source_model_lt
        self.gsim_lt = gsim_lt
        self.init()  # set .sm_rlzs and .trt_by_grp

    def init(self):
        sm_rlzs = logictree.get_effective_rlzs(self.source_model_lt)
        if not self.num_samples:
            num_gsim_rlzs = self.gsim_lt.get_num_paths()
        offset = 0
        for sm_rlz in sm_rlzs:
            sm_rlz.offset = offset
            if self.num_samples:
                offset += sm_rlz.samples
            else:
                offset += num_gsim_rlzs
        self.sm_rlzs = sm_rlzs

    @property
    def trt_by_grp(self):
        trt_by_grp = []
        n = len(self.sm_rlzs)
        trts = list(self.gsim_lt.values)
        for smodel in self.sm_rlzs:
            for grp_id in self.grp_ids(smodel.ordinal):
                trt_by_grp.append((grp_id, trts[grp_id // n]))
        return dict(sorted(trt_by_grp))

    @property
    def seed(self):
        return self.source_model_lt.seed

    @property
    def num_samples(self):
        return self.source_model_lt.num_samples

    def grp_ids(self, eri):
        """
        :param eri: effective realization index
        :returns: array of T group IDs, being T the number of TRTs
        """
        nt = len(self.gsim_lt.values)
        ns = len(self.sm_rlzs)
        return eri + numpy.arange(nt) * ns

    def get_samples_by_grp(self):
        """
        :returns: a dictionary grp_id -> source_model.samples
        """
        return {grp_id: sm.samples for sm in self.sm_rlzs
                for grp_id in self.grp_ids(sm.ordinal)}

    def gsim_by_trt(self, rlz):
        """
        :returns: a dictionary trt->gsim for the given realization
        """
        return dict(zip(self.gsim_lt.values, rlz.gsim_rlz.value))

    def get_rlzs(self, eri):
        """
        :returns: a list of LtRealization objects
        """
        rlzs = []
        sm = self.sm_rlzs[eri]
        if self.num_samples:
            gsim_rlzs = self.gsim_lt.sample(sm.samples, self.seed + sm.ordinal)
        elif hasattr(self, 'gsim_rlzs'):  # cache
            gsim_rlzs = self.gsim_rlzs
        else:
            self.gsim_rlzs = gsim_rlzs = logictree.get_effective_rlzs(
                self.gsim_lt)
        for i, gsim_rlz in enumerate(gsim_rlzs):
            weight = sm.weight * gsim_rlz.weight
            rlz = LtRealization(sm.offset + i, sm.lt_path, gsim_rlz, weight)
            rlzs.append(rlz)
        return rlzs

    def get_realizations(self):
        """
        :returns: the complete list of LtRealizations
        """
        rlzs = sum((self.get_rlzs(sm.ordinal) for sm in self.sm_rlzs), [])
        assert rlzs, 'No realizations found??'
        if self.num_samples:
            assert len(rlzs) == self.num_samples, (len(rlzs), self.num_samples)
            for rlz in rlzs:
                for k in rlz.weight.dic:
                    rlz.weight.dic[k] = 1. / self.num_samples
        else:
            tot_weight = sum(rlz.weight for rlz in rlzs)
            if not tot_weight.is_one():
                # this may happen for rounding errors; we ensure the sum of
                # the weights is 1
                for rlz in rlzs:
                    rlz.weight = rlz.weight / tot_weight
        return rlzs

    def get_rlzs_by_gsim(self, grp_id):
        """
        :returns: a dictionary gsim -> rlzs
        """
        trti, eri = divmod(grp_id, len(self.sm_rlzs))
        rlzs_by_gsim = AccumDict(accum=[])
        for rlz in self.get_rlzs(eri):
            rlzs_by_gsim[rlz.gsim_rlz.value[trti]].append(rlz.ordinal)
        return {gsim: U32(rlzs) for gsim, rlzs in sorted(rlzs_by_gsim.items())}

    def get_rlzs_by_gsim_grp(self):
        """
        :returns: a dictionary grp_id -> gsim -> rlzs
        """
        dic = {}
        for sm in self.sm_rlzs:
            for grp_id in self.grp_ids(sm.ordinal):
                dic[grp_id] = self.get_rlzs_by_gsim(grp_id)
        return dic

    def get_rlzs_by_grp(self):
        """
        :returns: a dictionary grp_id -> [rlzis, ...]
        """
        dic = {}
        for sm in self.sm_rlzs:
            for grp_id in self.grp_ids(sm.ordinal):
                grp = 'grp-%02d' % grp_id
                dic[grp] = list(self.get_rlzs_by_gsim(grp_id).values())
        return dic  # grp_id -> lists of rlzi

    def __getnewargs__(self):
        # with this FullLogicTree instances will be unpickled correctly
        return self.seed, self.num_samples, self.sm_rlzs

    def __toh5__(self):
        # save full_lt/sm_data in the datastore
        sm_data = []
        for sm in self.sm_rlzs:
            sm_data.append((sm.value, sm.weight, '_'.join(sm.lt_path),
                            sm.samples, sm.offset))
        return (dict(
            source_model_lt=self.source_model_lt,
            gsim_lt=self.gsim_lt,
            sm_data=numpy.array(sm_data, source_model_dt)),
                dict(seed=self.seed, num_samples=self.num_samples,
                     trts=hdf5.array_of_vstr(self.gsim_lt.values)))

    def __fromh5__(self, dic, attrs):
        # TODO: this is called more times than needed, maybe we should cache it
        sm_data = dic['sm_data']
        vars(self).update(attrs)
        self.source_model_lt = dic['source_model_lt']
        self.gsim_lt = dic['gsim_lt']
        self.sm_rlzs = []
        for sm_id, rec in enumerate(sm_data):
            path = tuple(str(decode(rec['path'])).split('_'))
            sm = logictree.Realization(
                rec['name'], rec['weight'], sm_id, path,
                rec['samples'], rec['offset'])
            self.sm_rlzs.append(sm)

    def get_num_rlzs(self, sm_rlz=None):
        """
        :param sm_rlz: a Realization instance (or None)
        :returns: the number of realizations per source model (or all)
        """
        if sm_rlz is None:
            return sum(self.get_num_rlzs(sm) for sm in self.sm_rlzs)
        if self.num_samples:
            return sm_rlz.samples
        return self.gsim_lt.get_num_paths()

    @property
    def rlzs(self):
        """
        :returns: an array of realizations
        """
        tups = [(r.ordinal, r.pid, r.weight['weight'])
                for r in self.get_realizations()]
        return numpy.array(tups, rlz_dt)

    def get_gsims_by_trt(self):
        """
        :returns: a dictionary trt -> sorted gsims
        """
        if self.num_samples:
            gsims_by_trt = AccumDict(accum=set())
            for sm in self.sm_rlzs:
                rlzs = self.gsim_lt.sample(sm.samples, self.seed + sm.ordinal)
                for t, trt in enumerate(self.gsim_lt.values):
                    gsims_by_trt[trt].update([rlz.value[t] for rlz in rlzs])
        else:
            gsims_by_trt = self.gsim_lt.values
        return {trt: sorted(gsims) for trt, gsims in gsims_by_trt.items()}

    def get_sm_by_grp(self):
        """
        :returns: a dictionary grp_id -> sm_id
        """
        return {grp_id: sm.ordinal for sm in self.sm_rlzs
                for grp_id in self.grp_ids(sm.ordinal)}

    def __repr__(self):
        info_by_model = {}
        for sm in self.sm_rlzs:
            info_by_model[sm.lt_path] = (
                '_'.join(map(decode, sm.lt_path)),
                decode(sm.value), sm.weight, self.get_num_rlzs(sm))
        summary = ['%s, %s, weight=%s: %d realization(s)' % ibm
                   for ibm in info_by_model.values()]
        return '<%s\n%s>' % (self.__class__.__name__, '\n'.join(summary))


class CompositeSourceModel(collections.abc.Sequence):
    """
    :param gsim_lt:
        a :class:`openquake.commonlib.logictree.GsimLogicTree` instance
    :param full_lt:
        a :class:`FullLogicTree` instance
    :param groups:
        a list of SourceGroups
    :param ses_seed:
        a seed used in event based
    :param event_based:
        a flag True for event based calculations, flag otherwise
    """
    def __init__(self, full_lt, src_groups):
        self.gsim_lt = full_lt.gsim_lt
        self.source_model_lt = full_lt.source_model_lt
        self.sm_rlzs = full_lt.sm_rlzs
        self.full_lt = full_lt
        self.src_groups = src_groups

    def get_nonparametric_sources(self):
        """
        :returns: list of non parametric sources in the composite source model
        """
        return [src for src_group in self.src_groups
                for src in src_group if hasattr(src, 'data')]

    def get_floating_spinning_factors(self):
        """
        :returns: (floating rupture factor, spinning rupture factor)
        """
        data = []
        for sg in self.src_groups:
            for src in sg:
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
            sm.ordinal, sm.name, '_'.join(sm.lt_path), sm.weight,
            len(sm.src_groups)) for sm in self.sm_rlzs]
        return '<%s\n%s>' % (self.__class__.__name__, '\n'.join(models))

    def __getitem__(self, i):
        """Return the i-th source model"""
        return self.sm_rlzs[i]

    def __iter__(self):
        """Return an iterator over the underlying source models"""
        return iter(self.sm_rlzs)

    def __len__(self):
        """Return the number of underlying source models"""
        return len(self.sm_rlzs)
