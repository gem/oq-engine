# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from __future__ import division
import math
import logging
import operator
import numpy

from openquake.baselib import parallel
from openquake.baselib.python3compat import encode
from openquake.baselib.general import AccumDict
from openquake.hazardlib.calc.hazard_curve import (
    pmap_from_grp, pmap_from_trt, ProbabilityMap)
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.commonlib import source, calc
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
weight = operator.attrgetter('weight')


source_data_dt = numpy.dtype(
    [('taskno', U16), ('nsites', U32), ('nruptures', U32), ('weight', F32)])


def saving_sources_by_task(iterargs, dstore):
    """
    Yield the iterargs again by populating 'task_info/source_data'
    """
    source_ids = []
    data = []
    for i, args in enumerate(iterargs, 1):
        source_ids.append(' ' .join(src.source_id for src in args[0]))
        for src in args[0]:  # collect source data
            data.append((i, src.nsites, src.num_ruptures, src.weight))
        yield args
    dstore['task_sources'] = encode(source_ids)
    dstore.extend('task_info/source_data', numpy.array(data, source_data_dt))


def classical(sources, src_filter, gsims, param, monitor):
    """
    :param sources:
        a list of independent sources or a SourceGroup with mutex sources
    :param src_filter:
        a SourceFilter instance
    :param gsims:
        a list of GSIMs
    :param param:
        a dictionary with parameters imtls and truncation_level
    :param monitor:
        a Monitor instance
    :returns: a dictionary grp_id -> ProbabilityMap
    """
    if getattr(sources, 'src_interdep', None) == 'mutex':
        return pmap_from_grp(sources, src_filter, gsims, param, monitor)
    else:
        return pmap_from_trt(sources, src_filter, gsims, param, monitor)


