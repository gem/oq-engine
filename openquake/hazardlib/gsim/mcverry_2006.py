# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Module exports :class:`McVerry2006Asc`, :class:`McVerry2006SInter`,
:class:`McVerry2006SSlab`, :class:`McVerry2006Volc`,
:class:`McVerry2006AscSC`, :class:`McVerry2006SInterSC`,
:class:`McVerry2006SSlabSC`, :class:`McVerry2006VolcSC`.
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class McVerry2006Asc(GMPE):
    """
    Implements GMPE developed by G. McVerry, J. Zhao, N.A. Abrahamson,
    P. Somerville published as "New Zealand Acceleration Response Spectrum
    Attenuation Relations for Crustal and Subduction Zone Earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.39,
    no. 1, p. 1-58, March 2006.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/39(1)0001.pdf
    Last accessed 10 September 2014.

    This class implements the GMPE for Active Shallow Crust
    earthquakes (Asc suffix).

    The GMPE distinguishes between rock, stiff soil and soft soil
    which respectively equate to the New Zealand site class combined A/B
    C, and D. No model is provided for New Zealand site class E
    The rake angle is also taken into account to
    distinguish between faulting mechanisms. A hanging-wall term is noted in
    the functional form of the model in the paper but is not used at present.
    Furthermore, a Rvolc (volcanic path distance) is noted in the functional
    form but this is not implemented in the McVerry2006Asc model, it is
    implemented in a seperate GMPE McVerry2006Volc where Rvol=Rrup as this
    is how it is implemented in Stirling et al. 2012.

    This is a legacy class based on the original implementation of McVerry
    et al. (2006), where the site terms are incorrectly implemented as
    functions of Vs30. The New Zealand site classification boundaries do not
    depend on Vs30 and so this class will yield erroneous results for some
    site locations. Instead, calling `McVerry2006AscSC` and specifying site
    class values in the .ini file will give the correct results.
    """

    #: Supported tectonic region type for base class is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are PGA and SA. PGA is assumed to
    #: have same coefficients as SA(0.00)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the stronger of two
    #: horizontal components (see Section 6 paragraph 2, page 21)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = \
        const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation types are Inter, Intra and Total
    # (see equations 8-9 page 29)
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: The legacy implementation of the McVerry model takes vs30 and maps
    #  to New Zealand's categorical site classification scheme
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude, and rake and hypocentral
    # depth rake is for determining fault style flags. Hypo depth is for
    # subduction GMPEs
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake', 'hypo_depth'))

    #: Required distance measure is RRup (paragraphy 3, page 26) which is
    # defined as nearest distance to the source.
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        # Compute SA with primed coeffs and PGA with both unprimed and
        # primed coeffs
        C = self.COEFFS_PRIMED[imt]
        C_PGA = self.COEFFS_PRIMED[PGA()]
        C_PGA_unprimed = self.COEFFS_UNPRIMED[PGA()]

        # Get S term to determine if consider site term is applied
        S = self._get_site_class(sites)
        # Abrahamson and Silva (1997) hanging wall term. This is not used
        # in the latest version of GMPE but is defined in functional form in
        # the paper so we keep it here as a placeholder
        f4HW = self._compute_f4(C, rup.mag, dists.rrup)

        # Flags for rake angles
        CN, CR = self._get_fault_mechanism_flags(rup.rake)

        # Get volcanic path distance which Rvol=0 for current implementation
        # of McVerry2006Asc, but kept here as placeholder for future use
        rvol = self._get_volcanic_path_distance(dists.rrup)

        # Get delta_C and delta_D terms for site class
        delta_C, delta_D = self._get_deltas(sites)
        # Compute lnPGA_ABCD primed
        lnPGAp_ABCD = self._compute_mean(C_PGA, S, rup.mag, dists.rrup, rvol,
                                         rup.hypo_depth, CN, CR, f4HW,
                                         delta_C, delta_D)

        # Compute lnPGA_ABCD unprimed
        lnPGA_ABCD = self._compute_mean(C_PGA_unprimed, S, rup.mag, dists.rrup,
                                        rvol, rup.hypo_depth, CN, CR, f4HW,
                                        delta_C, delta_D)

        # Compute lnSA_ABCD
        lnSAp_ABCD = self._compute_mean(C, S, rup.mag, dists.rrup, rvol,
                                        rup.hypo_depth, CN, CR, f4HW,
                                        delta_C, delta_D)

        # Stage 3: Equation 6 SA_ABCD(T). This is lnSA_ABCD
        # need to calculate final lnSA_ABCD from non-log values but return log
        mean = np.log(np.exp(lnSAp_ABCD) *
                      (np.exp(lnPGA_ABCD) / np.exp(lnPGAp_ABCD)))

        # Compute standard deviations
        C_STD = self.COEFFS_STD[imt]
        stddevs = self._get_stddevs(
            C_STD, rup.mag, stddev_types, sites
        )

        return mean, stddevs

    def _compute_mean(self, C, S, mag, rrup, rvol, hypo_depth, CN, CR, f4HW,
                      delta_C, delta_D):
        """
        Compute mean value on site class A,B,C,D (equation 4)
        returns lnSA_ABCD
        """

        # Stage 1: compute PGA_ABCD and PGA'_ABCD which are then used in
        # equation 6
        # Equation 1 PGA unprimed version
        lnSA_AB = self._compute_mean_on_rock(C, mag, rrup, rvol, hypo_depth,
                                             CN, CR, f4HW)

        # Equation 4 PGA unprimed version
        lnSA_ABCD = lnSA_AB + S *\
            self._compute_nonlinear_soil_term(C, lnSA_AB, delta_C, delta_D)

        return lnSA_ABCD

    def _compute_mean_on_rock(self, C, mag, rrup, rvol, hypo_depth, CN, CR,
                              f4HW):
        """
        Compute mean value on site class A/B (equation 1 on page 22)
        """

        lnSA_AB = (
            # line 1 of equation 1
            C['c1'] + C['c4as'] * (mag - 6) +
            # line 2
            C['c3as'] * (8.5 - mag) ** 2 +
            # line 3
            C['c5'] * rrup +
            # line 3 and 4
            (C['c8'] + C['c6as'] * (mag - 6)) *
            np.log((rrup ** 2 + C['c10as'] ** 2) ** 0.5) +
            # line 5
            C['c46'] * rvol +
            # line 6
            C['c32'] * CN + C['c33as'] * CR + f4HW
        )

        return lnSA_AB

    def _compute_nonlinear_soil_term(self, C, lnSA_AB, delta_C, delta_D):
        """
        Compute mean value on site class C/D (equation 4 on page 22 without
        the first term)
        """

        lnSA_CD = (
            # line 1 equation 4 without first term (lnSA_AB)
            C['c29'] * delta_C +
            # line 2 and 3
            (C['c30as'] * np.log(np.exp(lnSA_AB) + 0.03) + C['c43']) * delta_D
            )

        return lnSA_CD

    def _get_stddevs(self, C, mag, stddev_types, sites):
        """
        Return standard deviation as defined on page 29 in
        equation 8a,b,c and 9.
        """
        num_sites = sites.vs30.size
        sigma_intra = np.zeros(num_sites)

        # interevent stddev
        tau = sigma_intra + C['tau']

        # intraevent std (equations 8a-8c page 29)
        if mag < 5.0:
            sigma_intra += C['sigmaM6'] - C['sigSlope']
        elif 5.0 <= mag < 7.0:
            sigma_intra += C['sigmaM6'] + C['sigSlope'] * (mag - 6)
        else:
            sigma_intra += C['sigmaM6'] + C['sigSlope']

        std = []

        for stddev_type in stddev_types:
            if stddev_type == const.StdDev.TOTAL:
                # equation 9 page 29
                std += [np.sqrt(sigma_intra**2 + tau**2)]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                std.append(sigma_intra)
            elif stddev_type == const.StdDev.INTER_EVENT:
                std.append(tau)

        return std

    def _get_site_class(self, sites):
        """
        Return site class flag (0 if vs30 > 760, that is rock, or 1 if vs30 <=
        760, that is deep soil)
        """
        vs30 = sites.vs30
        S = np.zeros_like(vs30)
        S[vs30 <= 760] = 1

        return S

    def _get_volcanic_path_distance(self, rrup):
        """
        Computes the path length in km through the Taupo Volcanic Zone
        NOTE: For the NZ Seismic Hazard Model this term is only used for
        sources with "Normal Volcanic" faulting type and the term is applied
        to the whole path length (i.e. rvol = rrup)
        In order to test the NSHM against OQ, the NSHM model approach is
        implemented here as a seperate GMPE for volcanic travel paths. For
        the crustal model of McVerry2006Asc rvol is always equal to 0
        """

        return 0

    def _get_fault_mechanism_flags(self, rake):
        """
        Return the fault mechanism flag CN and CR, page 23
        CN = -1 for normal (-146<rake<-33), 0 otherwise
        CR = 0.5 for reverse-oblique (33<rake<66), 1 for reverse (67<rake<123)
        and 0 otherwise
        """

        CN, CR = 0, 0

        # Pure Normal: rake = -90
        if rake > -147 and rake < -33:
            CN = -1

        # Pure Reverse: rake = 90
        if rake > 67 and rake < 123:
            CR = 1

        # Pure Oblique Reverse: rake = 45
        if rake > 33 and rake < 66:
            CR = 0.5

        return CN, CR

    def _get_deltas(self, sites):
        """
        Return delta's for equation 4
        delta_C = 1 for site class C (360<=Vs30<760), 0 otherwise
        delta_D = 1 for site class D (Vs30<=360), 0 otherwise
        """
        vs30 = sites.vs30
        delta_C = np.zeros(len(vs30))
        delta_C[(vs30 >= 360) & (vs30 < 760)] = 1

        delta_D = np.zeros(len(vs30))
        delta_D[vs30 < 360] = 1

        return delta_C, delta_D

    def _compute_f4(self, C, mag, rrup):
        """
        Abrahamson and Silva 1997 f4 term for hanging wall effects.
        This is in McVerry equation 1 but is not used (Section 6.1 page 27)
        Compute f4 term (eq. 7, 8, and 9, page 106)
        """
        fhw_m = 0
        fhw_r = np.zeros_like(rrup)

        if mag <= 5.5:
            fhw_m = 0
        elif 5.5 < mag < 6.5:
            fhw_m = mag - 5.5
        else:
            fhw_m = 1

        idx = (rrup > 4) & (rrup <= 8)
        fhw_r[idx] = C['ca9'] * (rrup[idx] - 4.) / 4.

        idx = (rrup > 8) & (rrup <= 18)
        fhw_r[idx] = C['ca9']

        idx = (rrup > 18) & (rrup <= 24)
        fhw_r[idx] = C['ca9'] * (1 - (rrup[idx] - 18.) / 7.)

        f4 = fhw_m * fhw_r

        # Not used in current implementation of McVerry 2006, but keep here
        # for future use (return f4)

        return 0

    #: Coefficient table (table 3, page 108)
    COEFFS_PRIMED = CoeffsTable(sa_damping=5, table="""\
    imt	c1	   c3as     c4as     c5      c6as     c8      ca9     c10as   c11     c12y     c13y     c15      c17     c18y    c19y     c20      c24      c29      c30as   c32      c33as    c43      c46
    pga     0.18130  0.00000 -0.14400 -0.00846 0.17000 -0.75519 0.37000 5.60000 8.10697 1.41400  0.00000 -2.55200 -2.48795 1.78180 0.55400  0.01622 -0.41369	0.44307 -0.23000 0.20000  0.26000 -0.29648 -0.03301
    0.075   1.36561  0.03000 -0.14400 -0.00889 0.17000 -0.94568 0.37000 5.58000 8.68782 1.41400  0.00000 -2.70700 -2.54215 1.78180 0.55400  0.01850 -0.48652	0.31139 -0.28000 0.20000  0.26000 -0.48366 -0.03452
    0.10    1.77717  0.02800 -0.14400 -0.00837 0.17000 -1.01852 0.37000 5.50000 9.37929 1.41400 -0.00110 -2.65500 -2.60945 1.78180 0.55400  0.01740 -0.61973	0.34059 -0.28000 0.20000  0.26000 -0.43854 -0.03595
    0.20    1.39535 -0.01380 -0.14400 -0.00940 0.17000 -0.78199 0.37000 5.10000 10.6148 1.41400 -0.00270 -2.52800 -2.70851 1.78180 0.55400  0.01542 -0.67672	0.37235 -0.24500 0.20000  0.26000 -0.29906 -0.03853
    0.30    0.44591 -0.03600 -0.14400 -0.00987 0.17000 -0.56098 0.37000 4.80000 9.40776 1.41400 -0.00360 -2.45400 -2.47668 1.78180 0.55400  0.01278 -0.59339	0.56648 -0.19500 0.20000  0.19800 -0.05184 -0.03604
    0.40    0.01645 -0.05180 -0.14400 -0.00923 0.17000 -0.51281 0.37000 4.52000 8.50343 1.41400 -0.00430 -2.40100 -2.36895 1.78180 0.55400  0.01426 -0.30579	0.69911 -0.16000 0.20000  0.15400  0.20301 -0.03364
    0.50    0.14826 -0.06350 -0.14400 -0.00823 0.17000 -0.56716 0.37000 4.30000 8.46463 1.41400 -0.00480 -2.36000 -2.40630 1.78180 0.55400  0.01287 -0.24839	0.63188 -0.12100 0.20000  0.11900  0.37026 -0.03260
    0.75   -0.21246 -0.08620 -0.14400 -0.00738 0.17000 -0.55384 0.33100 3.90000 7.30176 1.41400 -0.00570 -2.28600 -2.26512 1.78180 0.55400  0.01080 -0.01298	0.51577 -0.05000 0.20000  0.05700  0.73517 -0.02877
    1.00   -0.10451 -0.10200 -0.14400 -0.00588 0.17000 -0.65892 0.28100 3.70000 7.08727 1.41400 -0.00640 -2.23400 -2.27668 1.78180 0.55400  0.00946  0.06672	0.34048  0.00000 0.20000  0.01300  0.87764 -0.02561
    1.50   -0.48665 -0.12000 -0.14400 -0.00630 0.17000 -0.58222 0.21000 3.55000 6.93264 1.41400 -0.00730 -2.16000 -2.28347 1.78180 0.55400  0.00788 -0.02289	0.12468  0.04000 0.20000 -0.04900  0.75438 -0.02034
    2.00   -0.77433 -0.12000 -0.14400 -0.00630 0.17000 -0.58222 0.16000 3.55000 6.64496 1.41400 -0.00730 -2.16000 -2.28347 1.78180 0.55400  0.00788 -0.02289	0.12468  0.04000 0.20000 -0.04900  0.75438 -0.02034
    3.00   -1.30916 -0.17260 -0.14400 -0.00553 0.17000 -0.57009 0.08900 3.50000 5.05488 1.41400 -0.00890 -2.03300 -2.03050 1.78180 0.55400 -0.00265 -0.20537	0.14593  0.04000 0.20000 -0.15600  0.61545 -0.01673
    """)

    COEFFS_UNPRIMED = CoeffsTable(sa_damping=5, table="""\
    imt	c1	   c3as     c4as     c5      c6as     c8      ca9      c10as   c11     c12y     c13y     c15      c17     c18y    c19y    c20      c24      c29      c30as    c32      c33as    c43      c46
    pga     0.28815  0.00000 -0.14400 -0.00967 0.17000 -0.70494 0.37000 5.60000 8.68354 1.41400  0.00000 -2.55200 -2.56727 1.78180 0.55400  0.01550 -0.50962	0.30206 -0.23000 0.20000  0.26000 -0.31769 -0.03279
    0.075   1.36561  0.03000 -0.14400 -0.00889 0.17000 -0.94568 0.37000 5.58000 8.68782 1.41400  0.00000 -2.70700 -2.54215 1.78180 0.55400  0.01850 -0.48652	0.31139 -0.28000 0.20000  0.26000 -0.48366 -0.03452
    0.10    1.77717  0.02800 -0.14400 -0.00837 0.17000 -1.01852 0.37000 5.50000 9.37929 1.41400 -0.00110 -2.65500 -2.60945 1.78180 0.55400  0.01740 -0.61973	0.34059 -0.28000 0.20000  0.26000 -0.43854 -0.03595
    0.20    1.39535 -0.01380 -0.14400 -0.00940 0.17000 -0.78199 0.37000 5.10000 10.6148 1.41400 -0.00270 -2.52800 -2.70851 1.78180 0.55400  0.01542 -0.67672	0.37235 -0.24500 0.20000  0.26000 -0.29906 -0.03853
    0.30    0.44591 -0.03600 -0.14400 -0.00987 0.17000 -0.56098 0.37000 4.80000 9.40776 1.41400 -0.00360 -2.45400 -2.47668 1.78180 0.55400  0.01278 -0.59339	0.56648 -0.19500 0.20000  0.19800 -0.05184 -0.03604
    0.40    0.01645 -0.05180 -0.14400 -0.00923 0.17000 -0.51281 0.37000 4.52000 8.50343 1.41400 -0.00430 -2.40100 -2.36895 1.78180 0.55400  0.01426 -0.30579	0.69911 -0.16000 0.20000  0.15400  0.20301 -0.03364
    0.50    0.14826 -0.06350 -0.14400 -0.00823 0.17000 -0.56716 0.37000 4.30000 8.46463 1.41400 -0.00480 -2.36000 -2.40630 1.78180 0.55400  0.01287 -0.24839	0.63188 -0.12100 0.20000  0.11900  0.37026 -0.03260
    0.75   -0.21246 -0.08620 -0.14400 -0.00738 0.17000 -0.55384 0.33100 3.90000 7.30176 1.41400 -0.00570 -2.28600 -2.26512 1.78180 0.55400  0.01080 -0.01298	0.51577 -0.05000 0.20000  0.05700  0.73517 -0.02877
    1.00   -0.10451 -0.10200 -0.14400 -0.00588 0.17000 -0.65892 0.28100 3.70000 7.08727 1.41400 -0.00640 -2.23400 -2.27668 1.78180 0.55400  0.00946  0.06672	0.34048  0.00000 0.20000  0.01300  0.87764 -0.02561
    1.50   -0.48665 -0.12000 -0.14400 -0.00630 0.17000 -0.58222 0.21000 3.55000 6.93264 1.41400 -0.00730 -2.16000 -2.28347 1.78180 0.55400  0.00788 -0.02289	0.12468  0.04000 0.20000 -0.04900  0.75438 -0.02034
    2.00   -0.77433 -0.12000 -0.14400 -0.00630 0.17000 -0.58222 0.16000 3.55000 6.64496 1.41400 -0.00730 -2.16000 -2.28347 1.78180 0.55400  0.00788 -0.02289	0.12468  0.04000 0.20000 -0.04900  0.75438 -0.02034
    3.00   -1.30916 -0.17260 -0.14400 -0.00553 0.17000 -0.57009 0.08900 3.50000 5.05488 1.41400 -0.00890 -2.03300 -2.03050 1.78180 0.55400 -0.00265 -0.20537	0.14593  0.04000 0.20000 -0.15600  0.61545 -0.01673
    """)

    #: Coefficient table for standard deviation calculation (table 4, page 109)
    COEFFS_STD = CoeffsTable(sa_damping=5, table="""\
    imt    sigmaM6 sigSlope tau
    pga    0.4865 -0.1261   0.2687
    0.075  0.5281	-0.0970   0.3217
    0.10   0.5398	-0.0673   0.3088
    0.20   0.5703	-0.0243   0.2726
    0.30   0.5505	-0.0861   0.2112
    0.40   0.5627	-0.1405   0.2005
    0.50   0.5680	-0.1444   0.1476
    0.75   0.5562	-0.0932   0.1794
    1.00   0.5629	-0.0749   0.2053
    1.50   0.5394	-0.0056   0.2411
    2.00   0.5394	-0.0056   0.2411
    3.00   0.5701	 0.0934   0.2406
    """)


