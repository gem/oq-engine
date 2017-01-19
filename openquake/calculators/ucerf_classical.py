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
import sys
import h5py
import numpy as np
import copy
import time
import logging
import functools

from openquake.baselib.performance import Monitor
from openquake.baselib.python3compat import raise_
from openquake.baselib.general import DictArray, AccumDict
from openquake.baselib import parallel
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.geodetic import min_geodetic_distance
from openquake.hazardlib.source import PointSource
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.calc.hazard_curve import (
    get_probability_no_exceedance, pmap_from_grp)
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.hazardlib import valid, nrml
from openquake.commonlib import source, readinput
from openquake.hazardlib.sourceconverter import SourceConverter

from openquake.calculators import base, classical
from openquake.calculators.ucerf_event_based import (
    UCERFSESControl, get_ucerf_rupture, DEFAULT_TRT)


class UCERFControl(UCERFSESControl):
    """
    General control file for a UCERF branch for the classical calculator.
    Here we add a new method to generate a set of background sources per
    branch
    """
    def get_background_sources(self, background_sids):
        """
        Turn the background model of a given branch into a set of point sources

        :param str branch_id:
            Valid ID of a UCERF branch
        :param background_sids:
            Site IDs affected by the background sources
        """
        with h5py.File(self.source_file, "r") as hdf5:
            grid_loc = "/".join(["Grid", self.idx_set["grid_key"]])
            mags = hdf5[grid_loc + "/Magnitude"][:]
            mmax = hdf5[grid_loc + "/MMax"][background_sids]
            rates = hdf5[grid_loc + "/RateArray"][background_sids, :]
            locations = hdf5["Grid/Locations"][background_sids, :]
            sources = []
            for i, bg_idx in enumerate(background_sids):
                src_id = "_".join([self.idx_set["grid_key"], str(bg_idx)])
                src_name = "|".join([self.idx_set["total_key"], str(bg_idx)])
                # Get MFD
                mag_idx = np.logical_and(mags >= self.min_mag, mags < mmax[i])
                src_mags = mags[mag_idx]
                src_rates = rates[i, :]
                src_mfd = EvenlyDiscretizedMFD(
                    src_mags[0], src_mags[1] - src_mags[0],
                    src_rates[mag_idx].tolist())
                ps = PointSource(
                    src_id, src_name, self.tectonic_region_type, src_mfd,
                    self.mesh_spacing, self.msr, self.aspect, self.tom,
                    self.usd, self.lsd,
                    Point(locations[i, 0], locations[i, 1]),
                    self.npd, self.hdd)
                sources.append(ps)
        return sources

    def get_rupture_indices(self, branch_id):
        """
        Returns a set of rupture indices
        """
        with h5py.File(self.source_file, "r") as hdf5:
            idxs = np.arange(len(hdf5[self.idx_set["rate_idx"]]))
        logging.info('Found %d ruptures in %s', len(idxs), self.source_file)
        logging.info(branch_id)
        return idxs

    def filter_sites_by_distance_from_rupture_set(
            self, rupset_idx, sites, max_dist):
        """
        Filter sites by distances from a set of ruptures
        """
        with h5py.File(self.source_file, "r") as hdf5:
            rup_index_key = "/".join([self.idx_set["geol_idx"],
                                      "RuptureIndex"])

            # Find the combination of rupture sections used in this model
            rupture_set = set()
            # Determine which of the rupture sections used in this set
            # of indices
            rup_index = hdf5[rup_index_key]
            for i in rupset_idx:
                rupture_set.update(rup_index[i])
            centroids = np.empty([1, 3])
            # For each of the identified rupture sections, retreive the
            # centroids
            for ridx in rupture_set:
                trace_idx = "{:s}/{:s}".format(self.idx_set["sec_idx"],
                                               str(ridx))
                centroids = np.vstack([
                    centroids,
                    hdf5[trace_idx + "/Centroids"][:].astype("float64")])
            distance = min_geodetic_distance(centroids[1:, 0],
                                             centroids[1:, 1],
                                             sites.lons, sites.lats)
            idx = distance <= max_dist
            if np.any(idx):
                return rupset_idx, sites.filter(idx)
            else:
                return [], []


