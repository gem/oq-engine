"""
Module :mod:`nhe.geo.surface.base` implements :class:`BaseSurface`.
"""
import abc


class BaseSurface(object):
    """
    Base class for surface in 3D-space.

    Subclasses must implement :meth:`get_mesh` and can (for the sake
    of performance) implement :meth:`get_min_distance`.
    """
    __metaclass__ = abc.ABCMeta

    def get_min_distance(self, point):
        """
        Compute and return the minimum distance from the surface to ``point``.

        :returns:
            Distance in km.

        Base class implementation does a numerical approach -- finds
        a minimum distance from each point of the :meth:`mesh <get_mesh>`.
        """
        return min(point.distance(mesh_point)
                   for mesh_point in self.get_mesh())

    @abc.abstractmethod
    def get_mesh(self):
        """
        Create and return the mesh of points covering the surface.

        :returns:
            An instance of :class:`nhe.geo.mesh.Mesh`.
        """
