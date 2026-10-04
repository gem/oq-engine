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
import copy
import os.path
import pickle
import operator
import logging
import numpy

from openquake.baselib import parallel, performance, general, hdf5
from openquake.hazardlib import (
    geo, nrml, source, sourceconverter, InvalidFile, calc)
from openquake.hazardlib.source_group import (
    CompositeSourceModel, SourceGroup, get_unique)
from openquake.hazardlib.source.multi_fault import save_and_split
from openquake.hazardlib.lt import (
    apply_uncertainties, check_correlated, get_bset_value,
    restrict_sampling, sampling_dt, unc_subsets)
from openquake.hazardlib.contexts import get_unique_inverse
from openquake.hazardlib.valid import basename

TWO24 = 2**24
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
bybranch = operator.attrgetter('branch')
checksum = operator.attrgetter('checksum')

source_info_dt = numpy.dtype([
    ('source_id', hdf5.vstr),          # 0
    ('grp_id', U16),                   # 1
    ('code', (numpy.bytes_, 1)),       # 2
    ('calc_time', F32),                # 3
    ('num_ctxs', numpy.uint64),        # 4
    ('est_ctxs', numpy.uint64),        # 5
    ('num_ruptures', U32),             # 6
    ('weight', F32),                   # 7
    ('mul', U16),                      # 8
])


def sampling(samples, trt_smr):
    """
    :returns: a structured array (trt_smr, samples) of length 1
    """
    return numpy.array([(trt_smr, samples)], sampling_dt)


# NB: blocksize is chosen so that event_based/case_35 works
def splitMF(sources, disagg_by_src, blocksize=1000):
    """
    Split the MultiPointSources to avoid oceanic sources with 160M ruptures
    hanging during rupture sampling
    """    
    splits = []
    for src in sources:
        if src.code == b'M' and len(src) > blocksize:
            for i, slc in enumerate(general.gen_slices(0, len(src), blocksize)):
                segment = source.MultiPointSource(
                    source_id=f'{src.source_id}:{i}',
                    name=src.name,
                    tectonic_region_type=src.tectonic_region_type,
                    mfd=src.mfd[slc],
                    magnitude_scaling_relationship=(
                        src.magnitude_scaling_relationship),
                    rupture_aspect_ratio=src.rupture_aspect_ratio,
                    upper_seismogenic_depth=src.upper_seismogenic_depth,
                    lower_seismogenic_depth=src.lower_seismogenic_depth,
                    nodal_plane_distribution=src.nodal_plane_distribution,
                    hypocenter_distribution=src.hypocenter_distribution,
                    mesh=geo.Mesh(src.mesh.lons[slc], src.mesh.lats[slc]),
                    temporal_occurrence_model=src.temporal_occurrence_model)
                segment.sampling = src.sampling
                splits.append(segment)
        elif src.code == b'F' and not disagg_by_src:
            # use the colon convention only in absence of kendra-splitting
            for segment in src:
                segment.sampling = src.sampling
                splits.append(segment)
        else:
            splits.append(src)
    sources[:] = splits


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
            if srcs:
                kept = [src for src in srcs if src.source_id in applied]
                rand = general.random_filter(srcs, float(sample))
                sg.sources = (kept + rand) or [srcs[0]]
            else:
                sg.sources = []
    sm.rtime = time.time() - t0  # save the read time
    return {fname: sm}


# NB:this is called after reduce_sources, so ";" is not added
# if the same source appears multiple times, i.e. len(srcs) == 1
def add_semicolons(src_groups):
    """
    Add semicolons to differentiate different sources with the same source_id
    and then sort the sources in each group by extended source_id
    """
    sources = general.AccumDict(accum=[])
    for sg in src_groups:
        for src in sg:
            sources[src.source_id].append(src)
    for src_id, srcs in sources.items():
        srcs = get_unique(srcs)
        if len(srcs) > 1:
            # happens in logictree/case_01/rup.ini
            for i, src in enumerate(srcs):
                src.source_id = '%s;%d' % (src.source_id, i)
    for sg in src_groups:
        sg.sources.sort(key=operator.attrgetter('source_id'))
    # tested in logictree/case_05 with 9 variations of
    # AreaSource 1 and SimpleFaultSource 2


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
    Build a CompositeSourceModel without applying the uncertainties,
    that are applied in the workers, see modified_groups.
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
        infer_occur_rates=oq.infer_occur_rates,
        filter_sourcecodes=oq.filter_sourcecodes)
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
    found = add_bangs(smdict)
    if found:
        logging.info('Found different sources with same ID %s',
                     general.shortlist(found))

    # checking ps_grid_spacing
    pointlike_sources = 0
    for sm in smdict.values():
        for sg in sm.src_groups:
            for src in sg:
                if src.code in b'PAM':
                    pointlike_sources += 1
                    break
    if (oq.strict and oq.mosaic_model and pointlike_sources and
        'classical' in oq.calculation_mode and oq.ps_grid_spacing == 0
        and not oq.sites and not oq.disagg_by_src):
        raise InvalidFile(f'{oq.inputs["job_ini"]}: '
                          'missing ps_grid_spacing')

    return build_csm(oq, full_lt, smdict, dstore)


