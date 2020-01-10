# coding: utf-8
# The Hazard Library
# Copyright (C) 2012-2019 GEM Foundation
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
import collections
import toml
from openquake.baselib import general
from openquake.baselib.slots import with_slots
from openquake.hazardlib import geo, contexts
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo.mesh import (
    Mesh, RectangularMesh, surface_to_array)
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.geodetic import geodetic_distance
from openquake.hazardlib.near_fault import (
    get_plane_equation, projection_pp, directp, average_s_rad, isochone_ratio)
from openquake.hazardlib.geo.surface.base import BaseSurface

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
TWO16 = 2 ** 16
TWO32 = 2 ** 32
pmf_dt = numpy.dtype([('prob', float), ('occ', U32)])
events_dt = numpy.dtype([('id', U32), ('rup_id', U32), ('rlz_id', U16)])
code2cls = {}


def get_rupture(dic, geom=None, trt=None):
    """
    :param dic: a dictionary or a record
    :param geom: if any, an array with fields lon, lat, depth
    :returns: a rupture instance
    """
    if not code2cls:
        code2cls.update(BaseRupture.init())
    if geom is None:
        lons = dic['lons']
        mesh = numpy.zeros((3, len(lons), len(lons[0])), F32)
        mesh[0] = dic['lons']
        mesh[1] = dic['lats']
        mesh[2] = dic['depths']
    else:
        mesh = numpy.zeros((3,) + geom.shape, F32)
        mesh[0] = geom['lon']
        mesh[1] = geom['lat']
        mesh[2] = geom['depth']
    rupture_cls, surface_cls = code2cls[dic['code']]
    rupture = object.__new__(rupture_cls)
    rupture.rup_id = dic['serial']
    rupture.surface = object.__new__(surface_cls)
    rupture.mag = dic['mag']
    rupture.rake = dic['rake']
    rupture.hypocenter = geo.Point(*dic['hypo'])
    rupture.occurrence_rate = dic['occurrence_rate']
    rupture.tectonic_region_type = trt or dic['trt']
    if surface_cls is geo.PlanarSurface:
        rupture.surface = geo.PlanarSurface.from_array(
            mesh[:, 0, :])
    elif surface_cls is geo.MultiSurface:
        # mesh has shape (3, n, 4)
        rupture.surface.__init__([
            geo.PlanarSurface.from_array(mesh[:, i, :])
            for i in range(mesh.shape[1])])
    elif surface_cls is geo.GriddedSurface:
        # fault surface, strike and dip will be computed
        rupture.surface.strike = rupture.surface.dip = None
        rupture.surface.mesh = Mesh(*mesh)
    else:
        # fault surface, strike and dip will be computed
        rupture.surface.strike = rupture.surface.dip = None
        rupture.surface.__init__(RectangularMesh(*mesh))
    return rupture


def from_toml(toml_str):
    """
    :param toml_str: a string in TOML format
    :returns: a rupture instance
    """
    return get_rupture(toml.loads(toml_str))


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
            dic[k] = [[float5(y) for y in x] for x in v]


def to_toml(rup):
    """
    :param rup: a rupture instance
    :returns: a TOML string
    """
    return toml.dumps(rup.todict())


def to_checksum(cls1, cls2):
    """
    Convert a pair of classes into a numeric code (uint8)
    """
    names = '%s,%s' % (cls1.__name__, cls2.__name__)
    return sum(map(ord, names)) % 256


@with_slots
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
    _slots_ = '''mag rake tectonic_region_type hypocenter surface
    rupture_slip_direction weight'''.split()
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
        rupture_classes = [BaseRupture] + list(get_subclasses(BaseRupture))
        surface_classes = list(get_subclasses(BaseSurface))
        code2cls = {}
        for rup, sur in itertools.product(rupture_classes, surface_classes):
            chk = to_checksum(rup, sur)
            if chk in code2cls and code2cls[chk] != (rup, sur):
                raise ValueError('Non-unique checksum %d for %s, %s' %
                                 (chk, rup, sur))
            cls._code[rup, sur] = chk
            code2cls[chk] = rup, sur
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

    get_probability_no_exceedance = (
        contexts.RuptureContext.get_probability_no_exceedance)

    def todict(self):
        """
        :returns: a representation of the rupture as a dict
        """
        if not code2cls:
            code2cls.update(BaseRupture.init())
        hypo = self.hypocenter.x, self.hypocenter.y, self.hypocenter.z
        mesh = surface_to_array(self.surface)  # shape (3, sy, sz)
        sy, sz = mesh.shape[1:]
        dic = {'serial': int(self.rup_id),
               'mag': self.mag, 'rake': self.rake, 'hypo': hypo,
               'trt': self.tectonic_region_type,
               'code': self.code, 'occurrence_rate': self.occurrence_rate,
               'rupture_cls': self.__class__.__name__,
               'surface_cls': self.surface.__class__.__name__,
               'lons': mesh[0], 'lats': mesh[1], 'depths': mesh[2]}
        _fixfloat32(dic)
        return dic

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
        self.probs_occur = numpy.array(
            [prob for (prob, occ) in pmf.data], numpy.float32)
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


@with_slots
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
    _slots_ = BaseRupture._slots_ + [
        'occurrence_rate', 'temporal_occurrence_model']

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


