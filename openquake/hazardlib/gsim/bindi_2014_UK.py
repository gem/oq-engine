# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Module exports :class:`BindiEtAl2014UKcoeffMed`,
Module exports :class:`BindiEtAl2014UKcoeffHigh`,
Module exports :class:`BindiEtAl2014UKcoeffLow`,
"""

import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.bindi_2014 import BindiEtAl2014Rjb
from openquake.hazardlib.gsim.bindi_2014_UK_coeffs import COEFFS_UK_VSKAPPA

class BindiEtAl2014UKcoeffMed(BindiEtAl2014Rjb):
    """
    applies vs-kappa (med) to BindiEtAl2014Rjb
    SO FAR THIS IS UNTESTED!
    """
    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = set(('rake', 'mag'))

    #: Required distance measure is Rjb (eq. 1).
    REQUIRES_DISTANCES = set(('rjb', ))

    
    
    def __init__(self, adjustment_factor=1.0):
        super().__init__()
        self.adjustment_factor = np.log(adjustment_factor)
        
    def get_coeffs(self,imt):

        if imt.period>2.0:
            C = COEFFS_UK_VSKAPPA[SA(2.0)]
        else:
            C = COEFFS_UK_VSKAPPA[imt]

        return C

    def get_corner_frequency(self, mag):
        """
        chooses corner frequency (TD) as smaller of max period with coeff
        and TD, where TD = 10^(-1.884 - log10(D_sigma)/3 + 0.5*Mw) and
        D_sigma = 80 bars (8 MPa)
        """
        D_sigma = 80

        td = 10**(-1.884 - np.log10(D_sigma)/3 + 0.5*mag)
        
        if td<1.0:
            td = 1.0

        return td

    def get_imt(self,imt,cf):

        #bindi 2014 has a coefficients for maximum period of T=3s
        b2014_max = 3.0

        if imt.name in "SA" and imt.period>cf or imt.period>b2014_max: 
            if (cf<b2014_max):
                imt_new = SA(cf) 
            else:
                imt_new = SA(b2014_max)
        else:
            imt_new = imt

        return imt_new

    def get_mean_and_stddevs_part1(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # check if cf is less than max of the original coeffs 
        cf = self.get_corner_frequency(rup.mag)

        imt_new = self.get_imt(imt,cf)

        # extracting dictionary of coefficients specific to required
        # intensity measure type.

        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt_new, stddev_types)

        C = self.get_coeffs(imt_new)

        return mean, stddevs, C

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        mean, stddevs, C = self.get_mean_and_stddevs_part1(sites, rup, dists,
                                                   imt, stddev_types)
        
        kappa = C['k_med']

        mean += np.log(kappa)
        
        return mean, stddevs

class BindiEtAl2014UKcoeffLow(BindiEtAl2014UKcoeffMed):
    """
    applies vs-kappa (low) to BindiEtAl2014Rjb
    """
    
    def __init__(self, adjustment_factor=1.0):
        super().__init__()
        self.adjustment_factor = np.log(adjustment_factor)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        mean, stddevs, C = super().get_mean_and_stddevs_part1(sites, rup, dists,
                                                   imt, stddev_types)
        
        kappa = C['k_low']

        mean += np.log(kappa)
        
        return mean, stddevs

class BindiEtAl2014UKcoeffHigh(BindiEtAl2014UKcoeffMed):
    """
    applies vs-kappa (low) to BindiEtAl2014Rjb
    """
    
    def __init__(self, adjustment_factor=1.0):
        super().__init__()
        self.adjustment_factor = np.log(adjustment_factor)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):


        mean, stddevs, C = super().get_mean_and_stddevs_part1(sites, rup, dists,
                                                   imt, stddev_types)
        
        kappa = C['k_high']

        mean += np.log(kappa)
        
        return mean, stddevs

class BindiEtAl2014UK(BindiEtAl2014UKcoeffMed):
    """
    for the case where extrapolation is necessary but no kappa applied
    (maybe not needed)
    """
    
    def __init__(self, adjustment_factor=1.0):
        super().__init__()
        self.adjustment_factor = np.log(adjustment_factor)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):


        mean, stddevs, C = super().get_mean_and_stddevs_part1(sites, rup, dists,
                                                   imt, stddev_types)
        
        return mean, stddevs