def get_bset_values(full_lt, sources):
    """
    :param full_lt: a FullLogicTree instance
    :param sources: a SourceGroup or a list of sources of the same group
    :returns: the dictionary of uncertainties to apply expected by
        modified_groups, i.e. one entry for each set of realizations
        with the same uncertainties; the uncertainties of a set are the
        ones of its first realization

    NB: only the uncertainties relevant for the given sources are
        returned, since the logic tree can be huge and the dictionary is
        sent to the workers
    """
    ordinals = {trt_smrs[0] % TWO24 for src in sources
                for trt_smrs in unc_subsets(src)}
    return {ordinal: full_lt.get_bset_values(ordinal)
            for ordinal in sorted(ordinals)}


def modified_groups(sources, bset_values):
    """
    Apply the uncertainties to a group of sources built *without* them,
    as needed by the workers computing the rates or the ruptures: this
    is done one set of realizations at a time, i.e. one set with the
    same uncertainties at a time (see build_groups).

    :param sources: a SourceGroup or a list of sources of the same group
    :param bset_values:
        the uncertainties to apply, as returned by get_bset_values; it
        can be empty, if there are no uncertainties at all
    :returns:
        a generator of (trt_smrs, group) pairs, one for each set of
        realizations with the same uncertainties, with the uncertainties
        applied and the sampling restricted to the set of realizations
    """
    for trt_smrs, srcs in _subsets_by_unc(sources).items():
        grp = _restricted_group(sources, srcs, trt_smrs)
        # NB: the trt_smrs are trti * TWO24 + ordinal, see gen_groups
        bvals = bset_values[trt_smrs[0] % TWO24] if bset_values else []
        # NB: check=False since the group is a fragment of the original
        # one (split by weight in the preclassical), so the correlated
        # branchsets were already checked at build time, see build_groups
        grp = apply_uncertainties(bvals, grp, check=False)
        for src in grp:
            # the sources are modified after the preclassical, so the
            # cached geometry must be discarded; it depends on the
            # occurrence rates (see PointSource.
            # _get_max_rupture_projection_radius)
            if hasattr(src, 'radius'):
                del src.radius
        yield trt_smrs, grp


def _subsets_by_unc(sources):
    """
    :returns: a dictionary trt_smrs -> sources, i.e. the sources grouped
        by set of realizations with the same uncertainties
    """
    if getattr(sources, 'atomic', False):
        # the sources of an atomic group are mutually exclusive (or belong
        # to a cluster), so they must be kept together, see sample_cluster
        # and cmakers_groups; the sets of realizations are the same for
        # all of them, since they belong to the same source model
        return {trt_smrs: list(sources)
                for trt_smrs in unc_subsets(sources[0])}
    subsets = {}
    for src in sources:
        for trt_smrs in unc_subsets(src):
            subsets.setdefault(trt_smrs, []).append(src)
    return subsets


def _restricted_group(sources, srcs, trt_smrs):
    """
    :returns: a group with the given sources, i.e. copies of the sources
        of `sources` with the sampling restricted to trt_smrs
    """
    restricted = [restrict_sampling(src, trt_smrs) for src in srcs]
    if hasattr(sources, 'sources'):  # keep the attributes of the group
        grp = copy.copy(sources)
        grp.sources = restricted
    else:  # a plain list of sources, e.g. a block of sources
        grp = SourceGroup(sources[0].tectonic_region_type, restricted)
    return grp


