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
import logging
import operator
import numpy

from openquake.baselib import parallel, hdf5, datastore
from openquake.baselib.python3compat import encode
from openquake.baselib.general import AccumDict, block_splitter
from openquake.hazardlib.calc.hazard_curve import classical, ProbabilityMap
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.hazardlib import source
from openquake.commonlib import calc
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
    Yield the iterargs again by populating 'source_data'
    """
    source_ids = []
    data = []
    for i, args in enumerate(iterargs, 1):
        source_ids.append(get_src_ids(args[0]))
        for src in args[0]:  # collect source data
            data.append((i, src.nsites, src.num_ruptures, src.weight))
        yield args
    dstore['task_sources'] = encode(source_ids)
    dstore.extend('source_data', numpy.array(data, source_data_dt))


@base.calculators.add('classical')
class ClassicalCalculator(base.HazardCalculator):
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
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(pmap_by_grp.calc_times)
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
        if self.oqparam.hazard_calculation_id:
            parent = datastore.read(self.oqparam.hazard_calculation_id)
            self.csm_info = parent['csm_info']
            parent.close()
            self.calc_stats(parent)  # post-processing
            return {}
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
                self.core_task.__func__, iterargs, self.monitor()
            ).submit_all()
        self.nsites = []
        acc = ires.reduce(self.agg_dicts, self.zerodict())
        if not self.nsites:
            raise RuntimeError('All sources were filtered out!')
        logging.info('Effective sites per task: %d', numpy.mean(self.nsites))
        self.store_csm_info(acc.eff_ruptures)
        return acc

    def gen_args(self, monitor):
        """
        Used in the case of large source model logic trees.

        :param monitor: a :class:`openquake.baselib.performance.Monitor`
        :yields: (sources, sites, gsims, monitor) tuples
        """
        oq = self.oqparam
        opt = self.oqparam.optimize_same_id_sources
        param = dict(
            truncation_level=oq.truncation_level, imtls=oq.imtls,
            filter_distance=oq.filter_distance, reqv=oq.get_reqv(),
            pointsource_distance=oq.pointsource_distance)
        minweight = source.MINWEIGHT * math.sqrt(len(self.sitecol))
        num_tasks = 0
        num_sources = 0
        maxweight = self.csm.get_maxweight(
            weight, oq.concurrent_tasks, minweight)
        if maxweight == minweight:
            logging.info('Using minweight=%d', minweight)
        else:
            logging.info('Using maxweight=%d', maxweight)

        if self.csm.has_dupl_sources and not opt:
            logging.warn('Found %d duplicated sources',
                         self.csm.has_dupl_sources)

        for sg in self.csm.src_groups:
            if sg.src_interdep == 'mutex' and len(sg) > 0:
                par = param.copy()
                par['src_interdep'] = sg.src_interdep
                par['rup_interdep'] = sg.rup_interdep
                par['grp_probability'] = sg.grp_probability
                gsims = self.csm.info.gsim_lt.get_gsims(sg.trt)
                yield sg.sources, self.src_filter, gsims, par, monitor
                num_tasks += 1
                num_sources += len(sg.sources)
        # NB: csm.get_sources_by_trt discards the mutex sources
        for trt, sources in self.csm.sources_by_trt.items():
            gsims = self.csm.info.gsim_lt.get_gsims(trt)
            for block in block_splitter(sources, maxweight, weight):
                yield block, self.src_filter, gsims, param, monitor
                num_tasks += 1
                num_sources += len(block)
        logging.info('Sent %d sources in %d tasks', num_sources, num_tasks)

    def gen_getters(self, parent):
        """
        :yields: pgetter, hstats, monitor
        """
        monitor = self.monitor('build_hazard_stats')
        hstats = self.oqparam.hazard_stats()
        for t in self.sitecol.split_in_tiles(self.oqparam.concurrent_tasks):
            pgetter = getters.PmapGetter(parent, self.rlzs_assoc, t.sids)
            if parent is self.datastore:  # read now, not in the workers
                logging.info('Reading PoEs on %d sites', len(t))
                pgetter.init()
            yield pgetter, hstats, monitor

    def save_hazard_stats(self, acc, pmap_by_kind):
        """
        Works by side effect by saving statistical hcurves and hmaps on the
        datastore.

        :param acc: ignored
        :param pmap_by_kind: a dictionary of ProbabilityMaps

        kind can be ('hcurves', 'mean'), ('hmaps', 'mean'),  ...
        """
        with self.monitor('saving statistics', autoflush=True):
            for kind in pmap_by_kind:  # i.e. kind == ('hcurves', 'mean')
                pmap = pmap_by_kind[kind]
                if pmap:
                    key = '%s/%s' % kind
                    dset = self.datastore.getitem(key)
                    for sid in pmap:
                        arr = pmap[sid].array[:, 0]
                        dset[sid] = arr
            self.datastore.flush()

    def post_execute(self, pmap_by_grp_id):
        """
        Collect the hazard curves by realization and export them.

        :param pmap_by_grp_id:
            a dictionary grp_id -> hazard curves
        """
        oq = self.oqparam
        csm_info = self.datastore['csm_info']
        grp_trt = csm_info.grp_by("trt")
        grp_source = csm_info.grp_by("name")
        if oq.disagg_by_src:
            src_name = {src.src_group_id: src.name
                        for src in self.csm.get_sources()}
        data = []
        with self.monitor('saving probability maps', autoflush=True):
            for grp_id, pmap in pmap_by_grp_id.items():
                if pmap:  # pmap can be missing if the group is filtered away
                    base.fix_ones(pmap)  # avoid saving PoEs == 1
                    key = 'poes/grp-%02d' % grp_id
                    self.datastore[key] = pmap
                    self.datastore.set_attrs(key, trt=grp_trt[grp_id])
                    if oq.disagg_by_src:
                        data.append(
                            (grp_id, grp_source[grp_id], src_name[grp_id]))
        if oq.hazard_calculation_id is None and 'poes' in self.datastore:
            self.datastore.set_nbytes('poes')
            if oq.disagg_by_src and csm_info.get_num_rlzs() == 1:
                # this is useful for disaggregation, which is implemented
                # only for the case of a single realization
                self.datastore['disagg_by_src/source_id'] = numpy.array(
                    sorted(data), grp_source_dt)

            # save a copy of the poes in hdf5cache
            if hasattr(self, 'hdf5cache'):
                with hdf5.File(self.hdf5cache) as cache:
                    cache['oqparam'] = oq
                    self.datastore.hdf5.copy('poes', cache)
                self.calc_stats(self.hdf5cache)
            else:
                self.calc_stats(self.datastore)

    def calc_stats(self, parent):
        oq = self.oqparam
        # initialize datasets
        N = len(self.sitecol.complete)
        L = len(oq.imtls.array)
        P = len(oq.poes)
        I = len(oq.imtls)
        for name, stat in oq.hazard_stats():
            self.datastore.create_dset('hcurves/%s' % name, F32, (N, L))
            self.datastore.set_attrs('hcurves/%s' % name, nbytes=N * L * 4)
            if oq.poes:
                self.datastore.create_dset('hmaps/' + name, F32, (N, P * I))
                self.datastore.set_attrs('hmaps/' + name, nbytes=N * P * I * 4)
        logging.info('Building hazard statistics')
        parallel.Starmap(
            build_hazard_stats, self.gen_getters(parent), self.monitor()
        ).reduce(self.save_hazard_stats)


@base.calculators.add('preclassical')
class PreCalculator(ClassicalCalculator):
    """
    Calculator to filter the sources and compute the number of effective
    ruptures
    """
    def execute(self):
        eff_ruptures = AccumDict(accum=0)
        for src in self.csm.get_sources():
            eff_ruptures[src.src_group_id] += src.num_ruptures
        self.store_csm_info(eff_ruptures)
        return {}


def build_hazard_stats(pgetter, hstats, monitor):
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
    for statname, stat in hstats:
        with monitor('compute ' + statname):
            pmap = compute_pmap_stats(pmaps, [stat], pgetter.weights)
        pmap_by_kind['hcurves', statname] = pmap
        if pgetter.poes:
            pmap_by_kind['hmaps', statname] = calc.make_hmap(
                pmap, pgetter.imtls, pgetter.poes)
    return pmap_by_kind
