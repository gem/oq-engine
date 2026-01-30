# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2026, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import toml
import copy
import zlib
import pickle
import logging
import operator
import collections
import numpy
from openquake.baselib import config, python3compat, hdf5, performance
from openquake.baselib.general import (
    block_splitter, split_in_blocks, AccumDict, groupby)
from openquake.hazardlib.calc.filters import split_source
from openquake.hazardlib.source import NonParametricSeismicSource
from openquake.hazardlib.source.point import msr_name
from openquake.hazardlib.valid import basename, fragmentno
from openquake.hazardlib.contexts import get_cmakers

U16 = numpy.uint16
TWO16 = 2 ** 16  # 65,536
TWO16 = 2 ** 16  # 65,536
TWO24 = 2 ** 24  # 16,777,216
TWO30 = 2 ** 30  # 1,073,741,24
TWO32 = 2 ** 32  # 4,294,967,296
weight = operator.attrgetter('weight')
CALC_TIME, NUM_CTXS, NUM_RUPTURES, WEIGHT, MUTEX = 3, 4, 5, 6, 7


def _grp_id(blk):
    # NB: grp_id may by passed instead of a source or a block
    if isinstance(blk, (U16, int)):
        return blk
    src = blk[0]
    return src if isinstance(src, U16) else src.grp_id


