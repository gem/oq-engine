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
Module exports :class:`SedaghatiPezeshk2017`.
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGV, PGA, SA

class SedaghatiPezeshk2017(GMPE):
    """
    Sedaghati, F., and S. Pezeshk (2017). Partially nonergodic empirical ground
    motion models for predicting horizontal and vertical PGV, PGA, and
    5% damped linear acceleration response spectra using data from
    Iranian plateau, Bull. Seismol. Soc. Am. 107, no. 4, 934–948.
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: PGV, and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGV,
        PGA,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see equations 6 and 7.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is magnitude.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: The required distance parameter is 'Joyner-Boore' distance.
    REQUIRES_DISTANCES = {'rjb'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        mean = (self._get_magnitude_scaling_term(C, rup.mag) +
                self._get_geometric_attenuation_term(C, dists.rjb, rup.mag) +
                self._get_site_scaling(C, sites.vs30))
        stddevs = self._get_stddevs(C, stddev_types)
        return mean, stddevs
    def _get_magnitude_scaling_term(self, C, mag):
        """
        Returns the magnitude scling term defined in equation 3
        """
        mh = self.CONSTS['mh']
        dmag = mag - mh
        if mag <= mh:
            mag_term = (C["a1"] + C["a2"] * dmag) + (C["a3"] * (dmag ** 2.0))
        else:
            mag_term = (C["a1"] + C["a4"] * dmag)
        return  mag_term
    def _get_geometric_attenuation_term(self, C, rjb, mag):
        """
        Returns the geometric attenuation term defined in equation 4
        """
        return (
            (C['b1'] + C['b2'] * mag) *
            np.log(np.sqrt(rjb ** 2.0 + C['h'] ** 2.0)) +
            (C['b3'] * (np.sqrt(rjb ** 2.0 + C['h'] ** 2.0)))
        )
    def _get_site_scaling(self, C, vs30):
        """
        Returns the shallow site response term defined in equation 5
        """
        return (C['c1'] + C['c2'] * np.log(vs30))

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
imt         a1        a2        a3        a4        b1        b2        b3         h        c1        c2       tau                 phi     sigma
PGV    4.33325   1.41553   0.05836   0.86556  -0.01452  -0.09448   0.00000   3.43732   1.04360  -0.16201   0.21991   0.632618371295049   0.66975
PGA    0.44780   0.24582  -0.14444   0.49645  -1.17792   0.04959   0.00000   4.52478   0.68185  -0.10727   0.20592   0.498769286143403   0.53961
0.05   1.28296   0.39084  -0.06956   0.41181  -1.26192   0.03221   0.00000   5.57414  -0.14576   0.02251   0.26759   0.578140639031715   0.63706
0.075  1.79752   0.40895  -0.07594   0.48121  -1.21353   0.01317   0.00000   6.69748  -0.41950   0.06567   0.29109   0.574944005360522   0.64443
0.1    1.75732   0.44831  -0.10471   0.51506  -0.91959  -0.01771  -0.00132   5.89668  -0.23816   0.03735   0.26870   0.611215205308245   0.66767
0.15   1.92211   0.68712  -0.09073   0.42364  -0.66230  -0.05142  -0.00107   5.05776   0.53382  -0.08402   0.24067   0.611015859450473   0.65671
0.2    1.84094   0.81142  -0.06014   0.41682  -0.61504  -0.05301  -0.00052   5.21685   0.96326  -0.15205   0.22902   0.604550011909685   0.64648
0.3    0.93871   0.42956  -0.12175  -0.13730  -1.08613   0.04596  -0.00141   4.05788   1.94902  -0.30571   0.26071   0.606516354602248   0.66018
0.5    0.16310   0.12164  -0.25975   0.15371  -1.26131   0.08491  -0.00131   4.79965   2.41536  -0.37835   0.23706   0.665819562719510   0.70676
0.75  -0.35304   0.07930  -0.27238   0.49447  -1.45150   0.11993  -0.00114   6.58682   2.32740  -0.36478   0.25190   0.716318070761865   0.75932
1.0   -0.32946   0.09923  -0.31769   0.33462  -1.53799   0.11986   0.00000   9.71673   2.31834  -0.36319   0.25511   0.738841191664352   0.78164
1.5   -1.07378   0.17559  -0.31747   0.32466  -1.69669   0.15532   0.00000   8.85002   2.65348  -0.41564   0.26505   0.772176473353080   0.81640
2.0   -1.34555   0.21828  -0.33131   0.39197  -1.86417   0.17975   0.00000  10.79563   2.61514  -0.40933   0.23501   0.773796518537012   0.80870
3.0   -1.071058  0.18318  -0.40189   0.60346  -2.02030   0.20208   0.00000  14.60791   2.32699  -0.36371   0.33210   0.720084986234264   0.79298
4.0   -1.64664   0.42652  -0.33922   0.66777  -2.06789   0.20052   0.00000  20.18967   2.01555  -0.31493   0.48985   0.669545109159943   0.82960
""")

    #: equation constants (that are IMT independent)
    CONSTS = {
        # coefficients in paper
        'mh': 7.0
    }
