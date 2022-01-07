# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
import numpy
from openquake.baselib import general, parallel, hdf5
from openquake.baselib.python3compat import encode
from openquake.baselib.general import (
    AccumDict, groupby, get_nbytes_msg)
from openquake.hazardlib.contexts import read_cmakers
from openquake.hazardlib.source.point import grid_point_sources, msr_name
from openquake.hazardlib.source.base import get_code2cls
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.calc.filters import split_source, SourceFilter
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO32 = 2 ** 32


def zero_times(sources):
    source_data = AccumDict(accum=[])
    for src in sources:
        source_data['src_id'].append(src.source_id)
        source_data['nsites'].append(src.nsites)
        source_data['nrupts'].append(src.num_ruptures)
        source_data['weight'].append(src.weight)
        source_data['ctimes'].append(0)
    return source_data


def preclassical(srcs, sites, cmaker, monitor):
    """
    Weight the sources. Also split them if split_sources is true. If
    ps_grid_spacing is set, grid the point sources before weighting them.
    """
    split_sources = []
    spacing = cmaker.ps_grid_spacing
    grp_id = srcs[0].grp_id
    if sites is None:
        # in csm2rup just split the sources and count the ruptures
        for src in srcs:
            ss = split_source(src)
            if len(ss) > 1:
                for ss_ in ss:
                    ss_.nsites = 1
            split_sources.extend(ss)
            src.num_ruptures = src.count_ruptures()
        dic = {grp_id: split_sources}
        dic['before'] = len(srcs)
        dic['after'] = len(dic[grp_id])
        return dic

    sf = SourceFilter(sites, cmaker.maximum_distance)
    with monitor('splitting sources'):
        for src in srcs:
            # NB: this is approximate, since the sites are sampled
            src.nsites = len(sf.close_sids(src))  # can be 0
            # NB: it is crucial to split only the close sources, for
            # performance reasons (think of Ecuador in SAM)
            splits = split_source(src) if (
                cmaker.split_sources and src.nsites) else [src]
            split_sources.extend(splits)
    dic = grid_point_sources(split_sources, spacing, monitor)
    # this is also prefiltering the split sources
    mon = monitor('weighting sources', measuremem=False)
    cmaker.set_weight(dic[grp_id], sf, mon)
    dic['before'] = len(split_sources)
    dic['after'] = len(dic[grp_id])
    if spacing:
        dic['ps_grid/%02d' % monitor.task_no] = dic[grp_id]
    return dic


