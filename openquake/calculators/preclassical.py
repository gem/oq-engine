# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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

import os
import sys
import logging
import operator
import numpy
import h5py
from openquake.baselib import general, parallel, hdf5, config
from openquake.hazardlib import pmf, geo, source_reader
from openquake.baselib.general import AccumDict, groupby, block_splitter
from openquake.hazardlib.contexts import read_cmakers
from openquake.hazardlib.source.point import grid_point_sources
from openquake.hazardlib.source.base import get_code2cls
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.calc.filters import (
    getdefault, split_source, SourceFilter)
from openquake.hazardlib.scalerel.point import PointMSR
from openquake.commonlib import readinput
from openquake.calculators import base, getters

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO24 = 2 ** 24
TWO32 = 2 ** 32


def source_data(sources):
    """
    Set the source .id attribute to the index in the source_info table
    :returns: a dictionary of lists with keys src_id, nsites, nruptrs, weight, ctimes
    """
    data = AccumDict(accum=[])
    for src in sources:
        data['src_id'].append(src.source_id)
        data['nsites'].append(src.nsites)
        data['nrupts'].append(src.num_ruptures)
        data['weight'].append(src.weight)
        data['ctimes'].append(0)
    return data


def check_maxmag(pointlike):
    """Check for pointlike sources with high magnitudes"""
    for src in pointlike:
        maxmag = src.get_annual_occurrence_rates()[-1][0]
        if maxmag >= 9.:
            logging.info('%s %s has maximum magnitude %s',
                         src.__class__.__name__, src.source_id, maxmag)


def collapse_nphc(src):
    """
    Collapse the nodal_plane_distribution and hypocenter_distribution.
    """
    if (hasattr(src, 'nodal_plane_distribution') and
            hasattr(src, 'hypocenter_distribution')):
        if len(src.nodal_plane_distribution.data) > 1:
            ws, nps = zip(*src.nodal_plane_distribution.data)
            strike = numpy.average([np.strike for np in nps], weights=ws)
            dip = numpy.average([np.dip for np in nps], weights=ws)
            rake = numpy.average([np.rake for np in nps], weights=ws)
            val = geo.NodalPlane(strike, dip, rake)
            src.nodal_plane_distribution = pmf.PMF([(1., val)])
        if len(src.hypocenter_distribution.data) > 1:
            ws, vals = zip(*src.hypocenter_distribution.data)
            val = numpy.average(vals, weights=ws)
            src.hypocenter_distribution = pmf.PMF([(1., val)])
        src.magnitude_scaling_relationship = PointMSR()


def _filter(srcs, min_mag):
    # filter by magnitude and count the ruptures
    mmag = getdefault(min_mag, srcs[0].tectonic_region_type)
    out = [src for src in srcs if src.get_mags()[-1] >= mmag]
    for ss in out:
        ss.num_ruptures = ss.count_ruptures()
    return out


def preclassical(srcs, sites, cmaker, secparams, monitor):
    """
    Weight the sources. Also split them if split_sources is true. If
    ps_grid_spacing is set, grid the point sources before weighting them.
    """
    grp_id = srcs[0].grp_id
    if sites:
        N = len(sites)
        multiplier = 1 + len(sites) // 10_000
        sf = SourceFilter(sites, cmaker.maximum_distance).reduce(multiplier)
    else:
        N = 0
        multiplier = 1
        sf = SourceFilter(None)
    splits = []
    mon1 = monitor('building top of ruptures', measuremem=True)
    mon2 = monitor('setting msparams', measuremem=False)
    ry0 = 'ry0' in cmaker.REQUIRES_DISTANCES
    for src in srcs:
        if src.code == b'F':
            if N and N <= cmaker.max_sites_disagg:
                mask = sf.get_close(secparams) > 0  # shape S
            else:
                mask = None
            src.set_msparams(secparams, mask, ry0, mon1, mon2)
        if sites:
            # NB: this is approximate, since the sites are sampled
            src.nsites = len(sf.close_sids(src))  # can be 0
            # print(f'{src.source_id=}, {src.nsites=}')
        else:
            src.nsites = 1
        # NB: it is crucial to split only the close sources, for
        # performance reasons (think of Ecuador in SAM)
        if cmaker.split_sources and src.nsites:
            splits.extend(split_source(src))
        else:
            splits.append(src)
    splits = _filter(splits, cmaker.oq.minimum_magnitude)
    if splits:
        mon = monitor('weighting sources', measuremem=False)
        with mon:
            cmaker.set_weight(splits, sf, multiplier)
        yield {grp_id: splits}