class McVerry2006SInter(McVerry2006Asc):
    """
    Extend :class:`McVerry2006Asc` for Subduction Interface events (SInter)

    Implements GMPE developed by G. McVerry, J. Zhao, N.A. Abrahamson,
    P. Somerville published as "New Zealand Acceleration Response Spectrum
    Attenuation Relations for Crustal and Subduction Zone Earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.39,
    no. 1, p. 1-58, March 2006.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/39(1)0001.pdf
    Last accessed 10 September 2014.

    This class implements the GMPE for Subduction Interface
    earthquakes (SInter suffix).

    The GMPE distinguishes between rock (vs30 >= 760) and deep soil
    (vs30 < 760) which equation to the New Zealand site class A and B (rock)
    and C,D and E (soil).
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    def _compute_mean_on_rock(self, C, mag, rrup, rvol, hypo_depth, CN, CR,
                              f4HW):
        """
        Compute mean value on site class A/B (equation 2 on page 22)
        """

        # Define subduction flag (page 23)
        # SI=1 for subduction interface, 0 otherwise
        # DS=0 for subduction intraslab, 0 otherwise
        SI = 1
        DS = 0

        lnSA_AB = (
            # line 1 and 2 of equation 2
            C['c11'] + (C['c12y'] + (C['c15'] - C['c17']) * C['c19y']) *
            (mag - 6) +
            # line 3
            C['c13y'] * (10 - mag) ** 3 +
            # line 4
            C['c17'] * np.log(rrup + C['c18y'] * np.exp(C['c19y'] * mag)) +
            # line 5
            C['c20'] * hypo_depth + C['c24'] * SI +
            # line 6
            C['c46'] * rvol * (1 - DS)
        )

        return lnSA_AB


class McVerry2006SSlab(McVerry2006Asc):
    """
    Extend :class:`McVerry2006Asc` for Subduction Intraslab events (SSlab)

    Implements GMPE developed by G. McVerry, J. Zhao, N.A. Abrahamson,
    P. Somerville published as "New Zealand Acceleration Response Spectrum
    Attenuation Relations for Crustal and Subduction Zone Earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.39,
    no. 1, p. 1-58, March 2006.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/39(1)0001.pdf
    Last accessed 10 September 2014.

    This class implements the GMPE for Subduction Intraslab
    earthquakes (SSlab suffix).

    The GMPE distinguishes between rock (vs30 >= 760) and deep soil
    (vs30 < 760) which equation to the New Zealand site class A and B (rock)
    and C,D and E (soil).
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    def _compute_mean_on_rock(self, C, mag, rrup, rvol, hypo_depth, CN, CR,
                              f4HW):
        """
        Compute mean value on site class A/B (equation 2 on page 22)
        """

        # Define subduction flag (page 23)
        # SI=1 for subduction interface, 0 otherwise
        # DS=1 for subduction intraslab, 0 otherwise
        SI = 0
        DS = 1

        lnSA_AB = (
            # line 1 and 2 of equation 2
            C['c11'] + (C['c12y'] + (C['c15'] - C['c17']) * C['c19y']) *
            (mag - 6) +
            # line 3
            C['c13y'] * (10 - mag) ** 3 +
            # line 4
            C['c17'] * np.log(rrup + C['c18y'] * np.exp(C['c19y'] * mag)) +
            # line 5
            C['c20'] * hypo_depth + C['c24'] * SI +
            # line 6
            C['c46'] * rvol * (1 - DS)
        )

        return lnSA_AB


