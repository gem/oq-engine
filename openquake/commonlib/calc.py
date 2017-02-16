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
import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import encode, decode
from openquake.baselib.general import get_array, group_array
from openquake.hazardlib.geo.mesh import RectangularMesh, build_array
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.imt import from_string
from openquake.hazardlib import geo, tom, valid
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.probability_map import ProbabilityMap, get_shape
from openquake.commonlib import readinput, util


MAX_INT = 2 ** 31 - 1  # this is used in the random number generator
# in this way even on 32 bit machines Python will not have to convert
# the generated seed into a long integer

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64

event_dt = numpy.dtype([('eid', U32), ('ses', U32), ('occ', U32),
                        ('sample', U32)])
stored_event_dt = numpy.dtype([
    ('eid', U32), ('rupserial', U32), ('year', U32),
    ('ses', U32), ('occ', U32), ('sample', U32), ('grp_id', U16)])

# ############## utilities for the classical calculator ############### #


# used in classical and event_based calculators
def combine_pmaps(rlzs_assoc, results):
    """
    :param rlzs_assoc: a :class:`openquake.commonlib.source.RlzsAssoc` instance
    :param results: dictionary src_group_id -> probability map
    :returns: a dictionary rlz -> aggregate probability map
    """
    num_levels = get_shape(results.values())[1]
    acc = {rlz: ProbabilityMap(num_levels, 1)
           for rlz in rlzs_assoc.realizations}
    for grp_id in results:
        for i, gsim in enumerate(rlzs_assoc.gsims_by_grp_id[grp_id]):
            pmap = results[grp_id].extract(i)
            for rlz in rlzs_assoc.rlzs_assoc[grp_id, gsim]:
                if rlz in acc:
                    acc[rlz] |= pmap
    return acc

# ######################### hazard maps ################################### #

# cutoff value for the poe
EPSILON = 1E-30


def compute_hazard_maps(curves, imls, poes):
    """
    Given a set of hazard curve poes, interpolate a hazard map at the specified
    ``poe``.

    :param curves:
        2D array of floats. Each row represents a curve, where the values
        in the row are the PoEs (Probabilities of Exceedance) corresponding to
        ``imls``. Each curve corresponds to a geographical location.
    :param imls:
        Intensity Measure Levels associated with these hazard ``curves``. Type
        should be an array-like of floats.
    :param poes:
        Value(s) on which to interpolate a hazard map from the input
        ``curves``. Can be an array-like or scalar value (for a single PoE).
    :returns:
        An array of shape N x P, where N is the number of curves and P the
        number of poes.
    """
    poes = numpy.array(poes)

    if len(poes.shape) == 0:
        # `poes` was passed in as a scalar;
        # convert it to 1D array of 1 element
        poes = poes.reshape(1)

    if len(curves.shape) == 1:
        # `curves` was passed as 1 dimensional array, there is a single site
        curves = curves.reshape((1,) + curves.shape)  # 1 x L

    L = curves.shape[1]  # number of levels
    if L != len(imls):
        raise ValueError('The curves have %d levels, %d were passed' %
                         (L, len(imls)))
    result = []
    imls = numpy.log(numpy.array(imls[::-1]))
    for curve in curves:
        # the hazard curve, having replaced the too small poes with EPSILON
        curve_cutoff = [max(poe, EPSILON) for poe in curve[::-1]]
        hmap_val = []
        for poe in poes:
            # special case when the interpolation poe is bigger than the
            # maximum, i.e the iml must be smaller than the minumum
            if poe > curve_cutoff[-1]:  # the greatest poes in the curve
                # extrapolate the iml to zero as per
                # https://bugs.launchpad.net/oq-engine/+bug/1292093
                # a consequence is that if all poes are zero any poe > 0
                # is big and the hmap goes automatically to zero
                hmap_val.append(0)
            else:
                # exp-log interpolation, to reduce numerical errors
                # see https://bugs.launchpad.net/oq-engine/+bug/1252770
                val = numpy.exp(
                    numpy.interp(
                        numpy.log(poe), numpy.log(curve_cutoff), imls))
                hmap_val.append(val)

        result.append(hmap_val)
    return numpy.array(result)


