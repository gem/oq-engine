"""
Module :mod:`nhe.source.point` defines :class:`PointSource`.
"""
import math

from nhe.common.geo import Point
from nhe.source.base import SeismicSource, SourceError
from nhe.source.rupture import Rupture, EvenlyGriddedSurface


class PointSource(SeismicSource):
    """
    Point source typology represents seismicity on a single geographical
    location.
    """
    def __init__(self, source_id, name, trt, mfd,
                 location, nodal_plane_distribution, hypocenter_distribution,
                 upper_seismogenic_depth, lower_seismogenic_depth,
                 magnitude_scaling_relationship, rupture_aspect_ratio):
        super(PointSource, self).__init__(source_id, name, trt, mfd)

        if upper_seismogenic_depth < 0:
            raise SourceError('upper seismogenic depth must be non-negative')

        if lower_seismogenic_depth < upper_seismogenic_depth:
            raise SourceError('lower seismogenic depth must be below '
                              'upper seismogenic depth')

        if not all(upper_seismogenic_depth <= depth <= lower_seismogenic_depth
                   for (prob, depth) in hypocenter_distribution.data):
            raise SourceError('depths of all hypocenters must be in between '
                              'lower and upper seismogenic depths')

        if not rupture_aspect_ratio > 0:
            raise SourceError('rupture aspect ratio must be positive')

        self.location = location
        self.nodal_plane_distribution = nodal_plane_distribution
        self.hypocenter_distribution = hypocenter_distribution
        self.upper_seismogenic_depth = upper_seismogenic_depth
        self.lower_seismogenic_depth = lower_seismogenic_depth
        self.magnitude_scaling_relationship = magnitude_scaling_relationship
        self.rupture_aspect_ratio = rupture_aspect_ratio

    def iter_ruptures(self, temporal_occurrence_model):
        for (mag, mag_occ_rate) in self.mfd.get_annual_occurrence_rates():
            for (np_prob, np) in self.nodal_plane_distribution.data:
                for (hc_prob, hc_depth) in self.hypocenter_distribution.data:
                    hypocenter = Point(latitude=self.location.latitude,
                                       longitude=self.location.longitude,
                                       depth=hc_depth)
                    occurrence_rate = mag_occ_rate * np_prob * hc_prob
                    probability = temporal_occurrence_model.get_probability(
                        occurrence_rate
                    )
                    surface = self.get_rupture_surface(mag, np, hypocenter)
                    rupture = Rupture(self, mag, np.rake, hypocenter,
                                      probability, surface)
                    yield rupture

    def _get_rupture_dimensions(self, mag, nodal_plane):
        """
        Calculate and return the rupture length and width
        for given magnitude ``mag`` and nodal plane.

        :param nodal_plane:
            Instance of :class:`nhe.common.nodalplane.NodalPlane`.
        :returns:
            Tuple of two items: rupture length in width in km.

        The rupture area is calculated using method
        :meth:`~nhe.msr.base.BaseMSR.get_median_area` of source's
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

    def get_rupture_surface(self, mag, nodal_plane, hypocenter):
        """
        Create and return rupture surface object with given properties.

        :param mag:
            Magnitude value, used to calculate rupture dimensions,
            see :meth:`_get_rupture_dimensions`.
        :param nodal_plane:
            Instance of :class:`nhe.common.nodalplane.NodalPlane`
            describing the rupture orientation.
        :param hypocenter:
            Point representing rupture's hypocenter.
        :returns:
            Instance of :class:`nhe.source.rupture.EvenlyGriddedSurface`.
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
        hheight = rup_proj_height / 2
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

        # now we can find four corner points of the rupture rectangle.
        # we find the point that is on the same depth than the rupture
        # center but lies on the right border of its surface:
        right_center = rupture_center.point_at(
            horizontal_distance=rup_length / 2.0,
            vertical_increment=0, azimuth=azimuth_right
        )
        # than we get the right bottom corner:
        right_bottom = right_center.point_at(
            horizontal_distance=rup_proj_width / 2.0,
            vertical_increment=rup_proj_height / 2.0,
            azimuth=azimuth_down
        )
        # and other three points can be easily found by stepping from
        # already known points horizontally only by rupture length
        # (to get to left point from right one) or horizontally and
        # vertically (to get to top edge from bottom).
        right_top = right_bottom.point_at(horizontal_distance=rup_proj_width,
                                          vertical_increment=-rup_proj_height,
                                          azimuth=azimuth_up)
        left_top = right_top.point_at(horizontal_distance=rup_length,
                                      vertical_increment=0,
                                      azimuth=azimuth_left)
        left_bottom = right_bottom.point_at(horizontal_distance=rup_length,
                                            vertical_increment=0,
                                            azimuth=azimuth_left)

        return EvenlyGriddedSurface(left_top, right_top, right_bottom,
                                    left_bottom, rup_length, rup_width)
