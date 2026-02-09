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

import time
import zlib
import os.path
import pickle
import operator
import logging
import numpy

from openquake.baselib import parallel, general, hdf5
from openquake.hazardlib import nrml, sourceconverter, InvalidFile, calc
from openquake.hazardlib.source_group import CompositeSourceModel
from openquake.hazardlib.source.multi_fault import save_and_split
from openquake.hazardlib.lt import apply_uncertainties
from openquake.hazardlib.valid import basename

bybranch = operator.attrgetter('branch')
checksum = operator.attrgetter('checksum')
source_info_dt = numpy.dtype([
    ('source_id', hdf5.vstr),          # 0
    ('grp_id', numpy.uint16),          # 1
    ('code', (numpy.bytes_, 1)),       # 2
    ('calc_time', numpy.float32),      # 3
    ('num_sites', numpy.uint64),       # 4
    ('num_ruptures', numpy.uint32),    # 5
    ('weight', numpy.float32),         # 6
    ('mutex_weight', numpy.float64),   # 7
    ('trti', numpy.uint8),             # 8
])


def check_unique(ids, msg='', strict=True):
    """
    Raise a DuplicatedID exception if there are duplicated IDs
    """
    if isinstance(ids, dict):  # ids by key
        all_ids = sum(ids.values(), [])
        unique, counts = numpy.unique(all_ids, return_counts=True)
        for dupl in unique[counts > 1]:
            keys = [k for k in ids if dupl in ids[k]]
            if keys:
                errmsg = '%r appears in %s %s' % (dupl, keys, msg)
                if strict:
                    raise nrml.DuplicatedID(errmsg)
                else:
                    logging.info('*' * 60 + ' DuplicatedID:\n' + errmsg)
        return
    unique, counts = numpy.unique(ids, return_counts=True)
    for u, c in zip(unique, counts):
        if c > 1:
            errmsg = '%r appears %d times %s' % (u, c, msg)
            if strict:
                raise nrml.DuplicatedID(errmsg)
            else:
                logging.info('*' * 60 + ' DuplicatedID:\n' + errmsg)


def create_source_info(csm, h5):
    """
    Creates source_info, trt_smrs, toms
    """
    csm.source_info = csm.get_source_info()
    num_srcs = len(csm.source_info)
    # avoid hdf5 damned bug by creating source_info in advance
    h5.create_dataset('source_info', (num_srcs,), source_info_dt)


def trt_smrs(src):
    return tuple(src.trt_smrs)


def _sample(srcs, sample, applied):
    out = [src for src in srcs if src.source_id in applied]
    rand = general.random_filter(srcs, sample)
    return (out + rand) or [srcs[0]]


def read_source_model(fname, branch, converter, applied, sample, monitor):
    """
    :param fname: path to a source model XML file
    :param branch: source model logic tree branch ID
    :param converter: SourceConverter
    :param applied: list of source IDs within applyToSources
    :param sample: a string with the sampling factor (if any)
    :param monitor: a Monitor instance
    :returns: a SourceModel instance
    """
    t0 = time.time()
    [sm] = nrml.read_source_models([fname], converter)
    sm.branch = branch
    for sg in sm.src_groups:
        if sample and not sg.atomic:
            srcs = []
            for src in sg:
                if src.source_id in applied:
                    srcs.append(src)
                else:
                    srcs.extend(calc.filters.split_source(src))
            sg.sources = _sample(srcs, float(sample), applied)
    sm.rtime = time.time() - t0  # save the read time
    return {fname: sm}


# NB: in classical this is called after reduce_sources, so ";" is not
# added if the same source appears multiple times, len(srcs) == 1
# in event based instead identical sources can appear multiple times
# but will have different seeds and produce different rupture sets
def _fix_dupl_ids(src_groups):
    sources = general.AccumDict(accum=[])
    for sg in src_groups:
        for src in sg.sources:
            sources[src.source_id].append(src)
    for src_id, srcs in sources.items():
        if len(srcs) > 1:
            # happens in logictree/case_01/rup.ini
            for i, src in enumerate(srcs):
                src.source_id = '%s;%d' % (src.source_id, i)


def check_branchID(branchID):
    """
    Forbids invalid characters .:; used in fragmentno
    """
    if '.' in branchID:
        raise InvalidFile('branchID %r contains an invalid "."' % branchID)
    elif ':' in branchID:
        raise InvalidFile('branchID %r contains an invalid ":"' % branchID)
    elif ';' in branchID:
        raise InvalidFile('branchID %r contains an invalid ";"' % branchID)


