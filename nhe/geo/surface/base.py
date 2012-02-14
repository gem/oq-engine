"""
Module :mod:`nhe.geo.surface.base` implements :class:`BaseSurface`.
"""
import abc


class BaseSurface(object):
    """
    Base class for surface in 3D-space.

    Subclasses must implement :meth:`_create_mesh`, :meth:`get_strike` and
    :meth:`get_dip`, and can (for the sake of performance) override
    :meth:`get_min_distance` and :meth:`get_joyner_boore_distance`.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._mesh = None

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

    def get_joyner_boore_distance(self, point):
        """
        Compute and return Joyner-Boore distance to ``point``.

        :returns:
            The closest distance between the point and the surface projection.

        Base class calls surface mesh's method
        :meth:`~nhe.geo.mesh.RectangularMesh.get_joyner_boore_distance`.
        """
        return self.get_mesh().get_joyner_boore_distance(point)

    def get_mesh(self):
        """
        Return surface's mesh.

        Uses :meth:`_create_mesh` for creating the mesh for the first time.
        All subsequent calls to :meth:`get_mesh` return the same mesh object.
        """
        if self._mesh is None:
            self._mesh = self._create_mesh()
        return self._mesh

    @abc.abstractmethod
    def _create_mesh(self):
        """
        Create and return the mesh of points covering the surface.

        :returns:
            An instance of :class:`nhe.geo.mesh.RectangularMesh`.
        """

    @abc.abstractmethod
    def get_strike(self):
        """
        Return surface's strike as decimal degrees in a range ``[0, 360)``.

        The actual definition of the strike might depend on surface geometry.
        """

    @abc.abstractmethod
    def get_dip(self):
        """
        Return surface's dip as decimal degrees in a range ``(0, 90]``.

        The actual definition of the dip might depend on surface geometry.
        """