# #########################  GMF->curves #################################### #

# NB (MS): the approach used here will not work for non-poissonian models
def _gmvs_to_haz_curve(gmvs, imls, invest_time, duration):
    """
    Given a set of ground motion values (``gmvs``) and intensity measure levels
    (``imls``), compute hazard curve probabilities of exceedance.

    :param gmvs:
        A list of ground motion values, as floats.
    :param imls:
        A list of intensity measure levels, as floats.
    :param float invest_time:
        Investigation time, in years. It is with this time span that we compute
        probabilities of exceedance.

        Another way to put it is the following. When computing a hazard curve,
        we want to answer the question: What is the probability of ground
        motion meeting or exceeding the specified levels (``imls``) in a given
        time span (``invest_time``).
    :param float duration:
        Time window during which GMFs occur. Another was to say it is, the
        period of time over which we simulate ground motion occurrences.

        NOTE: Duration is computed as the calculation investigation time
        multiplied by the number of stochastic event sets.

    :returns:
        Numpy array of PoEs (probabilities of exceedance).
    """
    # convert to numpy array and redimension so that it can be broadcast with
    # the gmvs for computing PoE values; there is a gmv for each rupture
    # here is an example: imls = [0.03, 0.04, 0.05], gmvs=[0.04750576]
    # => num_exceeding = [1, 1, 0] coming from 0.04750576 > [0.03, 0.04, 0.05]
    imls = numpy.array(imls).reshape((len(imls), 1))
    num_exceeding = numpy.sum(numpy.array(gmvs) >= imls, axis=1)
    poes = 1 - numpy.exp(- (invest_time / duration) * num_exceeding)
    return poes


# ################## utilities for classical calculators ################ #

def get_imts_periods(imtls):
    """
    Returns a list of IMT strings and a list of periods. There is an element
    for each IMT of type Spectral Acceleration, including PGA which is
    considered an alias for SA(0.0). The lists are sorted by period.

    :param imtls: a set of intensity measure type strings
    :returns: a list of IMT strings and a list of periods
    """
    def getperiod(imt):
        return imt[1] or 0
    imts = sorted((from_string(imt) for imt in imtls
                   if imt.startswith('SA') or imt == 'PGA'), key=getperiod)
    return [str(imt) for imt in imts], [imt[1] or 0.0 for imt in imts]


def make_hmap(pmap, imtls, poes):
    """
    Compute the hazard maps associated to the passed probability map.

    :param pmap: hazard curves in the form of a ProbabilityMap
    :param imtls: DictArray of intensity measure types and levels
    :param poes: P PoEs where to compute the maps
    :returns: a ProbabilityMap with size (N, I * P, 1)
    """
    I, P = len(imtls), len(poes)
    hmap = ProbabilityMap.build(I * P, 1, pmap)
    for i, imt in enumerate(imtls):
        curves = numpy.array([pmap[sid].array[imtls.slicedic[imt], 0]
                              for sid in pmap.sids])
        data = compute_hazard_maps(curves, imtls[imt], poes)  # array N x P
        for sid, value in zip(pmap.sids, data):
            array = hmap[sid].array
            for j, val in enumerate(value):
                array[i * P + j] = val
    return hmap


def make_uhs(pmap, imtls, poes, nsites):
    """
    Make Uniform Hazard Spectra curves for each location.

    It is assumed that the `lons` and `lats` for each of the `maps` are
    uniform.

    :param pmap:
        a probability map of hazard curves
    :param imtls:
        a dictionary of intensity measure types and levels
    :param poes:
        a sequence of PoEs for the underlying hazard maps
    :returns:
        an composite array containing nsites uniform hazard maps
    """
    P = len(poes)
    imts, _ = get_imts_periods(imtls)
    array = make_hmap(pmap, imtls, poes).array  # size (N, I x P, 1)
    imts_dt = numpy.dtype([(str(imt), F64) for imt in imts])
    uhs_dt = numpy.dtype([(str(poe), imts_dt) for poe in poes])
    uhs = numpy.zeros(nsites, uhs_dt)
    for j, poe in enumerate(map(str, poes)):
        for i, imt in enumerate(imtls):
            if imt in imts:
                uhs[poe][imt] = array[:, i * P + j, 0]
    return uhs


