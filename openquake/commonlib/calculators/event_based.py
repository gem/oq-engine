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

from openquake.hazardlib import geo
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.filters import \
    filter_sites_by_distance_to_rupture
from openquake.hazardlib import site, calc
from openquake.commonlib import readinput, parallel
from openquake.commonlib.util import max_rel_diff_index

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
    def __init__(self, rupture, indices, seed, tag, trt_model_id):
        self.rupture = rupture
        self.indices = indices
        self.seed = seed
        self.tag = tag
        self.trt_model_id = trt_model_id
        # extract the SES ordinal (>=1) from the rupture tag
        # for instance 'col=00|ses=0001|src=1|rup=001-01' => 1
        pieces = tag.split('|')
        self.col_idx = int(pieces[0].split('=')[1])
        self.ses_idx = int(pieces[1].split('=')[1])

    def export(self):
        """
        Return a new SESRupture object, with all the attributes set
        suitable to export in XML format.
        """
        rupture = self.rupture
        new = self.__class__(
            rupture, self.indices, self.seed, self.tag, self.trt_model_id)
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
            col_idx = info.get_col_idx(src.trt_model_id, idx)
            for ses_idx in range(1, num_ses + 1):
                numpy.random.seed(rnd.randint(0, MAX_INT))
                num_occurrences = rup.sample_number_of_occurrences()
                if num_occurrences:
                    num_occ_by_rup[rup] += {
                        (col_idx, ses_idx): num_occurrences}
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
                    SESRupture(rup, indices, seed, tag, src.trt_model_id))
        if sesruptures:
            yield rup, sesruptures


