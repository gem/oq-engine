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

from nhlib.gsim.base import GMPE, CoeffsTable
from nhlib import const
from nhlib.imt import PGA, PGV, SA


class AtkinsonBoore2006(GMPE):
    """
    Implements GMPE developed by Gail M. Atkinson and David M. Boore
    and published as "Earthquake Ground-Motion Prediction Equations
    for Eastern North America" (2006, Bulletin of the Seismological
    Society of America, Volume 96, No. 6, pages 2181-2205).
    This class implements only the equations for stress parameter of
    140 bars. The correction described in 'Adjustment of Equations
    to Consider Alternative Stress Parameters', pag 2198, is not
    implemented.
    It also implements the correction as described in the 'Erratum'
    (2007, Bulletin of the Seismological Society of America,
    Volume 97, No. 3, page 1032).
    """
    #: Supported tectonic region type is stable continental, given
    #: that the equations have been derived for Eastern North America
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration, see paragraph
    #: 'Methodology and Model Parameters', pag 2182
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is horizontal
    #: :attr:`~nhlib.const.IMC.HORIZONTAL`, see paragraph 'Results', 
    #: pag 2190, and caption to table 6, pag 2192
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type is total, see table 6
    #: and 9, pag 2192 and 2202, respectively.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: Required site parameters is Vs30. 
    #: See paragraph 'Equations for soil sites', pag 2200
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameter is magnitude (see
    #: paragraph 'Methodology and Model Parameters', pag 2182)
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is Rrup.
    #: See paragraph 'Methodology and Model Parameters', pag 2182
    REQUIRES_DISTANCES = set(('rrup', ))
    
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <nhlib.gsim.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)
                   
        #: Total sigma is constant for all frequencies
        stddevs = [np.zeros_like(sites.vs30) + COEFFS_IMT_INDEPENDENT['std_total'] for _ in stddev_types]
        means = np.zeros_like(sites.vs30)
        
        #: extracting dictionaries of coefficients specific to required
        #: intensity measure type.
        C_HARD_ROCK = self.COEFFS_HARD_ROCK[imt]
        C_ROCK = self.COEFFS_ROCK[imt]
        C_STRESS = self.COEFFS_STRESS[imt]
        C_SOIL_RESPONSE = self.COEFFS_SOIL_RESPONSE[imt]
        
        #: minimum allowed distance is 1 km. See end of
        #: paragraph 'Methodology and Model Parameters',
        #: pag 2182
        #: the equations have a singularity for distance = 0,
        #: so that's why distances are clipped to 1.
        dists = rup.rrup
        dists[dists < 1] = 1
        
        #: compute factor f0, see equation (5), pag 2191
        #: f0 = max(log(R0/rrup),0)
        f0 = np.log(COEFFS_IMT_INDEPENDENT['R0'] / dists)
        f0[f0 < 0] = 0.0
        
        #: compute factor f1, see equation (5), pag 2191
        #: f1 = min(log(rrup),log(R1))
        f1 = np.log(dists)
        logR1 = np.log(COEFFS_IMT_INDEPENDENT['R1'])
        f1[f1 > logR1] = logR1
        
        #: compute factor f2, see equation (5), pag 2191
        #: f2 = max(log(rrup/R2),0)
        f2 = np.log(dists / COEFFS_IMT_INDEPENDENT['R2'])
        f2[f2 < 0] = 0.0
        
        #: compute mean value for hard rock sites (Vs30 >= 2000),
        #: see paragraph 'Conclusions', pag 2203
        #: equation (5), pag 2191, with last term S = 0
        idx = sites.vs30 >= 2000.0
        means[idx] = C_HARD_ROCK['c1'] + C_HARD_ROCK['c2'] * rup.mag + C_HARD_ROCK['c3'] * (rup.mag ** 2) +\
                    (C_HARD_ROCK['c4'] + C_HARD_ROCK['c5'] * rup.mag) * f1[idx] +\
                    (C_HARD_ROCK['c6'] + C_HARD_ROCK['c7'] * rup.mag) * f2[idx] +\
                    (C_HARD_ROCK['c8'] + C_HARD_ROCK['c9'] * rup.mag) * f0[idx] +\
                    C_HARD_ROCK['c10'] * dists[idx]
                    
        #: compute mean value for non-hard rock sites
        #: equation (5), pag 2191, with last term S
        #: given by equations (7a) (7b), pag 2200
        idx = sites.vs30 <= 2000.0
        
        # compute soil amplification
        
        #: compute non-linear slope, equations (8a) to (8d), pag 2200
        
        #: equation (8d), bnl has zero value for vs30 > Vref = 760.0
        bnl = np.zeros_like(sites.vs30)
        
        #: equation (8a)
        bnl[sites.vs30 <= COEFFS_IMT_INDEPENDENT['v1']] = C_SOIL_RESPONSE['b1']
        
        #: equation (8b)
        idx1 = sites.vs30
        
        
        
        
        
        
        means[idx] = COEFFS_ROCK['c1'] + COEFFS_ROCK['c2'] * rup.mag + COEFFS_ROCK['c3'] * (rup.mag ** 2) +\
                    (COEFFS_ROCK['c4'] + COEFFS_ROCK['c5'] * rup.mag) * f1[idx] +\
                    (COEFFS_ROCK['c6'] + COEFFS_ROCK['c7'] * rup.mag) * f2[idx] +\
                    (COEFFS_ROCK['c8'] + COEFFS_ROCK['c9'] * rup.mag) * f0[idx] +\
                    COEFFS_ROCK['c10'] * dists[idx]
        
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
    COEFFS_ROCK = CoeffsTable(sa_damping=5, table="""\
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
    
    #: Stress adjustment factors coefficients, table 7, pag 2201,
    COEFFS_STRESS = CoeffsTable(sa_damping=5, table="""\
    IMT     delta  Ml    Mh
    5.00    0.15   6.00  8.50
    4.00    0.15   5.75  8.37
    3.13    0.15   5.50  8.25
    2.50    0.15   5.25  8.12
    2.00    0.15   5.00  8.00
    1.59    0.15   4.84  7.70
    1.25    0.15   4.67  7.45
    1.00    0.15   4.50  7.20
    0.794   0.15   4.34  6.95
    0.629   0.15   4.17  6.70
    0.500   0.15   4.00  6.50
    0.397   0.15   3.65  6.37
    0.315   0.15   3.30  6.25
    0.251   0.15   2.90  6.12
    0.199   0.15   2.50  6.00
    0.158   0.15   1.85  5.84
    0.125   0.15   1.15  5.67
    0.100   0.15   0.50  5.50
    0.079   0.15   0.34  5.34
    0.063   0.15   0.17  5.17
    0.050   0.15   0.00  5.00
    0.040   0.15   0.00  5.00
    0.031   0.15   0.00  5.00
    0.025   0.15   0.00  5.00
    pga     0.15   0.50  5.50
    pgv     0.11   2.00  5.50
    """)
    
    
    #: Soil response coefficients, table 8, pag 2201.
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
    
    #: IMT-independent coefficients
    #: std is the total standard deviation
    #: see Table 6, pag 2192 and Table 9, pag 2202.
    #: R0, R1, R2 are required coefficients
    #: for mean calculation - see equation (5) pag 2191.
    #: v1, v2, Vref are coefficients for soil response calculation
    #: see table 8, pag 2201
    COEFFS_IMT_INDEPENDENT = {
        'std_total': 0.30,
        'R0': 10.0,
        'R1': 70.0,
        'R2': 140.0,
        'v1': 180.0,
        'v2': 300.0,
        'Vref': 760.0
    }