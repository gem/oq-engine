# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
Module exports :class:`TusaLanger2016RepiBA08SE`,
               :class:`TusaLanger2016RepiBA08DE`,
               :class:`TusaLanger2016RepiSP87SE`,
               :class:`TusaLanger2016RepiSP87DE`,
               :class:`TusaLanger2016Rhypo`
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class TusaLanger2016RepiBA08SE(GMPE):
    """
    Implements GMPE developed by Giuseppina Tusa and Horst Langer (2016) and
    published as "Prediction of ground motion parameters for the volcanic area
    of Mount Etna" Journal of Seismology, DOI 10.1007/s10950-015-9508-x.

    GMPE derives from earthquakes in the volcanic area of Mt. Etna in the
    magnitude range 3<ML<4.8 for epicentral distances <100 km, and for soil
    classes A, B, and D. Authors do NOT derive coefficients for site class C
    due to limited data. For implementation using hypocentral distance see
    :class:`TusaLanger2016Rhypo`.

    Two functional forms were considered by the authors: Sabetta and Pugliese,
    1987 (SP87) and a simplified version of Boore and Atkinson, 2008 (BA08).
    The GMPE distinguishes between shallow volcano-tectonic events related to
    flank movements (SE, focal depths <5km) and deeper events occurring due to
    regional tectonics (DE, focal depths >5km).

    Test tables are generated from a spreadsheet provided by the authors, and
    modified according to OQ format (e.g. conversion from cm/s2 to m/s2).

    Jan 2019: After noticing an anomalous-looking spike in the response spectra
    of the TusaLanger2016RepiBA08SE model at T=0.14s, we contacted the authors
    who found a mistake in one of the coefficients in the publication. It has
    been updated according to the authors suggestion.
    """
    #: Supported tectonic region type is 'volcanic' because the
    #: equations have been derived from data from Etna (Sicily, Italy)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure types are PGA and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the maximum of two horizontal
    #: components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = \
        const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: Required site parameter is Vs30
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Required rupture parameter is magnitude.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: Required distance measure is Repi
    REQUIRES_DISTANCES = set(('repi',))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type
        C = self.COEFFS[imt]

        imean = (self._compute_magnitude(rup, C) +
                 self._compute_distance(rup, dists, C) +
                 self._get_site_amplification(sites, C))

        istddevs = self._get_stddevs(C,
                                     stddev_types,
                                     num_sites=sites.vs30.size)

        # convert from log10 to ln and from cm/s**2 to g
        mean = np.log((10.0 ** (imean - 2.0)) / g)
        # Return stddevs in terms of natural log scaling
        stddevs = np.log(10.0 ** np.array(istddevs))

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations as defined in tables below
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            for stddev_type in stddev_types)
        stddevs = [np.zeros(num_sites) + C['SigmaTot'] for _ in stddev_types]
        return stddevs

    def _compute_distance(self, rup, dists, C):
        """
        Compute the distance function, equation (9):
        """
        mref = 3.6
        rref = 1.0
        rval = np.sqrt(dists.repi ** 2 + C['h'] ** 2)
        return (C['c1'] + C['c2'] * (rup.mag - mref)) *\
            np.log10(rval / rref) + C['c3'] * (rval - rref)

    def _compute_magnitude(self, rup, C):
        """
        Compute the magnitude function, equation (9):
        """
        return C['a'] + (C['b1'] * (rup.mag)) + (C['b2'] * (rup.mag) ** 2)

    def _get_site_amplification(self, sites, C):
        """
        Compute the site amplification function given by FS = eiSi, for
        i = 1,2,3 where Si are the coefficients determined through regression
        analysis, and ei are dummy variables (0 or 1) used to denote the
        different EC8 site classes.
        """
        ssa, ssb, ssd = self._get_site_type_dummy_variables(sites)

        return (C['sA'] * ssa) + (C['sB'] * ssb) + (C['sD'] * ssd)

    def _get_site_type_dummy_variables(self, sites):
        """
        Get site type dummy variables, which classified the sites into
        different site classes based on the shear wave velocity in the
        upper 30 m (Vs30) according to the EC8 (CEN 2003):
        class A: Vs30 > 800 m/s
        class B: Vs30 = 360 - 800 m/s
        class C*: Vs30 = 180 - 360 m/s
        class D: Vs30 < 180 m/s
        *Not computed by this GMPE
        """
        ssa = np.zeros(len(sites.vs30))
        ssb = np.zeros(len(sites.vs30))
        ssd = np.zeros(len(sites.vs30))
        # Class D; Vs30 < 180 m/s.
        idx = (sites.vs30 < 180.0)
        ssd[idx] = 1.0
        # Class B; 360 m/s <= Vs30 <= 800 m/s.
        idx = (sites.vs30 >= 360.0) & (sites.vs30 < 800.0)
        ssb[idx] = 1.0
        # Class A; Vs30 > 800 m/s.
        idx = (sites.vs30 >= 800.0)
        ssa[idx] = 1.0

        for value in sites.vs30:
            if 180 <= value < 360:
                raise Exception(
                    'GMPE does not consider site class C (Vs30 = 180-360 m/s)')

        return ssa, ssb, ssd

    # Coefficients from Table 9 (PGA) and Table 12 (SA); sigma values in log
    # Correction made to coeff b2 (0.14s) by Giuseppina Tusa in email (Jan 15, 2019)
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT    a       b1      b2      c1      c2       h       c3      sA  sB      sD      SigmaIE SigmaIS SigmaTot
    pga   -0.568   0.475   0.037   -2.054  -0.015   2.317   0.006   0   0.452   0.477   0.222   0.221   0.390
    10.0  -4.794   0.827   0.054   -1.273   0.096   2.221  -0.002   0   0.363   0.340   0.164   0.243   0.351
    5.00  -4.010   0.646   0.083   -1.036   0.142   1.517  -0.003   0   0.296   0.241   0.163   0.263   0.363
    3.33  -5.200   1.456  -0.015   -0.953   0.092   1.728  -0.006   0   0.281   0.246   0.168   0.263   0.369
    2.50  -5.753   1.912  -0.069   -1.024   0.025   2.641  -0.006   0   0.343   0.353   0.158   0.255   0.359
    2.00  -5.531   2.016  -0.089   -1.139   0.037   3.044  -0.005   0   0.375   0.367   0.157   0.250   0.355
    1.67  -3.923   1.431  -0.023   -1.369   0.061   3.542  -0.003   0   0.403   0.384   0.150   0.238   0.342
    1.43  -3.023   1.184  -0.011   -1.461   0.114   3.668  -0.001   0   0.438   0.385   0.142   0.243   0.342
    1.25  -2.558   1.091  -0.014   -1.468   0.142   3.565  -0.001   0   0.433   0.379   0.131   0.246   0.341
    1.11  -1.921   0.847   0.011   -1.523   0.157   3.580   0.000   0   0.450   0.397   0.126   0.256   0.346
    1.00  -1.358   0.629   0.030   -1.522   0.191   3.356   0.000   0   0.465   0.416   0.124   0.263   0.353
    0.67  -1.348   0.824  -0.012   -1.631   0.152   3.229   0.003   0   0.532   0.510   0.128   0.247   0.339
    0.50  -2.278   1.574  -0.115   -1.897   0.075   3.761   0.005   0   0.486   0.523   0.144   0.234   0.337
    0.40  -2.601   1.771  -0.141   -1.916  -0.001   3.513   0.004   0   0.491   0.559   0.158   0.219   0.332
    0.33  -1.309   1.112  -0.051   -1.957  -0.020   3.442   0.004   0   0.460   0.510   0.178   0.212   0.339
    0.29   0.025   0.441   0.047   -2.134  -0.037   3.759   0.006   0   0.455   0.505   0.201   0.215   0.356
    0.25   0.127   0.413   0.051   -2.219  -0.051   3.695   0.007   0   0.468   0.528   0.220   0.221   0.374
    0.22   0.139   0.448   0.040   -2.259  -0.038   3.476   0.007   0   0.478   0.546   0.233   0.222   0.385
    0.20   0.136   0.455   0.038   -2.266  -0.044   3.363   0.007   0   0.468   0.576   0.240   0.223   0.392
    0.17   0.021   0.556   0.016   -2.240  -0.026   2.997   0.006   0   0.423   0.542   0.263   0.234   0.413
    0.14  -0.289   0.741  -0.013   -2.240  -0.023   2.676   0.006   0   0.403   0.516   0.277   0.236   0.428
    0.13  -0.119   0.593   0.011   -2.243  -0.035   2.402   0.007   0   0.412   0.490   0.285   0.236   0.437
    0.11  -0.015   0.476   0.031   -2.219  -0.044   2.316   0.006   0   0.411   0.456   0.288   0.233   0.439
    0.10  -0.221   0.522   0.030   -2.193  -0.062   2.300   0.006   0   0.412   0.435   0.283   0.231   0.437
    """)


class TusaLanger2016RepiBA08DE(TusaLanger2016RepiBA08SE):
    """
    Implements Tusa and Langer (2016) using the BA08 model and DE.

    Extends
    :class:`openquake.hazardlib.gsim.tusa_langer_2016.TusaLanger2016RepiBA08SE`
    because the same functional form is used, only the coefficients differ.
    """
    # Coefficients from Table 9 (PGA) and Table 13 (SA); sigma values in log
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT    a       b1      b2       c1      c2      h       c3      sA  sB      sD      SigmaIE SigmaIS SigmaTot
    pga    2.527  -0.397   0.094   -1.998   0.315   9.6080  0.000   0  -0.200   0.002   0.161   0.276   0.399
    10.0  -3.019  -0.236   0.123   -0.716   0.144   2.0850 -0.004   0   0.115   0.006   0.170   0.203   0.342
    5.00  -2.383  -0.325   0.147   -0.695   0.062   2.0800 -0.002   0   0.120   0.003   0.167   0.213   0.347
    3.33  -2.170  -0.307   0.155   -0.633   0.002   2.2200 -0.002   0   0.107  -0.023   0.162   0.226   0.359
    2.50  -2.038  -0.210   0.136   -0.620   0.053   2.1350 -0.003   0   0.132  -0.026   0.169   0.215   0.348
    2.00  -1.977  -0.056   0.106   -0.625   0.120   2.3880 -0.004   0   0.139  -0.041   0.179   0.207   0.343
    1.67  -1.893   0.048   0.088   -0.635   0.158   2.8030 -0.005   0   0.128  -0.040   0.179   0.206   0.340
    1.43  -1.656   0.065   0.078   -0.667   0.199   3.2940 -0.005   0   0.136  -0.022   0.186   0.208   0.345
    1.25  -1.441   0.059   0.075   -0.702   0.216   4.0100 -0.005   0   0.145   0.004   0.189   0.206   0.344
    1.11  -1.054   0.025   0.076   -0.834   0.229   5.5460 -0.004   0   0.140  -0.003   0.193   0.203   0.346
    1.00  -0.945   0.041   0.074   -0.871   0.226   5.5910 -0.004   0   0.140  -0.007   0.191   0.201   0.345
    0.67   0.202  -0.354   0.121   -0.902   0.244   3.9200 -0.003   0   0.151   0.050   0.183   0.197   0.340
    0.50   1.322  -0.596   0.146   -1.135   0.256   5.9340 -0.002   0   0.062   0.037   0.181   0.201   0.342
    0.40   2.073  -0.688   0.152   -1.420   0.274   7.0510  0.000   0   0.021   0.024   0.186   0.207   0.351
    0.33   2.131  -0.635   0.144   -1.484   0.277   6.8740  0.000   0   0.037   0.035   0.191   0.223   0.362
    0.29   2.496  -0.600   0.138   -1.761   0.282   8.2450  0.002   0   0.046   0.050   0.195   0.238   0.371
    0.25   2.651  -0.482   0.116   -1.953   0.305   8.8410  0.003   0   0.021   0.051   0.189   0.252   0.380
    0.22   2.967  -0.358   0.097   -2.294   0.296   10.742  0.006   0  -0.014   0.058   0.183   0.260   0.383
    0.20   3.633  -0.334   0.091   -2.764   0.299   12.651  0.009   0  -0.061   0.666   0.177   0.269   0.389
    0.17   3.837  -0.311   0.085   -2.820   0.301   13.203  0.007   0  -0.145   0.079   0.178   0.282   0.403
    0.14   3.980  -0.328   0.081   -2.811   0.316   13.357  0.006   0  -0.197   0.051   0.177   0.292   0.414
    0.13   4.139  -0.335   0.077   -2.879   0.337   13.486  0.006   0  -0.232   0.015   0.183   0.306   0.427
    0.11   3.918  -0.339   0.077   -2.736   0.342   12.535  0.005   0  -0.241  -0.025   0.186   0.312   0.434
    0.10   3.746  -0.339   0.074   -2.612   0.354   12.019  0.004   0  -0.247  -0.054   0.192   0.317   0.443
    """)


