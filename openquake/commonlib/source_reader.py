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
import gzip
import zlib
import numpy

from openquake.baselib import parallel, general, hdf5
from openquake.hazardlib import nrml, sourceconverter, InvalidFile
from openquake.hazardlib.contexts import basename
from openquake.hazardlib.calc.filters import magstr
from openquake.hazardlib.lt import apply_uncertainties

TWO16 = 2 ** 16  # 65,536
by_id = operator.attrgetter('source_id')
CALC_TIME, NUM_SITES, EFF_RUPTURES, WEIGHT = 3, 4, 5, 6

source_info_dt = numpy.dtype([
    ('source_id', hdf5.vstr),          # 0
    ('grp_id', numpy.uint16),          # 1
    ('code', (numpy.string_, 1)),      # 2
    ('calc_time', numpy.float32),      # 3
    ('num_sites', numpy.uint32),       # 4
    ('eff_ruptures', numpy.uint32),    # 5
    ('weight', numpy.float32),         # 6
    ('trti', numpy.uint8),             # 7
])


def create_source_info(csm, source_data, h5):
    """
    Creates source_info, source_wkt, trt_smrs, toms
    """
    data = {}  # src_id -> row
    wkts = []
    lens = []
    for sg in csm.src_groups:
        for src in sg:
            srcid = basename(src)
            trti = csm.full_lt.trti.get(src.tectonic_region_type, -1)
            lens.append(len(src.trt_smrs))
            row = [srcid, src.grp_id, src.code, 0, 0, 0, trti, 0]
            wkts.append(getattr(src, '_wkt', ''))
            data[srcid] = row
            src.id = len(data) - 1

    logging.info('There are %d groups and %d sources with len(trt_smrs)=%.2f',
                 len(csm.src_groups), sum(len(sg) for sg in csm.src_groups),
                 numpy.mean(lens))
    csm.source_info = data  # src_id -> row
    num_srcs = len(csm.source_info)
    # avoid hdf5 damned bug by creating source_info in advance
    h5.create_dataset('source_info',  (num_srcs,), source_info_dt)
    h5['source_info'].attrs['atomic'] = any(
        grp.atomic for grp in csm.src_groups)
    h5['source_wkt'] = numpy.array(wkts, hdf5.vstr)


def trt_smrs(src):
    return tuple(src.trt_smrs)


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
        oq.source_id, discard_trts=oq.discard_trts,
        floating_x_step=oq.floating_x_step,
        floating_y_step=oq.floating_y_step)
    classical = not oq.is_event_based()
    full_lt.ses_seed = oq.ses_seed
    if oq.is_ucerf():
        [grp] = nrml.to_python(oq.inputs["source_model"], converter)
        src_groups = []
        for grp_id, sm_rlz in enumerate(full_lt.sm_rlzs):
            sg = copy.copy(grp)
            src_groups.append(sg)
            src = sg[0].new(sm_rlz.ordinal, sm_rlz.value[0])  # one source
            src.checksum = src.grp_id = src.trt_smr = grp_id
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
    fix_geometry_sections(smdict)
    groups = _build_groups(full_lt, smdict)

    # checking the changes
    changes = sum(sg.changes for sg in groups)
    if changes:
        logging.info('Applied {:_d} changes to the composite source model'.
                     format(changes))
    return _get_csm(full_lt, groups)


def fix_geometry_sections(smdict):
    """
    If there are MultiFaultSources, fix the sections according to the
    GeometryModels (if any).
    """
    gmodels = []
    smodels = []
    for fname, mod in smdict.items():
        if isinstance(mod, nrml.GeometryModel):
            gmodels.append(mod)
        elif isinstance(mod, nrml.SourceModel):
            smodels.append(mod)
        else:
            raise RuntimeError('Unknown model %s' % mod)

    # merge and reorder the sections
    sections = {}
    for gmod in gmodels:
        sections.update(gmod.sections)
    sections = {sid: sections[sid] for sid in sorted(sections)}
    nrml.check_unique(sections)

    # fix the MultiFaultSources
    for smod in smodels:
        for sg in smod.src_groups:
            for src in sg:
                if hasattr(src, 'set_sections'):
                    if not sections:
                        raise RuntimeError('Missing geometryModel files!')
                    src.set_sections(sections)


