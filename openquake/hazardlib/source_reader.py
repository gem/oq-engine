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

import re
import os.path
import pickle
import operator
import logging
import collections
import gzip
import zlib
import numpy

from openquake.baselib import parallel, general, hdf5, python3compat
from openquake.hazardlib import nrml, sourceconverter, InvalidFile
from openquake.hazardlib.contexts import basename
from openquake.hazardlib.lt import apply_uncertainties
from openquake.hazardlib.geo.surface.kite_fault import kite_to_geom

TWO16 = 2 ** 16  # 65,536
TWO24 = 2 ** 24  # 16,777,216
TWO30 = 2 ** 30  # 1,073,741,24
TWO32 = 2 ** 32  # 4,294,967,296
by_id = operator.attrgetter('source_id')

CALC_TIME, NUM_SITES, NUM_RUPTURES, WEIGHT, MUTEX = 3, 4, 5, 6, 7

source_info_dt = numpy.dtype([
    ('source_id', hdf5.vstr),          # 0
    ('grp_id', numpy.uint16),          # 1
    ('code', (numpy.string_, 1)),      # 2
    ('calc_time', numpy.float32),      # 3
    ('num_sites', numpy.uint32),       # 4
    ('num_ruptures', numpy.uint32),    # 5
    ('weight', numpy.float32),         # 6
    ('mutex_weight', numpy.float64),   # 7
    ('trti', numpy.uint8),             # 8
])

checksum = operator.attrgetter('checksum')


def gzpik(obj):
    """
    gzip and pickle a python object
    """
    gz = gzip.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL))
    return numpy.frombuffer(gz, numpy.uint8)


def fragmentno(src):
    "Postfix after :.; as an integer"
    # in disagg/case-12 one has source IDs like 'SL_kerton:665!unseg_z1_m03'
    fragment = re.split('[:.;]', src.source_id, 1)[1]
    fragment = fragment.split('!')[0]  # strip !unseg_z1_m03
    return int(fragment.replace('.', '').replace(';', ''))


def mutex_by_grp(src_groups):
    """
    :returns: a composite array with boolean fields src_mutex, rup_mutex
    """
    lst = []
    for sg in src_groups:
        lst.append((sg.src_interdep == 'mutex', sg.rup_interdep == 'mutex'))
    return numpy.array(lst, [('src_mutex', bool), ('rup_mutex', bool)])


def build_rup_mutex(src_groups):
    """
    :returns: a composite array with fields (grp_id, src_id, rup_id, weight)
    """
    lst = []
    dtlist = [('grp_id', numpy.uint16), ('src_id', numpy.uint32),
              ('rup_id', numpy.int64), ('weight', numpy.float64)]
    for sg in src_groups:
        if sg.rup_interdep == 'mutex':
            for src in sg:
                for i, (rup, _) in enumerate(src.data):
                    lst.append((src.grp_id, src.id, i, rup.weight))
    return numpy.array(lst, dtlist)


def create_source_info(csm, h5):
    """
    Creates source_info, source_wkt, trt_smrs, toms
    """
    data = {}  # src_id -> row
    wkts = []
    lens = []
    for srcid, srcs in general.groupby(
            csm.get_sources(), basename).items():
        src = srcs[0]
        num_ruptures = sum(src.num_ruptures for src in srcs)
        mutex = getattr(src, 'mutex_weight', 0)
        trti = csm.full_lt.trti.get(src.tectonic_region_type, -1)
        if src.code == b'p':
            code = b'p'
        else:
            code = csm.code.get(srcid, b'P')
        lens.append(len(src.trt_smrs))
        row = [srcid, src.grp_id, code, 0, 0, num_ruptures,
               src.weight, mutex, trti]
        wkts.append(getattr(src, '_wkt', ''))
        data[srcid] = row

    logging.info('There are %d groups and %d sources with len(trt_smrs)=%.2f',
                 len(csm.src_groups), len(data), numpy.mean(lens))
    csm.source_info = data  # src_id -> row
    num_srcs = len(csm.source_info)
    # avoid hdf5 damned bug by creating source_info in advance
    h5.create_dataset('source_info',  (num_srcs,), source_info_dt)
    h5['mutex_by_grp'] = mutex_by_grp(csm.src_groups)
    h5['rup_mutex'] = build_rup_mutex(csm.src_groups)
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

# NB: in classical this is called after reduce_sources, so ";" is not
# added if the same source appears multiple times, len(srcs) == 1
def _fix_dupl_ids(src_groups):
    sources = general.AccumDict(accum=[])
    for sg in src_groups:
        for src in sg.sources:
            sources[src.source_id].append(src)
    for src_id, srcs in sources.items():
        if len(srcs) > 1:
            for i, src in enumerate(srcs):
                src.source_id = '%s;%d' % (src.source_id, i)


