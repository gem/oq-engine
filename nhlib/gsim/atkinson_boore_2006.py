# nhlib: A New Hazard Library
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
Module exports :class:`AtkinsonBoore2006`.
"""
from __future__ import division

import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g

from nhlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from nhlib.gsim.base import CoeffsTable
from nhlib import const
from nhlib.imt import PGA, PGV, SA


class AtkinsonBoore2006(BooreAtkinson2008):
    """
    Implements GMPE developed by Gail M. Atkinson and David M. Boore and
    published as "Earthquake Ground-Motion Prediction Equations for Eastern
    North America" (2006, Bulletin of the Seismological Society of America,
    Volume 96, No. 6, pages 2181-2205). This class implements only the 
    equations for stress parameter of 140 bars. The correction described in
    'Adjustment of Equations to Consider Alternative Stress Parameters',
    p. 2198, is not implemented.
    This class extends the BooreAtkinson2008 because it uses the same soil
    amplification function. Note that in the paper, the reported soil
    amplification function is the one used in a preliminary version of the
    Boore and Atkinson 2008 GMPE, while the one that should be used is the
    one described in the final paper. See comment in:
    http://www.daveboore.com/pubs_online/ab06_gmpes_programs_and_tables.pdf
    """
    #: Supported tectonic region type is stable continental, given
    #: that the equations have been derived for Eastern North America
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration, see paragraph
    #: 'Methodology and Model Parameters', p. 2182
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is horizontal
    #: :attr:`~nhlib.const.IMC.HORIZONTAL`, see paragraph 'Results', 
    #: pag 2190, and caption to table 6, p. 2192
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type is total, see table 6
    #: and 9, p. 2192 and 2202, respectively.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: Required site parameters is Vs30. 
    #: See paragraph 'Equations for soil sites', p. 2200
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameter is magnitude (see
    #: paragraph 'Methodology and Model Parameters', p. 2182)
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is Rrup.
    #: See paragraph 'Methodology and Model Parameters', p. 2182
    REQUIRES_DISTANCES = set(('rrup', ))
    
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <nhlib.gsim.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type.
        C_HR = self.COEFFS_HARD_ROCK[imt]
        C_BC = self.COEFFS_BC[imt]
        C_SR = self.COEFFS_SOIL_RESPONSE[imt]

        # clip distances to avoid singularity at 0
        rrup = self._clip_distances(dists)

        # compute factors required for mean value calculation
        f0 = self._compute_f0_factor(rrup)
        f1 = self._compute_f1_factor(rrup)
        f2 = self._compute_f2_factor(rrup)

        # compute pga for BC boundary (required for soil amplification
        # calculation on non-hard-rock sites)
        pga_bc = np.zeros_like(sites.vs30)
        self._compute_mean(self.COEFFS_BC[PGA()], f0, f1, f2, rup.mag,
                                    rrup, sites, sites.vs30 < 2000.0, pga_bc)
        pga_bc = (10**pga_bc) * 1e-2 / g

        # compute mean values for hard-rock sites (vs30 >= 2000),
        # and non-hard-rock sites (vs30 < 2000)
        mean = np.zeros_like(sites.vs30)
        self._compute_mean(C_HR, f0, f1, f2, rup.mag, rrup, sites,
                           sites.vs30 >= 2000.0, mean)
        self._compute_mean(C_BC, f0, f1, f2, rup.mag, rrup, sites,
                           sites.vs30 < 2000.0, mean)
        self._compute_soil_amplification(C_SR, sites, pga_bc, mean)

        # convert from base 10 to base e
        if imt == PGV():
            mean = np.log(10**mean)
        else:
            # convert from cm/s**2 to g
            mean = np.log((10**mean) * 1e-2 / g)

        stddevs = self._get_stddevs(stddev_types, num_sites=len(sites.vs30))

        return mean, stddevs

    def _clip_distances(self, dists):
        """
        Return array of distances with values clipped to 1. See end of
        paragraph 'Methodology and Model Parameters', p. 2182. The equations
        have a singularity for distance = 0, so that's why distances are
        clipped to 1.
        """
        rrup = dists.rrup
        rrup[rrup < 1] = 1

        return rrup

    def _compute_f0_factor(self, rrup):
        """
        Compute and return factor f0 - see equation (5), 6th term, p. 2191.
        """
        # f0 = max(log10(R0/rrup),0)
        f0 = np.log10(self.COEFFS_IMT_INDEPENDENT['R0'] / rrup)
        f0[f0 < 0] = 0.0

        return f0

    def _compute_f1_factor(self, rrup):
        """
        Compute and return factor f1 - see equation (5), 4th term, p. 2191
        """
        # f1 = min(log10(rrup),log10(R1))
        f1 = np.log10(rrup)
        logR1 = np.log10(self.COEFFS_IMT_INDEPENDENT['R1'])
        f1[f1 > logR1] = logR1

        return f1

    def _compute_f2_factor(self, rrup):
        """
        Compute and return factor f2, see equation (5), 5th term, pag 2191
        """
        # f2 = max(log10(rrup/R2),0)
        f2 = np.log10(rrup / self.COEFFS_IMT_INDEPENDENT['R2'])
        f2[f2 < 0] = 0.0

        return f2

    def _compute_mean(self, C, f0, f1, f2, mag, rrup, sites, idxs, mean):
        """
        Compute mean value (for a set of indexes) without site amplification
        terms. This is equation (5), p. 2191, without S term.
        """
        mean[idxs] = \
            C['c1'] + \
            C['c2'] * mag + \
            C['c3'] * (mag ** 2) + \
            (C['c4'] + C['c5'] * mag) * f1[idxs] + \
            (C['c6'] + C['c7'] * mag) * f2[idxs] + \
            (C['c8'] + C['c9'] * mag) * f0[idxs] + \
            C['c10'] * rrup[idxs]

    def _compute_soil_amplification(self, C, sites, pga_bc, mean):
        """
        Compute soil amplification, that is S term in equation (5), p. 2191,
        and add to mean values for non hard rock sites.
        """
        sal = self._get_site_amplification_linear(sites, C)
        sanl = self._get_site_amplification_non_linear(sites, pga_bc, C)

        idxs = sites.vs30 < 2000.0
        mean[idxs] = sal[idxs] + sanl[idxs]

    def _get_stddevs(self, stddev_types, num_sites):
        """
        Return total standard deviation (see table 6, p. 2192).
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)
        stddevs = [np.zeros(num_sites) + \
                   self.COEFFS_IMT_INDEPENDENT['std_total']
                   for _ in stddev_types]
        return stddevs

    #: Hard rock coefficents, table 6, pag 2192,
    COEFFS_HARD_ROCK = CoeffsTable(sa_damping=5, table="""\
    IMT     c1        c2         c3         c4        c5         c6        c7         c8         c9         c10
    5.00   -5.41E+00  1.71E+00  -9.01E-02  -2.54E+00  2.27E-01  -1.27E+00  1.16E-01   9.79E-01  -1.77E-01  -1.76E-04
    4.00   -5.79E+00  1.92E+00  -1.07E-01  -2.44E+00  2.11E-01  -1.16E+00  1.02E-01   1.01E+00  -1.82E-01  -2.01E-04
    3.13   -6.04E+00  2.08E+00  -1.22E-01  -2.37E+00  2.00E-01  -1.07E+00  8.95E-02   1.00E+00  -1.80E-01  -2.31E-04
    2.50   -6.17E+00  2.21E+00  -1.35E-01  -2.30E+00  1.90E-01  -9.86E-01  7.86E-02   9.68E-01  -1.77E-01  -2.82E-04
    2.00   -6.18E+00  2.30E+00  -1.44E-01  -2.22E+00  1.77E-01  -9.37E-01  7.07E-02   9.52E-01  -1.77E-01  -3.22E-04
    1.59   -6.04E+00  2.34E+00  -1.50E-01  -2.16E+00  1.66E-01  -8.70E-01  6.05E-02   9.21E-01  -1.73E-01  -3.75E-04
    1.25   -5.72E+00  2.32E+00  -1.51E-01  -2.10E+00  1.57E-01  -8.20E-01  5.19E-02   8.56E-01  -1.66E-01  -4.33E-04
    1.00   -5.27E+00  2.26E+00  -1.48E-01  -2.07E+00  1.50E-01  -8.13E-01  4.67E-02   8.26E-01  -1.62E-01  -4.86E-04
    0.794  -4.60E+00  2.13E+00  -1.41E-01  -2.06E+00  1.47E-01  -7.97E-01  4.35E-02   7.75E-01  -1.56E-01  -5.79E-04
    0.629  -3.92E+00  1.99E+00  -1.31E-01  -2.05E+00  1.42E-01  -7.82E-01  4.30E-02   7.88E-01  -1.59E-01  -6.95E-04
    0.500  -3.22E+00  1.83E+00  -1.20E-01  -2.02E+00  1.34E-01  -8.13E-01  4.44E-02   8.84E-01  -1.75E-01  -7.70E-04
    0.397  -2.44E+00  1.65E+00  -1.08E-01  -2.05E+00  1.36E-01  -8.43E-01  4.48E-02   7.39E-01  -1.56E-01  -8.51E-04
    0.315  -1.72E+00  1.48E+00  -9.74E-02  -2.08E+00  1.38E-01  -8.89E-01  4.87E-02   6.10E-01  -1.39E-01  -9.54E-04
    0.251  -1.12E+00  1.34E+00  -8.72E-02  -2.08E+00  1.35E-01  -9.71E-01  5.63E-02   6.14E-01  -1.43E-01  -1.06E-03
    0.199  -6.15E-01  1.23E+00  -7.89E-02  -2.09E+00  1.31E-01  -1.12E+00  6.79E-02   6.06E-01  -1.46E-01  -1.13E-03
    0.158  -1.46E-01  1.12E+00  -7.14E-02  -2.12E+00  1.30E-01  -1.30E+00  8.31E-02   5.62E-01  -1.44E-01  -1.18E-03
    0.125   2.14E-01  1.05E+00  -6.66E-02  -2.15E+00  1.30E-01  -1.61E+00  1.05E-01   4.27E-01  -1.30E-01  -1.15E-03
    0.100   4.80E-01  1.02E+00  -6.40E-02  -2.20E+00  1.27E-01  -2.01E+00  1.33E-01   3.37E-01  -1.27E-01  -1.05E-03
    0.079   6.91E-01  9.97E-01  -6.28E-02  -2.26E+00  1.25E-01  -2.49E+00  1.64E-01   2.14E-01  -1.21E-01  -8.47E-04
    0.063   9.11E-01  9.80E-01  -6.21E-02  -2.36E+00  1.26E-01  -2.97E+00  1.91E-01   1.07E-01  -1.17E-01  -5.79E-04
    0.050   1.11E+00  9.72E-01  -6.20E-02  -2.47E+00  1.28E-01  -3.39E+00  2.14E-01  -1.39E-01  -9.84E-02  -3.17E-04
    0.040   1.26E+00  9.68E-01  -6.23E-02  -2.58E+00  1.32E-01  -3.64E+00  2.28E-01  -3.51E-01  -8.13E-02  -1.23E-04
    0.031   1.44E+00  9.59E-01  -6.28E-02  -2.71E+00  1.40E-01  -3.73E+00  2.34E-01  -5.43E-01  -6.45E-02  -3.23E-05
    0.025   1.52E+00  9.60E-01  -6.35E-02  -2.81E+00  1.46E-01  -3.65E+00  2.36E-01  -6.54E-01  -5.50E-02  -4.85E-05
    pga     9.07E-01  9.83E-01  -6.60E-02  -2.70E+00  1.59E-01  -2.80E+00  2.12E-01  -3.01E-01  -6.53E-02  -4.48E-04
    pgv    -1.44E+00  9.91E-01  -5.85E-02  -2.70E+00  2.16E-01  -2.44E+00  2.66E-01   8.48E-02  -6.93E-02  -3.73E-04
    """)

    #: Coefficients for NEHRP BC boundary (Vs30 = 760 m/s), table 9, pag 2202
    COEFFS_BC = CoeffsTable(sa_damping=5, table="""\
    IMT     c1        c2         c3         c4        c5         c6        c7         c8         c9         c10
    5.00   -4.85E+00  1.58E+00  -8.07E-02  -2.53E+00  2.22E-01  -1.43E+00  1.36E-01   6.34E-01  -1.41E-01  -1.61E-04
    4.00   -5.26E+00  1.79E+00  -9.79E-02  -2.44E+00  2.07E-01  -1.31E+00  1.21E-01   7.34E-01  -1.56E-01  -1.96E-04
    3.13   -5.59E+00  1.97E+00  -1.14E-01  -2.33E+00  1.91E-01  -1.20E+00  1.10E-01   8.45E-01  -1.72E-01  -2.45E-04
    2.50   -5.80E+00  2.13E+00  -1.28E-01  -2.26E+00  1.79E-01  -1.12E+00  9.54E-02   8.91E-01  -1.80E-01  -2.60E-04
    2.00   -5.85E+00  2.23E+00  -1.39E-01  -2.20E+00  1.69E-01  -1.04E+00  8.00E-02   8.67E-01  -1.79E-01  -2.86E-04
    1.59   -5.75E+00  2.29E+00  -1.45E-01  -2.13E+00  1.58E-01  -9.57E-01  6.76E-02   8.67E-01  -1.79E-01  -3.43E-04
    1.25   -5.49E+00  2.29E+00  -1.48E-01  -2.08E+00  1.50E-01  -9.00E-01  5.79E-02   8.21E-01  -1.72E-01  -4.07E-04
    1.00   -5.06E+00  2.23E+00  -1.45E-01  -2.03E+00  1.41E-01  -8.74E-01  5.41E-02   7.92E-01  -1.70E-01  -4.89E-04
    0.794  -4.45E+00  2.12E+00  -1.39E-01  -2.01E+00  1.36E-01  -8.58E-01  4.98E-02   7.08E-01  -1.59E-01  -5.75E-04
    0.629  -3.75E+00  1.97E+00  -1.29E-01  -2.00E+00  1.31E-01  -8.42E-01  4.82E-02   6.77E-01  -1.56E-01  -6.76E-04
    0.500  -3.01E+00  1.80E+00  -1.18E-01  -1.98E+00  1.27E-01  -8.47E-01  4.70E-02   6.67E-01  -1.55E-01  -7.68E-04
    0.397  -2.28E+00  1.63E+00  -1.05E-01  -1.97E+00  1.23E-01  -8.88E-01  5.03E-02   6.84E-01  -1.58E-01  -8.59E-04
    0.315  -1.56E+00  1.46E+00  -9.31E-02  -1.98E+00  1.21E-01  -9.47E-01  5.58E-02   6.50E-01  -1.56E-01  -9.55E-04
    0.251  -8.76E-01  1.29E+00  -8.19E-02  -2.01E+00  1.23E-01  -1.03E+00  6.34E-02   5.81E-01  -1.49E-01  -1.05E-03
    0.199  -3.06E-01  1.16E+00  -7.21E-02  -2.04E+00  1.22E-01  -1.15E+00  7.38E-02   5.08E-01  -1.43E-01  -1.14E-03
    0.158   1.19E-01  1.06E+00  -6.47E-02  -2.05E+00  1.19E-01  -1.36E+00  9.16E-02   5.16E-01  -1.50E-01  -1.18E-03
    0.125   5.36E-01  9.65E-01  -5.84E-02  -2.11E+00  1.21E-01  -1.67E+00  1.16E-01   3.43E-01  -1.32E-01  -1.13E-03
    0.100   7.82E-01  9.24E-01  -5.56E-02  -2.17E+00  1.19E-01  -2.10E+00  1.48E-01   2.85E-01  -1.32E-01  -9.90E-04
    0.079   9.67E-01  9.03E-01  -5.48E-02  -2.25E+00  1.22E-01  -2.53E+00  1.78E-01   1.00E-01  -1.15E-01  -7.72E-04
    0.063   1.11E+00  8.88E-01  -5.39E-02  -2.33E+00  1.23E-01  -2.88E+00  2.01E-01  -3.19E-02  -1.07E-01  -5.48E-04
    0.050   1.21E+00  8.83E-01  -5.44E-02  -2.44E+00  1.30E-01  -3.04E+00  2.13E-01  -2.10E-01  -9.00E-02  -4.15E-04
    0.040   1.26E+00  8.79E-01  -5.52E-02  -2.54E+00  1.39E-01  -2.99E+00  2.16E-01  -3.91E-01  -6.75E-02  -3.88E-04
    0.031   1.19E+00  8.88E-01  -5.64E-02  -2.58E+00  1.45E-01  -2.84E+00  2.12E-01  -4.37E-01  -5.87E-02  -4.33E-04
    0.025   1.05E+00  9.03E-01  -5.77E-02  -2.57E+00  1.48E-01  -2.65E+00  2.07E-01  -4.08E-01  -5.77E-02  -5.12E-04
    pga     5.23E-01  9.69E-01  -6.20E-02  -2.44E+00  1.47E-01  -2.34E+00  1.91E-01  -8.70E-02  -8.29E-02  -6.30E-04
    pgv    -1.66E+00  1.05E+00  -6.04E-02  -2.50E+00  1.84E-01  -2.30E+00  2.50E-01   1.27E-01  -8.70E-02  -4.27E-04
    """)

    # Soil response coefficients, table 8, pag 2201.
    COEFFS_SOIL_RESPONSE = CoeffsTable(sa_damping=5, table="""\
    IMT     blin    b1      b2
    5.00   -0.752  -0.300   0
    4.00   -0.745  -0.310   0
    3.13   -0.740  -0.330   0
    2.00   -0.730  -0.375   0
    1.59   -0.726  -0.395   0
    1.00   -0.700  -0.440   0
    0.769  -0.690  -0.465  -0.002
    0.625  -0.670  -0.480  -0.031
    0.500  -0.600  -0.495  -0.060
    0.400  -0.500  -0.508  -0.095
    0.313  -0.445  -0.513  -0.130
    0.250  -0.390  -0.518  -0.160
    0.200  -0.306  -0.521  -0.185
    0.159  -0.280  -0.528  -0.185
    0.125  -0.260  -0.560  -0.140
    0.100  -0.250  -0.595  -0.132
    0.079  -0.232  -0.637  -0.117
    0.063  -0.249  -0.642  -0.105
    0.050  -0.286  -0.643  -0.105
    0.040  -0.314  -0.609  -0.105
    0.031  -0.322  -0.618  -0.108
    0.025  -0.330  -0.624  -0.115
    pga    -0.361  -0.641  -0.144
    pgv    -0.600  -0.495  -0.060
    """)

    #: IMT-independent coefficients. std_total is the total standard deviation,
    #: see Table 6, pag 2192 and Table 9, pag 2202. R0, R1, R2 are coefficients
    #: required for mean calculation - see equation (5) pag 2191. v1, v2, Vref
    #: are coefficients required for soil response calculation, see table 8,
    #: p. 2201
    COEFFS_IMT_INDEPENDENT = {
        'std_total': 0.30,
        'R0': 10.0,
        'R1': 70.0,
        'R2': 140.0,
        'v1': 180.0,
        'v2': 300.0,
        'Vref': 760.0
    }
