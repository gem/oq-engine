# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
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
Module exports :class:`Campbell2003`, :class:`Campbell2003SHARE`,
:class:`Campbell2003MblgAB1987NSHMP2008`,
:class:`Campbell2003MblgJ1996NSHMP2008`,
:class:`Campbell2003MwNSHMP2008`
"""
import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.gsim.utils import (
    mblg_to_mw_atkinson_boore_87,
    mblg_to_mw_johnston_96,
    clip_mean)
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class Campbell2003(GMPE):
    """
    Implements GMPE developed by K.W Campbell and published as "Prediction of
    Strong Ground Motion Using the Hybrid Empirical Method and Its Use in the
    Development of Ground Motion (Attenuation) Relations in Eastern North
    America" (Bulletting of the Seismological Society of America, Volume 93,
    Number 3, pages 1012-1033, 2003). The class implements also the corrections
    given in the erratum (2004).
    """

    #: Supported tectonic region type is stable continental crust given that
    #: the equations have been derived for Eastern North America.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see table 6, page 1022 (PGA is assumed
    #: to be equal to SA at 0.01 s)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of
    #: two horizontal components
    #: :attr:`~openquake.hazardlib.const.IMC.AVERAGE_HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is only total, see equation 35, page
    #: 1021
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No site parameters are needed
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is only magnitude, see equation 30 page
    #: 1021.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is closest distance to rupture, see equation
    #: 30 page 1021.
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        C = self.COEFFS[imt]
        mean = self._compute_mean(C, rup.mag, dists.rrup)
        stddevs = self._get_stddevs(C, stddev_types, rup.mag,
                                    dists.rrup.shape[0])

        return mean, stddevs

    def _compute_mean(self, C, mag, rrup):
        """
        Compute mean value according to equation 30, page 1021.
        """
        mean = (C['c1'] +
                self._compute_term1(C, mag) +
                self._compute_term2(C, mag, rrup) +
                self._compute_term3(C, rrup))
        return mean

    def _get_stddevs(self, C, stddev_types, mag, num_sites):
        """
        Return total standard deviation as for equation 35, page 1021.
        """
        stddevs = []
        for _ in stddev_types:
            if mag < 7.16:
                sigma = C['c11'] + C['c12'] * mag
            elif mag >= 7.16:
                sigma = C['c13']
            stddevs.append(np.zeros(num_sites) + sigma)

        return stddevs

    def _compute_term1(self, C, mag):
        """
        This computes the term f1 in equation 31, page 1021
        """
        return (C['c2'] * mag) + C['c3'] * (8.5 - mag) ** 2

    def _compute_term2(self, C, mag, rrup):
        """
        This computes the term f2 in equation 32, page 1021
        """
        c78_factor = (C['c7'] * np.exp(C['c8'] * mag)) ** 2
        R = np.sqrt(rrup ** 2 + c78_factor)

        return C['c4'] * np.log(R) + (C['c5'] + C['c6'] * mag) * rrup

    def _compute_term3(self, C, rrup):
        """
        This computes the term f3 in equation 34, page 1021 but corrected
        according to the erratum.
        """
        f3 = np.zeros_like(rrup)

        idx_between_70_130 = (rrup > 70) & (rrup <= 130)
        idx_greater_130 = rrup > 130

        f3[idx_between_70_130] = (
            C['c9'] * (np.log(rrup[idx_between_70_130]) - np.log(70))
        )

        f3[idx_greater_130] = (
            C['c9'] * (np.log(rrup[idx_greater_130]) - np.log(70)) +
            C['c10'] * (np.log(rrup[idx_greater_130]) - np.log(130))
        )

        return f3

    #: Coefficient tables are constructed from the electronic suplements of
    #: the original paper.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT       c1        c2        c3        c4        c5          c6          c7       c8       c9       c10       c11       c12       c13
    pga       0.0305    0.633    -0.0427    -1.591    -0.00428    0.000483    0.683    0.416    1.140    -0.873    1.030    -0.0860    0.414
    0.020     1.3535    0.630    -0.0404    -1.787    -0.00388    0.000497    1.020    0.363    0.851    -0.715    1.030    -0.0860    0.414
    0.030     1.1860    0.622    -0.0362    -1.691    -0.00367    0.000501    0.922    0.376    0.759    -0.922    1.030    -0.0860    0.414
    0.050     0.3736    0.616    -0.0353    -1.469    -0.00378    0.000500    0.630    0.423    0.771    -1.239    1.042    -0.0838    0.443
    0.075    -0.0395    0.615    -0.0353    -1.383    -0.00421    0.000486    0.491    0.463    0.955    -1.349    1.052    -0.0838    0.453
    0.100    -0.1475    0.613    -0.0353    -1.369    -0.00454    0.000460    0.484    0.467    1.096    -1.284    1.059    -0.0838    0.460
    0.150    -0.1901    0.616    -0.0478    -1.368    -0.00473    0.000393    0.461    0.478    1.239    -1.079    1.068    -0.0838    0.469
    0.200    -0.4328    0.617    -0.0586    -1.320    -0.00460    0.000337    0.399    0.493    1.250    -0.928    1.077    -0.0838    0.478
    0.300    -0.6906    0.609    -0.0786    -1.280    -0.00414    0.000263    0.349    0.502    1.241    -0.753    1.081    -0.0838    0.482
    0.500    -0.5907    0.534    -0.1379    -1.216    -0.00341    0.000194    0.318    0.503    1.166    -0.606    1.098    -0.0824    0.508
    0.750    -0.5429    0.480    -0.1806    -1.184    -0.00288    0.000160    0.304    0.504    1.110    -0.526    1.105    -0.0806    0.528
    1.000    -0.6104    0.451    -0.2090    -1.158    -0.00255    0.000141    0.299    0.503    1.067    -0.482    1.110    -0.0793    0.543
    1.500    -0.9666    0.441    -0.2405    -1.135    -0.00213    0.000119    0.304    0.500    1.029    -0.438    1.099    -0.0771    0.547
    2.000    -1.4306    0.459    -0.2552    -1.124    -0.00187    0.000103    0.310    0.499    1.015    -0.417    1.093    -0.0758    0.551
    3.000    -2.2331    0.492    -0.2646    -1.121    -0.00154    0.000084    0.310    0.499    1.014    -0.393    1.090    -0.0737    0.562
    4.000    -2.7975    0.507    -0.2738    -1.119    -0.00135    0.000074    0.294    0.506    1.018    -0.386    1.092    -0.0722    0.575
    """)


