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
import logging
import itertools
import collections

import numpy

from openquake.baselib.general import AccumDict
from openquake.hazardlib.calc.filters import \
    filter_sites_by_distance_to_rupture
from openquake.hazardlib.calc.hazard_curve import zero_curves
from openquake.hazardlib import geo, site, calc
from openquake.commonlib import readinput, parallel, datastore
from openquake.commonlib.util import max_rel_diff_index

from openquake.commonlib.calculators import base
from openquake.commonlib.calculators.calc import MAX_INT, gmvs_to_haz_curve
from openquake.commonlib.calculators.classical import (
    ClassicalCalculator, agg_dicts)

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
    def __init__(self, rupture, indices, seed, tag, col_id):
        self.rupture = rupture
        self.indices = indices
        self.seed = seed
        self.tag = tag
        self.col_id = col_id
        # extract the SES ordinal (>=1) from the rupture tag
        # for instance 'col=00|ses=0001|src=1|rup=001-01' => 1
        pieces = tag.split('|')
        self.ses_idx = int(pieces[1].split('=')[1])

    def export(self):
        """
        Return a new SESRupture object, with all the attributes set
        suitable to export in XML format.
        """
        rupture = self.rupture
        new = self.__class__(
            rupture, self.indices, self.seed, self.tag, self.col_id)
        new.rupture = new
        new.is_from_fault_source = iffs = isinstance(
            rupture.surface, (geo.ComplexFaultSurface, geo.SimpleFaultSurface))
        new.is_multi_surface = ims = isinstance(
            rupture.surface, geo.MultiSurface)
        new.lons, new.lats, new.depths = get_geom(
            rupture.surface, iffs, ims)
        new.surface = rupture.surface
        new.strike = rupture.surface.get_strike()
        new.dip = rupture.surface.get_dip()
        new.rake = rupture.rake
        new.hypocenter = rupture.hypocenter
        new.tectonic_region_type = rupture.tectonic_region_type
        new.magnitude = new.mag = rupture.mag
        new.top_left_corner = None if iffs or ims else (
            new.lons[0], new.lats[0], new.depths[0])
        new.top_right_corner = None if iffs or ims else (
            new.lons[1], new.lats[1], new.depths[1])
        new.bottom_left_corner = None if iffs or ims else (
            new.lons[2], new.lats[2], new.depths[2])
        new.bottom_right_corner = None if iffs or ims else (
            new.lons[3], new.lats[3], new.depths[3])
        return new


@parallel.litetask
def compute_ruptures(sources, sitecol, info, monitor):
    """
    :param sources:
        List of commonlib.source.Source tuples
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param info:
        a :class:`openquake.commonlib.source.CompositionInfo` instance
    :param monitor:
        monitor instance
    :returns:
        a dictionary trt_model_id -> [Rupture instances]
    """
    # NB: by construction each block is a non-empty list with
    # sources of the same trt_model_id
    trt_model_id = sources[0].trt_model_id
    oq = monitor.oqparam
    sesruptures = []

    # Compute and save stochastic event sets
    for src in sources:
        s_sites = src.filter_sites_by_distance_to_source(
            oq.maximum_distance, sitecol)
        if s_sites is None:
            continue

        num_occ_by_rup = sample_ruptures(
            src, oq.ses_per_logic_tree_path, info)
        # NB: the number of occurrences is very low, << 1, so it is
        # more efficient to filter only the ruptures that occur, i.e.
        # to call sample_ruptures *before* the filtering

        for rup, rups in build_ses_ruptures(
                src, num_occ_by_rup, s_sites, oq.maximum_distance, sitecol):
            sesruptures.extend(rups)

    return {trt_model_id: sesruptures}


def sample_ruptures(src, num_ses, info):
    """
    Sample the ruptures contained in the given source.

    :param src: a hazardlib source object
    :param num_ses: the number of Stochastic Event Sets to generate
    :param info: a :class:`openquake.commonlib.source.CompositionInfo` instance
    :returns: a dictionary of dictionaries rupture ->
              {(col_id, ses_id): num_occurrences}
    """
    rnd = random.Random(src.seed)

    # the dictionary `num_occ_by_rup` contains a dictionary
    # (col_id, ses_id) -> num_occurrences
    # for each occurring rupture
    num_occ_by_rup = collections.defaultdict(AccumDict)
    # generating ruptures for the given source
    for rup_no, rup in enumerate(src.iter_ruptures(), 1):
        rup.rup_no = rup_no
        for idx in range(info.get_num_samples(src.trt_model_id)):
            col_id = info.get_col_id(src.trt_model_id, idx)
            for ses_idx in range(1, num_ses + 1):
                numpy.random.seed(rnd.randint(0, MAX_INT))
                num_occurrences = rup.sample_number_of_occurrences()
                if num_occurrences:
                    num_occ_by_rup[rup] += {
                        (col_id, ses_idx): num_occurrences}
    return num_occ_by_rup


