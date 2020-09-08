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
Module exports:
class:`ECOS2009`,
class:`ECOS2009Highest`
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import MMI


class ECOS2009(GMPE):
    """
    Implements the Intensity Prediction Equation of
    "Calibration of historical earthquakes for the earthquake catalogue
    of Switzerland (ECOS-09)": Appendix D

    This class implements the version using "all intensity levels",
    fixed depth (h=10km) and the weighting scheme "no weighting".

    See page 18 for general equation (8) - needs to be solved for I_obs -
    and equation (9) for estimating coefficients c0,c1,c2,c3.
    Coefficients a,b are taken from Table 4 on page 19.
    Coefficients alpha,beta are taken from Table 5 on page 19.

    implemented by laurentiu.danciu@sed.ethz.ch
    """
    #: % Swiss IPE ECOS-09
    #: h = 10;
    #: a = -0.67755;
    #: b = -0.00174;

    #: alpha = 0.7725;
    #: beta = 1.0363
    #: c0 = alpha * (a * log(30/h) + b * (30 -h)) + beta;
    #: c1 = alpha;
    #: %c1 = 0.7725;
    #: %c2 = 0.5234;
    #: %c3 = 0.00135;
    #: c2 = -a * alpha;
    #: c3 = -b * alpha;
    #: I_SWISS = (Mw - c2 .* log(Rhyp/h) -c3 .* (Rhyp -h) -c0) ./ c1;

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are MMI

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        MMI
    ])

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    #: Required distance measure is hypocenter,
    REQUIRES_DISTANCES = set(('rhypo',))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type
        C = self.COEFFS[imt]
        mean = self._compute_mean(C, rup, dists, imt)
#         print (adj_mean)
        stddevs = self._get_stddevs(C, stddev_types, num_sites=dists.rhypo.shape)

        return mean, stddevs

    def _compute_mean(self, C, rup, dists, num_sites):
        """
        Compute mean value .
        """
        c0 = C['alpha'] * (C['a']*np.log(30/C['hypo_depth']) +
                           C['b']*(30-C['hypo_depth'])) + C['beta']
        c1 = C['alpha']
        c2 = -(C['a']) * C['alpha']
        c3 = -(C['b']) * C['alpha']

        log_term = np.log(dists.rhypo / C['hypo_depth'])
        dist_term = c3 * (dists.rhypo-C['hypo_depth'])

        return (rup.mag - c2 * log_term - dist_term - c0) / c1

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return total standard deviation.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            stddevs.append((C['sigma']) + np.zeros(num_sites))

        return stddevs

    #: Coefficient table constructed from the electronic suplements of the
    #: original paper.
    COEFFS = CoeffsTable(table="""\
    IMT             a          b    alpha      beta   hypo_depth   sigma
    MMI      -0.67755   -0.00174   0.7725    1.0363      10.0      0.4073
        """)


class ECOS2009Highest(ECOS2009):
    """
    This class implements the version using "three highest intensity levels",
    fixed depth (h=10km) and the weighting scheme "no weighting".

    See page 18 for general equation (8) - needs to be solved for I_obs -
    and equation (9) for estimating coefficients c0,c1,c2,c3.
    Coefficients a,b are taken from Table 4 on page 19.
    Coefficients alpha,beta are taken from Table 5 on page 19.
    """

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
    ])

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        C = self.COEFFS[imt]
        mean = self._compute_mean(C, rup, dists, imt)
        stddevs = self._get_stddevs(C, stddev_types, num_sites=dists.rhypo.shape)
        return mean, stddevs

    COEFFS = CoeffsTable(table="""\
    IMT             a          b    alpha      beta   hypo_depth   sigma
    MMI       -0.4834   -0.00179    0.732     1.132      10.0      0.36474
        """)
