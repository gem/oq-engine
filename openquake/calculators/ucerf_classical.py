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
import os
import time
import logging
from datetime import datetime
import numpy

from openquake.baselib.general import DictArray, AccumDict
from openquake.baselib import parallel
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib import valid
from openquake.commonlib import source, readinput, util
from openquake.hazardlib.sourceconverter import SourceConverter

from openquake.calculators import base
from openquake.calculators.classical import ClassicalCalculator, PSHACalculator
from openquake.calculators.ucerf_event_based import (
    UCERFSource, get_composite_source_model)
# FIXME: the counting of effective ruptures has to be revised


def convert_UCERFSource(self, node):
    """
    Converts the Ucerf Source node into an SES Control object
    """
    dirname = os.path.dirname(self.fname)  # where the source_model_file is
    source_file = os.path.join(dirname, node["filename"])
    if "startDate" in node.attrib and "investigationTime" in node.attrib:
        # Is a time-dependent model - even if rates were originally
        # poissonian
        # Verify that the source time span is the same as the TOM time span
        inv_time = float(node["investigationTime"])
        if inv_time != self.tom.time_span:
            raise ValueError("Source investigation time (%s) is not "
                             "equal to configuration investigation time "
                             "(%s)" % (inv_time, self.tom.time_span))
        start_date = datetime.strptime(node["startDate"], "%d/%m/%Y")
    else:
        start_date = None
    return UCERFSource(
        source_file,
        node["id"],
        self.tom.time_span,
        start_date,
        float(node["minMag"]),
        npd=self.convert_npdist(node),
        hdd=self.convert_hpdist(node),
        aspect=~node.ruptAspectRatio,
        upper_seismogenic_depth=~node.pointGeometry.upperSeismoDepth,
        lower_seismogenic_depth=~node.pointGeometry.lowerSeismoDepth,
        msr=valid.SCALEREL[~node.magScaleRel](),
        mesh_spacing=self.rupture_mesh_spacing,
        trt=node["tectonicRegion"])


SourceConverter.convert_UCERFSource = convert_UCERFSource


@util.reader
def ucerf_classical(rupset_idx, ucerf_source, src_filter, gsims, monitor):
    """
    :param rupset_idx:
        indices of the rupture sets
    :param ucerf_source:
        an object taking the place of a source for UCERF
    :param src_filter:
        a source filter returning the sites affected by the source
    :param gsims:
        a list of GSIMs
    :param monitor:
        a monitor instance
    :returns:
        a ProbabilityMap
    """
    t0 = time.time()
    truncation_level = monitor.oqparam.truncation_level
    imtls = monitor.oqparam.imtls
    ucerf_source.src_filter = src_filter  # so that .iter_ruptures() work
    grp_id = ucerf_source.src_group_id
    mag = ucerf_source.mags[rupset_idx].max()
    ridx = set()
    for idx in rupset_idx:
        ridx.update(ucerf_source.get_ridx(idx))
    ucerf_source.rupset_idx = rupset_idx
    ucerf_source.num_ruptures = nruptures = len(rupset_idx)

    # prefilter the sites close to the rupture set
    s_sites = ucerf_source.get_rupture_sites(ridx, src_filter, mag)
    if s_sites is None:  # return an empty probability map
        pm = ProbabilityMap(len(imtls.array), len(gsims))
        acc = AccumDict({grp_id: pm})
        acc.calc_times = {
            ucerf_source.source_id:
            numpy.array([nruptures, 0, time.time() - t0, 1])}
        acc.eff_ruptures = {grp_id: 0}
        return acc

    # compute the ProbabilityMap
    cmaker = ContextMaker(gsims, src_filter.integration_distance,
                          monitor=monitor)
    imtls = DictArray(imtls)
    pmap = cmaker.poe_map(ucerf_source, s_sites, imtls, truncation_level)
    nsites = len(s_sites)
    acc = AccumDict({grp_id: pmap})
    acc.calc_times = {
        ucerf_source.source_id:
        numpy.array([nruptures * nsites, nsites, time.time() - t0, 1])}
    acc.eff_ruptures = {grp_id: ucerf_source.num_ruptures}
    return acc


@base.calculators.add('ucerf_psha')
class UcerfPSHACalculator(PSHACalculator):
    """
    UCERF classical calculator.
    """
    core_task = ucerf_classical
    is_stochastic = False

    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        logging.warn('%s is still experimental', self.__class__.__name__)
        sitecol = readinput.get_site_collection(self.oqparam)
        self.datastore['sitecol'] = self.sitecol = sitecol
        self.csm = get_composite_source_model(self.oqparam)
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
        monitor.oqparam = oq = self.oqparam
        self.src_filter = SourceFilter(self.sitecol, oq.maximum_distance)
        self.nsites = []
        acc = AccumDict({
            grp_id: ProbabilityMap(len(oq.imtls.array), len(gsims))
            for grp_id, gsims in self.gsims_by_grp.items()})
        acc.calc_times = {}
        acc.eff_ruptures = AccumDict()  # grp_id -> eff_ruptures
        acc.bb_dict = {}  # just for API compatibility
        param = dict(imtls=oq.imtls, truncation_level=oq.truncation_level,
                     filter_distance=oq.filter_distance)
        for sm in self.csm.source_models:  # one branch at the time
            grp_id = sm.ordinal
            gsims = self.gsims_by_grp[grp_id]
            [[ucerf_source]] = sm.src_groups
            ucerf_source.nsites = len(self.sitecol)
            self.csm.infos[ucerf_source.source_id] = source.SourceInfo(
                ucerf_source)
            ct = self.oqparam.concurrent_tasks or 1

            # parallelize by rupture subsets
            rup_sets = numpy.arange(ucerf_source.num_ruptures)
            taskname = 'ucerf_classical_%d' % grp_id
            acc = parallel.Starmap.apply(
                ucerf_classical,
                (rup_sets, ucerf_source, self.src_filter, gsims, monitor),
                concurrent_tasks=ct, name=taskname
            ).reduce(self.agg_dicts, acc)

            # parallelize on the background sources, small tasks
            bckgnd_sources = ucerf_source.get_background_sources(
                self.src_filter)
            args = (bckgnd_sources, self.src_filter, gsims, param, monitor)
            bg_res = parallel.Starmap.apply(
                classical, args, name='background_sources_%d' % grp_id,
                concurrent_tasks=ct)
            # compose probabilities from background sources
            for pmap in bg_res:
                acc[grp_id] |= pmap[grp_id]

        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(self.csm.infos, acc)
        return acc  # {grp_id: pmap}


@base.calculators.add('ucerf_classical')
class UCERFClassicalCalculator(ClassicalCalculator):
    pre_calculator = 'ucerf_psha'
