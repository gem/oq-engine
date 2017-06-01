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
Module :mod:`openquake.hazardlib.source.point` defines :class:`PointSource`.
"""
import math

from openquake.hazardlib.geo import Point, geodetic
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.baselib.slots import with_slots

KM_TO_DEGREES = 0.0089932  # 1 degree == 111 km
DEGREES_TO_RAD = 0.01745329252  # 1 radians = 57.295779513 degrees


def angular_distance(km, lat):
    """Return the angular distance of two points at the given latitude"""
    return km * KM_TO_DEGREES / math.cos(lat * DEGREES_TO_RAD)


@with_slots
class PointSource(ParametricSeismicSource):
    """
    Point source typology represents seismicity on a single geographical
    location.

    :param upper_seismogenic_depth:
        Minimum depth an earthquake rupture can reach, in km.
    :param lower_seismogenic_depth:
        Maximum depth an earthquake rupture can reach, in km.
    :param location:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the seismic source.
    :param nodal_plane_distribution:
        :class:`~openquake.hazardlib.pmf.PMF` object with values
        that are instances
        of :class:`openquake.hazardlib.geo.nodalplane.NodalPlane`.
        Shows the distribution
        of probability for rupture to have the certain nodal plane.
    :param hypocenter_distribution:
        :class:`~openquake.hazardlib.pmf.PMF` with values being float
        numbers in km representing the depth of the hypocenter. Latitude
        and longitude of the hypocenter is always set to ones of ``location``.

    See also :class:`openquake.hazardlib.source.base.ParametricSeismicSource`
    for description of other parameters.

    :raises ValueError:
        If upper seismogenic depth is below lower seismogenic
        depth,  if one or more of hypocenter depth values is shallower
        than upper seismogenic depth or deeper than lower seismogenic depth.
    """
    _slots_ = ParametricSeismicSource._slots_ + '''upper_seismogenic_depth
    lower_seismogenic_depth location nodal_plane_distribution
    hypocenter_distribution
    '''.split()

    MODIFICATIONS = set(())

    RUPTURE_WEIGHT = 1 / 10.

    def __init__(self, source_id, name, tectonic_region_type,
                 mfd, rupture_mesh_spacing,
                 magnitude_scaling_relationship, rupture_aspect_ratio,
                 temporal_occurrence_model,
                 # point-specific parameters
                 upper_seismogenic_depth, lower_seismogenic_depth,
                 location, nodal_plane_distribution, hypocenter_distribution):
        super(PointSource, self).__init__(
            source_id, name, tectonic_region_type, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio,
            temporal_occurrence_model)

        if not lower_seismogenic_depth > upper_seismogenic_depth:
            raise ValueError('lower seismogenic depth must be below '
                             'upper seismogenic depth')

        if not all(upper_seismogenic_depth <= depth <= lower_seismogenic_depth
                   for (prob, depth) in hypocenter_distribution.data):
            raise ValueError('depths of all hypocenters must be in between '
                             'lower and upper seismogenic depths')

        if not upper_seismogenic_depth > geodetic.EARTH_ELEVATION:
            raise ValueError(
                "Upper seismogenic depth must be greater than the "
                "maximum elevation on Earth's surface (-8.848 km)")

        self.location = location
        self.nodal_plane_distribution = nodal_plane_distribution
        self.hypocenter_distribution = hypocenter_distribution
        self.upper_seismogenic_depth = upper_seismogenic_depth
        self.lower_seismogenic_depth = lower_seismogenic_depth
        self.max_radius = 0

    def _get_max_rupture_projection_radius(self):
        """
        Find a maximum radius of a circle on Earth surface enveloping a rupture
        produced by this source.

        :returns:
            Half of maximum rupture's diagonal surface projection.
        """
        if self.max_radius:  # already computed
            return self.max_radius

        # extract maximum magnitude
        max_mag, _rate = self.get_annual_occurrence_rates()[-1]
        for (np_prob, np) in self.nodal_plane_distribution.data:
            # compute rupture dimensions
            rup_length, rup_width = self._get_rupture_dimensions(max_mag, np)
            # compute rupture width surface projection
            rup_width = rup_width * math.cos(math.radians(np.dip))
            # the projection radius is half of the rupture diagonal
            radius = math.sqrt(rup_length ** 2 + rup_width ** 2) / 2.0
            if radius > self.max_radius:
                self.max_radius = radius
        return self.max_radius

    def get_rupture_enclosing_polygon(self, dilation=0):
        """
        Returns a circle-shaped polygon with radius equal to ``dilation`` plus
        :meth:`_get_max_rupture_projection_radius`.

        See :meth:`superclass method
        <openquake.hazardlib.source.base.BaseSeismicSource.get_rupture_enclosing_polygon>`
        for parameter and return value definition.
        """
        max_rup_radius = self._get_max_rupture_projection_radius()
        return self.location.to_polygon(max_rup_radius + dilation)

    def filter_sites_by_distance_to_source(self, integration_distance, sites):
        """
        Filter sites that are closer than maximum rupture projection radius
        plus integration distance along the great circle arc from source's
        epicenter location. Overrides :meth:`base class' method
        <openquake.hazardlib.source.base.BaseSeismicSource.filter_sites_by_distance_to_source>`
        in order to avoid using polygon.
        """
        radius = self._get_max_rupture_projection_radius()
        radius += integration_distance
        return sites.filter(self.location.closer_than(sites.mesh, radius))

    def iter_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.iter_ruptures`.

        Generate one rupture for each combination of magnitude, nodal plane
        and hypocenter depth.
        """
        return self._iter_ruptures_at_location(self.temporal_occurrence_model,
                                               self.location)

    def _iter_ruptures_at_location(self, temporal_occurrence_model, location,
                                   rate_scaling_factor=1):
        """
        The common part of :meth:
        `openquake.hazardlib.source.point.Point.iter_ruptures`
        shared between point source
        and :class:`~openquake.hazardlib.source.area.AreaSource`.

        :param temporal_occurrence_model:
            The same object as given to :meth:
            `openquake.hazardlib.source.base.BaseSeismicSource.iter_ruptures`.
        :param location:
            A :class:`~openquake.hazardlib.geo.point.Point`
            object representing the hypocenter
            location. In case of :class:`PointSource` it is the one provided
            to constructor, and for area source the location points are taken
            from polygon discretization.
        :param rate_scaling_factor:
            Positive float number to multiply occurrence rates by. It is used
            by area source to scale the occurrence rates with respect
            to number of locations. Point sources use no scaling
            (``rate_scaling_factor = 1``).
        """
        assert 0 < rate_scaling_factor
        for (mag, mag_occ_rate) in self.get_annual_occurrence_rates():
            for (np_prob, np) in self.nodal_plane_distribution.data:
                for (hc_prob, hc_depth) in self.hypocenter_distribution.data:
                    hypocenter = Point(latitude=location.latitude,
                                       longitude=location.longitude,
                                       depth=hc_depth)
                    occurrence_rate = (
                        mag_occ_rate * float(np_prob) * float(hc_prob))
                    occurrence_rate *= rate_scaling_factor
                    surface = self._get_rupture_surface(mag, np, hypocenter)
                    yield ParametricProbabilisticRupture(
                        mag, np.rake, self.tectonic_region_type, hypocenter,
                        surface, type(self),
                        occurrence_rate, self.temporal_occurrence_model
                    )

    def count_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.count_ruptures`.
        """
        return (len(self.get_annual_occurrence_rates()) *
                len(self.nodal_plane_distribution.data) *
                len(self.hypocenter_distribution.data))

    def _get_rupture_dimensions(self, mag, nodal_plane):
        """
        Calculate and return the rupture length and width
        for given magnitude ``mag`` and nodal plane.

        :param nodal_plane:
            Instance of :class:`openquake.hazardlib.geo.nodalplane.NodalPlane`.
        :returns:
            Tuple of two items: rupture length in width in km.

        The rupture area is calculated using method
        :meth:`~openquake.hazardlib.scalerel.base.BaseMSR.get_median_area`
        of source's
        magnitude-scaling relationship. In any case the returned
        dimensions multiplication is equal to that value. Than
        the area is decomposed to length and width with respect
        to source's rupture aspect ratio.

        If calculated rupture width being inclined by nodal plane's
        dip angle would not fit in between upper and lower seismogenic
        depth, the rupture width is shrunken to a maximum possible
        and rupture length is extended to preserve the same area.
        """
        area = self.magnitude_scaling_relationship.get_median_area(
            mag, nodal_plane.rake
        )
        rup_length = math.sqrt(area * self.rupture_aspect_ratio)
        rup_width = area / rup_length

        seismogenic_layer_width = (self.lower_seismogenic_depth
                                   - self.upper_seismogenic_depth)
        max_width = (seismogenic_layer_width
                     / math.sin(math.radians(nodal_plane.dip)))
        if rup_width > max_width:
            rup_width = max_width
            rup_length = area / rup_width
        return rup_length, rup_width

    def _get_rupture_surface(self, mag, nodal_plane, hypocenter):
        """
        Create and return rupture surface object with given properties.

        :param mag:
            Magnitude value, used to calculate rupture dimensions,
            see :meth:`_get_rupture_dimensions`.
        :param nodal_plane:
            Instance of :class:`openquake.hazardlib.geo.nodalplane.NodalPlane`
            describing the rupture orientation.
        :param hypocenter:
            Point representing rupture's hypocenter.
        :returns:
            Instance of :class:`~openquake.hazardlib.geo.surface.planar.PlanarSurface`.
        """
        assert self.upper_seismogenic_depth <= hypocenter.depth \
            and self.lower_seismogenic_depth >= hypocenter.depth
        rdip = math.radians(nodal_plane.dip)

        # precalculated azimuth values for horizontal-only and vertical-only
        # moves from one point to another on the plane defined by strike
        # and dip:
        azimuth_right = nodal_plane.strike
        azimuth_down = (azimuth_right + 90) % 360
        azimuth_left = (azimuth_down + 90) % 360
        azimuth_up = (azimuth_left + 90) % 360

        rup_length, rup_width = self._get_rupture_dimensions(mag, nodal_plane)
        # calculate the height of the rupture being projected
        # on the vertical plane:
        rup_proj_height = rup_width * math.sin(rdip)
        # and it's width being projected on the horizontal one:
        rup_proj_width = rup_width * math.cos(rdip)

        # half height of the vertical component of rupture width
        # is the vertical distance between the rupture geometrical
        # center and it's upper and lower borders:
        hheight = rup_proj_height / 2.
        # calculate how much shallower the upper border of the rupture
        # is than the upper seismogenic depth:
        vshift = self.upper_seismogenic_depth - hypocenter.depth + hheight
        # if it is shallower (vshift > 0) than we need to move the rupture
        # by that value vertically.
        if vshift < 0:
            # the top edge is below upper seismogenic depth. now we need
            # to check that we do not cross the lower border.
            vshift = self.lower_seismogenic_depth - hypocenter.depth - hheight
            if vshift > 0:
                # the bottom edge of the rupture is above the lower sesmogenic
                # depth. that means that we don't need to move the rupture
                # as it fits inside seismogenic layer.
                vshift = 0
            # if vshift < 0 than we need to move the rupture up by that value.

        # now we need to find the position of rupture's geometrical center.
        # in any case the hypocenter point must lie on the surface, however
        # the rupture center might be off (below or above) along the dip.
        rupture_center = hypocenter
        if vshift != 0:
            # we need to move the rupture center to make the rupture fit
            # inside the seismogenic layer.
            hshift = abs(vshift / math.tan(rdip))
            rupture_center = rupture_center.point_at(
                horizontal_distance=hshift, vertical_increment=vshift,
                azimuth=(azimuth_up if vshift < 0 else azimuth_down)
            )

        # from the rupture center we can now compute the coordinates of the
        # four coorners by moving along the diagonals of the plane. This seems
        # to be better then moving along the perimeter, because in this case
        # errors are accumulated that induce distorsions in the shape with
        # consequent raise of exceptions when creating PlanarSurface objects
        # theta is the angle between the diagonal of the surface projection
        # and the line passing through the rupture center and parallel to the
        # top and bottom edges. Theta is zero for vertical ruptures (because
        # rup_proj_width is zero)
        theta = math.degrees(
            math.atan((rup_proj_width / 2.) / (rup_length / 2.))
        )
        hor_dist = math.sqrt(
            (rup_length / 2.) ** 2 + (rup_proj_width / 2.) ** 2
        )

        left_top = rupture_center.point_at(
            horizontal_distance=hor_dist,
            vertical_increment=-rup_proj_height / 2.,
            azimuth=(nodal_plane.strike + 180 + theta) % 360
        )
        right_top = rupture_center.point_at(
            horizontal_distance=hor_dist,
            vertical_increment=-rup_proj_height / 2.,
            azimuth=(nodal_plane.strike - theta) % 360
        )
        left_bottom = rupture_center.point_at(
            horizontal_distance=hor_dist,
            vertical_increment=rup_proj_height / 2.,
            azimuth=(nodal_plane.strike + 180 - theta) % 360
        )
        right_bottom = rupture_center.point_at(
            horizontal_distance=hor_dist,
            vertical_increment=rup_proj_height / 2.,
            azimuth=(nodal_plane.strike + theta) % 360
        )

        return PlanarSurface(self.rupture_mesh_spacing, nodal_plane.strike,
                             nodal_plane.dip, left_top, right_top,
                             right_bottom, left_bottom)

    def get_bounding_box(self, maxdist):
        """
        Bounding box containing all points, enlarged by the maximum distance
        and the maximum rupture projection radius (upper limit).
        """
        lon = self.location.x
        lat = self.location.y
        maxradius = self._get_max_rupture_projection_radius()
        a1 = (maxdist + maxradius) * KM_TO_DEGREES
        a2 = angular_distance(maxdist + maxradius, lat)
        return lon - a2, lat - a1, lon + a2, lat + a1
