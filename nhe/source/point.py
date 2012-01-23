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
                    prob = temporal_occurrence_model.get_rate(occurrence_rate)
                    surface = self.get_rupture_surface(mag, np, hc_depth)
                    rupture = Rupture(self, mag, np.rake, hypocenter,
                                      prob, surface)
                    yield rupture

    def _get_rupture_dimensions(self, mag, nodal_plane):
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
        rdip = math.radians(nodal_plane.dip)

        azimuth_right = nodal_plane.strike
        azimuth_down = (azimuth_right + 90) % 360
        azimuth_left = (azimuth_down + 90) % 360
        azimuth_up = (azimuth_left + 90) % 360

        rup_length, rup_width = self._get_rupture_dimensions(mag, nodal_plane)
        rup_proj_height = rup_width * math.sin(rdip)
        rup_proj_width = rup_width * math.cos(rdip)

        hheight = rup_proj_height / 2
        vshift = self.upper_seismogenic_depth - hypocenter.depth + hheight
        if vshift < 0:
            vshift = self.lower_seismogenic_depth - hypocenter.depth - hheight
            if vshift > 0:
                vshift = 0
        rupture_center = hypocenter

        if vshift != 0:
            hshift = abs(vshift / math.tan(rdip))
            rupture_center = rupture_center.point_at(
                horizontal_distance=hshift, vertical_increment=vshift,
                azimuth=(azimuth_up if vshift < 0 else azimuth_down)
            )

        right_center = rupture_center.point_at(
            horizontal_distance=rup_length / 2.0,
            vertical_increment=0, azimuth=azimuth_right
        )
        right_bottom = right_center.point_at(
            horizontal_distance=rup_proj_width / 2.0,
            vertical_increment=rup_proj_height / 2.0,
            azimuth=azimuth_down
        )
        right_top = right_bottom.point_at(horizontal_distance=rup_proj_width,
                                          vertical_increment=rup_proj_height,
                                          azimuth=azimuth_up)
        left_top = right_top.point_at(horizontal_distance=rup_length,
                                      vertical_increment=0,
                                      azimuth=azimuth_left)
        left_bottom = right_bottom.point_at(horizontal_distance=rup_length,
                                            vertical_increment=0,
                                            azimuth=azimuth_left)

        return EvenlyGriddedSurface(left_top, right_top, right_bottom,
                                    left_bottom)
