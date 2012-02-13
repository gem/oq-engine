"""
Module :mod:`nhe.geo.surface.planar` contains :class:`PlanarSurface`.
"""
from nhe.geo.surface.base import BaseSurface
from nhe.geo.mesh import Mesh
from nhe.geo.nodalplane import NodalPlane


class PlanarSurface(BaseSurface):
    """
    Planar rectangular surface with two sides parallel to the Earth surface.

    :param mesh_spacing:
        The desired distance between two adjacent points in the surface mesh
        in both horizontal and vertical directions, in km.
    :param strike:
        Strike of the surface is the azimuth from ``top_left`` to ``top_right``
        points.
    :param dip:
        Dip is the angle between the surface itself and the earth surface.

    Other parameters are points (instances of :class:`~nhe.geo.point.Point`)
    defining the surface corners in clockwise direction starting from top
    left corner. Top and bottom edges of the polygon must be parallel
    to earth surface and to each other.

    See :class:`~nhe.geo.nodalplane.NodalPlane` for more detailed definition
    of ``strike`` and ``dip``. Note that these parameters are supposed
    to match the factual surface geometry (defined by corner points), but
    this is not enforced or even checked.

    :raises ValueError:
        If either top or bottom points differ in depth or if top edge
        is not parallel to the bottom edge, if top edge differs in length
        from the bottom one, or if mesh spacing is not positive.
    """
    #: The maximum angle between top and bottom edges for them
    #: to be considered parallel, in degrees.
    ANGLE_TOLERANCE = 0.1
    #: Maximum difference between lengths of top and bottom edges
    #: in kilometers.
    LENGTH_TOLERANCE = 1e-3

    def __init__(self, mesh_spacing, strike, dip,
                 top_left, top_right, bottom_right, bottom_left):
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

        if not mesh_spacing > 0:
            raise ValueError("mesh spacing must be positive")
        self.mesh_spacing = mesh_spacing

        NodalPlane.check_dip(dip)
        NodalPlane.check_strike(strike)
        self.dip = dip
        self.strike = strike

        # we don't need to check if left edge has the same length
        # as right one because previous checks guarantee that.
        self.width = top_left.distance(bottom_left)

        self.top_left = top_left
        self.top_right = top_right
        self.bottom_right = bottom_right
        self.bottom_left = bottom_left

    def get_mesh(self):
        """
        See :meth:`nhe.surface.base.BaseSurface.get_mesh`.
        """
        points = []
        l_line = self.top_left.equally_spaced_points(self.bottom_left,
                                                     self.mesh_spacing)
        r_line = self.top_right.equally_spaced_points(self.bottom_right,
                                                      self.mesh_spacing)
        for i, left in enumerate(l_line):
            right = r_line[i]
            points.extend(left.equally_spaced_points(right, self.mesh_spacing))
        return Mesh.from_points_list(points)

    def get_strike(self):
        """
        Return strike value that was provided to the constructor.
        """
        return self.strike

    def get_dip(self):
        """
        Return dip value that was provided to the constructor.
        """
        return self.dip
