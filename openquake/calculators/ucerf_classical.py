# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2016 GEM Foundation
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
import h5py
import numpy as np
import copy
import time
import logging

from openquake.baselib.performance import Monitor
from openquake.baselib.general import groupby, DictArray, AccumDict
#from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.geodetic import min_geodetic_distance
from openquake.hazardlib.source import PointSource
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.calc.filters import (source_site_distance_filter,
                                              source_site_noop_filter)
from openquake.hazardlib.calc.hazard_curve import (
    get_probability_no_exceedance, hazard_curves_per_trt)
from openquake.hazardlib.calc import filters
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.risklib import valid
from openquake.commonlib import parallel, datastore, source, calc, readinput
from openquake.commonlib.sourceconverter import SourceConverter

#from ucerf_branch_generator import lt_set, enumerate_set
from openquake.calculators import base, classical
from openquake.calculators.ucerf_event_based import (UCERFSESControl,
                                                     get_ucerf_rupture,
                                                     DEFAULT_TRT,
                                                     DEFAULT_MESH_SPACING)

DEFAULT_SPLIT = 100

class UCERFControl(UCERFSESControl):
    """
    General control file for a UCERF branch for the classical calculator.
    Here we add a new method to generate a set of background sources per
    branch
    """
    def get_background_sources(self, branch_id, sites,
                               integration_distance=1000.0):
        """
        Turn the background model of a given branch into a set of point sources

        :param str branch_id:
            Valid ID of a UCERF branch
        :param sites:
            Sites used to filter the model, as instance of
            openquake.hazardlib.site.SiteCollection
        :param float integration_distance:
            Maximum source to site distance (km)
        """
        if not self.idx_set:
            self.idx_set = self.build_idx_set(branch_id)
        self.update_background_site_filter(branch_id,
                                           sites,
                                           integration_distance)

        with h5py.File(self.source_file, "r") as hdf5:
            background_idx = np.where(self.background_idx)[0].tolist()
            grid_loc = "/".join(["Grid", self.idx_set["grid_key"]])
            mags = hdf5[grid_loc + "/Magnitude"][:]
            mmax = hdf5[grid_loc + "/MMax"][background_idx]
            rates = hdf5[grid_loc + "/RateArray"][background_idx, :]
            locations = hdf5["Grid/Locations"][background_idx, :]
            sources = []
            for i, bg_idx in enumerate(background_idx):
                src_id = "_".join([self.idx_set["grid_key"], str(bg_idx)])
                src_name = "|".join([self.idx_set["total_key"], str(bg_idx)])
                # Get MFD
                mag_idx = np.logical_and(mags >= self.min_mag,
                                         mags < mmax[i])
                src_mags = mags[mag_idx]
                src_rates = rates[i, :]
                src_mfd = EvenlyDiscretizedMFD(src_mags[0],
                                               src_mags[1] - src_mags[0],
                                               src_rates[mag_idx].tolist())
                sources.append(PointSource(
                               src_id,
                               src_name,
                               self.tectonic_region_type,
                               src_mfd,
                               self.mesh_spacing,
                               self.msr,
                               self.aspect,
                               self.tom,
                               self.usd,
                               self.lsd,
                               Point(locations[i, 0], locations[i, 1]),
                               self.npd,
                               self.hdd))
        return sources
        
#    def __iter__(self):
#        """
#        A bit of trickery here! The __iter__ method will split a vector
#        of rupture indices [0, 1, 2, ..., Nrup] into a number of subsets
#        or rupture indices, the number given by the DEFAULT_SPLIT option
#        """
#        with h5py.File(self.source_file, "r") as hdf5:
#            nrup = len(hdf5[self.idx_set["rate_idx"]][:])
#            rup_indices = np.arange(0, nrup)
#            for ridx in np.array_split(rup_indices, DEFAULT_SPLIT):
#                yield ridx

    def get_rupture_indices(self, branch_id, split=0):
        """
        Returns a set of rupture indices
        """
        if not self.idx_set:
            self.idx_set = self.build_idx_set(branch_id)
        with h5py.File(self.source_file, "r") as hdf5:
            nrup = len(hdf5[self.idx_set["rate_idx"]][:])
            rup_indices = np.arange(0, nrup)
            if split:
                return [np.array_split(rup_indices, split)]
            else:
                return rup_indices
    
    def filter_sites_by_distance_from_rupture_set(self, rupset_idx, sites,
                                                  max_dist):
        """
        Filter sites by distances from a set of ruptures     
        """
        with h5py.File(self.source_file, "r") as hdf5:
            rup_index_key = "/".join([self.idx_set["geol_idx"],
                                      "RuptureIndex"])

            # Find the combination of rupture sections used in this model
            rupset_indices = []
            rupture_set = set(())
            # Determine which of the rupture sections used in this set
            # of indices
            for i in rupset_idx:
                rupture_set.update(hdf5[rup_index_key][i])
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
                #print np.where(idx)[0]
                return rupset_idx, sites.filter(idx)
            else:
                return [], []

                
                
