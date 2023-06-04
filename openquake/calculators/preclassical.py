# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
import logging
import operator
import numpy
import h5py
from openquake.baselib import general, parallel, hdf5
from openquake.hazardlib import pmf, geo
from openquake.baselib.general import AccumDict, groupby, block_splitter
from openquake.hazardlib.contexts import read_cmakers
from openquake.hazardlib.source.point import grid_point_sources, msr_name
from openquake.hazardlib.source.base import get_code2cls
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.calc.filters import split_source, SourceFilter
from openquake.hazardlib.scalerel.point import PointMSR
from openquake.commonlib import readinput
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO24 = 2 ** 24
TWO32 = 2 ** 32


def source_data(sources):
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
        if maxmag >= 8.:
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


def preclassical(srcs, sites, cmaker, monitor):
    """
    Weight the sources. Also split them if split_sources is true. If
    ps_grid_spacing is set, grid the point sources before weighting them.
    """
    split_sources = []
    spacing = cmaker.ps_grid_spacing
    grp_id = srcs[0].grp_id
    if sites:
        multiplier = 1 + len(sites) // 10_000
        sf = SourceFilter(sites, cmaker.maximum_distance).reduce(multiplier)
    for src in srcs:
        if sites:
            # NB: this is approximate, since the sites are sampled
            src.nsites = len(sf.close_sids(src))  # can be 0
        else:
            src.nsites = 1
        # NB: it is crucial to split only the close sources, for
        # performance reasons (think of Ecuador in SAM)
        splits = split_source(src) if (
            cmaker.split_sources and src.nsites) else [src]
        for ss in splits:
            ss.num_ruptures = ss.count_ruptures()
        split_sources.extend(splits)
    mon = monitor('weighting sources', measuremem=False)
    if sites is None or spacing == 0:
        if sites is None:
            for src in split_sources:
                src.weight = .01
        else:
            cmaker.set_weight(split_sources, sf, multiplier, mon)
        dic = {grp_id: split_sources}
        dic['before'] = len(srcs)
        dic['after'] = len(split_sources)
        yield dic
    else:
        cnt = 0
        for msr, block in groupby(split_sources, msr_name).items():
            dic = grid_point_sources(block, spacing, msr, cnt, monitor)
            cnt = dic.pop('cnt')
            for src in dic[grp_id]:
                src.num_ruptures = src.count_ruptures()
            # this is also prefiltering the split sources
            cmaker.set_weight(dic[grp_id], sf, multiplier, mon)
            # print(f'{mon.task_no=}, {mon.duration=}')
            dic['before'] = len(block)
            dic['after'] = len(dic[grp_id])
            yield dic


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
        oq = self.oqparam
        csm = self.csm
        self.store()
        cmakers = read_cmakers(self.datastore, csm)
        trt_smrs = [U32(sg[0].trt_smrs) for sg in csm.src_groups]
        data = csm.full_lt.get_trt_rlzs(trt_smrs)
        self.datastore.hdf5.save_vlen('trt_smrs', trt_smrs)
        self.sitecol = sites = csm.sitecol if csm.sitecol else None
        if sites is None:
            logging.warning('No sites??')
        # do nothing for atomic sources except counting the ruptures
        atomic_sources = []
        normal_sources = []
        reqv = 'reqv' in oq.inputs
        if reqv:
            logging.warning(
                'Using equivalent distance approximation and '
                'collapsing hypocenters and nodal planes')
        for sg in csm.src_groups:
            if reqv and sg.trt in oq.inputs['reqv']:
                for src in sg:
                    if src.source_id not in oq.reqv_ignore_sources:
                        collapse_nphc(src)
            grp_id = sg.sources[0].grp_id
            if sg.atomic:
                cmakers[grp_id].set_weight(sg, sites)
                atomic_sources.extend(sg)
            else:
                for src in sg:
                    if hasattr(src, 'rupture_idxs'):  # multiFault
                        normal_sources.extend(split_source(src))
                    else:
                        normal_sources.append(src)

        # run preclassical for non-atomic sources
        sources_by_key = groupby(normal_sources, operator.attrgetter('grp_id'))
        logging.info('Starting preclassical with %d source groups',
                     len(sources_by_key))
        smap = parallel.Starmap(preclassical, h5=self.datastore.hdf5)
        for grp_id, srcs in sources_by_key.items():
            pointsources, pointlike, others = [], [], []
            for src in srcs:
                if hasattr(src, 'location'):
                    pointsources.append(src)
                elif hasattr(src, 'nodal_plane_distribution'):
                    pointlike.append(src)
                elif src.code in b'CFN':  # send the heavy sources
                    smap.submit(([src], sites, cmakers[grp_id]))
                else:
                    others.append(src)
            check_maxmag(pointlike)
            if pointsources or pointlike:
                if oq.ps_grid_spacing:
                    # do not split the pointsources
                    smap.submit(
                        (pointsources + pointlike, sites, cmakers[grp_id]))
                else:
                    for block in block_splitter(pointsources, 1000):
                        smap.submit((block, sites, cmakers[grp_id]))
                    others.extend(pointlike)
            for block in block_splitter(others, 20):
                smap.submit((block, sites, cmakers[grp_id]))
        normal = smap.reduce()
        if atomic_sources:  # case_35
            n = len(atomic_sources)
            atomic = AccumDict({'before': n, 'after': n})
            for grp_id, srcs in groupby(
                    atomic_sources, lambda src: src.grp_id).items():
                atomic[grp_id] = srcs
        else:
            atomic = AccumDict()
        res = normal + atomic
        if ('before' in res and 'after' in res and
                res['before'] != res['after']):
            logging.info(
                'Reduced the number of point sources from {:_d} -> {:_d}'.
                format(res['before'], res['after']))
        acc = AccumDict(accum=0)
        code2cls = get_code2cls()
        for grp_id, srcs in res.items():
            # NB: grp_id can be the string "before" or "after"
            if not isinstance(grp_id, str):
                srcs.sort(key=operator.attrgetter('source_id'))
            # srcs can be empty if the minimum_magnitude filter is on
            if srcs and not isinstance(grp_id, str) and grp_id not in atomic:
                # check if OQ_SAMPLE_SOURCES is set
                ss = os.environ.get('OQ_SAMPLE_SOURCES')
                if ss:
                    logging.info('Sampled sources for group #%d', grp_id)
                    srcs = general.random_filter(srcs, float(ss)) or [srcs[0]]
                newsg = SourceGroup(srcs[0].tectonic_region_type)
                newsg.sources = srcs
                csm.src_groups[grp_id] = newsg
                for src in srcs:
                    assert src.weight, src
                    assert src.num_ruptures, src
                    acc[src.code] += int(src.num_ruptures)
        csm.fix_src_offset()
        for val, key in sorted((val, key) for key, val in acc.items()):
            cls = code2cls[key].__name__
            logging.info('{} ruptures: {:_d}'.format(cls, val))
        self.store_source_info(source_data(csm.get_sources()))
        return res

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
        self.max_weight = self.csm.get_max_weight(self.oqparam)
        return self.csm

    def post_execute(self, csm):
        """
        Raise an error if the sources were all discarded
        """
        if 'source_info' in self.datastore:
            num_sites = self.datastore['source_info']['num_sites']
            if (num_sites == 0).all():
                raise RuntimeError('There are no sources close to the site(s)')

    def post_process(self):
        if self.oqparam.calculation_mode == 'preclassical':
            super().post_process()
        # else do nothing, post_process will be called later on