def check_duplicates(smdict, strict):
    # check_duplicates in the same file
    for sm in smdict.values():
        srcids = []
        for sg in sm.src_groups:
            srcids.extend(src.source_id for src in sg)
            if sg.src_interdep == 'mutex':
                # mutex sources in the same group must have all the same
                # basename, i.e. the colon convention must be used
                basenames = set(map(basename, sg))
                assert len(basenames) == 1, basenames
        check_unique(srcids, 'in ' + sm.fname, strict)

    # check duplicates in different files but in the same branch
    # the problem was discovered in the DOM model
    for branch, sms in general.groupby(smdict.values(), bybranch).items():
        srcids = general.AccumDict(accum=[])
        fnames = []
        for sm in sms:
            if isinstance(sm, nrml.GeometryModel):
                # the section IDs are not checked since they not count
                # as real sources
                continue
            for sg in sm.src_groups:
                srcids[sm.fname].extend(src.source_id for src in sg)
            fnames.append(sm.fname)
        check_unique(srcids, 'in branch %s' % branch, strict=strict)

    found = find_false_duplicates(smdict)
    if found:
        logging.info('Found different sources with same ID %s',
                     general.shortlist(found))


def save_read_times(dstore, source_models):
    """
    Store how many seconds it took to read each source model file
    in a table (fname, rtime)
    """
    dt = [('fname', hdf5.vstr), ('rtime', float)]
    arr = numpy.array([(sm.fname, sm.rtime) for sm in source_models], dt)
    dstore.create_dset('source_model_read_times', arr)


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

    # NB: the source models file must be in the shared directory
    # NB: dstore is None in logictree_test.py
    allargs = []
    sdata = full_lt.source_model_lt.source_data
    allpaths = set(full_lt.source_model_lt.info.smpaths)
    dic = general.group_array(sdata, 'fname')
    smpaths = []
    ss = os.environ.get('OQ_SAMPLE_SOURCES')
    applied = set()
    for srcs in full_lt.source_model_lt.info.applytosources.values():
        applied.update(srcs)
    for fname, rows in dic.items():
        path = os.path.abspath(
            os.path.join(full_lt.source_model_lt.basepath, fname))
        smpaths.append(path)
        allargs.append((path, rows[0]['branch'], converter, applied, ss))
    for path in allpaths - set(smpaths):  # geometry models
        allargs.append((path, '', converter, applied, ss))
    smdict = parallel.Starmap(read_source_model, allargs,
                              h5=dstore if dstore else None).reduce()
    parallel.Starmap.shutdown()  # save memory
    smdict = {k: smdict[k] for k in sorted(smdict)}
    if dstore:
        save_read_times(dstore, smdict.values())
    check_duplicates(smdict, strict=oq.disagg_by_src)

    logging.info('Applying uncertainties')
    groups = _build_groups(full_lt, smdict)

    # checking the changes
    changes = sum(sg.changes for sg in groups)
    if changes:
        logging.info('Applied {:_d} changes to the composite source model'.
                     format(changes))
    is_event_based = oq.calculation_mode.startswith(('event_based', 'ebrisk'))
    csm = _get_csm(full_lt, groups, is_event_based)
    out = []
    probs = []
    for sg in csm.src_groups:
        if sg.src_interdep == 'mutex' and 'src_mutex' not in dstore:
            segments = []
            for src in sg:
                segments.append(src.source_id.split(':')[1])
                t = (src.source_id, src.grp_id,
                     src.count_ruptures(), src.mutex_weight,
                     sg.rup_interdep == 'mutex')
                out.append(t)
            probs.append((src.grp_id, sg.grp_probability))
            assert len(segments) == len(set(segments)), segments
    if out:
        dtlist = [('src_id', hdf5.vstr), ('grp_id', int),
                  ('num_ruptures', int), ('mutex_weight', float),
                  ('rup_mutex', bool)]
        dstore.create_dset('src_mutex', numpy.array(out, dtlist))
        lst = [('grp_id', int), ('probability', float)]
        dstore.create_dset('grp_probability', numpy.array(probs, lst))

    # split multifault sources if there is a single site
    try:
        sitecol = dstore['sitecol']
    except (KeyError, TypeError):  # 'NoneType' object is not subscriptable
        sitecol = None
    else:
        # NB: in AELO we can have multiple vs30 on the same location
        lonlats = set(zip(sitecol.lons, sitecol.lats))
        if len(lonlats) > 1:
            sitecol = None
    # must be called *after* _fix_dupl_ids
    fix_geometry_sections(
        smdict, csm.src_groups, dstore.tempname if dstore else '',
        sitecol if oq.disagg_by_src and oq.use_rates else None)
    return csm