class TusaLanger2016RepiSP87SE(TusaLanger2016RepiBA08SE):
    """
    Implements Tusa and Langer (2016) using the SP87 model and SE.

    Extends
    :class:`openquake.hazardlib.gsim.tusa_langer_2016.TusaLanger2016RepiBA08SE`
    with modification to the functional form and different coefficients.
    """
    def _compute_distance(self, rup, dists, C):
        """
        Compute the distance function, equation (5).
        """
        rval = np.sqrt(dists.repi ** 2 + C['h'] ** 2)
        return C['c1'] * np.log10(rval)

    def _compute_magnitude(self, rup, C):
        """
        Compute the magnitude function, equation (5).
        """
        return C['a'] + (C['b1'] * (rup.mag))

    # Coefficients from Table 8 (PGA) and Table 10 (SA); sigma values in log
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT    a       b1      c1      h       sA  sB      sD      SigmaIE SigmaIS SigmaTot
    pga   -1.186   0.726  -1.719   1.551   0   0.357   0.376   0.223   0.229   0.393
    10.0  -5.799   1.335  -1.408   2.731   0   0.379   0.354   0.165   0.243   0.351
    5.00  -5.528   1.424  -1.274   2.510   0   0.336   0.280   0.165   0.263   0.364
    3.33  -4.975   1.464  -1.415   4.285   0   0.312   0.268   0.167   0.265   0.371
    2.50  -4.410   1.454  -1.568   5.747   0   0.354   0.348   0.156   0.258   0.360
    2.00  -4.116   1.435  -1.589   5.364   0   0.387   0.368   0.155   0.252   0.357
    1.67  -3.676   1.352  -1.611   4.623   0   0.410   0.386   0.149   0.238   0.343
    1.43  -3.328   1.265  -1.573   4.078   0   0.438   0.383   0.143   0.243   0.342
    1.25  -2.978   1.189  -1.568   3.866   0   0.432   0.378   0.132   0.247   0.341
    1.11  -2.808   1.143  -1.536   3.520   0   0.441   0.390   0.127   0.257   0.347
    1.00  -2.655   1.108  -1.530   3.248   0   0.454   0.406   0.124   0.264   0.354
    0.67  -2.077   0.954  -1.468   2.577   0   0.491   0.471   0.128   0.249   0.340
    0.50  -1.474   0.866  -1.595   2.795   0   0.426   0.468   0.145   0.238   0.339
    0.40  -1.113   0.778  -1.613   2.585   0   0.433   0.506   0.160   0.223   0.334
    0.33  -0.839   0.729  -1.662   2.575   0   0.410   0.463   0.179   0.216   0.340
    0.29  -0.739   0.725  -1.723   2.615   0   0.395   0.448   0.202   0.221   0.358
    0.25  -0.661   0.710  -1.757   2.484   0   0.396   0.458   0.220   0.229   0.377
    0.22  -0.574   0.688  -1.777   2.297   0   0.389   0.458   0.233   0.232   0.388
    0.20  -0.501   0.669  -1.795   2.247   0   0.376   0.484   0.241   0.233   0.395
    0.17  -0.357   0.643  -1.844   2.125   0   0.333   0.450   0.263   0.242   0.415
    0.14  -0.275   0.623  -1.873   1.921   0   0.307   0.417   0.277   0.244   0.430
    0.13  -0.334   0.627  -1.863   1.669   0   0.304   0.440   0.286   0.245   0.439
    0.11  -0.427   0.640  -1.843   1.593   0   0.303   0.341   0.289   0.242   0.442
    0.10  -0.538   0.653  -1.814   1.556   0   0.306   0.322   0.285   0.241   0.440
    """)


class TusaLanger2016RepiSP87DE(TusaLanger2016RepiSP87SE):
    """
    Implements Tusa and Langer (2016) using the SP87 model and DE.

    Extends
    :class:`openquake.hazardlib.gsim.tusa_langer_2016.TusaLanger2016RepiSP87SE`
    because the same functional form is used, only the coefficients differ.
    """
    # Coefficients from Table 8 (PGA) and Table 11 (SA); sigma values in log
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT    a       b1      c1      h        sA  sB      sD      SigmaIE SigmaIS SigmaTot
    pga   -0.377   0.765  -1.824   9.5270   0  -0.202   0.004   0.162   0.277   0.402
    10.0  -4.942   0.877  -1.035   6.1470   0   0.122   0.013   0.172   0.204   0.344
    5.00  -4.444   0.853  -0.879   4.4510   0   0.133   0.017   0.170   0.213   0.349
    3.33  -4.039   0.841  -0.841   4.6740   0   0.120  -0.011   0.165   0.227   0.361
    2.50  -3.804   0.871  -0.886   5.6350   0   0.141  -0.019   0.172   0.216   0.350
    2.00  -3.470   0.899  -1.015   7.4860   0   0.138  -0.044   0.181   0.208   0.345
    1.67  -3.164   0.923  -1.134   8.8600   0   0.123  -0.048   0.181   0.207   0.342
    1.43  -3.007   0.926  -1.140   9.0160   0   0.132  -0.029   0.187   0.209   0.348
    1.25  -2.838   0.928  -1.169   9.5550   0   0.138  -0.006   0.191   0.207   0.348
    1.11  -2.642   0.920  -1.200   9.7200   0   0.132  -0.013   0.194   0.204   0.348
    1.00  -2.555   0.913  -1.182   9.2180   0   0.134  -0.015   0.192   0.201   0.348
    0.67  -2.242   0.895  -1.130   6.9400   0   0.152   0.050   0.185   0.197   0.344
    0.50  -1.567   0.858  -1.305   8.1620   0   0.056   0.031   0.185   0.201   0.346
    0.40  -1.268   0.840  -1.359   7.5770   0   0.018   0.023   0.190   0.207   0.355
    0.33  -1.201   0.839  -1.349   6.9760   0   0.032   0.034   0.194   0.223   0.366
    0.29  -1.072   0.833  -1.385   6.9500   0   0.045   0.055   0.197   0.239   0.375
    0.25  -0.908   0.825  -1.442   6.8940   0   0.023   0.061   0.190   0.253   0.384
    0.22  -0.697   0.806  -1.505   7.4290   0   0.001   0.083   0.183   0.262   0.387
    0.20  -0.535   0.794  -1.558   7.6410   0  -0.031   0.109   0.177   0.271   0.393
    0.17  -0.097   0.777  -1.763   9.0800   0  -0.116   0.119   0.177   0.284   0.406
    0.14   0.215   0.758  -1.907   10.038   0  -0.172   0.085   0.176   0.294   0.416
    0.13   0.215   0.758  -1.907   10.038   0  -0.172   0.085   0.182   0.307   0.430
    0.11   0.239   0.747  -1.930   9.6770   0  -0.221   0.004   0.184   0.313   0.437
    0.10   0.219   0.745  -1.929   9.6990   0  -0.233  -0.031   0.191   0.318   0.446
    """)


