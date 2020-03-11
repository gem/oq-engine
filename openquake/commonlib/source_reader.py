# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019, GEM Foundation
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
import copy
import random
import os.path
import pickle
import operator
import logging
import zlib
import numpy

from openquake.baselib import hdf5, parallel, general
from openquake.hazardlib import nrml, sourceconverter, calc
from openquake.commonlib.source import FullLogicTree, CompositeSourceModel


TWO16 = 2 ** 16  # 65,536
source_info_dt = numpy.dtype([
    ('sm_id', numpy.uint16),           # 0
    ('grp_id', numpy.uint16),          # 1
    ('source_id', hdf5.vstr),          # 2
    ('code', (numpy.string_, 1)),      # 3
    ('num_ruptures', numpy.uint32),    # 4
    ('calc_time', numpy.float32),      # 5
    ('num_sites', numpy.float32),      # 6
    ('eff_ruptures', numpy.float32),   # 7
    ('checksum', numpy.uint32),        # 8
    ('wkt', hdf5.vstr),                # 9
])


def random_filtered_sources(sources, srcfilter, seed):
    """
    :param sources: a list of sources
    :param srcfilte: a SourceFilter instance
    :param seed: a random seed
    :returns: an empty list or a list with a single filtered source
    """
    random.seed(seed)
    while sources:
        src = random.choice(sources)
        if srcfilter.get_close_sites(src) is not None:
            return [src]
        sources.remove(src)
    return []


class SourceReader(object):
    """
    :param converter: a SourceConverter instance
    :param smlt_dir: directory where the source model logic tree file is
    :param h5: if any, HDF5 file with datasets sitecol and oqparam
    """
    def __init__(self, converter, smlt_dir, h5=None):
        self.converter = converter
        self.smlt_dir = smlt_dir
        self.__name__ = 'SourceReader'
        if 'OQ_SAMPLE_SOURCES' in os.environ and h5:
            self.srcfilter = calc.filters.SourceFilter(
                h5['sitecol'], h5['oqparam'].maximum_distance)

    def __call__(self, ordinal, path, apply_unc, fname, fileno, monitor):
        src_groups = apply_unc(path, fname, self.converter)
        for i, sg in enumerate(src_groups):
            # sample a source for each group
            if os.environ.get('OQ_SAMPLE_SOURCES'):
                sg.sources = random_filtered_sources(
                    sg.sources, self.srcfilter, i)
            for i, src in enumerate(sg):
                dic = {k: v for k, v in vars(src).items()
                       if k != 'grp_id'}
                src.checksum = zlib.adler32(pickle.dumps(dic, protocol=4))
                src._wkt = src.wkt()
        return dict(src_groups=src_groups, ordinal=ordinal, fileno=fileno)


