# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
import logging

from openquake.baselib.general import AccumDict
from openquake.baselib import parallel
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.commonlib import readinput, source

from openquake.calculators import base
from openquake.calculators.classical import ClassicalCalculator, PSHACalculator
from openquake.calculators.ucerf_base import UcerfFilter
# FIXME: the counting of effective ruptures has to be revised


@base.calculators.add('ucerf_psha')
class UcerfPSHACalculator(PSHACalculator):
    """
    UCERF classical calculator.
    """
    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        logging.warn('%s is still experimental', self.__class__.__name__)
        sitecol = readinput.get_site_collection(self.oqparam)
        self.datastore['sitecol'] = self.sitecol = sitecol
        self.csm = readinput.get_composite_source_model(self.oqparam)
        self.csm.split_all()
        self.gsims_by_grp = {grp.id: self.csm.info.get_gsims(grp.id)
                             for sm in self.csm.source_models
                             for grp in sm.src_groups}
        self.rup_data = {}

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        monitor = self.monitor(self.core_task.__name__)
        oq = self.oqparam
        self.src_filter = UcerfFilter(self.sitecol, oq.maximum_distance)
        self.nsites = []
        acc = AccumDict({
            grp_id: ProbabilityMap(len(oq.imtls.array), len(gsims))
            for grp_id, gsims in self.gsims_by_grp.items()})
        acc.calc_times = {}
        acc.eff_ruptures = AccumDict()  # grp_id -> eff_ruptures
        param = dict(imtls=oq.imtls, truncation_level=oq.truncation_level,
                     filter_distance=oq.filter_distance)
        for sm in self.csm.source_models:  # one branch at the time
            sources = []
            grp_id = sm.ordinal
            gsims = self.gsims_by_grp[grp_id]
            [grp] = sm.src_groups
            ucerf = grp[0]
            self.csm.infos[ucerf.source_id] = source.SourceInfo(ucerf)
            ct = self.oqparam.concurrent_tasks or 1
            logging.info('Getting background sources for %s', ucerf.source_id)
            bg_sources = ucerf.get_background_sources(self.src_filter)
            sources.extend(grp)
            sources.extend(bg_sources)
            acc = parallel.Starmap.apply(
                classical, (sources, self.src_filter, gsims, param, monitor),
                name='classical_%d' % grp_id, concurrent_tasks=ct * 2
            ).reduce(self.agg_dicts, acc)

        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(self.csm.infos, acc)
        return acc  # {grp_id: pmap}


@base.calculators.add('ucerf_classical')
class UCERFClassicalCalculator(ClassicalCalculator):
    pre_calculator = 'ucerf_psha'
