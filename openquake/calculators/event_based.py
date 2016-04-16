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

import time
import os.path
import operator
import logging
import collections

import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import AccumDict
from openquake.baselib.python3compat import zip
from openquake.baselib.performance import Monitor
from openquake.hazardlib.calc.filters import \
    filter_sites_by_distance_to_rupture
from openquake.hazardlib.calc.hazard_curve import zero_curves
from openquake.hazardlib import geo, site, calc
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.commonlib import readinput, parallel, datastore
from openquake.commonlib.util import max_rel_diff_index, Rupture

from openquake.calculators import base, views
from openquake.calculators.calc import gmvs_to_haz_curve
from openquake.calculators.classical import ClassicalCalculator

# ######################## rupture calculator ############################ #

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32


def num_affected_sites(rupture, num_sites):
    """
    :param rupture: a EBRupture object
    :param num_sites: the total number of sites
    :returns: the number of sites affected by the rupture
    """
    return (len(rupture.indices) if rupture.indices is not None
            else num_sites)


def get_site_ids(rupture, num_sites):
    """
    :param rupture: a EBRupture object
    :param num_sites: the total number of sites
    :returns: the indices of the sites affected by the rupture
    """
    if rupture.indices is None:
        return list(range(num_sites))
    return rupture.indices


@datastore.view.add('col_rlz_assocs')
def view_col_rlz_assocs(name, dstore):
    """
    :returns: an array with the association array col_ids -> rlz_ids
    """
    rlzs_assoc = dstore['rlzs_assoc']
    num_ruptures = dstore.get_attr('etags', 'num_ruptures')
    num_rlzs = len(rlzs_assoc.realizations)
    col_ids_list = [[] for _ in range(num_rlzs)]
    for rlz in rlzs_assoc.realizations:
        for col_id in sorted(rlzs_assoc.get_col_ids(rlz)):
            if num_ruptures[col_id]:
                col_ids_list[rlz.ordinal].append(col_id)
    assocs = collections.defaultdict(list)
    for i, col_ids in enumerate(col_ids_list):
        assocs[tuple(col_ids)].append(i)
    tbl = [['Collections', 'Realizations']] + sorted(assocs.items())
    return views.rst_table(tbl)


# #################################################################### #


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

    :param rupture: an instance of :class:`openquake.hazardlib.source.rupture.BaseProbabilisticRupture`
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


class EBRupture(object):
    """
    An event based rupture. It is a wrapper over a hazardlib rupture
    object, containing an array of site indices affected by the rupture,
    as well as the tags of the corresponding seismic events.
    """
    def __init__(self, rupture, indices, etags, trt_id, serial):
        self.rupture = rupture
        self.indices = indices
        self.etags = numpy.array(etags)
        self.trt_id = trt_id
        self.serial = serial

    @property
    def multiplicity(self):
        """
        How many times the underlying rupture occurs.
        """
        return len(self.etags)

    def export(self, mesh):
        """
        Yield :class:`openquake.commonlib.util.Rupture` objects, with all the
        attributes set, suitable for export in XML format.
        """
        rupture = self.rupture
        for etag in self.etags:
            new = Rupture(etag, self.indices)
            new.mesh = mesh[self.indices]
            new.etag = etag
            new.rupture = new
            new.is_from_fault_source = iffs = isinstance(
                rupture.surface, (geo.ComplexFaultSurface,
                                  geo.SimpleFaultSurface))
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
            yield new

    def __lt__(self, other):
        return self.serial < other.serial

    def __repr__(self):
        return '<%s #%d, trt_id=%d>' % (self.__class__.__name__,
                                        self.serial, self.trt_id)


