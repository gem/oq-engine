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

        Base class implementation calls the :meth:`corresponding
        <nhe.geo.mesh.Mesh.get_min_distance>` method of the
        surface's :meth:`mesh <get_mesh>`.

        Subclasses may override this method in order to make use
        of knowledge of a specific surface shape and thus perform
        better.
        """
        return self.get_mesh().get_min_distance(point)

    @abc.abstractmethod
    def get_mesh(self):
        """
        Create and return the mesh of points covering the surface.

        :returns:
            An instance of :class:`nhe.geo.mesh.Mesh`.
        """