def store_tiles(dstore, csm, sitecol, cmakers):
    """
    Store a `tiles` array if the calculation is large enough.
    :returns: a triple (max_weight, trt_rlzs, gids)
    """
    if sitecol is None:
        N = 0
    else:
        N = len(sitecol)
    oq = cmakers[0].oq
    fac = oq.imtls.size * N * 4 / 1024**3
    max_weight = csm.get_max_weight(oq)

    # build source_groups
    quartets = csm.split(cmakers, sitecol, max_weight, tiling=oq.tiling)
    data = numpy.array(
        [(cm.grp_id, len(cm.gsims), len(tgets), len(blocks), splits,
          len(cm.gsims) * fac * 1024, cm.weight, cm.codes, cm.trt)
         for cm, tgets, blocks, splits in quartets],
        [('grp_id', U16), ('gsims', U16), ('tiles', U16), ('blocks', U16),
         ('splits', U16), ('size_mb', F32), ('weight', F32),
         ('codes', '<S8'), ('trt', '<S32')])

    # determine light groups and tiling
    light, = numpy.where(data['blocks'] == 1)
    req_gb, trt_rlzs, gids = getters.get_pmaps_gb(dstore, csm.full_lt)
    mem_gb = req_gb - sum(len(cm.gsims) * fac for cm in cmakers[light])
    if len(light):
        logging.info('mem_gb = %.2f with %d light groups out of %d',
                     mem_gb, len(light), len(data))
    else:
        logging.info('Required mem_gb = %.2f', req_gb)
    max_gb = float(config.memory.pmap_max_gb or parallel.Starmap.num_cores/8)
    regular = (mem_gb < max_gb or oq.disagg_by_src or
               N < oq.max_sites_disagg or oq.tile_spec)
    if oq.tiling is None:
        # use tiling with OQ_SAMPLE_SOURCES to avoid slow tasks
        ss = os.environ.get('OQ_SAMPLE_SOURCES') is not None
        tiling = ss and N > 10_000 or not regular
    else:
        tiling = oq.tiling

    # store source_groups
    dstore.create_dset('source_groups', data, fillvalue=None,
                       attrs=dict(req_gb=req_gb, mem_gb=mem_gb, tiling=tiling))
    if req_gb >= 30 and not config.directory.custom_tmp:
        logging.info('We suggest to set custom_tmp')
    return req_gb, max_weight, trt_rlzs, gids


