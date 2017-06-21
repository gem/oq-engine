# -*- coding: utf-8 -*-

# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
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
Module exports :class:`YenierAtkinson2015`.
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class YenierAtkinson2015(GMPE):
        """
        Implements GMPE developed by Emrah Yenier and Gail M. Atkinson
        and published as "Regionally Adjustable Generic Ground-Motion Prediction 
        Equation Based on Equivalent Point-Source Simulations: Application to Central 
        and Eastern North America" (2015, Bulletin of the Seismological Society of America,
        Volume 105, No. 4, pages 1989-2009).
        """
        
        #: Define for tectonic region type stable shallow crust. 
        DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

        #: Supported intensity measure types are spectral acceleration,
        #: peak ground velocity and peak ground acceleration, see pag 1990.
        DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
               PGA,
               PGV,
               SA
        ])

        #: Supported intensity measure component is orientation-independent
        #: measure :attr:`~openquake.hazardlib.const.IMC.GMRotI50`.
        DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotI50
        
        #: Defined for standard deviation types inter-event, intra-event
        #: and total.
        DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
                const.StdDev.TOTAL,
                const.StdDev.INTER_EVENT,
                const.StdDev.INTRA_EVENT])	

        #: Required site parameters is Vs30.
        #: See paragraph 'Functional Form of the Generic GMPE', pag 1992.
        REQUIRES_SITES_PARAMETERS = set(('vs30', ))
       
        #: Required rupture parameters are magnitude.
        REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

        #: Required distance measure is rrup.
        #: See paragraph 'Functional Form of the Generic GMPE', pag 1991.
        REQUIRES_DISTANCES = set(('rrup', ))

        def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
                """
                See :meth:`superclass method
                <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
                for spec of input and result values.
                """
                # extracting dictionary of coefficients specific to required
                # intensity measure type.
                C = self.COEFFS[imt]
                C_SA = self.COEFFS_STRESS_ADJUSTMENT[imt]
        
                # compute PGA on rock conditions - needed to compute non-linear
                # site amplification term
                pga4nl = self._get_pga_on_rock(rup, dists, C, C_SA)
       
                # Computes equation (1) (see pag 1990). 
                # The fourth term, site amplification is computed as given in equation (10), 
                # that is the sum of a linear term (equation 11) and a non-linear one (equations
                # 12 and 13)
                # Note: The third and fifth terms are not incorporated in this implementation.
                if imt == PGA():
                    # avoid recomputing PGA on rock, just add site terms
                    mean = pga4nl + \
                        self._get_site_amplification_linear(sites.vs30, C) + \
                        self._get_site_amplification_non_linear(sites.vs30, pga4nl, C)
                else:
                    mean = self._compute_distance_scaling(rup, dists, C) + \
                        self._compute_magnitude_scaling(rup, C) + \
                        self._compute_stress_adjustment(rup, C_SA) + \
                        self._get_site_amplification_linear(sites.vs30, C) + \
                        self._get_site_amplification_non_linear(sites.vs30, pga4nl, C)

                stddevs = self._get_stddevs(C, stddev_types, num_sites=len(sites.vs30))
        
                return mean, stddevs
        
        def _get_stddevs(self, C, stddev_types, num_sites):
                """
                Return standard deviations as defined in table 8, pag 121.
                """
                stddevs = []
                for stddev_type in stddev_types:
                    assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                    if stddev_type == const.StdDev.TOTAL:
                        stddevs.append(C['std'] + np.zeros(num_sites))
                    elif stddev_type == const.StdDev.INTRA_EVENT:
                        stddevs.append(C['sigma'] + np.zeros(num_sites))
                    elif stddev_type == const.StdDev.INTER_EVENT:
                        stddevs.append(C['tau'] + np.zeros(num_sites))
                return stddevs
    
        def _compute_distance_scaling(self, rup, dists, C):
                """
                Compute distance scaling term, equations (5), (6), (7), and (8), pag 1991.
                """
                # Computing geometrical spreading, Fz.
                h = 10 ** (-0.405 + 0.235 * rup.mag)
                R = np.sqrt(np.amin(dists.rrup) ** 2 + (h ** 2))
                Rref = np.sqrt(1 + (h ** 2))
                b1 = -1.3
                b2 = -0.5
                Rt = 50		# Transition distance of 50km.
                if R <= Rt:
                        Z = R ** b1
                else:
                        Z = (Rt ** b1) * ((R/Rt) ** b2)
                return np.log(Z) + ((C['b3'] + (C['b4'] * rup.mag)) * np.log(R / Rref))
        
        def _compute_magnitude_scaling(self, rup, C):
                """
                Compute magnitude-scaling term, equation (3), pag 1991.
                """
                # Computing Fm from equation (3), used in Fe. 
                if rup.mag <= C['Mh']:
                    return C['e0'] + \
                        C['e1'] * (rup.mag - C['Mh']) + \
                        C['e2'] * (rup.mag - C['Mh']) ** 2
                else:
                    return C['e0'] + \
                        C['e1'] * (rup.mag - C['Mh'])

        def _compute_stress_adjustment(self, rup, C_SA):
                """
                Compute stress adjustment term, equation (4), pag 1991.
                """
                # delta is the reference stress in bar
                if rup.stress_drop <= 100.:
                        e_ref_stress = C_SA['s0'] + C_SA['s1'] * rup.mag + \
                                C_SA['s2'] * (rup.mag ** 2) + \
                                C_SA['s3'] * (rup.mag ** 3) + \
                                C_SA['s4'] * (rup.mag ** 4)
                else:
                        e_ref_stress = C_SA['s5'] + C_SA['s6'] * rup.mag + \
                                C_SA['s7'] * (rup.mag ** 2) + \
                                C_SA['s8'] * (rup.mag ** 3) + \
                                C_SA['s9'] * (rup.mag ** 4)
                        
                return e_ref_stress * np.log(ref_stress/100)

        def _get_site_amplification_linear(self, vs30, C):
                """
                Compute site amplification linear term,
                equation (11), pag 1992.
                """
                # Analyzes each element of vs30 separately and returns an 
                # array with the same dimensions as vs30.
                cvc = np.ones_like(vs30)
                for i in range(len(cvc)):
                        cvc[i] = C['Vc']
                
                return_array = np.ones_like(vs30)

                for i in range(len(vs30)):
                        if vs30[i] <= cvc[i]:
                                return_array[i] = C['c'] * np.log(vs30[i] / C['vref'])
                        else:
                                return_array[i] = C['c'] * np.log(cvc[i] / C['vref'])
                return return_array
                
        def _get_pga_on_rock(self, rup, dists, C, C_SA):
                """
                Compute and return PGA on rock conditions (that is vs30 = 760.0 m/s).
                This is needed to compute non-linear site amplification term.
                """
                # Median PGA in g for vs30 = 760.0, without site amplification,
                # that is equation (1) pag 1990, without Fs. 
                C_pga  = self.COEFFS[PGA()]
                C_pgsa = self.COEFFS_STRESS_ADJUSTMENT[PGA()]
                pga4nl = self._compute_distance_scaling(rup, dists, C_pga) + \
                         self._compute_magnitude_scaling(rup, C_pga) + \
                         self._compute_stress_adjustment(rup, C_pgsa)

                return pga4nl

        def _get_site_amplification_non_linear(self, vs30, pga4nl, C):
                """
                Compute non-linear site amplification,
                equation (12), pag 1992.
                """		                
                f2 = self._compute_non_linear_slope(vs30, C)
                return C['f1'] + self._compute_non_linear_term(pga4nl, f2, C)
                
        def _compute_non_linear_slope(self, vs30, C):
                """
                Compute non-linear slope factor,
                equation (12), pag 1992.
                """
                # Computing f2, equation 13.
                return C['f4'] * ((np.exp(C['f5'] * (np.minimum(vs30, 760) - 360))) - \
                        (np.exp(C['f5'] * (760 - 360))))

        def _compute_non_linear_term(self, pga4nl, f2, C):
                """
                Compute non-linear term,
                equation (12), pag 1992.
                """
                return f2 * np.log((np.exp(pga4nl) + C['f3']) / C['f3'])


        # Coefficient table is constructed from values in table 2 (pag 1996)
        # and Boore etal (2014) NGA-West2 GMPE. Spectral acceleration is defined for 
        # damping of 5%, see paragraph 'Introduction' page 1990.
        # b3, b4 are the period-dependent distance scaling coefficients.
        # e0, e1, e2, e3 are the period-dependent magnitude scaling coefficients.
        # sigma, tau, std are the intra-event uncertainty, inter-event
        # uncertainty, and total standard deviation, respectively.

        COEFFS = CoeffsTable(sa_damping=5, table="""\
                imt 	Mh 		e0 		    e1 		e2 			e3 		b3 			b4      c           Vc      vref    f1  f3      f4          f5			sigma tau   std
                                0.010	5.85	2.23E+0	    6.87E-1	-1.36E-1	7.64E-1	-6.21E-1	6.06E-2 -6.04E-01	1500.2	760	    0   0.1	    -1.48E-01	-7.01E-03	0.502 0.262 0.566
                0.020	5.90	2.38E+0	    7.00E-1	-1.07E-1	7.49E-1	-6.38E-1	6.25E-2 -5.74E-01	1500.36	760	    0   0.1	    -1.47E-01	-7.28E-03	0.502 0.262 0.566
                0.025	6.00	2.56E+0	    6.84E-1	-9.42E-2	7.41E-1	-6.31E-1	6.10E-2 -5.55E-01	1501.04	760	    0	0.1	    -1.50E-01	-7.36E-03	0.0	  0.0   0.0
                0.030	6.15	2.81E+0	    6.61E-1	-9.09E-2	7.39E-1	-6.03E-1	5.64E-2 -5.34E-01	1502.95	760	    0	0.1	    -1.55E-01	-7.35E-03	0.507 0.274 0.576
                0.040	5.75	2.73E+0	    7.03E-1	-1.09E-1	7.38E-1	-5.48E-1	4.82E-2 -4.91E-01	1503.35	760 	0	0.1	    -1.68E-01	-6.98E-03	0.0	  0.0   0.0
                0.050	5.35	2.56E+0	    7.19E-1	-1.64E-1	7.54E-1	-5.10E-1	4.28E-2 -4.58E-01	1501.42	760	    0	0.1	    -1.96E-01	-6.47E-03	0.516 0.286 0.589
                0.065	5.75	3.00E+0	    6.84E-1	-1.55E-1	7.55E-1	-4.67E-1	3.64E-2 -4.40E-01	1498.74	760	    0	0.1	    -2.12E-01	-5.93E-03	0.0	  0.0   0.0
                0.080	5.20	2.58E+0	    7.65E-1	-2.43E-1	7.87E-1	-4.21E-1	3.07E-2 -4.50E-01	1491.82	760	    0	0.1	    -2.34E-01	-5.67E-03	0.0	  0.0   0.0
                0.100	5.45	2.78E+0	    7.12E-1	-2.62E-1	7.94E-1	-3.77E-1	2.47E-2 -4.87E-01	1479.12	760	    0	0.1	    -2.49E-01	-5.60E-03	0.520 0.318 0.608
                0.130	5.35	2.64E+0	    7.35E-1	-3.32E-1	8.12E-1	-3.55E-1	2.22E-2 -5.42E-01	1464.09	760	    0	0.1	    -2.56E-01	-5.72E-03	0.0	  0.0   0.0
                0.160	5.25	2.47E+0	    8.09E-1	-3.87E-1	8.41E-1	-3.26E-1	1.92E-2 -6.01E-01	1434.22	760	    0	0.1	    -2.56E-01	-5.91E-03	0.0	  0.0   0.0
                0.200	5.45	2.55E+0	    8.19E-1	-3.86E-1	8.43E-1	-2.87E-1	1.38E-2 -6.88E-01	1392.61	760	    0	0.1	    -2.47E-01	-6.14E-03	0.523 0.288 0.596
                0.250	5.60	2.52E+0	    8.67E-1	-3.77E-1	8.78E-1	-2.43E-1	9.21E-3 -7.72E-01	1356.21	760	    0	0.1	    -2.36E-01	-6.44E-03	0.527 0.267 0.592
                0.300	5.85	2.63E+0	    8.47E-1	-3.63E-1	8.76E-1	-2.12E-1	5.16E-3 -8.42E-01	1308.47	760	    0	0.1	    -2.19E-01	-6.70E-03	0.546 0.269 0.608
                0.400	6.15	2.67E+0	    8.50E-1	-3.47E-1	8.97E-1	-1.93E-1	4.85E-3 -9.11E-01	1252.66	760	    0	0.1	    -1.96E-01	-7.13E-03	0.541 0.267 0.603
                0.500	6.25	2.54E+0	    8.86E-1	-3.49E-1	9.18E-1	-2.08E-1	8.54E-3 -9.69E-01	1203.91	760	    0	0.1	    -1.70E-01	-7.44E-03	0.555 0.265 0.615
                0.650	6.60	2.62E+0	    8.76E-1	-3.16E-1	9.25E-1	-2.28E-1	1.37E-2 -1.01E+00	1175.19	760	    0	0.1	    -1.56E-01	-7.87E-03	0.0	  0.0   0.0
                0.800	6.85	2.66E+0	    9.05E-1	-2.89E-1	8.94E-1	-2.52E-1	1.91E-2 -1.02E+00	1139.21	760	    0	0.1	    -1.33E-01	-8.22E-03	0.0	  0.0   0.0
                1.000	6.45	1.99E+0	    1.34E+0	-2.46E-1	9.83E-1	-2.97E-1	2.76E-2 -1.05E+00	1109.95	760	    0	0.1	    -1.05E-01	-8.44E-03	0.573 0.302 0.647
                1.300	6.75	2.01E+0	    1.39E+0	-2.06E-1	1.00E+0	-3.50E-1	3.78E-2 -1.06E+00	1088.67	760	    0	0.1	    -8.27E-02	-8.29E-03	0.0	  0.0   0.0
                1.600	6.75	1.75E+0	    1.56E+0	-1.68E-1	1.05E+0	-3.85E-1	4.43E-2 -1.04E+00	1061.77	760	    0	0.1	    -6.04E-02	-7.23E-03	0.0	  0.0   0.0
                2.000	6.65	1.25E+0	    1.75E+0	-1.32E-1	1.19E+0	-4.35E-1	5.36E-2 -1.04E+00	1009.49	760	    0	0.1	    -3.61E-02	-4.79E-03	0.580 0.389 0.700
                2.500	6.70	9.31E-1	    1.82E+0	-1.09E-1	1.29E+0	-4.79E-1	6.14E-2 -1.03E+00	966.94	760	    0	0.1	    -2.31E-02	-2.72E-03	0.0	  0.0   0.0
                3.000	6.65	5.16E-1	    1.91E+0	-8.98E-2	1.42E+0	-5.13E-1	6.76E-2 -1.01E+00	922.43	760	    0	0.1	    -1.36E-02	-1.83E-03	0.566 0.401 0.695
                4.000	6.85	3.44E-1	    1.93E+0	-7.47E-2	1.51E+0	-5.51E-1	7.43E-2 -9.69E-01	844.48	760	    0	0.1	    -3.21E-03	-1.52E-03	0.583 0.385 0.698
                5.000	6.85	-7.92E-2	1.98E+0	-6.21E-2	1.59E+0	-5.80E-1	7.90E-2 -9.20E-01	793.13	760	    0	0.1	    -2.55E-04	-1.44E-03	0.601 0.437 0.744
                6.500	7.15	-6.67E-3	1.97E+0	-5.45E-2	1.63E+0	-5.96E-1	8.12E-2 -8.34E-01	775.6	760	    0	0.1	    -3.64E-05	-1.37E-03  	0.0	  0.0   0.0
                8.000	7.50	2.56E-1 	1.94E+0	-5.23E-2	1.59E+0	-6.09E-1	8.30E-2 -7.50E-01	760.81	760	    0	0.1	    1.00E-04	-1.37E-03	0.0	  0.0   0.0
                10.000	7.45	-2.76E-1	1.97E+0	-4.63E-2	1.72E+0	-6.20E-1	8.42E-2 -6.56E-01	775	    760 	0	0.1	    0.00E+00	-1.36E-03	0.645 0.477 0.801
                PGA		5.85	2.22E+0	    6.86E-1	-1.39E-1	7.66E-1	-6.19E-1	6.03E-2 -6.00E-01	1500	760	    0	0.1	    -1.50E-01	-7.01E-03	0.502 0.260 0.564
                PGV		5.90	5.96E+0	    1.03E+0	-1.65E-1	1.08E+0	-5.79E-1	5.74E-2 -8.40E-01	1300	760	    0	0.1	    -1.00E-01	-8.44E-03   0.500 0.256 0.560
        """)

        # Coefficient table is constructed from values in table 3 (pag 1999).
        # Spectral acceleration is defined for damping of 5%, see paragraph 
        # 'Introduction' page 1990.
        # sigma, tau, std are the intra-event uncertainty, inter-event
        # uncertainty, and total standard deviation, respectively.
        
        COEFFS_STRESS_ADJUSTMENT = CoeffsTable(sa_damping=5, table="""\
        imt   s0    	    s1          s2          s3          s4          s5          s6          s7          s8          s9
        0.010   -2.05E+0	1.88E+0     -4.90E-1    5.67E-2     -2.43E-3    -1.44E+0    1.24E+0     -2.89E-1    3.09E-2     -1.25E-3
        0.013   -1.92E+0	1.80E+0     -4.71E-1    5.47E-2     -2.36E-3    -1.35E+0    1.20E+0     -2.80E-1    3.01E-2     -1.23E-3
        0.016   -1.71E+0	1.66E+0     -4.36E-1    5.09E-2     -2.20E-3    -1.08E+0    1.04E+0     -2.47E-1    2.69E-2     -1.11E-3
        0.020   -1.16E+0	1.27E+0     -3.34E-1    3.91E-2     -1.70E-3    -1.27E+0    1.25E+0     -3.17E-1    3.62E-2     -1.55E-3
        0.025   -1.54E+0	1.59E+0     -4.29E-1    5.10E-2     -2.24E-3    -1.45E+0    1.37E+0     -3.37E-1    3.73E-2     -1.54E-3
        0.030   -1.06E+0	1.20E+0     -3.13E-1    3.62E-2     -1.55E-3    -2.24E+0    1.98E+0     -5.09E-1    5.78E-2     -2.44E-3
        0.040   -8.57E-1	1.04E+0     -2.68E-1    3.08E-2     -1.33E-3    -3.31E+0    2.66E+0     -6.68E-1    7.42E-2     -3.06E-3
        0.050   -9.63E-1	9.83E-1     -2.16E-1    2.08E-2     -7.42E-4    -4.23E+0    3.29E+0     -8.32E-1    9.30E-2     -3.87E-3
        0.065   -2.23E+0	1.95E+0     -4.90E-1    5.49E-2     -2.29E-3    -3.96E+0    2.87E+0     -6.67E-1    6.88E-2     -2.65E-3
        0.080   -3.68E+0	2.96E+0     -7.51E-1    8.42E-2     -3.51E-3    -3.14E+0    2.18E+0     -4.67E-1    4.47E-2     -1.60E-3
        0.100   -4.05E+0	3.10E+0     -7.62E-1    8.33E-2     -3.39E-3    -2.45E+0    1.57E+0     -2.89E-1    2.30E-2     -6.57E-4
        0.130   -4.17E+0	3.09E+0     -7.44E-1    7.98E-2     -3.21E-3    -1.38E+0    6.26E-1     -1.16E-2    -1.09E-2    8.28E-4
        0.160   -3.96E+0	2.82E+0     -6.50E-1    6.72E-2     -2.61E-3    -2.00E-1    -3.37E-1    2.57E-1     -4.25E-2    2.18E-3
        0.200   -2.71E+0	1.73E+0     -3.30E-1    2.82E-2     -9.06E-4    8.20E-1     -1.08E+0    4.40E-1     -6.10E-2    2.85E-3
        0.250   -1.77E+0	9.83E-1     -1.31E-1    6.00E-3     -1.16E-5    1.78E+0     -1.77E+0    6.07E-1     -7.83E-2    3.50E-3
        0.300   -3.18E+0    -1.39E-1    1.70E-1     -2.85E-2    1.42E-3     2.25E+0     -2.00E+0    6.33E-1     -7.70E-2    3.27E-3
        0.400   2.02E+0     -1.86E+0    6.12E-1     -7.67E-2    3.34E-3     2.42E+0     -1.94E+0    5.56E-1     -6.17E-2    2.39E-3
        0.500   3.96E+0     -3.29E+0    9.88E-1     -1.20E-1    5.14E-3     8.56E-1     -4.53E-1    6.46E-2     5.22E-3     -8.30E-4
        0.650   3.65E+0     -2.82E+0    7.93E-1     -8.93E-2    3.55E-3     -6.67E-1    9.28E-1     -3.71E-1    6.18E-2     -3.43E-3
        0.800   2.40E+0     -1.65E+0    4.09E-1     -3.71E-2    1.05E-3     -2.12E+0    2.15E+0     -7.30E-1    1.05E-1     -5.29E-3
        1.000   1.07E+0     -4.55E-1    3.74E-2     1.03E-2     -1.08E-3    -4.47E+0    4.05E+0     -1.27E+0    1.71E-1     -8.14E-3
        1.300   -2.51E+0    2.52E+0     -8.45E-1    1.21E-1     -6.02E-3    -5.49E+0    4.77E+0     -1.44E+0    1.85E-1     -8.46E-3
        1.600   -5.26E+0    4.74E+0     -1.48E+0    1.96E-1     -9.28E-3    -5.88E+0    4.98E+0     -1.46E+0    1.83E-1     -8.16E-3
        2.000   -6.64E+0    5.77E+0     -1.74E+0    2.24E-1     -1.03E-2    -6.01E+0    4.99E+0     -1.43E+0    1.75E-1     -7.59E-3
        2.500   -8.08E+0    6.84E+0     -2.02E+0    2.54E-1     -1.14E-2    -4.88E+0    3.95E+0     -1.09E+0    1.26E-1     -5.17E-3
        3.000   -7.98E+0    6.64E+0     -1.92E+0    2.37E-1     -1.04E-2    -4.18E+0    3.32E+0     -8.86E-1    9.89E-2     -3.85E-3
        4.000   -7.12E+0    5.78E+0     -1.61E+0    1.90E-1     -7.98E-3    -2.63E+0    1.96E+0     -4.62E-1    4.24E-2     -1.18E-3
        5.000   -6.39E+0    5.08E+0     -1.38E+0    1.58E-1     -6.36E-3    -1.38E+0    9.09E-1     -1.42E-1    1.32E-3     7.11E-4
        6.500   -4.80E+0    3.68E+0     -9.37E-1    9.76E-2     -3.47E-3    -3.93E-1    9.83E-2     9.53E-2     -2.78E-2    1.96E-3
        8.000   -3.42E+0    2.51E+0     -5.80E-1    5.15E-2     -1.34E-3    -6.87E-3    -1.89E-1    1.69E-1     -3.53E-2    2.20E-3
        10.000   -2.1E+0    1.51E+0     -2.87E-1    1.53E-2     2.38E-4     2.68E-1     -3.86E-1    2.17E-1     -3.97E-2    2.30E-3
        PGA     -2.13E+0    1.9E+0      -5.04E-1    5.82E-2     -2.50E-3    -1.44E+0    1.24E+0     -2.85E-1    3.02E-2     -1.22E-3
        PGV     -2.25E+0    1.9E+0      -5.18E-1    6.14E-2     -2.73E-3    -1.76E+0    1.38E+0     -3.26E-1    3.50E-2     -1.42E-3
        """)


