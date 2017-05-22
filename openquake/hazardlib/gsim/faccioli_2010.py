# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Module exports :class:`FaccioliEtAl2010`.
"""
from __future__ import division

import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g

from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.cauzzi_faccioli_2008 import CauzziFaccioli2008
from openquake.hazardlib.imt import PGA, SA


class FaccioliEtAl2010(CauzziFaccioli2008):
    """
    Implements GMPE developed by Ezio Faccioli, Aldo Bianchini and Manuela
    Villani and published as "New ground motion prediction equations for T>1 s
    and their influence on seismic hazard assessment" (Proceedings of the
    University of Tokyo Symposium on Long-Period Ground Motion and Urban
    Disaster Mitigation, March 17-18, 2010).
    This class implements the prediction equations for horizontal peak ground
    acceleration, and 5%-damped spectral acceleration - equation 2 page 2,
    plus site and faulting style terms (equations 3 and 5, page 3).
    Spectral acceleration (SA) values are obtained from displacement response
    spectrum  (DSR) values (as provided by the original equations) using the
    following formula ::

        SA = DSR * (2 * π / T) ** 2

    This class extends :class:
    `~openquake.hazardlib.gsim.cauzzi_faccioli_2008.CauzziFaccioli2008`
    because the functional form is almost identical - the only
    difference is in the third term which rather then using
    hypocentral distance, uses closest distance to the rupture and
    additionaly considers a magnitude dependence.
    """

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see table 1, page 7.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Required distance measure is rrup, equation 2, page 2.
    REQUIRES_DISTANCES = set(('rrup', ))

    def _compute_mean(self, C, mag, dists, vs30, rake, imt):
        """
        Return mean value computed using equation 2, page 2, plus site
        term and faulting style term, equations 3 and 5, page 3.
        """
        mean = (self._compute_term_1_2(C, mag) +
                self._compute_term_3(C, dists.rrup, mag) +
                self._compute_site_term(C, vs30) +
                self._compute_faulting_style_term(C, rake))

        # convert from cm/s**2 to g for SA and from m/s**2 to g for PGA,
        # and also convert from base 10 to base e.
        if isinstance(imt, PGA):
            mean = np.log((10 ** mean) / g)
        elif isinstance(imt, SA):
            mean = np.log((10 ** mean) * ((2 * np.pi / imt.period) ** 2) *
                          1e-2 / g)

        return mean

    def _compute_term_3(self, C, rrup, mag):
        """
        This computes the third term in equation 2, page 2.
        """
        return (C['a3'] *
                np.log10(rrup + C['a4'] * np.power(10, C['a5'] * mag)))

    #: Coefficient table as from table 1 page 7
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT       a1        a2        a3        a4        a5        aB        aC        aD        aN        aR        aS        sigma
    pga       -1.1800   0.5590    -1.6240   0.0180    0.4450    0.2500    0.3100    0.3300    -0.0100   0.0900    -0.0500   0.3600
    0.05      -2.9600   0.6040    -1.8780   0.0520    0.3960    0.2000    0.2100    0.1800    -0.0200   0.0800    -0.0300   0.3800
    0.10      -2.0200   0.5590    -1.8370   0.0700    0.3730    0.2600    0.2400    0.1900    0.0100    0.0800    -0.0500   0.4000
    0.20      -1.9700   0.5270    -1.5120   0.0310    0.3910    0.3000    0.4200    0.4000    0.0400    0.0500    -0.0500   0.4000
    0.30      -2.1100   0.5700    -1.4210   0.0090    0.4590    0.2300    0.4200    0.4500    0.0200    0.0300    -0.0300   0.4000
    0.40      -2.2300   0.5960    -1.3550   0.0050    0.4780    0.1900    0.4200    0.5300    0.0400    0.0100    -0.0200   0.4100
    0.50      -2.3500   0.6130    -1.2950   0.0010    0.5560    0.2000    0.4200    0.6200    0.0500    0.0000    -0.0200   0.4100
    0.60      -2.4600   0.6410    -1.2820   0.0010    0.5660    0.1900    0.4200    0.6800    0.0600    -0.0100   -0.0200   0.4100
    0.70      -2.5000   0.6640    -1.2930   0.0010    0.5800    0.1700    0.4200    0.7000    0.0700    -0.0200   -0.0200   0.4100
    0.80      -2.5700   0.6930    -1.3130   0.0020    0.5360    0.1700    0.4100    0.7200    0.0600    -0.0300   -0.0100   0.4000
    0.90      -2.6300   0.7170    -1.3340   0.0030    0.5260    0.1700    0.4200    0.7300    0.0700    -0.0400   -0.0100   0.4000
    1.00      -2.6800   0.7310    -1.3350   0.0020    0.5290    0.1700    0.4200    0.7200    0.0800    -0.0400   -0.0100   0.4000
    1.25      -2.8400   0.7670    -1.3200   0.0010    0.5810    0.1600    0.4000    0.6700    0.0900    -0.0500   -0.0100   0.4000
    1.50      -2.9500   0.8010    -1.3420   0.0020    0.5290    0.1500    0.3900    0.6300    0.0900    -0.0500   -0.0100   0.4000
    2.00      -3.0900   0.8700    -1.4240   0.0180    0.4230    0.1200    0.3400    0.5500    0.0400    -0.0400   0.0100    0.4000
    2.50      -3.1400   0.9040    -1.4540   0.0780    0.3420    0.1100    0.3100    0.5000    0.0200    -0.0300   0.0100    0.3900
    3.00      -3.2000   0.9330    -1.4700   0.2620    0.2720    0.1100    0.2900    0.4900    0.0200    -0.0200   0.0000    0.3800
    4.00      -3.4900   1.0140    -1.4960   0.3870    0.2680    0.1100    0.2700    0.4400    0.0100    -0.0300   0.0100    0.3700
    5.00      -3.7100   1.0690    -1.4970   0.5270    0.2600    0.1000    0.2400    0.3900    0.0100    -0.0500   0.0200    0.3600
    7.50      -4.1500   1.0970    -1.3200   0.4550    0.2660    0.0900    0.2200    0.3400    0.0400    -0.0900   0.0400    0.3300
    10.00     -4.2800   1.0680    -1.1870   0.2100    0.2980    0.0800    0.2000    0.3200    0.0500    -0.1100   0.0400    0.3100
    15.00     -4.1700   1.0210    -1.1430   0.0890    0.3340    0.0900    0.1900    0.3200    0.0700    -0.1100   0.0400    0.2900
    20.00     -4.0200   0.9930    -1.1670   0.0650    0.3430    0.1100    0.2100    0.3300    0.0800    -0.1100   0.0300    0.3000
    """)