def build_ses_ruptures(
        src, num_occ_by_rup, s_sites, maximum_distance, sitecol):
    """
    Filter the ruptures stored in the dictionary num_occ_by_rup and
    yield pairs (rupture, <list of associated SESRuptures>)
    """
    rnd = random.Random(src.seed)
    for rup in sorted(num_occ_by_rup, key=operator.attrgetter('rup_no')):
        # filtering ruptures
        r_sites = filter_sites_by_distance_to_rupture(
            rup, maximum_distance, s_sites)
        if r_sites is None:
            # ignore ruptures which are far away
            del num_occ_by_rup[rup]  # save memory
            continue
        indices = r_sites.indices if len(r_sites) < len(sitecol) \
            else None  # None means that nothing was filtered

        # creating SESRuptures
        sesruptures = []
        for (col_id, ses_idx), num_occ in sorted(
                num_occ_by_rup[rup].iteritems()):
            for occ_no in range(1, num_occ + 1):
                seed = rnd.randint(0, MAX_INT)
                tag = 'col=%02d|ses=%04d|src=%s|rup=%03d-%02d' % (
                    col_id, ses_idx, src.source_id, rup.rup_no, occ_no)
                sesruptures.append(
                    SESRupture(rup, indices, seed, tag, col_id))
        if sesruptures:
            yield rup, sesruptures


