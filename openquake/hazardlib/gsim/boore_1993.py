# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
Module exports :class:`BooreEtAl1993GSCBest`,
:class:`BooreEtAl1993GSCUpperLimit`, :class:`BooreEtAl1993GSCLowerLimit`.
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class BooreEtAl1993GSCBest(GMPE):
    """
    Implement equation used by the Geological Survey of Canada (GSC) for
    the 2010 Western Canada National Seismic Hazard Model. The class implements
    the model of David M. Boore, William B. Joyner, and Thomas E. Fumal
    ("Estimation of Response Spectra and Peak Accelerations from Western North
    American Earthquakes: An Interim Report", 1993, U.S. Geological Survey,
    Open File Report 93-509).
    Equation coefficients provided by GSC for the random horizontal component
    and corresponding to the 'Best' case (that is mean unaffected)
    """
    #: Supported tectonic region type is active shallow crust, given
    #: that the equations have been derived for Western North America
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is random horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.RANDOM_HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RANDOM_HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: site params are not required
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is Rjb distance
    #: see paragraph 'Predictor Variables', page 6.
    REQUIRES_DISTANCES = set(('rjb', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C = self.COEFFS[imt]

        mag = rup.mag - 6
        d = np.sqrt(dists.rjb ** 2 + C['c7'] ** 2)
        mean = np.zeros_like(d)

        mean += C['c1'] + C['c2'] * mag + C['c3'] * mag ** 2 + C['c6']

        idx = d <= 100.
        mean[idx] = mean[idx] + C['c5'] * np.log10(d[idx])

        idx = d > 100.
        mean[idx] = (mean[idx] + C['c5'] * np.log10(100.) -
                     np.log10(d[idx] / 100.) + C['c4'] * (d[idx] - 100.))

        # convert from log10 to ln and from cm/s**2 to g
        mean = np.log((10.0 ** (mean - 2.0)) / g)

        stddevs = self._get_stddevs(C, stddev_types,  dists.rjb.shape[0])

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return total standard deviation.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)
        stddevs = [np.zeros(num_sites) + C['sigma'] for _ in stddev_types]
        return stddevs

    #: coefficient table provided by GSC
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT  c1     c2      c3      c4        c5     c6     c7    sigma
    pga  2.887  0.229   0.0    -0.00326  -0.778  0.162  5.57  0.529
    0.1  3.451  0.327  -0.098  -0.00395  -0.934  0.046  6.27  0.479
    0.2  3.464  0.309  -0.090  -0.00259  -0.924  0.190  7.02  0.495
    0.3  3.295  0.334  -0.070  -0.00202  -0.893  0.239  5.94  0.520
    0.5  2.980  0.384  -0.039  -0.00148  -0.846  0.279  4.13  0.562
    1.0  2.522  0.450  -0.014  -0.00097  -0.798  0.314  2.90  0.622
    2.0  2.234  0.471  -0.037  -0.00064  -0.812  0.360  5.85  0.675
    """)


class BooreEtAl1993GSCUpperLimit(BooreEtAl1993GSCBest):
    """
    Implement equation used by the Geological Survey of Canada (GSC) for
    the 2010 Western Canada National Seismic Hazard Model. The class implements
    the model of David M. Boore, William B. Joyner, and Thomas E. Fumal
    ("Estimation of Response Spectra and Peak Accelerations from Western North
    American Earthquakes: An Interim Report", 1993, U.S. Geological Survey,
    Open File Report 93-509).
    Equation coefficients provided by GSC for the random horizontal component
    and corresponding to the 'Upper Limit' case (that is mean value + 0.7 nat
    log)
    """

    #: coefficient table provided by GSC
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT  c1     c2      c3      c4        c5     c6     c7    sigma
    pga  3.187  0.229   0.0    -0.00326  -0.778  0.162  5.57  0.529
    0.1  3.751  0.327  -0.098  -0.00395  -0.934  0.046  6.27  0.479
    0.2  3.764  0.309  -0.090  -0.00259  -0.924  0.190  7.02  0.495
    0.3  3.595  0.334  -0.070  -0.00202  -0.893  0.239  5.94  0.520
    0.5  3.280  0.384  -0.039  -0.00148  -0.846  0.279  4.13  0.562
    1.0  2.822  0.450  -0.014  -0.00097  -0.798  0.314  2.90  0.622
    2.0  2.534  0.471  -0.037  -0.00064  -0.812  0.360  5.85  0.675
    """)


class BooreEtAl1993GSCLowerLimit(BooreEtAl1993GSCBest):
    """
    Implement equation used by the Geological Survey of Canada (GSC) for
    the 2010 Western Canada National Seismic Hazard Model. The class implements
    the model of David M. Boore, William B. Joyner, and Thomas E. Fumal
    ("Estimation of Response Spectra and Peak Accelerations from Western North
    American Earthquakes: An Interim Report", 1993, U.S. Geological Survey,
    Open File Report 93-509).
    Equation coefficients provided by GSC for the random horizontal component
    and corresponding to the 'Lower Limit' case (that is mean value - 0.7 nat
    log)
    """

    #: coefficient table provided by GSC
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT  c1     c2      c3      c4        c5     c6     c7    sigma
    pga  2.587  0.229   0.0    -0.00326  -0.778  0.162  5.57  0.529
    0.1  3.151  0.327  -0.098  -0.00395  -0.934  0.046  6.27  0.479
    0.2  3.164  0.309  -0.090  -0.00259  -0.924  0.190  7.02  0.495
    0.3  2.995  0.334  -0.070  -0.00202  -0.893  0.239  5.94  0.520
    0.5  2.680  0.384  -0.039  -0.00148  -0.846  0.279  4.13  0.562
    1.0  2.222  0.450  -0.014  -0.00097  -0.798  0.314  2.90  0.622
    2.0  1.934  0.471  -0.037  -0.00064  -0.812  0.360  5.85  0.675
    """)
