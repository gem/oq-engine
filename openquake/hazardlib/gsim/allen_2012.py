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
Module exports :class:`Allen2012`
"""
from __future__ import division

import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import SA


class Allen2012(GMPE):
    """
    Implements GMPE developed by T. Allen and published as "Stochastic ground-
    motion prediction equations for southeastern Australian earthquakes using
    updated source and attenuation parameters", 2012, Geoscience Australia
    Record 2012/69. Document available at:
    https://www.ga.gov.au/products/servlet/controller?event=GEOCAT_DETAILS&catno=74133
    """

    #: Supported tectonic region type is stable continental crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types is spectral acceleration, see table 7,
    #: page 35
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        SA
    ])

    #: Supported intensity measure component is the median horizontal component
    #: see table 7, page 35
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.MEDIAN_HORIZONTAL

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No site parameters are needed, the GMPE is calibrated for average South
    #: East Australia site conditions (assumed consistent to Vs30 = 820 m/s)
    #: see paragraph 'Executive Summary', page VII
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter are magnitude and hypocentral depth, see
    #: paragraph 'Regression of Model Coefficients', page 32 and tables 7 and
    #: 8, pages 35, 36
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    #: Required distance measure is closest distance to rupture, see paragraph
    #: 'Regression of Model Coefficients', page 32
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        if rup.hypo_depth < 10:
            C = self.COEFFS_SHALLOW[imt]
        else:
            C = self.COEFFS_DEEP[imt]

        mean = self._compute_mean(C, rup.mag, dists.rrup)
        stddevs = self._get_stddevs(C, stddev_types, dists.rrup.shape[0])

        return mean, stddevs

    def _compute_mean(self, C, mag, rrup):
        """
        Compute mean value according to equation 18, page 32.
        """
        # see table 3, page 14
        R1 = 90.
        R2 = 150.
        # see equation 19, page 32
        m_ref = mag - 4
        r1 = R1 + C['c8'] * m_ref
        r2 = R2 + C['c11'] * m_ref
        assert r1 > 0
        assert r2 > 0
        g0 = np.log10(
            np.sqrt(np.minimum(rrup, r1) ** 2 + (1 + C['c5'] * m_ref) ** 2)
        )
        g1 = np.maximum(np.log10(rrup / r1), 0)
        g2 = np.maximum(np.log10(rrup / r2), 0)

        mean = (C['c0'] + C['c1'] * m_ref + C['c2'] * m_ref ** 2 +
                (C['c3'] + C['c4'] * m_ref) * g0 +
                (C['c6'] + C['c7'] * m_ref) * g1 +
                (C['c9'] + C['c10'] * m_ref) * g2)

        # convert from log10 to ln and units from cm/s2 to g
        mean = np.log((10 ** mean) * 1e-2 / g)

        return mean

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return total standard deviation.
        """
        # standard deviation is converted from log10 to ln
        std_total = np.log(10 ** C['sigma'])
        stddevs = []
        for _ in stddev_types:
            stddevs.append(np.zeros(num_sites) + std_total)

        return stddevs

    #COEFFS_SHALLOW = CoeffsTable(sa_damping=5, table="""\
    #IMT    c0       c1        c2        c3       c4       c5        c6        c7        c8        c9       c10       c11      sigma
    #pga    3.28432  0.71567  -0.13249  -1.86799  0.14563  1.43902  -0.00868  -0.13001  -4.82595  -3.22576  0.42194  -0.83425  0.41690
    #0.010  3.28432  0.71567  -0.13249  -1.86799  0.14563  1.43902  -0.00868  -0.13001  -4.82595  -3.22576  0.42194  -0.83425  0.41690
    #0.020  3.54527  0.70842  -0.13904  -1.95303  0.16192  1.70628  -0.15717  -0.17762  -5.03268  -3.28271  0.51030  -0.99924  0.44074
    #0.030  3.54463  0.67635  -0.12418  -1.88290  0.13507  1.59544  -0.49693  -0.02690  -5.00995  -2.96495  0.33273  -1.43516  0.43462
    #0.050  3.60836  0.60666  -0.10686  -1.86254  0.13113  1.55774  -0.44338  -0.03481  -5.22313  -3.17240  0.36202  -1.33519  0.40820
    #0.075  3.56156  0.61129  -0.10602  -1.81488  0.12555  1.49099  -0.29314  -0.06202  -5.09340  -3.35985  0.35756  -0.53397  0.39321
    #0.100  3.47534  0.64237  -0.11048  -1.76503  0.11969  1.42646  -0.18442  -0.07562  -4.97156  -3.38424  0.31066   0.33207  0.38524
    #0.150  3.32311  0.69523  -0.11818  -1.70119  0.11642  1.35222  -0.02248  -0.10494  -5.08910  -3.23179  0.21587   1.72567  0.38077
    #0.200  3.16009  0.75604  -0.12857  -1.65285  0.11637  1.26247   0.12164  -0.12168  -5.10432  -3.04893  0.16714   2.15490  0.37852
    #0.250  2.99078  0.82309  -0.14095  -1.60949  0.11657  1.15320   0.25592  -0.12702  -4.95705  -2.89363  0.15222   1.94721  0.37752
    #0.300  2.83112  0.88650  -0.15257  -1.57453  0.11656  1.06399   0.35620  -0.12683  -4.78670  -2.76591  0.14927   1.55661  0.37739
    #0.400  2.54441  0.99501  -0.17067  -1.53196  0.11566  0.99861   0.42894  -0.11962  -4.59340  -2.56596  0.14436   0.87733  0.37729
    #0.500  2.30892  1.07930  -0.18325  -1.51129  0.11448  1.01459   0.41580  -0.11079  -4.52995  -2.42254  0.13713   0.42048  0.37627
    #0.750  1.86975  1.21169  -0.20048  -1.50536  0.11975  1.08237   0.42756  -0.11400  -4.19215  -2.37489  0.15811  -0.08486  0.37204
    #1.000  1.56521  1.28082  -0.20747  -1.51961  0.13024  1.11021   0.51214  -0.13468  -3.75267  -2.51255  0.20442  -0.18177  0.37049
    #1.500  1.13314  1.31258  -0.20045  -1.53403  0.14462  1.10469   0.53358  -0.15547  -4.03287  -2.57192  0.24393   0.23082  0.36775
    #2.000  0.83828  1.29361  -0.18482  -1.53710  0.15200  1.09020   0.46481  -0.15536  -4.77854  -2.48440  0.24216   0.67205  0.36672
    #3.000  0.47788  1.23178  -0.15464  -1.55520  0.16061  1.14326   0.41713  -0.13102  -5.05414  -2.44378  0.22215   0.32849  0.36477
    #4.000  0.25651  1.16981  -0.13220  -1.57923  0.16998  1.18150   0.43967  -0.12020  -4.72557  -2.50826  0.22759  -0.13271  0.36400
    #""")

    #COEFFS_DEEP = CoeffsTable(sa_damping=5, table="""\
    #IMT    c0       c1        c2        c3       c4       c5        c6        c7        c8        c9       c10      c11      sigma
    #pga    3.34566  0.66718  -0.08950  -1.86813  0.12191  1.78942  -0.28205  -0.03110  -5.47270  -3.24500  0.38647  0.03038  0.39518
    #0.010  3.34566  0.66718  -0.08950  -1.86813  0.12191  1.78942  -0.28205  -0.03110  -5.47270  -3.24500  0.38647  0.03038  0.39518
    #0.020  3.61220  0.52023  -0.05292  -1.87946  0.11882  1.88046  -0.57242  -0.04228  -7.11743  -3.29487  0.43897  1.96844  0.41888
    #0.030  3.72726  0.51582  -0.06358  -1.91180  0.13074  1.72102  -0.56309   0.00582  -5.49800  -3.43426  0.43464  0.13521  0.41308
    #0.050  3.66826  0.58015  -0.07921  -1.86736  0.12442  1.68227  -0.47890  -0.03386  -5.46278  -3.58717  0.47329  0.06738  0.38678
    #0.075  3.58253  0.63274  -0.09359  -1.82611  0.12812  1.59087  -0.34375  -0.05052  -5.10966  -3.58666  0.41621 -0.54826  0.37283
    #0.100  3.49973  0.67696  -0.10560  -1.79769  0.13389  1.49716  -0.22696  -0.05545  -4.78735  -3.50650  0.33763 -0.81117  0.36700
    #0.150  3.31259  0.77323  -0.12568  -1.74610  0.13641  1.39093  -0.06156  -0.08265  -4.97548  -3.28921  0.22681  0.44644  0.36240
    #0.200  3.12485  0.86093  -0.14290  -1.70673  0.13960  1.32280   0.07876  -0.09631  -4.95390  -3.07425  0.17062  0.99689  0.36022
    #0.250  2.95216  0.93535  -0.15793  -1.67781  0.14542  1.26602   0.20882  -0.09453  -4.58026  -2.88227  0.14467  0.58947  0.36027
    #0.300  2.79495  0.99832  -0.17022  -1.65668  0.15081  1.22197   0.31332  -0.09061  -4.20346  -2.73596  0.13571 -0.03961  0.36032
    #0.400  2.50356  1.10267  -0.18730  -1.63048  0.15571  1.17200   0.43339  -0.09808  -3.98552  -2.59284  0.14889 -0.78844  0.35907
    #0.500  2.25471  1.18341  -0.19788  -1.61605  0.15607  1.15191   0.48503  -0.11652  -4.17594  -2.55773  0.17699 -1.00212  0.35835
    #0.750  1.78281  1.29256  -0.20567  -1.60149  0.15818  1.19091   0.53229  -0.15384  -4.56177  -2.59529  0.24625 -1.08718  0.35612
    #1.000  1.45972  1.32998  -0.20198  -1.59926  0.16411  1.26500   0.55263  -0.17196  -4.56936  -2.65121  0.29523 -1.15616  0.35470
    #1.500  1.05739  1.30779  -0.18223  -1.62215  0.18060  1.28334   0.54967  -0.17855  -4.32481  -2.67803  0.32751 -0.89189  0.35274
    #2.000  0.81445  1.25309  -0.16123  -1.65243  0.19490  1.24212   0.53353  -0.17467  -4.11726  -2.66657  0.32834 -0.45858  0.35082
    #3.000  0.50001  1.16290  -0.12883  -1.69123  0.20794  1.30190   0.54440  -0.17692  -4.08066  -2.72393  0.34504  0.09670  0.34726
    #4.000  0.28413  1.09808  -0.10780  -1.71325  0.21496  1.38058   0.56909  -0.18169  -4.10520  -2.79730  0.36649  0.17705  0.34473
    #""")

    #: Coefficients for shallow events taken from table 7, page 35
    #: Note that PGA is assumed to have coefficients equal to SA(0.1)
    COEFFS_SHALLOW = CoeffsTable(sa_damping=5, table="""\
    IMT   c0     c1      c2      c3     c4     c5      c6      c7      c8      c9     c10    c11   sigma
    pga   3.259  0.505  -0.069  -1.839  0.158  1.247  -0.204  -0.044  -5.100  -2.862  0.251 -0.639 0.412
    0.01  3.259  0.505  -0.069  -1.839  0.158  1.247  -0.204  -0.044  -5.100  -2.862  0.251 -0.639 0.412
    0.02  3.368  0.496  -0.062  -1.808  0.136  1.247  -0.486   0.017  -4.677  -2.865  0.244 -0.776 0.438
    0.03  3.511  0.471  -0.060  -1.852  0.142  1.434  -0.545   0.015  -4.983  -2.849  0.250 -1.103 0.431
    0.05  3.545  0.477  -0.063  -1.837  0.140  1.459  -0.489  -0.011  -5.109  -3.073  0.301 -1.178 0.399
    0.08  3.516  0.492  -0.068  -1.806  0.142  1.418  -0.341  -0.043  -4.994  -3.251  0.309 -0.904 0.381
    0.10  3.458  0.515  -0.073  -1.774  0.142  1.375  -0.216  -0.061  -4.849  -3.284  0.274 -0.467 0.372
    0.15  3.296  0.580  -0.082  -1.700  0.131  1.286  -0.062  -0.067  -4.641  -3.123  0.158  0.538 0.364
    0.20  3.136  0.642  -0.092  -1.648  0.127  1.214   0.072  -0.080  -4.663  -2.936  0.106  1.089 0.359
    0.25  2.998  0.692  -0.101  -1.615  0.130  1.159   0.207  -0.105  -4.828  -2.789  0.112  1.256 0.358
    0.30  2.872  0.736  -0.110  -1.593  0.135  1.121   0.317  -0.126  -4.911  -2.678  0.132  1.193 0.356
    0.40  2.623  0.818  -0.124  -1.565  0.140  1.082   0.432  -0.128  -4.484  -2.539  0.137  0.621 0.354
    0.50  2.398  0.889  -0.134  -1.548  0.140  1.070   0.468  -0.104  -3.733  -2.461  0.114 -0.111 0.352
    0.75  1.944  1.011  -0.147  -1.527  0.140  1.050   0.481  -0.088  -3.243  -2.413  0.121 -1.055 0.350
    1.00  1.616  1.078  -0.151  -1.522  0.145  1.025   0.484  -0.121  -3.942  -2.442  0.187 -1.130 0.349
    1.50  1.193  1.102  -0.142  -1.540  0.160  1.009   0.504  -0.159  -4.242  -2.499  0.256 -0.703 0.349
    2.00  0.929  1.074  -0.126  -1.564  0.175  1.016   0.522  -0.164  -3.762  -2.526  0.267 -0.293 0.348
    3.00  0.574  1.011  -0.095  -1.588  0.185  1.048   0.514  -0.158  -3.784  -2.536  0.268 -0.054 0.347
    4.00  0.340  0.954  -0.071  -1.604  0.189  1.071   0.509  -0.158  -4.199  -2.565  0.286 -0.108 0.346
    """)

    #: Coefficients for deep events taken from table 8, page 36
    #: Note that PGA is assumed to have coefficients equal to SA(0.1)
    #: Note that in the original document the c5 coefficient for 0.1 is -0.122,
    #: while it should be positive 0.122
    COEFFS_DEEP = CoeffsTable(sa_damping=5, table="""\
    IMT   c0     c1      c2      c3     c4      c5      c6      c7      c8      c9     c10    c11   sigma
    pga   3.383  0.604  -0.091  -1.929  0.175   1.429  -0.182  -0.013  -4.699  -3.149  0.316 -0.765 0.365
    0.01  3.383  0.604  -0.091  -1.929  0.175   1.429  -0.182  -0.013  -4.699  -3.149  0.316 -0.765 0.365
    0.02  3.557  0.590  -0.086  -1.940  0.162   2.186  -0.455   0.034  -4.863  -3.093  0.305 -1.284 0.390
    0.03  3.707  0.528  -0.084  -1.973  0.186   0.967  -0.455   0.002  -4.683  -3.285  0.393 -1.260 0.384
    0.05  3.739  0.546  -0.084  -1.937  0.165   1.740  -0.440   0.001  -4.337  -3.478  0.418 -1.128 0.356
    0.08  3.672  0.584  -0.089  -1.888  0.158   0.656  -0.299  -0.033  -4.186  -3.553  0.398 -1.194 0.339
    0.10  3.579  0.627  -0.097  -1.848  0.157   1.122  -0.164  -0.058  -4.049  -3.517  0.345 -1.087 0.332
    0.15  3.378  0.728  -0.113  -1.780  0.148   1.127  -0.009  -0.045  -3.626  -3.284  0.185 -0.325 0.327
    0.20  3.183  0.821  -0.128  -1.733  0.144   2.006   0.123  -0.043  -3.487  -3.059  0.108 -0.016 0.325
    0.25  3.004  0.899  -0.143  -1.701  0.148   1.902   0.260  -0.063  -3.599  -2.884  0.106 -0.177 0.325
    0.30  2.843  0.963  -0.156  -1.679  0.154   1.532   0.369  -0.084  -3.751  -2.750  0.124 -0.478 0.325
    0.40  2.550  1.065  -0.172  -1.652  0.159   1.227   0.461  -0.095  -3.856  -2.560  0.130 -0.996 0.325
    0.50  2.303  1.139  -0.181  -1.637  0.160   1.367   0.462  -0.083  -3.790  -2.437  0.109 -1.334 0.323
    0.75  1.822  1.248  -0.186  -1.615  0.158   1.708   0.453  -0.077  -3.632  -2.381  0.117 -1.557 0.319
    1.00  1.479  1.297  -0.182  -1.603  0.157   1.706   0.487  -0.101  -3.612  -2.471  0.182 -1.411 0.318
    1.50  1.071  1.274  -0.161  -1.626  0.173   1.651   0.526  -0.135  -3.723  -2.564  0.248 -0.982 0.316
    2.00  0.841  1.206  -0.139  -1.664  0.194   1.660   0.539  -0.148  -3.764  -2.581  0.261 -0.654 0.314
    3.00  0.534  1.096  -0.105  -1.707  0.218   1.616   0.598  -0.167  -3.160  -2.707  0.309 -0.405 0.311
    4.00  0.284  1.098  -0.108  -1.713  0.215   1.381   0.569  -0.182  -4.105  -2.797  0.367  0.177 0.345
    """)