@base.calculators.add('event_based_rupture')
class EventBasedRuptureCalculator(base.HazardCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_func = compute_ruptures
    sescollection = datastore.persistent_attribute('sescollection')

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
        Run in parallel `core_func(sources, sitecol, info, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        monitor = self.monitor(self.core_func.__name__)
        monitor.oqparam = self.oqparam
        csm = self.composite_source_model
        sources = list(csm.sources)
        ruptures_by_trt = parallel.apply_reduce(
            self.core_func.__func__,
            (sources, self.sitecol, csm.info, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('trt_model_id'))

        logging.info('Generated %d SESRuptures',
                     sum(len(v) for v in ruptures_by_trt.itervalues()))

        self.rlzs_assoc = csm.get_rlzs_assoc(
            lambda trt: len(ruptures_by_trt.get(trt.id, [])))

        return ruptures_by_trt

    def post_execute(self, result):
        nc = self.rlzs_assoc.csm_info.num_collections
        sescollection = [{} for col_id in range(nc)]
        for trt_id in result:
            for sr in result[trt_id]:
                sescollection[sr.col_id][sr.tag] = sr
        self.sescollection = sescollection

# ######################## GMF calculator ############################ #


# NB: this will be replaced by hazardlib.calc.gmf.build_gmf_by_tag
def make_gmf_by_tag(ses_ruptures, sitecol, imts, gsims,
                    trunc_level, correl_model):
    """
    :returns: a dictionary tag -> (r_sites, gmf_array)
    """
    dic = {}
    for rupture, group in itertools.groupby(
            ses_ruptures, operator.attrgetter('rupture')):
        sesruptures = list(group)
        indices = sesruptures[0].indices
        r_sites = (sitecol if indices is None else
                   site.FilteredSiteCollection(indices, sitecol))
        computer = calc.gmf.GmfComputer(
            rupture, r_sites, imts, gsims, trunc_level, correl_model)
        for sr in sesruptures:
            dic[sr.tag] = computer.compute([sr.seed])[0]
    return dic


@parallel.litetask
def compute_gmfs_and_curves(ses_ruptures, sitecol, rlzs_assoc, monitor):
    """
    :param ses_ruptures:
        a list of blocks of SESRuptures of the same SESCollection
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param rlzs_assoc:
        a RlzsAssoc instance
    :param monitor:
        a Monitor instance
    :returns:
        a dictionary trt_model_id -> curves_by_gsim
        where the list of bounding boxes is empty
   """
    oq = monitor.oqparam
    # NB: by construction each block is a non-empty list with
    # ruptures of the same col_id and therefore trt_model_id
    col_id = ses_ruptures[0].col_id
    trt_id = rlzs_assoc.csm_info.get_trt_id(col_id)
    gsims = rlzs_assoc.get_gsims_by_col()[col_id]
    trunc_level = getattr(oq, 'truncation_level', None)
    correl_model = readinput.get_correl_model(oq)
    num_sites = len(sitecol)
    dic = make_gmf_by_tag(
        ses_ruptures, sitecol, oq.imtls, gsims, trunc_level, correl_model)
    zero = zero_curves(num_sites, oq.imtls)
    result = AccumDict({(trt_id, str(gsim)): [dic, zero] for gsim in gsims})
    gmfs = [dic[tag] for tag in sorted(dic)]
    if getattr(oq, 'hazard_curves_from_gmfs', None):
        duration = oq.investigation_time * oq.ses_per_logic_tree_path * (
            oq.number_of_logic_tree_samples or 1)
        for gsim in gsims:
            gs = str(gsim)
            result[trt_id, gs][1] = to_haz_curves(
                num_sites, gs, gmfs, oq.imtls,
                oq.investigation_time, duration)
    if not oq.ground_motion_fields:
        # reset the gmf_by_tag dictionary to avoid
        # transferring a lot of unused data
        for key in result:
            result[key][0].clear()
    return result


def to_haz_curves(num_sites, gs, gmfs, imtls, investigation_time, duration):
    """
    :param num_sites: length of the full site collection
    :param gs: a GSIM string
    :param gmfs: gmf arrays
    :param imtls: ordered dictionary {IMT: intensity measure levels}
    :param investigation_time: investigation time
    :param duration: investigation_time * number of Stochastic Event Sets
    """
    # group gmvs by site index
    data = [[] for idx in range(num_sites)]
    for gmf in gmfs:
        for idx, gmv in zip(gmf['idx'], gmf[gs]):
            data[idx].append(gmv)
    curves = zero_curves(num_sites, imtls)
    for imt in imtls:
        curves[imt] = numpy.array([
            gmvs_to_haz_curve([gmv[imt] for gmv in gmvs], imtls[imt],
                              investigation_time, duration) for gmvs in data])
    return curves


@base.calculators.add('event_based')
class EventBasedCalculator(ClassicalCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    pre_calculator = 'event_based_rupture'
    core_func = compute_gmfs_and_curves
    gmf_by_trt_gsim = datastore.persistent_attribute('gmf_by_trt_gsim')

    def pre_execute(self):
        """
        Read the precomputed ruptures (or compute them on the fly) and
        prepare some empty files in the export directory to store the gmfs
        (if any). If there were pre-existing files, they will be erased.
        """
        ClassicalCalculator.pre_execute(self)
        rupture_by_tag = sum(self.datastore['sescollection'], AccumDict())
        self.sesruptures = [rupture_by_tag[tag]
                            for tag in sorted(rupture_by_tag)]

    def combine_curves_and_save_gmfs(self, acc, res):
        """
        Combine the hazard curves (if any) and save the gmfs (if any)
        sequentially; however, notice that the gmfs may come from
        different tasks in any order.

        :param acc: an accumulator for the hazard curves
        :param res: a dictionary trt_id, gsim -> (gmfs, curves_by_imt)
        :returns: a new accumulator
        """
        gen_gmf = self.oqparam.ground_motion_fields
        for trt_id, gsim in res:
            gmf_by_tag, curves_by_imt = res[trt_id, gsim]
            if gen_gmf:
                self.gmf_dict[trt_id, gsim] += gmf_by_tag
            acc = agg_dicts(acc, AccumDict({(trt_id, gsim): curves_by_imt}))
        return acc

    def execute(self):
        """
        Run in parallel `core_func(sources, sitecol, monitor)`, by
        parallelizing on the ruptures according to their weight and
        tectonic region type.
        """
        monitor = self.monitor(self.core_func.__name__)
        monitor.oqparam = self.oqparam
        zc = zero_curves(len(self.sitecol), self.oqparam.imtls)
        zerodict = AccumDict((key, zc) for key in self.rlzs_assoc)
        self.gmf_dict = collections.defaultdict(AccumDict)
        curves_by_trt_gsim = parallel.apply_reduce(
            self.core_func.__func__,
            (self.sesruptures, self.sitecol, self.rlzs_assoc, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            acc=zerodict, agg=self.combine_curves_and_save_gmfs,
            key=operator.attrgetter('col_id'))
        return curves_by_trt_gsim

    def post_execute(self, result):
        """
        Return a dictionary with the output files, i.e. gmfs (if any)
        and hazard curves (if any).
        """
        oq = self.oqparam
        if oq.hazard_curves_from_gmfs:
            ClassicalCalculator.post_execute.__func__(self, result)
        if oq.ground_motion_fields:
            for (trt_id, gsim), gmf_by_tag in self.gmf_dict.items():
                self.gmf_dict[trt_id, gsim] = {tag: gmf_by_tag[tag][gsim]
                                               for tag in gmf_by_tag}
            self.gmf_by_trt_gsim = self.gmf_dict
            self.gmf_dict.clear()
        if self.mean_curves is not None:  # compute classical ones
            export_dir = os.path.join(oq.export_dir, 'cl')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            oq.export_dir = export_dir
            # use a different datastore
            self.cl = ClassicalCalculator(oq, self.monitor)
            # copy the relevant attributes
            self.cl.composite_source_model = self.csm
            self.cl.sitecol = self.sitecol
            self.cl.rlzs_assoc = self.csm.get_rlzs_assoc()
            result = self.cl.run(pre_execute=False)
            for imt in self.mean_curves.dtype.fields:
                rdiff, index = max_rel_diff_index(
                    self.cl.mean_curves[imt], self.mean_curves[imt])
                logging.warn('Relative difference with the classical '
                             'mean curves for IMT=%s: %d%% at site index %d',
                             imt, rdiff * 100, index)
