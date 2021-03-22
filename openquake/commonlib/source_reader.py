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
import os.path
import pickle
import operator
import logging
import zlib
import numpy

from openquake.baselib import parallel, general
from openquake.hazardlib import nrml, sourceconverter, InvalidFile
from openquake.hazardlib.lt import apply_uncertainties

TWO16 = 2 ** 16  # 65,536
by_id = operator.attrgetter('source_id')

CALC_TIME, NUM_SITES, EFF_RUPTURES, TASK_NO = 3, 4, 5, 7


def et_ids(src):
    return tuple(src.et_ids)


def read_source_model(fname, converter, monitor):
    """
    :param fname: path to a source model XML file
    :param converter: SourceConverter
    :param monitor: a Monitor instance
    :returns: a SourceModel instance
    """
    [sm] = nrml.read_source_models([fname], converter)
    return {fname: sm}


# NB: called after the .checksum has been stored in reduce_sources
def _check_dupl_ids(src_groups):
    sources = general.AccumDict(accum=[])
    for sg in src_groups:
        for src in sg.sources:
            sources[src.source_id].append(src)
    first = True
    for src_id, srcs in sources.items():
        if len(srcs) > 1:
            # duplicate IDs with different checksums, see cases 11, 13, 20
            for i, src in enumerate(srcs):
                src.source_id = '%s;%d' % (src.source_id, i)
            if first:
                logging.info('There are multiple different sources with '
                             'the same ID %s', srcs)
                first = False


def get_csm(oq, full_lt, h5=None):
    """
    Build source models from the logic tree and to store
    them inside the `source_full_lt` dataset.
    """
    converter = sourceconverter.SourceConverter(
        oq.investigation_time, oq.rupture_mesh_spacing,
        oq.complex_fault_mesh_spacing, oq.width_of_mfd_bin,
        oq.area_source_discretization, oq.minimum_magnitude,
        oq.source_id, discard_trts=oq.discard_trts)
    classical = not oq.is_event_based()
    full_lt.ses_seed = oq.ses_seed
    if oq.is_ucerf():
        [grp] = nrml.to_python(oq.inputs["source_model"], converter)
        src_groups = []
        for et_id, sm_rlz in enumerate(full_lt.sm_rlzs):
            sg = copy.copy(grp)
            src_groups.append(sg)
            src = sg[0].new(sm_rlz.ordinal, sm_rlz.value)  # one source
            src.checksum = src.et_id = src.id = et_id
            src.samples = sm_rlz.samples
            logging.info('Reading sections and rupture planes for %s', src)
            planes = src.get_planes()
            if classical:
                src.ruptures_per_block = oq.ruptures_per_block
                sg.sources = list(src)
                for s in sg:
                    s.planes = planes
                    s.sections = s.get_sections()
                # add background point sources
                sg = copy.copy(grp)
                src_groups.append(sg)
                sg.sources = src.get_background_sources()
            else:  # event_based, use one source
                sg.sources = [src]
                src.planes = planes
                src.sections = src.get_sections()
        return CompositeSourceModel(full_lt, src_groups)

    logging.info('Reading the source model(s) in parallel')

    # NB: the source models file are often NOT in the shared directory
    # (for instance in oq-engine/demos) so the processpool must be used
    dist = ('no' if os.environ.get('OQ_DISTRIBUTE') == 'no'
            else 'processpool')
    # NB: h5 is None in logictree_test.py
    allargs = []
    for fname in full_lt.source_model_lt.info.smpaths:
        allargs.append((fname, converter))
    smdict = parallel.Starmap(read_source_model, allargs, distribute=dist,
                              h5=h5 if h5 else None).reduce()
    if len(smdict) > 1:  # really parallel
        parallel.Starmap.shutdown()  # save memory
    groups = _build_groups(full_lt, smdict)

    # checking the changes
    changes = sum(sg.changes for sg in groups)
    if changes:
        logging.info('Applied %d changes to the composite source model',
                     changes)
    return _get_csm(full_lt, groups)


def _build_groups(full_lt, smdict):
    # build all the possible source groups from the full logic tree
    smlt_file = full_lt.source_model_lt.filename
    smlt_dir = os.path.dirname(smlt_file)

    def _groups_ids(value):
        # extract the source groups and ids from a sequence of source files
        groups = []
        for name in value.split():
            fname = os.path.abspath(os.path.join(smlt_dir, name))
            groups.extend(smdict[fname].src_groups)
        return groups, set(src.source_id for grp in groups for src in grp)

    groups = []
    for rlz in full_lt.sm_rlzs:
        src_groups, source_ids = _groups_ids(rlz.value)
        bset_values = full_lt.source_model_lt.bset_values(rlz)
        if bset_values and bset_values[0][0].uncertainty_type == 'extendModel':
            (bset, value), *bset_values = bset_values
            extra, extra_ids = _groups_ids(value)
            common = source_ids & extra_ids
            if common:
                raise InvalidFile(
                    '%s contains source(s) %s already present in %s' %
                    (value, common, rlz.value))
            src_groups.extend(extra)
        for src_group in src_groups:
            et_id = full_lt.get_et_id(src_group.trt, rlz.ordinal)
            sg = apply_uncertainties(bset_values, src_group)
            for src in sg:
                src.et_id = et_id
                if rlz.samples > 1:
                    src.samples = rlz.samples
            groups.append(sg)

        # check applyToSources
        sm_branch = rlz.lt_path[0]
        srcids = full_lt.source_model_lt.info.applytosources[sm_branch]
        for srcid in srcids:
            if srcid not in source_ids:
                raise ValueError(
                    "The source %s is not in the source model,"
                    " please fix applyToSources in %s or the "
                    "source model(s) %s" % (srcid, smlt_file,
                                            rlz.value.split()))
    return groups


