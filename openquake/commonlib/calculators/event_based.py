#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import random
import operator
import itertools
import collections

import numpy

from openquake.hazardlib import geo
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.filters import \
    filter_sites_by_distance_to_rupture
from openquake.hazardlib import site, calc
from openquake.commonlib import readinput, parallel
from openquake.commonlib.export import export
from openquake.commonlib.export.hazard import SESCollection
from openquake.baselib.general import AccumDict, groupby

from openquake.commonlib.writers import save_csv
from openquake.commonlib.calculators import base
from openquake.commonlib.calculators.calc import \
    MAX_INT, gmvs_to_haz_curve, agg_prob
from openquake.commonlib.calculators.classical import ClassicalCalculator

# ######################## rupture calculator ############################ #


def get_geom(surface, is_from_fault_source, is_multi_surface):
    """
    The following fields can be interpreted different ways,
    depending on the value of `is_from_fault_source`. If
    `is_from_fault_source` is True, each of these fields should
    contain a 2D numpy array (all of the same shape). Each triple
    of (lon, lat, depth) for a given index represents the node of
    a rectangular mesh. If `is_from_fault_source` is False, each
    of these fields should contain a sequence (tuple, list, or
    numpy array, for example) of 4 values. In order, the triples
    of (lon, lat, depth) represent top left, top right, bottom
    left, and bottom right corners of the the rupture's planar
    surface. Update: There is now a third case. If the rupture
    originated from a characteristic fault source with a
    multi-planar-surface geometry, `lons`, `lats`, and `depths`
    will contain one or more sets of 4 points, similar to how
    planar surface geometry is stored (see above).

    :param rupture: an instance of :class:
    `openquake.hazardlib.source.rupture.BaseProbabilisticRupture`

    :param is_from_fault_source: a boolean
    :param is_multi_surface: a boolean
    """
    if is_from_fault_source:
        # for simple and complex fault sources,
        # rupture surface geometry is represented by a mesh
        surf_mesh = surface.get_mesh()
        lons = surf_mesh.lons
        lats = surf_mesh.lats
        depths = surf_mesh.depths
    else:
        if is_multi_surface:
            # `list` of
            # openquake.hazardlib.geo.surface.planar.PlanarSurface
            # objects:
            surfaces = surface.surfaces

            # lons, lats, and depths are arrays with len == 4*N,
            # where N is the number of surfaces in the
            # multisurface for each `corner_*`, the ordering is:
            #   - top left
            #   - top right
            #   - bottom left
            #   - bottom right
            lons = numpy.concatenate([x.corner_lons for x in surfaces])
            lats = numpy.concatenate([x.corner_lats for x in surfaces])
            depths = numpy.concatenate([x.corner_depths for x in surfaces])
        else:
            # For area or point source,
            # rupture geometry is represented by a planar surface,
            # defined by 3D corner points
            lons = numpy.zeros((4))
            lats = numpy.zeros((4))
            depths = numpy.zeros((4))

            # NOTE: It is important to maintain the order of these
            # corner points. TODO: check the ordering
            for i, corner in enumerate((surface.top_left,
                                        surface.top_right,
                                        surface.bottom_left,
                                        surface.bottom_right)):
                lons[i] = corner.longitude
                lats[i] = corner.latitude
                depths[i] = corner.depth
    return lons, lats, depths


class SESRupture(object):
    def __init__(self, rupture, site_indices, seed, tag, trt_model_id):
        self.rupture = self
        self.site_indices = site_indices
        self.seed = seed
        self.tag = tag
        self.trt_model_id = trt_model_id

        self.is_from_fault_source = iffs = isinstance(
            rupture.surface, (geo.ComplexFaultSurface, geo.SimpleFaultSurface))
        self.is_multi_surface = ims = isinstance(
            rupture.surface, geo.MultiSurface)
        self.lons, self.lats, self.depths = get_geom(
            rupture.surface, iffs, ims)
        self.surface = rupture.surface
        self.strike = rupture.surface.get_strike()
        self.dip = rupture.surface.get_dip()
        self.rake = rupture.rake
        self.hypocenter = rupture.hypocenter
        self.tectonic_region_type = rupture.tectonic_region_type
        self.magnitude = self.mag = rupture.mag

    @property
    def top_left_corner(self):
        if not (self.is_from_fault_source or self.is_multi_surface):
            return self.lons[0], self.lats[0], self.depths[0]

    @property
    def top_right_corner(self):
        if not (self.is_from_fault_source or self.is_multi_surface):
            return self.lons[1], self.lats[1], self.depths[1]

    @property
    def bottom_left_corner(self):
        if not (self.is_from_fault_source or self.is_multi_surface):
            return self.lons[2], self.lats[2], self.depths[2]

    @property
    def bottom_right_corner(self):
        if not (self.is_from_fault_source or self.is_multi_surface):
            return self.lons[3], self.lats[3], self.depths[3]


def get_ses_idx(sesrupture):
    """
    Extract the SES ordinal (>=1) from the rupture tag.
    For instance 'trt=00|ses=0001|src=1|rup=001-01' => 1
    """
    return int(sesrupture.tag.split('|', 2)[1].split('=')[1])