@parallel.litetask
def compute_ruptures(sources, sitecol, siteidx, rlzs_assoc, monitor):
    """
    :param sources:
        List of commonlib.source.Source tuples
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param siteidx:
        always equal to 0
    :param rlzs_assoc:
        a :class:`openquake.commonlib.source.RlzsAssoc` instance
    :param monitor:
        monitor instance
    :returns:
        a dictionary trt_model_id -> [Rupture instances]
    """
    assert siteidx == 0, (
        'siteidx can be nonzero only for the classical_tiling calculations: '
        'tiling with the EventBasedRuptureCalculator is an error')
    # NB: by construction each block is a non-empty list with
    # sources of the same trt_model_id
    trt_model_id = sources[0].trt_model_id
    oq = monitor.oqparam
    trt = sources[0].tectonic_region_type
    try:
        max_dist = oq.maximum_distance[trt]
    except KeyError:
        max_dist = oq.maximum_distance['default']
    totsites = len(sitecol)
    cmaker = ContextMaker(rlzs_assoc.gsims_by_trt_id[trt_model_id])
    params = cmaker.REQUIRES_RUPTURE_PARAMETERS
    rup_data_dt = numpy.dtype(
        [('rupserial', U32), ('multiplicity', U16), ('numsites', U32)] + [
            (param, F32) for param in params])

    eb_ruptures = []
    rup_data = []
    calc_times = []

    # Compute and save stochastic event sets
    for src in sources:
        t0 = time.time()
        s_sites = src.filter_sites_by_distance_to_source(max_dist, sitecol)
        if s_sites is None:
            continue

        num_occ_by_rup = sample_ruptures(
            src, oq.ses_per_logic_tree_path, rlzs_assoc.csm_info)
        # NB: the number of occurrences is very low, << 1, so it is
        # more efficient to filter only the ruptures that occur, i.e.
        # to call sample_ruptures *before* the filtering
        for ebr in build_eb_ruptures(
                src, num_occ_by_rup, s_sites, max_dist, sitecol,
                oq.random_seed):
            nsites = totsites if ebr.indices is None else len(ebr.indices)
            rc = cmaker.make_rupture_context(ebr.rupture)
            ruptparams = tuple(getattr(rc, param) for param in params)
            rup_data.append((ebr.serial, len(ebr.etags), nsites) + ruptparams)
            eb_ruptures.append(ebr)
        dt = time.time() - t0
        calc_times.append((src.id, dt))
    res = AccumDict({trt_model_id: eb_ruptures})
    res.calc_times = calc_times
    res.rup_data = numpy.array(rup_data, rup_data_dt)
    res.trt = trt
    return res


def sample_ruptures(src, num_ses, info):
    """
    Sample the ruptures contained in the given source.

    :param src: a hazardlib source object
    :param num_ses: the number of Stochastic Event Sets to generate
    :param info: a :class:`openquake.commonlib.source.CompositionInfo` instance
    :returns: a dictionary of dictionaries rupture ->
              {(col_id, ses_id): num_occurrences}
    """
    col_ids = info.col_ids_by_trt_id[src.trt_model_id]
    # the dictionary `num_occ_by_rup` contains a dictionary
    # (col_id, ses_id) -> num_occurrences
    # for each occurring rupture
    num_occ_by_rup = collections.defaultdict(AccumDict)
    # generating ruptures for the given source
    for rup_no, rup in enumerate(src.iter_ruptures()):
        rup.seed = seed = src.serial[rup_no] + info.seed
        numpy.random.seed(seed)
        for col_id in col_ids:
            for ses_idx in range(1, num_ses + 1):
                num_occurrences = rup.sample_number_of_occurrences()
                if num_occurrences:
                    num_occ_by_rup[rup] += {
                        (col_id, ses_idx): num_occurrences}
        rup.rup_no = rup_no + 1
    return num_occ_by_rup


def build_eb_ruptures(
        src, num_occ_by_rup, s_sites, maximum_distance, sitecol, random_seed):
    """
    Filter the ruptures stored in the dictionary num_occ_by_rup and
    yield pairs (rupture, <list of associated EBRuptures>)
    """
    totsites = len(sitecol)
    for rup in sorted(num_occ_by_rup, key=operator.attrgetter('rup_no')):
        # filtering ruptures
        r_sites = filter_sites_by_distance_to_rupture(
            rup, maximum_distance, s_sites)
        if r_sites is None:
            # ignore ruptures which are far away
            del num_occ_by_rup[rup]  # save memory
            continue
        if len(r_sites) < totsites:
            indices = r_sites.indices
        else:
            indices = None  # None means that nothing was filtered

        # creating EBRuptures
        serial = rup.seed - random_seed + 1
        etags = []
        for (col_idx, ses_idx), num_occ in sorted(
                num_occ_by_rup[rup].items()):
            for occ_no in range(1, num_occ + 1):
                etag = 'col=%02d~ses=%04d~src=%s~rup=%d-%02d' % (
                    col_idx, ses_idx, src.source_id, serial, occ_no)
                etags.append(etag)
        if etags:
            yield EBRupture(rup, indices, etags, src.trt_model_id, serial)