def reduce_sources(sources_with_same_id):
    """
    :param sources_with_same_id: a list of sources with the same source_id
    :returns: a list of truly unique sources, ordered by et_id
    """
    out = []
    for src in sources_with_same_id:
        dic = {k: v for k, v in vars(src).items()
               if k not in 'source_id et_id samples'}
        src.checksum = zlib.adler32(pickle.dumps(dic, protocol=4))
    for srcs in general.groupby(
            sources_with_same_id, operator.attrgetter('checksum')).values():
        # duplicate sources: same id, same checksum
        src = srcs[0]
        if len(srcs) > 1:  # happens in classical/case_20
            src.et_id = tuple(s.et_id for s in srcs)
        else:
            src.et_id = src.et_id,
        out.append(src)
    out.sort(key=operator.attrgetter('et_id'))
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
    key = operator.attrgetter('source_id', 'code')
    src_groups = []
    for trt in acc:
        lst = []
        for srcs in general.groupby(acc[trt], key).values():
            if len(srcs) > 1:
                srcs = reduce_sources(srcs)
            lst.extend(srcs)
        for sources in general.groupby(lst, et_ids).values():
            # check if OQ_SAMPLE_SOURCES is set
            ss = os.environ.get('OQ_SAMPLE_SOURCES')
            if ss:
                logging.info('Reducing the number of sources for %s', trt)
                split = []
                for src in sources:
                    for s in src:
                        s.et_id = src.et_id
                        split.append(s)
                sources = general.random_filter(split, float(ss)) or split[0]
            # set ._wkt attribute (for later storage in the source_wkt dataset)
            for src in sources:
                src._wkt = src.wkt()
            src_groups.append(sourceconverter.SourceGroup(trt, sources))
    for ag in atomic:
        for src in ag:
            src._wkt = src.wkt()
    src_groups.extend(atomic)
    _check_dupl_ids(src_groups)
    return CompositeSourceModel(full_lt, src_groups)


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
        self.gsim_lt = full_lt.gsim_lt
        self.source_model_lt = full_lt.source_model_lt
        self.sm_rlzs = full_lt.sm_rlzs
        self.full_lt = full_lt
        self.src_groups = src_groups
        idx = 0
        for grp_id, sg in enumerate(src_groups):
            assert len(sg)  # sanity check
            for src in sg:
                src.id = idx
                src.grp_id = grp_id
                idx += 1

    def get_et_ids(self):
        """
        :returns: an array of et_ids (to be stored as an hdf5.vuint32 array)
        """
        keys = [sg.sources[0].et_ids for sg in self.src_groups]
        assert len(keys) < TWO16, len(keys)
        return [numpy.array(et_ids, numpy.uint32) for et_ids in keys]

    def get_sources(self, atomic=None):
        """
        :returns: list of sources in the composite source model
        """
        srcs = []
        for src_group in self.src_groups:
            if atomic is None:  # get all sources
                srcs.extend(src_group)
            elif atomic == src_group.atomic:
                srcs.extend(src_group)
        return srcs

    # used only in calc_by_rlz.py
    def get_groups(self, eri):
        """
        :param eri: effective source model realization ID
        :returns: SourceGroups associated to the given `eri`
        """
        src_groups = []
        for sg in self.src_groups:
            et_id = self.full_lt.get_et_id(sg.trt, eri)
            src_group = copy.copy(sg)
            src_group.sources = [src for src in sg if et_id in src.et_ids]
            if len(src_group):
                src_groups.append(src_group)
        return src_groups

    def get_mags_by_trt(self):
        """
        :returns: a dictionary trt -> magnitudes in the sources as strings
        """
        mags = general.AccumDict(accum=set())  # trt -> mags
        for sg in self.src_groups:
            for src in sg:
                if hasattr(src, 'mags'):  # UCERF
                    srcmags = ['%.2f' % mag for mag in numpy.unique(
                        numpy.round(src.mags, 2))]
                elif hasattr(src, 'data'):  # nonparametric
                    srcmags = ['%.2f' % item[0].mag for item in src.data]
                else:
                    srcmags = ['%.2f' % item[0] for item in
                               src.get_annual_occurrence_rates()]
                mags[sg.trt].update(srcmags)
        return {trt: sorted(mags[trt]) for trt in mags}

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

    def update_source_info(self, calc_times, nsites=False):
        """
        Update (eff_ruptures, num_sites, calc_time) inside the source_info
        """
        for src_id, arr in calc_times.items():
            row = self.source_info[src_id]
            row[CALC_TIME] += arr[2]
            if len(arr) == 4:  # after preclassical
                row[TASK_NO] = arr[3]
            if nsites:
                row[EFF_RUPTURES] += arr[0]
                row[NUM_SITES] += arr[1]

    def count_ruptures(self):
        """
        Call src.count_ruptures() on each source. Slow.
        """
        n = 0
        for src in self.get_sources():
            n += src.count_ruptures()
        return n

    def __repr__(self):
        """
        Return a string representation of the composite model
        """
        contents = []
        for sg in self.src_groups:
            arr = numpy.array([src.source_id for src in sg])
            line = f'grp_id={sg.sources[0].grp_id} {arr}'
            contents.append(line)
        return '<%s\n%s>' % (self.__class__.__name__, '\n'.join(contents))
