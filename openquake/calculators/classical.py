# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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
import collections
from functools import partial, reduce
import numpy

from openquake.baselib.python3compat import encode
from openquake.baselib.general import AccumDict, block_splitter
from openquake.hazardlib.geo.utils import get_spherical_bounding_box
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.geodetic import npoints_between
from openquake.hazardlib.calc.hazard_curve import (
    pmap_from_grp, ProbabilityMap)
from openquake.hazardlib.calc.filters import (
    SourceSitesFilter, source_site_noop_filter)
from openquake.hazardlib.probability_map import PmapStats
from openquake.commonlib import parallel, datastore, source, calc
from openquake.commonlib.sourceconverter import split_source
from openquake.calculators import base

U16 = numpy.uint16
F32 = numpy.float32
F64 = numpy.float64

MAXWEIGHT = 200
HazardCurve = collections.namedtuple('HazardCurve', 'location poes')


class BBdict(AccumDict):
    """
    A serializable dictionary containing bounding box information
    """
    dt = numpy.dtype([('lt_model_id', U16), ('site_id', U16),
                      ('min_dist', F64), ('max_dist', F64),
                      ('east', F64), ('west', F64),
                      ('south', F64), ('north', F64)])

    def __toh5__(self):
        rows = []
        for lt_model_id, site_id in self:
            bb = self[lt_model_id, site_id]
            rows.append((lt_model_id, site_id, bb.min_dist, bb.max_dist,
                         bb.east, bb.west, bb.south, bb.north))
        return numpy.array(rows, self.dt), {}

    def __fromh5__(self, array, attrs):
        for row in array:
            lt_model_id = row['lt_model_id']
            site_id = row['site_id']
            bb = BoundingBox(lt_model_id, site_id)
            bb.min_dist = row['min_dist']
            bb.max_dist = row['max_dist']
            bb.east = row['east']
            bb.west = row['west']
            bb.north = row['north']
            bb.south = row['south']
            self[lt_model_id, site_id] = bb


# this is needed for the disaggregation
class BoundingBox(object):
    """
    A class to store the bounding box in distances, longitudes and magnitudes,
    given a source model and a site. This is used for disaggregation
    calculations. The goal is to determine the minimum and maximum
    distances of the ruptures generated from the model from the site;
    moreover the maximum and minimum longitudes and magnitudes are stored, by
    taking in account the international date line.
    """
    def __init__(self, lt_model_id, site_id):
        self.lt_model_id = lt_model_id
        self.site_id = site_id
        self.min_dist = self.max_dist = 0
        self.east = self.west = self.south = self.north = 0

    def update(self, dists, lons, lats):
        """
        Compare the current bounding box with the value in the arrays
        dists, lons, lats and enlarge it if needed.

        :param dists:
            a sequence of distances
        :param lons:
            a sequence of longitudes
        :param lats:
            a sequence of latitudes
        """
        if self.min_dist:
            dists = [self.min_dist, self.max_dist] + dists
        if self.west:
            lons = [self.west, self.east] + lons
        if self.south:
            lats = [self.south, self.north] + lats
        self.min_dist, self.max_dist = min(dists), max(dists)
        self.west, self.east, self.north, self.south = \
            get_spherical_bounding_box(lons, lats)

    def update_bb(self, bb):
        """
        Compare the current bounding box with the given bounding box
        and enlarge it if needed.

        :param bb:
            an instance of :class:
            `openquake.engine.calculators.hazard.classical.core.BoundingBox`
        """
        if bb:  # the given bounding box must be non-empty
            self.update([bb.min_dist, bb.max_dist], [bb.west, bb.east],
                        [bb.south, bb.north])

    def bins_edges(self, dist_bin_width, coord_bin_width):
        """
        Define bin edges for disaggregation histograms, from the bin data
        collected from the ruptures.

        :param dists:
            array of distances from the ruptures
        :param lons:
            array of longitudes from the ruptures
        :param lats:
            array of latitudes from the ruptures
        :param dist_bin_width:
            distance_bin_width from job.ini
        :param coord_bin_width:
            coordinate_bin_width from job.ini
        """
        dist_edges = dist_bin_width * numpy.arange(
            int(self.min_dist / dist_bin_width),
            int(numpy.ceil(self.max_dist / dist_bin_width) + 1))

        west = numpy.floor(self.west / coord_bin_width) * coord_bin_width
        east = numpy.ceil(self.east / coord_bin_width) * coord_bin_width
        lon_extent = get_longitudinal_extent(west, east)

        lon_edges, _, _ = npoints_between(
            west, 0, 0, east, 0, 0,
            numpy.round(lon_extent / coord_bin_width) + 1)

        lat_edges = coord_bin_width * numpy.arange(
            int(numpy.floor(self.south / coord_bin_width)),
            int(numpy.ceil(self.north / coord_bin_width) + 1))

        return dist_edges, lon_edges, lat_edges

    def __bool__(self):
        """
        True if the bounding box is non empty.
        """
        return bool(self.max_dist - self.min_dist or
                    self.west - self.east or
                    self.north - self.south)
    __nonzero__ = __bool__


