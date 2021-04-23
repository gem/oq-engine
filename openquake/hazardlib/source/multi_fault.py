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

import numpy as np
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.source.rupture import (
        NonParametricProbabilisticRupture)
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.source.base import BaseSeismicSource


class MultiFaultSource(BaseSeismicSource):

    code = b'X'
    MODIFICATIONS = {}

    def __init__(self, source_id: str, name: str, tectonic_region_type: str,
                 sections: list, rupture_idxs: list, occurrence_probs: list,
                 magnitudes: list, rakes: list):
        """
        """
        self.sections = sections
        self.rupture_idxs = rupture_idxs
        self.poes = occurrence_probs
        self.mags = magnitudes
        self.rakes = rakes
        self.trt = tectonic_region_type
        super().__init__(source_id, name, tectonic_region_type)

    def iter_ruptures(self, fromidx=0, untilidx=None):
        """
        :param fromidx:
        :param untilidx:
        """
        untilidx = len(self.mags) if untilidx is None else untilidx
        for i in range(fromidx, untilidx):

            idxs = self.rupture_idxs[i]
            if len(idxs) > 1:
                sfc = self.sections[idxs[0]]
            else:
                sfc = MultiSurface([self.sections[j] for j in idxs])

            rake = self.rakes[idxs[0]]
            hypo = self.sections[idxs[0]].get_middle_point()
            data = [[self.poes[i][j], j] for j in range(len(self.poes[i]))]
            pmf = PMF(data=data)
            print(">>>", data)

            yield NonParametricProbabilisticRupture(self.mags[i], rake,
                                                    self.trt, hypo, sfc, pmf)

    def count_ruptures(self):
        return len(self.mags)

    def get_min_max_mag(self):
        return np.min(self.mags), np.max(self.mags)

    def get_one_rupture(self, ses_seed, rupture_mutex):
        raise NotImplementedError()
