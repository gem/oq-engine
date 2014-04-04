# The Hazard Library
# Copyright (C) 2013-2014, GEM Foundation
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
Module exports :class:`AkkarEtAl2013`.
"""
from __future__ import division

import numpy as np
import warnings
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class AkkarEtAl2013(GMPE):
    """
    Implements GMPE developed by S. Akkar, M. A. Sandikkaya, and J. J. Bommer
    as published in "Empirical Ground-Motion Models for Point- and Extended-
    Source Crustal Earthquake Scenarios in Europe and the Middle East",
    Bullettin of Earthquake Engineering (2013).
    The class implements the equations for Joyner-Boore distance and based on
    manuscript provided by the original authors.
    """
    #: The supported tectonic region type is active shallow crust because
    #: the equations have been developed for "all seismically- active regions
    #: bordering the Mediterranean Sea and extending to the Middle East", see
    #: section 'A New Generation of European Ground-Motion Models', page 4.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: The supported intensity measure types are PGA, PGV, and SA, see table
    #: 4.a, pages 22-23
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: The supported intensity measure component is 'average horizontal', see
    #: section 'A New Generation of European Ground-Motion Models', page 8
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: The supported standard deviations are total, inter and intra event, see
    #: table 4.a, pages 22-23
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: The required site parameter is vs30, see equation 1, page 20.
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: The required rupture parameters are rake and magnitude, see equation 1,
    #: page 20.
    REQUIRES_RUPTURE_PARAMETERS = set(('rake', 'mag'))

    #: The required distance parameter is 'Joyner-Boore' distance, because
    #: coefficients in table 4.a, pages 22-23, are used.
    REQUIRES_DISTANCES = set(('rjb', ))
    warnings.warn('AkkarEtAl2013 is deprecated - use AkkarEtAlRjb2014 instead',
                  DeprecationWarning)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.

        Implement equation 1, page 20.
        """
        # compute median PGA on rock, needed to compute non-linear site
        # amplification
        C_pga = self.COEFFS[PGA()]
        median_pga = np.exp(
            self._compute_mean(C_pga, rup.mag, dists, rup.rake)
        )

        # compute full mean value by adding nonlinear site amplification terms
        C = self.COEFFS[imt]
        mean = (self._compute_mean(C, rup.mag, dists, rup.rake) +
                self._compute_non_linear_term(C, median_pga, sites))

        stddevs = self._get_stddevs(C, stddev_types, num_sites=sites.vs30.size)

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations as defined in table 4a, p. 22.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                sigma_t = np.sqrt(C['sigma'] ** 2 + C['tau'] ** 2)
                stddevs.append(sigma_t + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C['sigma'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(num_sites))
        return stddevs

    def _compute_linear_magnitude_term(self, C, mag):
        """
        Compute and return second term in equations (2a)
        and (2b), page 20.
        """
        if mag <= self.c1:
            # this is the second term in eq. (2a), p. 20
            return C['a2'] * (mag - self.c1)
        else:
            # this is the second term in eq. (2b), p. 20
            return C['a7'] * (mag - self.c1)

    def _compute_quadratic_magnitude_term(self, C, mag):
        """
        Compute and return third term in equations (2a)
        and (2b), page  20.
        """
        return C['a3'] * (8.5 - mag) ** 2

    def _compute_logarithmic_distance_term(self, C, mag, dists):
        """
        Compute and return fourth term in equations (2a)
        and (2b), page 20.
        """
        return (
            (C['a4'] + C['a5'] * (mag - self.c1)) *
            np.log(np.sqrt(dists.rjb ** 2 + C['a6'] ** 2))
        )

    def _compute_faulting_style_term(self, C, rake):
        """
        Compute and return fifth and sixth terms in equations (2a)
        and (2b), pages 20.
        """
        Fn = float(rake > -135.0 and rake < -45.0)
        Fr = float(rake > 45.0 and rake < 135.0)

        return C['a8'] * Fn + C['a9'] * Fr

    def _compute_non_linear_term(self, C, pga_only, sites):
        """
        Compute non-linear term, equation (3a) to (3c), page 20.
        """
        Vref = 750.0
        Vcon = 1000.0
        lnS = np.zeros_like(sites.vs30)

        # equation (3a)
        idx = sites.vs30 < Vref
        lnS[idx] = (
            C['b1'] * np.log(sites.vs30[idx] / Vref) +
            C['b2'] * np.log(
                (pga_only[idx] + C['c'] * (sites.vs30[idx] / Vref) ** C['n']) /
                ((pga_only[idx] + C['c']) * (sites.vs30[idx] / Vref) ** C['n'])
            )
        )

        # equation (3b)
        idx = (sites.vs30 >= Vref) & (sites.vs30 <= Vcon)
        lnS[idx] = C['b1'] * np.log(sites.vs30[idx]/Vref)

        # equation (3c)
        idx = sites.vs30 > Vcon
        lnS[idx] = C['b1'] * np.log(Vcon/Vref)

        return lnS

    def _compute_mean(self, C, mag, dists, rake):
        """
        Compute and return mean value without site conditions,
        that is equations (1a) and (1b), p.2981-2982.
        """
        mean = (
            C['a1'] +
            self._compute_linear_magnitude_term(C, mag) +
            self._compute_quadratic_magnitude_term(C, mag) +
            self._compute_logarithmic_distance_term(C, mag, dists) +
            self._compute_faulting_style_term(C, rake)
        )

        return mean

    #: c1 is the reference magnitude, fixed to 6.75Mw (which happens to be the
    #: same value used in Boore and Atkinson, 2008)
    #: see paragraph 'Functional Form of Predictive Equations and Regressions',
    #: page 21
    c1 = 6.75

    #: Coefficient table (from Table 3 and 4a, page 22)
    #: Table 4.a: Period-dependent regression coefficients of the RJB
    #: ground-motion model
    #: sigma is the 'intra-event' standard deviation, while tau is the
    #: 'inter-event' standard deviation
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT         a1           a2           a3            a4           a5          a6       a7           a8           a9          c1        Vcon      Vref     c        n        b1            b2            sigma       tau
    pga         1.85329      0.0029      -0.02807      -1.23452      0.2529      7.5      -0.5096      -0.1091      0.0937      6.75      1000      750      2.5      3.2      -0.41997      -0.28846      0.6201      0.3501
    0.010       1.87032      0.0029      -0.02740      -1.23698      0.2529      7.5      -0.5096      -0.1115      0.0953      6.75      1000      750      2.5      3.2      -0.41729      -0.28685      0.6215      0.3526
    0.020       1.95279      0.0029      -0.02715      -1.25363      0.2529      7.5      -0.5096      -0.1040      0.1029      6.75      1000      750      2.5      3.2      -0.39998      -0.28241      0.6266      0.3555
    0.030       2.07006      0.0029      -0.02403      -1.27525      0.2529      7.5      -0.5096      -0.0973      0.1148      6.75      1000      750      2.5      3.2      -0.34799      -0.26842      0.6410      0.3565
    0.040       2.20452      0.0029      -0.01797      -1.30123      0.2529      7.5      -0.5096      -0.0884      0.1073      6.75      1000      750      2.5      3.2      -0.27572      -0.24759      0.6534      0.3484
    0.050       2.35413      0.0029      -0.01248      -1.32632      0.2529      7.5      -0.5096      -0.0853      0.1052      6.75      1000      750      2.5      3.2      -0.21231      -0.22385      0.6622      0.3551
    0.075       2.63078      0.0029      -0.00532      -1.35722      0.2529      7.5      -0.5096      -0.0779      0.0837      6.75      1000      750      2.5      3.2      -0.14427      -0.17525      0.6626      0.3759
    0.100       2.85412      0.0029      -0.00925      -1.38182      0.2529      7.5      -0.5096      -0.0749      0.0761      6.75      1000      750      2.5      3.2      -0.27064      -0.29293      0.6670      0.4067
    0.110       2.89772      0.0029      -0.01062      -1.38345      0.2529      7.5      -0.5096      -0.0704      0.0707      6.75      1000      750      2.5      3.2      -0.31025      -0.31837      0.6712      0.4059
    0.120       2.92748      0.0029      -0.01291      -1.37997      0.2529      7.5      -0.5096      -0.0604      0.0653      6.75      1000      750      2.5      3.2      -0.34796      -0.33860      0.6768      0.4022
    0.130       2.95162      0.0029      -0.01592      -1.37627      0.2529      7.5      -0.5096      -0.0490      0.0617      6.75      1000      750      2.5      3.2      -0.39668      -0.36646      0.6789      0.4017
    0.140       2.96299      0.0029      -0.01866      -1.37155      0.2529      7.5      -0.5096      -0.0377      0.0581      6.75      1000      750      2.5      3.2      -0.43996      -0.38417      0.6822      0.3945
    0.150       2.96622      0.0029      -0.02193      -1.36460      0.2529      7.5      -0.5096      -0.0265      0.0545      6.75      1000      750      2.5      3.2      -0.48313      -0.39551      0.6796      0.3893
    0.160       2.93166      0.0029      -0.02429      -1.35074      0.2529      7.5      -0.5096      -0.0194      0.0509      6.75      1000      750      2.5      3.2      -0.52431      -0.40869      0.6762      0.3928
    0.170       2.88988      0.0029      -0.02712      -1.33454      0.2529      7.5      -0.5096      -0.0125      0.0507      6.75      1000      750      2.5      3.2      -0.55680      -0.41528      0.6723      0.396
    0.180       2.84627      0.0029      -0.03003      -1.31959      0.2529      7.5      -0.5096      -0.0056      0.0502      6.75      1000      750      2.5      3.2      -0.58922      -0.42717      0.6694      0.396
    0.190       2.79778      0.0029      -0.03300      -1.30450      0.2529      7.5      -0.5096      0.00000      0.0497      6.75      1000      750      2.5      3.2      -0.62635      -0.44130      0.6647      0.3932
    0.200       2.73872      0.0029      -0.03462      -1.28877      0.2529      7.5      -0.5096      0.00000      0.0493      6.75      1000      750      2.5      3.2      -0.65315      -0.44644      0.6645      0.3842
    0.220       2.63479      0.0029      -0.03789      -1.26125      0.2529      7.5      -0.5096      0.00000      0.0488      6.75      1000      750      2.5      3.2      -0.68711      -0.44872      0.6600      0.3887
    0.240       2.53886      0.0029      -0.04173      -1.23600      0.2529      7.5      -0.5096      0.00000      0.0483      6.75      1000      750      2.5      3.2      -0.72744      -0.46341      0.6651      0.3792
    0.260       2.48747      0.0029      -0.04768      -1.21882      0.2529      7.5      -0.5096      0.00000      0.0478      6.75      1000      750      2.5      3.2      -0.77335      -0.48705      0.6650      0.3754
    0.280       2.38739      0.0029      -0.05178      -1.19543      0.2529      7.5      -0.5096      0.00000      0.0474      6.75      1000      750      2.5      3.2      -0.80508      -0.47334      0.6590      0.3757
    0.300       2.30150      0.0029      -0.05672      -1.17072      0.2529      7.5      -0.5096      0.00000      0.0469      6.75      1000      750      2.5      3.2      -0.82609      -0.45730      0.6599      0.3816
    0.320       2.17298      0.0029      -0.06015      -1.13847      0.2529      7.5      -0.5096      0.00000      0.0464      6.75      1000      750      2.5      3.2      -0.84080      -0.44267      0.6654      0.3866
    0.340       2.07474      0.0029      -0.06508      -1.11131      0.2529      7.5      -0.5096      0.00000      0.0459      6.75      1000      750      2.5      3.2      -0.86251      -0.43888      0.6651      0.3881
    0.360       2.01953      0.0029      -0.06974      -1.09484      0.2529      7.5      -0.5096      0.00000      0.0459      6.75      1000      750      2.5      3.2      -0.87479      -0.43820      0.6662      0.3924
    0.380       1.95078      0.0029      -0.07346      -1.07812      0.2529      7.5      -0.5096      0.00000      0.0429      6.75      1000      750      2.5      3.2      -0.88522      -0.43678      0.6698      0.3945
    0.400       1.89372      0.0029      -0.07684      -1.06530      0.2529      7.5      -0.5096      0.00000      0.0400      6.75      1000      750      2.5      3.2      -0.89517      -0.43008      0.6697      0.3962
    0.420       1.83717      0.0029      -0.08010      -1.05451      0.2529      7.5      -0.5096      0.00000      0.0374      6.75      1000      750      2.5      3.2      -0.90875      -0.42190      0.6696      0.389
    0.440       1.77528      0.0029      -0.08296      -1.04332      0.2529      7.5      -0.5096      0.00000      0.0349      6.75      1000      750      2.5      3.2      -0.91922      -0.40903      0.6641      0.3929
    0.460       1.73155      0.0029      -0.08623      -1.03572      0.2529      7.5      -0.5096      0.00000      0.0323      6.75      1000      750      2.5      3.2      -0.92670      -0.39442      0.6575      0.4009
    0.480       1.70132      0.0029      -0.09070      -1.02724      0.2529      7.5      -0.5096      0.00000      0.0297      6.75      1000      750      2.5      3.2      -0.93720      -0.38462      0.6540      0.4022
    0.500       1.67127      0.0029      -0.09490      -1.01909      0.2529      7.5      -0.5096      0.00000      0.0271      6.75      1000      750      2.5      3.2      -0.94614      -0.37408      0.6512      0.4021
    0.550       1.53838      0.0029      -0.10275      -0.99351      0.2529      7.5      -0.5096      0.00000      0.0245      6.75      1000      750      2.5      3.2      -0.96564      -0.35582      0.6570      0.4057
    0.600       1.37505      0.0029      -0.10747      -0.96429      0.2529      7.5      -0.5096      0.00000      0.0219      6.75      1000      750      2.5      3.2      -0.98499      -0.34053      0.6630      0.406
    0.650       1.21156      0.0029      -0.11262      -0.93347      0.2529      7.5      -0.5096      0.00000      0.0193      6.75      1000      750      2.5      3.2      -0.99733      -0.30949      0.6652      0.4124
    0.700       1.09262      0.0029      -0.11835      -0.91162      0.2529      7.5      -0.5096      0.00000      0.0167      6.75      1000      750      2.5      3.2      -1.00469      -0.28772      0.6696      0.4135
    0.750       0.95211      0.0029      -0.12347      -0.88393      0.2529      7.5      -0.5096      0.00000      0.0141      6.75      1000      750      2.5      3.2      -1.00786      -0.28957      0.6744      0.4043
    0.800       0.85227      0.0029      -0.12678      -0.86884      0.2529      7.5      -0.5096      0.00000      0.0115      6.75      1000      750      2.5      3.2      -1.00606      -0.28555      0.6716      0.3974
    0.850       0.76564      0.0029      -0.13133      -0.85442      0.2529      7.5      -0.5096      0.00000      0.0089      6.75      1000      750      2.5      3.2      -1.01093      -0.28364      0.6713      0.3971
    0.900       0.66856      0.0029      -0.13551      -0.83929      0.2529      7.5      -0.5096      0.00000      0.0062      6.75      1000      750      2.5      3.2      -1.01576      -0.28037      0.6738      0.3986
    0.950       0.58739      0.0029      -0.13957      -0.82668      0.2529      7.5      -0.5096      0.00000      0.0016      6.75      1000      750      2.5      3.2      -1.01353      -0.28390      0.6767      0.3949
    1.000       0.52349      0.0029      -0.14345      -0.81838      0.2529      7.5      -0.5096      0.00000      0.0000      6.75      1000      750      2.5      3.2      -1.01331      -0.28702      0.6787      0.3943
    1.100       0.37680      0.0029      -0.15051      -0.79691      0.2529      7.5      -0.5096      0.00000      0.0000      6.75      1000      750      2.5      3.2      -1.01240      -0.27669      0.6912      0.3806
    1.200       0.23251      0.0029      -0.15527      -0.77813      0.2529      7.5      -0.5096      0.00000      0.0000      6.75      1000      750      2.5      3.2      -1.00489      -0.27538      0.7015      0.3802
    1.300       0.10481      0.0029      -0.16106      -0.75888      0.2529      7.5      -0.5096      0.00000      0.0000      6.75      1000      750      2.5      3.2      -0.98876      -0.25008      0.7017      0.3803
    1.400       0.00887      0.0029      -0.16654      -0.74871      0.2529      7.5      -0.5096      0.00000      0.0000      6.75      1000      750      2.5      3.2      -0.97760      -0.23508      0.7141      0.3766
    1.500      -0.01867      0.0029      -0.17187      -0.75751      0.2529      7.5      -0.5096      0.00000      0.0000      6.75      1000      750      2.5      3.2      -0.98071      -0.24695      0.7164      0.3799
    1.600      -0.09960      0.0029      -0.17728      -0.74823      0.2529      7.5      -0.5096      0.00000      0.0000      6.75      1000      750      2.5      3.2      -0.96369      -0.22870      0.7198      0.3817
    1.700      -0.21166      0.0029      -0.17908      -0.73766      0.2529      7.5      -0.5096      0.00000      0.0000      6.75      1000      750      2.5      3.2      -0.94634      -0.21655      0.7226      0.3724
    1.800      -0.27300      0.0029      -0.18438      -0.72996      0.2529      7.5      -0.5096      0.00000      -0.003      6.75      1000      750      2.5      3.2      -0.93606      -0.20302      0.7241      0.371
    1.900      -0.35366      0.0029      -0.18741      -0.72279      0.2529      7.5      -0.5096      0.00000      -0.006      6.75      1000      750      2.5      3.2      -0.91408      -0.18228      0.7266      0.3745
    2.000      -0.42891      0.0029      -0.19029      -0.72033      0.2529      7.5      -0.5096      0.00000      -0.009      6.75      1000      750      2.5      3.2      -0.91007      -0.17336      0.7254      0.3717
    2.200      -0.55307      0.0029      -0.19683      -0.71662      0.2529      7.5      -0.5096      0.00000      -0.0141     6.75      1000      750      2.5      3.2      -0.89376      -0.15463      0.7207      0.3758
    2.400      -0.67806      0.0029      -0.20339      -0.70452      0.2529      7.5      -0.5096      0.00000      -0.0284     6.75      1000      750      2.5      3.2      -0.87052      -0.13181      0.7144      0.3973
    2.600      -0.80494      0.0029      -0.20703      -0.69691      0.2529      7.5      -0.5096      0.00000      -0.0408     6.75      1000      750      2.5      3.2      -0.85889      -0.14066      0.7122      0.4001
    2.800      -0.91278      0.0029      -0.21074      -0.69560      0.2529      7.5      -0.5096      0.00000      -0.0534     6.75      1000      750      2.5      3.2      -0.86106      -0.13882      0.7129      0.4025
    3.000      -1.05642      0.0029      -0.21392      -0.69085      0.2529      7.5      -0.5096      0.00000      -0.0683     6.75      1000      750      2.5      3.2      -0.85793      -0.13336      0.6997      0.4046
    3.200      -1.17715      0.0029      -0.21361      -0.67711      0.2529      7.5      -0.5096      0.00000      -0.078      6.75      1000      750      2.5      3.2      -0.82094      -0.13770      0.6820      0.4194
    3.400      -1.22091      0.0029      -0.21951      -0.68177      0.2529      7.5      -0.5096      0.00000      -0.0943     6.75      1000      750      2.5      3.2      -0.84449      -0.15337      0.6682      0.3971
    3.600      -1.34547      0.0029      -0.22724      -0.65918      0.2529      7.5      -0.5096      0.00000      -0.1278     6.75      1000      750      2.5      3.2      -0.83216      -0.10884      0.6508      0.4211
    3.800      -1.39790      0.0029      -0.23180      -0.65298      0.2529      7.5      -0.5096      0.00000      -0.1744     6.75      1000      750      2.5      3.2      -0.79216      -0.08884      0.6389      0.415
    4.000      -1.37536      0.0029      -0.23848      -0.66482      0.2529      7.5      -0.5096      0.00000      -0.2231     6.75      1000      750      2.5      3.2      -0.75645      -0.07749      0.6196      0.3566
    pgv         5.61201      0.0029      -0.09980      -0.98388      0.2529      7.5      -0.5096      -0.0616      0.0630      6.75      1000      750      2.5      3.2      -0.72057      -0.19688      0.6014      0.3311
    """)