@base.calculators.add('psha')
class PSHACalculator(base.HazardCalculator):
    """
    Classical PSHA calculator
    """
    core_task = classical

    def agg_dicts(self, acc, pmap):
        """
        Aggregate dictionaries of hazard curves by updating the accumulator.

        :param acc: accumulator dictionary
        :param pmap: dictionary grp_id -> ProbabilityMap
        """
        with self.monitor('aggregate curves', autoflush=True):
            acc.eff_ruptures += pmap.eff_ruptures
            for grp_id in pmap:
                if pmap[grp_id]:
                    acc[grp_id] |= pmap[grp_id]
            for src_id, nsites, srcweight, calc_time in pmap.calc_times:
                src_id = src_id.split(':', 1)[0]
                try:
                    info = self.csm.infos[grp_id, src_id]
                except KeyError:
                    continue
                info.calc_time += calc_time
                info.num_sites = max(info.num_sites, nsites)
                info.num_split += 1
        return acc

    def zerodict(self):
        """
        Initial accumulator, a dict grp_id -> ProbabilityMap(L, G)
        """
        csm_info = self.csm.info
        zd = AccumDict()
        num_levels = len(self.oqparam.imtls.array)
        for grp in self.csm.src_groups:
            num_gsims = len(csm_info.gsim_lt.get_gsims(grp.trt))
            zd[grp.id] = ProbabilityMap(num_levels, num_gsims)
        zd.calc_times = []
        zd.eff_ruptures = AccumDict()  # grp_id -> eff_ruptures
        return zd

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        try:
            self.csm
        except AttributeError:
            raise RuntimeError('No CompositeSourceModel, did you forget to '
                               'run the hazard or the --hc option?')
        with self.monitor('managing sources', autoflush=True):
            allargs = self.gen_args(self.monitor('classical'))
            iterargs = saving_sources_by_task(allargs, self.datastore)
            if isinstance(allargs, list):
                # there is a trick here: if the arguments are known
                # (a list, not an iterator), keep them as a list
                # then the Starmap will understand the case of a single
                # argument tuple and it will run in core the task
                iterargs = list(iterargs)
            ires = parallel.Starmap(
                self.core_task.__func__, iterargs).submit_all()
        acc = ires.reduce(self.agg_dicts, self.zerodict())
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(self.csm.infos, acc)
        return acc

    def gen_args(self, monitor):
        """
        Used in the case of large source model logic trees.

        :param monitor: a :class:`openquake.baselib.performance.Monitor`
        :yields: (sources, sites, gsims, monitor) tuples
        """
        oq = self.oqparam
        opt = self.oqparam.optimize_same_id_sources
        num_tiles = math.ceil(len(self.sitecol) / oq.sites_per_tile)
        if num_tiles > 1:
            tiles = self.sitecol.split_in_tiles(num_tiles)
        else:
            tiles = [self.sitecol]
        maxweight = self.csm.get_maxweight(oq.concurrent_tasks)
        numheavy = len(self.csm.get_sources('heavy', maxweight))
        logging.info('Using maxweight=%d, numheavy=%d, tiles=%d',
                     maxweight, numheavy, len(tiles))
        param = dict(truncation_level=oq.truncation_level, imtls=oq.imtls)
        for tile_i, tile in enumerate(tiles, 1):
            num_tasks = 0
            num_sources = 0
            with self.monitor('prefiltering'):
                logging.info('Prefiltering tile %d of %d', tile_i, len(tiles))
                src_filter = SourceFilter(tile, oq.maximum_distance)
                csm = self.csm.filter(src_filter)
            if csm.has_dupl_sources and not opt:
                logging.warn('Found %d duplicated sources, use oq info',
                             csm.has_dupl_sources)
            for sg in csm.src_groups:
                if sg.src_interdep == 'mutex':
                    gsims = self.csm.info.gsim_lt.get_gsims(sg.trt)
                    self.csm.add_infos(sg.sources)  # update self.csm.infos
                    yield sg, src_filter, gsims, param, monitor
                    num_tasks += 1
                    num_sources += len(sg.sources)
            # NB: csm.get_sources_by_trt discards the mutex sources
            for trt, sources in self.csm.get_sources_by_trt(opt).items():
                gsims = self.csm.info.gsim_lt.get_gsims(trt)
                self.csm.add_infos(sources)  # update with unsplit sources
                for block in csm.split_in_blocks(maxweight, sources):
                    yield block, src_filter, gsims, param, monitor
                    num_tasks += 1
                    num_sources += len(block)
            logging.info('Sent %d sources in %d tasks', num_sources, num_tasks)
        source.split_map.clear()

    def post_execute(self, pmap_by_grp_id):
        """
        Collect the hazard curves by realization and export them.

        :param pmap_by_grp_id:
            a dictionary grp_id -> hazard curves
        """
        grp_trt = self.csm.info.grp_trt()
        with self.monitor('saving probability maps', autoflush=True):
            for grp_id, pmap in pmap_by_grp_id.items():
                if pmap:  # pmap can be missing if the group is filtered away
                    fix_ones(pmap)  # avoid saving PoEs == 1
                    key = 'poes/grp-%02d' % grp_id
                    self.datastore[key] = pmap
                    self.datastore.set_attrs(key, trt=grp_trt[grp_id])
            if 'poes' in self.datastore:
                self.datastore.set_nbytes('poes')


def fix_ones(pmap):
    """
    Physically, an extremely small intensity measure level can have an
    extremely large probability of exceedence, however that probability
    cannot be exactly 1 unless the level is exactly 0. Numerically, the
    PoE can be 1 and this give issues when calculating the damage (there
    is a log(0) in
    :class:`openquake.risklib.scientific.annual_frequency_of_exceedence`).
    Here we solve the issue by replacing the unphysical probabilities 1
    with .9999999999999999 (the float64 closest to 1).
    """
    for sid in pmap:
        array = pmap[sid].array
        array[array == 1.] = .9999999999999999


