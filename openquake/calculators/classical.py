# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
import logging
import operator
import collections
from functools import partial, reduce
import numpy

from openquake.baselib import hdf5, parallel
from openquake.baselib.general import AccumDict, block_splitter
from openquake.hazardlib import sourceconverter
from openquake.hazardlib.geo.utils import get_spherical_bounding_box
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.geodetic import npoints_between
from openquake.hazardlib.calc.hazard_curve import (
    pmap_from_grp, ProbabilityMap)
from openquake.hazardlib.probability_map import PmapStats
from openquake.commonlib import datastore, source, calc
from openquake.calculators import base

U16 = numpy.uint16
F32 = numpy.float32
F64 = numpy.float64

HazardCurve = collections.namedtuple('HazardCurve', 'location poes')


def split_filter_source(src, sites, src_filter, random_seed):
    """
    :param src: an heavy source
    :param sites: sites affected by the source
    :param src_filter: a SourceFilter instance
    :random_seed: used only for event based calculations
    :returns: a list of split sources
    """
    split_sources = []
    start = 0
    for split in sourceconverter.split_source(src):
        if random_seed:
            nr = split.num_ruptures
            split.serial = src.serial[start:start + nr]
            start += nr
        if src_filter.affected(split) is not None:
            split_sources.append(split)
    return split_sources


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