def get_csm(oq, full_lt, dstore=None):
    """
    Build source models from the logic tree and to store
    them inside the `source_full_lt` dataset.
    """
    converter = sourceconverter.SourceConverter(
        oq.investigation_time, oq.rupture_mesh_spacing,
        oq.complex_fault_mesh_spacing, oq.width_of_mfd_bin,
        oq.area_source_discretization, oq.minimum_magnitude,
        oq.source_id,
        discard_trts=[s.strip() for s in oq.discard_trts.split(',')],
        floating_x_step=oq.floating_x_step,
        floating_y_step=oq.floating_y_step,
        source_nodes=oq.source_nodes,
        infer_occur_rates=oq.infer_occur_rates)
    full_lt.ses_seed = oq.ses_seed
    logging.info('Reading the source model(s) in parallel')

    # NB: the source models file are often NOT in the shared directory
    # (for instance in oq-engine/demos) so the processpool must be used
    dist = ('no' if os.environ.get('OQ_DISTRIBUTE') == 'no'
            else 'processpool')
    # NB: dstore is None in logictree_test.py
    allargs = []
    for fname in full_lt.source_model_lt.info.smpaths:
        allargs.append((fname, converter))
    smdict = parallel.Starmap(read_source_model, allargs, distribute=dist,
                              h5=dstore if dstore else None).reduce()
    smdict = {k: smdict[k] for k in sorted(smdict)}
    parallel.Starmap.shutdown()  # save memory
    fix_geometry_sections(smdict, dstore)

    found = find_false_duplicates(smdict)
    if found:
        logging.warning('Found different sources with same ID %s',
                        general.shortlist(found))

    logging.info('Applying uncertainties')
    groups = _build_groups(full_lt, smdict)

    # checking the changes
    changes = sum(sg.changes for sg in groups)
    if changes:
        logging.info('Applied {:_d} changes to the composite source model'.
                     format(changes))
    is_event_based = oq.calculation_mode.startswith(('event_based', 'ebrisk'))
    csm = _get_csm(full_lt, groups, is_event_based)
    for sg in csm.src_groups:
        if sg.src_interdep == 'mutex' and 'src_mutex' not in dstore:
            dtlist = [('src_id', hdf5.vstr), ('grp_id', int),
                      ('num_ruptures', int), ('mutex_weight', float)]
            out = []
            segments = []
            for src in sg:
                segments.append(int(src.source_id.split(':')[1]))
                t = (src.source_id, src.count_ruptures(),
                     src.grp_id, src.mutex_weight)
                out.append(t)
            assert len(segments) == len(set(segments)), segments
            dstore.create_dset('src_mutex', numpy.array(out, dtlist),
                               fillvalue=None)
    return csm


def add_checksums(srcs):
    """
    Build and attach a checksum to each source
    """
    for src in srcs:
        dic = {k: v for k, v in vars(src).items()
               if k not in 'source_id trt_smr smweight samples fname'}
        src.checksum = zlib.adler32(pickle.dumps(dic, protocol=4))


def find_false_duplicates(smdict):
    """
    Discriminate different sources with same ID (false duplicates)
    and put a question mark in their source ID
    """
    acc = general.AccumDict(accum=[])
    atomic = set()
    for smodel in smdict.values():
        for sgroup in smodel.src_groups:
            for src in sgroup:
                src.fname = os.path.basename(smodel.fname).rsplit('.')[0]
                assert '!' not in src.fname, src.fname
                acc[src.source_id].append(src)
                if sgroup.atomic:
                    atomic.add(src.source_id)
    found = []
    for srcid, srcs in acc.items():
        if len(srcs) > 1:  # duplicated ID
            if any(src.source_id in atomic for src in srcs):
                raise RuntimeError('Sources in atomic groups cannot be '
                                   'duplicated: %s', srcid)
            if any(getattr(src, 'mutex_weight', 0) for src in srcs):
                raise RuntimeError('Mutually exclusive sources cannot be '
                                   'duplicated: %s', srcid)
            add_checksums(srcs)
            gb = general.AccumDict(accum=[])
            for src in srcs:
                gb[checksum(src)].append(src)
            if len(gb) > 1:
                for same_checksum in gb.values():
                    # sources with the same checksum get the same ID
                    for src in same_checksum:
                        src.source_id += '!%s' % src.fname
                found.append(srcid)
    return found


