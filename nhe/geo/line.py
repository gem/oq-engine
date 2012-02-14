"""
Module :mod:`nhe.geo.line` defines :class:`Line`.
"""
from nhe.geo import _utils as utils


class Line(object):
    """
    This class represents a geographical line, which is basically
    a sequence of geographical points.

    A line is defined by at least one point. The surface projection
    of a line cannot intersect itself (depth dimension is neglected
    to check if a line intersects itself or not).

    :param points:
        The sequence of points defining this line.
    :type points:
        list of :class:`~nhe.geo.point.Point` instances
    """

    def __init__(self, points):
        self.points = utils.clean_points(points)

        if len(self.points) < 1:
            raise ValueError("One point needed to create a line!")

        lats = [point.latitude for point in self.points]
        lons = [point.longitude for point in self.points]
        if utils.line_intersects_itself(lons, lats):
            raise ValueError("Line intersects itself!")

    def __eq__(self, other):
        """
        >>> from nhe.geo.point import Point
        >>> points = [Point(1, 2), Point(3, 4)]; Line(points) == Line(points)
        True
        >>> Line(points) == Line(list(reversed(points)))
        False
        """
        return self.points == other.points

    def __ne__(self, other):
        """
        >>> from nhe.geo.point import Point
        >>> Line([Point(1, 2)]) != Line([Point(1, 2)])
        False
        >>> Line([Point(1, 2)]) != Line([Point(2, 1)])
        True
        """
        return not self.__eq__(other)

    def __len__(self):
        return len(self.points)

    def resample(self, section_length):
        """
        Resample this line into sections.

        The first point in the resampled line corresponds
        to the first point in the original line.

        Starting from the first point in the original line, a line
        segment is defined as the line connecting the last point in the
        resampled line and the next point in the original line.
        The line segment is then split into sections of length equal to
        ``section_length``. The resampled line is obtained
        by concatenating all sections.

        The number of sections in a line segment is calculated as follows:
        ``round(segment_length / section_length)``.

        Note that the resulting line has a length that is an exact multiple of
        ``section_length``, therefore its length is in general smaller
        or greater (depending on the rounding) than the length
        of the original line.

        For a straight line, the difference between the resulting length
        and the original length is at maximum half of the ``section_length``.
        For a curved line, the difference my be larger,
        because of corners getting cut.

        :param section_length:
            The length of the section, in km.
        :type section_length:
            float
        :returns:
            A new line resampled into sections based on the given length.
        :rtype:
            An instance of :class:`Line`
        """

        if len(self.points) < 2:
            return Line(self.points)

        resampled_points = []

        # 1. Resample the first section. 2. Loop over the remaining points
        # in the line and resample the remaining sections.
        # 3. Extend the list with the resampled points, except the first one
        # (because it's already contained in the previous set of
        # resampled points).

        resampled_points.extend(self.points[0].equally_spaced_points(
                self.points[1], section_length))

        # Skip the first point, it's already resampled
        for i in range(2, len(self.points)):
            points = resampled_points[-1].equally_spaced_points(
                    self.points[i], section_length)

            resampled_points.extend(points[1:])

        return Line(resampled_points)