def get_subclasses(cls):
    """
    :returns: the subclasses of `cls`, ordered by name
    """
    for subclass in sorted(cls.__subclasses__(), key=lambda cls: cls.__name__):
        yield subclass
        for ssc in get_subclasses(subclass):
            yield ssc


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


def get_eids(rup_array, samples_by_grp, num_rlzs_by_grp):
    """
    :param rup_array: a composite array with fields rup_id, n_occ and grp_id
    :param samples_by_grp: a dictionary grp_id -> samples
    :param num_rlzs_by_grp: a dictionary grp_id -> num_rlzs
    """
    all_eids = []
    for rup in rup_array:
        grp_id = rup['grp_id']
        samples = samples_by_grp[grp_id]
        num_rlzs = num_rlzs_by_grp[grp_id]
        num_events = rup['n_occ'] if samples > 1 else rup['n_occ'] * num_rlzs
        eids = numpy.arange(num_events, dtype=U32)
        all_eids.append(eids)
    return numpy.concatenate(all_eids)


class EBRupture(object):
    """
    An event based rupture. It is a wrapper over a hazardlib rupture
    object, containing an array of site indices affected by the rupture,
    as well as the IDs of the corresponding seismic events.
    """
    def __init__(self, rupture, srcidx, grp_id, n_occ, samples=1, id=None):
        # NB: when reading an exported ruptures.xml the rup_id will be 0
        # for the first rupture; it used to be the seed instead
        assert rupture.rup_id >= 0  # sanity check
        self.rupture = rupture
        self.srcidx = srcidx
        self.grp_id = grp_id
        self.n_occ = n_occ
        self.samples = samples
        self.id = id  # id of the rupture on the DataStore, to be overridden

    @property
    def rup_id(self):
        """
        Serial number of the rupture
        """
        return self.rupture.rup_id

    def get_eids_by_rlz(self, rlzs_by_gsim):
        """
        :param n_occ: number of occurrences
        :params rlzs_by_gsim: a dictionary gsims -> rlzs array
        :param samples: number of samples in current source group
        :returns: a dictionary rlz index -> eids array
        """
        j = 0
        dic = {}
        if self.samples == 1:  # full enumeration or akin to it
            for rlzs in rlzs_by_gsim.values():
                for rlz in rlzs:
                    dic[rlz] = numpy.arange(j, j + self.n_occ, dtype=U32)
                    j += self.n_occ
        else:  # associated eids to the realizations
            rlzs = numpy.concatenate(list(rlzs_by_gsim.values()))
            assert len(rlzs) == self.samples, (len(rlzs), self.samples)
            histo = general.random_histogram(
                self.n_occ, self.samples, self.rup_id)
            for rlz, n in zip(rlzs, histo):
                dic[rlz] = numpy.arange(j, j + n, dtype=U32)
                j += n
        return dic

    def get_events(self, rlzs_by_gsim, e0=None):
        """
        :returns: an array of events with fields eid, rlz
        """
        all_eids, rlzs = [], []
        for rlz, eids in self.get_eids_by_rlz(rlzs_by_gsim).items():
            all_eids.extend(eids)
            rlzs.extend([rlz] * len(eids))
        evs = U32(all_eids) + (e0 if e0 is not None else self.e0)
        rupids = [self.rup_id] * len(evs)
        return numpy.fromiter(zip(evs, rupids, rlzs), events_dt)

    def get_eids(self, num_rlzs):
        """
        :param num_rlzs: the number of realizations for the given group
        :returns: an array of event IDs
        """
        num_events = self.n_occ if self.samples > 1 else self.n_occ * num_rlzs
        return numpy.arange(num_events, dtype=U32)

    def get_events_by_ses(self, events, num_ses):
        """
        :returns: a dictionary ses index -> events array
        """
        numpy.random.seed(self.rup_id)
        sess = numpy.random.choice(num_ses, len(events)) + 1
        events_by_ses = collections.defaultdict(list)
        for ses, event in zip(sess, events):
            events_by_ses[ses].append(event)
        for ses in events_by_ses:
            events_by_ses[ses] = numpy.array(events_by_ses[ses])
        return events_by_ses

    def get_ses_by_eid(self, rlzs_by_gsim, num_ses):
        events = self.get_events(rlzs_by_gsim)
        numpy.random.seed(self.rup_id)
        sess = numpy.random.choice(num_ses, len(events)) + 1
        return dict(zip(events['id'], sess))

    def export(self, rlzs_by_gsim, num_ses):
        """
        Yield :class:`Rupture` objects, with all the
        attributes set, suitable for export in XML format.
        """
        rupture = self.rupture
        events = self.get_events(rlzs_by_gsim, e0=TWO32 * self.rup_id)
        events_by_ses = self.get_events_by_ses(events, num_ses)
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
    weight = 1  # overridden in calculators.getters

    def __init__(self, rec, sids=None):
        self.rec = rec
        self.sids = sids

    @property
    def weight(self):
        return 1 if self.sids is None else numpy.sqrt(len(self.sids)) / 10

    def __getitem__(self, name):
        return self.rec[name]

    def to_ebr(self, geom, trt, samples):
        # not implemented: rupture_slip_direction
        rupture = get_rupture(self.rec, geom, trt)
        ebr = EBRupture(rupture, self.rec['srcidx'], self.rec['grp_id'],
                        self.rec['n_occ'], samples)
        ebr.sids = self.sids
        ebr.id = self.rec['id']
        return ebr