class McVerry2006Volc(McVerry2006Asc):
    """
    Extend :class:`McVerry2006Asc` for earthquakes with Volcanic paths (Volc)

    Implements GMPE developed by G. McVerry, J. Zhao, N.A. Abrahamson,
    P. Somerville published as "New Zealand Acceleration Response Spectrum
    Attenuation Relations for Crustal and Subduction Zone Earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.39,
    no. 1, p. 1-58, March 2006.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/39(1)0001.pdf
    Last accessed 10 September 2014.

    This class implements the GMPE for earthquakes with Volcanic paths

    The GMPE distinguishes between rock (vs30 >= 760) and deep soil
    (vs30 < 760) which equation to the New Zealand site class A and B (rock)
    and C,D and E (soil). The rake angle is also taken into account to
    distinguish between faulting mechanisms. A hanging-wall term is noted in
    the functional form of the model in the paper but is not used at present.

    rvolc is equal to rrup
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    def _get_volcanic_path_distance(self, rrup):
        """
        Computes the path length in km through the Taupo Volcanic Zone
        NOTE: For the NZ Seismic Hazard Model this term is only used for
        sources with "Normal Volcanic" faulting type and the term is applied
        to the whole path length (i.e. rvol = rrup)
        In order to test the NSHM against OQ, the NSHM model approach is
        implemented here as a seperate GMPE for volcanic travel paths. For
        the crustal model of McVerry2006Asc rvol is always equal to 0
        """

        return rrup


class McVerry2006AscSC(McVerry2006Asc):

    #: Uses NZS1170.5 site classification. Calls of 'A' or 'B' yield the same outputs.
    # 'E' is not a valid option
    REQUIRES_SITES_PARAMETERS = set(('siteclass', ))

    def _get_deltas(self, sites):
        """
        Return delta's for equation 4
        delta_C = 1 for site class C, 0 otherwise
        delta_D = 1 for site class D, 0 otherwise
        """
        siteclass = sites.siteclass
        delta_C = np.zeros_like(siteclass, dtype=np.float)
        delta_C[siteclass == b'C'] = 1

        delta_D = np.zeros_like(siteclass, dtype=np.float)
        delta_D[siteclass == b'D'] = 1

        return delta_C, delta_D

    def _get_site_class(self, sites):
        """
        Return site class flag (0 if class A or B, that is rock, or 1 if
        class C or D).
        """
        siteclass = sites.siteclass
        S = np.zeros_like(siteclass, dtype=np.float)
        S[(siteclass == b'C') | (siteclass == b'D')] = 1

        return S

    def _get_stddevs(self, C, mag, stddev_types, sites):
        """
        Return standard deviation as defined on page 29 in
        equation 8a,b,c and 9.
        """
        num_sites = sites.siteclass.size
        sigma_intra = np.zeros(num_sites)

        # interevent stddev
        tau = sigma_intra + C['tau']

        # intraevent std (equations 8a-8c page 29)
        if mag < 5.0:
            sigma_intra += C['sigmaM6'] - C['sigSlope']
        elif 5.0 <= mag < 7.0:
            sigma_intra += C['sigmaM6'] + C['sigSlope'] * (mag - 6)
        else:
            sigma_intra += C['sigmaM6'] + C['sigSlope']

        std = []

        for stddev_type in stddev_types:
            if stddev_type == const.StdDev.TOTAL:
                # equation 9 page 29
                std += [np.sqrt(sigma_intra**2 + tau**2)]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                std.append(sigma_intra)
            elif stddev_type == const.StdDev.INTER_EVENT:
                std.append(tau)

        return std


class McVerry2006SInterSC(McVerry2006AscSC):
    """
    Extend :class:`McVerry2006AscSC` for Subduction Interface events (SInter)

    Identical to class McVerry2006SInter, except the site term is defined in
    terms of siteclass instead of Vs30.

    Implements GMPE developed by G. McVerry, J. Zhao, N.A. Abrahamson,
    P. Somerville published as "New Zealand Acceleration Response Spectrum
    Attenuation Relations for Crustal and Subduction Zone Earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.39,
    no. 1, p. 1-58, March 2006.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/39(1)0001.pdf
    Last accessed 10 September 2014.
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    def _compute_mean_on_rock(self, C, mag, rrup, rvol, hypo_depth, CN, CR,
                              f4HW):
        """
        Compute mean value on site class A/B (equation 2 on page 22)
        """

        # Define subduction flag (page 23)
        # SI=1 for subduction interface, 0 otherwise
        # DS=0 for subduction intraslab, 0 otherwise
        SI = 1
        DS = 0

        lnSA_AB = (
            # line 1 and 2 of equation 2
            C['c11'] + (C['c12y'] + (C['c15'] - C['c17']) * C['c19y']) *
            (mag - 6) +
            # line 3
            C['c13y'] * (10 - mag) ** 3 +
            # line 4
            C['c17'] * np.log(rrup + C['c18y'] * np.exp(C['c19y'] * mag)) +
            # line 5
            C['c20'] * hypo_depth + C['c24'] * SI +
            # line 6
            C['c46'] * rvol * (1 - DS)
        )

        return lnSA_AB