class SourceGroup(collections.abc.Sequence):
    """
    A container for the following parameters:

    :param str trt:
        the tectonic region type all the sources belong to
    :param list sources:
        a list of hazardlib source objects
    :param name:
        The name of the group
    :param src_interdep:
        A string specifying if the sources in this cluster are independent or
        mutually exclusive
    :param rup_indep:
        A string specifying if the ruptures within each source of the cluster
        are independent or mutually exclusive
    :param weights:
        A dictionary whose keys are the source IDs of the cluster and the
        values are the weights associated with each source
    :param min_mag:
        the minimum magnitude among the given sources
    :param max_mag:
        the maximum magnitude among the given sources
    :param id:
        an optional numeric ID (default 0) set by the engine and used
        when serializing SourceModels to HDF5
    :param temporal_occurrence_model:
        A temporal occurrence model controlling the source group occurrence
    :param cluster:
        A boolean indicating if the sources behaves as a cluster similarly
        to what used by the USGS for the New Madrid in the 2008 National
        Hazard Model.
    """
    changes = 0  # set in apply_uncertainty

    @classmethod
    def collect(cls, sources):
        """
        :param sources: dictionaries with a key 'tectonicRegion'
        :returns: an ordered list of SourceGroup instances
        """
        source_stats_dict = {}
        for src in sources:
            trt = src['tectonicRegion']
            if trt not in source_stats_dict:
                source_stats_dict[trt] = SourceGroup(trt)
            sg = source_stats_dict[trt]
            if not sg.sources:
                # we append just one source per SourceGroup, so that
                # the memory occupation is insignificant
                sg.sources.append(src)

        # return SourceGroups, ordered by TRT string
        return sorted(source_stats_dict.values())

    def __init__(self, trt, sources=None, name=None, src_interdep='indep',
                 rup_interdep='indep', grp_probability=1.,
                 min_mag={'default': 0}, max_mag=None,
                 temporal_occurrence_model=None, cluster=False):
        # checks
        self.trt = trt
        self.sources = []
        self.name = name
        self.src_interdep = src_interdep
        self.rup_interdep = rup_interdep
        self._check_init_variables(sources, name, src_interdep, rup_interdep)
        self.grp_probability = grp_probability
        self.min_mag = min_mag
        self.max_mag = max_mag
        if sources:
            for src in sorted(sources, key=operator.attrgetter('source_id')):
                self.update(src)
        self.source_model = None  # to be set later, in FullLogicTree
        self.temporal_occurrence_model = temporal_occurrence_model
        self.cluster = cluster
        # check weights in case of mutually exclusive ruptures
        if rup_interdep == 'mutex':
            for src in self.sources:
                assert isinstance(src, NonParametricSeismicSource)
                for rup, _ in src.data:
                    assert rup.weight is not None

    @property
    def grp_id(self):
        """
        The grp_id of the underlying sources
        """
        return self.sources[0].grp_id

    @property
    def trt_smrs(self):
        """
        The trt_smrs of the underlying sources
        """
        return self.sources[0].trt_smrs

    @property
    def tom_name(self):
        """
        :returns: name of the associated temporal occurrence model
        """
        if self.temporal_occurrence_model:
            return self.temporal_occurrence_model.__class__.__name__
        else:
            return 'PoissonTOM'

    @property
    def atomic(self):
        """
        :returns: True if the group cannot be split
        """
        return (self.cluster or self.src_interdep == 'mutex' or
                self.rup_interdep == 'mutex')

    @property
    def weight(self):
        """
        :returns: total weight of the underlying sources
        """
        return sum(src.weight for src in self)

    @property
    def codes(self):
        """
        The codes of the underlying sources as a byte string
        """
        codes = set()
        for src in self.sources:
            codes.add(src.code)
        return b''.join(sorted(codes))

    def _check_init_variables(self, src_list, name,
                              src_interdep, rup_interdep):
        if src_interdep not in ('indep', 'mutex'):
            raise ValueError('source interdependence incorrect %s ' %
                             src_interdep)
        if rup_interdep not in ('indep', 'mutex'):
            raise ValueError('rupture interdependence incorrect %s ' %
                             rup_interdep)
        # check TRT
        if src_list:  # can be None
            for src in src_list:
                assert src.tectonic_region_type == self.trt, (
                    src.tectonic_region_type, self.trt)
                # Mutually exclusive ruptures can only belong to non-parametric
                # sources
                if rup_interdep == 'mutex':
                    if not isinstance(src, NonParametricSeismicSource):
                        msg = "Mutually exclusive ruptures can only be "
                        msg += "modelled using non-parametric sources"
                        raise ValueError(msg)

    def update(self, src):
        """
        Update the attributes sources, min_mag, max_mag
        according to the given source.

        :param src:
            an instance of :class:
            `openquake.hazardlib.source.base.BaseSeismicSource`
        """
        assert src.tectonic_region_type == self.trt, (
            src.tectonic_region_type, self.trt)

        # checking mutex ruptures
        if (not isinstance(src, NonParametricSeismicSource) and
                self.rup_interdep == 'mutex'):
            msg = "Mutually exclusive ruptures can only be "
            msg += "modelled using non-parametric sources"
            raise ValueError(msg)

        self.sources.append(src)
        _, max_mag = src.get_min_max_mag()
        prev_max_mag = self.max_mag
        if prev_max_mag is None or max_mag > prev_max_mag:
            self.max_mag = max_mag

    def get_trt_smr(self):
        """
        :returns: the .trt_smr attribute of the underlying sources
        """
        return self.sources[0].trt_smr

    # not used by the engine
    def count_ruptures(self):
        """
        Set src.num_ruptures on each source in the group
        """
        for src in self:
            src.nsites = 1
            src.num_ruptures = src.count_ruptures()
            print(src.weight)
        return self

    # used only in event_based, where weight = num_ruptures
    def split(self, maxweight):
        """
        Split the group in subgroups with weight <= maxweight, unless it
        it atomic.
        """
        if self.atomic:
            return [self]

        # split multipoint/multifault in advance
        sources = []
        for src in self:
            if src.code in b'MF':
                sources.extend(split_source(src))
            else:
                sources.append(src)
        out = []
        def weight(src):
            if src.code == b'F':  # consider it much heavier
                return src.num_ruptures * 25
            return src.num_ruptures
        for block in block_splitter(sources, maxweight, weight):
            sg = copy.copy(self)
            sg.sources = block
            out.append(sg)
        logging.info('Produced %d subgroup(s) of %s', len(out), self)
        return out

    def get_tom_toml(self, time_span):
        """
        :returns: the TOM as a json string {'PoissonTOM': {'time_span': 50}}
        """
        tom = self.temporal_occurrence_model
        if tom is None:
            return '[PoissonTOM]\ntime_span=%s' % time_span
        dic = {tom.__class__.__name__: vars(tom)}
        return toml.dumps(dic)

    def is_poissonian(self):
        """
        :returns: True if all the sources in the group are poissonian
        """
        tom = getattr(self.sources[0], 'temporal_occurrence_model', None)
        return tom.__class__.__name__ == 'PoissonTOM'

    def __repr__(self):
        return '<%s %s, %d source(s), weight=%d>' % (
            self.__class__.__name__, self.trt, len(self.sources), self.weight)

    def __lt__(self, other):
        """
        Make sure there is a precise ordering of SourceGroup objects.
        Objects with less sources are put first; in case the number
        of sources is the same, use lexicographic ordering on the trts
        """
        num_sources = len(self.sources)
        other_sources = len(other.sources)
        if num_sources == other_sources:
            return self.trt < other.trt
        return num_sources < other_sources

    def __getitem__(self, i):
        return self.sources[i]

    def __iter__(self):
        return iter(self.sources)

    def __len__(self):
        return len(self.sources)


