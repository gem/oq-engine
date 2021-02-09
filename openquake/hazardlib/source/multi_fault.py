# The Hazard Library
# Copyright (C) 2012-2021 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.source.multi_fault`
defines :class:`MultiFaultSource`.
"""

from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.source.non_parametric import (
        NonParametricSeismicSource)


class MultiFaultSource(NonParametricSeismicSource):

    def __init__(self, source_id: str, name: str, tectonic_region_type: str,
                 sections: list, rupture_idxs: list, occurrence_probs: list,
                 magnitudes: list, rakes: list):
        """
        """
        self.sections = sections
        self.rupture_idxs = rupture_idxs
        self.prob_occ = occurrence_probs
        self.mags = magnitudes
        self.rakes = rakes
        self.trt = tectonic_region_type
        data = self._get_data()
        super().__init__(source_id, name, tectonic_region_type, data)

    def _get_data(self):
        """
        Returns the tuple required to instantiate a
        :class:`openquake.hazardlib.source.nonparametric.NonParametricSeismicSource`

        :param sections:
        :param rupture_idxs:
        :param occurrence_probabilities:
        """
        data = []
        for i, idxs in enumerate(self.rupture_idxs):
            if len(idxs) > 1:
                sfc = self.sections[idxs[0]]
            else:
                sfc = MultiSurface([self.sections[j] for j in idxs])
            hypo = self.sections[idxs[0]].get_middle_point()
            rup = BaseRupture(self.mags[i], self.rakes[i], self.trt, hypo, sfc)
            data.append([rup, self.prob_occ[i]])
        return data