def ucerf_poe_map(hdf5, ucerf_source, rupset_idx, s_sites, imtls, cmaker,
                  trunclevel, ctx_mon, pne_mon):
    """
    Compute a ProbabilityMap generated by the given set of indices.

    :param hdf5:
        UCERF file as instance of open h5py.File object
    :param ucerf_source:
        UCERFControl object
    :param list rupset_idx:
        List of rupture indices
    """
    pmap = ProbabilityMap.build(len(imtls.array), len(cmaker.gsims),
                                s_sites.sids, initvalue=1.)
    try:
        for ridx in rupset_idx:
            # Get the ucerf rupture
            if not hdf5[ucerf_source.idx_set["rate_idx"]][ridx]:
                # Ruptures seem to have a zero probability from time to time
                # If this happens, skip it
                continue

            rup, ridx_string = get_ucerf_rupture(
                hdf5, ridx,
                ucerf_source.idx_set,
                ucerf_source.tom, s_sites,
                ucerf_source.integration_distance,
                ucerf_source.mesh_spacing,
                ucerf_source.tectonic_region_type)
            if not rup:
                # rupture outside of integration distance
                continue
            with ctx_mon:  # compute distances
                try:
                    sctx, rctx, dctx = cmaker.make_contexts(s_sites, rup)
                except FarAwayRupture:
                    continue
            with pne_mon:  # compute probabilities and updates the pmap
                pnes = get_probability_no_exceedance(
                    rup, sctx, rctx, dctx, imtls, cmaker.gsims, trunclevel)
                for sid, pne in zip(sctx.sites.sids, pnes):
                    pmap[sid].array *= pne
    except Exception as err:
        etype, err, tb = sys.exc_info()
        msg = 'An error occurred with rupture=%s. Error: %s'
        msg %= (ridx, str(err))
        raise_(etype, msg, tb)
    return ~pmap