class CompositeSourceModel:
    """
    :param full_lt:
        a :class:`FullLogicTree` instance
    :param src_groups:
        a list of SourceGroups
    :param event_based:
        a flag True for event based calculations, flag otherwise
    """
    def __init__(self, full_lt, src_groups):
        self.src_groups = src_groups
        trts = {sg.trt for sg in src_groups}
        gsim_trts = set(full_lt.gsim_lt.bsetdict)
        if trts < gsim_trts:
            # the bset must be reduced so that `oq show rlz` works
            full_lt.gsim_lt.bsetdict = {
                trt: bset for trt, bset in full_lt.gsim_lt.bsetdict.items()
                if trt in trts}
        self.init(full_lt)

    def init(self, full_lt):
        self.full_lt = full_lt
        self.gsim_lt = full_lt.gsim_lt
        self.source_model_lt = full_lt.source_model_lt
        self.sm_rlzs = full_lt.sm_rlzs

        # initialize the code dictionary
        self.code = {}  # srcid -> code
        for grp_id, sg in enumerate(self.src_groups):
            assert len(sg)  # sanity check
            for src in sg:
                src.grp_id = grp_id
                if src.code != b'P':
                    source_id = basename(src)
                    self.code[source_id] = src.code

    def get_sources(self, smr=None):
        """
        :param smr:
            yields only the sources associated to the given source model
            realization, or all realizations if smr is None (the default).
        """
        srcs = []
        for grp in self.src_groups:
            if smr is not None:
                keep = any(trt_smr % TWO24 == smr for trt_smr in grp.trt_smrs)
                if not keep:
                    continue
            srcs.extend(grp)
        return srcs

    def get_trt_smrs(self):
        """
        :returns: an array of trt_smrs (to be stored as an hdf5.vuint32 array)
        """
        keys = [sg.sources[0].trt_smrs for sg in self.src_groups]
        assert len(keys) < TWO16, len(keys)
        return [numpy.array(trt_smrs, numpy.uint32) for trt_smrs in keys]

    def get_cmakers(self, oq):
        """
        :param oq: the OqParam used to build the CompositeSourceModel
        :returns: a ContextMakerSequence instance
        """
        return get_cmakers(self.get_trt_smrs(), self.full_lt, oq)

    def get_basenames(self):
        """
        :returns: a sorted list of source names stripped of the suffixes
        """
        sources = set()
        for src in self.get_sources():
            sources.add(basename(src, ';:.').split('!')[0])
        return sorted(sources)

    def get_mags_by_trt(self, maximum_distance):
        """
        :param maximum_distance: dictionary trt -> magdist interpolator
        :returns: a dictionary trt -> magnitudes in the sources as strings
        """
        mags = AccumDict(accum=set())  # trt -> mags
        for sg in self.src_groups:
            for src in sg:
                mags[sg.trt].update(src.get_magstrs())
        out = {}
        for trt in mags:
            minmag = maximum_distance(trt).x[0]
            out[trt] = sorted(m for m in mags[trt] if float(m) >= minmag)
        return out

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

    def update_source_info(self, source_data):
        """
        Update (eff_ruptures, num_sites, calc_time) inside the source_info
        """
        if not hasattr(self, 'source_info'):
            self.source_info = self.get_source_info()
        # this is called in preclassical and then in classical
        assert len(source_data) < TWO24, len(source_data)
        for src_id, nctxs, weight, ctimes in python3compat.zip(
                source_data['src_id'], source_data['nctxs'],
                source_data['weight'], source_data['ctimes']):
            baseid = basename(src_id)
            row = self.source_info[baseid]
            row[CALC_TIME] += ctimes
            row[NUM_CTXS] = nctxs

    def count_ruptures(self):
        """
        Call src.count_ruptures() on each source. Slow.
        """
        n = 0
        for src in self.get_sources():
            n += src.count_ruptures()
        return n

    def fix_src_offset(self):
        """
        Set the src.offset field for each source
        """
        src_id = 0
        for srcs in groupby(self.get_sources(), basename).values():
            offset = 0
            if len(srcs) > 1:  # order by split number
                srcs.sort(key=fragmentno)
            for src in srcs:
                src.id = src_id
                src.offset = offset
                if not src.num_ruptures:
                    src.num_ruptures = src.count_ruptures()
                offset += src.num_ruptures
                if src.num_ruptures >= TWO30:
                    raise ValueError(
                        '%s contains more than 2**30 ruptures' % src)
                # print(src, src.offset, offset)
            src_id += 1

    def set_msparams(self):
        """
        Set the `.msparams` attribute on multifault sources, if any
        """
        for src in self.get_sources():
            if src.code == b'F':
                with hdf5.File(src.hdf5path, 'r') as h5:
                    secparams = h5['secparams'][:]
                break
        for src in self.get_sources():
            if src.code == b'F':
                src.set_msparams(secparams)

    def get_msr_by_grp(self):
        """
        :returns: a dictionary grp_id -> MSR string
        """
        acc = AccumDict(accum=set())
        for grp_id, sg in enumerate(self.src_groups):
            for src in sg:
                acc[grp_id].add(msr_name(src))
        return {grp_id: ' '.join(sorted(acc[grp_id])) for grp_id in acc}

    def get_max_weight(self, oq):  # used in preclassical
        """
        :param oq: an OqParam instance
        :returns: total weight and max weight of the sources
        """
        srcs = self.get_sources()
        tot_weight = 0
        nr = 0
        for src in srcs:
            nr += src.num_ruptures
            tot_weight += src.weight
            if src.code == b'C' and src.num_ruptures > 20_000:
                msg = ('{} is suspiciously large, containing {:_d} '
                       'ruptures with complex_fault_mesh_spacing={} km')
                spc = oq.complex_fault_mesh_spacing
                logging.info(msg.format(src, src.num_ruptures, spc))
        assert tot_weight
        max_weight = tot_weight / (oq.concurrent_tasks or 1)
        max_weight *= 1.05  # increased to produce fewer tasks
        logging.info('tot_weight={:_d}, max_weight={:_d}, num_sources={:_d}'.
                     format(int(tot_weight), int(max_weight), len(srcs)))
        return max_weight

    def split(self, cmdict, sitecol, max_weight, num_chunks=1, tiling=False):
        """
        :yields: (cmaker, tilegetters, blocks, splits) for each source group
        """
        grp_ids = numpy.argsort([sg.weight for sg in self.src_groups])[::-1]
        # cmakers is a dictionary label -> array of cmakers
        with_labels = len(cmdict) > 1
        for idx, label in enumerate(cmdict):
            cms = cmdict[label].to_array(grp_ids)
            for cmaker, grp_id in zip(cms, grp_ids):
                sg = self.src_groups[grp_id]
                if sg.weight == 0:
                    # happens in LogicTreeTestCase::test_case_08 since the
                    # point sources are far away as determined in preclassical
                    continue
                if len(cmdict) > 1:  # has labels
                    sites = sitecol.filter(sitecol.ilabel == idx)
                else:
                    sites = sitecol
                if sites:
                    if with_labels:
                        cmaker.ilabel = idx
                    yield self.split_sg(
                        cmaker, sg, sites, max_weight, num_chunks, tiling)

    def split_sg(self, cmaker, sg, sitecol, max_weight,
                 num_chunks=1, tiling=False):
        N = len(sitecol)
        oq = cmaker.oq
        max_mb = float(config.memory.pmap_max_mb)
        mb_per_gsim = oq.imtls.size * N * 4 / 1024**2
        G = len(cmaker.gsims)
        splits = int(numpy.ceil(G * mb_per_gsim / max_mb))
        hint = sg.weight / max_weight
        if sg.atomic or tiling:
            blocks = [sg.grp_id]
            maxhint = max(hint, splits)
            if N / maxhint < oq.max_sites_disagg:
                # in test_JPN there are 3 sites which we don't want to split
                # in that case hint=15.238, splits=1, max_sites_disagg=3
                maxhint = N / oq.max_sites_disagg  # becomes 1
            tilegetters = list(sitecol.split(maxhint))
        else:
            blocks = list(split_in_blocks(sg, hint/1.5, weight))
            tilegetters = list(sitecol.split(splits, oq.max_sites_disagg))
        extra = dict(codes=sg.codes,
                     num_chunks=num_chunks,
                     blocks=len(blocks),
                     weight=sg.weight,
                     atomic=sg.atomic)
        cmaker.gsims = list(cmaker.gsims)  # save data transfer
        return cmaker, tilegetters, blocks, extra

    def get_source_info(self):
        """
        :returns: dict src_id -> row
        """
        data = {}  # src_id -> row
        lens = []
        for srcid, srcs in groupby(self.get_sources(), basename).items():
            src = srcs[0]
            mutex = getattr(src, 'mutex_weight', 0)
            trti = self.full_lt.trti.get(src.tectonic_region_type, 0)
            lens.append(len(src.trt_smrs))
            row = [srcid, src.grp_id, src.code, 0, 0,
                   sum(s.num_ruptures for s in srcs),
                   sum(s.weight for s in srcs),
                   mutex, trti]
            data[srcid] = row
        logging.info('There are %d groups and %d sources with '
                     'len(trt_smrs)=%.2f', len(self.src_groups), len(data),
                     numpy.mean(lens))
        return data

    def __repr__(self):
        """
        Return a string representation of the composite model
        """
        contents = []
        for sg in self.src_groups:
            arr = numpy.array(_strip_colons(sg))
            line = f'grp_id={sg.sources[0].grp_id} {arr}'
            contents.append(line)
        return '<%s\n%s>' % (self.__class__.__name__, '\n'.join(contents))