def add_checksums(srcs):
    """
    Build and attach a checksum to each source
    """
    for src in srcs:
        dic = {k: v for k, v in vars(src).items()
               if k not in 'source_id trt_smr smweight samples branch'}
        src.checksum = zlib.adler32(pickle.dumps(dic, protocol=4))


# called before _fix_dupl_ids
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
                src.branch = smodel.branch
                srcid = (src.source_id if sgroup.atomic
                         else basename(src))
                acc[srcid].append(src)
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
                    for src in same_checksum:
                        check_branchID(src.branch)
                        src.source_id += '!%s' % src.branch
                found.append(srcid)
    return found


def replace(lst, splitdic, key):
    """
    Replace a list of named elements with the split elements in splitdic
    """
    new = []
    for el in lst:
        tag = getattr(el, key)
        if tag in splitdic:
            new.extend(splitdic[tag])
        else:
            new.append(el)
    lst[:] = new


def fix_geometry_sections(smdict, src_groups, hdf5path='', site1=None):
    """
    If there are MultiFaultSources, fix the sections according to the
    GeometryModels (if any).
    """
    gmodels = []
    gfiles = []
    for fname, mod in smdict.items():
        if isinstance(mod, nrml.GeometryModel):
            gmodels.append(mod)
            gfiles.append(fname)

    # merge and reorder the sections
    sec_ids = []
    sections = {}
    for gmod in gmodels:
        sec_ids.extend(gmod.sections)
        sections.update(gmod.sections)
    check_unique(sec_ids, 'section ID in files ' + ' '.join(gfiles))

    if sections:
        # save in the temporary file sources and sections
        assert hdf5path, ('You forgot to pass the dstore to '
                          'get_composite_source_model')
        mfsources = []
        for sg in src_groups:
            for src in sg:
                if src.code == b'F':
                    mfsources.append(src)
        if mfsources:
            split_dic, secparams = save_and_split(
                mfsources, sections, hdf5path, site1)
            for sg in src_groups:
                replace(sg.sources, split_dic, 'source_id')
            return secparams
    return ()


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
            (_bset, value), *bset_values = bset_values
            extra, extra_ids = _groups_ids(smlt_dir, smdict, value.split())
            common = source_ids & extra_ids
            if common:
                raise InvalidFile(
                    '%s contains source(s) %s already present in %s' %
                    (value, common, rlz.value))
            src_groups.extend(extra)
        for src_group in src_groups:
            # an example of bsetvalues is in LogicTreeCase2ClassicalPSHA:
            # (<abGRAbsolute(3, applyToSources=['first'])>, (4.6, 1.1))
            # (<abGRAbsolute(3, applyToSources=['second'])>, (3.3, 1.0))
            # (<maxMagGRAbsolute(3, applyToSources=['first'])>, 7.0)
            # (<maxMagGRAbsolute(3, applyToSources=['second'])>, 7.5)
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
    add_checksums(sources_with_same_id)
    for srcs in general.groupby(sources_with_same_id, checksum).values():
        # duplicate sources: same id, same checksum
        src = srcs[0]
        if len(srcs) > 1:  # happens in logictree/case_07
            src.trt_smr = tuple(s.trt_smr for s in srcs)
        else:
            src.trt_smr = src.trt_smr,
        out.append(src)
    out.sort(key=operator.attrgetter('trt_smr'))
    return out


def split_by_tom(sources):
    """
    Groups together sources with the same TOM
    """
    def key(src):
        tom = getattr(src, 'temporal_occurrence_model', None)
        return tom.__class__.__name__
    return general.groupby(sources, key).values()


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
            for grp in split_by_tom(sources):
                src_groups.append(sourceconverter.SourceGroup(trt, grp))
    src_groups.extend(atomic)
    _fix_dupl_ids(src_groups)

    # sort by source_id
    for sg in src_groups:
        sg.sources.sort(key=operator.attrgetter('source_id'))
    return CompositeSourceModel(full_lt, src_groups)
