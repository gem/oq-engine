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
Module exports
:class:`AtkinsonBoore2003SInter`,
:class:`AtkinsonBoore2003SSlab`,
:class:`AtkinsonBoore2003SInterNSHMP2008`,
:class:`AtkinsonBoore2003SSlabNSHMP2008`,
:class:`AtkinsonBoore2003SSlabCascadia`,
:class:`AtkinsonBoore2003SSlabCascadiaNSHMP2008`,
:class:`AtkinsonBoore2003SSlabJapan`
:class:`AtkinsonBoore2003SSlabJapanNSHMP2008`
"""
import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g
import copy

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class AtkinsonBoore2003SInter(GMPE):
    """
    Implements GMPE developed by G. M  Atkinson and D. Boore and published as
    "Empirical Ground-Motion Relations for Subduction-Zone Earthquakes and
    Their Application to Cascadia and Other Regions" (Bulletin of the
    Seismological Society of America, Volume 93, Number 4, pages 1703-1929,
    2003) and includes correction for subduction interface equations as
    described in "Erratum to 'Empirical Ground Motion Relations for
    Subduction-Zone Earthquakes and their application to Cascadia and other
    regions'", Gail M. Atkinson and David M. Boore, Volume 98, Number 5,
    pp.2567-2569, 2008. The class implements the global model but not the
    corrections for Japan/Cascadia. SA values at 4 s (not supported by the
    original equations) are obtained from mean value at 3 s divided by a
    factor equal to 0.550 (scaling factor computed in the context of the SHARE
    project and obtained as average ratio between median values at 4 and 3
    seconds as predicted by SHARE subduction GMPEs). The class implements the
    equations for 'Subduction Interface' (that's why the class name ends with
    'SInter').
    """
    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see table 1, page 1715
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the random horizontal
    #: component:
    #: attr:`~openquake.hazardlib.const.IMC.RANDOM_HORIZONTAL`, see
    #: paragraph 'Functional : Form', page 1706
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RANDOM_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see table 1, page 1715
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters is Vs30, used to distinguish between NEHRP
    #: soil classes, see paragraph 'Functional Form', page 1706
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude and focal depth, see equation
    #: 1, page 1706
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    #: Required distance measure is closest distance to rupture, see equation
    #: 1, page 1706
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS_SINTER[imt]

        # cap magnitude values at 8.5, see page 1709
        mag = rup.mag
        if mag > 8.5:
            mag = 8.5

        # compute PGA on rock (needed for site amplification calculation)
        G = 10 ** (1.2 - 0.18 * mag)
        pga_rock = self._compute_mean(self.COEFFS_SINTER[PGA()], G, mag,
                                      rup.hypo_depth, dists.rrup, sites.vs30,
                                      # by passing pga_rock > 500 the soil
                                      # amplification is 0
                                      np.zeros_like(sites.vs30) + 600,
                                      PGA())
        pga_rock = 10 ** (pga_rock)

        # periods 0.4 s (2.5 Hz) and 0.2 s (5 Hz) need a special case because
        # of the erratum. SA for 0.4s and 0.2s is computed and a weighted sum
        # is returned
        if imt.period in (0.2, 0.4):
            C04 = self.COEFFS_SINTER[SA(period=0.4, damping=5.0)]
            C02 = self.COEFFS_SINTER[SA(period=0.2, damping=5.0)]
            mean04 = self._compute_mean(C04, G, mag, rup.hypo_depth,
                                        dists.rrup, sites.vs30, pga_rock, imt)
            mean02 = self._compute_mean(C02, G, mag, rup.hypo_depth,
                                        dists.rrup, sites.vs30, pga_rock, imt)

            if imt.period == 0.2:
                mean = 0.333 * mean02 + 0.667 * mean04
            else:
                mean = 0.333 * mean04 + 0.667 * mean02
        else:
            mean = self._compute_mean(C, G, mag, rup.hypo_depth, dists.rrup,
                                      sites.vs30, pga_rock, imt)

        # convert from log10 to ln and units from cm/s**2 to g
        mean = np.log((10 ** mean) * 1e-2 / g)

        if imt.period == 4.0:
            mean /= 0.550

        stddevs = self._get_stddevs(C, stddev_types, sites.vs30.shape[0])

        return mean, stddevs

    def _compute_mean(self, C, g, mag, hypo_depth, rrup, vs30, pga_rock, imt):
        """
        Compute mean according to equation 1, page 1706.
        """
        if hypo_depth > 100:
            hypo_depth = 100
        delta = 0.00724 * 10 ** (0.507 * mag)
        R = np.sqrt(rrup ** 2 + delta ** 2)

        s_amp = self._compute_soil_amplification(C, vs30, pga_rock, imt)

        mean = (
            # 1st term
            C['c1'] + C['c2'] * mag +
            # 2nd term
            C['c3'] * hypo_depth +
            # 3rd term
            C['c4'] * R -
            # 4th term
            g * np.log10(R) +
            # 5th, 6th and 7th terms
            s_amp
        )

        return mean

    @classmethod
    def _compute_soil_amplification(cls, C, vs30, pga_rock, imt):
        """
        Compute soil amplification (5th, 6th, and 7th terms in equation 1,
        page 1706).
        """
        Sc, Sd, Se = cls._compute_site_class_dummy_variables(vs30)
        sl = cls._compute_soil_linear_factor(pga_rock, imt)

        return C['c5'] * sl * Sc + C['c6'] * sl * Sd + C['c7'] * sl * Se

    @classmethod
    def _compute_site_class_dummy_variables(cls, vs30):
        """
        Compute site class dummy variables as explained in paragraph
        'Functional Form', page 1706.
        """
        Sc = np.zeros_like(vs30)
        Sd = np.zeros_like(vs30)
        Se = np.zeros_like(vs30)

        Sc[(vs30 > 360) & (vs30 <= 760)] = 1
        Sd[(vs30 >= 180) & (vs30 <= 360)] = 1
        Se[vs30 < 180] = 1

        return Sc, Sd, Se

    @classmethod
    def _compute_soil_linear_factor(cls, pga_rock, imt):
        """
        Compute soil linear factor as explained in paragraph 'Functional
        Form', page 1706.
        """
        if imt.period >= 1:
            return np.ones_like(pga_rock)
        else:
            sl = np.zeros_like(pga_rock)

            pga_between_100_500 = (pga_rock > 100) & (pga_rock < 500)
            pga_greater_equal_500 = pga_rock >= 500

            is_SA_between_05_1 = 0.5 < imt.period < 1

            is_SA_less_equal_05 = imt.period <= 0.5

            if is_SA_between_05_1:
                sl[pga_between_100_500] = (1 - (1. / imt.period - 1) *
                                           (pga_rock[pga_between_100_500] -
                                           100) / 400)
                sl[pga_greater_equal_500] = 1 - (1. / imt.period - 1)

            if is_SA_less_equal_05 or imt.period == 0:
                sl[pga_between_100_500] = (1 - (pga_rock[pga_between_100_500] -
                                           100) / 400)

            sl[pga_rock <= 100] = 1

            return sl

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations as defined in table 1, pag 1715.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.log(10 ** C['sigma']) + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(np.log(10 ** C['s1']) + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(np.log(10 ** C['s2']) + np.zeros(num_sites))
        return stddevs

    COEFFS_SINTER = CoeffsTable(sa_damping=5, table="""\
    IMT      c1          c2          c3           c4          c5          c6          c7          sigma       s1          s2
    pga      2.991000    0.035250    0.007590    -0.002060   0.190000    0.240000    0.290000    0.230000    0.200000    0.110000
    0.0400   2.875300    0.070520    0.010040    -0.002780   0.150000    0.200000    0.200000    0.260000    0.220000    0.140000
    0.1000   2.778900    0.098410    0.009740    -0.002870   0.150000    0.230000    0.200000    0.270000    0.250000    0.100000
    0.2000   2.663800    0.123860    0.008840    -0.002800   0.150000    0.270000    0.250000    0.280000    0.250000    0.130000
    0.4000   2.524900    0.147700    0.007280    -0.002350   0.130000    0.370000    0.380000    0.290000    0.250000    0.150000
    1.0000   2.144200    0.134500    0.005210    -0.001100   0.100000    0.300000    0.550000    0.340000    0.280000    0.190000
    2.0000   2.190700    0.071480    0.002240     0.000000   0.100000    0.250000    0.400000    0.340000    0.290000    0.180000
    3.0000   2.301000    0.022370    0.000120     0.000000   0.100000    0.250000    0.360000    0.360000    0.310000    0.180000
    4.0000   2.301000    0.022370    0.000120     0.000000   0.100000    0.250000    0.360000    0.360000    0.310000    0.180000
    """)


class AtkinsonBoore2003SSlab(AtkinsonBoore2003SInter):
    """
    Implements GMPE developed by G. M  Atkinson and D. Boore and published as
    "Empirical Ground-Motion Relations for Subduction-Zone Earthquakes and
    Their Application to Cascadia and Other Regions" (Bulletin of the
    Seismological Society of America, Volume 93, Number 4, pages 1703-1929,
    2003). The class implements the global model but not the corrections for
    Japan/Cascadia. SA values at 4 s (not supported by the original equations)
    are obtained from mean value at 3 s divided by a factor equal to 0.550
    (scaling factor computed in the context of the SHARE project and obtained
    as average ratio between median values at 4 and 3 seconds as predicted by
    SHARE subduction GMPEs). The class implements the equations for 'Subduction
    IntraSlab' (that's why the class name ends with 'SSlab').
    """
    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS_SSLAB[imt]

        # cap magnitude values at 8.0, see page 1709
        mag = rup.mag
        if mag >= 8.0:
            mag = 8.0

        # compute PGA on rock (needed for site amplification calculation)
        G = 10 ** (0.301 - 0.01 * mag)
        pga_rock = self._compute_mean(self.COEFFS_SSLAB[PGA()], G, mag,
                                      rup.hypo_depth, dists.rrup, sites.vs30,
                                      # by passing pga_rock > 500 the soil
                                      # amplification is 0
                                      np.zeros_like(sites.vs30) + 600,
                                      PGA())
        pga_rock = 10 ** (pga_rock)

        # compute actual mean and convert from log10 to ln and units from
        # cm/s**2 to g
        mean = self._compute_mean(C, G, mag, rup.hypo_depth, dists.rrup,
                                  sites.vs30, pga_rock, imt)
        mean = np.log((10 ** mean) * 1e-2 / g)

        if imt.period == 4.0:
            mean /= 0.550

        stddevs = self._get_stddevs(C, stddev_types, sites.vs30.shape[0])

        return mean, stddevs

    COEFFS_SSLAB = CoeffsTable(sa_damping=5, table="""\
    IMT      c1         c2         c3         c4         c5          c6         c7         sigma      s1        s2
    pga     -0.04713    0.69090    0.01130    -0.00202    0.19000    0.24000    0.29000    0.27000    0.23000    0.14000
    0.0400   0.50697    0.63273    0.01275    -0.00234    0.15000    0.20000    0.20000    0.25000    0.24000    0.07000
    0.1000   0.43928    0.66675    0.01080    -0.00219    0.15000    0.23000    0.20000    0.28000    0.27000    0.07000
    0.2000   0.51589    0.69186    0.00572    -0.00192    0.15000    0.27000    0.25000    0.28000    0.26000    0.10000
    0.4000   0.00545    0.77270    0.00173    -0.00178    0.13000    0.37000    0.38000    0.28000    0.26000    0.10000
    1.0000  -1.02133    0.87890    0.00130    -0.00173    0.10000    0.30000    0.55000    0.29000    0.27000    0.11000
    2.0000  -2.39234    0.99640    0.00364    -0.00118    0.10000    0.25000    0.40000    0.30000    0.28000    0.11000
    3.0000  -3.70012    1.11690    0.00615    -0.00045    0.10000    0.25000    0.36000    0.30000    0.29000    0.08000
    4.0000  -3.70012    1.11690    0.00615    -0.00045    0.10000    0.25000    0.36000    0.30000    0.29000    0.08000
    """)


class AtkinsonBoore2003SInterNSHMP2008(AtkinsonBoore2003SInter):
    """
    Extend :class:`AtkinsonBoore2003SInter` and introduces site amplification
    for B/C site condition and fixed rupture hypocentral depth (20 km) as
    defined by the National Seismic Hazard Mapping Project (NSHMP) for the
    2008 US hazard model

    Site amplification for B/C is triggered when vs30 > 760 and it is
    computed as site amplification for C soil scaled by a factor equal to 0.5

    The class implements the equation as coded in ``subroutine getABsub``
    in ``hazSUBXnga.f`` Fortran code available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.

        Call super class method with hypocentral depth fixed at 20 km
        """
        # fix hypocentral depth to 20 km. Create new rupture context to avoid
        # changing the original one
        new_rup = copy.deepcopy(rup)
        new_rup.hypo_depth = 20.

        mean, stddevs = super().get_mean_and_stddevs(
            sites, new_rup, dists, imt, stddev_types)

        return mean, stddevs

    @classmethod
    def _compute_soil_amplification(cls, C, vs30, pga_rock, imt):
        """
        Compute soil amplification (5th, 6th, and 7th terms in equation 1,
        page 1706) and add the B/C site condition as implemented by NSHMP.
        """
        Sbc, Sc, Sd, Se = cls._compute_site_class_dummy_variables(vs30)
        sl = cls._compute_soil_linear_factor(pga_rock, imt)

        return (
            C['c5'] * sl * Sbc * 0.5 +
            C['c5'] * sl * Sc +
            C['c6'] * sl * Sd +
            C['c7'] * sl * Se
        )

    @classmethod
    def _compute_site_class_dummy_variables(cls, vs30):
        """
        Extend
        :meth:`AtkinsonBoore2003SInter._compute_site_class_dummy_variables`
        and includes dummy variable for B/C site conditions (vs30 > 760.)
        """
        Sbc = np.zeros_like(vs30)
        Sc = np.zeros_like(vs30)
        Sd = np.zeros_like(vs30)
        Se = np.zeros_like(vs30)

        Sbc[vs30 > 760.] = 1
        Sc[(vs30 > 360) & (vs30 <= 760)] = 1
        Sd[(vs30 >= 180) & (vs30 <= 360)] = 1
        Se[vs30 < 180] = 1

        return Sbc, Sc, Sd, Se


class AtkinsonBoore2003SSlabNSHMP2008(AtkinsonBoore2003SSlab):
    """
    Extend :class:`AtkinsonBoore2003SSlab` and introduces site amplification
    for B/C site condition as defined by the National Seismic Hazard Mapping
    Project (NSHMP) for the 2008 US hazard model.

    Site amplification for B/C is triggered when vs30 > 760 and it is
    computed as site amplification for C soil scaled by a factor equal to 0.5

    The class replicates the equation as coded in ``subroutine getABsub``
    in ``hazgridXnga2.f`` Fortran code available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/
    """
    @classmethod
    def _compute_soil_amplification(cls, C, vs30, pga_rock, imt):
        """
        Compute soil amplification (5th, 6th, and 7th terms in equation 1,
        page 1706) and add the B/C site condition as implemented by NSHMP.

        Call
        :meth:`AtkinsonBoore2003SInterNSHMP2008._compute_soil_amplification`
        """
        return AtkinsonBoore2003SInterNSHMP2008._compute_soil_amplification(
            C, vs30, pga_rock, imt)

    @classmethod
    def _compute_site_class_dummy_variables(cls, vs30):
        """
        Extend
        :meth:`AtkinsonBoore2003SInter._compute_site_class_dummy_variables`
        and includes dummy variable for B/C site conditions (vs30 > 760.)

        Call
        meth:`AtkinsonBoore2003SInter._compute_site_class_dummy_variables`
        """
        return AtkinsonBoore2003SInterNSHMP2008. \
            _compute_site_class_dummy_variables(vs30)


class AtkinsonBoore2003SSlabCascadia(AtkinsonBoore2003SSlab):
    """
    Extends :class:`AtkinsonBoore2003SSlab` but uses coefficients for
    Cascadia region

    The class replicates the equation as coded in ``subroutine getABsub``
    in ``hazgridXnga2.f`` Fortran code available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/
    """
    COEFFS_SSLAB = CoeffsTable(sa_damping=5, table="""\
    IMT      c1      c2         c3         c4         c5          c6         c7         sigma      s1        s2
    pga     -0.25    0.69090    0.01130    -0.00202    0.19000    0.24000    0.29000    0.27000    0.23000    0.14000
    0.0400   0.23    0.63273    0.01275    -0.00234    0.15000    0.20000    0.20000    0.25000    0.24000    0.07000
    0.1000   0.16    0.66675    0.01080    -0.00219    0.15000    0.23000    0.20000    0.28000    0.27000    0.07000
    0.2000   0.40    0.69186    0.00572    -0.00192    0.15000    0.27000    0.25000    0.28000    0.26000    0.10000
    0.4000  -0.01    0.77270    0.00173    -0.00178    0.13000    0.37000    0.38000    0.28000    0.26000    0.10000
    1.0000  -0.98    0.87890    0.00130    -0.00173    0.10000    0.30000    0.55000    0.29000    0.27000    0.11000
    2.0000  -2.25    0.99640    0.00364    -0.00118    0.10000    0.25000    0.40000    0.30000    0.28000    0.11000
    3.0000  -3.64    1.11690    0.00615    -0.00045    0.10000    0.25000    0.36000    0.30000    0.29000    0.08000
    """)


class AtkinsonBoore2003SSlabCascadiaNSHMP2008(AtkinsonBoore2003SSlabCascadia,
                                              AtkinsonBoore2003SSlabNSHMP2008):
    """
    Combines :class:`AtkinsonBoore2003SSlabNSHMP2008` for NSHMP site
    amplification with :class:`AtkinsonBoore2003SSlabCascadia` for Cascadia.
    """
    pass


class AtkinsonBoore2003SSlabJapan(AtkinsonBoore2003SSlab):
    """
    Extends :class:`AtkinsonBoore2003SSlab` but substitutes values for c1 from
    Table 3 which incorporate correction factors for Japan.
    """

    COEFFS_SSLAB = CoeffsTable(sa_damping=5, table="""\
    IMT      c1      c2         c3         c4         c5          c6         c7         sigma      s1        s2
    pga      0.10    0.69090    0.01130    -0.00202    0.19000    0.24000    0.29000    0.27000    0.23000    0.14000
    0.0400   0.68    0.63273    0.01275    -0.00234    0.15000    0.20000    0.20000    0.25000    0.24000    0.07000
    0.1000   0.61    0.66675    0.01080    -0.00219    0.15000    0.23000    0.20000    0.28000    0.27000    0.07000
    0.2000   0.70    0.69186    0.00572    -0.00192    0.15000    0.27000    0.25000    0.28000    0.26000    0.10000
    0.4000   0.07    0.77270    0.00173    -0.00178    0.13000    0.37000    0.38000    0.28000    0.26000    0.10000
    1.0000  -0.98    0.87890    0.00130    -0.00173    0.10000    0.30000    0.55000    0.29000    0.27000    0.11000
    2.0000  -2.44    0.99640    0.00364    -0.00118    0.10000    0.25000    0.40000    0.30000    0.28000    0.11000
    3.0000  -3.73    1.11690    0.00615    -0.00045    0.10000    0.25000    0.36000    0.30000    0.29000    0.08000
    """)


class AtkinsonBoore2003SSlabJapanNSHMP2008(AtkinsonBoore2003SSlabJapan,
                                           AtkinsonBoore2003SSlabNSHMP2008):
    """
    Combines :class:`AtkinsonBoore2003SSlabNSHMP2008` for NSHMP site
    amplification with :class:`AtkinsonBoore2003SSlabJapan` for Japan.

    Validation test vector was generated by applying increments in columns 1
    and 2 of Table 3 to test vector for
    AtkinsonBoore2003SSlabCascadiaNSHMP2008.
    """
    pass