def get_gmfs(dstore, precalc=None):
    """
    :param dstore: a datastore
    :param precalc: a scenario calculator with attribute .gmfa
    :returns: a dictionary grp_id, gsid -> gmfa
    """
    oq = dstore['oqparam']
    if 'gmfs' in oq.inputs:  # from file
        logging.info('Reading gmfs from file')
        sitecol, etags, gmfs_by_imt = readinput.get_gmfs(oq)

        # reduce the gmfs matrices to the filtered sites
        for imt in oq.imtls:
            gmfs_by_imt[imt] = gmfs_by_imt[imt][sitecol.indices]

        logging.info('Preparing the risk input')
        return etags, [gmfs_by_imt]

    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    rlzs = rlzs_assoc.realizations
    sitecol = dstore['sitecol']
    # NB: if the hazard site collection has N sites, the hazard
    # filtered site collection for the nonzero GMFs has N' <= N sites
    # whereas the risk site collection associated to the assets
    # has N'' <= N' sites
    if dstore.parent:
        haz_sitecol = dstore.parent['sitecol']  # N' values
    else:
        haz_sitecol = sitecol
    risk_indices = set(sitecol.indices)  # N'' values
    N = len(haz_sitecol.complete)
    imt_dt = numpy.dtype([(str(imt), F32) for imt in oq.imtls])
    E = oq.number_of_ground_motion_fields
    etags = numpy.array(sorted(b'scenario-%010d~ses=1' % i for i in range(E)))
    gmfs = numpy.zeros((len(rlzs_assoc), N, E), imt_dt)
    if precalc:
        for i, gsim in enumerate(precalc.gsims):
            for imti, imt in enumerate(oq.imtls):
                gmfs[imt][i, sitecol.sids] = precalc.gmfa[gsim][imti]
        return etags, gmfs

    # else read from the datastore
    for i, rlz in enumerate(rlzs):
        data = group_array(dstore['gmf_data/sm-0000/%04d' % i], 'sid')
        for sid, array in data.items():
            if sid in risk_indices:
                for imti, imt in enumerate(oq.imtls):
                    a = get_array(array, imti=imti)
                    gmfs[imt][i, sid, a['eid']] = a['gmv']
    return etags, gmfs


def fix_minimum_intensity(min_iml, imts):
    """
    :param min_iml: a dictionary, possibly with a 'default' key
    :param imts: an ordered list of IMTs
    :returns: a numpy array of intensities, one per IMT

    Make sure the dictionary minimum_intensity (provided by the user in the
    job.ini file) is filled for all intensity measure types and has no key
    named 'default'. Here is how it works:

    >>> min_iml = {'PGA': 0.1, 'default': 0.05}
    >>> fix_minimum_intensity(min_iml, ['PGA', 'PGV'])
    array([ 0.1 ,  0.05], dtype=float32)
    >>> sorted(min_iml.items())
    [('PGA', 0.1), ('PGV', 0.05)]
    """
    if min_iml:
        for imt in imts:
            try:
                min_iml[imt] = valid.getdefault(min_iml, imt)
            except KeyError:
                raise ValueError(
                    'The parameter `minimum_intensity` in the job.ini '
                    'file is missing the IMT %r' % imt)
    if 'default' in min_iml:
        del min_iml['default']
    return F32([min_iml.get(imt, 0) for imt in imts])


gmv_dt = numpy.dtype([('sid', U16), ('eid', U32), ('imti', U8), ('gmv', F32)])


