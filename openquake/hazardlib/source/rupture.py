# coding: utf-8
# The Hazard Library
# Copyright (C) 2012-2021 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.source.rupture` defines classes
:class:`BaseRupture` and its subclasses
:class:`NonParametricProbabilisticRupture` and
:class:`ParametricProbabilisticRupture`
"""
import abc
import numpy
import math
import itertools
import json
from openquake.baselib import general, hdf5
from openquake.hazardlib import geo, contexts
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo.mesh import (
    Mesh, RectangularMesh, surface_to_arrays)
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.geodetic import geodetic_distance
from openquake.hazardlib.near_fault import (
    get_plane_equation, projection_pp, directp, average_s_rad, isochone_ratio)
from openquake.hazardlib.geo.surface.base import BaseSurface

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16
TWO32 = 2 ** 32
pmf_dt = numpy.dtype([('prob', float), ('occ', U32)])
events_dt = numpy.dtype([('id', U32), ('rup_id', U32), ('rlz_id', U16)])
rupture_dt = numpy.dtype([('seed', U32),
                          ('mag', F32),
                          ('rake', F32),
                          ('lon', F32),
                          ('lat', F32),
                          ('dep', F32),
                          ('multiplicity', U32),
                          ('trt', hdf5.vstr),
                          ('kind', hdf5.vstr),
                          ('mesh', hdf5.vstr),
                          ('extra', hdf5.vstr)])

code2cls = {}


def to_csv_array(ruptures):
    """
    :param ruptures: a list of ruptures
    :returns: an array of ruptures suitable for serialization in CSV
    """
    if not code2cls:
        code2cls.update(BaseRupture.init())
    arr = numpy.zeros(len(ruptures), rupture_dt)
    for rec, rup in zip(arr, ruptures):
        arrays = surface_to_arrays(rup.surface)  # shape (3, s1, s2)
        rec['seed'] = rup.rup_id
        rec['mag'] = rup.mag
        rec['rake'] = rup.rake
        rec['lon'] = rup.hypocenter.x
        rec['lat'] = rup.hypocenter.y
        rec['dep'] = rup.hypocenter.z
        rec['multiplicity'] = rup.multiplicity
        rec['trt'] = rup.tectonic_region_type
        rec['kind'] = ' '.join(cls.__name__ for cls in code2cls[rup.code])
        rec['mesh'] = json.dumps(
            [[[[float5(z) for z in y] for y in x] for x in array]
             for array in arrays])
        extra = {}
        if hasattr(rup, 'probs_occur'):
            extra['probs_occur'] = rup.probs_occur
        else:
            extra['occurrence_rate'] = rup.occurrence_rate
        if hasattr(rup, 'weight'):
            extra['weight'] = rup.weight
        _fixfloat32(extra)
        rec['extra'] = json.dumps(extra)
    return arr


def from_array(aw):
    """
    :returns: a list of ruptures from an ArrayWrapper
    """
    rups = []
    names = aw.array.dtype.names
    for rec in aw.array:
        dic = dict(zip(names, rec))
        dic['trt'] = aw.trts[int(dic.pop('et_id'))]
        dic['hypo'] = dic.pop('lon'), dic.pop('lat'), dic.pop('dep')
        dic.update(json.loads(dic.pop('extra')))
        rups.append(_get_rupture(dic))
    return rups


def _get_rupture(rec, geom=None, trt=None):
    # rec: a dictionary or a record
    # geom: if any, an array of floats32 convertible into a mesh
    if not code2cls:
        code2cls.update(BaseRupture.init())
    if geom is None:
        points = F32([rec['lons'], rec['lats'], rec['depths']]).flat
        geom = numpy.concatenate([[1], [len(rec['lons']), 1], points])

    # build surface
    arrays = []
    num_surfaces = int(geom[0])
    start = num_surfaces * 2 + 1
    for i in range(1, 2 * num_surfaces, 2):
        s1, s2 = int(geom[i]), int(geom[i + 1])
        size = s1 * s2 * 3
        array = geom[start:start + size].reshape(3, s1, s2)
        arrays.append(array)
        start += size
    mesh = arrays[0]
    rupture_cls, surface_cls = code2cls[rec['code']]
    surface = object.__new__(surface_cls)
    if surface_cls is geo.PlanarSurface:
        surface = geo.PlanarSurface.from_array(mesh[:, 0, :])
    elif surface_cls is geo.MultiSurface:
        if all(array.shape == (3, 1, 4) for array in arrays):
            # for PlanarSurfaces each array has shape (3, 1, 4)
            surface.__init__([
                geo.PlanarSurface.from_array(array[:, 0, :])
                for array in arrays])
        else:
            # assume KyteSurfaces
            surface.__init__([geo.KiteSurface(RectangularMesh(*array))
                              for array in arrays])

    elif surface_cls is geo.GriddedSurface:
        # fault surface, strike and dip will be computed
        surface.strike = surface.dip = None
        surface.mesh = Mesh(*mesh)
    else:
        # fault surface, strike and dip will be computed
        surface.strike = surface.dip = None
        surface.__init__(RectangularMesh(*mesh))

    # build rupture
    rupture = object.__new__(rupture_cls)
    rupture.rup_id = rec['seed']
    rupture.surface = surface
    rupture.mag = rec['mag']
    rupture.rake = rec['rake']
    rupture.hypocenter = geo.Point(*rec['hypo'])
    rupture.occurrence_rate = rec['occurrence_rate']
    try:
        rupture.probs_occur = rec['probs_occur']
    except (KeyError, ValueError):  # rec can be a numpy record
        pass
    rupture.tectonic_region_type = trt or rec['trt']
    rupture.multiplicity = rec['n_occ']
    return rupture


def float5(x):
    # a float with 5 digits
    return round(float(x), 5)


def _fixfloat32(dic):
    # work around a TOML/numpy issue
    for k, v in dic.items():
        if isinstance(v, F32):
            dic[k] = float5(v)
        elif isinstance(v, tuple):
            dic[k] = [float5(x) for x in v]
        elif isinstance(v, numpy.ndarray):
            if len(v.shape) == 3:  # 3D array
                dic[k] = [[[float5(z) for z in y] for y in x] for x in v]
            elif len(v.shape) == 2:  # 2D array
                dic[k] = [[float5(y) for y in x] for x in v]
            elif len(v.shape) == 1:  # 1D array
                dic[k] = [float5(x) for x in v]
            else:
                raise NotImplementedError


def to_checksum8(cls1, cls2):
    """
    Convert a pair of classes into a numeric code (uint8)
    """
    names = '%s,%s' % (cls1.__name__, cls2.__name__)
    return sum(map(ord, names)) % 256


class BaseRupture(metaclass=abc.ABCMeta):
    """
    Rupture object represents a single earthquake rupture.

    :param mag:
        Magnitude of the rupture.
    :param rake:
        Rake value of the rupture.
        See :class:`~openquake.hazardlib.geo.nodalplane.NodalPlane`.
    :param tectonic_region_type:
        Rupture's tectonic regime. One of constants
        in :class:`openquake.hazardlib.const.TRT`.
    :param hypocenter:
        A :class:`~openquake.hazardlib.geo.point.Point`, rupture's hypocenter.
    :param surface:
        An instance of subclass of
        :class:`~openquake.hazardlib.geo.surface.base.BaseSurface`.
        Object representing the rupture surface geometry.
    :param rupture_slip_direction:
        Angle describing rupture propagation direction in decimal degrees.

    :raises ValueError:
        If magnitude value is not positive, or tectonic region type is unknown.

    NB: if you want to convert the rupture into XML, you should set the
    attribute surface_nodes to an appropriate value.
    """
    rup_id = 0  # set to a value > 0 by the engine
    _code = {}

    @classmethod
    def init(cls):
        """
        Initialize the class dictionary `._code` by encoding the
        bidirectional correspondence between an integer in the range 0..255
        (the code) and a pair of classes (rupture_class, surface_class).
        This is useful when serializing the rupture to and from HDF5.
        :returns: {code: pair of classes}
        """
        rupture_classes = [BaseRupture] + list(
            general.gen_subclasses(BaseRupture))
        surface_classes = list(general.gen_subclasses(BaseSurface))
        code2cls = {}
        BaseRupture.str2code = {}
        for rup, sur in itertools.product(rupture_classes, surface_classes):
            chk = to_checksum8(rup, sur)
            if chk in code2cls and code2cls[chk] != (rup, sur):
                raise ValueError('Non-unique checksum %d for %s, %s' %
                                 (chk, rup, sur))
            cls._code[rup, sur] = chk
            code2cls[chk] = rup, sur
            BaseRupture.str2code['%s %s' % (rup.__name__, sur.__name__)] = chk
        return code2cls

    def __init__(self, mag, rake, tectonic_region_type, hypocenter,
                 surface, rupture_slip_direction=None, weight=None):
        if not mag > 0:
            raise ValueError('magnitude must be positive')
        NodalPlane.check_rake(rake)
        self.tectonic_region_type = tectonic_region_type
        self.rake = rake
        self.mag = mag
        self.hypocenter = hypocenter
        self.surface = surface
        self.rupture_slip_direction = rupture_slip_direction
        self.weight = weight

    @property
    def code(self):
        """Returns the code (integer in the range 0 .. 255) of the rupture"""
        return self._code[self.__class__, self.surface.__class__]

    def size(self):
        """
        Dummy method for compatibility with the RuptureContext.

        :returns: 1
        """
        return 1

    get_probability_no_exceedance = (
        contexts.RuptureContext.get_probability_no_exceedance)

    def sample_number_of_occurrences(self, n=1):
        """
        Randomly sample number of occurrences from temporal occurrence model
        probability distribution.

        .. note::
            This method is using random numbers. In order to reproduce the
            same results numpy random numbers generator needs to be seeded, see
            http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.seed.html

        :returns:
            numpy array of size n with number of rupture occurrences
        """
        raise NotImplementedError


class NonParametricProbabilisticRupture(BaseRupture):
    """
    Probabilistic rupture for which the probability distribution for rupture
    occurrence is described through a generic probability mass function.

    :param pmf:
        Instance of :class:`openquake.hazardlib.pmf.PMF`. Values in the
        abscissae represent number of rupture occurrences (in increasing order,
        staring from 0) and values in the ordinates represent associated
        probabilities. Example: if, for a given time span, a rupture has
        probability ``0.8`` to not occurr, ``0.15`` to occur once, and
        ``0.05`` to occur twice, the ``pmf`` can be defined as ::

          pmf = PMF([(0.8, 0), (0.15, 1), 0.05, 2)])

    :raises ValueError:
        If number of ruptures in ``pmf`` do not start from 0, are not defined
        in increasing order, and if they are not defined with unit step
    """
    def __init__(self, mag, rake, tectonic_region_type, hypocenter, surface,
                 pmf, rupture_slip_direction=None, weight=None):
        occ = numpy.array([occ for (prob, occ) in pmf.data])
        if not occ[0] == 0:
            raise ValueError('minimum number of ruptures must be zero')
        if not numpy.all(numpy.sort(occ) == occ):
            raise ValueError(
                'numbers of ruptures must be defined in increasing order')
        if not numpy.all(numpy.diff(occ) == 1):
            raise ValueError(
                'numbers of ruptures must be defined with unit step')
        super().__init__(
            mag, rake, tectonic_region_type, hypocenter, surface,
            rupture_slip_direction, weight)
        # an array of probabilities with sum 1
        self.probs_occur = numpy.array([prob for (prob, occ) in pmf.data])
        self.occurrence_rate = numpy.nan

    def sample_number_of_occurrences(self, n=1):
        """
        See :meth:`superclass method
        <.rupture.BaseRupture.sample_number_of_occurrences>`
        for spec of input and result values.

        Uses 'Inverse Transform Sampling' method.
        """
        # compute cdf from pmf
        cdf = numpy.cumsum(self.probs_occur)
        n_occ = numpy.digitize(numpy.random.random(n), cdf)
        return n_occ


class ParametricProbabilisticRupture(BaseRupture):
    """
    :class:`Rupture` associated with an occurrence rate and a temporal
    occurrence model.

    :param occurrence_rate:
        Number of times rupture happens per year.
    :param temporal_occurrence_model:
        Temporal occurrence model assigned for this rupture. Should
        be an instance of :class:`openquake.hazardlib.tom.PoissonTOM`.

    :raises ValueError:
        If occurrence rate is not positive.
    """
    def __init__(self, mag, rake, tectonic_region_type, hypocenter, surface,
                 occurrence_rate, temporal_occurrence_model,
                 rupture_slip_direction=None):
        if not occurrence_rate > 0:
            raise ValueError('occurrence rate must be positive')
        super().__init__(
            mag, rake, tectonic_region_type, hypocenter, surface,
            rupture_slip_direction)
        self.temporal_occurrence_model = temporal_occurrence_model
        self.occurrence_rate = occurrence_rate

    def get_probability_one_or_more_occurrences(self):
        """
        Return the probability of this rupture to occur one or more times.

        Uses
        :meth:`~openquake.hazardlib.tom.PoissonTOM.get_probability_one_or_more_occurrences`
        of an assigned temporal occurrence model.
        """
        tom = self.temporal_occurrence_model
        rate = self.occurrence_rate
        return tom.get_probability_one_or_more_occurrences(rate)

    def get_probability_one_occurrence(self):
        """
        Return the probability of this rupture to occur exactly one time.

        Uses :meth:
        `openquake.hazardlib.tom.PoissonTOM.get_probability_n_occurrences`
        of an assigned temporal occurrence model.
        """
        tom = self.temporal_occurrence_model
        rate = self.occurrence_rate
        return tom.get_probability_n_occurrences(rate, 1)

    def sample_number_of_occurrences(self, n=1):
        """
        Draw a random sample from the distribution and return a number
        of events to occur as an array of integers of size n.

        Uses :meth:
        `openquake.hazardlib.tom.PoissonTOM.sample_number_of_occurrences`
        of an assigned temporal occurrence model.
        """
        r = self.occurrence_rate * self.temporal_occurrence_model.time_span
        return numpy.random.poisson(r, n)

    def get_probability_no_exceedance(self, poes):
        """
        See :meth:`superclass method
        <.rupture.BaseRupture.get_probability_no_exceedance>`
        for spec of input and result values.

        Uses
        :meth:`openquake.hazardlib.tom.PoissonTOM.get_probability_no_exceedance`
        """
        tom = self.temporal_occurrence_model
        rate = self.occurrence_rate
        return tom.get_probability_no_exceedance(rate, poes)

    def get_dppvalue(self, site):
        """
        Get the directivity prediction value, DPP at
        a given site as described in Spudich et al. (2013).

        :param site:
            :class:`~openquake.hazardlib.geo.point.Point` object
            representing the location of the target site
        :returns:
            A float number, directivity prediction value (DPP).
        """

        origin = self.surface.get_resampled_top_edge()[0]
        dpp_multi = []
        index_patch = self.surface.hypocentre_patch_index(
            self.hypocenter, self.surface.get_resampled_top_edge(),
            self.surface.mesh.depths[0][0], self.surface.mesh.depths[-1][0],
            self.surface.get_dip())
        idx_nxtp = True
        hypocenter = self.hypocenter

        while idx_nxtp:

            # E Plane Calculation
            p0, p1, p2, p3 = self.surface.get_fault_patch_vertices(
                self.surface.get_resampled_top_edge(),
                self.surface.mesh.depths[0][0],
                self.surface.mesh.depths[-1][0],
                self.surface.get_dip(), index_patch=index_patch)

            [normal, dist_to_plane] = get_plane_equation(
                p0, p1, p2, origin)

            pp = projection_pp(site, normal, dist_to_plane, origin)
            pd, e, idx_nxtp = directp(
                p0, p1, p2, p3, hypocenter, origin, pp)
            pd_geo = origin.point_at(
                (pd[0] ** 2 + pd[1] ** 2) ** 0.5, -pd[2],
                numpy.degrees(math.atan2(pd[0], pd[1])))

            # determine the lower bound of E path value
            f1 = geodetic_distance(p0.longitude,
                                   p0.latitude,
                                   p1.longitude,
                                   p1.latitude)
            f2 = geodetic_distance(p2.longitude,
                                   p2.latitude,
                                   p3.longitude,
                                   p3.latitude)

            if f1 > f2:
                f = f1
            else:
                f = f2

            fs, rd, r_hyp = average_s_rad(site, hypocenter, origin,
                                          pp, normal, dist_to_plane, e, p0,
                                          p1, self.rupture_slip_direction)
            cprime = isochone_ratio(e, rd, r_hyp)

            dpp_exp = cprime * numpy.maximum(e, 0.1 * f) *\
                numpy.maximum(fs, 0.2)
            dpp_multi.append(dpp_exp)

            # check if go through the next patch of the fault
            index_patch = index_patch + 1

            if (len(self.surface.get_resampled_top_edge())
                <= 2) and (index_patch >=
                           len(self.surface.get_resampled_top_edge())):

                idx_nxtp = False
            elif index_patch >= len(self.surface.get_resampled_top_edge()):
                idx_nxtp = False
            elif idx_nxtp:
                hypocenter = pd_geo
                idx_nxtp = True

        # calculate DPP value of the site.
        dpp = numpy.log(numpy.sum(dpp_multi))

        return dpp

    def get_cdppvalue(self, target, buf=1.0, delta=0.01, space=2.):
        """
        Get the directivity prediction value, centered DPP(cdpp) at
        a given site as described in Spudich et al. (2013), and this cdpp is
        used in Chiou and Young (2014) GMPE for near-fault directivity
        term prediction.

        :param target_site:
            A mesh object representing the location of the target sites.
        :param buf:
            A buffer distance in km to extend the mesh borders
        :param delta:
            The distance between two adjacent points in the mesh
        :param space:
            The tolerance for the distance of the sites (default 2 km)
        :returns:
            The centered directivity prediction value of Chiou and Young
        """
        min_lon, max_lon, max_lat, min_lat = self.surface.get_bounding_box()
        min_lon -= buf
        max_lon += buf
        min_lat -= buf
        max_lat += buf

        lons = numpy.arange(min_lon, max_lon + delta, delta)
        # ex shape (233,)
        lats = numpy.arange(min_lat, max_lat + delta, delta)
        # ex shape (204,)
        mesh = RectangularMesh(*numpy.meshgrid(lons, lats))
        mesh_rup = self.surface.get_min_distance(mesh).reshape(mesh.shape)
        # ex shape (204, 233)

        target_rup = self.surface.get_min_distance(target)
        # ex shape (2,)
        cdpp = numpy.zeros_like(target.lons)
        for i, (target_lon, target_lat) in enumerate(
                zip(target.lons, target.lats)):
            # indices around target_rup[i]
            around = (mesh_rup <= target_rup[i] + space) & (
                mesh_rup >= target_rup[i] - space)
            dpp_target = self.get_dppvalue(Point(target_lon, target_lat))
            dpp_mean = numpy.mean(
                [self.get_dppvalue(Point(lon, lat))
                 for lon, lat in zip(mesh.lons[around], mesh.lats[around])])
            cdpp[i] = dpp_target - dpp_mean

        return cdpp


class PointSurface:
    """
    A fake surface used in PointRuptures.
    The parameters `hypocenter`, `strike` and `dip` are determined by
    collapsing the corresponding parameters in the original PointSource.
    """
    def __init__(self, hypocenter, strike, dip):
        self.hypocenter = hypocenter
        self.strike = strike
        self.dip = dip

    def get_strike(self):
        return self.strike

    def get_dip(self):
        return self.dip

    def get_top_edge_depth(self):
        return self.hypocenter.depth

    def get_width(self):
        return 0

    def get_closest_points(self, mesh):
        return mesh

    def __bool__(self):
        return False


class PointRupture(ParametricProbabilisticRupture):
    """
    A rupture coming from a far away PointSource, so that the finite
    size effects can be neglected.
    """
    def __init__(self, mag, tectonic_region_type, hypocenter, strike,
                 dip, rake, occurrence_rate, temporal_occurrence_model):
        self.tectonic_region_type = tectonic_region_type
        self.hypocenter = hypocenter
        self.mag = mag
        self.strike = strike
        self.rake = rake
        self.dip = dip
        self.occurrence_rate = occurrence_rate
        self.temporal_occurrence_model = temporal_occurrence_model
        self.surface = PointSurface(hypocenter, strike, dip)
        self.weight = None  # no mutex


def get_geom(surface, is_from_fault_source, is_multi_surface,
             is_gridded_surface):
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

    :param surface: a Surface instance
    :param is_from_fault_source: a boolean
    :param is_multi_surface: a boolean
    """
    if is_from_fault_source:
        # for simple and complex fault sources,
        # rupture surface geometry is represented by a mesh
        surf_mesh = surface.mesh
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
        elif is_gridded_surface:
            # the surface mesh has shape (1, N)
            lons = surface.mesh.lons[0]
            lats = surface.mesh.lats[0]
            depths = surface.mesh.depths[0]
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