def fix_geometry_sections(smdict, dstore):
    """
    If there are MultiFaultSources, fix the sections according to the
    GeometryModels (if any).
    """
    gmodels = []
    smodels = []
    gfiles = []
    for fname, mod in smdict.items():
        if isinstance(mod, nrml.GeometryModel):
            gmodels.append(mod)
            gfiles.append(fname)
        elif isinstance(mod, nrml.SourceModel):
            smodels.append(mod)
        else:
            raise RuntimeError('Unknown model %s' % mod)

    # merge and reorder the sections
    sec_ids = []
    sections = {}
    for gmod in gmodels:
        sec_ids.extend(gmod.sections)
        sections.update(gmod.sections)
    nrml.check_unique(
        sec_ids, 'section ID in files ' + ' '.join(gfiles))
    s2i = {suid: i for i, suid in enumerate(sections)}
    for idx, sec in enumerate(sections.values()):
        sec.suid = idx
    if sections:
        assert dstore, ('You forgot to pass the dstore to '
                        'get_composite_source_model')
        with hdf5.File(dstore.tempname, 'w') as h5:
            h5.save_vlen('multi_fault_sections',
                         [kite_to_geom(sec) for sec in sections.values()])

    # fix the MultiFaultSources
    section_idxs = []
    for smod in smodels:
        for sg in smod.src_groups:
            for src in sg:
                if hasattr(src, 'set_sections'):
                    if not sections:
                        raise RuntimeError('Missing geometryModel files!')
                    if dstore:
                        src.hdf5path = dstore.tempname
                    src.rupture_idxs = [tuple(s2i[idx] for idx in idxs)
                                        for idxs in src.rupture_idxs]
                    for idxs in src.rupture_idxs:
                        section_idxs.extend(idxs)
    cnt = collections.Counter(section_idxs)
    if cnt:
        mean_counts = numpy.mean(list(cnt.values()))
        logging.info('Section multiplicity = %.1f', mean_counts)


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
    frac = 1. / len(full_lt.sm_rlzs)
    for rlz in full_lt.sm_rlzs:
        src_groups, source_ids = _groups_ids(
            smlt_dir, smdict, rlz.value[0].split())
        bset_values = full_lt.source_model_lt.bset_values(rlz.lt_path)
        while (bset_values and
               bset_values[0][0].uncertainty_type == 'extendModel'):
            (bset, value), *bset_values = bset_values
            extra, extra_ids = _groups_ids(smlt_dir, smdict, value.split())
            common = source_ids & extra_ids
            if common:
                raise InvalidFile(
                    '%s contains source(s) %s already present in %s' %
                    (value, common, rlz.value))
            src_groups.extend(extra)
        for src_group in src_groups:
            sg = apply_uncertainties(bset_values, src_group)
            full_lt.set_trt_smr(sg, smr=rlz.ordinal)
            for src in sg:
                # the smweight is used in event based sampling:
                # see oq-risk-tests etna
                src.smweight = rlz.weight if full_lt.num_samples else frac
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


def reduce_sources(sources_with_same_id, full_lt):
    """
    :param sources_with_same_id: a list of sources with the same source_id
    :returns: a list of truly unique sources, ordered by trt_smr
    """
    out = []
    srcid = sources_with_same_id[0].source_id
    add_checksums(sources_with_same_id)
    for srcs in general.groupby(sources_with_same_id, checksum).values():
        # duplicate sources: same id, same checksum
        src = srcs[0]
        if len(srcs) > 1:  # happens in logictree/case_07
            src.trt_smr = tuple(s.trt_smr for s in srcs)
        else:
            src.trt_smr = src.trt_smr,
        # tup = full_lt.get_trt_smrs(srcid)
        # assert src.trt_smr == tup, (src.trt_smr, tup)
        out.append(src)
    out.sort(key=operator.attrgetter('trt_smr'))
    return out


def _get_csm(full_lt, groups, event_based):
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
            # NB: not reducing the sources in event based
            if len(srcs) > 1 and not event_based:
                srcs = reduce_sources(srcs, full_lt)
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
    _fix_dupl_ids(src_groups)
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
        self.src_groups = src_groups
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

    def get_basenames(self):
        """
        :returns: a sorted list of source names stripped of the suffixes
        """
        sources = set()
        for src in self.get_sources():
            sources.add(basename(src, ';:.'))
        return sorted(sources)

    def get_mags_by_trt(self, maximum_distance):
        """
        :param maximum_distance: dictionary trt -> magdist interpolator
        :returns: a dictionary trt -> magnitudes in the sources as strings
        """
        mags = general.AccumDict(accum=set())  # trt -> mags
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
        assert len(source_data) < TWO24, len(source_data)
        for src_id, nsites, weight, ctimes in python3compat.zip(
                source_data['src_id'], source_data['nsites'],
                source_data['weight'], source_data['ctimes']):
            baseid = basename(src_id)
            row = self.source_info[baseid]
            row[CALC_TIME] += ctimes
            row[WEIGHT] += weight
            row[NUM_SITES] += nsites

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
        for srcs in general.groupby(self.get_sources(), basename).values():
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
        G = len(self.src_groups)
        arr = numpy.zeros(G + 1, hdf5.vuint8)
        for grp_id, grp in enumerate(self.src_groups):
            arr[grp_id] = gzpik(grp)
        arr[G] = gzpik(self.source_info)
        size = sum(len(val) for val in arr)
        logging.info(f'Storing {general.humansize(size)} '
                     'of CompositeSourceModel')
        return arr, {}

    # tested in case_36
    def __fromh5__(self, arr, attrs):
        objs = [pickle.loads(gzip.decompress(a.tobytes())) for a in arr]
        self.src_groups = objs[:-1]
        self.source_info = objs[-1]

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