@base.calculators.add('event_based_rupture')
class EventBasedRuptureCalculator(base.HazardCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_func = compute_ruptures
    result_kind = 'ruptures_by_trt'

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
        ses_ruptures_by_trt_id = parallel.apply_reduce(
            self.core_func.__func__,
            (sources, self.sitecol, csm.info, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('trt_model_id'))

        num_ruptures = sum(
            len(rups) for rups in ses_ruptures_by_trt_id.itervalues())
        logging.info('Generated %d SESRuptures', num_ruptures)

        self.rlzs_assoc = csm.get_rlzs_assoc(
            lambda trt: len(ses_ruptures_by_trt_id.get(trt.id, [])))

        return ses_ruptures_by_trt_id

    def post_execute(self, result):
        """Export the ruptures, if any"""
        oq = self.oqparam
        saved = AccumDict()
        if not oq.exports:
            return saved
        exports = oq.exports.split(',')
        for smodel in self.composite_source_model:
            smpath = '_'.join(smodel.path)
            for trt_model in smodel.trt_models:
                sesruptures = result.get(trt_model.id, [])
                ses_coll = SESCollection(
                    groupby(sesruptures, operator.attrgetter('ses_idx')),
                    smodel.path, oq.investigation_time)
                for fmt in exports:
                    fname = 'ses-%d-smltp_%s.%s' % (trt_model.id, smpath, fmt)
                    saved += export(
                        ('ses', fmt), oq.export_dir, fname, ses_coll)
        return saved


# ######################## GMF calculator ############################ #

GmfsCurves = collections.namedtuple('GmfsCurves', 'gmfs curves')


def make_gmf_by_key(ses_ruptures, sitecol, imts, gsims,
                    trunc_level, correl_model):
    """
    Yield gmf_by_imt AccumDicts for each SESRupture and GSIM, with attributes
    .tag, .gsim_str and .r_sites.
    """
    trt_id = ses_ruptures[0].trt_model_id
    dic = {(trt_id, str(gsim)): {} for gsim in gsims}
    for rupture, group in itertools.groupby(
            ses_ruptures, operator.attrgetter('rupture')):
        sesruptures = list(group)
        indices = sesruptures[0].indices
        r_sites = (sitecol if indices is None else
                   site.FilteredSiteCollection(indices, sitecol))
        computer = calc.gmf.GmfComputer(
            rupture, r_sites, imts, gsims, trunc_level, correl_model)
        for sr in sesruptures:
            for gsim_str, gmvs in computer.compute(sr.seed):
                gmf_by_imt = AccumDict(gmvs)
                gmf_by_imt.tag = sr.tag
                gmf_by_imt.r_sites = r_sites
                gmf_by_imt.gsim_str = gsim_str
                dic[trt_id, gsim_str][sr.tag] = gmf_by_imt
    return dic


@parallel.litetask
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
    # ruptures of the same col_idx and therefore trt_model_id
    trt_id = ses_ruptures[0].trt_model_id
    gsims = sorted(gsims_assoc[trt_id])
    imts = map(from_string, oq.imtls)
    trunc_level = getattr(oq, 'truncation_level', None)
    correl_model = readinput.get_correl_model(oq)

    result = AccumDict({(trt_id, str(gsim)): GmfsCurves([], AccumDict())
                        for gsim in gsims})
    ddic = make_gmf_by_key(
        ses_ruptures, sitecol, imts, gsims, trunc_level, correl_model)
    for gsim in gsims:
        data = ddic[trt_id, str(gsim)]
        result[trt_id, str(gsim)].gmfs.extend(
            data[tag] for tag in sorted(data))
    if getattr(oq, 'hazard_curves_from_gmfs', None):
        duration = oq.investigation_time * oq.ses_per_logic_tree_path * (
            oq.number_of_logic_tree_samples or 1)
        for gsim in gsims:
            gmfs, curves = result[trt_id, str(gsim)]
            curves.update(to_haz_curves(
                sitecol.sids, gmfs, oq.imtls, oq.investigation_time, duration))
    if not oq.ground_motion_fields:
        # reset the gmfs lists inside the result dictionary to avoid
        # transferring a lot of unused data
        for key in result:
            result[key].gmfs[:] = []
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
class EventBasedCalculator(ClassicalCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    hazard_calculator = 'event_based_rupture'
    core_func = compute_gmfs_and_curves
    result_kind = 'curves_by_trt_gsim'

    def pre_execute(self):
        """
        Read the precomputed ruptures (or compute them on the fly) and
        prepare some empty files in the export directory to store the gmfs
        (if any). If there were pre-existing files, they will be erased.
        """
        haz_out, hcalc = base.get_hazard(self, exports=self.oqparam.exports)
        self.composite_source_model = hcalc.composite_source_model
        self.sitecol = hcalc.sitecol
        self.rlzs_assoc = hcalc.rlzs_assoc
        self.sesruptures = sorted(
            sum(haz_out['ruptures_by_trt'].itervalues(), []),
            key=operator.attrgetter('tag'))
        self.saved = AccumDict()
        if self.oqparam.ground_motion_fields and 'csv' in self.oqparam.exports:
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
            if fname:  # when ground_motion_fields is true and there is csv
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
        curves_by_trt_gsim = parallel.apply_reduce(
            self.core_func.__func__,
            (self.sesruptures, self.sitecol, gsims_assoc, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks, acc=zero,
            agg=self.combine_curves_and_save_gmfs,
            key=operator.attrgetter('col_idx'))
        return curves_by_trt_gsim

    def post_execute(self, result):
        """
        Return a dictionary with the output files, i.e. gmfs (if any)
        and hazard curves (if any).
        """
        if getattr(self.oqparam, 'hazard_curves_from_gmfs', None):
            return self.saved + ClassicalCalculator.post_execute.__func__(
                self, result)
        return self.saved

    def save_pik(self, result, **kw):
        """
        :param result: the output of the `execute` method
        :param kw: extras to add to the output dictionary
        :returns: a dictionary with the saved data
        """
        haz_out = super(EventBasedCalculator, self).save_pik(result, **kw)
        if self.mean_curves is not None:  # compute classical ones
            export_dir = os.path.join(self.oqparam.export_dir, 'cl')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            self.oqparam.export_dir = export_dir
            self.cl = ClassicalCalculator(self.oqparam, self.monitor)
            # copy the relevant attributes
            self.cl.composite_source_model = self.composite_source_model
            self.cl.sitecol = self.sitecol
            self.cl.rlzs_assoc = self.composite_source_model.get_rlzs_assoc()
            result = self.cl.execute()
            exported = self.cl.post_execute(result)
            for item in sorted(exported.iteritems()):
                logging.info('exported %s: %s', *item)
            self.cl.save_pik(result, exported=exported)
            for imt in self.mean_curves:
                rdiff, index = max_rel_diff_index(
                    self.cl.mean_curves[imt], self.mean_curves[imt])
                logging.warn('Relative difference with the classical '
                             'mean curves for IMT=%s: %d%% at site index %d',
                             imt, rdiff * 100, index)
        return haz_out