def classical(sources, sitecol, gsims, monitor):
    """
    :param sources:
        a non-empty sequence of sources of homogeneous tectonic region type
    :param sitecol:
        a SiteCollection instance
    :param gsims:
        a list of GSIMs for the current tectonic region type
    :param monitor:
        a monitor instance
    :returns:
        an AccumDict rlz -> curves
    """
    truncation_level = monitor.truncation_level
    imtls = monitor.imtls
    src_group_id = sources[0].src_group_id
    # sanity check: the src_group must be the same for all sources
    for src in sources[1:]:
        assert src.src_group_id == src_group_id
    trt = sources[0].tectonic_region_type
    max_dist = monitor.maximum_distance[trt]

    dic = AccumDict()
    if monitor.poes_disagg:
        sm_id = monitor.sm_id
        dic.bbs = [BoundingBox(sm_id, sid) for sid in sitecol.sids]
    else:
        dic.bbs = []
    # NB: the source_site_filter below is ESSENTIAL for performance inside
    # pmap_from_grp, since it reduces the full site collection
    # to a filtered one *before* doing the rupture filtering
    dic[src_group_id] = pmap_from_grp(
        sources, sitecol, imtls, gsims, truncation_level,
        maximum_distance=max_dist, bbs=dic.bbs, monitor=monitor)
    dic.calc_times = monitor.calc_times  # added by pmap_from_grp
    dic.eff_ruptures = {src_group_id: monitor.eff_ruptures}  # idem
    return dic


