# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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
Module exports :class:`TavakoliPezeshk2005`.
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class TavakoliPezeshk2005(GMPE):
    """
    Implements the GMPE developed by B. Tavakoli and S. Pezeshk in 2005
    and published as "Empirical-Stochastic Ground-Motion Prediction for
    Eastern North America" (2005, Bull. Seism. Soc. Am., Volume 95, No. 6,
    pages 2283-2296).
    """
    #: Supported tectonic region type is stable continental crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are peak ground acceleration
    #: and spectral acceleration, see abstract
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.GMRotI50`, see paragraph
    #: 'Response Variables', page 100 and table 8, pag 121.
    # TODO
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotI50

    #: Supported standard deviation types is total, see equation 23, pag 2291.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
    ])

    #: This GMPE doesn't require site parameters since it has been developed
    #: for hard rock sites (see page 2290)
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters is magnitude
    #: See equation 18 page page 2291
    REQUIRES_RUPTURE_PARAMETERS = set(('mag'))

    #: Required distance measure is Rrup.
    #: See equation 18 page page 2291
    REQUIRES_DISTANCES = set(('rrup'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients
        C = self.COEFFS[imt]

        # computing the magnitude term. Equation 19, page 2291
        f1 = self._compute_magnitude_scaling_term(C, rup.mag)

        # computing the geometrical spreading term. Equation 20, page 2291
        f2 = self._compute_geometrical_spreading_term(C, dists.rrup)

        # computing the anelastic attenuation term. Equation 21, page 2291
        f3 = self._compute_anelastic_attenuation_term(C, dists.rrup, rup.mag)

        # computing the mean ln(IMT) using equation 18 at page 2290
        mean = f1 + f2 + f3

        # computing the total standard deviation
        stddevs = self._get_stddevs(C, stddev_types, num_sites=len(dists.rrup),
                                    mag=rup.mag)

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites, mag):
        """
        Returns standard deviation as defined in equation 23, page 2291
        (Tavakoli and Pezeshk, 2005)
        """
        stddevs = []
        sigma = (C['c14'] + C['c15'] * mag) if mag < 7.2 else C['c16']
        vals = sigma * np.ones((num_sites))
        stddevs.append(vals)
        return stddevs

    def _compute_magnitude_scaling_term(self, C, mag):
        """
        Compute magnitude scaling term as defined in equation 19, page 2291
        (Tavakoli and Pezeshk, 2005)
        """
        return C['c1'] + C['c2'] * mag + (C['c3'] * mag) ** 2.5

    def _compute_geometrical_spreading_term(self, C, rrup):
        """
        Compute magnitude scaling term as defined in equation 19, page 2291
        (Tavakoli and Pezeshk, 2005)
        """
        f2 = np.ones_like(rrup)
        idx1 = np.nonzero(rrup <= 70.)
        idx2 = np.nonzero((rrup > 70.) & (rrup <= 130.))
        idx3 = np.nonzero(rrup > 130.)

        f2[idx1] = (C['c9'] * np.log(rrup[idx1] + 4.5))
        f2[idx2] = (C['c10'] * np.log(rrup[idx3]/70.) +
                    C['c9'] * np.log(rrup[idx3] + 4.5))
        f2[idx3] = (C['c11'] * np.log(rrup[idx3]/130.) +
                    C['c10'] * np.log(rrup[idx3]/70.) +
                    C['c9'] * np.log(rrup[idx3] + 4.5))
        return f2

    def _compute_anelastic_attenuation_term(self, C, rrup, mag):
        """
        Compute magnitude-distance scaling term as defined in equation 21,
        page 2291 (Tavakoli and Pezeshk, 2005)
        """
        r = (rrup**2. + (C['c5'] * np.exp(C['c6'] * mag +
                                          C['c7'] * (8.5 - mag)**2.))**2.)**.5
        f3 = ((C['c4'] + C['c13'] * mag) * np.log(r) +
              (C['c8'] + C['c12'] * mag) * r)
        return f3

    #: Coefficient table is constructed from an excel spreadsheet available
    #: on Pezeshk's website http://www.ce.memphis.edu/pezeshk
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT    c1         c2         c3          c4          c5          c6          c7          c8          c9         c10        c11         c12        c13        c14         c15        c16
pga    1.139E+00  6.228E-01  -4.834E-02  -1.807E+00  -6.516E-01  4.465E-01  -2.933E-05  -4.045E-03   9.456E-03  1.410E+00  -9.611E-01  4.315E-04  1.332E-04  1.205E+00  -1.109E-01  4.091E-01
0.05   1.823E+00  5.333E-01  -4.748E-02  -1.631E+00  -5.672E-01  4.538E-01   7.771E-03  -4.907E-03  -3.139E-03  9.797E-01  -9.386E-01  5.121E-04  9.301E-04  1.216E+00  -1.080E-01  4.413E-01
0.08   6.826E-01  7.428E-01  -2.928E-02  -1.715E+00  -7.562E-01  4.601E-01  -9.677E-04  -4.941E-03  -5.500E-03  1.135E+00  -9.156E-01  4.822E-04  7.331E-04  1.224E+00  -1.081E-01  4.494E-01
0.10   8.692E-01  6.070E-01  -4.736E-02  -1.522E+00  -7.044E-01  4.491E-01  -6.188E-03  -4.702E-03  -4.239E-03  1.039E+00  -9.129E-01  4.108E-04  3.584E-04  1.232E+00  -1.081E-01  4.562E-01
0.15   2.383E+00  5.009E-01  -6.422E-02  -1.732E+00  -9.763E-01  4.137E-01   6.598E-03  -4.805E-03   3.928E-03  1.506E+00  -8.650E-01  3.642E-04  6.841E-04  1.240E+00  -1.082E-01  4.643E-01
0.20  -5.476E-01  8.570E-01  -2.622E-02  -1.684E+00  -8.607E-01  4.332E-01   2.786E-03  -3.655E-03  -2.025E-03  1.643E+00  -9.252E-01  1.615E-04  6.434E-04  1.240E+00  -1.082E-01  4.691E-01
0.30  -5.130E-01  6.673E-01  -4.431E-02  -1.421E+00  -4.695E-01  4.681E-01   1.076E-02  -5.407E-03   6.436E-03  1.519E+00  -9.153E-01  4.324E-04  2.870E-04  1.260E+00  -1.088E-01  4.788E-01
0.50   2.403E-01  6.106E-01  -7.889E-02  -1.548E+00  -8.438E-01  4.145E-01   7.889E-03  -3.648E-03  -2.654E-04  1.592E+00  -8.586E-01  2.770E-04  1.457E-04  1.275E+00  -1.073E-01  5.051E-01
0.75  -6.789E-01  6.659E-01  -8.304E-02  -1.481E+00  -7.340E-01  4.347E-01   9.531E-03  -3.374E-03  -1.189E-03  1.546E+00  -7.839E-01  2.454E-04  5.470E-04  1.276E+00  -1.050E-01  5.222E-01
1.00  -1.550E+00  7.644E-01  -8.585E-02  -1.491E+00  -9.409E-01  4.238E-01  -5.836E-03  -2.088E-03   3.298E-03  1.519E+00  -7.568E-01  1.166E-04  7.589E-04  1.275E+00  -1.029E-01  5.368E-01
1.50  -2.296E+00  7.941E-01  -8.842E-02  -1.453E+00  -8.860E-01  4.122E-01   8.299E-03  -3.272E-03   2.506E-03  1.706E+00  -7.688E-01  2.329E-04  1.656E-04  1.268E+00  -9.990E-02  5.509E-01
2.00  -2.704E+00  8.053E-01  -9.294E-02  -1.444E+00  -9.235E-01  4.077E-01   2.062E-02  -2.143E-03   2.301E-03  1.426E+00  -7.551E-01  2.138E-04  3.908E-04  1.264E+00  -9.780E-02  5.617E-01
3.00  -2.421E+00  8.008E-01  -1.077E-01  -1.648E+00  -8.976E-01  4.368E-01   1.675E-02  -2.033E-03   3.576E-03  1.934E+00  -8.183E-01  1.158E-04  3.983E-04  1.257E+00  -9.520E-02  5.729E-01
4.00  -3.685E+00  8.166E-01  -1.177E-01  -1.463E+00  -8.448E-01  4.249E-01   1.135E-02  -1.719E-03  -3.345E-03  1.689E+00  -7.374E-01  1.100E-04  3.592E-04  1.254E+00  -9.260E-02  5.893E-01    
""")
