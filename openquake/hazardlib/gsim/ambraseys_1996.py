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
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim import utils
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA



def _compute_magnitude(ctx, C):
    """
    Added a function that converts the input magnitudes Mw into Ms.
    Function from Appendix 1 (pag. 9) of "Gruppo di Lavoro (2004). 
    Redazione della mappa di pericolosità sismica prevista dall’Ordinanza
    PCM 3274 del 20 marzo 2003. Rapporto Conclusivo per il Dipartimento 
    della Protezione Civile, INGV, Milano-Roma"
    """
    Ms = (ctx.mag - 1.938)/0.673
    return C['c1'] + (C['c2'] * Ms)

def _compute_distance(ctx, C):
    #convertion from repi to rjb if M>6 (Montaldo et al 2005, eq. 3)
    
    R = np.where(ctx.mag >= 6, -3.5525 + (0.8845 * ctx.repi), ctx.repi)
    R = np.where(R < 0, 0, R)
    return (C['c4']* np.log10(np.sqrt(R ** 2 + C['h'] ** 2)))

def _site_amplification(ctx, C):
    #site condition
    ssa = np.zeros(len(ctx.vs30))
    sss = np.zeros(len(ctx.vs30))
    
    idx = (ctx.vs30 > 360.0) & (ctx.vs30 <= 750.0)
    ssa[idx] = 1.0
    idx = (ctx.vs30 <= 360.0)
    sss[idx] = 1.0
    
    return C['ca'] * ssa + C['cs'] * sss

def _get_mechanism(ctx, C):
    #style of faulting correction as in Montale et al 2005 (Table 2)
    SS, NS, RS = utils.get_fault_type_dummy_variables(ctx)
    
    idx = (ctx.mag < 6)
    SS[idx] = 0
    NS[idx] = 0
    RS[idx] = 0
    
    Fr = np.log10(1.13)
    Fn = np.log10(0.88)
    Fss = np.log10(0.93)
    
    return Fr*RS + Fn*NS + Fss*SS


class AmbraseysEtAl1996(GMPE):
    """
    Implements GMPE developed by Ambraseys, N. N., Simpson, K. U., & 
    Bommer, J. J. (1996). Prediction of horizontal response spectra in Europe.
    Earthquake Engineering & Structural Dynamics, 25(4), 371-400.
    SA are given up to 2 s.
    The regressions are developed considering the largest horizontal component
    
    GMPE implemented as adopted in MPS04 (Montaldo et al 2005).
    In this implementation, a convertion function from Mw to Ms is included 
    to be consistent with the other gsims in OQ. 
    """
    #: Supported tectonic region type is 'active shallow crust'

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the largest
    #: horizontal component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is Repi
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
            _site_amplification(ctx, C) +\
            _get_mechanism(ctx, C)

            # convert from base 10 to base e (already in g)
            mean[m] = np.log(10.0 ** imean)

            # Return stddevs in terms of natural log scaling
            sig[m] = np.log(10.0 ** C['sigma'])



    #: Coefficients for PGA and SA

    COEFFS = CoeffsTable(sa_damping=5, table="""
         IMT       c1      c2     h     c4     ca      cs  sigma
         pga    -1.48   0.266   3.5 -0.922  0.117   0.124   0.25
        0.10    -0.84   0.219   4.5 -0.954  0.078   0.027   0.27
        0.11    -0.86   0.221   4.5 -0.945  0.098   0.036   0.27
        0.12    -0.87   0.231   4.7 -0.960  0.111   0.052   0.27
        0.13    -0.87   0.238   5.3 -0.981  0.131   0.068   0.27
        0.14    -0.94   0.244   4.9 -0.955  0.136   0.077   0.27
        0.15    -0.98   0.247   4.7 -0.938  0.143   0.085   0.27
        0.16    -1.05   0.252   4.4 -0.907  0.152   0.101   0.27
        0.17    -1.08   0.258   4.3 -0.896  0.140   0.102   0.27
        0.18    -1.13   0.268   4.0 -0.901  0.129   0.107   0.27
        0.19    -1.19   0.278   3.9 -0.907  0.133   0.130   0.28
        0.20    -1.21   0.284   4.2 -0.922  0.135   0.142   0.27
        0.22    -1.28   0.295   4.1 -0.911  0.120   0.143   0.28
        0.24    -1.37   0.308   3.9 -0.916  0.124   0.155   0.28
        0.26    -1.40   0.318   4.3 -0.942  0.134   0.163   0.28
        0.28    -1.46   0.326   4.4 -0.946  0.134   0.158   0.29
        0.30    -1.55   0.338   4.2 -0.933  0.133   0.148   0.30
        0.32    -1.63   0.349   4.2 -0.932  0.125   0.161   0.31
        0.34    -1.65   0.351   4.4 -0.939  0.118   0.163   0.31
        0.36    -1.69   0.354   4.5 -0.936  0.124   0.160   0.31
        0.38    -1.82   0.364   3.9 -0.900  0.132   0.164   0.31
        0.40    -1.94   0.377   3.6 -0.888  0.139   0.172   0.31
        0.42    -1.99   0.384   3.7 -0.897  0.147   0.180   0.32
        0.44    -2.05   0.393   3.9 -0.908  0.153   0.187   0.32
        0.46    -2.11   0.401   3.7 -0.911  0.149   0.191   0.32
        0.48    -2.17   0.410   3.5 -0.920  0.150   0.197   0.32
        0.50    -2.25   0.420   3.3 -0.913  0.147   0.201   0.32
        0.55    -2.38   0.434   3.1 -0.911  0.134   0.203   0.32
        0.60    -2.49   0.438   2.5 -0.881  0.124   0.212   0.32
        0.65    -2.58   0.451   2.8 -0.901  0.122   0.215   0.32
        0.70    -2.67   0.463   3.1 -0.914  0.116   0.214   0.33
        0.75    -2.75   0.477   3.5 -0.942  0.113   0.212   0.32
        0.80    -2.86   0.485   3.7 -0.925  0.127   0.218   0.32
        0.85    -2.93   0.492   3.9 -0.920  0.124   0.218   0.32
        0.90    -3.03   0.502   4.0 -0.920  0.124   0.225   0.32
        0.95    -3.10   0.503   4.0 -0.892  0.121   0.217   0.32
        1.00    -3.17   0.508   4.3 -0.885  0.128   0.219   0.32
        1.10    -3.30   0.513   4.0 -0.857  0.123   0.206   0.32
        1.20    -3.38   0.513   3.6 -0.851  0.128   0.214   0.31
        1.30    -3.43   0.514   3.6 -0.848  0.115   0.200   0.31
        1.40    -3.52   0.522   3.4 -0.839  0.109   0.197   0.31
        1.50    -3.61   0.524   3.0 -0.817  0.109   0.204   0.31
        1.60    -3.68   0.520   2.5 -0.781  0.108   0.206   0.31
        1.70    -3.74   0.517   2.5 -0.759  0.105   0.206   0.31
        1.80    -3.79   0.514   2.4 -0.730  0.104   0.204   0.32
        1.90    -3.80   0.508   2.8 -0.724  0.103   0.194   0.32
        2.00    -3.79   0.503   3.2 -0.728  0.101   0.182   0.32
    """)


