# The Hazard Library
# Copyright (C) 2013 GEM Foundation
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
Module exports :class:`AtkinsonBoore1995GSC`.
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class AtkinsonBoore1995GSC(GMPE):
    """
    Implement equation used by the Geological Survey of Canada (GSC) for
    the Canada National Seismic Hazard Model. The equation fits the table
    values defined by Gail M. Atkinson and David M. Boore in "Ground-Motion
    Relations for Eastern North America", Bullettin of the Seismological
    Society of America, Vol. 85, No. 1, pp. 17-30, February 1995. Table of
    coefficients were provided by GSC.
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
        rhypo = dists.rhypo
        rhypo[rhypo < 10] = 10

        # functional form as explained in 'Youngs_fit_to_AB95lookup.doc'
        f1 = np.minimum(np.log(rhypo), np.log(70.))
        f2 = np.maximum(np.log(rhypo / 130.), 0)
        mean = (
            C['c1'] + C['c2'] * rup.mag + C['c3'] * rup.mag ** 2 +
            (C['c4'] + C['c5'] * rup.mag) * f1 +
            (C['c6'] + C['c7'] * rup.mag) * f2 +
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
    IMT      c1          c2           c3           c4          c5           c6          c7           c8
    pga     -0.1329E+01  0.1272E+01  -0.8240E-01  -0.2556E+01  0.1722E+00  -0.1960E+01  0.1746E+00  -0.4535E-02
    0.0500  -0.1538E+01  0.1465E+01  -0.8818E-01  -0.2297E+01  0.1360E+00  -0.2466E+01  0.1475E+00  -0.4297E-02
    0.0769  -0.2269E+01  0.1423E+01  -0.7964E-01  -0.2088E+01  0.1260E+00  -0.1623E+01  0.9561E-01  -0.4684E-02
    0.1266  -0.3481E+01  0.1612E+01  -0.9036E-01  -0.2020E+01  0.1238E+00  -0.1242E+01  0.6531E-01  -0.3972E-02
    0.2000  -0.5487E+01  0.1932E+01  -0.1029E+00  -0.1818E+01  0.9797E-01  -0.1076E+01  0.6075E-01  -0.3325E-02
    0.3125  -0.7567E+01  0.2284E+01  -0.1193E+00  -0.1734E+01  0.8814E-01  -0.9551E+00  0.4392E-01  -0.2570E-02
    0.5000  -0.9476E+01  0.2503E+01  -0.1231E+00  -0.1631E+01  0.7610E-01  -0.1049E+01  0.6224E-01  -0.1959E-02
    0.7692  -0.1060E+02  0.2470E+01  -0.1086E+00  -0.1539E+01  0.6442E-01  -0.9642E+00  0.5758E-01  -0.1640E-02
    1.2500  -0.1159E+02  0.2470E+01  -0.1032E+00  -0.1504E+01  0.5929E-01  -0.8648E+00  0.4812E-01  -0.1375E-02
    2.0000  -0.1321E+02  0.2945E+01  -0.1567E+00  -0.1864E+01  0.1162E+00  -0.7653E+00  0.2729E-01  -0.9921E-03
    """)
