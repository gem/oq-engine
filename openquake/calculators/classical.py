# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
import math
import time
import logging
import operator
import numpy

from openquake.baselib import parallel, hdf5
from openquake.baselib.python3compat import encode
from openquake.baselib.general import AccumDict, block_splitter, groupby
from openquake.hazardlib.calc.hazard_curve import classical, ProbabilityMap
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.hazardlib import source
from openquake.calculators import getters
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
weight = operator.attrgetter('weight')

grp_source_dt = numpy.dtype([('grp_id', U16), ('source_id', hdf5.vstr),
                             ('source_name', hdf5.vstr)])
source_data_dt = numpy.dtype(
    [('taskno', U16), ('nsites', U32), ('nruptures', U32), ('weight', F32)])


def get_src_ids(sources):
    """
    :returns:
       a string with the source IDs of the given sources, stripping the
       extension after the colon, if any
    """
    src_ids = []
    for src in sources:
        long_src_id = src.source_id
        try:
            src_id, ext = long_src_id.rsplit(':', 1)
        except ValueError:
            src_id = long_src_id
        src_ids.append(src_id)
    return ' '.join(set(src_ids))


def saving_sources_by_task(iterargs, dstore):
    """
    Yield the iterargs again by populating 'task_info/source_data'
    """
    source_ids = []
    data = []
    for i, args in enumerate(iterargs, 1):
        source_ids.append(get_src_ids(args[0]))
        for src in args[0]:  # collect source data
            data.append((i, src.nsites, src.num_ruptures, src.weight))
        yield args
    dstore['task_info/task_sources'] = encode(source_ids)
    dstore.extend('task_info/source_data', numpy.array(data, source_data_dt))


@base.calculators.add('psha')
class PSHACalculator(base.HazardCalculator):
    """
    Classical PSHA calculator
    """
    core_task = classical

    def agg_dicts(self, acc, pmap_by_grp):
        """
        Aggregate dictionaries of hazard curves by updating the accumulator.

        :param acc: accumulator dictionary
        :param pmap_by_grp: dictionary grp_id -> ProbabilityMap
        """
        with self.monitor('aggregate curves', autoflush=True):
            acc.eff_ruptures += pmap_by_grp.eff_ruptures
            for grp_id in pmap_by_grp:
                if pmap_by_grp[grp_id]:
                    acc[grp_id] |= pmap_by_grp[grp_id]
                self.nsites.append(len(pmap_by_grp[grp_id]))
            for srcid, (srcweight, nsites, calc_time, split) in \
                    pmap_by_grp.calc_times.items():
                info = self.csm.infos[srcid]
                info.num_sites += nsites
                info.calc_time += calc_time
                info.num_split += split
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
        self.nsites = []
        acc = ires.reduce(self.agg_dicts, self.zerodict())
        if not self.nsites:
            raise RuntimeError('All sources were filtered out!')
        logging.info('Effective sites per task: %d', numpy.mean(self.nsites))
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
        param = dict(truncation_level=oq.truncation_level, imtls=oq.imtls,
                     filter_distance=oq.filter_distance)
        minweight = source.MINWEIGHT * math.sqrt(len(self.sitecol))
        totweight = 0
        num_tasks = 0
        num_sources = 0
        csm, src_filter = self.filter_csm()
        maxweight = csm.get_maxweight(weight, oq.concurrent_tasks, minweight)
        if maxweight == minweight:
            logging.info('Using minweight=%d', minweight)
        else:
            logging.info('Using maxweight=%d', maxweight)
        totweight += csm.info.tot_weight

        if csm.has_dupl_sources and not opt:
            logging.warn('Found %d duplicated sources',
                         csm.has_dupl_sources)

        for sg in csm.src_groups:
            if sg.src_interdep == 'mutex' and len(sg) > 0:
                gsims = self.csm.info.gsim_lt.get_gsims(sg.trt)
                yield sg, src_filter, gsims, param, monitor
                num_tasks += 1
                num_sources += len(sg.sources)
        # NB: csm.get_sources_by_trt discards the mutex sources
        for trt, sources in csm.get_sources_by_trt().items():
            gsims = self.csm.info.gsim_lt.get_gsims(trt)
            for block in block_splitter(sources, maxweight, weight):
                yield block, src_filter, gsims, param, monitor
                num_tasks += 1
                num_sources += len(block)
        logging.info('Sent %d sources in %d tasks', num_sources, num_tasks)
        self.csm.info.tot_weight = totweight

    def post_execute(self, pmap_by_grp_id):
        """
        Collect the hazard curves by realization and export them.

        :param pmap_by_grp_id:
            a dictionary grp_id -> hazard curves
        """
        oq = self.oqparam
        grp_trt = self.csm.info.grp_by("trt")
        grp_source = self.csm.info.grp_by("name")
        if oq.disagg_by_src:
            src_name = {src.src_group_id: src.name
                        for src in self.csm.get_sources()}
        data = []
        with self.monitor('saving probability maps', autoflush=True):
            for grp_id, pmap in pmap_by_grp_id.items():
                if pmap:  # pmap can be missing if the group is filtered away
                    fix_ones(pmap)  # avoid saving PoEs == 1
                    key = 'poes/grp-%02d' % grp_id
                    self.datastore[key] = pmap
                    self.datastore.set_attrs(key, trt=grp_trt[grp_id])
                    if oq.disagg_by_src:
                        data.append(
                            (grp_id, grp_source[grp_id], src_name[grp_id]))
        if 'poes' in self.datastore:
            self.datastore.set_nbytes('poes')
            if oq.disagg_by_src and self.csm.info.get_num_rlzs() == 1:
                # this is useful for disaggregation, which is implemented
                # only for the case of a single realization
                self.datastore['disagg_by_src/source_id'] = numpy.array(
                    sorted(data), grp_source_dt)

            # save a copy of the poes in hdf5cache
            if hasattr(self, 'hdf5cache'):
                with hdf5.File(self.hdf5cache) as cache:
                    cache['oqparam'] = oq
                    self.datastore.hdf5.copy('poes', cache)


