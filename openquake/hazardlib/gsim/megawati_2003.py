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
Module exports :class:`megawatiEtAl2003`.
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def _get_azimuth_correction(coe, azimuth):
    """
    This is the azimuth correction defined in the functional form (see
    equation 3 at page 2256)
    """
    term1 = abs(np.cos(np.radians(2.*azimuth)))
    term2 = abs(np.sin(np.radians(2.*azimuth)))*coe['a5']
    return np.log(np.max(np.hstack((term1, term2))))


def _get_distance_scaling(coe, rhypo):
    """
    Returns the distance scaling term
    """
    return coe["a3"] * np.log(rhypo) + coe["a4"] * rhypo


def _get_magnitude_scaling(coe, mag):
    """
    Returns the magnitude scaling term
    """
    return coe["a0"] + coe["a1"] * mag + coe["a2"] * mag**2.


class MegawatiEtAl2003(GMPE):
    """
    Implements GMPE developed by Megawati, Pan and Koketsu and published in
    2003 as "Response spectral attenuation relationships for Singapore and the
    Malay Peninsula due to distant Sumatran-fault earthquakes", Earthquake
    Engineering & Structural Dynamics Volume 32, pages 2241–2265.
    """

    #: Supported tectonic region type is active shallow crust
    #: Sumatra strike-slip fault
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground veloacity and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is geometric mean
    #: of two horizontal components,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No site parameter required. This GMPE is for very hard rock conditions
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is hypocentral distance, and azimuth
    REQUIRES_DISTANCES = {'rhypo', 'azimuth'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            coe = self.COEFFS[imt]
            mean[m] = (_get_magnitude_scaling(coe, ctx.mag) +
                       _get_distance_scaling(coe, ctx.rhypo) +
                       _get_azimuth_correction(coe, ctx.azimuth))
            # Convert to g
            if imt.string.startswith(("PGA", "SA")):
                mean[m] = np.log(np.exp(mean[m]) / (100.0 * g))
            # Compute std
            sig[m] = coe['sigma']

    #: Coefficient table for rock ctx, see table 3 page 2257
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT             a0       a1          a2        a3          a4      a5    sigma
PGV        -13.512   3.8980   -0.129363   -1.0000   -0.000887  0.1286   0.3740
PGA         -8.167   2.7779   -0.045945   -1.0000   -0.001906  0.1356   0.3511
 0.50       -6.190   2.5075   -0.023022   -1.0000   -0.002847  0.2049   0.3432
 0.55       -5.965   2.4599   -0.019483   -1.0000   -0.002834  0.1859   0.3423
 0.60       -5.831   2.4234   -0.016979   -1.0000   -0.002763  0.1754   0.3358
 0.65       -5.619   2.3407   -0.010115   -1.0000   -0.002683  0.1712   0.3383
 0.70       -5.425   2.2721   -0.004676   -1.0000   -0.002601  0.1542   0.3509
 0.75       -5.380   2.2521   -0.003320   -1.0000   -0.002510  0.1510   0.3650
 0.80       -5.528   2.2516   -0.003498   -0.9790   -0.002431  0.1531   0.3726
 0.85       -5.778   2.2476   -0.003025   -0.9421   -0.002398  0.1551   0.3683
 0.90       -5.790   2.2218   -0.000880   -0.9360   -0.002332  0.1529   0.3735
 0.95       -6.094   2.2605   -0.004202   -0.9075   -0.002299  0.1492   0.3787
 1.00       -6.396   2.3033   -0.007976   -0.8811   -0.002250  0.1450   0.3775
 1.10       -6.862   2.3479   -0.011760   -0.8375   -0.002148  0.1403   0.3914
 1.20       -7.661   2.4732   -0.021870   -0.7801   -0.002080  0.1370   0.4034
 1.30       -8.447   2.5829   -0.030536   -0.7182   -0.002022  0.1444   0.3903
 1.40       -8.729   2.5796   -0.029935   -0.6847   -0.001955  0.1460   0.3857
 1.50       -9.002   2.6385   -0.034455   -0.6849   -0.001866  0.1429   0.3917
 1.60       -9.599   2.8548   -0.051636   -0.7163   -0.001713  0.1381   0.3935
 1.70      -10.069   2.9852   -0.062163   -0.7195   -0.001603  0.1352   0.4030
 1.80      -10.449   3.0345   -0.066243   -0.6909   -0.001545  0.1334   0.4138
 1.90      -10.888   3.0905   -0.070529   -0.6560   -0.001512  0.1314   0.4215
 2.00      -11.553   3.2211   -0.080618   -0.6191   -0.001527  0.1322   0.4261
 2.20      -12.586   3.4295   -0.096925   -0.5719   -0.001506  0.1303   0.4642
 2.40      -13.313   3.5537   -0.106129   -0.5401   -0.001436  0.1327   0.4928
 2.60      -14.023   3.7036   -0.117145   -0.5248   -0.001363  0.1354   0.4987
 2.80      -14.747   3.8781   -0.130894   -0.5145   -0.001310  0.1359   0.4916
 3.00      -15.204   4.0192   -0.141834   -0.5396   -0.001176  0.1379   0.4687
 3.20      -15.571   4.1214   -0.149159   -0.5631   -0.001031  0.1429   0.4571
 3.40      -16.028   4.2365   -0.157839   -0.5734   -0.000912  0.1472   0.4532
 3.60      -16.682   4.3508   -0.166237   -0.5417   -0.000911  0.1503   0.4473
 3.80      -17.249   4.4454   -0.172847   -0.5129   -0.000930  0.1547   0.4389
 4.00      -17.832   4.5516   -0.180406   -0.4906   -0.000918  0.1711   0.4268
 4.20      -18.330   4.6497   -0.187109   -0.4774   -0.000907  0.1741   0.4137
 4.40      -18.783   4.7669   -0.195587   -0.4804   -0.000881  0.1768   0.4016
 4.60      -19.139   4.8543   -0.201619   -0.4838   -0.000857  0.1796   0.3970
 4.80      -19.462   4.9128   -0.205331   -0.4756   -0.000861  0.1841   0.3911
 5.00      -19.772   4.9712   -0.209015   -0.4699   -0.000862  0.1887   0.3847
 5.50      -20.538   5.1717   -0.223871   -0.4814   -0.000816  0.2035   0.3740
 6.00      -20.812   5.2707   -0.230283   -0.5326   -0.000680  0.2244   0.3741
 6.50      -21.142   5.3397   -0.234073   -0.5513   -0.000626  0.2295   0.3720
 7.00      -21.702   5.5028   -0.245792   -0.5773   -0.000569  0.2479   0.3771
 7.50      -22.037   5.5940   -0.251227   -0.6049   -0.000532  0.2538   0.3910
 8.00      -22.199   5.6220   -0.251133   -0.6306   -0.000507  0.2574   0.4111
 8.50      -22.371   5.6944   -0.255129   -0.6780   -0.000397  0.2621   0.4196
 9.00      -22.632   5.7649   -0.259591   -0.7002   -0.000319  0.2636   0.4144
 9.50      -22.918   5.8431   -0.265147   -0.7169   -0.000260  0.2631   0.4087
10.00      -23.078   5.8682   -0.266233   -0.7268   -0.000222  0.2619   0.4056
11.00      -22.998   5.7565   -0.254562   -0.7317   -0.000176  0.2517   0.3968
12.00      -23.017   5.7090   -0.249180   -0.7423   -0.000138  0.2437   0.3854
13.00      -23.091   5.7515   -0.252199   -0.7820   -0.000071  0.2412   0.3778
14.00      -22.970   5.7395   -0.250671   -0.8244   -0.000011  0.2309   0.3729
15.00      -22.947   5.7004   -0.246974   -0.8330   -0.000000  0.2287   0.3707
16.00      -22.907   5.6432   -0.241860   -0.8330   -0.000000  0.2266   0.3683
17.00      -22.816   5.5623   -0.234844   -0.8276   -0.000009  0.2226   0.3657
18.00      -22.726   5.4955   -0.229113   -0.8274   -0.000015  0.2168   0.3636
19.00      -22.761   5.4510   -0.225431   -0.8087   -0.000085  0.1936   0.3632
20.00      -22.928   5.4329   -0.224139   -0.7800   -0.000167  0.1865   0.3629
""")