def _strip_colons(sources):
    ids = set()
    for src in sources:
        if ':' in src.source_id:
            ids.add(src.source_id.split(':')[0])
        else:
            ids.add(src.source_id)
    return sorted(ids)


def get_allargs(csm, cmdict, sitecol, max_weight, num_chunks, tiling):
    """
    Generates task arguments from atomic and non-atomic groups
    """
    out = []
    atomic = []
    allargs = csm.split(cmdict, sitecol, max_weight, num_chunks, tiling)
    for cmaker, tilegetters, blocks, extra in allargs:
        n = len(blocks)
        grp_id = _grp_id(blocks[0])
        if extra['atomic']:
            atomic.append((cmaker, tilegetters, blocks, extra))
        else:
            if n > 1:
                grp_keys = [f'{grp_id}-{b}' for b in range(len(blocks))]
            else:
                grp_keys = [str(grp_id)]
            out.append((cmaker, tilegetters, grp_keys, extra))
    # collect the atomic groups
    blocks_ = AccumDict(accum=[])
    tilegetters_ = {}
    cmaker_ = {}
    for cmaker, tilegetters, blocks, extra in atomic:
        gid = tuple(cmaker.gid)
        tilegetters_[gid] = tilegetters
        blocks_[gid].extend(blocks)
        cmaker_[gid] = cmaker
    extra = dict(atomic=1, blocks=1, num_chunks=extra['num_chunks'])
    for gid, tgetters in tilegetters_.items():
        grp_keys = [str(grp_id) for grp_id in blocks_[gid]]
        out.append((cmaker_[gid], tgetters, grp_keys, extra))
    if atomic:
        logging.info('Collapsed %d atomic tasks into %d',
                     len(atomic), len(cmaker_))
    return out