def run_preclassical(calc):
    """
    :param csm: a CompositeSourceModel
    :param oqparam: the parameters in job.ini file
    :param h5: a DataStore instance
    """
    csm = calc.csm
    calc.datastore['trt_smrs'] = csm.get_trt_smrs()
    calc.datastore['toms'] = numpy.array(
        [sg.tom_name for sg in csm.src_groups], hdf5.vstr)
    cmakers = read_cmakers(calc.datastore, csm.full_lt)
    h5 = calc.datastore.hdf5
    calc.sitecol = sites = csm.sitecol if csm.sitecol else None
    # do nothing for atomic sources except counting the ruptures
    atomic_sources = []
    normal_sources = []
    for sg in csm.src_groups:
        grp_id = sg.sources[0].grp_id
        if sg.atomic:
            cmakers[grp_id].set_weight(sg, sites)
            atomic_sources.extend(sg)
        else:
            normal_sources.extend(sg)
    # run preclassical for non-atomic sources
    sources_by_grp = groupby(
        normal_sources, lambda src: (src.grp_id, msr_name(src)))
    if csm.sitecol:
        logging.info('Sending %s', sites)
    smap = parallel.Starmap(preclassical, h5=h5)
    for (grp_id, msr), srcs in sources_by_grp.items():
        pointsources, pointlike, others = [], [], []
        for src in srcs:
            if hasattr(src, 'location'):
                pointsources.append(src)
            elif hasattr(src, 'nodal_plane_distribution'):
                pointlike.append(src)
            else:
                others.append(src)
        if calc.oqparam.ps_grid_spacing:
            if pointsources or pointlike:
                smap.submit((pointsources + pointlike, sites, cmakers[grp_id]))
        else:
            smap.submit_split((pointsources, sites, cmakers[grp_id]), 10, 100)
            for src in pointlike:  # area, multipoint
                smap.submit(([src], sites, cmakers[grp_id]))
        smap.submit_split((others, sites, cmakers[grp_id]), 10, 100)
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
    if res['before'] != res['after']:
        logging.info('Reduced the number of point sources from {:_d} -> {:_d}'.
                     format(res['before'], res['after']))
    acc = AccumDict(accum=0)
    code2cls = get_code2cls()
    for grp_id, srcs in res.items():
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
                assert src.weight
                assert src.num_ruptures
                acc[src.code] += int(src.num_ruptures)
    for val, key in sorted((val, key) for key, val in acc.items()):
        cls = code2cls[key].__name__
        logging.info('{} ruptures: {:_d}'.format(cls, val))

    source_data = zero_times(csm.get_sources())
    calc.store_source_info(source_data)
    # store ps_grid data, if any
    for key, sources in res.items():
        if isinstance(key, str) and key.startswith('ps_grid/'):
            arrays = []
            for ps in sources:
                if hasattr(ps, 'location'):
                    lonlats = [ps.location.x, ps.location.y]
                    for src in getattr(ps, 'pointsources', []):
                        lonlats.extend([src.location.x, src.location.y])
                    arrays.append(F32(lonlats))
            h5[key] = arrays

    h5['full_lt'] = csm.full_lt
    return res


@base.calculators.add('preclassical')
class PreClassicalCalculator(base.HazardCalculator):
    """
    PreClassical PSHA calculator
    """
    core_task = preclassical
    accept_precalc = []

    def get_source_ids(self):
        """
        :returns: the unique source IDs contained in the composite model
        """
        oq = self.oqparam
        self.M = len(oq.imtls)
        self.L1 = oq.imtls.size // self.M
        sources = encode([src_id for src_id in self.csm.source_info])
        size, msg = get_nbytes_msg(
            dict(N=self.N, R=self.R, M=self.M, L1=self.L1, Ns=self.Ns))
        ps = 'pointSource' in self.full_lt.source_model_lt.source_types
        if size > TWO32 and not ps:
            raise RuntimeError('The matrix disagg_by_src is too large: %s'
                               % msg)
        elif size > TWO32:
            msg = ('The source model contains point sources: you cannot set '
                   'disagg_by_src=true unless you convert them to multipoint '
                   'sources with the command oq upgrade_nrml --multipoint %s'
                   ) % oq.base_path
            raise RuntimeError(msg)
        return sources

    def init(self):
        super().init()
        if self.oqparam.hazard_calculation_id:
            full_lt = self.datastore.parent['full_lt']
            trt_smrs = self.datastore.parent['trt_smrs'][:]
        else:
            full_lt = self.csm.full_lt
            trt_smrs = self.csm.get_trt_smrs()
        self.grp_ids = numpy.arange(len(trt_smrs))
        rlzs_by_gsim_list = full_lt.get_rlzs_by_gsim_list(trt_smrs)
        rlzs_by_g = []
        for rlzs_by_gsim in rlzs_by_gsim_list:
            for rlzs in rlzs_by_gsim.values():
                rlzs_by_g.append(rlzs)
        self.datastore.hdf5.save_vlen(
            'rlzs_by_g', [U32(rlzs) for rlzs in rlzs_by_g])

    def execute(self):
        """
        Run `preclassical(srcs, srcfilter, params, monitor)` by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        run_preclassical(self)
        self.max_weight = self.csm.get_max_weight(self.oqparam)
        return self.csm

    def post_execute(self, csm):
        """
        Store the CompositeSourceModel in binary format
        """
        self.datastore['_csm'] = csm
