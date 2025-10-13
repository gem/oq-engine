# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
Module exports :class:`DrouetBrazil2015`
               :class:`DrouetBrazil2015_with_depth`
"""
import numpy as np

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from scipy.constants import g


_compute_distance_term = CallableDict()


@_compute_distance_term.add(False)
def _compute_distance_term_1(depth, C, ctx, rjb):
    """
    This computes the term f2 equation 8 Drouet & Cotton (2015)
    """
    return (C['c4'] + C['c5'] * ctx.mag) * np.log(
        np.sqrt(rjb ** 2. + C['c6'] ** 2.)) + C['c7'] * rjb


@_compute_distance_term.add(True)
def _compute_distance_term_2(depth, C, ctx, rjb):
    """
    This computes the term f2 equation 8 Drouet & Cotton (2015)
    """
    return (C['c4'] + C['c5'] * ctx.mag) * np.log(
        np.sqrt(rjb ** 2. + ctx.hypo_depth ** 2.)) + C['c6'] * rjb


def _compute_magnitude_term(C, ctx):
    """
    This computes the term f1 equation 8 Drouet & Cotton (2015)
    """
    return C['c2'] * (ctx.mag - 8.0) + C['c3'] * (ctx.mag - 8.0) ** 2


def _compute_mean(depth, C, ctx, rjb):
    """
    Compute mean value according to equation 30, page 1021.
    """
    mean = (C['c1'] +
            _compute_magnitude_term(C, ctx) +
            _compute_distance_term(depth, C, ctx, rjb))
    return mean


class DrouetBrazil2015(GMPE):
    """
    Implements GMPE developed by S. Drouet unpublished for Brazil based on the
    method described in Douet & Cotton (2015) BSSA doi: 10.1785/0120140240.
    """

    #: Supported tectonic region type is stable continental crust given that
    #: the equations have been derived for Eastern North America.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see table 6, page 1022 (PGA is assumed
    #: to be equal to SA at 0.01 s)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the geometric mean of
    #: two horizontal components
    #: :attr:`~openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is only total, see equation 35, page
    #: 1021
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: No site parameters are needed
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is only magnitude, see equation 30 page
    #: 1021.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is closest distance to rupture, see equation
    #: 30 page 1021.
    REQUIRES_DISTANCES = {'rjb'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            depth = "hypo_depth" in self.REQUIRES_RUPTURE_PARAMETERS
            mean[m] = _compute_mean(depth, C, ctx, ctx.rjb)
            if imt.string.startswith(('PGA', 'SA')):  # from m/s**2 to g
                mean[m] -= np.log(g)
            elif imt.string == "PGV":  # Convert from m/s to cm/s
                mean[m] += np.log(100.0)
            sig[m] = np.sqrt(C['sigma'] ** 2 + C['tau'] ** 2)
            phi[m] = C['sigma']
            tau[m] = C['tau']

    #: Coefficient tables are constructed from the electronic suplements of
    #: the original paper.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT          c1         c2         c3         c4        c5        c6         c7     sigma       tau
    pgv    0.457169   0.230048  -0.140795  -1.785544  0.162408  7.201555  -0.002832  0.526166  0.393025
    pga    2.575109  -0.243140  -0.155164  -1.807995  0.156084  7.629410  -0.003996  0.625075  0.481226 
    0.010  2.586201  -0.242271  -0.154703  -1.808695  0.156141  7.623170  -0.004020  0.630187  0.481707 
    0.020  2.717172  -0.261739  -0.152580  -1.859646  0.160136  7.773640  -0.004048  0.688591  0.486003
    0.030  2.930319  -0.236637  -0.147729  -1.831982  0.155727  7.918015  -0.004558  0.751663  0.490319
    0.040  3.156209  -0.266436  -0.143032  -1.915769  0.162181  8.224381  -0.004350  0.779379  0.498289
    0.050  3.268731  -0.189794  -0.140262  -1.753521  0.144779  7.767181  -0.004910  0.780218  0.497182
    0.075  3.352582  -0.164010  -0.140254  -1.691894  0.140095  7.428414  -0.004756  0.706350  0.493511
    0.100  3.455122  -0.203575  -0.148680  -1.708867  0.139700  7.707583  -0.004261  0.652456  0.490010
    0.150  3.456514  -0.169395  -0.160434  -1.607720  0.131021  7.274064  -0.004025  0.587130  0.480912
    0.200  3.480893  -0.155262  -0.168476  -1.646459  0.132556  7.424609  -0.002871  0.556933  0.462619
    0.250  3.358985  -0.255601  -0.194574  -1.669187  0.134462  7.753731  -0.002732  0.533650  0.458696
    0.300  3.115954  -0.237559  -0.215762  -1.451276  0.114182  7.212529  -0.003761  0.526336  0.452876
    0.400  2.806835  -0.340296  -0.250121  -1.418762  0.114054  6.837724  -0.004081  0.519411  0.440790
    0.500  2.837393  -0.355473  -0.271003  -1.453916  0.111753  7.298391  -0.003037  0.512892  0.427910
    0.750  2.383076  -0.374649  -0.298428  -1.472297  0.117984  7.051676  -0.002899  0.507442  0.405868
    1.000  2.070536  -0.263869  -0.303220  -1.410898  0.117144  6.815268  -0.003307  0.511352  0.384417
    1.250  1.944386  -0.196142  -0.309115  -1.408815  0.116519  6.904435  -0.003017  0.511909  0.376152
    1.500  1.973072  -0.160616  -0.313180  -1.493457  0.122469  7.427893  -0.002316  0.511871  0.370833
    1.750  1.747518  -0.129961  -0.320672  -1.400692  0.116855  7.143261  -0.003402  0.508641  0.361738
    2.000  1.667278  -0.083863  -0.319818  -1.405853  0.114769  7.128404  -0.003174  0.505025  0.353357
    3.000  1.292331   0.312316  -0.263539  -1.464213  0.130085  6.416692  -0.002621  0.512370  0.344082
    """)