def compute_ruptures(sources, sitecol, monitor):
    """
    :param sources:
        List of commonlib.source.Source tuples
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param monitor:
        monitor instance
    :returns:
        a dictionary trt_model_id -> [Rupture instances]
    """
    # NB: by construction each block is a non-empty list with
    # sources of the same trt_model_id
    trt_model_id = sources[0].trt_model_id
    oq = monitor.oqparam
    all_ses = range(1, oq.ses_per_logic_tree_path + 1)
    sesruptures = []

    # Compute and save stochastic event sets
    rnd = random.Random()
    for src in sources:
        rnd.seed(src.seed)  # keep this here and not after the filtering;
        # in this way changing the maximum distance does not change the
        # generated seeds, which could be surprising

        s_sites = src.filter_sites_by_distance_to_source(
            oq.maximum_distance, sitecol)
        if s_sites is None:
            continue

        # the dictionary `ses_num_occ` contains [(ses, num_occurrences)]
        # for each occurring rupture for each ses in the ses collection
        ses_num_occ = collections.defaultdict(list)
        # generating ruptures for the given source
        for rup_no, rup in enumerate(src.iter_ruptures(), 1):
            rup.rup_no = rup_no
            for ses_idx in all_ses:
                numpy.random.seed(rnd.randint(0, MAX_INT))
                num_occurrences = rup.sample_number_of_occurrences()
                if num_occurrences:
                    ses_num_occ[rup].append((ses_idx, num_occurrences))

        # NB: the number of occurrences is very low, << 1, so it is
        # more efficient to filter only the ruptures that occur, i.e.
        # to call sample_number_of_occurrences() *before* the filtering
        for rup in sorted(ses_num_occ, key=operator.attrgetter('rup_no')):
            # filtering ruptures
            r_sites = filter_sites_by_distance_to_rupture(
                rup, oq.maximum_distance, s_sites)
            if r_sites is None:
                # ignore ruptures which are far away
                del ses_num_occ[rup]  # save memory
                continue
            indices = r_sites.indices if len(r_sites) < len(sitecol) \
                else None  # None means that nothing was filtered

            # creating SESRuptures
            for ses_idx, num_occurrences in ses_num_occ[rup]:
                for occ_no in range(1, num_occurrences + 1):
                    seed = rnd.randint(0, MAX_INT)
                    tag = 'trt=%02d|ses=%04d|src=%s|rup=%03d-%02d' % (
                        trt_model_id, ses_idx, src.source_id, rup.rup_no,
                        occ_no)
                    sesruptures.append(
                        SESRupture(rup, indices, seed, tag, trt_model_id))

    return {trt_model_id: sesruptures}