class TusaLanger2016Rhypo(TusaLanger2016RepiBA08SE):
    """
    Implements the GMPE using the BA08 model and hypocentral distance (not
    described in Tusa and Langer, 2016). This version has been developed in the
    frame of V3-2012 INGV-DPC Project in order to perform PSHA calculations
    when topography is taken into consideration (e.g. the flanks of Mt Etna),
    hence dependence on vertical distance is required.

    Extends
    :class:`openquake.hazardlib.gsim.tusa_langer_2016.TusaLanger2016RepiBA08SE`
    because the same functional form is used, only the distance type and
    coefficients differ.
    """
    # Required distance measure is Rhypo
    REQUIRES_DISTANCES = set(('rhypo', ))

    def _compute_distance(self, rup, dists, C):
        """
        Compute the distance function, equation (9):
        """
        mref = 3.6
        rref = 1.0
        rval = np.sqrt(dists.rhypo ** 2 + C['h'] ** 2)
        return (C['c1'] + C['c2'] * (rup.mag - mref)) *\
            np.log10(rval / rref) + C['c3'] * (rval - rref)

    # Coefficients provided by Giuseppina Tusa in excel file
    # 'SpectralAccXLaura.xlsx' (email dated May 29, 2016) with modification
    # to pga coefficients in Catania (personal communication, July, 2016);
    # sigma values in log
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT    a        b1       b2       c1       c2       h        c3          sA  sB        sD        SigmaTot
    pga    0.3290   0.1050   0.0760  -2.1110   0.0390   1.5530   0.0060000   0   0.45000   0.45700   0.3940
    0.10   0.8594   0.0525   0.0790  -2.2258   0.0066   1.8689   0.0068670   0   0.41397   0.42120   0.4424
    0.20   1.0619   0.0418   0.0804  -2.2684   0.0194   2.6969   0.0072450   0   0.47176   0.56672   0.3960
    0.25   0.9928   0.0316   0.0904  -2.2318   0.0067   3.1724   0.0067460   0   0.47069   0.51751   0.3779
    0.40  -1.8031   1.4272  -0.1051  -1.9414   0.0496   3.0608   0.0047120   0   0.49105   0.54594   0.3353
    0.50  -1.4907   1.2390  -0.0806  -1.9292   0.1235   3.3918   0.0049110   0   0.48505   0.50924   0.3401
    1.00  -0.6283   0.3082   0.0638  -1.5327   0.2391   2.7319   0.0005733   0   0.46483   0.40585   0.3549
    1.25  -1.8557   0.7888   0.0174  -1.4873   0.1883   3.0522  -0.0006545   0   0.43149   0.36715   0.3426
    2.00  -4.8586   1.7503  -0.0610  -1.1999   0.0767   2.8470  -0.0043670   0   0.36832   0.34906   0.3567
    """)