def unc_signature(bset_values, src):
    """
    :returns: a tuple identifying the uncertainties applied to src
    """
    sig = []
    for bset, value in bset_values:
        ok, val = get_bset_value(bset, value, src)
        if ok:
            sig.append((bset.id, str(val)))
    return tuple(sig)


def build_groups(full_lt, rlz_groups, oq):
    """
    Build the source groups without applying the uncertainties, as needed
    by the workers. There is one group per source group in the source
    model files, as expected in a CompositeSourceModel, and the
    sources keep the trt_smrs of all the realizations they belong to (i.e.
    the full trt_smrs of their group), not just the ones with a given set
    of uncertainties: this way the number of groups (and of associated
    cmakers) depends on the source models only and not on the
    uncertainties.

    The uncertainties to be applied in each realization are not known
    until the workers, so the realizations with different uncertainties
    are stored in the bysrc_subsets attribute of each source (see
    unc_subsets), and the rates are computed and attributed one set at a
    time.

    NB: the same source_id can be used by different sources, i.e. in
    different source models, so the sources are keyed by id(src) and not
    by source_id; the ids are disambiguated at the end, by adding a
    semicolon, see add_semicolons
    """
    dic = {}  # id(grp) -> [group, {id(src): (src, [(trt_smr, samples, sig)])}]
    for rlz, grp in rlz_groups:
        trti = full_lt.trti.get(grp.trt, 0)
        trt_smr = trti * TWO24 + rlz.ordinal
        bset_values = full_lt.get_bset_values(rlz.ordinal)
        # NB: the uncertainties are applied later, in the workers, on
        # groups split by weight, so the correlated branchsets are checked
        # here, where the groups are still whole
        check_correlated(bset_values, grp)
        # NB: the sources are collected by id(grp), since the group objects
        # are shared by all the realizations selecting the same source model
        # file (see gen_groups); the groups built from them are then merged
        # by trt_smrs below. The dicts preserve the order of first
        # appearance, making the groups and the sources inside them
        # reproducible.
        srcs = dic.setdefault(id(grp), [grp, {}])[1]
        for src in grp:
            sig = unc_signature(bset_values, src)
            pairs = srcs.setdefault(id(src), (src, []))[1]
            pairs.append((trt_smr, rlz.samples, sig))

    out, atomic, acc = [], [], general.AccumDict(accum=[])
    for grp, srcs in dic.values():
        new_srcs = []
        for src, pairs in srcs.values():
            arrays, sigdict = [], {}
            for trt_smr, samples, sig in pairs:
                arrays.append((trt_smr, samples))
                sigdict.setdefault(sig, []).append(trt_smr)
            new_src = copy.copy(src)
            new_src.sampling = numpy.array(
                sorted(arrays), sampling_dt)  # sorted by trt_smr
            # NB: the subsets are stored only if the uncertainties are not
            # the same in all the realizations; a source with no
            # uncertainties (or with the same uncertainties everywhere)
            # keeps its sampling as it is
            new_src.bysrc_subsets = [
                numpy.array(sorted(t), U32) for t in sigdict.values()
                ] if len(sigdict) > 1 else []
            # flag the sources which will be modified in the workers:
            # they must not be split in the preclassical, since the
            # splitting destroys the geometry (and the MFD of the fault
            # sources)
            new_src.bysrc_unc = any(sigdict)  # NB: () means no uncertainty
            new_srcs.append(new_src)
        if grp.atomic:
            # the atomic groups are never merged with the other groups,
            # since their sources must be computed together
            new = copy.copy(grp)
            new.sources = new_srcs
            atomic.append(new)
        else:
            acc[grp.trt].extend(new_srcs)
    if atomic:
        logging.info('Found %d atomic groups', len(atomic))
    # NB: the sources are grouped by trt_smrs and TOM, so that there is
    # one cmaker for each set of realizations, see get_cmakers
    red_sources = 0
    for trt, sources in acc.items():
        grps, red = _group_sources(trt, sources)
        out.extend(grps)
        red_sources += red
    if red_sources:
        logging.info('reduce_sources was called %d times', red_sources)
    out.extend(atomic)
    for grp in out:
        splitMF(grp.sources, oq.disagg_by_src)
    add_semicolons(out)  # else sources with the same id are lost
    return out


