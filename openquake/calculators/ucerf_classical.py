# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import numpy as np
from openquake.baselib import parallel, general
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.calculators import base
from openquake.calculators.classical import (
    ClassicalCalculator, classical_split_filter)


@base.calculators.add('ucerf_classical')
class UcerfClassicalCalculator(ClassicalCalculator):
    """
    UCERF classical calculator.
    """
    accept_precalc = ['ucerf_psha']

    def pre_execute(self):
        super().pre_execute()
        self.csm_info = self.csm.info
        for sm in self.csm.source_models:  # one branch at the time
            [grp] = sm.src_groups
            for src in grp:
                grp.tot_ruptures += src.num_ruptures

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        monitor = self.monitor(self.core_task.__name__)
        oq = self.oqparam
        acc = self.acc0()
        self.nsites = []  # used in agg_dicts
        param = dict(imtls=oq.imtls, truncation_level=oq.truncation_level,
                     filter_distance=oq.filter_distance, maxweight=1E10)
        self.calc_times = general.AccumDict(accum=np.zeros(2, np.float32))
        rlzs_by_gsim = self.csm.info.get_rlzs_by_gsim_grp()
        for sm in self.csm.source_models:  # one branch at the time
            [grp] = sm.src_groups
            gsims = list(rlzs_by_gsim[grp.id])
            acc = parallel.Starmap.apply(
                classical_split_filter,
                (grp, self.src_filter, gsims, param, monitor),
                weight=operator.attrgetter('weight'),
                concurrent_tasks=oq.concurrent_tasks,
            ).reduce(self.agg_dicts, acc)
            ucerf = grp.sources[0].orig
            logging.info('Getting background sources from %s', ucerf.source_id)
            sample = .001 if os.environ.get('OQ_SAMPLE_SOURCES') else None
            srcs = ucerf.get_background_sources(self.src_filter, sample)
            acc = parallel.Starmap.apply(
                classical, (srcs, self.src_filter, gsims, param, monitor),
                weight=operator.attrgetter('weight'),
                concurrent_tasks=oq.concurrent_tasks,
            ).reduce(self.agg_dicts, acc)
        self.store_rlz_info(acc.eff_ruptures)
        self.store_source_info(self.calc_times)
        return acc  # {grp_id: pmap}