class ExportedRupture(object):
    """
    Simplified Rupture class with attributes rupid, events_by_ses, indices
    and others, used in export.

    :param rupid: rupture rup_id ID
    :param events_by_ses: dictionary ses_idx -> event records
    :param indices: site indices
    """
    def __init__(self, rupid, n_occ, events_by_ses, indices=None):
        self.rupid = rupid
        self.n_occ = n_occ
        self.events_by_ses = events_by_ses
        self.indices = indices


class EBRupture(object):
    """
    An event based rupture. It is a wrapper over a hazardlib rupture
    object, containing an array of site indices affected by the rupture,
    as well as the IDs of the corresponding seismic events.
    """
    def __init__(self, rupture, source_id, et_id, n_occ, id=None, e0=0):
        # NB: when reading an exported ruptures.xml the rup_id will be 0
        # for the first rupture; it used to be the seed instead
        assert rupture.rup_id >= 0  # sanity check
        self.rupture = rupture
        self.source_id = source_id
        self.et_id = et_id
        self.n_occ = n_occ
        self.id = id  # id of the rupture on the DataStore
        self.e0 = e0
        self.scenario = False

    @property
    def rup_id(self):
        """
        Seed of the rupture
        """
        return self.rupture.rup_id

    def get_eids_by_rlz(self, rlzs_by_gsim):
        """
        :params rlzs_by_gsim: a dictionary gsims -> rlzs array
        :returns: a dictionary rlz index -> eids array
        """
        dic = {}
        rlzs = numpy.concatenate(list(rlzs_by_gsim.values()))
        if self.scenario:
            all_eids = numpy.arange(self.n_occ, dtype=U32) + self.e0
            splits = numpy.array_split(all_eids, len(rlzs))
            for rlz_id, eids in zip(rlzs, splits):
                dic[rlz_id] = eids
        else:
            j = 0
            histo = general.random_histogram(
                self.n_occ, len(rlzs), self.rup_id)
            for rlz, n in zip(rlzs, histo):
                dic[rlz] = numpy.arange(j, j + n, dtype=U32) + self.e0
                j += n
        return dic

    def get_eids(self):
        """
        :returns: an array of event IDs
        """
        return numpy.arange(self.n_occ, dtype=U32)

    def export(self, events_by_ses):
        """
        Yield :class:`Rupture` objects, with all the
        attributes set, suitable for export in XML format.
        """
        rupture = self.rupture
        new = ExportedRupture(self.id, self.n_occ, events_by_ses)
        if isinstance(rupture.surface, geo.ComplexFaultSurface):
            new.typology = 'complexFaultsurface'
        elif isinstance(rupture.surface, geo.SimpleFaultSurface):
            new.typology = 'simpleFaultsurface'
        elif isinstance(rupture.surface, geo.GriddedSurface):
            new.typology = 'griddedRupture'
        elif isinstance(rupture.surface, geo.MultiSurface):
            new.typology = 'multiPlanesRupture'
        else:
            new.typology = 'singlePlaneRupture'
        new.is_from_fault_source = iffs = isinstance(
            rupture.surface, (geo.ComplexFaultSurface,
                              geo.SimpleFaultSurface))
        new.is_gridded_surface = igs = isinstance(
            rupture.surface, geo.GriddedSurface)
        new.is_multi_surface = ims = isinstance(
            rupture.surface, geo.MultiSurface)
        new.lons, new.lats, new.depths = get_geom(
            rupture.surface, iffs, ims, igs)
        new.surface = rupture.surface
        new.strike = rupture.surface.get_strike()
        new.dip = rupture.surface.get_dip()
        new.rake = rupture.rake
        new.hypocenter = rupture.hypocenter
        new.tectonic_region_type = rupture.tectonic_region_type
        new.magnitude = new.mag = rupture.mag
        new.top_left_corner = None if iffs or ims or igs else (
            new.lons[0], new.lats[0], new.depths[0])
        new.top_right_corner = None if iffs or ims or igs else (
            new.lons[1], new.lats[1], new.depths[1])
        new.bottom_left_corner = None if iffs or ims or igs else (
            new.lons[2], new.lats[2], new.depths[2])
        new.bottom_right_corner = None if iffs or ims or igs else (
            new.lons[3], new.lats[3], new.depths[3])
        return new

    def __repr__(self):
        return '<%s %d[%d]>' % (
            self.__class__.__name__, self.rup_id, self.n_occ)


class RuptureProxy(object):
    """
    A proxy for a rupture record.

    :param rec: a record with the rupture parameters
    :param nsites: approx number of sites affected by the rupture
    """
    def __init__(self, rec, nsites=None, scenario=False):
        self.rec = rec
        self.nsites = nsites
        self.scenario = scenario

    @property
    def weight(self):
        """
        :returns:
            heuristic weight for the underlying rupture, depending on the
            number of occurrences, number of samples and number of sites
        """
        return self['n_occ'] * (
            100 if self.nsites is None else max(self.nsites, 100))

    def __getitem__(self, name):
        return self.rec[name]

    # NB: requires the .geom attribute to be set
    def to_ebr(self, trt):
        """
        :returns: EBRupture instance associated to the underlying rupture
        """
        # not implemented: rupture_slip_direction
        rupture = _get_rupture(self.rec, self.geom, trt)
        ebr = EBRupture(rupture, self.rec['source_id'], self.rec['et_id'],
                        self.rec['n_occ'], self.rec['id'], self.rec['e0'])
        ebr.scenario = self.scenario
        return ebr