def build_hcurves_and_stats(pgetter, hstats, monitor):
    """
    :param pgetter: an :class:`openquake.commonlib.calc.PmapGetter`
    :param hstats: a list of pairs (statname, statfunc)
    :param monitor: instance of Monitor
    :returns: a dictionary kind -> ProbabilityMap

    The "kind" is a string of the form 'rlz-XXX' or 'mean' of 'quantile-XXX'
    used to specify the kind of output.
    """
    with monitor('combine pmaps'):
        pmaps = pgetter.get_pmaps(pgetter.sids)
    if sum(len(pmap) for pmap in pmaps) == 0:  # no data
        return {}
    pmap_by_kind = {}
    for kind, stat in hstats:
        with monitor('compute ' + kind):
            pmap = compute_pmap_stats(pmaps, [stat], pgetter.weights)
        pmap_by_kind[kind] = pmap
    return pmap_by_kind


@base.calculators.add('classical')
class ClassicalCalculator(PSHACalculator):
    """
    Classical PSHA calculator
    """
    pre_calculator = 'psha'
    core_task = build_hcurves_and_stats

    def execute(self):
        """
        Build statistical hazard curves from the stored PoEs
        """
        if 'poes' not in self.datastore:  # for short report
            return
        oq = self.oqparam
        num_rlzs = len(self.datastore['realizations'])
        if num_rlzs == 1:  # no stats to compute
            return {}
        elif not oq.hazard_stats():
            if oq.hazard_maps or oq.uniform_hazard_spectra:
                raise ValueError('The job.ini says that no statistics should '
                                 'be computed, but then there is no output!')
            else:
                return {}
        # initialize datasets
        N = len(self.sitecol)
        L = len(oq.imtls.array)
        attrs = dict(
            __pyclass__='openquake.hazardlib.probability_map.ProbabilityMap',
            sids=numpy.arange(N, dtype=numpy.uint32))
        nbytes = N * L * 4  # bytes per realization (32 bit floats)
        totbytes = 0
        if num_rlzs > 1:
            for name, stat in oq.hazard_stats():
                self.datastore.create_dset(
                    'hcurves/' + name, F32, (N, L, 1), attrs=attrs)
                totbytes += nbytes
        if 'hcurves' in self.datastore:
            self.datastore.set_attrs('hcurves', nbytes=totbytes)
        self.datastore.flush()

        with self.monitor('sending pmaps', autoflush=True, measuremem=True):
            monitor = self.monitor('build_hcurves_and_stats')
            hstats = oq.hazard_stats()
            allargs = (
                (calc.PmapGetter(self.datastore, tile.sids, self.rlzs_assoc),
                 hstats, monitor)
                for tile in self.sitecol.split_in_tiles(oq.concurrent_tasks))
            ires = parallel.Starmap(
                self.core_task.__func__, allargs).submit_all()
        nbytes = ires.reduce(self.save_hcurves)
        return nbytes

    def save_hcurves(self, acc, pmap_by_kind):
        """
        Works by side effect by saving hcurves and statistics on the
        datastore; the accumulator stores the number of bytes saved.

        :param acc: dictionary kind -> nbytes
        :param pmap_by_kind: a dictionary of ProbabilityMaps
        """
        with self.monitor('saving statistical hcurves', autoflush=True):
            for kind in pmap_by_kind:
                pmap = pmap_by_kind[kind]
                if pmap:
                    key = 'hcurves/' + kind
                    dset = self.datastore.getitem(key)
                    for sid in pmap:
                        dset[sid] = pmap[sid].array
                    # in the datastore we save 4 byte floats, thus we
                    # divide the memory consumption by 2: pmap.nbytes / 2
                    acc += {kind: pmap.nbytes // 2}
            self.datastore.flush()
            return acc

    def post_execute(self, acc):
        """Save the number of bytes per each dataset"""
        for kind, nbytes in acc.items():
            self.datastore.getitem('hcurves/' + kind).attrs['nbytes'] = nbytes