@base.calculators.add('event_based_rupture')
class EventBasedRuptureCalculator(ClassicalCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_task = compute_ruptures
    etags = datastore.persistent_attribute('etags')
    is_stochastic = True

    def count_eff_ruptures(self, ruptures_by_trt_id, trt_model):
        """
        Returns the number of ruptures sampled in the given trt_model.

        :param ruptures_by_trt_id: a dictionary with key trt_id
        :param trt_model: a TrtModel instance
        """
        return sum(
            len(ruptures) for trt_id, ruptures in ruptures_by_trt_id.items()
            if trt_model.id == trt_id)

    def agg_curves(self, acc, val):
        """
        For the rupture calculator, increment the AccumDict trt_id -> ruptures
        and save the rup_data
        """
        acc += val
        if len(val.rup_data):
            try:
                dset = self.rup_data[val.trt]
            except KeyError:
                dset = self.rup_data[val.trt] = self.datastore.create_dset(
                    'rup_data/' + val.trt, val.rup_data.dtype)
            dset.extend(val.rup_data)

    def zerodict(self):
        """
        Initial accumulator, a dictionary trt_model_id -> list of ruptures
        """
        smodels = self.rlzs_assoc.csm_info.source_models
        zd = AccumDict((tm.id, []) for smodel in smodels
                       for tm in smodel.trt_models)
        zd.calc_times = []
        return zd

    def send_sources(self):
        """
        Filter, split and set the seed array for each source, then send it the
        workers
        """
        oq = self.oqparam
        self.manager = self.SourceManager(
            self.csm, self.core_task.__func__,
            oq.maximum_distance, self.datastore,
            self.monitor.new(oqparam=oq), oq.random_seed, oq.filter_sources)
        self.manager.submit_sources(self.sitecol)

    def post_execute(self, result):
        """
        Save the SES collection
        """
        logging.info('Generated %d EBRuptures',
                     sum(len(v) for v in result.values()))
        with self.monitor('saving ruptures', autoflush=True):
            nc = self.rlzs_assoc.csm_info.num_collections
            sescollection = [[] for trt_id in range(nc)]
            etags = []
            for trt_id in result:
                for ebr in result[trt_id]:
                    sescollection[trt_id].append(ebr)
                    etags.extend(ebr.etags)
            etags.sort()
            etag2eid = dict(zip(etags, range(len(etags))))
            self.etags = numpy.array(etags, (bytes, 100))
            self.datastore.set_attrs(
                'etags',
                num_ruptures=numpy.array([len(sc) for sc in sescollection]))
            for i, sescol in enumerate(sescollection):
                for ebr in sescol:
                    ebr.eids = [etag2eid[etag] for etag in ebr.etags]
                nr = len(sescol)
                if nr:
                    logging.info('Saving SES collection #%d with %d ruptures',
                                 i, nr)
                    key = 'sescollection/trt=%02d' % i
                    self.datastore[key] = hdf5.PickleableSequence(
                        sorted(sescol, key=operator.attrgetter('serial')))
                    self.datastore.set_attrs(key, trt_model_id=i)
        self.datastore.set_nbytes('sescollection')
        for dset in self.rup_data.values():
            numsites = dset.dset['numsites']
            multiplicity = dset.dset['multiplicity']
            spr = numpy.average(numsites, weights=multiplicity)
            mul = numpy.average(multiplicity, weights=numsites)
            self.datastore.set_attrs(dset.name, sites_per_rupture=spr,
                                     multiplicity=mul)
        self.datastore.set_nbytes('rup_data')


# ######################## GMF calculator ############################ #

GmfaSidsEtags = collections.namedtuple('GmfaSidsEtags', 'gmfa sids etags')


def make_gmfs(eb_ruptures, sitecol, imts, gsims,
              trunc_level, correl_model, monitor=Monitor()):
    """
    :param eb_ruptures: a list of EBRuptures
    :param sitecol: a SiteCollection instance
    :param imts: an ordered list of intensity measure type strings
    :param gsims: an order list of GSIM instance
    :param trunc_level: truncation level
    :param correl_model: correlation model instance
    :param monitor: a monitor instance
    :returns: a dictionary serial -> GmfaSidsEtags
    """
    dic = {}  # serial -> GmfaSidsEtags
    ctx_mon = monitor('make contexts')
    gmf_mon = monitor('compute poes')
    sites = sitecol.complete
    for ebr in eb_ruptures:
        with ctx_mon:
            r_sites = (sitecol if ebr.indices is None else
                       site.FilteredSiteCollection(ebr.indices, sites))
            computer = calc.gmf.GmfComputer(
                ebr.rupture, r_sites, imts, gsims, trunc_level, correl_model)
        with gmf_mon:
            gmfa = computer.calcgmfs(ebr.multiplicity, ebr.rupture.seed)
            dic[ebr.serial] = GmfaSidsEtags(gmfa, r_sites.indices, ebr.etags)
    return dic


@parallel.litetask
def compute_gmfs_and_curves(eb_ruptures, sitecol, rlzs_assoc, monitor):
    """
    :param eb_ruptures:
        a list of blocks of EBRuptures of the same SESCollection
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param rlzs_assoc:
        a RlzsAssoc instance
    :param monitor:
        a Monitor instance
    :returns:
        a dictionary (trt_model_id, gsim) -> haz_curves and/or
        (trt_model_id, col_id) -> gmfs
   """
    oq = monitor.oqparam
    # NB: by construction each block is a non-empty list with
    # ruptures of the same col_id and therefore trt_model_id
    trt_id = eb_ruptures[0].trt_id
    gsims = rlzs_assoc.gsims_by_trt_id[trt_id]
    trunc_level = oq.truncation_level
    correl_model = readinput.get_correl_model(oq)
    tot_sites = len(sitecol.complete)
    gmfa_sids_etags = make_gmfs(
        eb_ruptures, sitecol, oq.imtls, gsims, trunc_level, correl_model,
        monitor)
    result = {trt_id: gmfa_sids_etags if oq.ground_motion_fields else None}
    if oq.hazard_curves_from_gmfs:
        with monitor('bulding hazard curves', measuremem=False):
            duration = oq.investigation_time * oq.ses_per_logic_tree_path * (
                oq.number_of_logic_tree_samples or 1)

            # collect the gmvs by site
            gmvs_by_sid = collections.defaultdict(list)
            for serial in gmfa_sids_etags:
                gst = gmfa_sids_etags[serial]
                for sid, gmvs in zip(gst.sids, gst.gmfa.T):
                    gmvs_by_sid[sid].extend(gmvs)

            # build the hazard curves for each GSIM
            for gsim in gsims:
                gs = str(gsim)
                result[trt_id, gs] = to_haz_curves(
                    tot_sites, gmvs_by_sid, gs, oq.imtls,
                    oq.investigation_time, duration)
    return result


def to_haz_curves(num_sites, gmvs_by_sid, gs, imtls,
                  investigation_time, duration):
    """
    :param num_sites: length of the full site collection
    :param gmvs_by_sid: dictionary site_id -> gmvs
    :param gs: GSIM string
    :param imtls: ordered dictionary {IMT: intensity measure levels}
    :param investigation_time: investigation time
    :param duration: investigation_time * number of Stochastic Event Sets
    """
    curves = zero_curves(num_sites, imtls)
    for imt in imtls:
        curves[imt] = numpy.array([
            gmvs_to_haz_curve(
                [gmv[gs][imt] for gmv in gmvs_by_sid[sid]],
                imtls[imt], investigation_time, duration)
            for sid in range(num_sites)])
    return curves


@base.calculators.add('event_based')
class EventBasedCalculator(ClassicalCalculator):
    """
    Event based PSHA calculator generating the ground motion fields and
    the hazard curves from the ruptures, depending on the configuration
    parameters.
    """
    pre_calculator = 'event_based_rupture'
    core_task = compute_gmfs_and_curves
    is_stochastic = True

    def pre_execute(self):
        """
        Read the precomputed ruptures (or compute them on the fly) and
        prepare some empty files in the export directory to store the gmfs
        (if any). If there were pre-existing files, they will be erased.
        """
        super(EventBasedCalculator, self).pre_execute()
        self.sesruptures = []
        for trt_id in range(self.rlzs_assoc.csm_info.num_collections):
            try:
                sescol = self.datastore['sescollection/trt=%02d' % trt_id]
            except KeyError:  # empty collections are missing
                continue
            self.sesruptures.extend(sescol)

    def combine_curves_and_save_gmfs(self, acc, res):
        """
        Combine the hazard curves (if any) and save the gmfs (if any)
        sequentially; notice that the gmfs may come from
        different tasks in any order.

        :param acc: an accumulator for the hazard curves
        :param res: a dictionary trt_id, gsim -> gmf_array or curves_by_imt
        :returns: a new accumulator
        """
        sav_mon = self.monitor('saving gmfs')
        agg_mon = self.monitor('aggregating hcurves')
        save_gmfs = self.oqparam.ground_motion_fields
        for trt_id in res:
            if isinstance(trt_id, int) and save_gmfs:
                with sav_mon:
                    gmfa_sids_etags = res[trt_id]
                    for serial in sorted(gmfa_sids_etags):
                        gst = gmfa_sids_etags[serial]
                        self.datastore['gmf_data/%s' % serial] = gst.gmfa
                        self.datastore['sid_data/%s' % serial] = gst.sids
                        self.datastore.set_attrs('gmf_data/%s' % serial,
                                                 trt_id=trt_id,
                                                 etags=gst.etags)
                    self.datastore.hdf5.flush()
            elif isinstance(trt_id, tuple):  # aggregate hcurves
                with agg_mon:
                    self.agg_dicts(acc, {trt_id: res[trt_id]})
        sav_mon.flush()
        agg_mon.flush()
        return acc

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the ruptures according to their weight and
        tectonic region type.
        """
        oq = self.oqparam
        if not oq.hazard_curves_from_gmfs and not oq.ground_motion_fields:
            return
        monitor = self.monitor(self.core_task.__name__)
        monitor.oqparam = oq
        zc = zero_curves(len(self.sitecol.complete), self.oqparam.imtls)
        zerodict = AccumDict((key, zc) for key in self.rlzs_assoc)
        curves_by_trt_gsim = parallel.apply_reduce(
            self.core_task.__func__,
            (self.sesruptures, self.sitecol, self.rlzs_assoc, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            acc=zerodict, agg=self.combine_curves_and_save_gmfs,
            key=operator.attrgetter('trt_id'),
            weight=operator.attrgetter('multiplicity'))
        if oq.ground_motion_fields:
            self.datastore.set_nbytes('gmf_data')
            self.datastore.set_nbytes('sid_data')
        return curves_by_trt_gsim

    def post_execute(self, result):
        """
        :param result:
            a dictionary (trt_model_id, gsim) -> haz_curves or an empty
            dictionary if hazard_curves_from_gmfs is false
        """
        oq = self.oqparam
        if not oq.hazard_curves_from_gmfs and not oq.ground_motion_fields:
            return
        if oq.hazard_curves_from_gmfs:
            ClassicalCalculator.post_execute.__func__(self, result)
        if oq.compare_with_classical:  # compute classical curves
            export_dir = os.path.join(oq.export_dir, 'cl')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            oq.export_dir = export_dir
            # use a different datastore
            self.cl = ClassicalCalculator(oq, self.monitor)
            self.cl.datastore.parent = self.datastore
            # TODO: perhaps it is possible to avoid reprocessing the source
            # model, however usually this is quite fast and do not dominate
            # the computation
            result = self.cl.run()
            for imt in self.mean_curves.dtype.fields:
                rdiff, index = max_rel_diff_index(
                    self.cl.mean_curves[imt], self.mean_curves[imt])
                logging.warn('Relative difference with the classical '
                             'mean curves for IMT=%s: %d%% at site index %d',
                             imt, rdiff * 100, index)