class YenierAtkinson2015CEUS(YenierAtkinson2015):
	"""
	This class accounts for the regional adjustment factors for the Central
	and Eastern United States.
	Overall, uses equation 26.
	Equations 23 through 25. Adding 23 and 24 yields the total calibration factor.
	This class extends the :class:'YenierAtkinson2015'.
	"""
	def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
                """
                See :meth:`superclass method
                <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
                for spec of input and result values.
                """
                # extracting dictionary of coefficients specific to required
                # intensity measure type.
                C = self.COEFFS[imt]
                C_SA = self.COEFFS_STRESS_ADJUSTMENT[imt]
        
                # compute PGA on rock conditions - needed to compute non-linear
                # site amplification term
                pga4nl = self._get_pga_on_rock(rup, dists, imt, C, C_SA)
       
                # Computes equation (1) (see pag 1990). 
                # The fourth term, site amplification is computed as given in equation (10), 
                # that is the sum of a linear term (equation 11) and a non-linear one (equations
                # 12 and 13)
                # Note: The third and fifth terms are not incorporated in this implementation.
                if imt == PGA():
                    # avoid recomputing PGA on rock, just add site terms
                    mean = pga4nl + \
                        self._get_site_amplification_linear(sites.vs30, C) + \
                        self._get_site_amplification_non_linear(sites.vs30, pga4nl, C) + \
			self._compute_event_based_calibration(imt, C) + \
			self._compute_path_related_calibration(imt, rup, dists, C)
                else:
                    mean = self._compute_distance_scaling(rup, dists, C) + \
                        self._compute_magnitude_scaling(rup, C) + \
                        self._compute_stress_adjustment(rup, C_SA) + \
                        self._get_site_amplification_linear(sites.vs30, C) + \
                        self._get_site_amplification_non_linear(sites.vs30, pga4nl, C) + \
			self._compute_event_based_calibration(imt, C) + \
			self._compute_path_related_calibration(imt, rup, dists, C)

                stddevs = self._get_stddevs(C, stddev_types, num_sites=len(sites.vs30))
        
                return mean, stddevs

        def _get_stddevs(self, C, stddev_types, num_sites):
                """
                Return standard deviations as defined in table 8, pag 121.
                """
                stddevs = []
                for stddev_type in stddev_types:
                    assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                    if stddev_type == const.StdDev.TOTAL:
                        stddevs.append(C['std'] + np.zeros(num_sites))
                    elif stddev_type == const.StdDev.INTRA_EVENT:
                        stddevs.append(C['sigma'] + np.zeros(num_sites))
                    elif stddev_type == const.StdDev.INTER_EVENT:
                        stddevs.append(C['tau'] + np.zeros(num_sites))
                return stddevs

        def _get_pga_on_rock(self, rup, dists, imt, C, C_SA):
                """
                Compute and return PGA on rock conditions (that is vs30 = 760.0 m/s).
                This is needed to compute non-linear site amplification term.
                """
                # Median PGA in g for vs30 = 760.0, without site amplification,
                # that is equation (1) pag 1990, without Fs. 
                C_pga  = self.COEFFS[PGA()]
                C_pgsa = self.COEFFS_STRESS_ADJUSTMENT[PGA()]
                pga4nl = self._compute_distance_scaling(rup, dists, C_pga) + \
                         self._compute_magnitude_scaling(rup, C_pga) + \
                         self._compute_stress_adjustment(rup, C_pgsa) + \
			 self._compute_event_based_calibration(imt, C) + \
			 self._compute_path_related_calibration(imt, rup, dists, C)

                return pga4nl

	# Preferred value of ref_stress = 300 bar.
        def _compute_stress_adjustment(self, rup, C_SA):
                """
                Compute stress adjustment term, equation (4), pag 1991.
                """
                # ref_stress is the reference stress in bar
                if rup.stress_drop <= 100.:
                        e_ref_stress = C_SA['s0'] + C_SA['s1'] * rup.mag + \
                                C_SA['s2'] * (rup.mag ** 2) + \
                                C_SA['s3'] * (rup.mag ** 3) + \
                                C_SA['s4'] * (rup.mag ** 4)
                else:
                        e_ref_stress = C_SA['s5'] + C_SA['s6'] * rup.mag + \
                                C_SA['s7'] * (rup.mag ** 2) + \
                                C_SA['s8'] * (rup.mag ** 3) + \
                                C_SA['s9'] * (rup.mag ** 4)
                        
                return e_ref_stress * np.log(rup.stress_drop/100)

	def _compute_event_based_calibration(self, imt, C):
		"""
		Compute event based calibration factor as defined in equation (23), pag 2003.
		"""
		Ceb = 0.0
		if imt == PGA():
			Ceb = -0.25
		elif imt == PGV():
			Ceb = -0.21
		elif imt.period <= 10:
			Ceb = -0.25 + np.amax([0, 0.39 * np.log(imt.period / 2)])
		return Ceb

	def _compute_geo_attenuation_calibration(self, imt, C):
		"""
		Compute geometrical attenuation rate calibration as defined in 
		equation (25), pag 2004.
		Needed to compute path-related calibration factor, equation (24).
		"""
		b3 = 0.0
		if imt == PGA():
			b3 = 0.030
		elif imt == PGV():
			b3 = 0.052
		elif imt.period <= 10:
			b3 = np.amin([0.095, 0.030 + np.amax([0, 0.095 * np.log(imt.period / 0.065)])])
		return b3

	def _compute_path_related_calibration(self, imt, rup, dists, C):
		"""
		Compute path related calibration as defined in equation (24), pag 2004.
		"""
                h = 10 ** (-0.405 + 0.235 * rup.mag)
                R = np.sqrt(np.amin(dists.rrup) ** 2 + (h ** 2))
		b3 = self._compute_geo_attenuation_calibration(imt, C)
		Cp = 0.0
		if R <= 150:
			Cp = b3 * np.log(R / 150)
		else:
			Cp = 0.0
		return Cp


