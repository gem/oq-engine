# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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
Module exports :class:`AtkinsonBoore1995GSCBest`,
:class:`AtkinsonBoore1995GSCLowerLimit`,
:class:`AtkinsonBoore1995GSCUpperLimit`
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class AtkinsonBoore1995GSCBest(GMPE):
    """
    Implement equation used by the Geological Survey of Canada (GSC) for
    the 2010 Eastern Canada National Seismic Hazard Model. The equation fits
    the table values defined by Gail M. Atkinson and David M. Boore in
    "Ground-Motion Relations for Eastern North America", Bullettin of the
    Seismological Society of America, Vol. 85, No. 1, pp. 17-30, February 1995.
    Table of coefficients were provided by GSC and are associated to the 'Best'
    case (that is mean value unaffected).

    The class assumes magnitude to be in Mblg scale. The Atkinson 1993
    conversion equation is used to obtain Mw values.
    """
    #: Supported tectonic region type is stable continental, given
    #: that the equations have been derived for Eastern North America
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is random horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.RANDOM_HORIZONTAL`,
    #: see page 22 in Atkinson and Boore's manuscript
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RANDOM_HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: site params are not required
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is hypocentral distance
    #: see page 18 in Atkinson and Boore's manuscript
    REQUIRES_DISTANCES = set(('rhypo', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C = self.COEFFS[imt]

        # clip rhypo at 10 (this is the minimum distance used in
        # deriving the equation), see page 22, this avoids singularity
        # in mean value equation
        rhypo = dists.rhypo.copy()
        rhypo[rhypo < 10] = 10

        # convert magnitude from Mblg to Mw
        mag = rup.mag * 0.98 - 0.39 if rup.mag <= 5.5 else \
              2.715 - 0.277 * rup.mag + 0.127 * rup.mag * rup.mag

        # functional form as explained in 'Youngs_fit_to_AB95lookup.doc'
        f1 = np.minimum(np.log(rhypo), np.log(70.))
        f2 = np.maximum(np.log(rhypo / 130.), 0)
        mean = (
            C['c1'] + C['c2'] * mag + C['c3'] * mag ** 2 +
            (C['c4'] + C['c5'] * mag) * f1 +
            (C['c6'] + C['c7'] * mag) * f2 +
            C['c8'] * rhypo
        )

        stddevs = self._get_stddevs(stddev_types,  dists.rhypo.shape[0])

        return mean, stddevs

    def _get_stddevs(self, stddev_types, num_sites):
        """
        Return total standard deviation.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)
        stddevs = [np.zeros(num_sites) + 0.69 for _ in stddev_types]
        return stddevs

    #: coefficient table provided by GSC
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT      c1      c2      c3        c4     c5        c6      c7        c8
    pga     -1.329   1.272  -0.08240  -2.556  0.17220  -1.9600  0.17460  -0.0045350
    0.1     -2.907   1.522  -0.08528  -2.052  0.12484  -1.4224  0.07965  -0.0043090
    0.2     -5.487   1.932  -0.10290  -1.818  0.09797  -1.0760  0.06075  -0.0033250
    0.3     -7.567   2.284  -0.11930  -1.734  0.08814  -0.9551  0.04392  -0.0025700
    0.5     -9.476   2.503  -0.12310  -1.631  0.07610  -1.0490  0.06224  -0.0019590
    1.0     -11.134  2.470  -0.10569  -1.520  0.06165  -0.9106  0.05248  -0.001497
    2.0     -13.210  2.945  -0.15670  -1.864  0.11620  -0.7653  0.02729  -0.0009921
    """)


class AtkinsonBoore1995GSCLowerLimit(AtkinsonBoore1995GSCBest):
    """
    Implement equation used by the Geological Survey of Canada (GSC) for
    the 2010 Eastern Canada National Seismic Hazard Model. The equation fits
    the table values defined by Gail M. Atkinson and David M. Boore in
    "Ground-Motion Relations for Eastern North America", Bullettin of the
    Seismological Society of America, Vol. 85, No. 1, pp. 17-30, February 1995.
    Table of coefficients were provided by GSC and are associated to the 'Lower
    Limit' case (that is mean value decreased).
    """

    #: coefficient table provided by GSC
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT      c1      c2      c3        c4     c5        c6      c7        c8
    pga     -2.204   1.272  -0.08240  -2.556  0.17220  -1.9600  0.17460  -0.0045350
    0.1     -3.782   1.522  -0.08528  -2.052  0.12484  -1.4224  0.07965  -0.0043090
    0.2     -6.224   1.932  -0.10290  -1.818  0.09797  -1.0760  0.06075  -0.0033250
    0.3     -8.212   2.284  -0.11930  -1.734  0.08814  -0.9551  0.04392  -0.0025700
    0.5     -10.029  2.503  -0.12310  -1.631  0.07610  -1.0490  0.06224  -0.0019590
    1.0     -11.548  2.470  -0.10569  -1.520  0.06165  -0.9106  0.05248  -0.001497
    """)


class AtkinsonBoore1995GSCUpperLimit(AtkinsonBoore1995GSCBest):
    """
    Implement equation used by the Geological Survey of Canada (GSC) for
    the 2010 Eastern Canada National Seismic Hazard Model. The equation fits
    the table values defined by Gail M. Atkinson and David M. Boore in
    "Ground-Motion Relations for Eastern North America", Bullettin of the
    Seismological Society of America, Vol. 85, No. 1, pp. 17-30, February 1995.
    Table of coefficients were provided by GSC and are associated to the 'Upper
    Limit' case (that is mean value increased).
    """

    #: coefficient table provided by GSC
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT      c1      c2      c3        c4     c5        c6      c7        c8
    pga     -1.030   1.272  -0.08240  -2.556  0.17220  -1.9600  0.17460  -0.0045350
    0.1     -2.608   1.522  -0.08528  -2.052  0.12484  -1.4224  0.07965  -0.0043090
    0.2     -4.911   1.932  -0.10290  -1.818  0.09797  -1.0760  0.06075  -0.0033250
    0.3     -6.784   2.284  -0.11930  -1.734  0.08814  -0.9551  0.04392  -0.0025700
    0.5     -8.509   2.503  -0.12310  -1.631  0.07610  -1.0490  0.06224  -0.0019590
    1.0     -9.891   2.470  -0.10569  -1.520  0.06165  -0.9106  0.05248  -0.001497
    """)
