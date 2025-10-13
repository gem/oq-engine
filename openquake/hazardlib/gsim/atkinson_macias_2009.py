# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
Module exports :class:'AtkinsonMacias2009'
"""
import numpy as np
from scipy.constants import g
import copy

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.mgmpe.ba08_site_term import _get_ba08_site_term
from openquake.hazardlib.gsim.mgmpe.cb14_basin_term import _get_cb14_basin_term
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import _get_z2pt5_ref


def _get_distance_term(C, rrup, mag):
    """
    Returns the distance scaling given in Equation (4), page 1569,
    with distance adjusted by the magnitude-dependent depth scaling
    factor given in Equation (6)
    """
    r_adj = np.sqrt(rrup ** 2.0 + (mag ** 2.0 - 3.1 * mag - 14.55) ** 2.)
    return C["c1"] * np.log10(r_adj) + C["c2"] * r_adj


def _get_magnitude_term(C, mag):
    """
    Returns the magnitude scaling term provided in Equation (5)
    """
    dmag = mag - 8.0
    return C["c0"] + C["c3"] * dmag + C["c4"] * (dmag ** 2.)


class AtkinsonMacias2009(GMPE):
    """
    Implements the Subduction Interface GMPE of Atkinson & Macias (2009) for
    large interface earthquakes in the Cascadia subduction zone.
    Atkinson, G. M. and Macias, M. (2009) "Predicted Ground Motions for
    Great Interface Earthquakes in the Cascadia Subduction Zone", Bulletin
    of the Seismological Society of America, 99(3), 1552 - 1578
    """
    #: The GMPE is derived for subduction interface earthquakes in Cascadia
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are peak ground acceleration and
    #: Spectral Acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is assumed to be equivalent
    #: to the random horizontal component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RANDOM_HORIZONTAL

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No required site parameters, the GMPE is derived for B/C site
    #: conditions
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is rupture distance
    REQUIRES_DISTANCES = {'rrup'}

    def __init__(self, ba08_site_term=False,
                 cb14_basin_term=False, m9_basin_term=False):
        if cb14_basin_term or m9_basin_term:
            self.REQUIRES_SITES_PARAMETERS |= {'z2pt5'}
        if ba08_site_term:
            self.REQUIRES_SITES_PARAMETERS |= {'vs30'}
            self.REQUIRES_RUPTURE_PARAMETERS |= {'rake'}
        self.ba08_site_term = ba08_site_term
        if self.ba08_site_term:
            self.REQUIRES_DISTANCES |= {"rjb"}
        self.cb14_basin_term = cb14_basin_term
        self.m9_basin_term = m9_basin_term
        
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = (_get_magnitude_term(C, ctx.mag) +
                     _get_distance_term(C, ctx.rrup, ctx.mag))
            # Convert mean from cm/s and cm/s/s and from common logarithm to
            # natural logarithm
            ln_mean = np.log((10.0 ** (imean - 2.0)) / g)
            # Set a null site term
            fs = np.zeros(len(ln_mean))
            # Apply the ba08 site term if specified
            if self.ba08_site_term:
                fs = _get_ba08_site_term(imt, ctx) 
            # Set a null basin term
            fb = np.zeros(len(ln_mean))
            # Apply cb14 basin term if specified (-999 z2pt5
            # values will be updated within this function)
            if self.cb14_basin_term:
                fb = _get_cb14_basin_term(imt, ctx)
            # Apply m9 basin term if specified (will override
            # cb14 basin term for basin sites if T >= 1.9 s)
            if self.m9_basin_term and imt.period >= 1.9:
                # Also need to update -999 z2pt5 here so have
                # a z2pt5 for each site to ensure always applying m9
                # basin term where appropriate --> In US23 model we
                # always use in combination with CB14 basin term so
                # using this relationship here to provides consistency
                # for estimating z2pt5 from vs30
                z2pt5 = ctx.z2pt5.copy()
                mask = z2pt5 == -999 # None-measured values
                z2pt5[mask] = _get_z2pt5_ref(False, ctx.vs30[mask])
                fb[z2pt5 >= 6.0] = np.log(2.0) # Basin sites use m9 basin
            
            # Add site/basin term (if any) to mean and get sigma
            mean[m] = ln_mean + fs + fb
            sig[m] = np.log(10.0 ** C["sigma"])

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT            c0        c1          c2       c3        c4  sigma
    pga        5.0060   -1.5573   -0.000340   0.1774    0.0827   0.24
    0.050000   5.8430   -1.9391    0.000000   0.1813    0.0199   0.26
    0.063091   5.8230   -1.8889   -0.000220   0.1845    0.0160   0.26
    0.079365   5.6760   -1.7633   -0.000710   0.1784    0.0245   0.27
    0.100000   5.4900   -1.6257   -0.001150   0.1736    0.0261   0.27
    0.125000   5.2090   -1.4404   -0.001630   0.1788    0.0151   0.27
    0.158730   4.9300   -1.2671   -0.002040   0.1645    0.0301   0.27
    0.200000   4.7460   -1.1691   -0.002120   0.1593    0.0432   0.27
    0.250000   4.4720   -1.0133   -0.002340   0.1713    0.0255   0.27
    0.316456   4.3030   -0.9322   -0.002310   0.1713    0.0270   0.27
    0.400000   4.1670   -0.8854   -0.002110   0.1802    0.0258   0.27
    0.500000   3.9990   -0.8211   -0.001950   0.1870    0.0271   0.27
    0.632911   3.8590   -0.7746   -0.001790   0.2010    0.0153   0.28
    0.793651   3.7330   -0.7473   -0.001590   0.2035    0.0292   0.28
    1.000000   3.6210   -0.7376   -0.001280   0.2116    0.0328   0.29
    1.265823   3.4530   -0.6885   -0.001190   0.2417    0.0125   0.29
    1.587302   3.3930   -0.7101   -0.000890   0.2483    0.0103   0.29
    2.000000   3.2410   -0.6741   -0.000810   0.2696   -0.0064   0.30
    2.500000   3.1040   -0.6585   -0.000630   0.2990   -0.0074   0.30
    3.125000   2.9780   -0.6431   -0.000570   0.3258   -0.0103   0.30
    4.000000   2.8140   -0.6108   -0.000460   0.3490   -0.0299   0.30
    5.000000   2.6710   -0.5942   -0.000400   0.3822   -0.0417   0.32
    6.250000   2.5690   -0.6048   -0.000240   0.4324   -0.0641   0.34
    7.692308   2.4890   -0.6412   -0.000030   0.4760   -0.0629   0.35
    10.00000   2.3380   -0.6311    0.000000   0.5357   -0.0737   0.38
    """)