class YenierAtkinson2015Cal(YenierAtkinson2015):
	"""
	This class accounts for the regional adjustment factors for California, USA.
	Overall, used equation 28.
	Equation 27 through 29.
	This class extends the :class:'YenierAtkinson2015'.
	"""

        def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
                """
                See :meth:`superclass method
                <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
                for spec of input and result values.
                """
                # extracting dictionary of coefficients specific to required
                # intensity measure type.
                C = self.COEFFS[imt]
                C_SA = self.COEFFS_STRESS_ADJUSTMENT[imt]

                # compute PGA on rock conditions - needed to compute non-linear
                # site amplification term
                pga4nl = self._get_pga_on_rock(rup, dists, imt, C, C_SA)
       
                # Computes equation (1) (see pag 1990). 
                # The fourth term, site amplification is computed as given in equation (10), 
                # that is the sum of a linear term (equation 11) and a non-linear one (equations
                # 12 and 13)
                # Note: The third and fifth terms are not incorporated in this implementation.
                if imt == PGA():
                    # avoid recomputing PGA on rock, just add site terms
                    mean = pga4nl + \
                        self._get_site_amplification_linear(sites.vs30, C) + \
                        self._get_site_amplification_non_linear(sites.vs30, pga4nl, C) + \
			self._compute_calibration_factor(imt, C)
                else:
                    mean = self._compute_distance_scaling(rup, dists, C) + \
                        self._compute_magnitude_scaling(rup, C) + \
                        self._compute_stress_adjustment(rup, C_SA) + \
                        self._get_site_amplification_linear(sites.vs30, C) + \
                        self._get_site_amplification_non_linear(sites.vs30, pga4nl, C) + \
			self._compute_calibration_factor(imt, C)

                stddevs = self._get_stddevs(C, stddev_types, num_sites=len(sites.vs30))

                return mean, stddevs

        def _get_stddevs(self, C, stddev_types, num_sites):
                """
                Return standard deviations as defined in table 8, pag 121.
                """
                stddevs = []
                for stddev_type in stddev_types:
                    assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                    if stddev_type == const.StdDev.TOTAL:
                        stddevs.append(C['std'] + np.zeros(num_sites))
                    elif stddev_type == const.StdDev.INTRA_EVENT:
                        stddevs.append(C['sigma'] + np.zeros(num_sites))
                    elif stddev_type == const.StdDev.INTER_EVENT:
                        stddevs.append(C['tau'] + np.zeros(num_sites))
                return stddevs

        def _get_site_amplification_non_linear(self, vs30, pga4nl, C):
                """
                Compute non-linear site amplification,
                equation (12), pag 1992.
                """		                
                f2 = self._compute_non_linear_slope(vs30, C)
                return C['f1'] + self._compute_non_linear_term(pga4nl, f2, C)

        def _get_pga_on_rock(self, rup, dists, imt, C, C_SA):
                """
                Compute and return PGA on rock conditions (that is vs30 = 760.0 m/s).
                This is needed to compute non-linear site amplification term.
                """
                # Median PGA in g for vs30 = 760.0, without site amplification,
                # that is equation (1) pag 1990, without Fs. 
                C_pga  = self.COEFFS[PGA()]
                C_pgsa = self.COEFFS_STRESS_ADJUSTMENT[PGA()]
                pga4nl = self._compute_distance_scaling(rup, dists, C_pga) + \
                         self._compute_magnitude_scaling(rup, C_pga) + \
                         self._compute_stress_adjustment(rup, C_pgsa) + \
			 self._compute_calibration_factor(imt, C)

                return pga4nl

	def _compute_calibration_factor(self, imt, C):
		"""
		Compute event based calibration factor as defined in equation (29), pag 2007.
		"""
		Cf = 0.0
		if imt == PGA():
			Cf = -0.25
		elif imt == PGV():
			Cf = -0.15
		elif imt.period <= 0.2:
			Cf = np.amax([-0.25,-0.25 + 0.36 * np.log(imt.period / 0.1)])
		elif imt.period > 0.2 and imt.period <= 10:
			Cf = np.amax([0, 0.39 * np.log(imt.period / 1.5)])
		return Cf
        