def convert_UCERFSource(self, node):
    """
    Converts the Ucerf Source node into an SES Control object
    """
    dirname = os.path.dirname(self.fname)  # where the source_model_file is
    source_file = os.path.join(dirname, node["filename"])
    return UCERFControl(
        source_file,
        node["id"],
        self.tom.time_span,
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


def hazard_curves_per_rupture_subset(
        rupset_idx, ucerf_source, src_filter, imtls, cmaker,
        truncation_level=None, monitor=Monitor()):
    """
    Calculates the probabilities of exceedence from a set of rupture indices
    """
    imtls = DictArray(imtls)
    ctx_mon = monitor('making contexts', measuremem=False)
    pne_mon = monitor('computing poes', measuremem=False)
    pmap = ProbabilityMap(len(imtls.array), len(cmaker.gsims))
    pmap.calc_times = []
    pmap.eff_ruptures = 0
    pmap.grp_id = ucerf_source.src_group_id
    nsites = len(src_filter.sitecol)
    with h5py.File(ucerf_source.source_file, "r") as hdf5:
        t0 = time.time()
        pmap |= ucerf_poe_map(hdf5, ucerf_source, rupset_idx,
                              src_filter.sitecol, imtls, cmaker,
                              truncation_level, ctx_mon, pne_mon)
        pmap.calc_times.append(
            (ucerf_source.source_id, nsites, time.time() - t0))
        pmap.eff_ruptures += pne_mon.counts
    return pmap


def ucerf_classical_hazard_by_rupture_set(
        rupset_idx, branchname, ucerf_source, src_group_id, src_filter,
        gsims, monitor):
    """
    :param rupset_idx:
        indices of the rupture sets
    :param branchname:
        name of the branch
    :param ucerf_source:
        an object taking the place of a source for UCERF
    :param src_group_id:
        source group index
    :param src_filter:
        a source filter returning the sites affected by the source
    :param gsims:
        a list of GSIMs
    :param monitor:
        a monitor instance
    :returns:
        an AccumDict rlz -> curves
    """
    truncation_level = monitor.oqparam.truncation_level
    imtls = monitor.oqparam.imtls
    max_dist = monitor.oqparam.maximum_distance[DEFAULT_TRT]

    # Apply the initial rupture to site filtering
    rupset_idx, s_sites = \
        ucerf_source.filter_sites_by_distance_from_rupture_set(
            rupset_idx, src_filter.sitecol, max_dist)

    if len(s_sites):
        cmaker = ContextMaker(gsims, max_dist)
        pmap = hazard_curves_per_rupture_subset(
            rupset_idx, ucerf_source, src_filter, imtls, cmaker,
            truncation_level, monitor=monitor)
    else:
        pmap = ProbabilityMap(len(imtls.array), len(gsims))
        pmap.calc_times = []
        pmap.eff_ruptures = {src_group_id: 0}
    pmap.grp_id = ucerf_source.src_group_id
    return pmap


def ucerf_classical_hazard_by_branch(branchname, ucerf_source, src_group_id,
                                     src_filter, gsims, monitor):
    """
    :param branchname:
        a branch name
    :param ucerf_source:
        a source-like object for the UCERF model
    :param src_group_id:
        an ordinal number for the source
    :param source filter:
        a filter returning the sites affected by the source
    :param gsims:
        a list of GSIMs
    :param monitor:
        a monitor instance
    :returns:
        an AccumDict rlz -> curves
    """
    truncation_level = monitor.oqparam.truncation_level
    imtls = monitor.oqparam.imtls
    trt = ucerf_source.tectonic_region_type
    max_dist = monitor.oqparam.maximum_distance[trt]
    dic = AccumDict()
    dic.calc_times = []

    # Two step process here - the first generates the hazard curves from
    # the rupture sets
    monitor.eff_ruptures = 0
    # Apply the initial rupture to site filtering
    rupset_idx = ucerf_source.get_rupture_indices(branchname)
    rupset_idx, s_sites = \
        ucerf_source.filter_sites_by_distance_from_rupture_set(
            rupset_idx, src_filter.sitecol, max_dist)

    if len(s_sites):
        cmaker = ContextMaker(gsims, max_dist)
        dic[src_group_id] = pm = hazard_curves_per_rupture_subset(
            rupset_idx, ucerf_source, src_filter, imtls, cmaker,
            truncation_level, monitor=monitor)
        dic.calc_times.extend(pm.calc_times)
    else:
        dic[src_group_id] = ProbabilityMap(len(imtls.array), len(gsims))
    dic.eff_ruptures = {src_group_id: monitor.eff_ruptures}  # idem
    logging.info('Branch %s', branchname)
    # Get the background point sources
    background_sids = ucerf_source.get_background_sids(
        src_filter.sitecol, max_dist)
    bckgnd_sources = ucerf_source.get_background_sources(background_sids)
    if bckgnd_sources:
        pmap = pmap_from_grp(
            bckgnd_sources, src_filter, imtls, gsims, truncation_level,
            (), monitor=monitor)
        dic[src_group_id] |= pmap
        dic.eff_ruptures[src_group_id] += monitor.eff_ruptures
        dic.calc_times.extend(pmap.calc_times)
    return dic


@base.calculators.add('ucerf_psha')
class UcerfPSHACalculator(classical.PSHACalculator):
    """
    UCERF classical calculator.
    """
    core_task = ucerf_classical_hazard_by_branch
    is_stochastic = False

    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        self.sitecol = readinput.get_site_collection(self.oqparam)
        self.gsim_lt = readinput.get_gsim_lt(self.oqparam, [DEFAULT_TRT])
        self.smlt = readinput.get_source_model_lt(self.oqparam)
        parser = nrml.SourceModelParser(
            SourceConverter(self.oqparam.investigation_time,
                            self.oqparam.rupture_mesh_spacing))
        [self.src_group] = parser.parse_src_groups(
            self.oqparam.inputs["source_model"])
        source_models = []
        for sm in self.smlt.gen_source_models(self.gsim_lt):
            sg = copy.copy(self.src_group)
            sm.src_groups = [sg]
            [src] = sg
            # Update the event set
            src.src_group_id = sg.id = sm.ordinal
            src.nsites = len(self.sitecol)
            src.branch_id = sm.name
            src.idx_set = src.build_idx_set()
            source_models.append(sm)
        self.csm = source.CompositeSourceModel(
            self.gsim_lt, self.smlt, source_models, set_weight=False)
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc()
        self.rup_data = {}
        self.num_tiles = 1
        self.infos = {}

    def gen_args(self, branches, ucerf_source, monitor):
        """
        :yields: (branch, ucerf_source, grp_id, self.sitecol, gsims, monitor)
        """
        for grp_id, branch in enumerate(branches):
            gsims = self.rlzs_assoc.gsims_by_grp_id[grp_id]
            self.infos[grp_id, ucerf_source.source_id] = source.SourceInfo(
                ucerf_source)
            yield branch, ucerf_source, grp_id, self.src_filter, gsims, monitor

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        monitor = self.monitor.new(self.core_task.__name__)
        monitor.oqparam = oq = self.oqparam
        ucerf_source = self.src_group.sources[0]
        self.src_filter = SourceFilter(self.sitecol, oq.maximum_distance)
        acc = AccumDict({
            grp_id: ProbabilityMap(len(oq.imtls.array), len(gsims))
            for grp_id, gsims in self.rlzs_assoc.gsims_by_grp_id.items()})
        acc.calc_times = []
        acc.eff_ruptures = AccumDict()  # grp_id -> eff_ruptures
        acc.bb_dict = {}  # just for API compatibility

        if len(self.csm) > 1:
            # when multiple branches, parallelise by branch
            branches = [br.value for br in self.smlt.branches.values()]
            rup_res = parallel.Starmap(
                ucerf_classical_hazard_by_branch,
                self.gen_args(branches, ucerf_source, monitor)).submit_all()
        else:
            # single branch
            gsims = self.rlzs_assoc.gsims_by_grp_id[0]
            [(branch_id, branch)] = self.smlt.branches.items()
            branchname = branch.value
            ucerf_source.src_group_id = 0
            ucerf_source.weight = 1
            ucerf_source.nsites = len(self.sitecol)
            self.infos[0, ucerf_source.source_id] = source.SourceInfo(
                ucerf_source)
            logging.info('Getting the background point sources')
            with self.monitor('getting background sources', autoflush=True):
                background_sids = ucerf_source.get_background_sids(
                    self.sitecol, oq.maximum_distance[DEFAULT_TRT])
                bckgnd_sources = ucerf_source.get_background_sources(
                    background_sids)

            # parallelize on the background sources, small tasks
            args = (bckgnd_sources, self.src_filter, oq.imtls,
                    gsims, self.oqparam.truncation_level, (), monitor)
            bg_res = parallel.Starmap.apply(
                pmap_from_grp, args,
                concurrent_tasks=self.oqparam.concurrent_tasks).submit_all()

            # parallelize by rupture subsets
            tasks = self.oqparam.concurrent_tasks * 2  # they are big tasks
            rup_sets = ucerf_source.get_rupture_indices(branchname)
            rup_res = parallel.Starmap.apply(
                ucerf_classical_hazard_by_rupture_set,
                (rup_sets, branchname, ucerf_source, self.src_group.id,
                 self.src_filter, gsims, monitor),
                concurrent_tasks=tasks).submit_all()

            # compose probabilities from background sources
            for pmap in bg_res:
                acc[0] |= pmap
            self.save_data_transfer(bg_res)

        pmap_by_grp_id = functools.reduce(self.agg_dicts, rup_res, acc)
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(self.infos)
            self.save_data_transfer(rup_res)
        self.datastore['csm_info'] = self.csm.info
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc(
            functools.partial(self.count_eff_ruptures, pmap_by_grp_id))
        return pmap_by_grp_id


@base.calculators.add('ucerf_classical')
class UCERFClassicalCalculator(classical.ClassicalCalculator):
    pre_calculator = 'ucerf_psha'
