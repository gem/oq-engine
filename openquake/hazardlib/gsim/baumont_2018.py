# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
Module exports :

class:`BaumontEtAl2018High2210IAVGDC30n7`

"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import MMI


class BaumontEtAl2018High2210IAVGDC30n7(GMPE):
    """
    Implements "Intensity predictive attenuation models
    calibrated in Mw for metropolitan France
    David Baumont,Kévin Manchuel,Paola Traversa, Christophe Durouchoux,
    Emmanuelle Nayman, Gabriele Ameri
    Bull Earthquake Eng (2018) 16:2285–2310
    https://doi.org/10.1007/s10518-018-0344-6
    functional given on page 2293 for Rhypo
    This class implements the model
    Intensity Model:Q Domain:Depth Control:DBMI Data Selection
    given in Table 1:
    Intensity model:
    (1) Regional geometrical spreading,
    (2) Geometrical spreading and regional intrinsic attenuation
    Q-domain:(0) France, (1) France and Italy, (2) Q-regions (France and Italy)
    Depth control:
    (0) Depth fixed,
    (1) Depth free within the plausible range defined in Table 3,
    (2) Similar to depth case # 1 but with Io constraints
    DBMI data selection:     (0) IDP(MCS) <= VII, (1) IDP(MCS) <= VI
    Min Dc (km):  30, 50
    Min # intensity classes: 3,5,7
    Intensity metrics: IAVG, RAVG, ROBS, RP50, RP84
    ################################
    the model implmented is [2.2.1.0]
    for high attenuation, MinDc=30 and Min = 7 int. classes
    and IAVG as the base classes

    Implemented by laurentiu.danciu@sed.ethz.ch
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {MMI}

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    REQUIRES_SITES_PARAMETERS = set()

    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    REQUIRES_DISTANCES = {'rhypo'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type
        C = self.COEFFS[imt]

        mean = self._compute_mean(C, rup, dists)
        stddevs = self._get_stddevs(C, stddev_types, num_sites=dists.rhypo.shape)
        return mean, stddevs

    def _compute_mean(self, C, rup, dists):
        """
        Compute mean value defined by equation on 2293
        """
        term01 = C['beta'] * (np.log10(dists.rhypo))
        term02 = C['gamma'] * dists.rhypo
        mean = C['c1'] + C['c2'] * rup.mag + term01 + term02

        return mean

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return total standard deviation.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            stddevs.append(np.sqrt(C['be']**2+C['we']**2) + np.zeros(num_sites))

        return stddevs

    #: Coefficient table constructed from the electronic suplements of the
    #: original paper
    COEFFS = CoeffsTable(table="""\
    IMT           c1       c2      beta        gamma      we      be
    MMI        2.400    1.301    -2.544    -5.14E-03   0.227   0.373
     """)
