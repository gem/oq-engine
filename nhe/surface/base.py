"""
Module :mod:`nhe.surface.base` implements :class:`BaseSurface`.
"""
import abc


class BaseSurface(object):
    """
    Base class for earthquake rupture surface.

    Subclasses must implement :meth:`get_mesh` and can (for the sake
    of performance) implement :meth:`get_min_distance`.
    """
    __metaclass__ = abc.ABCMeta

    def get_min_distance(self, point, discretization):
        """
        Compute and return the minimum distance from the surface to ``point``.

        :param discretization:
            The minimum precision the calculation should be done with.
            This represents the maximum mesh spacing for the case when
            the actual implementation uses a numerical approach (like
            creating the :meth:`mesh <get_mesh>` and computing distances
            to each point of the mesh). The value is in km. The actual
            implementation is free to provide the result with higher
            precision or ignore that parameter's value altogether
            if perfectly correct calculation is possible and feasible.
        :returns:
            Distance in km.

        Base class implementation does a numerical approach -- finds
        a minimum distance from each point of the :meth:`mesh <get_mesh>`.
        """
        return min(min(point.distance(mesh_point) for mesh_point in row)
                   for row in self.get_mesh(discretization))

    @abc.abstractmethod
    def get_mesh(self, mesh_spacing):
        """
        Create and return the mesh of points covering the surface.

        :param mesh_spacing:
            The maximum distance between two adjacent points in the mesh
            in both horizontal and vertical directions, in km.
        :returns:
            A list of lists of points. First list representing the first
            "row" of points (the top edge) and so on.
        """