def ucerf_poe_map(hdf5, ucerf_source, rupset_idx, s_sites, imtls, cmaker,
                  trunclevel, bbs, ctx_mon, pne_mon, disagg_mon):
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

            # add optional disaggregation information (bounding boxes)
            if bbs:
                with disagg_mon:
                    sids = set(sctx.sites.sids)
                    jb_dists = dctx.rjb
                    closest_points = rup.surface.get_closest_points(
                        sctx.sites.mesh)
                    bs = [bb for bb in bbs if bb.site_id in sids]
                    # NB: the assert below is always true; we are
                    # protecting against possible refactoring errors
                    assert len(bs) == len(jb_dists) == len(closest_points)
                    for bb, dist, p in zip(bs, jb_dists, closest_points):
                        bb.update([dist], [p.longitude], [p.latitude])
    except Exception as err:
        etype, err, tb = sys.exc_info()
        msg = 'An error occurred with source id=%s. Error: %s'
        msg %= (src.source_id, str(err))
        raise_(etype, msg, tb)
    return ~pmap


class UCERFClassicalSourceConverter(SourceConverter):
    """
    Adjustment of the UCERF Source Converter to return the source information
    as an instance of the UCERF SES Control object
    """
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


def hazard_curves_per_rupture_subset(rupset_idx, ucerf_source, sites, imtls,
                                     gsims, truncation_level=None,
                                     maximum_distance=None, bbs=(),
                                     monitor=Monitor()):
    """
    Calculates the probabilities of exceedence from a set of rupture indices
    """
    imtls = DictArray(imtls)
    cmaker = ContextMaker(gsims, maximum_distance)
    #indices_sites = ((rup_indices, sites) for rup_indices in ucerf_source)
    ctx_mon = monitor('making contexts', measuremem=False)
    pne_mon = monitor('computing poes', measuremem=False)
    disagg_mon = monitor('get closest points', measuremem=False)
    monitor.calc_times = []
    pmap = ProbabilityMap()
    with h5py.File(ucerf_source.source_file, "r") as hdf5:
        #for i, (rupset_idx, s_sites) in enumerate(
        #    ucerf_source.filter_sites_by_distance_from_rupture_set(indices_sites,
        #                                                           maximum_distance)):
        t0 = time.time()
        pmap |= ucerf_poe_map(hdf5, ucerf_source, rupset_idx, sites,
                              imtls, cmaker, truncation_level, bbs,
                              ctx_mon, pne_mon, disagg_mon)
        monitor.calc_times.append((ucerf_source.id, time.time() - t0))
        monitor.eff_ruptures += pne_mon.counts
    return pmap


