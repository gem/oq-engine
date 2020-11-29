# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
Module exports :class:`LanzanoEtAl2019`.
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class LanzanoEtAl2019_RJB_OMO(GMPE):
    """
    Implements GMPE developed by G.Lanzano, L.Luzi, F.Pacor, L.Luzi,
    C.Felicetta, R.Puglia, S. Sgobba, M. D'Amico and published as "A Revised
    Ground-Motion Prediction Model for Shallow Crustal Earthquakes in Italy",
    Bull Seismol. Soc. Am., DOI 10.1785/0120180210

    SA are given up to 10 s.

    The prediction is valid for RotD50, which is the median of the
    distribution of the intensity measures, obtained from the combination
    of the two horizontal components across all nonredundant azimuths
    (Boore, 2010).
    """
    #: Supported tectonic region type is 'active shallow crust' because the
    #: equations have been derived from data from Italian database ITACA, as
    #: explained in the 'Introduction'.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is R Joyner-Boore distance (eq. 1).
    REQUIRES_DISTANCES = {'rjb'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.

        C = self.COEFFS[imt]

        imean = (self._compute_magnitude(rup, C) +
                 self._compute_distance(rup, dists, C) +
                 self._site_amplification(sites, C) +
                 self._get_mechanism(rup, C))

        istddevs = self._get_stddevs(C,
                                     stddev_types,
                                     num_sites=len(sites.vs30))

        # Convert units to g, but only for PGA and SA (not PGV):
        if imt.name in "SA PGA":
            mean = np.log((10.0 ** (imean - 2.0)) / g)
        else:
            # PGV:
            mean = np.log(10.0 ** imean)

        # Return stddevs in terms of natural log scaling
        stddevs = np.log(10.0 ** np.array(istddevs))
        # mean_LogNaturale = np.log((10 ** mean) * 1e-2 / g)

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations as defined in table 1.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(C['tau'] ** 2 + C['phi_S2S'] ** 2 +
                                       C['phi_0'] ** 2) + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(np.sqrt(C['phi_S2S'] ** 2 + C['phi_0'] ** 2) +
                               np.zeros(num_sites))
        return stddevs

    def _compute_distance(self, rup, dists, C):
        """
        Compute the third term of the equation 1:

        FD(Mw,R) = [c1(Mw-Mref) + c2] * log10(R) + c3(R) (eq 4)

        Mref, h, Mh are in matrix C
        """
        R = np.sqrt(dists.rjb**2 + C['h']**2)
        return ((C['c1'] * (rup.mag - C['Mref']) + C['c2']) * np.log10(R) +
                C['c3']*R)

    def _compute_magnitude(self, rup, C):
        """
        Compute the second term of the equation 1:

        b1 * (Mw-Mh) for M<=Mh
        b2 * (Mw-Mh) otherwise
        """
        dmag = rup.mag - C["Mh"]
        if rup.mag <= C["Mh"]:
            mag_term = C['a'] + C['b1'] * dmag
        else:
            mag_term = C['a'] + C['b2'] * dmag
        return mag_term

    def _site_amplification(self, sites, C):
        """
        Compute the fourth term of the equation 1 :
        The functional form Fs in Eq. (1) represents the site amplification and
        it is given by FS = klog10(V0/800) , where V0 = Vs30 when Vs30 <= 1500
        and V0=1500 otherwise
        """
        v0 = np.ones_like(sites.vs30) * 1500.
        v0[sites.vs30 < 1500] = sites.vs30
        return C['k'] * np.log10(v0/800)

    def _get_mechanism(self, rup, C):
        """
        Compute the part of the second term of the equation 1 (FM(SoF)):
        Get fault type dummy variables
        """
        SS, TF, NF = self._get_fault_type_dummy_variables(rup)
        return C['f1'] * SS + C['f2'] * TF

    def _get_fault_type_dummy_variables(self, rup):
        """
        Fault type (Strike-slip, Normal, Thrust/reverse) is
        derived from rake angle.
        Rakes angles within 30 of horizontal are strike-slip,
        angles from 30 to 150 are reverse, and angles from
        -30 to -150 are normal.
        """
        SS, TF, NF = 0, 0, 0
        if np.abs(rup.rake) <= 30.0 or (180.0 - np.abs(rup.rake)) <= 30.0:
            # strike-slip
            SS = 1
        elif rup.rake > 30.0 and rup.rake < 150.0:
            # reverse
            TF = 1
        else:
            # normal
            NF = 1
        return SS, TF, NF

    #: Coefficients from SA PGA and PGV from esupp Table S2

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT          a      b1       b2      c1       c2      c3        k      f1       f2     tau phi_S2S   phi_0   Mh   Mref       h
    pgv     2.0774  0.3486   0.1359  0.2841  -1.4565 -0.0006  -0.5928  0.0411  -0.0123  0.1389  0.1641  0.1939  5.7 5.0155  5.9310
    pga     3.4210  0.1940  -0.0220  0.2871  -1.4056 -0.0029  -0.3946  0.0860   0.0105  0.1560  0.2206  0.2001  5.5 5.3240  6.9237
    0.010   3.4245  0.1925  -0.0227  0.2875  -1.4066 -0.0029  -0.3936  0.0860   0.0105  0.1562  0.2207  0.2001  5.5 5.3266  6.9262
    0.025   3.4832  0.1745  -0.0303  0.2918  -1.4244 -0.0028  -0.3809  0.0869   0.0121  0.1585  0.2232  0.2009  5.5 5.3727  6.9274
    0.040   3.6506  0.1159  -0.0647  0.3111  -1.4695 -0.0027  -0.3429  0.0870   0.0161  0.1645  0.2325  0.2039  5.5 5.4969  6.9816
    0.050   3.7316  0.0938  -0.0847  0.3185  -1.4685 -0.0029  -0.3201  0.0900   0.0129  0.1679  0.2389  0.2069  5.5 5.5554  7.1218
    0.070   3.8298  0.0775  -0.1075  0.3220  -1.4693 -0.0035  -0.2775  0.1028   0.0229  0.1762  0.2513  0.2102  5.5 5.5054  7.2905
    0.100   3.8042  0.1360  -0.0692  0.2909  -1.4017 -0.0043  -0.2687  0.1148   0.0248  0.1787  0.2637  0.2114  5.5 5.3797  7.2743
    0.150   3.6501  0.2565   0.0271  0.2340  -1.3112 -0.0047  -0.3208  0.1109   0.0199  0.1667  0.2596  0.2113  5.5 5.0966  6.6928
    0.200   3.5441  0.3561   0.0935  0.1984  -1.2809 -0.0045  -0.3768  0.0942   0.0117  0.1612  0.2494  0.2085  5.5 4.8016  6.1274
    0.250   3.4904  0.4259   0.1431  0.1769  -1.2710 -0.0039  -0.4276  0.0803   0.0098  0.1541  0.2350  0.2074  5.5 4.7851  6.0908
    0.300   3.4415  0.4718   0.1926  0.1615  -1.2950 -0.0032  -0.4771  0.0777   0.0061  0.1466  0.2249  0.2059  5.5 4.7168  5.9795
    0.350   3.3447  0.5063   0.2151  0.1565  -1.3178 -0.0030  -0.5307  0.0728   0.0027  0.1411  0.2176  0.2080  5.5 4.3812  5.8131
    0.400   3.2551  0.5331   0.2422  0.1503  -1.2806 -0.0027  -0.5563  0.0662   0.0012  0.1352  0.2142  0.2046  5.5 4.4599  5.8073
    0.450   3.3643  0.5365   0.1855  0.1490  -1.3018 -0.0023  -0.5950  0.0648   0.0049  0.1283  0.2116  0.2038  5.8 4.4734  5.9505
    0.500   3.3609  0.5595   0.2002  0.1446  -1.3578 -0.0018  -0.6175  0.0643   0.0049  0.1293  0.2101  0.2021  5.8 4.3062  6.0828
    0.600   3.3139  0.6160   0.2430  0.1309  -1.3751 -0.0012  -0.6515  0.0518  -0.0107  0.1388  0.2085  0.2013  5.8 4.2622  6.0960
    0.700   3.2215  0.6410   0.2631  0.1310  -1.3778 -0.0008  -0.6770  0.0348  -0.0138  0.1487  0.2079  0.1990  5.8 4.2243  5.8706
    0.750   3.1946  0.6615   0.2754  0.1280  -1.3817 -0.0006  -0.6770  0.0326  -0.0106  0.1493  0.2061  0.1985  5.8 4.2193  5.9399
    0.800   3.1477  0.6745   0.2843  0.1274  -1.3805 -0.0005  -0.6808  0.0302  -0.0093  0.1489  0.2060  0.1975  5.8 4.1788  5.9158
    0.900   3.0439  0.6961   0.2908  0.1308  -1.3712 -0.0004  -0.6902  0.0244  -0.0057  0.1510  0.2088  0.1965  5.8 4.1280  5.6500
    1.000   2.9330  0.7163   0.2992  0.1330  -1.3581 -0.0003  -0.7010  0.0188  -0.0027  0.1499  0.2100  0.1953  5.8 4.0069  5.4265
    1.200   2.7970  0.7523   0.3149  0.1357  -1.3419 -0.0002  -0.7211  0.0157  -0.0124  0.1476  0.2085  0.1935  5.8 4.0000  5.2114
    1.400   2.6682  0.7789   0.3311  0.1374  -1.3265 -0.0001  -0.7304  0.0123  -0.0159  0.1480  0.2089  0.1905  5.8 4.0000  5.0912
    1.600   2.5723  0.7847   0.3394  0.1454  -1.3309  0.0000  -0.7386  0.0034  -0.0231  0.1468  0.2120  0.1888  5.8 4.0644  5.1206
    1.800   2.4933  0.7900   0.3305  0.1542  -1.3290  0.0000  -0.7538 -0.0080  -0.0354  0.1518  0.2126  0.1862  5.8 4.1264  5.2737
    2.000   2.4060  0.7777   0.3200  0.1685  -1.3283  0.0000  -0.7472 -0.0111  -0.0375  0.1533  0.2112  0.1855  5.8 4.2175  5.3911
    2.500   2.2251  0.7790   0.3281  0.1828  -1.3594  0.0000  -0.7333 -0.0299  -0.0447  0.1581  0.2057  0.1873  5.8 4.0841  5.2885
    3.000   2.0654  0.7855   0.3586  0.1917  -1.3622 -0.0001  -0.6907 -0.0523  -0.0535  0.1731  0.2047  0.1856  5.8 4.0000  5.0090
    3.500   1.9414  0.8007   0.3925  0.2003  -1.3460 -0.0003  -0.6573 -0.0831  -0.0498  0.1695  0.2000  0.1859  5.8 4.0000  5.2239
    4.000   1.8089  0.7742   0.3863  0.2210  -1.3605 -0.0005  -0.6361 -0.0851  -0.0482  0.1729  0.1933  0.1877  5.8 4.0000  5.1428
    4.500   1.7067  0.7607   0.3932  0.2319  -1.3607 -0.0005  -0.6212 -0.0852  -0.0421  0.1751  0.1913  0.1875  5.8 4.0000  4.9945
    5.000   1.5675  0.7352   0.4076  0.2445  -1.3444 -0.0006  -0.5996 -0.0740  -0.0295  0.1725  0.1850  0.1921  5.8 4.0995  4.9183
    6.000   1.8016  0.6866   0.2400  0.2681  -1.4273 -0.0004  -0.5583 -0.0530  -0.0282  0.1608  0.1827  0.1869  6.3 4.0726  5.6196
    7.000   1.6597  0.6688   0.2910  0.2737  -1.4576 -0.0002  -0.5294 -0.0165  -0.0064  0.1640  0.1793  0.1786  6.3 4.0598  5.3393
    8.000   1.5146  0.6053   0.2927  0.3021  -1.4528 -0.0002  -0.5055  0.0012  -0.0011  0.1605  0.1738  0.1769  6.3 4.2884  5.4985
    9.000   1.4187  0.5414   0.2752  0.3283  -1.4351  0.0000  -0.5015  0.0084   0.0036  0.1594  0.1667  0.1771  6.3 4.5885  6.0000
    10.000  1.3142  0.4897   0.2536  0.3484  -1.4422  0.0000  -0.4867  0.0170   0.0044  0.1581  0.1617  0.1776  6.3 4.6827  6.2391
    """)


class LanzanoEtAl2019_RUP_OMO(LanzanoEtAl2019_RJB_OMO):
    """
    Implements GMPE developed by G.Lanzano, L.Luzi, F.Pacor, L.Luzi,
    C.Felicetta, R.Puglia, S. Sgobba, M. D'Amico and published as "A Revised
    Ground-Motion Prediction Model for Shallow Crustal Earthquakes in Italy",
    Bull Seismol. Soc. Am., DOI 10.1785/0120180210

    SA are given up to 10 s.

    The prediction is valid for RotD50, which is the median of the
    distribution of the intensity measures, obtained from the combination
    of the two horizontal components across all nonredundant azimuths
    (Boore, 2010).
    """
    #: Supported tectonic region type is 'active shallow crust' because the
    #: equations have been derived from data from Italian database ITACA, as
    #: explained in the 'Introduction'.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is Rrup (eq. 1).
    REQUIRES_DISTANCES = {'rrup'}

    def _compute_distance(self, rup, dists, C):
        """
        Compute the third term of the equation 1:

        FD(Mw,R) = [c1(Mw-Mref) + c2] * log10(R) + c3(R) (eq 4)

        Mref, h, Mh are in matrix C

        """
        R = np.sqrt(dists.rrup**2 + C['h']**2)
        return ((C['c1'] * (rup.mag - C['Mref']) + C['c2']) * np.log10(R) +
                C['c3']*R)

    #: Coefficients from SA PGA and PGV from esupp Table S2
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT          a       b1       b2      c1       c2       c3        k      f1      f2     tau phi_S2S   phi_0   Mh   Mref       h
    pgv     2.3828   0.2389   0.0261  0.3406  -1.5179        0  -0.5767  0.0497  0.0049  0.1377  0.1658  0.1947  5.7 5.4986  5.2603
    pga     3.8476   0.0774  -0.1420  0.3479  -1.5533  -0.0019  -0.3805  0.0982  0.0313  0.1615  0.2215  0.2010  5.5 5.7161  6.6412
  0.010     3.8506   0.0759  -0.1428  0.3483  -1.5537  -0.0019  -0.3795  0.0982  0.0313  0.1617  0.2216  0.2010  5.5 5.7183  6.6340
  0.025     3.9192   0.0558  -0.1528  0.3537  -1.5755  -0.0018  -0.3665  0.0994  0.0335  0.1649  0.2240  0.2017  5.5 5.7583  6.6418
  0.040     4.1175  -0.0090  -0.1936  0.3763  -1.6562  -0.0016  -0.3280  0.1004  0.0391  0.1728  0.2330  0.2047  5.5 5.7990  6.7564
  0.050     4.2101  -0.0339  -0.2163  0.3851  -1.6588  -0.0017  -0.3051  0.1038  0.0364  0.1770  0.2393  0.2073  5.5 5.8514  6.9511
  0.070     4.3117  -0.0506  -0.2391  0.3886  -1.6360  -0.0023  -0.2626  0.1170  0.0468  0.1850  0.2515  0.2107  5.5 5.8719  7.2254
  0.100     4.2619   0.0155  -0.1931  0.3536  -1.5607  -0.0032  -0.2542  0.1288  0.0482  0.1871  0.2641  0.2116  5.5 5.7817  7.1942
  0.150     4.0281   0.1491  -0.0843  0.2905  -1.4559  -0.0038  -0.3066  0.1234  0.0410  0.1748  0.2598  0.2119  5.5 5.5070  6.0448
  0.200     3.9582   0.2581  -0.0068  0.2493  -1.4304  -0.0035  -0.3632  0.1054  0.0309  0.1663  0.2501  0.2095  5.5 5.4083  6.0815
  0.250     3.8975   0.3350   0.0505  0.2239  -1.4165  -0.0029  -0.4143  0.0907  0.0279  0.1578  0.2357  0.2085  5.5 5.4514  6.0144
  0.300     3.8390   0.3841   0.1031  0.2070  -1.4441  -0.0023  -0.4637  0.0874  0.0234  0.1496  0.2259  0.2074  5.5 5.3969  5.8135
  0.350     3.7428   0.4229   0.1305  0.1994  -1.4408  -0.0020  -0.5175  0.0821  0.0191  0.1437  0.2185  0.2099  5.5 5.2807  5.8177
  0.400     3.6333   0.4526   0.1604  0.1917  -1.4190  -0.0018  -0.5434  0.0748  0.0170  0.1359  0.2149  0.2065  5.5 5.2222  5.6501
  0.450     3.7155   0.4556   0.1097  0.1894  -1.4373  -0.0014  -0.5822  0.0725  0.0201  0.1287  0.2124  0.2057  5.8 5.2479  5.7811
  0.500     3.7226   0.4791   0.1250  0.1848  -1.4793  -0.0009  -0.6049  0.0719  0.0202  0.1287  0.2113  0.2037  5.8 5.2518  5.9417
  0.600     3.6683   0.5366   0.1687  0.1707  -1.5050  -0.0002  -0.6392  0.0589  0.0046  0.1366  0.2100  0.2025  5.8 5.2219  5.7576
  0.700     3.5476   0.5606   0.1871  0.1717  -1.4920        0  -0.6643  0.0414  0.0016  0.1444  0.2095  0.2003  5.8 5.1693  5.2232
  0.750     3.4860   0.5836   0.2010  0.1676  -1.4706        0  -0.6634  0.0391  0.0046  0.1444  0.2075  0.1999  5.8 5.1608  5.2391
  0.800     3.4153   0.5963   0.2090  0.1674  -1.4564        0  -0.6668  0.0364  0.0058  0.1436  0.2073  0.1990  5.8 5.1084  5.0193
  0.900     3.2838   0.6204   0.2174  0.1696  -1.4269        0  -0.6751  0.0303  0.0092  0.1440  0.2100  0.1981  5.8 5.0273  4.6889
  1.000     3.1646   0.6394   0.2244  0.1725  -1.4104        0  -0.6859  0.0244  0.0120  0.1426  0.2117  0.1965  5.8 4.9153  4.2786
  1.200     3.0001   0.6753   0.2398  0.1754  -1.3847        0  -0.7050  0.0204  0.0021  0.1377  0.2106  0.1947  5.8 4.8219  3.8903
  1.400     2.8548   0.7017   0.2555  0.1774  -1.3693        0  -0.7139  0.0169 -0.0016  0.1353  0.2111  0.1915  5.8 4.7439  3.6283
  1.600     2.7453   0.7088   0.2643  0.1849  -1.3617        0  -0.7215  0.0083 -0.0083  0.1332  0.2142  0.1895  5.8 4.7549  3.7025
  1.800     2.6642   0.7154   0.2561  0.1932  -1.3508        0  -0.7371 -0.0017 -0.0191  0.1382  0.2147  0.1869  5.8 4.8131  3.9589
  2.000     2.5757   0.7028   0.2447  0.2076  -1.3471        0  -0.7308 -0.0050 -0.0212  0.1398  0.2129  0.1865  5.8 4.8507  4.1479
  2.500     2.3964   0.7033   0.2519  0.2223  -1.3743        0  -0.7169 -0.0246 -0.0291  0.1437  0.2068  0.1887  5.8 4.7204  4.1181
  3.000     2.2443   0.7064   0.2806  0.2324  -1.3939        0  -0.6756 -0.0449 -0.0392  0.1580  0.2051  0.1872  5.8 4.5967  3.6676
  3.500     2.1509   0.7197   0.3145  0.2409  -1.3057        0  -0.6454 -0.0713 -0.0377  0.1574  0.2005  0.1876  5.8      5  3.9747
  4.000     2.0269   0.6873   0.3037  0.2643  -1.3613        0  -0.6251 -0.0737 -0.0364  0.1610  0.1940  0.1896  5.8 4.8167  3.5843
  4.500     1.9351   0.6688   0.3061  0.2778  -1.3145        0  -0.6110 -0.0741 -0.0295  0.1623  0.1928  0.1894  5.8      5  3.2645
  5.000     1.8090   0.6410   0.3184  0.2915  -1.3209        0  -0.5898 -0.0632 -0.0173  0.1600  0.1873  0.1941  5.8      5  3.3548
  6.000     1.9455   0.5902   0.1564  0.3140  -1.3376        0  -0.5478 -0.0425 -0.0126  0.1510  0.1839  0.1900  6.3      5  3.9006
  7.000     1.7832   0.5733   0.2019  0.3199  -1.3375        0  -0.5198 -0.0046  0.0111  0.1555  0.1794  0.1820  6.3      5  3.7233
  8.000     1.6473   0.5074   0.2006  0.3494  -1.4464        0  -0.4956  0.0136  0.0172  0.1529  0.1737  0.1803  6.3 4.8104  4.3526
  9.000     1.5106   0.4450   0.1831  0.3751  -1.4367        0  -0.4912  0.0209  0.0217  0.1530  0.1662  0.1804  6.3 4.9296  4.5510
  10.000    1.3967   0.3901   0.1590  0.3968  -1.4233        0  -0.4766  0.0296  0.0222  0.1525  0.1615  0.1808  6.3 5.0403  4.5998
  """)