def get_trt_smrs_gid(csm):
    """
    :param csm: a CompositeSourceModel built without applying the
        uncertainties
    :returns: a sorted list of trt_smrs, the indices of rate attribution
        (to be stored as an hdf5.vuint32 array)

    The uncertainties are applied in the workers, so the realizations
    with different uncertainties are not separated at build time (see
    build_groups). The rates are nevertheless computed separately for each
    set of uncertainties and must be attributed to the right
    realizations, hence this extra list; the gid of a rate is the index
    of its trt_smrs in it.
    """
    all_trt_smrs = [trt_smrs for sg in csm.src_groups for src in sg
                    for trt_smrs in unc_subsets(src)]
    unique, _ = get_unique_inverse(all_trt_smrs)
    return [numpy.array(trt_smrs, numpy.uint32) for trt_smrs in unique]


def read_trt_smrs_gid(dstore):
    """
    :param dstore: a DataStore instance, possibly closed
    :returns: the units of rate attribution stored by the preclassical,
        i.e. the sets of realizations with the same uncertainties, as a
        list of tuples (the inverse of get_trt_smrs_gid)
    """
    with dstore:  # NB: the datastore is closed when passed to a task
        return [tuple(t) for t in dstore['trt_smrs_gid'][:]]


def build_csm(oq, full_lt, smdict, dstore):
    """
    :param oq: OqParam instance
    :param full_lt: FullLogicTree instance
    :param smdict: dictionary source_model_path -> SourceModel instance
    :param dstore: DataStore instance
    :returns: a CompositeSourceModel instance
    """
    mon = performance.Monitor('_build_groups', measuremem=True)
    with mon:
        rlz_groups = []
        for rlz in full_lt.sm_rlzs:
            rlz_groups.extend((rlz, grp) for grp in
                              gen_groups(full_lt, smdict, rlz))
    logging.info(mon)

    logging.info('Building CompositeSourceModel')
    groups = build_groups(full_lt, rlz_groups, oq)
    csm = CompositeSourceModel(oq, full_lt, groups)
    store_data(oq, smdict, csm, dstore)
    return csm


