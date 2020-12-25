# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
Module exports :class:`ZafaraniEtAl2018`.
"""
import numpy as np
# from scipy.constants import g
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA

class ZafaraniEtAl2018(GMPE):
    """
    Zafarani, H., L. Luzi, G. Lanzano, and M. Soghrat (2018). Empirical
    equations for the prediction of PGA and pseudo spectral accelerations
    using Iranian strong-motion data, J. Seismol. 22, no. 1, 263–285.
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see equations 4 and 5.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, and rake.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is rrup
    REQUIRES_DISTANCES = {'rrup'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        imean = self._get_mean_values(C, sites, rup, dists)
        mean = np.log((10.0 ** (imean - 2.0)) / 10)
        stddevs = self._get_stddevs(C, stddev_types)
        return mean, stddevs

    def _get_mean_values(self, C, sites, rup, dists):
        return (self._get_magnitude_scaling_term(C, rup) +
                self._get_style_of_faulting_term(C, rup) +
                self._get_geometric_attenuation_term(C, dists) +
                self._get_site_scaling(C, sites.vs30))
    def _get_magnitude_scaling_term(self, C, rup):
        """
        Returns the magnitude scling term defined in equation (2)
        """
        dmag = rup.mag - C["mh"]
        if rup.mag <= C["mh"]:
            mag_term = (C["e1"] + C["b1"] * dmag) + (C["b2"] * (dmag ** 2.0))
        else:
            mag_term = (C["e1"] + C["b3"] * dmag)
        return  mag_term
    def _get_style_of_faulting_term(self, C, rup):
        """
        Returns the style-of-faulting term.
        Fault type (Strike-slip, Normal, Thrust/reverse) is
        derived from rake angle.
        Rakes angles within 30 of horizontal are strike-slip,
        angles from 30 to 150 are reverse, and angles from
        -30 to -150 are normal.
        Note that the 'Unspecified' case is not considered in this class
        as rake is required as an input variable
        """
        SS, NS, RS = 0.0, 0.0, 0.0
        if np.abs(rup.rake) <= 30.0 or (180.0 - np.abs(rup.rake)) <= 30.0:
            # strike-slip
            SS = 1.0
        elif rup.rake > 30.0 and rup.rake < 150.0:
            # reverse
            RS = 1.0
        else:
            # normal
            NS = 1.0
        return (0 * NS) + (C["fTF"] * RS) + (C["fSS"] * SS)
    def _get_geometric_attenuation_term(self, C, dists):
        """
        Returns the geometric attenuation term defined in equation 3
        """
        r_adj = np.sqrt(dists.rrup ** 2.0 + C["h"] ** 2.0)
        return C["c1"] * np.log10(r_adj)
    def _get_site_scaling(self, C, vs30):
        """
        Returns the shallow site response term defined in the text
        """
        f_s = np.zeros_like(vs30)
        # Site class B
        idx = np.logical_and(vs30 < 800.0, vs30 >= 360.0)
        f_s[idx] = C["SB"]
        # Site Class C
        idx = np.logical_and(vs30 < 360.0, vs30 >= 180.0)
        f_s[idx] = C["SC"]
        # Site Class D
        idx = vs30 < 180.0
        f_s[idx] = C["SD"]
        return f_s

    def _get_stddevs(self, C, stddev_types):
        """
        Return standard deviations as defined inin the text and table.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(C['sigma'])
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C['phi'])
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'])
        return stddevs


    COEFFS = CoeffsTable(sa_damping=5, table="""\
imt     mh      e1      b1      b2      b3      c1       h     fSS     fTF      SB      SC      SD     tau     phi   sigma
PGA    5.0   2.880   0.554   0.103   0.244  -0.960   7.283  -0.030  -0.039   0.027   0.010  -0.017   0.094   0.283   0.298
0.04   5.0   3.065   0.491   0.043   0.237  -1.027   6.835  -0.023  -0.045   0.010  -0.003  -0.039   0.098   0.294   0.310
0.07   5.3   3.473   0.241  -0.153   0.204  -1.037   8.311  -0.014  -0.046  -0.006  -0.037  -0.055   0.113   0.298   0.319
0.10   5.4   3.673   0.283  -0.116   0.180  -1.159   9.376  -0.024  -0.056   0.007  -0.052  -0.049   0.115   0.305   0.326
0.15   5.6   3.623   0.249  -0.097   0.183  -1.090  10.228  -0.020  -0.028   0.061  -0.001  -0.029   0.105   0.315   0.332
0.20   5.8   3.401   0.193  -0.124   0.207  -0.963   8.195   0.001   0.000   0.071   0.022   0.000   0.103   0.309   0.326
0.25   5.9   3.429   0.227  -0.112   0.232  -0.986  11.315   0.006   0.013   0.080   0.073   0.031   0.102   0.306   0.323
0.30   6.0   3.383   0.245  -0.118   0.227  -0.959  11.012  -0.008   0.010   0.073   0.104   0.048   0.103   0.308   0.325
0.35   6.0   3.325   0.305  -0.104   0.241  -0.947  11.250  -0.012   0.008   0.073   0.113   0.065   0.103   0.310   0.326
0.40   6.1   3.148   0.277  -0.128   0.254  -0.861   7.953  -0.016   0.010   0.076   0.114   0.077   0.104   0.313   0.330
0.45   6.1   3.089   0.286  -0.140   0.262  -0.848   7.498  -0.022   0.011   0.074   0.112   0.097   0.104   0.312   0.329
0.50   6.2   3.085   0.287  -0.139   0.263  -0.847   7.525  -0.013   0.020   0.060   0.095   0.100   0.104   0.313   0.330
0.60   6.3   3.029   0.311  -0.139   0.277  -0.836   6.723  -0.002   0.021   0.056   0.086   0.115   0.106   0.318   0.335
0.70   6.4   2.926   0.280  -0.157   0.302  -0.803   4.967   0.017   0.031   0.047   0.076   0.133   0.107   0.321   0.338
0.80   6.4   2.873   0.317  -0.159   0.330  -0.798   4.966   0.017   0.032   0.047   0.065   0.144   0.108   0.323   0.341
0.90   6.5   2.838   0.303  -0.164   0.373  -0.787   4.973   0.016   0.035   0.043   0.059   0.142   0.108   0.324   0.341
1.00   6.5   2.791   0.341  -0.161   0.372  -0.782   4.975   0.022   0.041   0.043   0.056   0.146   0.108   0.325   0.342
1.20   6.6   2.738   0.397  -0.145   0.388  -0.776   4.976   0.040   0.048   0.034   0.056   0.139   0.108   0.324   0.341
1.40   6.7   2.691   0.442  -0.128   0.377  -0.769   4.980   0.062   0.059   0.039   0.054   0.135   0.109   0.327   0.345
1.60   6.7   2.640   0.511  -0.110   0.410  -0.777   4.981   0.077   0.065   0.040   0.058   0.116   0.110   0.329   0.347
1.80   6.8   2.642   0.558  -0.091   0.395  -0.778   4.994   0.078   0.068   0.047   0.062   0.114   0.109   0.327   0.334
2.00   6.8   2.600   0.631  -0.072   0.397  -0.772   5.001   0.077   0.066   0.051   0.065   0.098   0.107   0.322   0.339
2.50   6.9   2.665   0.789  -0.026   0.135  -0.795   6.960   0.086   0.054   0.053   0.056   0.078   0.104   0.311   0.328
3.00   7.0   2.697   0.851  -0.008  -0.062  -0.809   8.447   0.099   0.048   0.047   0.041   0.043   0.101   0.303   0.319
4.00   7.2   2.626   0.877   0.001  -0.455  -0.775   8.296   0.107   0.023   0.048   0.025   0.032   0.134   0.290   0.319
""")