@base.calculators.add('event_based_rupture')
class EventBasedRuptureCalculator(base.HazardCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_func = compute_ruptures

    def pre_execute(self):
        """
        Set a seed on each source
        """
        super(EventBasedRuptureCalculator, self).pre_execute()
        rnd = random.Random()
        rnd.seed(self.oqparam.random_seed)
        for src in self.composite_source_model.sources:
            src.seed = rnd.randint(0, MAX_INT)

    def execute(self):
        """
        Run in parallel `core_func(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        monitor = self.monitor(self.core_func.__name__)
        monitor.oqparam = self.oqparam
        sources = list(self.composite_source_model.sources)
        result = parallel.apply_reduce(
            self.core_func.__func__,
            (sources, self.sitecol, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('trt_model_id'))
        return result

    def post_execute(self, result):
        """Export the ruptures, if any"""
        oq = self.oqparam
        saved = AccumDict()
        for smodel in self.composite_source_model:
            smpath = '_'.join(smodel.path)
            for trt_model in smodel.trt_models:
                sesruptures = result.get(trt_model.id, [])
                ses_coll = SESCollection(
                    groupby(sesruptures, get_ses_idx),
                    smodel.path, oq.investigation_time)
                fname = 'ses-%d-smltp_%s.xml' % (
                    trt_model.id, smpath)
                saved += export(('ses', 'xml'), oq.export_dir, fname, ses_coll)
        return saved


# ######################## GMF calculator ############################ #

def compute_gmfs_and_curves(ses_ruptures, sitecol, gsims_assoc, monitor):
    """
    :param ses_ruptures:
        a list of blocks of SESRuptures with homogeneous TrtModel
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param gsims_assoc:
        associations trt_model_id -> gsims
    :param monitor:
        a Monitor instance
    :returns:
        a dictionary trt_model_id -> curves_by_gsim
        where the list of bounding boxes is empty
    """
    oq = monitor.oqparam

    # NB: by construction each block is a non-empty list with
    # ruptures of the same trt_model_id
    trt_id = ses_ruptures[0].trt_model_id
    gsims = sorted(gsims_assoc[trt_id])
    imts = map(from_string, oq.imtls)
    trunc_level = getattr(oq, 'truncation_level', None)
    correl_model = readinput.get_correl_model(oq)

    result = AccumDict({(trt_id, str(gsim)): ([], AccumDict())
                        for gsim in gsims})
    for rupture, group in itertools.groupby(
            ses_ruptures, operator.attrgetter('rupture')):
        sesruptures = list(group)
        indices = sesruptures[0].site_indices
        r_sites = (sitecol if indices is None else
                   site.FilteredSiteCollection(indices, sitecol))

        computer = calc.gmf.GmfComputer(
            rupture, r_sites, imts, gsims, trunc_level, correl_model)
        for sr in sesruptures:
            for gsim_str, gmvs in computer.compute(sr.seed):
                gmf_by_imt = AccumDict(gmvs)
                gmf_by_imt.tag = sr.tag
                gmf_by_imt.r_sites = r_sites
                result[trt_id, gsim_str][0].append(gmf_by_imt)
    if getattr(oq, 'hazard_curves_from_gmfs', None):
        duration = oq.investigation_time * oq.ses_per_logic_tree_path
        for gsim in gsims:
            gmfs, curves = result[trt_id, str(gsim)]
            curves.update(to_haz_curves(
                sitecol.sids, gmfs, oq.imtls, oq.investigation_time, duration))
    return result


def to_haz_curves(sids, gmfs, imtls, investigation_time, duration):
    """
    :param sids: IDs of the given sites
    :param gmfs: a list of gmf keyed by IMT
    :param imtls: ordered dictionary {IMT: intensity measure levels}
    :param investigation_time: investigation time
    :param duration: investigation_time * number of Stochastic Event Sets
    """
    curves = {}
    for imt in imtls:
        data = collections.defaultdict(list)
        for gmf in gmfs:
            for sid, gmv in zip(gmf.r_sites.sids, gmf[imt]):
                data[sid].append(gmv)
        curves[imt] = numpy.array([
            gmvs_to_haz_curve(data.get(sid, []),
                              imtls[imt], investigation_time, duration)
            for sid in sids])
    return curves


@base.calculators.add('event_based')
class EventBasedCalculator(base.calculators['classical']):
    """
    Event based PSHA calculator generating the ruptures only
    """
    hazard_calculator = 'event_based_rupture'
    core_func = compute_gmfs_and_curves

    def pre_execute(self):
        """
        Read the precomputed ruptures (or compute them on the fly) and
        prepare some empty files in the export directory to store the gmfs
        (if any). If there were pre-existing files, they will be erased.
        """
        haz_out = base.get_hazard(self, post_execute=True)
        self.sitecol = haz_out['sitecol']
        self.rlzs_assoc = haz_out['rlzs_assoc']
        self.sesruptures = sorted(sum(haz_out['result'].itervalues(), []),
                                  key=operator.attrgetter('tag'))
        self.saved = AccumDict()
        if self.oqparam.ground_motion_fields:
            for trt_id, gsim in self.rlzs_assoc:
                name = '%s-%s.csv' % (trt_id, gsim)
                self.saved[name] = fname = os.path.join(
                    self.oqparam.export_dir, name)
                open(fname, 'w').close()

    def combine_curves_and_save_gmfs(self, acc, res):
        """
        Combine the hazard curves (if any) and save the gmfs (if any)
        sequentially; however, notice that the gmfs may come from
        different tasks in any order. The full list of gmfs is never
        stored in memory.

        :param acc: an accumulator for the hazard curves
        :param res: a dictionary trt_id, gsim -> (gmfs, curves_by_imt)
        :returns: a new accumulator
        """
        imts = list(self.oqparam.imtls)
        for trt_id, gsim in res:
            gmfs, curves_by_imt = res[trt_id, gsim]
            acc = agg_prob(acc, AccumDict({(trt_id, gsim): curves_by_imt}))
            fname = self.saved.get('%s-%s.csv' % (trt_id, gsim))
            if fname:  # when ground_motion_fields is true
                for gmf in gmfs:
                    row = [gmf.tag, gmf.r_sites.indices]
                    for imt in imts:
                        row.append(gmf[imt])
                    save_csv(fname, [row], mode='a')
        return acc

    def execute(self):
        """
        Run in parallel `core_func(sources, sitecol, monitor)`, by
        parallelizing on the ruptures according to their weight and
        tectonic region type.
        """
        monitor = self.monitor(self.core_func.__name__)
        monitor.oqparam = self.oqparam
        zero = AccumDict((key, AccumDict())
                         for key in self.rlzs_assoc)
        gsims_assoc = self.rlzs_assoc.get_gsims_by_trt_id()
        return parallel.apply_reduce(
            self.core_func.__func__,
            (self.sesruptures, self.sitecol, gsims_assoc, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks, acc=zero,
            agg=self.combine_curves_and_save_gmfs,
            key=operator.attrgetter('trt_model_id'))

    def post_execute(self, result):
        """
        Return a dictionary with the output files, i.e. gmfs (if any)
        and hazard curves (if any).
        """
        if getattr(self.oqparam, 'hazard_curves_from_gmfs', None):
            return self.saved + ClassicalCalculator.post_execute.__func__(
                self, result)
        return self.saved