@parallel.litetask
def ucerf_classical_hazard_by_rupture_set(rupset_idx, branchname, ucerf_source,
                                          src_group_id, sitecol, siteidx,
                                          rlzs_assoc, monitor):
    """
    :param sources:
        a non-empty sequence of sources of homogeneous tectonic region type
    :param sitecol:
        a SiteCollection instance
    :param siteidx:
        index of the first site (0 if there is a single tile)
    :param rlzs_assoc:
        a RlzsAssoc instance
    :param monitor:
        a monitor instance
    :returns:
        an AccumDict rlz -> curves
    """
    truncation_level = monitor.oqparam.truncation_level
    imtls = monitor.oqparam.imtls
    src_group_id = sources[0].src_group_id
    # sanity check: the src_group must be the same for all sources
    for src in sources[1:]:
        assert src.src_group_id == src_group_id
    gsims = rlzs_assoc.gsims_by_grp_id[src_group_id]
    trt = sources[0].tectonic_region_type
    max_dist = monitor.oqparam.maximum_distance[trt]

    dic = AccumDict()
    dic.siteslice = slice(siteidx, siteidx + len(sitecol))
    if monitor.oqparam.poes_disagg:
        sm_id = rlzs_assoc.sm_ids[src_group_id]
        dic.bbs = [BoundingBox(sm_id, sid) for sid in sitecol.sids]
    else:
        dic.bbs = []
    # NB: the source_site_filter below is ESSENTIAL for performance inside
    # hazard_curves_per_trt, since it reduces the full site collection
    # to a filtered one *before* doing the rupture filtering

    # Two step process here - the first generates the hazard curves from the
    # rupture sets
    monitor.eff_ruptures = 0
    # Apply the initial rupture to site filtering
    rupset_idx, s_sites =\
        ucerf_source.filter_sites_by_distance_from_rupture_set(
            rupset_idx, sitecol,
            monitor.oqparam.maximum_distance[trt])

    if len(s_sites):                                                       
        dic[src_group_id] = hazard_curves_per_rupture_subset(
            rupset_idx, ucerf_source, s_sites, imtls, gsims, truncation_level,
            maximum_distance=max_dist, bbs=dic.bbs, monitor=monitor)

    else:
        dic[src_group_id] = ProbabilityMap()
    dic.calc_times = monitor.calc_times  # added by hazard_curves_per_trt
    dic.eff_ruptures = {src_group_id: monitor.eff_ruptures}  # idem

    logging.info('Branchname for Background %s', branchname)
    # Get the background point sources
    bckgnd_sources = ucerf_source.get_background_sources(branchname,
                                                         sitecol,
                                                         max_dist)

    if len(bckgnd_sources):
        dic2 = AccumDict()
        dic2[src_group_id] = hazard_curves_per_trt(
            bckgnd_sources,
            sitecol, imtls, gsims, truncation_level,
            source_site_filter=source_site_distance_filter(max_dist),
            maximum_distance=max_dist, bbs=dic.bbs, monitor=monitor)

        dic[src_group_id] += dic2[src_group_id]
        dic.eff_ruptures[src_group_id] += monitor.eff_ruptures
    return dic


@parallel.litetask
def ucerf_classical_hazard_by_branch(branchname, ucerf_source, src_group_id,
                                     sitecol, siteidx, rlzs_assoc, monitor):
    """
    :param sources:
        a non-empty sequence of sources of homogeneous tectonic region type
    :param sitecol:
        a SiteCollection instance
    :param siteidx:
        index of the first site (0 if there is a single tile)
    :param rlzs_assoc:
        a RlzsAssoc instance
    :param monitor:
        a monitor instance
    :returns:
        an AccumDict rlz -> curves
    """
    truncation_level = monitor.oqparam.truncation_level
    imtls = monitor.oqparam.imtls
    #src_group_id = sources[0].src_group_id
    # sanity check: the src_group must be the same for all sources
    #for src in sources[1:]:
    #    assert src.src_group_id == src_group_id
    gsims = rlzs_assoc.gsims_by_grp_id[src_group_id]
    trt = ucerf_source.tectonic_region_type
    max_dist = monitor.oqparam.maximum_distance[trt]

    dic = AccumDict()
    dic.siteslice = slice(siteidx, siteidx + len(sitecol))
    if monitor.oqparam.poes_disagg:
        sm_id = rlzs_assoc.sm_ids[src_group_id]
        dic.bbs = [BoundingBox(sm_id, sid) for sid in sitecol.sids]
    else:
        dic.bbs = []
    # NB: the source_site_filter below is ESSENTIAL for performance inside
    # hazard_curves_per_trt, since it reduces the full site collection
    # to a filtered one *before* doing the rupture filtering

    # Two step process here - the first generates the hazard curves from the
    # rupture sets
    monitor.eff_ruptures = 0
    # Apply the initial rupture to site filtering
    rupset_idx = ucerf_source.get_rupture_indices(branchname)
    rupset_idx, s_sites =\
        ucerf_source.filter_sites_by_distance_from_rupture_set(
            rupset_idx, sitecol,
            monitor.oqparam.maximum_distance[trt])

    if len(s_sites):                                                       
        dic[src_group_id] = hazard_curves_per_rupture_subset(
            rupset_idx, ucerf_source, s_sites, imtls, gsims, truncation_level,
            maximum_distance=max_dist, bbs=dic.bbs, monitor=monitor)

    else:
        dic[src_group_id] = ProbabilityMap()
    dic.calc_times = monitor.calc_times  # added by hazard_curves_per_trt
    dic.eff_ruptures = {src_group_id: monitor.eff_ruptures}  # idem
    logging.info('Branchname for Background %s', branchname)
    # Get the background point sources
    bckgnd_sources = ucerf_source.get_background_sources(branchname,
                                                         sitecol,
                                                         max_dist)
    if len(bckgnd_sources):
        dic2 = AccumDict()
        dic2[src_group_id] = hazard_curves_per_trt(
            bckgnd_sources,
            sitecol, imtls, gsims, truncation_level,
            source_site_filter=source_site_noop_filter,
            maximum_distance=max_dist, bbs=dic.bbs, monitor=monitor)

        dic[src_group_id] += dic2[src_group_id]
        dic.eff_ruptures[src_group_id] += monitor.eff_ruptures
    return dic