def _groups_ids(smlt_dir, smdict, fnames):
    # extract the source groups and ids from a sequence of source files
    groups = []
    for fname in fnames:
        fullname = os.path.abspath(os.path.join(smlt_dir, fname))
        groups.extend(smdict[fullname].src_groups)
    return groups, set(src.source_id for grp in groups for src in grp)


def _build_groups(full_lt, smdict):
    # build all the possible source groups from the full logic tree
    smlt_file = full_lt.source_model_lt.filename
    smlt_dir = os.path.dirname(smlt_file)
    groups = []
    for rlz in full_lt.sm_rlzs:
        src_groups, source_ids = _groups_ids(
            smlt_dir, smdict, rlz.value[0].split())
        bset_values = full_lt.source_model_lt.bset_values(rlz.lt_path)
        if bset_values and bset_values[0][0].uncertainty_type == 'extendModel':
            (bset, value), *bset_values = bset_values
            extra, extra_ids = _groups_ids(smlt_dir, smdict, value.split())
            common = source_ids & extra_ids
            if common:
                raise InvalidFile(
                    '%s contains source(s) %s already present in %s' %
                    (value, common, rlz.value))
            src_groups.extend(extra)
        for src_group in src_groups:
            trt_smr = full_lt.get_trt_smr(src_group.trt, rlz.ordinal)
            sg = apply_uncertainties(bset_values, src_group)
            for src in sg:
                src.trt_smr = trt_smr
                if rlz.samples > 1:
                    src.samples = rlz.samples
            groups.append(sg)

        # check applyToSources
        sm_branch = rlz.lt_path[0]
        src_id = full_lt.source_model_lt.info.applytosources[sm_branch]
        for srcid in src_id:
            if srcid not in source_ids:
                raise ValueError(
                    "The source %s is not in the source model,"
                    " please fix applyToSources in %s or the "
                    "source model(s) %s" % (srcid, smlt_file,
                                            rlz.value[0].split()))
    return groups


def reduce_sources(sources_with_same_id):
    """
    :param sources_with_same_id: a list of sources with the same source_id
    :returns: a list of truly unique sources, ordered by trt_smr
    """
    out = []
    for src in sources_with_same_id:
        dic = {k: v for k, v in vars(src).items()
               if k not in 'source_id trt_smr samples'}
        src.checksum = zlib.adler32(pickle.dumps(dic, protocol=4))
    for srcs in general.groupby(
            sources_with_same_id, operator.attrgetter('checksum')).values():
        # duplicate sources: same id, same checksum
        src = srcs[0]
        if len(srcs) > 1:  # happens in classical/case_20
            src.trt_smr = tuple(s.trt_smr for s in srcs)
        else:
            src.trt_smr = src.trt_smr,
        out.append(src)
    out.sort(key=operator.attrgetter('trt_smr'))
    return out