class McVerry2006SSlabSC(McVerry2006AscSC):
    """
    Extend :class:`McVerry2006AscSC` for Subduction Intraslab events (SSlab)

    Identical to class McVerry2006SSlab, except the site term is defined in
    terms of siteclass instead of Vs30.

    Implements GMPE developed by G. McVerry, J. Zhao, N.A. Abrahamson,
    P. Somerville published as "New Zealand Acceleration Response Spectrum
    Attenuation Relations for Crustal and Subduction Zone Earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.39,
    no. 1, p. 1-58, March 2006.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/39(1)0001.pdf
    Last accessed 10 September 2014.
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    def _compute_mean_on_rock(self, C, mag, rrup, rvol, hypo_depth, CN, CR,
                              f4HW):
        """
        Compute mean value on site class A/B (equation 2 on page 22)
        """

        # Define subduction flag (page 23)
        # SI=1 for subduction interface, 0 otherwise
        # DS=1 for subduction intraslab, 0 otherwise
        SI = 0
        DS = 1

        lnSA_AB = (
            # line 1 and 2 of equation 2
            C['c11'] + (C['c12y'] + (C['c15'] - C['c17']) * C['c19y']) *
            (mag - 6) +
            # line 3
            C['c13y'] * (10 - mag) ** 3 +
            # line 4
            C['c17'] * np.log(rrup + C['c18y'] * np.exp(C['c19y'] * mag)) +
            # line 5
            C['c20'] * hypo_depth + C['c24'] * SI +
            # line 6
            C['c46'] * rvol * (1 - DS)
        )

        return lnSA_AB


class McVerry2006VolcSC(McVerry2006AscSC):
    """
    Extend :class:`McVerry2006AscSC` for earthquakes with Volcanic paths (Volc)

    Identical to class McVerry2006Volc, except the site term is defined in
    terms of siteclass instead of Vs30.

    Implements GMPE developed by G. McVerry, J. Zhao, N.A. Abrahamson,
    P. Somerville published as "New Zealand Acceleration Response Spectrum
    Attenuation Relations for Crustal and Subduction Zone Earthquakes",
    Bulletin of the New Zealand Society for Earthquake Engineering, v.39,
    no. 1, p. 1-58, March 2006.

    URL: http://www.nzsee.org.nz/db/Bulletin/Archive/39(1)0001.pdf
    Last accessed 10 September 2014.

    This class implements the GMPE for earthquakes with Volcanic paths
    rvolc is equal to rrup
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    def _get_volcanic_path_distance(self, rrup):
        """
        Computes the path length in km through the Taupo Volcanic Zone
        NOTE: For the NZ Seismic Hazard Model this term is only used for
        sources with "Normal Volcanic" faulting type and the term is applied
        to the whole path length (i.e. rvol = rrup)
        In order to test the NSHM against OQ, the NSHM model approach is
        implemented here as a seperate GMPE for volcanic travel paths. For
        the crustal model of McVerry2006Asc rvol is always equal to 0
        """

        return rrup
