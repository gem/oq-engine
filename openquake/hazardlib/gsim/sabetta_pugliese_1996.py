# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
Module exports :class:`AmbraseysEtAl1996`.
"""
import numpy as np
from scipy.constants import g, pi

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim import utils
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA




def _compute_magnitude(ctx, C):
    """
    Added a function that convert input magnitudes Mw into the
    type of magnitudes requested by the model. Specifically,
    it assumes M = ML for M < 5.5 and M = Ms for M >= 5.5
    (Montaldo et al., 2005)
    Function from Appendix 1 (pag. 7 and 9) of "Gruppo di Lavoro (2004). 
    Redazione della mappa di pericolosità sismica prevista dall’Ordinanza
    PCM 3274 del 20 marzo 2003. Rapporto Conclusivo per il Dipartimento 
    della Protezione Civile, INGV, Milano-Roma"
    """
    M = np.where(ctx.mag < 5.5, (ctx.mag - 1.145)/ 0.812, (ctx.mag - 1.938)/0.673)
    return C['a'] + (C['b'] * M)

def _compute_distance(ctx, C):
    return (C['c']* np.log10(np.sqrt(ctx.repi ** 2 + C['h'] ** 2)))

def _site_amplification(ctx, C):
    #site condition
    sshallow = np.zeros(len(ctx.vs30))
    sdeep = np.zeros(len(ctx.vs30))
    idx = (ctx.vs30 >= 400.0) & (ctx.vs30 < 800.0)
    sshallow[idx] = 1.0
    idx = (ctx.vs30 < 400.0)
    sdeep[idx] = 1.0
    return C['e1'] * sshallow + C['e2'] * sdeep

def _get_mechanism(ctx, C):
    #style of faulting correction as in Montale et al 2005 (Table 2)
    SS, NS, RS = utils.get_fault_type_dummy_variables(ctx)
    idx = (ctx.mag < 6)
    SS[idx] = 0
    NS[idx] = 0
    RS[idx] = 0
    Fr = np.log10(1.15)
    Fn = np.log10(0.89)
    Fss = np.log10(0.94)
    return Fr*RS + Fn*NS + Fss*SS




class SabettaPugliese1996(GMPE):
    """
    Implements GMPE developed by Sabetta, F., & Pugliese, A. (1996). 
    Estimation of response spectra and simulation of nonstationary earthquake 
    ground motions. Bulletin of the Seismological Society of America, 86(2), 337-352.
    SA are given up to 4 s.
    The regressions are developed considering the largest horizontal component
    and epicentral distance (Table 2 of Sabetta and Pugliese, 1996).
    
    GMPE implemented as adopted in MPS04 (Montaldo et al 2005)
    In this implementation, a convertion function from Mw to Ms/ML is included 
    to be consistent with the other gsims in OQ.
    """
    #: Supported tectonic region type is 'active shallow crust'

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the largest
    #: horizontal component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is magnitude.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is Repi (eq. 1).
    REQUIRES_DISTANCES = {'repi'}


    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = _compute_magnitude(ctx, C) + \
            _compute_distance(ctx, C) + \
            _site_amplification(ctx, C) + \
            _get_mechanism(ctx, C)

            # Convert units to g (only pga is already in g)
            # Sa in PSV (cm/s)
            if imt.string.startswith(('SA')):
                mean[m] = np.log((10.0 ** (imean - 2.0)) * (2*pi/imt.period) / g)
            elif imt == PGV():
                #PGV - convert in g unit and from base 10 to base e
                mean[m] = np.log((10.0 ** (imean - 2.0)) / g)
            else:
                # PGA - from base 10 to base e
                mean[m] = np.log(10.0 ** imean)
            
            # Return stddevs in terms of natural log scaling
            sig[m] = np.log(10.0 ** C['sigma'])


    #: Coefficients for PGA and SA

    COEFFS = CoeffsTable(sa_damping=5, table="""
        IMT      a      b       c       e1      e2      h       sigma
        4.0000  -2.5000 0.7250  -1.0000 0.0000  0.1000  2.6000  0.3190
        3.0303  -2.2500 0.7150  -1.0000 0.0000  0.1080  3.0000  0.3190
        2.0000  -1.9000 0.6870  -1.0000 0.0000  0.1500  3.6000  0.3190
        1.4925  -1.6470 0.6600  -1.0000 0.0100  0.1750  4.0000  0.3150
        1.0000  -1.2800 0.6120  -1.0000 0.0500  0.2080  4.4000  0.3080
        0.7519  -1.0000 0.5700  -1.0000 0.1200  0.1900  4.7000  0.3030
        0.5000  -0.5950 0.5000  -1.0000 0.2300  0.1240  5.0000  0.2900
        0.4000  -0.2810 0.4450  -1.0000 0.2220  0.0780  5.2000  0.2800
        0.3003  0.1000  0.3770  -1.0000 0.1850  0.0200  5.4000  0.2600
        0.2000  0.2960  0.3230  -1.0000 0.1610  0.0000  5.7000  0.2340
        0.1499  0.2220  0.3100  -1.0000 0.1610  0.0000  5.9000  0.2200
        0.1000  -0.0190 0.3040  -1.0000 0.1610  0.0000  6.2000  0.2080
        0.0667  -0.3120 0.3040  -1.0000 0.1610  0.0000  6.3000  0.2000
        0.0400  -0.8170 0.3300  -1.0000 0.1610  0.0000  4.7000  0.1950
        pga     -1.845  0.363   -1.0000 0.1950  0.0000  5.0000  0.1900
        pgv     -0.828  0.489   -1.0000 0.1160  0.1160  3.9000  0.2490
    """)

