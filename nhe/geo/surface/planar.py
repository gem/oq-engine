"""
Module :mod:`nhe.geo.surface.planar` contains :class:`PlanarSurface`.
"""
from nhe.geo.surface.base import BaseSurface


class PlanarSurface(BaseSurface):
    """
    Planar rectangular surface with two sides parallel to the Earth surface.

    Parameters are four points (instances of :class:`~nhe.geo.point.Point`)
    defining the surface corners in clockwise direction starting from top
    left corner. Top and bottom edges of the polygon must be parallel
    to earth surface and to each other.

    :raises ValueError:
        If either top or bottom points differ in depth or if top edge
        is not parallel to the bottom edge, or if top edge differs
        in length from the bottom one.
    """
    #: The maximum angle between top and bottom edges for them
    #: to be considered parallel, in degrees.
    ANGLE_TOLERANCE = 0.1
    #: Maximum difference between lengths of top and bottom edges
    #: in kilometers.
    LENGTH_TOLERANCE = 1e-3

    def __init__(self, top_left, top_right, bottom_right, bottom_left):
        if not (top_left.depth == top_right.depth
                and bottom_left.depth == bottom_right.depth):
            raise ValueError("top and bottom edges must be parallel "
                             "to the earth surface")

        top_azimuth = top_left.azimuth(top_right)
        bottom_azimuth = bottom_left.azimuth(bottom_right)
        azimuth_diff = abs(top_azimuth - bottom_azimuth)
        if azimuth_diff > 180:
            azimuth_diff = abs(360 - azimuth_diff)
        if not (azimuth_diff < self.ANGLE_TOLERANCE):
            raise ValueError("top and bottom edges must be parallel")

        top_length = top_left.distance(top_right)
        bottom_length = bottom_left.distance(bottom_right)
        if not abs(top_length - bottom_length) < self.LENGTH_TOLERANCE:
            raise ValueError("top and bottom edges must have "
                             "the same length")
        self.length = top_length

        # we don't need to check if left edge has the same length
        # as right one because previous checks guarantee that.
        self.width = top_left.distance(bottom_left)

        self.top_left = top_left
        self.top_right = top_right
        self.bottom_right = bottom_right
        self.bottom_left = bottom_left

    def get_mesh(self, mesh_spacing):
        """
        See :meth:`nhe.surface.base.BaseSurface.get_mesh`.
        """
        mesh = []
        l_line = self.top_left.equally_spaced_points(self.bottom_left,
                                                     mesh_spacing)
        r_line = self.top_right.equally_spaced_points(self.bottom_right,
                                                      mesh_spacing)
        for i, left in enumerate(l_line):
            right = r_line[i]
            mesh.append(left.equally_spaced_points(right, mesh_spacing))
        return mesh
