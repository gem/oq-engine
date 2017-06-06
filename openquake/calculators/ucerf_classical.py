# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
import socket
import logging
import functools
from datetime import datetime
import numpy
import h5py

from openquake.baselib.general import DictArray, AccumDict
from openquake.baselib import parallel
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.calc.hazard_curve import pmap_from_grp, poe_map
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib import valid
from openquake.commonlib import source, readinput, util
from openquake.hazardlib.sourceconverter import SourceConverter

from openquake.calculators import base, classical
from openquake.calculators.ucerf_event_based import (
    UCERFControl, get_composite_source_model)
# FIXME: the counting of effective ruptures has to be revised completely


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
    return UCERFControl(
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
def ucerf_classical(
        rupset_idx, ucerf_source, src_filter, gsims, monitor):
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

    # prefilter the sites close to the rupture set
    with h5py.File(ucerf_source.control.source_file, "r") as hdf5:
        mag = hdf5[ucerf_source.idx_set["mag_idx"]][rupset_idx].max()
        ridx = set()
        # find the combination of rupture sections used in this model
        rup_index_key = "/".join(
            [ucerf_source.idx_set["geol_idx"], "RuptureIndex"])
        # determine which of the rupture sections used in this set of indices
        rup_index = hdf5[rup_index_key]
        for i in rupset_idx:
            ridx.update(rup_index[i])
        s_sites = ucerf_source.get_rupture_sites(hdf5, ridx, src_filter, mag)
        if s_sites is None:  # return an empty probability map
            pm = ProbabilityMap(len(imtls.array), len(gsims))
            pm.calc_times = []  # TODO: fix .calc_times
            pm.eff_ruptures = {ucerf_source.src_group_id: 0}
            pm.grp_id = ucerf_source.src_group_id
            return pm

    # compute the ProbabilityMap by using hazardlib.calc.hazard_curve.poe_map
    ucerf_source.rupset_idx = rupset_idx
    ucerf_source.num_ruptures = len(rupset_idx)
    cmaker = ContextMaker(gsims, src_filter.integration_distance)
    imtls = DictArray(imtls)
    ctx_mon = monitor('making contexts', measuremem=False)
    pne_mons = [monitor('%s.get_poes' % gsim, measuremem=False)
                for gsim in gsims]
    pmap = poe_map(ucerf_source, s_sites, imtls, cmaker,
                   truncation_level, ctx_mon, pne_mons)
    nsites = len(s_sites)
    pmap.calc_times = [(ucerf_source.source_id, nsites, time.time() - t0)]
    pmap.grp_id = ucerf_source.src_group_id
    pmap.eff_ruptures = {pmap.grp_id: ucerf_source.num_ruptures}
    return pmap


@base.calculators.add('ucerf_psha')
class UcerfPSHACalculator(classical.PSHACalculator):
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
        self.sitecol = readinput.get_site_collection(self.oqparam)
        self.csm = get_composite_source_model(self.oqparam)
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc()
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
        acc = AccumDict({
            grp_id: ProbabilityMap(len(oq.imtls.array), len(gsims))
            for grp_id, gsims in self.rlzs_assoc.gsims_by_grp_id.items()})
        acc.calc_times = []
        acc.eff_ruptures = AccumDict()  # grp_id -> eff_ruptures
        acc.bb_dict = {}  # just for API compatibility

        for sm in self.csm.source_models:  # one branch at the time
            grp_id = sm.ordinal
            gsims = self.rlzs_assoc.gsims_by_grp_id[grp_id]
            [[ucerf_source]] = sm.src_groups
            ucerf_source.nsites = len(self.sitecol)
            self.csm.infos[grp_id, ucerf_source.source_id] = source.SourceInfo(
                ucerf_source)
            logging.info('Getting the background point sources')
            bckgnd_sources = ucerf_source.get_background_sources(
                self.src_filter)

            # since there are two kinds of tasks (background and rupture_set)
            # we divide the concurrent_tasks parameter by 2;
            # notice the "or 1" below, to avoid issues when
            # self.oqparam.concurrent_tasks is 0 or 1
            ct2 = (self.oqparam.concurrent_tasks // 2) or 1

            # parallelize on the background sources, small tasks
            args = (bckgnd_sources, self.src_filter, oq.imtls,
                    gsims, self.oqparam.truncation_level, (), monitor)
            bg_res = parallel.Starmap.apply(
                pmap_from_grp, args, name='background_sources_%d' % grp_id,
                concurrent_tasks=ct2).submit_all()

            # parallelize by rupture subsets
            rup_sets = numpy.arange(ucerf_source.num_ruptures)
            taskname = 'ucerf_classical_%d' % grp_id
            acc = parallel.Starmap.apply(
                ucerf_classical,
                (rup_sets, ucerf_source, self.src_filter, gsims, monitor),
                concurrent_tasks=ct2, name=taskname
            ).reduce(self.agg_dicts, acc)

            # compose probabilities from background sources
            for pmap in bg_res:
                acc[grp_id] |= pmap

        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(self.csm.infos, acc)
        return acc  # {grp_id: pmap}


@base.calculators.add('ucerf_classical')
class UCERFClassicalCalculator(classical.ClassicalCalculator):
    pre_calculator = 'ucerf_psha'