class DrouetBrazil2015withDepth(DrouetBrazil2015):
    """
    Implements GMPE developed by S. Drouet unpublished for Brazil based on the
    method described in Douet & Cotton (2015) BSSA doi: 10.1785/0120140240.
    Model with magnitude-dependent depth distribution and depth-dependent
    stress distribution
    """

    #: Required rupture parameter is only magnitude, see equation 30 page
    #: 1021.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Coefficient tables are constructed from the electronic supplements of
    #: the original paper.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT            c1        c2        c3        c4       c5        c6    sigma      tau
    pgv      1.296890  0.307642 -0.155927 -1.727495 0.128331 -0.002079 0.507600 0.474106 
    pga      3.393123 -0.139286 -0.169796 -1.695729 0.116686 -0.003491 0.609317 0.573384 
    0.010000 3.405471 -0.138584 -0.169352 -1.696947 0.116766 -0.003513 0.614578 0.574138 
    0.020000 3.512058 -0.152120 -0.167461 -1.725659 0.119114 -0.003688 0.674715 0.580870 
    0.030000 3.695045 -0.123957 -0.162204 -1.688566 0.114624 -0.004259 0.738161 0.585416 
    0.040000 3.856703 -0.140850 -0.157819 -1.721169 0.117496 -0.004400 0.768733 0.597967 
    0.050000 4.085005 -0.080044 -0.155124 -1.628430 0.103907 -0.004434 0.766573 0.593676 
    0.075000 4.242841 -0.056117 -0.154044 -1.601802 0.100823 -0.004025 0.691819 0.587975 
    0.100000 4.278594 -0.087360 -0.162257 -1.582776 0.098667 -0.003803 0.638952 0.582946 
    0.150000 4.358265 -0.063108 -0.173452 -1.530628 0.092988 -0.003244 0.572059 0.565676 
    0.200000 4.385790 -0.041305 -0.181717 -1.553364 0.092537 -0.002134 0.539692 0.543338 
    0.250000 4.162408 -0.135372 -0.207677 -1.531599 0.092853 -0.002369 0.520273 0.534858 
    0.300000 3.991746 -0.134064 -0.227479 -1.386035 0.078380 -0.002944 0.511192 0.519484 
    0.400000 3.746791 -0.248433 -0.261965 -1.396553 0.080903 -0.002965 0.502079 0.499394 
    0.500000 3.728968 -0.246365 -0.282618 -1.384885 0.074963 -0.002185 0.495203 0.483281 
    0.750000 3.298203 -0.278081 -0.310518 -1.431361 0.083594 -0.001906 0.488881 0.452970 
    1.000000 2.966504 -0.185734 -0.315139 -1.405592 0.087333 -0.002169 0.492014 0.426399 
    1.250000 2.810007 -0.117505 -0.320881 -1.394705 0.086834 -0.001981 0.493565 0.416078 
    1.500000 2.760153 -0.068911 -0.325231 -1.426076 0.089344 -0.001624 0.494063 0.410019 
    1.750000 2.538491 -0.052014 -0.332247 -1.367936 0.087458 -0.002541 0.491032 0.398572 
    2.000000 2.485648 -0.001655 -0.331560 -1.370772 0.084286 -0.002297 0.487175 0.392599 
    3.000000 2.205128  0.365128 -0.276508 -1.504904 0.104957 -0.001304 0.492143 0.384311
    """)