def _get_csm(full_lt, groups):
    # 1. extract a single source from multiple sources with the same ID
    # 2. regroup the sources in non-atomic groups by TRT
    # 3. reorder the sources by source_id
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
        for sources in general.groupby(lst, trt_smrs).values():
            # set ._wkt attribute (for later storage in the source_wkt dataset)
            for src in sources:
                # check on MultiFaultSources and NonParametricSources
                mesh_size = getattr(src, 'mesh_size', 0)
                if mesh_size > 1E6:
                    msg = ('src "{}" has {:_d} underlying meshes with a total '
                           'of {:_d} points!').format(
                               src.source_id, src.count_ruptures(), mesh_size)
                    logging.warning(msg)
                src._wkt = src.wkt()
            src_groups.append(sourceconverter.SourceGroup(trt, sources))
    for ag in atomic:
        for src in ag:
            src._wkt = src.wkt()
    src_groups.extend(atomic)
    _check_dupl_ids(src_groups)
    for sg in src_groups:
        sg.sources.sort(key=operator.attrgetter('source_id'))
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
        for grp_id, sg in enumerate(src_groups):
            assert len(sg)  # sanity check
            for src in sg:
                src.grp_id = grp_id

    def get_trt_smrs(self):
        """
        :returns: an array of trt_smrs (to be stored as an hdf5.vuint32 array)
        """
        keys = [sg.sources[0].trt_smrs for sg in self.src_groups]
        assert len(keys) < TWO16, len(keys)
        return [numpy.array(trt_smrs, numpy.uint32) for trt_smrs in keys]

    def get_sources(self, atomic=None):
        """
        There are 3 options:

        atomic == None => return all the sources (default)
        atomic == True => return all the sources in atomic groups
        atomic == True => return all the sources not in atomic groups
        """
        srcs = []
        for src_group in self.src_groups:
            if atomic is None:  # get all sources
                srcs.extend(src_group)
            elif atomic == src_group.atomic:
                srcs.extend(src_group)
        return srcs

    # used only in calc_by_rlz.py
    def get_groups(self, smr):
        """
        :param smr: effective source model realization ID
        :returns: SourceGroups associated to the given `smr`
        """
        src_groups = []
        for sg in self.src_groups:
            trt_smr = self.full_lt.get_trt_smr(sg.trt, smr)
            src_group = copy.copy(sg)
            src_group.sources = [src for src in sg if trt_smr in src.trt_smrs]
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
                if hasattr(src, 'mags'):  # MultiFaultSource
                    srcmags = {magstr(mag) for mag in src.mags}
                    if hasattr(src, 'source_file'):  # UcerfSource
                        grid_key = "/".join(["Grid", src.ukey["grid_key"]])
                        # for instance Grid/FM0_0_MEANFS_MEANMSR_MeanRates
                        with hdf5.File(src.source_file, "r") as h5:
                            srcmags.update(magstr(mag) for mag in
                                           h5[grid_key + "/Magnitude"][:])
                elif hasattr(src, 'data'):  # nonparametric
                    srcmags = {magstr(item[0].mag) for item in src.data}
                else:
                    srcmags = {magstr(item[0]) for item in
                               src.get_annual_occurrence_rates()}
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

    def update_source_info(self, source_data):
        """
        Update (eff_ruptures, num_sites, calc_time) inside the source_info
        """
        for src_id, nsites, nrupts, weight, ctimes in zip(
                source_data['src_id'], source_data['nsites'],
                source_data['nrupts'], source_data['weight'],
                source_data['ctimes']):
            row = self.source_info[src_id.split(':')[0]]
            row[CALC_TIME] += ctimes
            row[WEIGHT] += weight
            row[EFF_RUPTURES] += nrupts
            row[NUM_SITES] += nsites

    def count_ruptures(self):
        """
        Call src.count_ruptures() on each source. Slow.
        """
        n = 0
        for src in self.get_sources():
            n += src.count_ruptures()
        return n

    def get_max_weight(self, oq):  # used in preclassical
        """
        :param oq: an OqParam instance
        :returns: total weight and max weight of the sources
        """
        srcs = self.get_sources()
        tot_weight = 0
        for src in srcs:
            tot_weight += src.weight
            if src.code == b'C' and src.num_ruptures > 20_000:
                msg = ('{} is suspiciously large, containing {:_d} '
                       'ruptures with complex_fault_mesh_spacing={} km')
                spc = oq.complex_fault_mesh_spacing
                logging.info(msg.format(src, src.num_ruptures, spc))
        assert tot_weight
        max_weight = tot_weight / (oq.concurrent_tasks or 1)
        if parallel.Starmap.num_cores > 64:  # if many cores less tasks
            max_weight *= 1.5
        logging.info('tot_weight={:_d}, max_weight={:_d}, num_sources={:_d}'.
                     format(int(tot_weight), int(max_weight), len(srcs)))
        heavy = [src for src in srcs if src.weight > max_weight]
        for src in sorted(heavy, key=lambda s: s.weight, reverse=True):
            logging.info('%s', src)
        if not heavy:
            maxsrc = max(srcs, key=lambda s: s.weight)
            logging.info('Heaviest: %s', maxsrc)
        return max_weight

    def __toh5__(self):
        data = gzip.compress(pickle.dumps(self, pickle.HIGHEST_PROTOCOL))
        logging.info(f'Storing {general.humansize(len(data))} '
                     'of CompositeSourceModel')
        return numpy.void(data), {}

    def __fromh5__(self, blob, attrs):
        other = pickle.loads(gzip.decompress(blob))
        vars(self).update(vars(other))

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
