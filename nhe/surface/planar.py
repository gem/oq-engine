"""
Module :mod:`nhe.surface.planar` contains :class:`PlanarSurface`.
"""
from nhe.surface.base import BaseSurface


class PlanarSurface(BaseSurface):
    """
    Planar rectangular surface with two sides parallel to the Earth surface.

    Parameters are four points defining the surface corners in clockwise
    direction starting from top left corner. Top and bottom edges
    of the polygon must be parallel to earth surface and to each other.
    """
    def __init__(self, top_left, top_right, bottom_right, bottom_left):
        assert (top_left.depth == top_right.depth
                and bottom_left.depth == bottom_right.depth), \
               "top and bottom edges must be parallel to the earth surface"
        assert abs(top_left.azimuth(top_right)
                   - bottom_left.azimuth(bottom_right)) < 1, \
               "top and bottom edges must be parallel"
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

    def get_min_distance(self, point, discretization):
        """
        Implements a numerical approach to :meth:`distance calculation
        <nhe.surface.base.BaseSurface.get_min_distance>`.
        """
        mesh = self.get_mesh(discretization)
        return min(min(point.distance(mesh_point) for mesh_point in row)
                   for row in mesh)