def check_overflow(calc):
    """
    :param calc: an event based calculator

    Raise a ValueError if the number of sites is larger than 65,536 or the
    number of IMTs is larger than 256 or the number of ruptures is larger
    than 4,294,967,296. The limits are due to the numpy dtype used to
    store the GMFs (gmv_dt). They could be relaxed in the future.
    """
    max_ = dict(sites=2**16, events=2**32, imts=2**8)
    num_ = dict(sites=len(calc.sitecol),
                events=len(calc.datastore['events']),
                imts=len(calc.oqparam.imtls))
    for var in max_:
        if num_[var] > max_[var]:
            raise ValueError(
                'The event based calculator is restricted to '
                '%d %s, got %d' % (max_[var], var, num_[var]))


class RuptureData(object):
    """
    Container for information about the ruptures of a given
    tectonic region type.
    """
    def __init__(self, trt, gsims):
        self.trt = trt
        self.cmaker = ContextMaker(gsims)
        self.params = sorted(self.cmaker.REQUIRES_RUPTURE_PARAMETERS -
                             set('mag strike dip rake hypo_depth'.split()))
        self.dt = numpy.dtype([
            ('rupserial', U32), ('multiplicity', U16),
            ('numsites', U32), ('occurrence_rate', F64),
            ('mag', F64), ('lon', F32), ('lat', F32), ('depth', F32),
            ('strike', F64), ('dip', F64), ('rake', F64),
            ('boundary', hdf5.vstr)] + [(param, F64) for param in self.params])

    def to_array(self, ebruptures, boundary=None):
        """
        Convert a list of ebruptures into an array of dtype RuptureRata.dt
        """
        data = []
        for ebr in ebruptures:
            rup = ebr.rupture
            rc = self.cmaker.make_rupture_context(rup)
            ruptparams = tuple(getattr(rc, param) for param in self.params)
            point = rup.surface.get_middle_point()
            multi_lons, multi_lats = rup.surface.get_surface_boundaries()
            if boundary is None:
                bounds = ','.join('((%s))' % ','.join(
                    '%.5f %.5f' % (lon, lat) for lon, lat in zip(lons, lats))
                    for lons, lats in zip(multi_lons, multi_lats))
            else:
                bounds = boundary
            try:
                rate = ebr.rupture.occurrence_rate
            except AttributeError:  # for nonparametric sources
                rate = numpy.nan
            data.append((ebr.serial, ebr.multiplicity, len(ebr.sids),
                         rate, rup.mag, point.x, point.y, point.z,
                         rup.surface.get_strike(), rup.surface.get_dip(),
                         rup.rake, decode(bounds)) + ruptparams)
        return numpy.array(data, self.dt)


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
    params = ['mag', 'rake', 'tectonic_region_type', 'hypo',
              'source_class', 'pmf', 'occurrence_rate',
              'time_span', 'rupture_slip_direction']

    def __init__(self, rupture, sids, events, source_id, grp_id, serial):
        self.rupture = rupture
        self.sids = sids
        self.events = events
        self.source_id = source_id
        self.grp_id = grp_id
        self.serial = serial

    @property
    def weight(self):
        """
        Weight of the EBRupture
        """
        return len(self.sids) * len(self.events)

    @property
    def etags(self):
        """
        An array of tags for the underlying seismic events
        """
        tags = []
        for (eid, ses, occ, sampleid) in self.events:
            tag = 'grp=%02d~ses=%04d~rup=%d-%02d' % (
                self.grp_id, ses, self.serial, occ)
            if sampleid > 0:
                tag += '~sample=%d' % sampleid
            tags.append(encode(tag))
        return numpy.array(tags)

    @property
    def eids(self):
        """
        An array with the underlying event IDs
        """
        return self.events['eid']

    @property
    def multiplicity(self):
        """
        How many times the underlying rupture occurs.
        """
        return len(self.events)

    def export(self, mesh, sm_by_grp):
        """
        Yield :class:`openquake.commonlib.util.Rupture` objects, with all the
        attributes set, suitable for export in XML format.
        """
        rupture = self.rupture
        for eid, etag in zip(self.eids, self.etags):
            new = util.Rupture(sm_by_grp[self.grp_id], eid, etag, self.sids)
            new.mesh = mesh[self.sids]
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

    def __toh5__(self):
        rup = self.rupture
        attrs = dict(source_id=self.source_id, grp_id=self.grp_id,
                     serial=self.serial)
        for par in self.params:
            val = getattr(self.rupture, par, None)
            if val is not None:
                attrs[par] = val
        if hasattr(rup, 'temporal_occurrence_model'):
            attrs['time_span'] = rup.temporal_occurrence_model.time_span
        if hasattr(rup, 'pmf'):
            attrs['pmf'] = rup.pmf_array()
        attrs['seed'] = rup.seed
        attrs['hypo'] = rup.hypocenter.x, rup.hypocenter.y, rup.hypocenter.z
        attrs['source_class'] = hdf5.cls2dotname(rup.source_typology)
        attrs['rupture_class'] = hdf5.cls2dotname(rup.__class__)
        attrs['surface_class'] = hdf5.cls2dotname(rup.surface.__class__)
        surface = self.rupture.surface
        if isinstance(surface, geo.MultiSurface):  # multiplanar surfaces
            n = len(surface.surfaces)
            arr = build_array([[s.corner_lons, s.corner_lats, s.corner_depths]
                               for s in surface.surfaces]).reshape(n, 2, 2)
            attrs['mesh_spacing'] = surface.surfaces[0].mesh_spacing
        else:
            mesh = surface.mesh
            if mesh is None:  # planar surface
                arr = build_array([[surface.corner_lons,
                                    surface.corner_lats,
                                    surface.corner_depths]]).reshape(1, 2, 2)
                attrs['mesh_spacing'] = surface.mesh_spacing
            else:  # general surface
                shp = (1,) + mesh.lons.shape
                arr = build_array(
                    [[mesh.lons, mesh.lats, mesh.depths]]).reshape(shp)
        attrs['nbytes'] = self.sids.nbytes + self.events.nbytes + arr.nbytes
        return dict(sids=self.sids, events=self.events, mesh=arr), attrs

    def __fromh5__(self, dic, attrs):
        attrs = dict(attrs)
        self.sids = dic['sids'].value
        self.events = dic['events'].value
        surface_class = attrs['surface_class']
        surface_cls = hdf5.dotname2cls(surface_class)
        self.rupture = object.__new__(hdf5.dotname2cls(attrs['rupture_class']))
        self.rupture.surface = surface = object.__new__(surface_cls)
        m = dic['mesh'].value
        if surface_class.endswith('PlanarSurface'):
            mesh_spacing = attrs.pop('mesh_spacing')
            self.rupture.surface = geo.PlanarSurface.from_array(
                mesh_spacing, m.flatten())
        elif surface_class.endswith('MultiSurface'):
            mesh_spacing = attrs.pop('mesh_spacing')
            self.rupture.surface.__init__([
                geo.PlanarSurface.from_array(mesh_spacing, m1.flatten())
                for m1 in m])
        else:  # fault surface
            surface.strike = surface.dip = None  # they will be computed
            surface.mesh = RectangularMesh(
                m['lon'][0], m['lat'][0], m['depth'][0])
        time_span = attrs.pop('time_span', None)
        if time_span:
            self.rupture.temporal_occurrence_model = tom.PoissonTOM(time_span)
        self.rupture.surface_nodes = ()
        if 'rupture_slip_direction' in attrs:
            logging.error('rupture_slip_direction not implemented yet')
        self.rupture.rupture_slip_direction = None
        self.rupture.hypocenter = Point(*attrs.pop('hypo'))
        self.rupture.source_typology = hdf5.dotname2cls(
            attrs.pop('source_class'))
        self.source_id = attrs.pop('source_id')
        self.grp_id = attrs.pop('grp_id')
        self.serial = attrs.pop('serial')
        del attrs['rupture_class']
        del attrs['surface_class']
        vars(self.rupture).update(attrs)

    def __lt__(self, other):
        return self.serial < other.serial

    def __repr__(self):
        return '<%s #%d, grp_id=%d>' % (self.__class__.__name__,
                                        self.serial, self.grp_id)
