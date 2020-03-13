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

from openquake.baselib import parallel, general
from openquake.hazardlib import nrml, sourceconverter, calc
from openquake.commonlib.source import FullLogicTree, CompositeSourceModel


TWO16 = 2 ** 16  # 65,536


def random_filtered_sources(sources, srcfilter, seed):
    """
    :param sources: a list of sources
    :param srcfilter: a SourceFilter instance
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


def read_source_model(fname, converter, srcfilter, monitor):
    """
    :param fname: path to a source model XML file
    :param converter: SourceConverter
    :param srcfilter: None unless OQ_SAMPLE_SOURCES is set
    :param monitor: a Monitor instance
    :returns: a SourceModel instance
    """
    [sm] = nrml.read_source_models([fname], converter)
    if srcfilter:  # if OQ_SAMPLE_SOURCES is set sample the close sources
        for i, sg in enumerate(sm.src_groups):
            sg.sources = random_filtered_sources(sg.sources, srcfilter, i)
    return {fname: sm}


def get_csm(oq, source_model_lt, gsim_lt, h5=None):
    """
    Build source models from the logic tree and to store
    them inside the `source_full_lt` dataset.
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
    full_lt = FullLogicTree(source_model_lt, gsim_lt)
    logging.info('%d effective smlt realization(s)', len(full_lt.sm_rlzs))
    classical = not oq.is_event_based()
    if oq.is_ucerf():
        sample = .001 if os.environ.get('OQ_SAMPLE_SOURCES') else None
        [grp] = nrml.to_python(oq.inputs["source_model"], converter)
        src_groups = []
        for grp_id, sm_rlz in enumerate(full_lt.sm_rlzs):
            sg = copy.copy(grp)
            src_groups.append(sg)
            src = sg[0].new(sm_rlz.ordinal, sm_rlz.value)  # one source
            src.checksum = src.grp_id = src.id = grp_id
            src.samples = sm_rlz.samples
            if classical:
                # split the sources upfront to improve the task distribution
                sg.sources = src.get_background_sources(sample)
                if not sample:
                    for s in src:
                        sg.sources.append(s)
            else:  # event_based, use one source
                sg.sources = [src]
        return CompositeSourceModel(full_lt, src_groups)

    logging.info('Reading the source model(s) in parallel')
    if 'OQ_SAMPLE_SOURCES' in os.environ and h5:
        srcfilter = calc.filters.SourceFilter(
            h5['sitecol'], h5['oqparam'].maximum_distance)
    else:
        srcfilter = None
    groups = []

    # NB: the source models file are often NOT in the shared directory
    # (for instance in oq-engine/demos) so the processpool must be used
    dist = ('no' if os.environ.get('OQ_DISTRIBUTE') == 'no'
            else 'processpool')
    # NB: h5 is None in logictree_test.py
    allargs = []
    for brid, fnames in source_model_lt.info.smpaths.items():
        for fname in fnames:
            allargs.append((fname, converter, srcfilter))
    smdict = parallel.Starmap(read_source_model, allargs, distribute=dist,
                              h5=h5 if h5 else None).reduce()
    if len(smdict) > 1:  # really parallel
        parallel.Starmap.shutdown()  # save memory
    logging.info('Applying logic tree uncertainties')
    for rlz in full_lt.sm_rlzs:
        bset_values = source_model_lt.bset_values(rlz)
        for name in rlz.value.split():
            sm = smdict[os.path.abspath(os.path.join(smlt_dir, name))]
            for src_group in sm.src_groups:
                if bset_values:  # the smlt is complex
                    sg = copy.deepcopy(src_group)
                    source_model_lt.apply_uncertainties(bset_values, sg)
                else:  # the smlt is simple
                    sg = src_group
                groups.append(sg)
                grp_id = source_model_lt.get_grp_id(sg.trt, rlz.ordinal)
                for src in sg:
                    src.grp_id = grp_id
                    if rlz.samples > 1:
                        src.samples = rlz.samples

        # check applyToSources
        '''
        source_ids = set(src.source_id for grp in groups[rlz.ordinal]
                         for src in grp)
        for brid, srcids in source_model_lt.info.applytosources.items():
            if brid in rlz.lt_path:
                for srcid in srcids:
                    if srcid not in source_ids:
                        raise ValueError(
                            "The source %s is not in the source model,"
                            " please fix applyToSources in %s or the "
                            "source model" % (srcid, source_model_lt.filename))
        '''

    # checking the changes
    changes = sum(sg.changes for sg in groups)
    if changes:
        logging.info('Applied %d changes to the composite source model',
                     changes)
    return _get_csm(full_lt, groups)


def reduce_sources(sources_with_same_id):
    """
    :param sources_with_same_id: a list of sources with the same source_id
    :returns: a list of truly unique sources, ordered by grp_id
    """
    out = []
    for src in sources_with_same_id:
        dic = {k: v for k, v in vars(src).items() if k not in 'grp_id samples'}
        src.checksum = zlib.adler32(pickle.dumps(dic, protocol=4))
    for srcs in general.groupby(
            sources_with_same_id, operator.attrgetter('checksum')).values():
        src = srcs[0]
        if len(srcs) > 1:  # happens in classical/case_20
            src.grp_id = tuple(s.grp_id for s in srcs)
        else:
            src.grp_id = src.grp_id,
        out.append(src)
    out.sort(key=operator.attrgetter('grp_id'))
    return out


def _get_csm(full_lt, groups):
    # extract a single source from multiple sources with the same ID
    # and regroup the sources in non-atomic groups by TRT
    atomic = []
    acc = general.AccumDict(accum=[])
    for grp in groups:
        if grp and grp.atomic:
            atomic.append(grp)
        elif grp:
            acc[grp.trt].extend(grp)
    dic = {}
    key = operator.attrgetter('source_id', 'code')
    idx = 0
    for trt in acc:
        lst = []
        for srcs in general.groupby(acc[trt], key).values():
            if len(srcs) > 1:
                srcs = reduce_sources(srcs)
            for src in srcs:
                src.id = idx
                src._wkt = src.wkt()
                idx += 1
                lst.append(src)
        dic[trt] = sourceconverter.SourceGroup(trt, lst)
    for ag in atomic:
        for src in ag:
            src.id = idx
            src._wkt = src.wkt()
            idx += 1
    src_groups = list(dic.values()) + atomic
    return CompositeSourceModel(full_lt, src_groups)
