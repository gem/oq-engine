# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:`PankowPechmann2004`.
"""
import numpy as np
from scipy.constants import g as gravity

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class PankowPechmann2004(GMPE):
    """
    Implements GMPE developed by Kris L. Pankow and James C. Pechmann
    and published as "The SEA99 Ground-Motion Predictive Relations for
    Extensional Tectonic Regimes: Revisions and a New Peak Ground Velocity
    Relation"
    Bulletin of the Seismological Society of America,
    Vol. 94, No. 1, pp. 341–348, February 2004
    """
    #: Supported tectonic region type is active shallow crust,
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: TO CHECK PSV!
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is VECTORIAL
    #: :attr:`~openquake.hazardlib.const.IMC.VECTORIAL`,
    #: NOTE: The paper indicates it as Geometric mean
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rjb distance
    #: see paragraph 'Predictor Variables', page 6.
    REQUIRES_DISTANCES = {'rjb'}

    #: No independent tests - verification against paper for PGA and PGV,
    #: but not for SA and Standard Deviations
    non_verified = True

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            M = ctx.mag - 6
            R = np.sqrt(ctx.rjb ** 2 + C['h'] ** 2)

            # In the original formulation of the GMPE, distinction is only made
            # between rock and soil ctx, which I assumed separated by the Vs30
            # value of 910m/s (see equation 5 of the paper)
            gamma = np.array([0 if v > 910. else 1 for v in ctx.vs30])

            mean[m] = (C['b1'] +
                       C['b2'] * M +
                       C['b3'] * M ** 2 +
                       C['b5'] * np.log10(R) +
                       C['b6'] * gamma)

            # Convert from base 10 to base e
            mean[m] /= np.log10(np.e)

            # Converting PSV to PSA
            if imt != PGA() and imt != PGV():
                omega = 2.*np.pi/imt.period
                mean[m] += np.log(omega/(gravity*100))

            # Computing standard deviation
            if (self.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT ==
                    'Random horizontal'):
                # Using equation 8 of the paper,
                # corrected as indicated in the erratum
                Sr = np.sqrt(C['SlZ']**2 + (C['S3'] / np.sqrt(2))**2)
            else:
                Sr = C['SlZ']

            # Convert from base 10 to base e
            sig[m] = Sr / np.log10(np.e)

    #: coefficient table provided by GSC (corrected as in the erratum)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt         Bv      b1      b2       b3       b5      b6      h     SlZ      S3
    pgv          0   2.252   0.490        0   -1.196   0.195   7.06   0.246   0.075
    pga     -0.371   0.237   0.229        0   -1.052   0.174   7.27   0.203   0.094
    0.100   -0.212   2.109   0.327   -0.098   -1.250   0.099   9.99   0.273   0.110
    0.110   -0.211   2.120   0.318   -0.100   -1.207   0.099   9.84   0.265   0.111
    0.120   -0.215   2.129   0.313   -0.101   -1.173   0.101   9.69   0.257   0.113
    0.130   -0.221   2.138   0.309   -0.101   -1.145   0.103   9.54   0.252   0.114
    0.140   -0.228   2.145   0.307   -0.100   -1.122   0.107   9.39   0.247   0.115
    0.150   -0.238   2.152   0.305   -0.099   -1.103   0.111   9.25   0.242   0.116
    0.160   -0.248   2.158   0.305   -0.098   -1.088   0.116   9.12   0.239   0.117
    0.170   -0.258   2.163   0.305   -0.096   -1.075   0.121   8.99   0.237   0.118
    0.180   -0.270   2.167   0.306   -0.094   -1.064   0.126   8.86   0.235   0.119
    0.190   -0.281   2.172   0.308   -0.092   -1.055   0.131   8.74   0.234   0.119
    0.200   -0.292   2.175   0.309   -0.090   -1.047   0.137   8.63   0.233   0.120
    0.220   -0.315   2.182   0.313   -0.086   -1.036   0.147   8.41   0.231   0.121
    0.240   -0.338   2.186   0.318   -0.082   -1.029   0.158   8.22   0.231   0.122
    0.260   -0.360   2.190   0.323   -0.078   -1.024   0.168   8.04   0.231   0.123
    0.280   -0.381   2.194   0.329   -0.073   -1.021   0.178   7.87   0.231   0.124
    0.300   -0.401   2.196   0.334   -0.070   -1.020   0.188   7.72   0.232   0.125
    0.320   -0.420   2.198   0.340   -0.066   -1.019   0.196   7.58   0.232   0.126
    0.340   -0.438   2.199   0.345   -0.062   -1.020   0.205   7.45   0.233   0.126
    0.360   -0.456   2.200   0.350   -0.059   -1.021   0.213   7.33   0.234   0.127
    0.380   -0.472   2.200   0.356   -0.055   -1.023   0.221   7.22   0.236   0.128
    0.400   -0.487   2.201   0.361   -0.052   -1.025   0.228   7.11   0.237   0.128
    0.420   -0.502   2.201   0.365   -0.049   -1.027   0.235   7.02   0.238   0.129
    0.440   -0.516   2.201   0.370   -0.047   -1.030   0.241   6.93   0.239   0.129
    0.460   -0.529   2.201   0.375   -0.044   -1.032   0.247   6.85   0.241   0.129
    0.480   -0.541   2.201   0.379   -0.042   -1.035   0.253   6.77   0.242   0.130
    0.500   -0.553   2.199   0.384   -0.039   -1.038   0.259   6.70   0.243   0.130
    0.550   -0.579   2.197   0.394   -0.034   -1.044   0.271   6.55   0.246   0.131
    0.600   -0.602   2.195   0.403   -0.030   -1.051   0.281   6.42   0.249   0.132
    0.650   -0.622   2.191   0.411   -0.026   -1.057   0.291   6.32   0.252   0.132
    0.700   -0.639   2.187   0.418   -0.023   -1.062   0.299   6.23   0.254   0.133
    0.750   -0.653   2.184   0.425   -0.020   -1.067   0.305   6.17   0.257   0.133
    0.800   -0.666   2.179   0.431   -0.018   -1.071   0.311   6.11   0.260   0.134
    0.850   -0.676   2.174   0.437   -0.016   -1.075   0.316   6.07   0.262   0.134
    0.900   -0.685   2.170   0.442   -0.015   -1.078   0.320   6.04   0.264   0.134
    0.950   -0.692   2.164   0.446   -0.014   -1.081   0.324   6.02   0.267   0.135
    1.000   -0.698   2.160   0.450   -0.014   -1.083   0.326   6.01   0.269   0.135
    1.100   -0.706   2.150   0.457   -0.013   -1.085   0.330   6.01   0.273   0.135
    1.200   -0.710   2.140   0.462   -0.014   -1.086   0.332   6.03   0.278   0.136
    1.300   -0.711   2.129   0.466   -0.015   -1.085   0.333   6.07   0.282   0.136
    1.400   -0.709   2.119   0.469   -0.017   -1.083   0.331   6.13   0.286   0.136
    1.500   -0.704   2.109   0.471   -0.019   -1.079   0.329   6.21   0.291   0.137
    1.600   -0.697   2.099   0.472   -0.022   -1.075   0.326   6.29   0.295   0.137
    1.700   -0.689   2.088   0.473   -0.025   -1.070   0.322   6.39   0.299   0.137
    1.800   -0.679   2.079   0.472   -0.029   -1.063   0.317   6.49   0.303   0.137
    1.900   -0.667   2.069   0.472   -0.032   -1.056   0.312   6.60   0.307   0.137
    2.000   -0.655   2.059   0.471   -0.037   -1.049   0.306   6.71   0.312   0.137
    """)