class Campbell2003SHARE(Campbell2003):
    """
    Extends
    :class:`~openquake.hazardlib.gsim.campbell_2003.Campbell2003` and
    introduces adjustments for style of faulting and default rock soil
    conditions as needed by the SHARE (http://www.share-eu.org/)
    project.
    """
    #: Required rupture parameters are magnitude and rake
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake'))

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 800.

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract faulting style  and rock adjustment coefficients for the
        # given imt
        C_ADJ = self.COEFFS_FS_ROCK[imt]

        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, stddev_types)

        # apply faulting style and rock adjustment factor for mean and std
        mean = np.log(np.exp(mean) *
                      _compute_faulting_style_term(C_ADJ['Frss'],
                                                   self.CONSTS_FS['pR'],
                                                   self.CONSTS_FS['Fnss'],
                                                   self.CONSTS_FS['pN'],
                                                   rup.rake) * C_ADJ['AFrock'])
        stddevs = np.array(stddevs)

        return mean, stddevs

    #: Coefficients for faulting style and rock adjustment
    COEFFS_FS_ROCK = CoeffsTable(sa_damping=5, table="""\
    IMT      Frss     AFrock
    pga      1.220000 0.735106
    0.020000 1.192000 0.474275
    0.030000 1.178000 0.423049
    0.050000 1.150000 0.550323
    0.075000 1.115000 0.730061
    0.100000 1.080000 0.888509
    0.150000 1.150000 1.094622
    0.200000 1.190000 1.197291
    0.300000 1.230000 1.288309
    0.500000 1.230000 1.311421
    0.750000 1.199444 1.298212
    1.000000 1.196667 1.265762
    1.500000 1.191111 1.197583
    2.000000 1.140000 1.215779
    3.000000 1.140000 1.215779
    4.000000 1.140000 1.215779
    """)

    #: Constants for faulting style adjustment
    CONSTS_FS = {'Fnss': 0.95, 'pN': 0.01, 'pR': 0.81}


def _compute_faulting_style_term(Frss, pR, Fnss, pN, rake):
    """
    Compute SHARE faulting style adjustment term.
    """
    if rake > 30.0 and rake <= 150.0:
        return np.power(Frss, 1 - pR) * np.power(Fnss, -pN)
    elif rake > -120.0 and rake <= -60.0:
        return np.power(Frss, - pR) * np.power(Fnss, 1 - pN)
    else:
        return np.power(Frss, - pR) * np.power(Fnss, - pN)


