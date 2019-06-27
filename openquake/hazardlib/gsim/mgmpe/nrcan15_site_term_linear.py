# The Hazard Library
# Copyright (C) 2012-2019 GEM Foundation
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
Module :mod:`openquake.hazardlib.mgmp.nrcan15_site_term` implements
:class:`~openquake.hazardlib.mgmpe.NRCan15SiteTerm`
"""

import copy
import numpy as np
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.gsim.mgmpe.nrcan15_site_term import NRCan15SiteTerm


class NRCan15SiteTermLinear(NRCan15SiteTerm):
    """
    Implements a modified GMPE class that can be used to account for local
    soil conditions in the estimation of ground motion.

    This site term issimilar in structure to the
    :class:`openquake.hazardlib.gsim.mgmpe.NRCan15SiteTerm` in the OQengine
    but uses a different scaling of the motion for values of Vs30 greater
    than 760 m/s.

    This implementation follows what suggested in
    http://www.daveboore.com/pubs_online/ab06_gmpes_programs_and_tables.pdf.

    :param gmpe_name:
        The name of a GMPE class
    """

    def BA08_AB06(self, vs30, imt, pgar):
        """
        Computes amplification factor using an approach similar to the one used
        for the 2015 Canada Buiding code. Michal Kolaj's help is acknoledged.

        :param vs30:
            an be either a scalar or a :class:`~numpy.ndarray` instance
        :param imt:
            The intensity measure type
        :param pgar:
            The value of hazard on rock (vs30=760). Can be either a scalar or
            a :class:`~numpy.ndarray` instance. Unit of measure is fractions
            of gravity acceleration.
        :return:
            A scalar or a :class:`~numpy.ndarray` instance with the
            amplification factor.
        """
        fa = np.ones_like(vs30)
        if np.isscalar(vs30):
            vs30 = np.array([vs30])
        if np.isscalar(pgar):
            pgar = np.array([pgar])
        #
        # Fixing vs30 for hard rock to 1999 m/s. Beyond this threshold the
        # motion will not be modified
        vs = copy.copy(vs30)
        vs[vs >= 2000] = 2000.
        #
        # Computing motion on rock
        idx = np.where(vs30 > 760)
        if np.size(idx) > 0:
            C2 = self.COEFFS_AB06r[imt]
            fa[idx] = 1. / 10**(np.interp(np.log10(vs[idx]),
                                          np.log10([760.0, 2000.0]),
                                          np.log10([1.0, C2['c']])))
        #
        # For values of Vs30 lower than 760 the amplification is computed
        # using the site term of Boore and Atkinson (2008)
        idx = np.where(vs < 760.)
        if np.size(idx) > 0:
            C = self.COEFFS_BA08[imt]
            nl = BooreAtkinson2008()._get_site_amplification_non_linear(
                vs[idx], pgar[idx], C)
            lin = BooreAtkinson2008()._get_site_amplification_linear(
                vs[idx], C)
            fa[idx] = np.exp(nl+lin)
        return fa

    COEFFS_AB06r = CoeffsTable(sa_damping=5, table="""\
    IMT  c
    pgv  1.230
    pga  0.891
    0.05 0.891
    0.10 1.072
    0.20 1.318
    0.30 1.380
    0.50 1.380
    1.00 1.288
    2.00 1.230
    5.00 1.148
    10.0 1.072
    """)

    COEFFS_BA08 = CoeffsTable(sa_damping=5, table="""\
    IMT     blin    b1      b2
    pgv    -0.60   -0.50   -0.06
    pga    -0.36   -0.64   -0.14
    0.010  -0.36   -0.64   -0.14
    0.020  -0.34   -0.63   -0.12
    0.030  -0.33   -0.62   -0.11
    0.040  -0.31   -0.61   -0.11
    0.050  -0.29   -0.64   -0.11
    0.060  -0.25   -0.64   -0.11
    0.075  -0.23   -0.64   -0.11
    0.090  -0.23   -0.64   -0.12
    0.100  -0.25   -0.60   -0.13
    0.120  -0.26   -0.56   -0.14
    0.150  -0.28   -0.53   -0.18
    0.170  -0.29   -0.53   -0.19
    0.200  -0.31   -0.52   -0.19
    0.240  -0.38   -0.52   -0.16
    0.250  -0.39   -0.52   -0.16
    0.300  -0.44   -0.52   -0.14
    0.360  -0.48   -0.51   -0.11
    0.400  -0.50   -0.51   -0.10
    0.460  -0.55   -0.50   -0.08
    0.500  -0.60   -0.50   -0.06
    0.600  -0.66   -0.49   -0.03
    0.750  -0.69   -0.47   -0.00
    0.850  -0.69   -0.46   -0.00
    1.000  -0.70   -0.44   -0.00
    1.500  -0.72   -0.40   -0.00
    2.000  -0.73   -0.38   -0.00
    3.000  -0.74   -0.34   -0.00
    4.000  -0.75   -0.31   -0.00
    5.000  -0.75   -0.291  -0.00
    7.500  -0.692  -0.247  -0.00
    10.00  -0.650  -0.215  -0.00
    """)