@base.calculators.add('psha')
class PSHACalculator(base.HazardCalculator):
    """
    Classical PSHA calculator
    """
    core_task = classical
    source_info = datastore.persistent_attribute('source_info')

    def agg_dicts(self, acc, val):
        """
        Aggregate dictionaries of hazard curves by updating the accumulator.

        :param acc: accumulator dictionary
        :param val: a nested dictionary grp_id -> ProbabilityMap
        """
        with self.monitor('aggregate curves', autoflush=True):
            if hasattr(val, 'calc_times'):
                acc.calc_times.extend(val.calc_times)
            if hasattr(val, 'eff_ruptures'):
                acc.eff_ruptures += val.eff_ruptures
            for bb in getattr(val, 'bbs', []):
                acc.bb_dict[bb.lt_model_id, bb.site_id].update_bb(bb)
            [(grp_id, pmap)] = val.items()  # val is a dict of len 1
            acc[grp_id] |= pmap
        self.datastore.flush()
        return acc

    def count_eff_ruptures(self, result_dict, src_group):
        """
        Returns the number of ruptures in the src_group (after filtering)
        or 0 if the src_group has been filtered away.

        :param result_dict: a dictionary with keys (grp_id, gsim)
        :param src_group: a SourceGroup instance
        """
        return (result_dict.eff_ruptures.get(src_group.id, 0) / self.num_tiles)

    def zerodict(self):
        """
        Initial accumulator, a dict grp_id -> ProbabilityMap(L, G)
        """
        zd = AccumDict()
        num_levels = len(self.oqparam.imtls.array)
        for grp in self.csm.src_groups:
            num_gsims = len(self.rlzs_assoc.gsims_by_grp_id[grp.id])
            zd[grp.id] = ProbabilityMap(num_levels, num_gsims)
        zd.calc_times = []
        zd.eff_ruptures = AccumDict()  # grp_id -> eff_ruptures
        zd.bb_dict = BBdict()
        if self.oqparam.poes_disagg:
            for sid in self.sitecol.sids:
                for smodel in self.csm.source_models:
                    zd.bb_dict[smodel.ordinal, sid] = BoundingBox(
                        smodel.ordinal, sid)
        return zd

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        oq = self.oqparam
        monitor = self.monitor.new(
            self.core_task.__name__,
            truncation_level=oq.truncation_level,
            imtls=oq.imtls,
            maximum_distance=oq.maximum_distance,
            poes_disagg=oq.poes_disagg,
            ses_per_logic_tree_path=oq.ses_per_logic_tree_path,
            random_seed=oq.random_seed)
        self.num_tiles = 1
        
        with self.monitor('managing sources', autoflush=True):
            src_groups = list(self.csm.src_groups)
            res = parallel.starmap(
                self.core_task.__func__, self.gen_args(src_groups, oq, monitor)
            ).submit_all()
        acc = reduce(self.agg_dicts, res, self.zerodict())
        self.save_data_transfer(res)
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(acc)
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc(
            partial(self.count_eff_ruptures, acc))
        self.datastore['csm_info'] = self.csm.info
        return acc

    def gen_args(self, src_groups, oq, monitor):
        """
        Used in the case of large source model logic trees
        """
        ss_filter = (SourceSitesFilter(oq.maximum_distance)
                     if oq.filter_sources else source_site_noop_filter)
        ngroups = len(src_groups)
        logging.info('Considering %d source groups', ngroups)
        if self.random_seed is not None:
            self.csm.init_serials()
        maxweight = max(
            math.ceil(self.csm.weight / oq.concurrent_tasks), MAXWEIGHT)
        nheavy = nlight = 0
        for sg in src_groups:
            gsims = self.rlzs_assoc.gsims_by_grp_id[sg.id]
            if oq.poes_disagg:  # only for disaggregation
                mon.sm_id = self.rlzs_assoc.sm_ids[sg.id]
            monitor.seed = self.rlzs_assoc.seed
            monitor.samples = self.rlzs_assoc.samples[sg.id]
            heavy = [src for src in sg.sources if src.weight > maxweight]
            light = [src for src in sg.sources if src.weight <= maxweight]
            for block in block_splitter(light, maxweight):
                yield block, self.sitecol, gsims, monitor
                nlight += 1
            for src, sites in ss_filter(heavy, self.sitecol):
                for block in block_splitter(split_source(src), maxweight):
                    yield block, sites, gsims, monitor
                    nheavy += 1
        logging.info('Sent %d light and %d heavy tasks', nlight, nheavy)
  
    def store_source_info(self, pmap_by_grp_id):
        # save the calculation times per each source
        calc_times = getattr(pmap_by_grp_id, 'calc_times', [])
        if calc_times and 'source_info' in self.datastore:
            sources = self.csm.get_sources()
            info_dict = {(rec['src_group_id'], rec['source_id']): rec
                         for rec in self.source_info}
            for src_idx, dt in calc_times:
                src = sources[src_idx]
                info = info_dict[src.src_group_id, encode(src.source_id)]
                info['cum_calc_time'] += dt
                info['num_tasks'] += 1
                if dt > info['max_calc_time']:
                    info['max_calc_time'] = dt

            rows = sorted(
                info_dict.values(), key=operator.itemgetter(7), reverse=True)
            array = numpy.zeros(len(rows), source.source_info_dt)
            for i, row in enumerate(rows):
                for name in array.dtype.names:
                    array[i][name] = row[name]
            self.source_info = array
        self.datastore.flush()

    def post_execute(self, pmap_by_grp_id):
        """
        Collect the hazard curves by realization and export them.

        :param pmap_by_grp_id:
            a dictionary grp_id -> hazard curves
        """
        if pmap_by_grp_id.bb_dict:
            self.datastore['bb_dict'] = pmap_by_grp_id.bb_dict
        with self.monitor('saving probability maps', autoflush=True):
            for grp_id, pmap in pmap_by_grp_id.items():
                if pmap:  # pmap can be missing if the group is filtered away
                    key = 'poes/%04d' % grp_id
                    self.datastore[key] = pmap
                    self.datastore.set_attrs(
                        key, trt=self.csm.info.get_trt(grp_id))
            if 'poes' in self.datastore:
                self.datastore.set_nbytes('poes')