# ################## read/write utilities ##################### # 

def zpik(obj):
    """
    zip and pickle a python object
    """
    gz = zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL))
    return numpy.frombuffer(gz, numpy.uint8)


def zunpik(data):
    """
    unzip and unpickle some data array
    """
    return pickle.loads(zlib.decompress(data.tobytes())) 


def store_src_groups(hdf5, grp_id, group, num_blocks):
    """
    Store the given source group in block of sources (unless it is
    atomic) and return a list of keys to the generated datasets.
    """
    keys = []
    blocks = numpy.array_split(group, num_blocks)
    if num_blocks == 1:
        key = f"_csm/{grp_id}"
        hdf5[key] = zpik(group)
        keys.append(key)
    else:
        for b, block in enumerate(blocks):
            key = f"_csm/{grp_id}-{b}"
            grp = copy.copy(group)
            grp.sources = block
            hdf5[key] = zpik(grp)
            keys.append(key)
    return keys
            

def read_src_group(hdf5, key, mon=performance.Monitor()):
    """
    Read the source group determined by the key.
    """
    with mon:
        grp = zunpik(hdf5[f"_csm/{key}"][:])
    return grp


def read_src_groups(hdf5, grp_id, mon=performance.Monitor()):
    """
    :yield: the list of subgroups associated to grp_id

    NB: this is a generator to save memory (crucial!)
    """
    grp_str = str(grp_id)
    keys = [key for key in hdf5['_csm'] if key.split('-')[0] == grp_str]
    for key in keys:
        yield read_src_group(hdf5, key, mon)


def read_csm(hdf5, full_lt=None):
    """
    :returns: a CompositeSourceModel instance
    """
    src_groups = []
    for grp_id in range(hdf5['_csm'].attrs['num_src_groups']):
        groups = list(read_src_groups(hdf5, grp_id))
        group = groups[0]
        group.sources = list(group.sources)
        for grp in groups[1:]:
            group.sources.extend(grp.sources)
        src_groups.append(group)
    return CompositeSourceModel(full_lt or hdf5['full_lt'].init(), src_groups)
