#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2019, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import logging
import numpy
from openquake.baselib import parallel, general
from openquake.hazardlib.calc.filters import split_sources
from openquake.commonlib import readinput
from openquake.calculators.classical import (
    base, classical, ClassicalCalculator, weight)

MAXWEIGHT = 1000


def classical_launcher(src_group, src_filter, gsims, param, monitor):
    if hasattr(src_group, 'atomic') and src_group.atomic:
        yield classical(src_group, src_filter, gsims, param)
        return
    isources = src_filter.filter(
        split_sources(src_filter.filter(src_group), times=False))
    for block in general.block_splitter(isources, MAXWEIGHT, weight):
        yield classical, block, src_filter, gsims, param


@base.calculators.add('classical_simple')
class SimpleCalculator(ClassicalCalculator):
    def pre_execute(self):
        oq = self.oqparam
        self.sitecol = readinput.get_site_collection(oq)
        self.csm = readinput.get_composite_source_model(oq)
        self.param = dict(
            truncation_level=oq.truncation_level, imtls=oq.imtls,
            filter_distance=oq.filter_distance, reqv=oq.get_reqv(),
            pointsource_distance=oq.pointsource_distance)

    def execute(self):
        smap = parallel.Starmap(classical_launcher, monitor=self.monitor())
        csm_atomic, sources_by_trt = self.csm.split2()
        for sg in csm_atomic.src_groups:
            gsims = self.csm.info.gsim_lt.get_gsims(sg.trt)
            smap.submit(sg, self.src_filter, gsims, self.param)
        for trt, sources in sources_by_trt.items():
            gsims = self.csm.info.gsim_lt.get_gsims(trt)
            for block in self.block_splitter(sources):
                smap.submit(block, self.src_filter, gsims, self.param)

        self.nsites = []
        self.calc_times = general.AccumDict(
            accum=numpy.zeros(3, numpy.float32))
        acc = smap.reduce(self.agg_dicts, self.acc0())
        self.store_csm_info(acc.eff_ruptures)
        if not self.nsites:
            raise RuntimeError('All sources were filtered out!')
        logging.info('Effective sites per task: %d', numpy.mean(self.nsites))