def build_hcurves_and_stats(pmap_by_grp, sids, pstats, rlzs_assoc, monitor):
    """
    :param pmap_by_grp: dictionary of probability maps by source group ID
    :param sids: array of site IDs
    :param pstats: instance of PmapStats
    :param rlzs_assoc: instance of RlzsAssoc
    :param monitor: instance of Monitor
    :returns: a dictionary kind -> ProbabilityMap

    The "kind" is a string of the form 'rlz-XXX' or 'mean' of 'quantile-XXX'
    used to specify the kind of output.
    """
    if sum(len(pmap) for pmap in pmap_by_grp.values()) == 0:  # all empty
        return {}
    rlzs = rlzs_assoc.realizations
    with monitor('combine pmaps'):
        pmap_by_rlz = calc.combine_pmaps(rlzs_assoc, pmap_by_grp)
    with monitor('compute stats'):
        pmap_by_kind = dict(
            pstats.compute(sids, [pmap_by_rlz[rlz] for rlz in rlzs]))
    if monitor.individual_curves:
        for rlz in rlzs:
            pmap_by_kind['rlz-%03d' % rlz.ordinal] = pmap_by_rlz[rlz]
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
        Builds hcurves and stats from the stored PoEs
        """
        if 'poes' not in self.datastore:  # for short report
            return
        oq = self.oqparam
        rlzs = self.rlzs_assoc.realizations

        # initialize datasets
        N = len(self.sitecol)
        L = len(oq.imtls.array)
        attrs = dict(
            __pyclass__='openquake.hazardlib.probability_map.ProbabilityMap',
            sids=numpy.arange(N, dtype=numpy.uint32))
        if oq.individual_curves:
            for rlz in rlzs:
                self.datastore.create_dset(
                    'hcurves/rlz-%03d' % rlz.ordinal, F32,
                    (N, L, 1),  attrs=attrs)
        if oq.mean_hazard_curves:
            self.datastore.create_dset(
                'hcurves/mean', F32, (N, L, 1), attrs=attrs)
        for q in oq.quantile_hazard_curves:
            self.datastore.create_dset(
                'hcurves/quantile-%s' % q, F32, (N, L, 1), attrs=attrs)
        self.datastore.flush()

        logging.info('Building hazard curves')
        with self.monitor('submitting poes', autoflush=True):
            pmap_by_grp = {
                int(group_id): self.datastore['poes/' + group_id]
                for group_id in self.datastore['poes']}
            sm = parallel.starmap(build_hcurves_and_stats,
                                  list(self.gen_args(pmap_by_grp)))
        with self.monitor('saving hcurves and stats', autoflush=True):
            return sm.reduce(self.save_hcurves)

    def gen_args(self, pmap_by_grp):
        """
        :param pmap_by_grp: dictionary of ProbabilityMaps keyed by src_grp_id
        :yields: arguments for the function build_hcurves_and_stats
        """
        monitor = self.monitor.new(
            'build_hcurves_and_stats',
            individual_curves=self.oqparam.individual_curves)
        weights = (None if self.oqparam.number_of_logic_tree_samples
                   else [rlz.weight for rlz in self.rlzs_assoc.realizations])
        pstats = PmapStats(self.oqparam.quantile_hazard_curves, weights)
        num_rlzs = len(self.rlzs_assoc.realizations)
        for block in self.sitecol.split_in_tiles(num_rlzs):
            pg = {grp_id: pmap_by_grp[grp_id].filter(block.sids)
                  for grp_id in pmap_by_grp}
            yield pg, block.sids, pstats, self.rlzs_assoc, monitor

    def save_hcurves(self, acc, pmap_by_kind):
        """
        Works by side effect by saving hcurves and statistics on the
        datastore; the accumulator stores the number of bytes saved.

        :param acc: dictionary kind -> nbytes
        :param pmap_by_kind: a dictionary of ProbabilityMaps
        """
        oq = self.oqparam
        for kind in pmap_by_kind:
            if kind == 'mean' and not oq.mean_hazard_curves:
                continue  # do not save the mean curves
            pmap = pmap_by_kind[kind]
            if pmap:
                key = 'hcurves/' + kind
                dset = self.datastore.getitem(key)
                for sid in pmap:
                    dset[sid] = pmap[sid].array
                acc += {kind: pmap.nbytes}
        self.datastore.flush()
        return acc

    def post_execute(self, acc):
        """Save the number of bytes per each dataset"""
        for kind, nbytes in acc.items():
            self.datastore.getitem('hcurves/' + kind).attrs['nbytes'] = nbytes