def store_data(oq, smdict, csm, dstore):
    """
    Create src_mutex, grp_probability in calc_XXX.hdf5 and sources
    and mf_sections in calc_XXX_tmp.hdf5
    """
    out = []
    probs = []
    for sg in csm.src_groups:
        if sg.src_interdep == 'mutex' and 'src_mutex' not in dstore:
            segments = []
            for src in sg:
                segments.append(src.source_id.split(':')[1])
                t = (src.source_id, src.grp_id,
                     src.num_ruptures, src.mutex_weight,
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

    # add rupids_by_tag to multifault sources if there is a single site
    try:
        sitecol = dstore['sitecol']
    except (KeyError, TypeError):  # 'NoneType' object is not subscriptable
        sitecol = None
    else:
        # NB: in AELO we can have multiple vs30 on the same location
        lonlats = set(zip(sitecol.lons, sitecol.lats))
        if len(lonlats) > 1:
            sitecol = None
    # must be called *after* add_semicolons
    t0 = time.time()
    secparams = fix_geometry_sections(
        smdict, csm.src_groups, dstore.tempname if dstore else '',
        sitecol if oq.disagg_by_src and oq.use_rates else None,
        split=not oq.calculation_mode.startswith('event_based'))
    if secparams is not None and len(secparams):
        logging.info('Spent %.1f seconds in fix_geometry_sections',
                     time.time()-t0)


# called by reduce_sources
def add_checksums(srcs):
    """
    Build and attach a checksum to each source
    """
    for src in srcs:
        dic = {k: v for k, v in vars(src).items()
               if k not in 'source_id sampling branch'}
        src.checksum = zlib.adler32(pickle.dumps(dic, protocol=4))


# called before add_semicolons
def add_bangs(smdict):
    """
    Discriminate different sources with same ID (false duplicates)
    and put an exclamation mark in their source ID
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


def fix_geometry_sections(smdict, src_groups, hdf5path='', site1=None,
                          split=True):
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
                mfsources, sections, hdf5path, site1, split=split)
            for sg in src_groups:
                new = []
                for src in sg.sources:
                    tag = src.source_id
                    if tag in split_dic:
                        new.extend(split_dic[tag])
                    else:
                        new.append(src)
                sg.sources[:] = new
            return secparams
    return None


def _groups_ids(smlt_dir, smdict, fnames):
    # extract the source groups and ids from a sequence of source files
    groups = []
    for fname in fnames:
        fullname = os.path.abspath(os.path.join(smlt_dir, fname))
        groups.extend(smdict[fullname].src_groups)
    return groups, set(src.source_id for grp in groups for src in grp)


def _add_sampling(src, rlz, trti):
    # associate the source to the sampling parameters of the realization;
    # the same source can appear in multiple realizations, hence the list.
    # NB: the multiplicity of the source is len(src.sampling) and it enters
    # the classical calculations too, via SourceGroup.fix_src_offset and
    # the source_info rows, so the sampling must be always set
    sampl = sampling(rlz.samples, trti * TWO24 + rlz.ordinal)
    if src.sampling is None:
        # the first time
        src.sampling = [sampl]
    else:
        # if the same source belongs to multiple realizations
        src.sampling.append(sampl)


def gen_groups(full_lt, smdict, rlz):
    # yield all the possible source groups from the given rlz
    smlt_file = full_lt.source_model_lt.filename
    smlt_dir = os.path.dirname(smlt_file)
    src_groups, source_ids = _groups_ids(
        smlt_dir, smdict, rlz.value[0].split())
    bset_values = full_lt.source_model_lt.bset_values(rlz.lt_path)
    if rlz.ordinal % 100 == 0:
        logging.info('Building source groups for rlz'
                     f'#{rlz.ordinal}: {"_".join(rlz.lt_path)}')
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
    # NB: the uncertainties are not applied here, but in the workers,
    # one set of realizations at a time, see modified_groups; the
    # sampling info is set anyway, since it determines the multiplicity
    for src_group in src_groups:
        trti = full_lt.trti.get(src_group.trt, 0)
        for src in src_group:  # tested in case_83_eb
            _add_sampling(src, rlz, trti)
        yield src_group

    # check applyToSources
    sm_branch = rlz.lt_path[0]
    src_id = full_lt.source_model_lt.info.applytosources[sm_branch]
    for srcid in src_id:
        if srcid not in source_ids:
            if full_lt.source_model_lt.branchID:
                continue
            raise ValueError(
                "The source %s is not in the source model,"
                " please fix applyToSources in %s or the "
                "source model(s) %s" % (srcid, smlt_file,
                                        rlz.value[0].split()))


def reduce_sources(sources_with_same_id):
    """
    :param sources_with_same_id: a list of sources with the same source_id
    :returns: a list of truly unique sources
    """
    # first reduce identical sources having the same id(src)
    # tested in LogictreeTestCase.test_case_08, where <PoinstSource 2>
    # appears 3 times
    unique = get_unique(sources_with_same_id)
    out = []
    add_checksums(unique)
    # in LogicTreeCase2ClassicalPSHA there 81 unique sources
    # grouped in 9 groups of 9 sources each with the same checksum
    for srcs in general.groupby(unique, checksum).values():
        # NB: the simplest test featuring the same source in two
        # different source models is logictree/case_01
        src = srcs[0]
        if len(srcs) > 1 and len(src.sampling) == 1:
            src.sampling = numpy.concatenate([s.sampling for s in srcs])
        out.append(src)
    return out


def split_by_tom(sources):
    """
    Groups together sources with the same TOM and collect multifault sources
    """
    def key(src):
        tom = getattr(src, 'temporal_occurrence_model', None)
        return (tom.__class__.__name__, src.code == b'F')
    return general.groupby(sources, key).values()


def _group_sources(trt, sources):
    """
    Reduce identical sources, regroup by trt_smrs and TOM,
    then return (source_groups, reduction_count).
    """
    key = operator.attrgetter('source_id', 'code')
    lst = []
    red = 0
    for srcs in general.groupby(sources, key).values():
        if len(srcs) > 1:
            srcs = reduce_sources(srcs)
            red += 1
        lst.extend(srcs)
    src_groups = []
    for sources in general.groupby(lst, trt_smrs).values():
        for grp in split_by_tom(sources):
            src_groups.append(sourceconverter.SourceGroup(trt, grp))
    return src_groups, red