# used in PreClassicalCalculator
def count_ruptures(sources, srcfilter, gsims, param, monitor):
    """
    Count the number of ruptures contained in the given sources by applying a
    raw source filtering on the integration distance. Return a dictionary
    src_group_id -> {}.
    All sources must belong to the same tectonic region type.
    """
    dic = groupby(sources, lambda src: src.src_group_ids[0])
    acc = AccumDict({grp_id: {} for grp_id in dic})
    acc.eff_ruptures = {grp_id: 0 for grp_id in dic}
    acc.calc_times = AccumDict(accum=numpy.zeros(4))
    for grp_id in dic:
        for src in sources:
            t0 = time.time()
            src_id = src.source_id.split(':')[0]
            sites = srcfilter.get_close_sites(src)
            if sites is not None:
                acc.eff_ruptures[grp_id] += src.num_ruptures
                dt = time.time() - t0
                acc.calc_times[src_id] += numpy.array(
                    [src.weight, len(sites), dt, 1])
    return acc


@base.calculators.add('preclassical')
class PreCalculator(PSHACalculator):
    """
    Calculator to filter the sources and compute the number of effective
    ruptures
    """
    core_task = count_ruptures


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
    :param pgetter: an :class:`openquake.commonlib.getters.PmapGetter`
    :param hstats: a list of pairs (statname, statfunc)
    :param monitor: instance of Monitor
    :returns: a dictionary kind -> ProbabilityMap

    The "kind" is a string of the form 'rlz-XXX' or 'mean' of 'quantile-XXX'
    used to specify the kind of output.
    """
    with monitor('combine pmaps'):
        pgetter.init()  # if not already initialized
        try:
            pmaps = pgetter.get_pmaps(pgetter.sids)
        except IndexError:  # no data
            return {}
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
        num_rlzs = self.datastore['csm_info'].get_num_rlzs()
        if num_rlzs == 1:  # no stats to compute
            return {}
        elif not oq.hazard_stats():
            if oq.hazard_maps or oq.uniform_hazard_spectra:
                logging.warn('mean_hazard_curves was false in the job.ini, '
                             'so no outputs were generated.\nYou can compute '
                             'the statistics without repeating the calculation'
                             ' with the --hc option')
            return {}
        # initialize datasets
        N = len(self.sitecol.complete)
        L = len(oq.imtls.array)
        pyclass = 'openquake.hazardlib.probability_map.ProbabilityMap'
        all_sids = self.sitecol.complete.sids
        nbytes = N * L * 4  # bytes per realization (32 bit floats)
        totbytes = 0
        if num_rlzs > 1:
            for name, stat in oq.hazard_stats():
                self.datastore.create_dset(
                    'hcurves/%s/array' % name, F32, (N, L, 1))
                self.datastore['hcurves/%s/sids' % name] = all_sids
                self.datastore.set_attrs(
                    'hcurves/%s' % name, __pyclass__=pyclass)
                totbytes += nbytes
        if 'hcurves' in self.datastore:
            self.datastore.set_attrs('hcurves', nbytes=totbytes)
        self.datastore.flush()

        with self.monitor('sending pmaps', autoflush=True, measuremem=True):
            ires = parallel.Starmap(
                self.core_task.__func__, self.gen_args()
            ).submit_all()
        nbytes = ires.reduce(self.save_hcurves)
        return nbytes

    def gen_args(self):
        """
        :yields: pgetter, hstats, monitor
        """
        monitor = self.monitor('build_hcurves_and_stats')
        hstats = self.oqparam.hazard_stats()
        parent = self.can_read_parent() or self.datastore
        for t in self.sitecol.split_in_tiles(self.oqparam.concurrent_tasks):
            pgetter = getters.PmapGetter(parent, self.rlzs_assoc, t.sids)
            if parent is self.datastore:  # read now, not in the workers
                logging.info('Reading PoEs on %d sites', len(t))
                pgetter.init()
            yield pgetter, hstats, monitor

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
                    key = 'hcurves/%s/array' % kind
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
