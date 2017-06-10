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
import math
import logging
import operator
from functools import partial
import numpy

from openquake.baselib import parallel
from openquake.baselib.python3compat import encode
from openquake.baselib.general import AccumDict
from openquake.hazardlib.geo.utils import get_spherical_bounding_box
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.geodetic import npoints_between
from openquake.hazardlib.calc.hazard_curve import (
    pmap_from_grp, ProbabilityMap)
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.commonlib import datastore, source, calc, util
from openquake.calculators import base

U16 = numpy.uint16
F32 = numpy.float32
F64 = numpy.float64
weight = operator.attrgetter('weight')


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


def classical(sources, src_filter, gsims, param, monitor):
    """
    :param sources:
        a non-empty sequence of sources of homogeneous tectonic region type
    :param src_filter:
        source filter
    :param gsims:
        a list of GSIMs for the current tectonic region type
    :param param:
        a dictionary of parameters
    :param monitor:
        a monitor instance
    :returns:
        an AccumDict rlz -> curves
    """
    truncation_level = param['truncation_level']
    imtls = param['imtls']
    src_group_id = sources[0].src_group_id
    assert src_group_id is not None
    # sanity check: the src_group must be the same for all sources
    for src in sources[1:]:
        assert src.src_group_id == src_group_id
    if param['disagg']:
        sm_id = param['sm_id']
        bbs = [BoundingBox(sm_id, sid) for sid in src_filter.sitecol.sids]
    else:
        bbs = []
    pmap = pmap_from_grp(
        sources, src_filter, imtls, gsims, truncation_level,
        bbs=bbs, monitor=monitor)
    pmap.bbs = bbs
    return pmap


def saving_sources_by_task(iterargs, dstore):
    """
    Yield the iterargs again by populating 'task_info/source_ids'
    """
    source_ids = []
    for args in iterargs:
        source_ids.append(' ' .join(src.source_id for src in args[0]))
        yield args
    dstore['task_sources'] = numpy.array([encode(s) for s in source_ids])


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
                info = self.csm.infos[pmap.grp_id, src_id]
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
        monitor = self.monitor(self.core_task.__name__)
        with self.monitor('managing sources', autoflush=True):
            allargs = self.gen_args(self.csm, monitor)
            iterargs = saving_sources_by_task(allargs, self.datastore)
            if isinstance(allargs, list):
                # there is a trick here: if the arguments are known
                # (a list, not an iterator), keep them as a list
                # then the Starmap will understand the case of a single
                # argument tuple and it will run in core the task
                iterargs = list(iterargs)
            ires = parallel.Starmap(
                self.core_task.__func__, iterargs).submit_all()
        acc = ires.reduce(self.agg_dicts, self.zerodict())
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(self.csm.infos, acc)
        return acc

    def gen_args(self, csm, monitor):
        """
        Used in the case of large source model logic trees.

        :param csm: a CompositeSourceModel instance
        :param monitor: a :class:`openquake.baselib.performance.Monitor`
        :yields: (sources, sites, gsims, monitor) tuples
        """
        oq = self.oqparam
        ngroups = sum(len(sm.src_groups) for sm in csm.source_models)
        if self.is_stochastic:  # disable tiling
            num_tiles = 1
        else:
            num_tiles = math.ceil(len(self.sitecol) / oq.sites_per_tile)
        if num_tiles > 1:
            tiles = self.sitecol.split_in_tiles(num_tiles)
        else:
            tiles = [self.sitecol]
        maxweight = self.csm.get_maxweight(oq.concurrent_tasks)
        numheavy = len(self.csm.get_sources('heavy', maxweight))
        logging.info('Using maxweight=%d, numheavy=%d, numtiles=%d',
                     maxweight, numheavy, len(tiles))
        for t, tile in enumerate(tiles):
            if num_tiles > 1:
                with self.monitor('prefiltering source model', autoflush=True):
                    logging.info('Instantiating src_filter for tile %d', t + 1)
                    src_filter = SourceFilter(tile, oq.maximum_distance)
                    csm = self.csm.filter(src_filter)
            else:
                src_filter = self.src_filter
            num_tasks = 0
            num_sources = 0
            for sm in csm.source_models:
                param = dict(
                    truncation_level=oq.truncation_level,
                    imtls=oq.imtls,
                    maximum_distance=oq.maximum_distance,
                    disagg=oq.poes_disagg or oq.iml_disagg,
                    samples=sm.samples, seed=oq.ses_seed,
                    ses_per_logic_tree_path=oq.ses_per_logic_tree_path)
                for sg in sm.src_groups:
                    if num_tiles <= 1:
                        logging.info(
                            'Sending source group #%d of %d (%s, %d sources)',
                            sg.id + 1, ngroups, sg.trt, len(sg.sources))
                    if oq.poes_disagg or oq.iml_disagg:  # only for disagg
                        param['sm_id'] = self.rlzs_assoc.sm_ids[sg.id]
                    if sg.src_interdep == 'mutex':  # do not split the group
                        self.csm.add_infos(sg.sources)
                        yield sg, src_filter, sg.gsims, param, monitor
                        num_tasks += 1
                        num_sources += len(sg)
                    else:
                        for block in self.csm.split_sources(
                                sg.sources, src_filter, maxweight):
                            yield block, src_filter, sg.gsims, param, monitor
                            num_tasks += 1
                            num_sources += len(block)
            logging.info('Sent %d sources in %d tasks', num_sources, num_tasks)
        source.split_map.clear()

    def store_source_info(self, infos, acc):
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
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc(
            partial(self.count_eff_ruptures, acc))
        self.datastore['csm_info'] = self.csm.info
        self.datastore['csm_info/assoc_by_grp'] = array = (
            self.rlzs_assoc.get_assoc_by_grp())
        # computing properly the length in bytes of a variable length array
        nbytes = array.nbytes + sum(rec['rlzis'].nbytes for rec in array)
        self.datastore.set_attrs('csm_info/assoc_by_grp', nbytes=nbytes)
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
                    key = 'poes/grp-%02d' % grp_id
                    self.datastore[key] = pmap
                    self.datastore.set_attrs(key, trt=grp_trt[grp_id])
            if 'poes' in self.datastore:
                self.datastore.set_nbytes('poes')


