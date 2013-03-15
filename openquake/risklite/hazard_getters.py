#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2010-2013, GEM foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


class MissingHazard(Exception):
    """
    Hazard getters with a maximum distance filter will throw this exception
    when it is impossible to find a hazard for the given site within the
    maximum range.
    """


class HazardGetter(object):
    """
    Hazard getter working on a list of rows of the form[(lon, lat, gmvs), ...]
    The implementation here is simple but slow, since it computes the distances
    from every site in the grid for each point. It is useful for small dataset
    and for comparison purposes, to check with alternative algorithms.
    """
    def __init__(self, gmf):
        self.gmf = gmf
        self.closest = {}

    def __call__(self, point):
        try:
            return self.closest[point]
        except KeyError:
            self.closest[point] = c = self._get_closest(point)
            return c

    def _get_closest(self, point):
        x, y = point
        min_dist = 1000000  # a big number, will be replaced by min_dist
        min_idx = 0
        for i, row in enumerate(self.gmf):
            dx = x - row[0]
            dy = y - row[1]
            dsquare = dx * dx + dy * dy
            # NOTE: one may wonder why I am not computing the distance by using
            # the correct formula. The answer is that it is not important to
            # have the correct absolute distance. It is important to have a
            # distance indicator which correctly gives the closest point.
            # Vitor was using the pytagoric distance, which is correct enough
            # in risk computation, remember that there is a maximum distance
            # filter of few kilometers. For performance reasons I have
            # also removed the square root. You can certainly consider
            # patological situations (i.e. the North pole) but keep
            # in mind that this hazard getter will be thrown away soon
            # and replaced with a grid-based hazard getter or something else
            if dsquare < min_dist:
                min_dist = dsquare
                min_idx = i
        return self.gmf[min_idx][-1]  # the gmvs array
