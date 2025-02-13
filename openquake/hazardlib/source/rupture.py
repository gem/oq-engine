# coding: utf-8
# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
import logging
import itertools
import json
from openquake.baselib import general, hdf5
from openquake.hazardlib import geo, site, scalerel
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo.mesh import (
    Mesh, RectangularMesh, surface_to_arrays)
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.geodetic import geodetic_distance
from openquake.hazardlib.near_fault import (
    get_plane_equation, projection_pp, directp, average_s_rad, isochone_ratio)
from openquake.hazardlib.geo.surface import BaseSurface, PlanarSurface

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
I64 = numpy.int64
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16
TWO24 = 2 ** 24
TWO30 = 2 ** 30
TWO32 = 2 ** 32

MSR = scalerel._get_available_class(scalerel.BaseMSR)

pmf_dt = numpy.dtype([
    ('prob', float),
    ('occ', U32)])

events_dt = numpy.dtype([
    ('id', U32),
    ('rup_id', I64),
    ('rlz_id', U16)])

rup_dt = numpy.dtype([
    ('seed', U32),
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

rupture_dt = numpy.dtype([
    ('id', I64),
    ('seed', I64),
    ('source_id', U32),
    ('trt_smr', U32),
    ('code', U8),
    ('n_occ', U32),
    ('mag', F32),
    ('rake', F32),
    ('occurrence_rate', F32),
    ('minlon', F32),
    ('minlat', F32),
    ('maxlon', F32),
    ('maxlat', F32),
    ('hypo', (F32, 3)),
    ('geom_id', U32),
    ('nsites', U32),
    ('e0', U32),
    ('model', '<S3')])

code2cls = {}


def to_csv_array(ebruptures):
    """
    :param ebruptures: a list of EBRuptures
    :returns: an array suitable for serialization in CSV
    """
    if not code2cls:
        code2cls.update(BaseRupture.init())
    arr = numpy.zeros(len(ebruptures), rup_dt)
    for rec, ebr in zip(arr, ebruptures):
        rup = ebr.rupture
        # s0=number of multi surfaces, s1=number of rows, s2=number of columns
        arrays = surface_to_arrays(rup.surface)  # shape (s0, 3, s1, s2)
        rec['seed'] = ebr.seed
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


def to_arrays(geom):
    """
    :param geom: an array [num_surfaces, shape_y, shape_z ..., coords]
    :returns: a list of num_surfaces arrays with shape (3, shape_y, shape_z)
    """
    arrays = []
    num_surfaces = int(geom[0])
    start = num_surfaces * 2 + 1
    for i in range(1, 2 * num_surfaces, 2):
        s1, s2 = int(geom[i]), int(geom[i + 1])
        size = s1 * s2 * 3
        array = geom[start:start + size].reshape(3, s1, s2)
        arrays.append(array)
        start += size
    return arrays


def get_ebr(rec, geom, trt):
    """
    Convert a rupture record plus geometry into an EBRupture instance
    """
    # rec: a dictionary or a record
    # geom: if any, an array of floats32 convertible into a mesh
    # NB: not implemented: rupture_slip_direction
    if not code2cls:
        code2cls.update(BaseRupture.init())

    # build surface
    arrays = to_arrays(geom)
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
            # assume KiteSurfaces
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
    rupture.seed = rec['seed']
    rupture.surface = surface
    rupture.mag = rec['mag']
    rupture.rake = rec['rake']
    rupture.hypocenter = geo.Point(*rec['hypo'])
    rupture.occurrence_rate = rec['occurrence_rate']
    try:
        rupture.probs_occur = rec['probs_occur']
    except (KeyError, ValueError):  # rec can be a numpy record
        pass
    rupture.tectonic_region_type = trt
    rupture.multiplicity = rec['n_occ']

    # build EBRupture
    ebr = EBRupture(rupture, rec['source_id'], rec['trt_smr'],
                    rec['n_occ'], rec['id'] % TWO30, rec['e0'])
    ebr.seed = rec['seed']
    return ebr


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
        self.ruid = None

    @property
    def hypo_depth(self):
        """Returns the hypocentral depth"""
        return self.hypocenter.z

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

    def sample_number_of_occurrences(self, n, rng):
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
        if weight is not None:
            self.weight = weight

    def sample_number_of_occurrences(self, n, rng):
        """
        See :meth:`superclass method
        <.rupture.BaseRupture.sample_number_of_occurrences>`
        for spec of input and result values.

        Uses 'Inverse Transform Sampling' method.
        """
        # compute cdf from pmf
        cdf = numpy.cumsum(self.probs_occur)
        n_occ = numpy.digitize(rng.random(n), cdf)
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

    def sample_number_of_occurrences(self, n, rng):
        """
        Draw a random sample from the distribution and return a number
        of events to occur as an array of integers of size n.

        Uses :meth:
        `openquake.hazardlib.tom.PoissonTOM.sample_number_of_occurrences`
        of an assigned temporal occurrence model.
        """
        r = self.occurrence_rate * self.temporal_occurrence_model.time_span
        return rng.poisson(r, n)

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
    """
    def __init__(self, hypocenter):
        self.hypocenter = hypocenter

    def get_strike(self):
        return 0

    def get_dip(self):
        return 0

    def get_top_edge_depth(self):
        return self.hypocenter.depth

    def get_width(self):
        return 0

    def get_closest_points(self, mesh):
        """
        :returns: N times the hypocenter if N is the number of points
        """
        N = len(mesh)
        lons = numpy.full(N, self.hypocenter.x)
        lats = numpy.full(N, self.hypocenter.y)
        deps = numpy.full(N, self.hypocenter.z)
        return Mesh(lons, lats, deps)

    def get_min_distance(self, mesh):
        """
        :returns: the distance from the hypocenter to the mesh
        """
        return self.hypocenter.distance_to_mesh(mesh).min()

    def __bool__(self):
        return False


class PointRupture(ParametricProbabilisticRupture):
    """
    A rupture coming from a far away PointSource, so that the finite
    size effects can be neglected.
    """
    def __init__(self, mag, tectonic_region_type, hypocenter,
                 occurrence_rate, temporal_occurrence_model, zbot=0):
        self.mag = mag
        self.tectonic_region_type = tectonic_region_type
        self.hypocenter = hypocenter
        self.occurrence_rate = occurrence_rate
        self.temporal_occurrence_model = temporal_occurrence_model
        self.surface = PointSurface(hypocenter)
        self.rake = 0
        self.dip = 0
        self.strike = 0
        self.zbot = zbot  # bottom edge depth, used in Campbell-Bozorgnia


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

    :param rupid: rupture ID
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
    object.

    :param rupture: the underlying rupture
    :param str source_id: ID of the source that generated the rupture
    :param int trt_smr: an integer describing TRT and source model realization
    :param int n_occ: number of occurrences of the rupture
    :param int e0: initial event ID (default 0)
    :param bool scenario: True for scenario ruptures, default False
    """
    seed = 'NA'  # set by the engine

    def __init__(self, rupture, source_id=0, trt_smr=0, n_occ=1, id=0, e0=0, seed=42):
        self.rupture = rupture
        self.source_id = source_id
        self.trt_smr = trt_smr
        self.n_occ = n_occ
        self.id = source_id * TWO30 + id
        self.e0 = e0
        self.seed = seed

    @property
    def tectonic_region_type(self):
        return self.rupture.tectonic_region_type

    @property
    def mag(self):
        return self.rupture.mag

    def get_eids(self):
        """
        :returns: an array of event IDs
        """
        return numpy.arange(self.n_occ, dtype=U32)

    def __repr__(self):
        return '<%s %d[%d]>' % (
            self.__class__.__name__, self.id, self.n_occ)


def get_eid_rlz(rec, rlzs, scenario):
    """
    :param rlzs: an array of realization indices
    :param scenario: if true distribute the rlzs evenly else randomly
    :returns: two arrays (eid, rlz)
    """
    e0 = rec['e0']
    n = rec['n_occ']
    eid = numpy.arange(e0, e0 + n, dtype=U32)
    if scenario:
        # the rlzs are distributed evenly
        rlz = rlzs[numpy.arange(rec['n_occ']) // (n // len(rlzs))]
    else:
        # event_based: the rlzs are distributed randomly
        rlz = general.random_choice(rlzs, n, 0, rec['seed'])
    return eid, rlz


def get_events(recs, rlzs, scenario):
    """
    Build the associations event_id -> rlz_id for each rup_id.

    :returns: a structured array with fields ('id', 'rup_id', 'rlz_id')
    """
    n_occ = sum(rec['n_occ'] for rec in recs)
    out = numpy.zeros(n_occ, events_dt)
    start = 0
    for rec in recs:
        n = rec['n_occ']
        stop = start + n
        slc = out[start:stop]
        eid, rlz = get_eid_rlz(rec, rlzs, scenario)
        slc['id'] = eid
        slc['rlz_id'] = rlz
        slc['rup_id'] = rec['id']
        start = stop
    return out


class RuptureProxy(object):
    """
    A proxy for a rupture record.

    :param rec: a record with the rupture parameters
    """
    def __init__(self, rec):
        self.rec = rec

    def __getitem__(self, name):
        return self.rec[name]

    # NB: requires the .geom attribute to be set
    def to_ebr(self, trt):
        """
        :returns: EBRupture instance associated to the underlying rupture
        """
        return get_ebr(self.rec, self.geom, trt)

    def __repr__(self):
        return '<%s#%d[%s], w=%d>' % (
            self.__class__.__name__, self['id'],
            self['source_id'], self['n_occ'])


def get_ruptures(fname_csv):
    """
    Read ruptures in CSV format and return an ArrayWrapper.

    :param fname_csv: path to the CSV file
    """
    if not BaseRupture._code:
        BaseRupture.init()  # initialize rupture codes
    code = BaseRupture.str2code
    aw = hdf5.read_csv(fname_csv, {n: rup_dt[n] for n in rup_dt.names})
    rups = []
    geoms = []
    n_occ = 1
    for u, row in enumerate(aw.array):
        hypo = row['lon'], row['lat'], row['dep']
        dic = json.loads(row['extra'])
        meshes = [F32(m) for m in json.loads(row['mesh'])]  # 3D arrays
        num_surfaces = len(meshes)
        shapes = []
        points = []
        minlons = []
        maxlons = []
        minlats = []
        maxlats = []
        for mesh in meshes:
            shapes.extend(mesh.shape[1:])
            points.extend(mesh.flatten())  # lons + lats + deps
            minlons.append(mesh[0].min())
            minlats.append(mesh[1].min())
            maxlons.append(mesh[0].max())
            maxlats.append(mesh[1].max())
        rec = numpy.zeros(1, rupture_dt)[0]
        rec['seed'] = row['seed']
        rec['minlon'] = minlon = min(minlons)
        rec['minlat'] = minlat = min(minlats)
        rec['maxlon'] = maxlon = max(maxlons)
        rec['maxlat'] = maxlat = max(maxlats)
        rec['mag'] = row['mag']
        rec['hypo'] = hypo
        rate = dic.get('occurrence_rate', numpy.nan)
        trt_smr = aw.trts.index(row['trt']) * TWO24
        tup = (u, row['seed'], 0, trt_smr,
               code[row['kind']], n_occ, row['mag'], row['rake'], rate,
               minlon, minlat, maxlon, maxlat, hypo, u, 1, 0, '???')
        rups.append(tup)
        geoms.append(numpy.concatenate([[num_surfaces], shapes, points]))
    if not rups:
        return ()
    dic = dict(geom=numpy.array(geoms, object), trts=aw.trts)
    # NB: PMFs for nonparametric ruptures are missing
    return hdf5.ArrayWrapper(numpy.array(rups, rupture_dt), dic)


def fix_vertices_order(array43):
    """
    Make sure the point inside array43 are in the form top_left, top_right,
    bottom_left, bottom_right
    The convention used in the USGS format has the last two points inverted
    with respect to what is expected by OQ
    """
    top_left = array43[0]
    top_right = array43[1]
    bottom_left = array43[3]
    bottom_right = array43[2]
    return numpy.array([top_left, top_right, bottom_left, bottom_right])


def is_matrix(rows):
    """
    :returns: False if the rows have different lenghts
    """
    lens = [len(row) for row in rows]
    return len(set(lens)) == 1


def get_multiplanar(multipolygon_coords, mag, rake, trt):
    """
    :param multipolygon_coords:
       an array or list of shape (P, 5, 3) coming from geojson
    :returns: a BaseRupture with a PlanarSurface or a multiPlanarSurface
    """
    # NB: in geojson the last vertex is the same as the first, so I discard it
    # expecting shape (P, 4, 3)
    coords = numpy.array(multipolygon_coords, float)[:, :-1, :]
    P, vertices, _ = coords.shape
    if vertices != 4:
        raise ValueError('Expecting 4 vertices, got %d' % vertices)
    for p, array43 in enumerate(coords):
        coords[p] = fix_vertices_order(array43)
    if P == 1:
        surf = PlanarSurface.from_array(coords[0, :, :].T)
    else:
        surf = geo.MultiSurface([geo.PlanarSurface.from_array(array.T)
                                 for array in coords])
    rup = BaseRupture(mag, rake, trt, surf.get_middle_point(), surf)
    rup.rup_id = 0
    return rup


def get_planar(site, msr, mag, aratio, strike, dip, rake, trt, ztor=None):
    """
    :returns: a BaseRupture with a PlanarSurface built around the site
    """
    hc = site.location
    surf = PlanarSurface.from_hypocenter(hc, msr, mag, aratio, strike, dip,
                                         rake, ztor)
    rup = BaseRupture(mag, rake, trt, hc, surf)
    rup.rup_id = 0
    vars(rup).update(vars(site))
    return rup


# use a hard-coded MSR
def _width_length(mag, rake):
    assert rake is None or -180 <= rake <= 180, rake
    if rake is None:
        # "All" case
        return 10.0 ** (-1.01 + 0.32 * mag), 10.0 ** (-2.44 + 0.59 * mag)
    elif -45 <= rake <= 45 or rake >= 135 or rake <= -135:
        # strike slip
        return 10.0 ** (-0.76 + 0.27 * mag), 10.0 ** (-2.57 + 0.62 * mag)
    elif rake > 0:
        # thrust/reverse
        return 10.0 ** (-1.61 + 0.41 * mag), 10.0 ** (-2.42 + 0.58 * mag)
    else:
        # normal
        return 10.0 ** (-1.14 + 0.35 * mag), 10.0 ** (-1.88 + 0.50 * mag)


# copied from the Input Preparation Toolkit (IPT) algorithm
def build_planar(hypocenter, mag, rake, strike=0., dip=90., trt='*'):
    """
    Build a rupture with a PlanarSurface suitable for scenario calculations
    """
    # copying the algorithm used in PlanarSurface.from_hypocenter
    # with a fixed Magnitude-Scaling Relationship
    rdip = math.radians(dip)
    rup_width, rup_length = _width_length(mag, rake)
    if rup_length > 1000.:
        logging.error(f'{rup_length=} is wrong, the hand-coded MSR is wrong, '
                      'using 1000 km instead')
        rup_length = 1000.

    # calculate the height of the rupture being projected
    # on the vertical plane:
    rup_proj_height = rup_width * math.sin(rdip)
    # and its width being projected on the horizontal one:
    rup_proj_width = rup_width * math.cos(rdip)

    # half height of the vertical component of rupture width
    # is the vertical distance between the rupture geometrical
    # center and it's upper and lower borders:
    hheight = rup_proj_height / 2.
    # calculate how much shallower the upper border of the rupture
    # is than the upper seismogenic depth:
    vshift = hheight - hypocenter.depth
    # if it is shallower (vshift > 0) than we need to move the rupture
    # by that value vertically.

    rupture_center = hypocenter
    if vshift > 0:
        # we need to move the rupture center to make the rupture plane
        # lie below the surface
        hshift = abs(vshift / math.tan(rdip))
        rupture_center = hypocenter.point_at(
            hshift, vshift, azimuth=(strike + 90) % 360)

    theta = math.degrees(
        math.atan((rup_proj_width / 2.) / (rup_length / 2.)))
    hor_dist = math.sqrt((rup_length / 2.)**2 + (rup_proj_width / 2.)**2)
    vertical_increment = rup_proj_height / 2.
    top_left = rupture_center.point_at(
        hor_dist, -vertical_increment, azimuth=(strike + 180 + theta) % 360)
    top_right = rupture_center.point_at(
        hor_dist, -vertical_increment, azimuth=(strike - theta) % 360)
    bottom_left = rupture_center.point_at(
        hor_dist, vertical_increment, azimuth=(strike + 180 - theta) % 360)
    bottom_right = rupture_center.point_at(
        hor_dist, vertical_increment, azimuth=(strike + theta) % 360)
    # print(dip, strike, top_left, top_right, bottom_left, bottom_right)
    surf = PlanarSurface(strike, dip, top_left, top_right,
                         bottom_right, bottom_left)
    rup = BaseRupture(mag, rake, trt, hypocenter, surf)
    rup.rup_id = 0
    vars(rup).update(vars(hypocenter))
    return rup


def build_planar_rupture_from_dict(rupture_dict):
    """
    Leverage the build_planar function to build a rupture with a PlanarSurface
    suitable for scenario calculations

    :param rupture_dict: a dictionary containing at least the coordinates of the
        hypocenter ('lon', 'lat' and 'dep'), the magnitude ('mag') and the 'rake'
        and, optionally, the 'trt' (default '*'), the 'strike' (default 0) and
        the 'dip' (default 90).
    :returns: a BaseRupture with a PlanarSurface built around the site
    """
    r = rupture_dict
    hypo = Point(r['lon'], r['lat'], r['dep'])
    trt = r.get('trt', '*')
    strike = r.get('strike', 0)
    dip = r.get('dip', 90)
    if not r.get('msr'):
        rup = build_planar(
            hypo, r['mag'], r['rake'],
            strike, dip, trt)
    else:
        aratio = r.get('aspect_ratio', 2.)
        msr = MSR[r['msr']]()
        rup = get_planar(
            site.Site(Point(r['lon'], r['lat'], r['dep'])), msr, r['mag'], aratio,
            strike, dip, r['rake'], trt, ztor=None)
    return rup