def get_csm(oq, source_model_lt, gsim_lt, h5=None):
    """
    Build source models from the logic tree and to store
    them inside the `source_info` dataset.
    """
    if oq.pointsource_distance['default'] == {}:
        spinning_off = False
    else:
        spinning_off = sum(oq.pointsource_distance.values()) == 0
    if spinning_off:
        logging.info('Removing nodal plane and hypocenter distributions')
    smlt_dir = os.path.dirname(source_model_lt.filename)
    converter = sourceconverter.SourceConverter(
        oq.investigation_time, oq.rupture_mesh_spacing,
        oq.complex_fault_mesh_spacing, oq.width_of_mfd_bin,
        oq.area_source_discretization, oq.minimum_magnitude,
        not spinning_off, oq.source_id, discard_trts=oq.discard_trts)
    info = FullLogicTree(source_model_lt, gsim_lt)
    groups = [[] for sm_rlz in info.sm_rlzs]
    classical = not oq.is_event_based()
    if oq.is_ucerf():
        sample = .001 if os.environ.get('OQ_SAMPLE_SOURCES') else None
        [grp] = nrml.to_python(oq.inputs["source_model"], converter)
        checksum = 0
        for grp_id, sm_rlz in enumerate(info.sm_rlzs):
            sg = copy.copy(grp)
            groups[grp_id] = [sg]
            src = sg[0].new(sm_rlz.ordinal, sm_rlz.value)  # one source
            src.checksum = src.grp_id = src.id = grp_id
            src.samples = sm_rlz.samples
            if classical:
                # split the sources upfront to improve the task distribution
                sg.sources = []
                for s in src:
                    s.checksum = checksum
                    sg.sources.append(s)
                    checksum += 1
                    if sample:  # consider only the first source
                        break
                sg.sources.extend(src.get_background_sources(sample))
            else:  # event_based, use one source
                sg.sources = [src]
        return _get_csm(info, groups, oq.ses_seed, not classical)

    logging.info('Reading the source model(s) in parallel')
    allargs = []
    fileno = 0
    for rlz in info.sm_rlzs:
        for name in rlz.value.split():
            fname = os.path.abspath(os.path.join(smlt_dir, name))
            allargs.append((rlz.ordinal, rlz.lt_path,
                            source_model_lt.apply_uncertainties, fname,
                            fileno))
            fileno += 1
    # NB: the source models file are often NOT in the shared directory
    # (for instance in oq-engine/demos) so the processpool must be used
    dist = ('no' if os.environ.get('OQ_DISTRIBUTE') == 'no'
            else 'processpool')
    smap = parallel.Starmap(
        SourceReader(converter, smlt_dir, h5),
        allargs, distribute=dist, h5=h5 if h5 else None)
    # NB: h5 is None in logictree_test.py

    # various checks
    changes = 0
    for dic in sorted(smap, key=operator.itemgetter('fileno')):
        eri = dic['ordinal']
        groups[eri].extend(dic['src_groups'])
        for sg in dic['src_groups']:
            changes += sg.changes
        gsim_file = oq.inputs.get('gsim_logic_tree')
        if gsim_file:  # check TRTs
            for src_group in dic['src_groups']:
                if src_group.trt not in gsim_lt.values:
                    raise ValueError(
                        "Found in the source models a tectonic region type %r "
                        "inconsistent with the ones in %r" %
                        (src_group.trt, gsim_file))
    for sm_rlz in info.sm_rlzs:
        # check applyToSources
        source_ids = set(src.source_id for grp in groups[sm_rlz.ordinal]
                         for src in grp)
        for brid, srcids in source_model_lt.info.applytosources.items():
            if brid in sm_rlz.lt_path:
                for srcid in srcids:
                    if srcid not in source_ids:
                        raise ValueError(
                            "The source %s is not in the source model,"
                            " please fix applyToSources in %s or the "
                            "source model" % (srcid, source_model_lt.filename))

    if changes:
        logging.info('Applied %d changes to the composite source model',
                     changes)
    return _get_csm(info, groups, oq.ses_seed, not classical)


def _get_csm(full_lt, groups, ses_seed=0, event_based=False):
    # extract a single source from multiple sources with the same ID
    # and regroup the sources in non-atomic groups by TRT
    atomic = []
    acc = general.AccumDict(accum=[])
    get_grp_id = full_lt.source_model_lt.get_grp_id(full_lt.gsim_lt.values)
    for sm in full_lt.sm_rlzs:
        for grp in groups[sm.ordinal]:
            if grp and grp.atomic:
                atomic.append(grp)
            elif grp:
                acc[grp.trt].extend(grp)
            grp_id = get_grp_id(grp.trt, sm.ordinal)
            for src in grp:
                src.grp_id = grp_id
                if sm.samples > 1:
                    src.samples = sm.samples
    dic = {}
    key = operator.attrgetter('source_id', 'checksum')
    idx = 0
    for trt in acc:
        lst = []
        for srcs in general.groupby(acc[trt], key).values():
            for src in srcs:
                src.id = idx
            idx += 1
            if len(srcs) > 1:  # happens in classical/case_20
                src.grp_id = [s.grp_id for s in srcs]
            lst.append(src)
        dic[trt] = sourceconverter.SourceGroup(trt, lst)
    for ag in atomic:
        for src in ag:
            src.id = idx
            idx += 1
    src_groups = list(dic.values()) + atomic
    if event_based:  # init serials
        serial = ses_seed
        for sg in src_groups:
            for src in sg:
                src.serial = serial
                serial += src.num_ruptures * len(src.grp_ids)
    return CompositeSourceModel(full_lt, src_groups)
