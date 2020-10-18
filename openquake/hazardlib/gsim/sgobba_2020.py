# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
Module :mod:`openquake.hazardlib.gsim.sgobba_2020` implements
:class:`~openquake.hazardlib.gsim.sgobba_2020.SgobbaEtAl2020`
"""

import numpy as np
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import from_string


class SgobbaEtAl2020(GMPE):
    """
    """

    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    }

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters is magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rjb
    REQUIRES_DISTANCES = {'rjb'}

    def __init__(self, calibration_event_id=None, directionality=False,
                 **kwargs):
        """
        """
        super().__init__(calibration_event_id=calibration_event_id,
                         directionality=directionality,
                         **kwargs)
        self.calibration_event_id = calibration_event_id
        self.directionality = directionality

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        """
        # Ergodic coeffs
        C = self.COEFFS[imt]

        # Get mean
        mean = (self._get_magnitude_term(C, rup.mag) +
                self._get_distance_term(C, dists) +
                self._get_adjustments(C)
                )

        # Get stds
        stds = []

        return mean, stds

    def _get_magnitude_term(self, C, mag):
        """
        """
        if mag <= self.consts['Mh']:
            return C['b1']*(mag-consts['Mh'])
        else:
            return C['b2']*(mag-consts['Mh'])

    def _get_distance_term(self, C, mag, dists):
        """
        """
        term1 = C['c1']*(mag-C['Mref'])
        tmp = np.sqrt(dists.rjb**2+consts['PseudoDepth']**2)
        term2 = np.log10(tmp/consts['Rref'])
        term3 = C['c3']*(tmp-consts['Rref'])
        return term1 * term2 + term3

    def _get_adjustments(self, sites):
        """
        """
        adj = np.zeros_like(sites.vs30)
        sig = np.zeros_like(sites.vs30)

        if self.calibration_event_id is not None:
            adj += DELTA_BETWEEN[self.calibration_event_id]
            sig += sigma
        else:
            pass

        adj = (self._get_between_adj() +
               self._get_delta_S2S_adj() +
               self._get_delta_L2L_adj() +
               self._get_delta_P2P_adj())


consts = {'Mh': 5.0,
          'Rref': 1.0,
          'PseudoDepth': 6.0}


DELTA_BETWEEN = {
    '090317011253': CoeffsTable(sa_damping=5, table="""\
                        imt             adj
                        pga      -0.32324576 """)
}
