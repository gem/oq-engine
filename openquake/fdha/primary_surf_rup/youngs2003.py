# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2024 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.fdha.primary_surf_rup.youngs2003` implements
the model of Youngs et al. (2003) in :class:`Youngs2003PrimarySR`.
"""


import numpy as np
from openquake.fdha.primary_surf_rup.base import BasePrimarySurfRup

class Youngs2003PrimarySR(BasePrimarySurfRup):
    """
    Model of Youngs et al. (2003) for the probability of surface rupture
    based on rupture mechanism and earthquake magnitude.
    """
    def get_prob(self, mag, style="all"):
        """
        :param mag: float or array-like, earthquake magnitude(s)
        :param style: string, 'all' or 'normal'
        :return: probability or array of probabilities
        """
        m = np.asarray(mag, dtype=float)
        if style == 'all':
            a, b = -12.51, 2.053
        elif style == 'normal':
            a, b = -16.02, 2.685
        else:
            raise ValueError(f"Invalid style '{style}'. Use 'all' or 'normal'.")
        fx = a + b * m
        prob = np.exp(fx) / (1.0 + np.exp(fx))
        return prob.item() if prob.shape == () else prob