@base.calculators.add('preclassical')
class PreClassicalCalculator(base.HazardCalculator):
    """
    PreClassical PSHA calculator
    """
    core_task = preclassical
    accept_precalc = []

    def init(self):
        if self.oqparam.hazard_calculation_id:
            self.full_lt = self.datastore.parent['full_lt'].init()
        else:
            super().init()
            self.full_lt = self.csm.full_lt

    def store(self):
        # store full_lt, toms
        self.datastore['full_lt'] = self.csm.full_lt
        self.datastore['toms'] = numpy.array(
            [sg.get_tom_toml(self.oqparam.investigation_time)
             for sg in self.csm.src_groups], hdf5.vstr)

    def populate_csm(self):
        """
        Update the CompositeSourceModel by splitting and weighting the
        sources; save the source_info table.
        """
        oq = self.oqparam
        csm = self.csm
        self.store()
        logging.info('Building cmakers')
        self.cmakers = read_cmakers(self.datastore, csm)
        trt_smrs = [U32(sg[0].trt_smrs) for sg in csm.src_groups]
        self.datastore.hdf5.save_vlen('trt_smrs', trt_smrs)
        sites = csm.sitecol if csm.sitecol else None
        if sites is None:
            logging.warning('No sites??')

        L = oq.imtls.size
        Gfull = self.full_lt.gfull(trt_smrs)
        gweights = numpy.concatenate([cm.wei for cm in self.cmakers])
        self.datastore['gweights'] = gweights

        Gt = len(gweights)
        extra = f'<{Gfull}' if Gt < Gfull else ''
        if sites is not None:
            nbytes = 4 * len(self.sitecol) * L * Gt
            # Gt is known before starting the preclassical
            logging.warning(f'The global pmap would require %s ({Gt=}%s)',
                            general.humansize(nbytes), extra)

        # do nothing for atomic sources except counting the ruptures
        atomic_sources = []
        normal_sources = []
        reqv = 'reqv' in oq.inputs
        if reqv:
            logging.warning(
                'Using equivalent distance approximation and '
                'collapsing hypocenters and nodal planes')
        multifaults = []
        for sg in csm.src_groups:
            for src in sg:
                if src.code == b'F':
                    multifaults.append(src)
                if reqv and sg.trt in oq.inputs['reqv']:
                    if src.source_id not in oq.reqv_ignore_sources:
                        collapse_nphc(src)
            grp_id = sg.sources[0].grp_id
            if sg.atomic:
                self.cmakers[grp_id].set_weight(
                    sg, SourceFilter(sites, oq.maximum_distance))
                atomic_sources.extend(sg)
            else:
                normal_sources.extend(sg)
        if multifaults:
            with hdf5.File(multifaults[0].hdf5path, 'r') as h5:
                secparams = h5['secparams'][:]
            logging.warning(
                'There are %d multiFaultSources (secparams=%s)',
                len(multifaults), general.humansize(secparams.nbytes))
        else:
            secparams = ()
        self._process(atomic_sources, normal_sources, sites, secparams)
        allsources = csm.get_sources()
        self.store_source_info(source_data(allsources))

    def _process(self, atomic_sources, normal_sources, sites, secparams):
        # run preclassical in parallel for non-atomic sources
        sources_by_key = groupby(normal_sources, operator.attrgetter('grp_id'))
        logging.info('Starting preclassical with %d source groups',
                     len(sources_by_key))
        if sys.platform != 'darwin':
            # avoid a segfault in macOS
            self.datastore.swmr_on()
        before_after = numpy.zeros(2, dtype=int)
        smap = parallel.Starmap(preclassical, h5=self.datastore.hdf5)
        for grp_id, srcs in sources_by_key.items():
            cmaker = self.cmakers[grp_id]
            cmaker.gsims = list(cmaker.gsims)  # reducing data transfer
            pointsources, pointlike, others = [], [], []
            for src in srcs:
                if hasattr(src, 'location'):
                    pointsources.append(src)
                elif hasattr(src, 'nodal_plane_distribution'):
                    pointlike.append(src)
                elif src.code in b'CFN':  # other heavy sources
                    smap.submit(([src], sites, cmaker, secparams))
                else:
                    others.append(src)
            check_maxmag(pointlike)
            if pointsources or pointlike:
                spacing = self.oqparam.ps_grid_spacing
                if spacing:
                    for plike in pointlike:
                        pointsources.extend(split_source(plike))
                    logging.info(f'Gridding point sources for {grp_id=}')
                    cpsources = grid_point_sources(pointsources, spacing)
                    before_after += [len(pointsources), len(cpsources)]
                    for block in block_splitter(cpsources, 200):
                        smap.submit((block, sites, cmaker, secparams))
                else:
                    for block in block_splitter(pointsources, 2000):
                        smap.submit((block, sites, cmaker, secparams))
                    others.extend(pointlike)
            for block in block_splitter(others, 40):
                smap.submit((block, sites, cmaker, secparams))
        res = smap.reduce()
        atomic = set(src.grp_id for src in atomic_sources)
        if atomic:  # case_35
            for grp_id, srcs in groupby(
                    atomic_sources, lambda src: src.grp_id).items():
                res[grp_id] = srcs
        if before_after[0] != before_after[1]:
            logging.info(
                'Reduced the number of point sources from {:_d} -> {:_d}'.
                format(before_after[0], before_after[1]))
        acc = AccumDict(accum=0)
        code2cls = get_code2cls()
        for grp_id, srcs in res.items():
            # NB: grp_id can be the string "before" or "after"
            if not isinstance(grp_id, str):
                srcs.sort(key=operator.attrgetter('source_id'))
            # srcs can be empty if the minimum_magnitude filter is on
            if srcs and not isinstance(grp_id, str) and grp_id not in atomic:
                newsg = SourceGroup(srcs[0].tectonic_region_type)
                newsg.sources = srcs
                self.csm.src_groups[grp_id] = newsg
                for src in srcs:
                    assert src.weight, src
                    assert src.num_ruptures, src
                    acc[src.code] += int(src.num_ruptures)
        self.csm.fix_src_offset()
        for val, key in sorted((val, key) for key, val in acc.items()):
            cls = code2cls[key].__name__
            logging.info('{} ruptures: {:_d}'.format(cls, val))

    def execute(self):
        """
        Run `preclassical(srcs, srcfilter, params, monitor)` by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        if not hasattr(self, 'csm'):  # used only for post_process
            return
        cachepath = readinput.get_cache_path(self.oqparam, self.datastore.hdf5)
        if os.path.exists(cachepath):
            realpath = os.path.realpath(cachepath)
            logging.info('Copying csm from %s', realpath)
            with h5py.File(realpath, 'r') as cache:  # copy _csm
                cache.copy(cache['_csm'], self.datastore.hdf5)
            self.store()  # full_lt, toms
        else:
            self.populate_csm()
            try:
                self.datastore['_csm'] = self.csm
            except RuntimeError as exc:
                # this happens when setrecursionlimit is too low
                # we can continue anyway, this is not critical
                logging.error(str(exc), exc_info=True)
            else:
                if cachepath:
                    os.symlink(self.datastore.filename, cachepath)
        return self.csm

    def post_execute(self, csm):
        """
        Raise an error if the sources were all discarded
        """
        self.datastore.create_dset(
            'weights',
            F32([rlz.weight[-1] for rlz in self.full_lt.get_realizations()]))
        totsites = sum(row[source_reader.NUM_SITES]
                       for row in self.csm.source_info.values())
        if totsites == 0:
            if self.N == 1:
                logging.error('There are no sources close to the site!')
            else:
                raise RuntimeError(
                    'There are no sources close to the site(s)! '
                    'Use oq plot sources? to debug')

        fname = self.oqparam.inputs.get('delta_rates')
        if fname:
            idx_nr = {row[0]: (idx, row[source_reader.NUM_RUPTURES])
                      for idx, row in enumerate(self.csm.source_info.values())}
            deltas = readinput.read_delta_rates(fname, idx_nr)
            self.datastore.hdf5.save_vlen('delta_rates', deltas)

        # save 'source_groups'
        if self.sitecol is not None:
            self.req_gb, self.max_weight, self.trt_rlzs, self.gids = (
                store_tiles(self.datastore, self.csm, self.sitecol, self.cmakers))

        # save gsims
        toml = []
        for cmaker in self.cmakers:
            for gsim in cmaker.gsims:
                toml.append(gsim._toml)
        self.datastore['gsims'] = numpy.array(toml)

    def post_process(self):
        if self.oqparam.calculation_mode == 'preclassical':
            super().post_process()
        # else do nothing, post_process will be called later on