class Campbell2003MblgAB1987NSHMP2008(Campbell2003):
    """
    Implement GMPE developed by Ken Campbell and described in
    "Development of semi-empirical attenuation relationships for the CEUS",
    U.S. Geological Survey, Award 01HQGR0011, final report.

    Document available at:
    http://earthquake.usgs.gov/research/external/reports/01HQGR0011.pdf

    This GMPE is used by the National Seismic Hazard Mapping Project (NSHMP)
    for the 2008 central and eastern US hazard model.

    This class replicates the algorithm as implemented in
    ``subroutine getCampCEUS`` in the ``hazgridXnga2.f`` Fortran code available
    at: http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/

    The class assumes rupture magnitude to be in Mblg scale (given that MFDs
    for central and eastern US are given in this scale). Mblg is converted to
    Mw using Atkinson and Boore 1987 conversion equation

    Coefficients are given for the B/C (firm rock) conditions.
    """

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.


    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        C = self.COEFFS[imt]
        mag = self._convert_magnitude(rup.mag)

        mean = self._compute_mean(C, mag, dists.rrup)
        mean = clip_mean(imt, mean)

        stddevs = self._get_stddevs(C, stddev_types, mag, dists.rrup.size)

        return mean, stddevs

    def _convert_magnitude(self, mag):
        """
        Convert magnitude from Mblg to Mw using Atkinson and Boore 1987
        equation.
        """
        return mblg_to_mw_atkinson_boore_87(mag)

    def _compute_mean(self, C, mag, rrup):
        """
        Compute mean value (Equation 30 in USGS report)
        """
        mean = np.zeros_like(rrup)

        mean += C['c1'] + C['c2'] * mag + C['c3'] * (8.5 - mag) ** 2

        idx = rrup > 70.
        mean[idx] += C['c7'] * (np.log(rrup[idx]) - np.log(70.))

        idx = rrup > 130.
        mean[idx] += C['c8'] * (np.log(rrup[idx]) - np.log(130.))

        R = np.sqrt(
            rrup ** 2 + (C['c5'] * np.exp(C['c6'] * mag)) ** 2
        )
        mean += C['c4'] * np.log(R) + (C['c9'] + C['c10'] * mag) * rrup

        return mean

    #: Coefficient tables extracted from ``subroutine getCampCEUS`` in
    #: ``hazgridXnga2.f``
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    c1       c2       c3        c4      c5      c6      c7       c8       c9        c10        c11      c12      c13
    pga    0.4492   0.633   -0.0427   -1.591   0.683   0.416   1.140   -0.873   -0.00428   0.000483   1.030   -0.0860   0.414
    0.1    0.4064   0.613   -0.0353   -1.369   0.484   0.467   1.096   -1.284   -0.00454   0.00046    1.059   -0.0838   0.460
    0.2    0.1325   0.617   -0.0586   -1.32    0.399   0.493   1.25    -0.928   -0.0046    0.000337   1.077   -0.0838   0.478
    0.3   -0.1483   0.609   -0.0786   -1.28    0.349   0.502   1.241   -0.753   -0.00414   0.000263   1.081   -0.0838   0.482
    0.5   -0.1333   0.534   -0.1379   -1.216   0.318   0.503   1.116   -0.606   -0.00341   0.000194   1.098   -0.0824   0.508
    1.0   -0.3177   0.451   -0.2090   -1.158   0.299   0.503   1.067   -0.482   -0.00255   0.000141   1.110   -0.0793   0.543
    2.0   -1.2483   0.459   -0.2552   -1.124   0.310   0.499   1.015   -0.417   -0.00187   0.000103   1.093   -0.0758   0.551
    """)


class Campbell2003MblgJ1996NSHMP2008(Campbell2003MblgAB1987NSHMP2008):
    """
    Extend :class:`Campbell2003MblgAB1987NSHMP2008` but uses Johnston 1996
    equation for converting Mblg to Mw
    """
    def _convert_magnitude(self, mag):
        """
        Convert magnitude from Mblg to Mw using Johnston 1996 equation.
        """
        return mblg_to_mw_johnston_96(mag)


class Campbell2003MwNSHMP2008(Campbell2003MblgAB1987NSHMP2008):
    """
    Extend :class:`Campbell2003MblgAB1987NSHMP2008` but assumes magnitude
    to be in Mw scale, so no converion is applied.
    """

    def _convert_magnitude(self, mag):
        """
        Return magnitude value unchanged
        """
        return mag