@util.reader
def build_hcurves_and_stats(pgetter, hstats, monitor):
    """
    :param pgetter: an :class:`openquake.commonlib.calc.PmapGetter`
    :param hstats: a list of pairs (statname, statfunc)
    :param monitor: instance of Monitor
    :returns: a dictionary kind -> ProbabilityMap

    The "kind" is a string of the form 'rlz-XXX' or 'mean' of 'quantile-XXX'
    used to specify the kind of output.
    """
    with monitor('combine pmaps'), pgetter:
        pmaps = pgetter.get_pmaps(pgetter.sids)
    if sum(len(pmap) for pmap in pmaps) == 0:  # no data
        return {}
    pmap_by_kind = {}
    for kind, stat in hstats:
        with monitor('compute ' + kind):
            pmap = compute_pmap_stats(pmaps, [stat], pgetter.weights)
        pmap_by_kind[kind] = pmap
    return pmap_by_kind


@base.calculators.add('classical')
class ClassicalCalculator(PSHACalculator):
    """
    Classical PSHA calculator
    """
    pre_calculator = 'psha'
    core_task = build_hcurves_and_stats

    def gen_args(self, pgetter):
        """
        :param pgetter: PmapGetter instance
        :yields: arguments for the function build_hcurves_and_stats
        """
        monitor = self.monitor('build_hcurves_and_stats')
        hstats = self.oqparam.hazard_stats()
        for tile in self.sitecol.split_in_tiles(self.oqparam.concurrent_tasks):
            newgetter = pgetter.new(tile.sids)
            yield newgetter, hstats, monitor

    def execute(self):
        """
        Build statistical hazard curves from the stored PoEs
        """
        if 'poes' not in self.datastore:  # for short report
            return
        oq = self.oqparam
        rlzs = self.rlzs_assoc.realizations
        if len(rlzs) == 1 or not oq.hazard_stats():
            return {}

        # initialize datasets
        N = len(self.sitecol)
        L = len(oq.imtls.array)
        attrs = dict(
            __pyclass__='openquake.hazardlib.probability_map.ProbabilityMap',
            sids=numpy.arange(N, dtype=numpy.uint32))
        nbytes = N * L * 4  # bytes per realization (32 bit floats)
        totbytes = 0
        if len(rlzs) > 1:
            for name, stat in oq.hazard_stats():
                self.datastore.create_dset(
                    'hcurves/' + name, F32, (N, L, 1), attrs=attrs)
                totbytes += nbytes
        if 'hcurves' in self.datastore:
            self.datastore.set_attrs('hcurves', nbytes=totbytes)
        self.datastore.flush()

        with self.monitor('sending pmaps', autoflush=True, measuremem=True):
            if self.datastore.parent != ():
                # workers read from the parent datastore
                pgetter = calc.PmapGetter(
                    self.datastore.parent, fromworker=True)
                allargs = list(self.gen_args(pgetter))
                self.datastore.parent.close()
            else:
                # workers read from the cache
                pgetter = calc.PmapGetter(self.datastore)
                allargs = self.gen_args(pgetter)
            ires = parallel.Starmap(
                self.core_task.__func__, allargs).submit_all()
        if self.datastore.parent != ():
            self.datastore.parent.open()  # if closed
        nbytes = ires.reduce(self.save_hcurves)
        return nbytes

    def save_hcurves(self, acc, pmap_by_kind):
        """
        Works by side effect by saving hcurves and statistics on the
        datastore; the accumulator stores the number of bytes saved.

        :param acc: dictionary kind -> nbytes
        :param pmap_by_kind: a dictionary of ProbabilityMaps
        """
        with self.monitor('saving statistical hcurves', autoflush=True):
            for kind in pmap_by_kind:
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