@base.calculators.add('ucerf_classical')
class UCERFClassicalCalculator(classical.PSHACalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_task = ucerf_classical_hazard_by_branch
    # TODO Do I need this?
    etags = datastore.persistent_attribute('etags')
    is_stochastic = False

    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        self.sitecol = readinput.get_site_collection(self.oqparam)
        self.gsim_lt = readinput.get_gsim_lt(self.oqparam, [DEFAULT_TRT])
        self.smlt = readinput.get_source_model_lt(self.oqparam)
        parser = source.SourceModelParser(
            UCERFClassicalSourceConverter(self.oqparam.investigation_time,
                                          self.oqparam.rupture_mesh_spacing))
        [self.src_group] = parser.parse_src_groups(
            self.oqparam.inputs["source_model"])
        branches = sorted(self.smlt.branches.items())
        source_models = []
        num_gsim_paths = self.gsim_lt.get_num_paths()
        for ordinal, (name, branch) in enumerate(branches):
            sg = copy.copy(self.src_group)
            sg.id = ordinal
            sg.sources[0].id = ordinal
            # Update the event set 
            sg.sources[0].idx_set = sg.sources[0].build_idx_set(branch.value)
            sm = source.SourceModel(
                name, branch.weight, [name], [sg], num_gsim_paths, ordinal, 1)
            source_models.append(sm)
        self.csm = source.CompositeSourceModel(
            self.gsim_lt, self.smlt, source_models, set_weight=False)
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc()
        self.rup_data = {}
        self.infos = []

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        monitor = self.monitor.new(self.core_task.__name__)
        monitor.oqparam = self.oqparam
        ucerf_source = self.src_group.sources[0]
        if len(self.csm) > 1:
            # Where mutiple branches are required - parallelise by branch
            branches = [branch.value
                        for _, branch in self.smlt.branches.items()]
            # Run parallelizing by branch
            pmap_by_grp_id = parallel.apply_reduce(
                 ucerf_classical_hazard_by_branch,
                 (branches, ucerf_source, self.src_group.id, self.sitecol, 0,
                 self.rlzs_assoc, monitor),
                 concurrent_tasks=self.oqparam.concurrent_tasks,
                 agg=self.agg_dicts)
        else:
            branchname = self.smlt.branches.items()[0][1] 
            rup_sets = self.csm.get_sources()[0].get_rupture_indices(
                split=monitor.oqparam.rupture_split)
            # Run parallelizing by rupture subsets
            pmap_by_grp_id = parallel.apply_reduce(
                ucerf_classical_hazard_by_rupture_set,
                (rup_sets, branchname, ucerf_source, self.src_group.id,
                self.sitecol, 0, self.rlzs_assoc, monitor),
                concurrent_tasks=self.oqparam.concurrent_tasks, agg=self.agg)

        #pmap_by_grp_id = self.taskman.reduce(self.agg_dicts, self.zerodict())
        #self.save_data_transfer(self.taskman)
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(pmap_by_grp_id)
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc(
            partial(self.count_eff_ruptures, pmap_by_grp_id))
        self.datastore['csm_info'] = self.csm.info
        return pmap_by_grp_id
