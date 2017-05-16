# coding: utf-8
# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
from openquake.baselib import general
from openquake.baselib.slots import with_slots
from openquake.baselib.python3compat import with_metaclass
from openquake.hazardlib import geo
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo.mesh import RectangularMesh
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.geodetic import geodetic_distance
from openquake.hazardlib.near_fault import (get_plane_equation, projection_pp,
                                            directp, average_s_rad,
                                            isochone_ratio)
from openquake.hazardlib.source.base import BaseSeismicSource
from openquake.hazardlib.geo.surface.base import BaseSurface

pmf_dt = numpy.dtype([('prob', float), ('occ', numpy.uint32)])


@with_slots
class BaseRupture(with_metaclass(abc.ABCMeta)):
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
    :param source_typology:
        Subclass of :class:`~openquake.hazardlib.source.base.BaseSeismicSource`
        (class object, not an instance) referencing the typology
        of the source that produced this rupture.
    :param rupture_slip_direction:
        Angle describing rupture propagation direction in decimal degrees.

    :raises ValueError:
        If magnitude value is not positive, or tectonic region type is unknown.

    NB: if you want to convert the rupture into XML, you should set the
    attribute surface_nodes to an appropriate value.
    """
    _slots_ = '''mag rake tectonic_region_type hypocenter surface
    source_typology rupture_slip_direction'''.split()

    @classmethod
    def init(cls):
        """
        Initialize the class dictionaries `._code` and .`types` encoding the
        bidirectional correspondence between an integer in the range 0..255
        (the code) and a triplet of classes (rupture_class, surface_class,
        source_class). This is useful when serializing the rupture to and
        from HDF5.
        """
        source_classes = get_subclasses(BaseSeismicSource)
        rupture_classes = [BaseRupture] + list(get_subclasses(BaseRupture))
        surface_classes = get_subclasses(BaseSurface)
        code, types, n = {}, {}, 0
        for src, rup, sur in itertools.product(
                source_classes, rupture_classes, surface_classes):
            code[rup, sur, src] = n
            types[n] = rup, sur, src
            n += 1
        if n >= 256:
            raise ValueError('Too many rupture codes: %d' % n)
        cls._code = code
        cls.types = types

    def __init__(self, mag, rake, tectonic_region_type, hypocenter,
                 surface, source_typology, rupture_slip_direction=None):
        if not mag > 0:
            raise ValueError('magnitude must be positive')
        NodalPlane.check_rake(rake)
        self.tectonic_region_type = tectonic_region_type
        self.rake = rake
        self.mag = mag
        self.hypocenter = hypocenter
        self.surface = surface
        self.source_typology = source_typology
        self.rupture_slip_direction = rupture_slip_direction

    @property
    def code(self):
        """Returns the code (integer in the range 0 .. 255) of the rupture"""
        return self._code[self.__class__, self.surface.__class__,
                          self.source_typology]

    def get_probability_no_exceedance(self, poes):
        """
        Compute and return the probability that in the time span for which the
        rupture is defined, the rupture itself never generates a ground motion
        value higher than a given level at a given site.

        Such calculation is performed starting from the conditional probability
        that an occurrence of the current rupture is producing a ground motion
        value higher than the level of interest at the site of interest.
        The actual formula used for such calculation depends on the temporal
        occurrence model the rupture is associated with.
        The calculation can be performed for multiple intensity measure levels
        and multiple sites in a vectorized fashion.

        :param poes:
            2D numpy array containing conditional probabilities the the a
            rupture occurrence causes a ground shaking value exceeding a
            ground motion level at a site. First dimension represent sites,
            second dimension intensity measure levels. ``poes`` can be obtained
            calling the :meth:`method
            <openquake.hazardlib.gsim.base.GroundShakingIntensityModel.get_poes>`.
        """
        raise NotImplementedError

    def sample_number_of_occurrences(self):
        """
        Randomly sample number of occurrences from temporal occurrence model
        probability distribution.

        .. note::
            This method is using random numbers. In order to reproduce the
            same results numpy random numbers generator needs to be seeded, see
            http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.seed.html

        :returns:
            int, Number of rupture occurrences
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

          pmf = PMF([(Decimal('0.8'), 0), (Decimal('0.15'), 1),
                      Decimal('0.05', 2)])

    :raises ValueError:
        If number of ruptures in ``pmf`` do not start from 0, are not defined
        in increasing order, and if they are not defined with unit step
    """
    def __init__(self, mag, rake, tectonic_region_type, hypocenter, surface,
                 source_typology, pmf, rupture_slip_direction=None):
        occ = numpy.array([occ for (prob, occ) in pmf.data])
        if not occ[0] == 0:
            raise ValueError('minimum number of ruptures must be zero')
        if not numpy.all(numpy.sort(occ) == occ):
            raise ValueError(
                'numbers of ruptures must be defined in increasing order')
        if not numpy.all(numpy.diff(occ) == 1):
            raise ValueError(
                'numbers of ruptures must be defined with unit step')
        super(NonParametricProbabilisticRupture, self).__init__(
            mag, rake, tectonic_region_type, hypocenter, surface,
            source_typology, rupture_slip_direction)
        # an array of probabilities with sum 1
        self.pmf = numpy.array(
            [prob for (prob, occ) in pmf.data], numpy.float32)

    def get_probability_no_exceedance(self, poes):
        """
        See :meth:`superclass method
        <.rupture.BaseRupture.get_probability_no_exceedance>`
        for spec of input and result values.

        Uses the formula ::

            ∑ p(k|T) * p(X<x|rup)^k

        where ``p(k|T)`` is the probability that the rupture occurs k times in
        the time span ``T``, ``p(X<x|rup)`` is the probability that a rupture
        occurrence does not cause a ground motion exceedance, and the summation
        ``∑`` is done over the number of occurrences ``k``.

        ``p(k|T)`` is given by the constructor's parameter ``pmf``, and
        ``p(X<x|rup)`` is computed as ``1 - poes``.
        """
        # Converting from 1d to 2d
        if len(poes.shape) == 1:
            poes = numpy.reshape(poes, (-1, len(poes)))
        p_kT = self.pmf
        prob_no_exceed = numpy.array(
            [v * ((1 - poes) ** i) for i, v in enumerate(p_kT)]
        )
        prob_no_exceed = numpy.sum(prob_no_exceed, axis=0)
        return prob_no_exceed

    def sample_number_of_occurrences(self):
        """
        See :meth:`superclass method
        <.rupture.BaseRupture.sample_number_of_occurrences>`
        for spec of input and result values.

        Uses 'Inverse Transform Sampling' method.
        """
        # compute cdf from pmf
        cdf = numpy.cumsum(self.pmf)

        rn = numpy.random.random()
        [n_occ] = numpy.digitize([rn], cdf)

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
                 source_typology, occurrence_rate, temporal_occurrence_model,
                 rupture_slip_direction=None):
        if not occurrence_rate > 0:
            raise ValueError('occurrence rate must be positive')
        super(ParametricProbabilisticRupture, self).__init__(
            mag, rake, tectonic_region_type, hypocenter, surface,
            source_typology, rupture_slip_direction
        )
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
        `openquake.hazardlib.tom.PoissonTOM.get_probability_one_occurrence`
        of an assigned temporal occurrence model.
        """
        tom = self.temporal_occurrence_model
        rate = self.occurrence_rate
        return tom.get_probability_one_occurrence(rate)

    def sample_number_of_occurrences(self):
        """
        Draw a random sample from the distribution and return a number
        of events to occur.

        Uses :meth:
        `openquake.hazardlib.tom.PoissonTOM.sample_number_of_occurrences`
        of an assigned temporal occurrence model.
        """
        return self.temporal_occurrence_model.sample_number_of_occurrences(
            self.occurrence_rate
        )

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
        Get the directivity prediction value, centred DPP(cdpp) at
        a given site as described in Spudich et al. (2013), and this cdpp is
        used in Chiou and Young(2014) GMPE for near-fault directivity
        term prediction.

        :param target_site:
            A mesh object representing the location of the target sites.
        :param buf:
            A float vaule presents  the buffer distance in km to extend the
            mesh borders to.
        :param delta:
            A float vaule presents the desired distance between two adjacent
            points in mesh
        :param space:
            A float vaule presents the tolerance for the same distance of the
            sites (default 2 km)
        :returns:
            A float value presents the centreed directivity predication value
            which used in Chioud and Young(2014) GMPE for directivity term
        """

        min_lon, max_lon, max_lat, min_lat = self.surface.get_bounding_box()

        min_lon -= buf
        max_lon += buf
        min_lat -= buf
        max_lat += buf

        lons = numpy.arange(min_lon, max_lon + delta, delta)
        lats = numpy.arange(min_lat, max_lat + delta, delta)
        lons, lats = numpy.meshgrid(lons, lats)

        target_rup = self.surface.get_min_distance(target)
        mesh = RectangularMesh(lons=lons, lats=lats, depths=None)
        mesh_rup = self.surface.get_min_distance(mesh)
        target_lons = target.lons
        target_lats = target.lats
        cdpp = numpy.empty(len(target_lons))

        for iloc, (target_lon, target_lat) in enumerate(zip(target_lons,
                                                        target_lats)):

            cdpp_sites_lats = mesh.lats[(mesh_rup <= target_rup[iloc] + space)
                                        & (mesh_rup >= target_rup[iloc]
                                        - space)]
            cdpp_sites_lons = mesh.lons[(mesh_rup <= target_rup[iloc] + space)
                                        & (mesh_rup >= target_rup[iloc]
                                        - space)]

            dpp_sum = []
            dpp_target = self.get_dppvalue(Point(target_lon, target_lat))

            for lon, lat in zip(cdpp_sites_lons, cdpp_sites_lats):
                site = Point(lon, lat, 0.)
                dpp_one = self.get_dppvalue(site)
                dpp_sum.append(dpp_one)

            mean_dpp = numpy.mean(dpp_sum)
            cdpp[iloc] = dpp_target - mean_dpp

        return cdpp


def get_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield subclass
        for ssc in get_subclasses(subclass):
            yield ssc


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

    :param surface: a Surface instance
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


class ExportedRupture(object):
    """
    Simplified Rupture class with attributes rupid, events_by_ses, indices
    and others, used in export.

    :param rupid: rupture serial ID
    :param events_by_ses: dictionary ses_idx -> event records
    :param indices: site indices
    """
    def __init__(self, rupid, events_by_ses, indices=None):
        self.rupid = rupid
        self.events_by_ses = events_by_ses
        self.indices = indices


class EBRupture(object):
    """
    An event based rupture. It is a wrapper over a hazardlib rupture
    object, containing an array of site indices affected by the rupture,
    as well as the IDs of the corresponding seismic events.
    """
    def __init__(self, rupture, sids, events, grp_id, serial):
        self.rupture = rupture
        self.sids = sids
        self.events = events
        self.grp_id = grp_id
        self.serial = serial
        self.sidx = self.eidx1 = self.eidx2 = None  # to be set when needed

    @property
    def weight(self):
        """
        Weight of the EBRupture
        """
        return len(self.sids) * len(self.events)

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
        Yield :class:`Rupture` objects, with all the
        attributes set, suitable for export in XML format.
        """
        rupture = self.rupture
        events_by_ses = general.group_array(self.events, 'ses')
        new = ExportedRupture(self.serial, events_by_ses, self.sids)
        new.mesh = mesh[self.sids]
        new.multiplicity = self.multiplicity
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

    def __repr__(self):
        return '<%s %d%s>' % (
            self.__class__.__name__, self.serial, self.events['eid'])
