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
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable


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
        Eq.1 - page 2
        """
        # Ergodic coeffs
        C = self.COEFFS[imt]

        # Get mean
        mean = (self._get_magnitude_term(C, rup.mag) +
                self._get_distance_term(C, dists) +
                self._get_adjustments(C))

        # Get stds
        stds = []

        # Get cluster region
        get_cluster_region(rup.hypocenter)

        return mean, stds

    def _get_magnitude_term(self, C, mag):
        """
        Eq.2 - page 3
        """
        if mag <= self.consts['Mh']:
            return C['b1']*(mag-consts['Mh'])
        else:
            return C['b2']*(mag-consts['Mh'])

    def _get_distance_term(self, C, mag, dists):
        """
        Eq.3 - page 3
        """
        term1 = C['c1']*(mag-C['Mref']) + C['c2']
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


def get_cluster_region(hypo):

    for key in REGIONS:
        pass


DELTA_BETWEEN = {
    
    }


consts = {'Mh': 5.0,
          'Rref': 1.0,
          'PseudoDepth': 6.0}


REGIONS = {'1': [13.37, 42.13, 14.94, 41.10, 15.23, 42.32, 13.26, 42.41,
                 13.03, 42.90, 14.81, 41.80],
           '4': [13.19, 42.36, 14.83, 41.17, 15.13, 42.38, 12.96, 42.86,
                 12.90, 43.06, 14.73, 41.85],
           '5': [13.37, 42.13, 14.94, 41.10, 15.23, 42.32, 13.26, 42.41,
                 13.03, 42.90, 14.81, 41.80]}
