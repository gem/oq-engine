# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
:class:`ZhaoEtAl2006AscSWISS05`,
:class:`ZhaoEtAl2006AscSWISS03`,
:class:`ZhaoEtAl2006AscSWISS08`.
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.zhao_2006 import ZhaoEtAl2006Asc

from openquake.hazardlib.gsim.zhao_2006_swiss_coeffs import (
    COEFFS_FS_ROCK_SWISS05,
    COEFFS_FS_ROCK_SWISS03,
    COEFFS_FS_ROCK_SWISS08
)
from openquake.hazardlib.gsim.utils_swiss_gmpe import _apply_adjustments


class ZhaoEtAl2006AscSWISS05(ZhaoEtAl2006Asc):

    """
    This class extends :class:ZhaoEtAl2006Asc,
    adjusted to be used for the Swiss Hazard Model [2014].
    This GMPE is valid for a fixed value of vs30=700m/s

    #. kappa value
       K-adjustments corresponding to model 01 - as prepared by Ben Edwards
       K-value for PGA were not provided but infered from SA[0.01s]
       the model applies to a fixed value of vs30=700m/s to match the 
       reference vs30=1100m/s

    #. small-magnitude correction

    #. single station sigma - inter-event magnitude/distance adjustment

    Disclaimer: these equations are modified to be used for the
    Swiss Seismic Hazard Model [2014].
    The hazard modeller is solely responsible for the use of this GMPE
    in a different tectonic context.

    Model implemented by laurentiu.danciu@gmail.com
    """

    # Supported standard deviation type is only total, but reported as a
    # combination of mean and magnitude/distance single station sigma
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        sites.vs30 = 700 * np.ones(len(sites.vs30))

        mean, stddevs = super(ZhaoEtAl2006AscSWISS05, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)

        tau_ss = 'tauC'
        log_phi_ss = 1.00
        C = ZhaoEtAl2006AscSWISS05.COEFFS_ASC
        mean, stddevs = _apply_adjustments(
            C, self.COEFFS_FS_ROCK[imt], tau_ss,
            mean, stddevs, sites, rup, dists.rrup, imt, stddev_types,
            log_phi_ss)

        return mean, stddevs
    COEFFS_FS_ROCK = COEFFS_FS_ROCK_SWISS05
    #: Original Coefficient table
    COEFFS_ASC = CoeffsTable(sa_damping=5, table="""\
    IMT    a     b         c       d      e        FR     CH     C1     C2     C3     C4     sigma   QC      WC      tauC
    pga    1.101 -0.00564  0.0055  1.080  0.01412  0.251  0.293  1.111  1.344  1.355  1.420  0.604   0.0     0.0     0.303
    0.05   1.076 -0.00671  0.0075  1.060  0.01463  0.251  0.939  1.684  1.793  1.747  1.814  0.640   0.0     0.0     0.326
    0.10   1.118 -0.00787  0.0090  1.083  0.01423  0.240  1.499  2.061  2.135  2.031  2.082  0.694   0.0     0.0     0.342
    0.15   1.134 -0.00722  0.0100  1.053  0.01509  0.251  1.462  1.916  2.168  2.052  2.113  0.702   0.0     0.0     0.331
    0.20   1.147 -0.00659  0.0120  1.014  0.01462  0.260  1.280  1.669  2.085  2.001  2.030  0.692   0.0     0.0     0.312
    0.25   1.149 -0.00590  0.0140  0.966  0.01459  0.269  1.121  1.468  1.942  1.941  1.937  0.682   0.0     0.0     0.298
    0.30   1.163 -0.00520  0.0150  0.934  0.01458  0.259  0.852  1.172  1.683  1.808  1.770  0.670   0.0     0.0     0.300
    0.40   1.200 -0.00422  0.0100  0.959  0.01257  0.248  0.365  0.655  1.127  1.482  1.397  0.659   0.0     0.0     0.346
    0.50   1.250 -0.00338  0.0060  1.008  0.01114  0.247 -0.207  0.071  0.515  0.934  0.955  0.653  -0.0126  0.0116  0.338
    0.60   1.293 -0.00282  0.0030  1.088  0.01019  0.233 -0.705 -0.429 -0.003  0.394  0.559  0.653  -0.0329  0.0202  0.349
    0.70   1.336 -0.00258  0.0025  1.084  0.00979  0.220 -1.144 -0.866 -0.449 -0.111  0.188  0.652  -0.0501  0.0274  0.351
    0.80   1.386 -0.00242  0.0022  1.088  0.00944  0.232 -1.609 -1.325 -0.928 -0.620 -0.246  0.647  -0.0650  0.0336  0.356
    0.90   1.433 -0.00232  0.0020  1.109  0.00972  0.220 -2.023 -1.732 -1.349 -1.066 -0.643  0.653  -0.0781  0.0391  0.348
    1.00   1.479 -0.00220  0.0020  1.115  0.01005  0.211 -2.451 -2.152 -1.776 -1.523 -1.084  0.657  -0.0899  0.0440  0.338
    1.25   1.551 -0.00207  0.0020  1.083  0.01003  0.251 -3.243 -2.923 -2.542 -2.327 -1.936  0.660  -0.1148  0.0545  0.313
    1.50   1.621 -0.00224  0.0020  1.091  0.00928  0.248 -3.888 -3.548 -3.169 -2.979 -2.661  0.664  -0.1351  0.0630  0.306
    2.00   1.694 -0.00201  0.0025  1.055  0.00833  0.263 -4.783 -4.410 -4.039 -3.871 -3.640  0.669  -0.1672  0.0764  0.283
    2.50   1.748 -0.00187  0.0028  1.052  0.00776  0.262 -5.444 -5.049 -4.698 -4.496 -4.341  0.671  -0.1921  0.0869  0.287
    3.00   1.759 -0.00147  0.0032  1.025  0.00644  0.307 -5.839 -5.431 -5.089 -4.893 -4.758  0.667  -0.2124  0.0954  0.278
    4.00   1.826 -0.00195  0.0040  1.044  0.00590  0.353 -6.598 -6.181 -5.882 -5.698 -5.588  0.647  -0.2445  0.1088  0.273
    5.00   1.825 -0.00237  0.0050  1.065  0.00510  0.248 -6.752 -6.347 -6.051 -5.873 -5.798  0.643  -0.2694  0.1193  0.275
    """)


class ZhaoEtAl2006AscSWISS03(ZhaoEtAl2006AscSWISS05):

    """
    This class extends :class:ZhaoEtAl2006Asc,following same strategy
    as for :class:ZhaoEtAl2006AscSWISS05
    """
    COEFFS_FS_ROCK = COEFFS_FS_ROCK_SWISS03


class ZhaoEtAl2006AscSWISS08(ZhaoEtAl2006AscSWISS05):
    """
    This class extends :class:ZhaoEtAl2006Asc,following same strategy
    as for :class:ZhaoEtAl2006AscSWISS05 to be used for the
    Swiss Hazard Model [2014].
    """
    COEFFS_FS_ROCK = COEFFS_FS_ROCK_SWISS08