def classical(sources, src_filter, gsims, monitor):
    """
    :param sources:
        a non-empty sequence of sources of homogeneous tectonic region type
    :param src_filter:
        source filter
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
    if monitor.disagg:
        sm_id = monitor.sm_id
        bbs = [BoundingBox(sm_id, sid) for sid in src_filter.sitecol.sids]
    else:
        bbs = []
    pmap = pmap_from_grp(
        sources, src_filter, imtls, gsims, truncation_level,
        bbs=bbs, monitor=monitor)
    pmap.bbs = bbs
    pmap.grp_id = src_group_id
    return pmap


def saving_sources_by_task(iterargs, dstore):
    """
    Yield the iterargs again by populating 'task_info/source_ids'
    """
    source_ids = []
    for args in iterargs:
        source_ids.append(' ' .join(src.source_id for src in args[0]))
        yield args
    dstore['task_sources'] = numpy.array(source_ids, hdf5.vstr)


@base.calculators.add('psha')
class PSHACalculator(base.HazardCalculator):
    """
    Classical PSHA calculator
    """
    core_task = classical
    source_info = datastore.persistent_attribute('source_info')

    def agg_dicts(self, acc, pmap):
        """
        Aggregate dictionaries of hazard curves by updating the accumulator.

        :param acc: accumulator dictionary
        :param pmap: a ProbabilityMap
        """
        with self.monitor('aggregate curves', autoflush=True):
            for src_id, nsites, calc_time in pmap.calc_times:
                src_id = src_id.split(':', 1)[0]
                info = self.infos[pmap.grp_id, src_id]
                info.calc_time += calc_time
                info.num_sites = max(info.num_sites, nsites)
                info.num_split += 1
            acc.eff_ruptures += pmap.eff_ruptures
            for bb in getattr(pmap, 'bbs', []):  # for disaggregation
                acc.bb_dict[bb.lt_model_id, bb.site_id].update_bb(bb)
            acc[pmap.grp_id] |= pmap
        self.datastore.flush()
        return acc

    def count_eff_ruptures(self, result_dict, src_group):
        """
        Returns the number of ruptures in the src_group (after filtering)
        or 0 if the src_group has been filtered away.

        :param result_dict: a dictionary with keys (grp_id, gsim)
        :param src_group: a SourceGroup instance
        """
        return result_dict.eff_ruptures.get(src_group.id, 0)

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
        if self.oqparam.poes_disagg or self.oqparam.iml_disagg:
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
            disagg=oq.poes_disagg or oq.iml_disagg,
            ses_per_logic_tree_path=oq.ses_per_logic_tree_path,
            seed=oq.random_seed)
        with self.monitor('managing sources', autoflush=True):
            src_groups = list(self.csm.src_groups)
            iterargs = saving_sources_by_task(
                self.gen_args(src_groups, oq, monitor), self.datastore)
            res = parallel.Starmap(
                self.core_task.__func__, iterargs).submit_all()
        acc = reduce(self.agg_dicts, res, self.zerodict())
        self.save_data_transfer(res)
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(self.infos)
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc(
            partial(self.count_eff_ruptures, acc))
        self.datastore['csm_info'] = self.csm.info
        return acc

    def gen_args(self, src_groups, oq, monitor):
        """
        Used in the case of large source model logic trees.

        :param src_groups: a list of SourceGroup instances
        :param oq: a :class:`openquake.commonlib.oqvalidation.OqParam` instance
        :param monitor: a :class:`openquake.baselib.performance.Monitor`
        :yields: (sources, sites, gsims, monitor) tuples
        """
        ngroups = len(src_groups)
        maxweight = self.csm.get_maxweight(oq.concurrent_tasks)
        logging.info('Using a maxweight of %d', maxweight)
        nheavy = nlight = 0
        self.infos = {}
        for sg in src_groups:
            logging.info('Sending source group #%d of %d (%s, %d sources)',
                         sg.id + 1, ngroups, sg.trt, len(sg.sources))
            gsims = self.rlzs_assoc.gsims_by_grp_id[sg.id]
            if oq.poes_disagg or oq.iml_disagg:  # only for disaggregation
                monitor.sm_id = self.rlzs_assoc.sm_ids[sg.id]
            monitor.seed = self.rlzs_assoc.seed
            monitor.samples = self.rlzs_assoc.samples[sg.id]
            light = [src for src in sg.sources if src.weight <= maxweight]
            for block in block_splitter(
                    light, maxweight, weight=operator.attrgetter('weight')):
                for src in block:
                    self.infos[sg.id, src.source_id] = source.SourceInfo(src)
                yield block, self.src_filter, gsims, monitor
                nlight += 1
            heavy = [src for src in sg.sources if src.weight > maxweight]
            if not heavy:
                continue
            with self.monitor('split/filter heavy sources', autoflush=True):
                for src in heavy:
                    sites = self.src_filter.affected(src)
                    self.infos[sg.id, src.source_id] = source.SourceInfo(src)
                    sources = split_filter_source(
                        src, sites, self.src_filter, self.random_seed)
                    if len(sources) > 1:
                        logging.info(
                            'Splitting %s "%s" in %d sources',
                            src.__class__.__name__,
                            src.source_id, len(sources))
                    for block in block_splitter(
                            sources, maxweight,
                            weight=operator.attrgetter('weight')):
                        yield block, self.src_filter, gsims, monitor
                        nheavy += 1
        logging.info('Sent %d light and %d heavy tasks', nlight, nheavy)

    def store_source_info(self, infos):
        # save the calculation times per each source
        if infos:
            rows = sorted(
                infos.values(),
                key=operator.attrgetter('calc_time'),
                reverse=True)
            array = numpy.zeros(len(rows), source.SourceInfo.dt)
            for i, row in enumerate(rows):
                for name in array.dtype.names:
                    array[i][name] = getattr(row, name)
            self.source_info = array
            infos.clear()
        self.datastore.flush()

    def post_execute(self, pmap_by_grp_id):
        """
        Collect the hazard curves by realization and export them.

        :param pmap_by_grp_id:
            a dictionary grp_id -> hazard curves
        """
        if pmap_by_grp_id.bb_dict:
            self.datastore['bb_dict'] = pmap_by_grp_id.bb_dict
        grp_trt = self.csm.info.grp_trt()
        with self.monitor('saving probability maps', autoflush=True):
            for grp_id, pmap in pmap_by_grp_id.items():
                if pmap:  # pmap can be missing if the group is filtered away
                    key = 'poes/%04d' % grp_id
                    self.datastore[key] = pmap
                    self.datastore.set_attrs(key, trt=grp_trt[grp_id])
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
        nbytes = N * L * 4  # bytes per realization (32 bit floats)
        totbytes = 0
        if oq.individual_curves:
            for rlz in rlzs:
                self.datastore.create_dset(
                    'hcurves/rlz-%03d' % rlz.ordinal, F32,
                    (N, L, 1),  attrs=attrs)
                totbytes += nbytes
        if oq.mean_hazard_curves and len(rlzs) > 1:
            self.datastore.create_dset(
                'hcurves/mean', F32, (N, L, 1), attrs=attrs)
            totbytes += nbytes
        for q in oq.quantile_hazard_curves:
            self.datastore.create_dset(
                'hcurves/quantile-%s' % q, F32, (N, L, 1), attrs=attrs)
            totbytes += nbytes
        if 'hcurves' in self.datastore:
            self.datastore.set_attrs('hcurves', nbytes=totbytes)
        self.datastore.flush()

        logging.info('Building hazard curves')
        with self.monitor('submitting poes', autoflush=True):
            pmap_by_grp = {
                int(group_id): self.datastore['poes/' + group_id]
                for group_id in self.datastore['poes']}
            res = parallel.Starmap(
                build_hcurves_and_stats,
                list(self.gen_args(pmap_by_grp))).submit_all()
        nbytes = reduce(self.save_hcurves, res, AccumDict())
        self.save_data_transfer(res)
        return nbytes

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
        with self.monitor('saving hcurves and stats', autoflush=True):
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
                    # in the datastore we save 4 byte floats, thus we
                    # divide the memory consumption by 2: pmap.nbytes / 2
                    acc += {kind: pmap.nbytes // 2}
            self.datastore.flush()
            return acc

    def post_execute(self, acc):
        """Save the number of bytes per each dataset"""
        for kind, nbytes in acc.items():
            self.datastore.getitem('hcurves/' + kind).attrs['nbytes'] = nbytes
