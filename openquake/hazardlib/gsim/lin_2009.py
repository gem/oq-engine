# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation, Chung-Han Chan
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
Module exports :class:`Lin2009`
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _get_distance_term(C, mag, rrup):
    """
    Returns the distance scaling term
    """
    return (C['C4'] + C['C5'] * (mag - 6.3)) * np.log(
        np.sqrt(rrup ** 2. + np.exp(C['H']) ** 2.))


def _get_fault_type_dummy_variables(rake):
    """
    Defines the fault type dummy variables for normal faulting (f_n) and
    reverse faulting (f_r) from rake. Classification based on that
    found in the original fortran code of Lin (2009)
    """
    f_n, f_r = np.zeros_like(rake), np.zeros_like(rake)
    f_n[(rake >= -120) & (rake <= -60)] = 1.  # normal
    f_r[(rake >= 30) & (rake <= 150)] = 1.  # reverse
    return f_n, f_r


def _get_magnitude_term(C, mag):
    """
    Returns the magnitude scaling term.
    """
    lny = C['C1'] + C['C3'] * (8.5 - mag) ** 2.
    return np.where(mag > 6.3,
                    lny - C['H'] * C['C5'] * (mag - 6.3),
                    lny + C['C2'] * (mag - 6.3))


def _get_site_response_term(C, vs30):
    """
    Returns the site amplification term
    """
    return C['C8'] * np.log(vs30 / 1130.0)


def _get_style_of_faulting_term(C, rake):
    """
    Returns the style of faulting factor
    """
    f_n, f_r = _get_fault_type_dummy_variables(rake)
    return C['C6'] * f_n + C['C7'] * f_r


class Lin2009(GMPE):
    """
    Implements GMPE developed by Po-Shen Lin and published as "Ground-motion
    attenuation relationship and path-effect study using Taiwan Data set"
    (Ph.D. dissertation of National Central University, Taiwan).
    This class implements the equations for 'crustal events'.
    """

    #: Supported tectonic region type is active shallow crust.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see Table 4.1 in pages 48-49.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is geometric mean
    #: of two horizontal components, see equation 4.1 page 46.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types is total, see equation 4.1 page 46.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameter is only Vs30 (used to distinguish rock).
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake see
    #: equation 4.1 page 46.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is rupture distance, see equation 4.1
    #: page 46.
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (
                _get_magnitude_term(C, ctx.mag) +
                _get_distance_term(C, ctx.mag, ctx.rrup) +
                _get_style_of_faulting_term(C, ctx.rake) +
                _get_site_response_term(C, ctx.vs30))
            sig[m] = C['sigma']

    #: Coefficient table for rock sites, see table 3 page 227.
    COEFFS = CoeffsTable(sa_damping=5.0, table="""\
    IMT       C1      C2       C3       C4      C5       H       C6      C7       C8  sigma
    pga   1.0109  0.3822   0.0000  -1.1634  0.1722  1.5184  -0.1907  0.1322  -0.4741  0.5363
    0.01  1.0209  0.3822  -0.0003  -1.1633  0.1722  1.5184  -0.1922  0.1314  -0.4738  0.5360
    0.02  1.0416  0.3822   0.0017  -1.1668  0.1722  1.5184  -0.1942  0.1311  -0.4700  0.5349
    0.03  1.1961  0.3822   0.0038  -1.2028  0.1722  1.5184  -0.1990  0.1314  -0.4741  0.5419
    0.04  1.3834  0.3822   0.0087  -1.2499  0.1722  1.5184  -0.1959  0.1362  -0.4806  0.5506
    0.05  1.5612  0.3822   0.0153  -1.2957  0.1722  1.5184  -0.1922  0.1417  -0.4911  0.5607
    0.06  1.6907  0.3822   0.0210  -1.3218  0.1722  1.5184  -0.1984  0.1500  -0.4900  0.5718
    0.07  1.7673  0.3822   0.0261  -1.3336  0.1722  1.5184  -0.2011  0.1557  -0.4920  0.5800
    0.08  1.8689  0.3822   0.0273  -1.3440  0.1722  1.5184  -0.1947  0.1627  -0.4944  0.5887
    0.09  1.9430  0.3822   0.0276  -1.3435  0.1722  1.5184  -0.2011  0.1589  -0.4910  0.5894
    0.10  2.0218  0.3822   0.0254  -1.3409  0.1722  1.5184  -0.1817  0.1607  -0.4825  0.5911
    0.15  2.0521  0.3822   0.0100  -1.2578  0.1722  1.5184  -0.1851  0.1212  -0.4804  0.5812
    0.20  2.0333  0.3822  -0.0091  -1.1769  0.1722  1.5184  -0.2265  0.0999  -0.4350  0.5715
    0.25  1.9887  0.3822  -0.0293  -1.1153  0.1722  1.5184  -0.2355  0.0994  -0.4101  0.5715
    0.30  1.8827  0.3822  -0.0459  -1.0726  0.1722  1.5184  -0.2163  0.1036  -0.4361  0.5768
    0.35  1.7459  0.3822  -0.0600  -1.0307  0.1722  1.5184  -0.1949  0.1029  -0.4507  0.5739
    0.40  1.6821  0.3822  -0.0737  -1.0116  0.1722  1.5184  -0.1955  0.1099  -0.4734  0.5696
    0.45  1.6139  0.3822  -0.0861  -0.9939  0.1722  1.5184  -0.2011  0.1178  -0.4927  0.5699
    0.50  1.5288  0.3822  -0.0960  -0.9755  0.1722  1.5184  -0.2089  0.1142  -0.5035  0.5681
    0.60  1.3081  0.3822  -0.1133  -0.9407  0.1722  1.5184  -0.2212  0.1016  -0.5546  0.5731
    0.70  1.1383  0.3822  -0.1292  -0.9193  0.1722  1.5184  -0.1900  0.1036  -0.6037  0.5703
    0.80  1.0757  0.3822  -0.1442  -0.9167  0.1722  1.5184  -0.1865  0.1058  -0.6319  0.5723
    0.90  0.9935  0.3822  -0.1577  -0.9104  0.1722  1.5184  -0.1643  0.1165  -0.6577  0.5736
    1.00  0.8642  0.3822  -0.1687  -0.9001  0.1722  1.5184  -0.1505  0.1372  -0.6916  0.5741
    1.50  0.3150  0.3822  -0.2006  -0.8696  0.1722  1.5184  -0.0377  0.1572  -0.7582  0.5743
    2.00 -0.1760  0.3822  -0.2190  -0.8328  0.1722  1.5184   0.0780  0.1660  -0.7863  0.5696
    2.50 -0.4103  0.3822  -0.2319  -0.8415  0.1722  1.5184   0.0907  0.1648  -0.7939  0.5521
    3.00 -0.5019  0.3822  -0.2431  -0.8684  0.1722  1.5184   0.1195  0.1790  -0.7754  0.5296
    3.50 -0.7206  0.3822  -0.2479  -0.8689  0.1722  1.5184   0.1206  0.1629  -0.7673  0.5256
    4.00 -0.9383  0.3822  -0.2493  -0.8618  0.1722  1.5184   0.1267  0.1262  -0.7457  0.5285
    4.40 -1.0405  0.3822  -0.2559  -0.8472  0.1722  1.5184   0.1655  0.1486  -0.7042  0.5239
    5.00 -1.3694  0.3822  -0.2535  -0.8287  0.1722  1.5184   0.2208  0.1648  -0.6955  0.5240
    """)


class Lin2009AdjustedSigma(Lin2009):
    """
    Implements the Lin (2009) GMPE with the total sigma adjusted according to
    the values in Cheng et al. (2013):
    C. -T. Cheng, P. -S. Hsieh, P. -S. Lin, Y. -T. Yen, C. -H. Chan (2013)
    Probability Seismic Hazard Mapping of Taiwan
    """
    #: Coefficient table for rock sites, see table 3 page 227.
    COEFFS = CoeffsTable(sa_damping=5.0, table="""\
    IMT       C1      C2       C3       C4      C5       H       C6      C7       C8  sigma
    pga   1.0109  0.3822   0.0000  -1.1634  0.1722  1.5184  -0.1907  0.1322  -0.4741  0.627
    0.01  1.0209  0.3822  -0.0003  -1.1633  0.1722  1.5184  -0.1922  0.1314  -0.4738  0.627
    0.02  1.0416  0.3822   0.0017  -1.1668  0.1722  1.5184  -0.1942  0.1311  -0.4700  0.627
    0.03  1.1961  0.3822   0.0038  -1.2028  0.1722  1.5184  -0.1990  0.1314  -0.4741  0.640
    0.04  1.3834  0.3822   0.0087  -1.2499  0.1722  1.5184  -0.1959  0.1362  -0.4806  0.655
    0.05  1.5612  0.3822   0.0153  -1.2957  0.1722  1.5184  -0.1922  0.1417  -0.4911  0.670
    0.06  1.6907  0.3822   0.0210  -1.3218  0.1722  1.5184  -0.1984  0.1500  -0.4900  0.681
    0.07  1.7673  0.3822   0.0261  -1.3336  0.1722  1.5184  -0.2011  0.1557  -0.4920  0.691
    0.08  1.8689  0.3822   0.0273  -1.3440  0.1722  1.5184  -0.1947  0.1627  -0.4944  0.699
    0.09  1.9430  0.3822   0.0276  -1.3435  0.1722  1.5184  -0.2011  0.1589  -0.4910  0.700
    0.10  2.0218  0.3822   0.0254  -1.3409  0.1722  1.5184  -0.1817  0.1607  -0.4825  0.705
    0.15  2.0521  0.3822   0.0100  -1.2578  0.1722  1.5184  -0.1851  0.1212  -0.4804  0.691
    0.20  2.0333  0.3822  -0.0091  -1.1769  0.1722  1.5184  -0.2265  0.0999  -0.4350  0.676
    0.25  1.9887  0.3822  -0.0293  -1.1153  0.1722  1.5184  -0.2355  0.0994  -0.4101  0.679
    0.30  1.8827  0.3822  -0.0459  -1.0726  0.1722  1.5184  -0.2163  0.1036  -0.4361  0.686
    0.35  1.7459  0.3822  -0.0600  -1.0307  0.1722  1.5184  -0.1949  0.1029  -0.4507  0.692
    0.40  1.6821  0.3822  -0.0737  -1.0116  0.1722  1.5184  -0.1955  0.1099  -0.4734  0.695
    0.45  1.6139  0.3822  -0.0861  -0.9939  0.1722  1.5184  -0.2011  0.1178  -0.4927  0.699
    0.50  1.5288  0.3822  -0.0960  -0.9755  0.1722  1.5184  -0.2089  0.1142  -0.5035  0.699
    0.60  1.3081  0.3822  -0.1133  -0.9407  0.1722  1.5184  -0.2212  0.1016  -0.5546  0.704
    0.70  1.1383  0.3822  -0.1292  -0.9193  0.1722  1.5184  -0.1900  0.1036  -0.6037  0.710
    0.80  1.0757  0.3822  -0.1442  -0.9167  0.1722  1.5184  -0.1865  0.1058  -0.6319  0.718
    0.90  0.9935  0.3822  -0.1577  -0.9104  0.1722  1.5184  -0.1643  0.1165  -0.6577  0.723
    1.00  0.8642  0.3822  -0.1687  -0.9001  0.1722  1.5184  -0.1505  0.1372  -0.6916  0.728
    1.50  0.3150  0.3822  -0.2006  -0.8696  0.1722  1.5184  -0.0377  0.1572  -0.7582  0.738
    2.00 -0.1760  0.3822  -0.2190  -0.8328  0.1722  1.5184   0.0780  0.1660  -0.7863  0.726
    2.50 -0.4103  0.3822  -0.2319  -0.8415  0.1722  1.5184   0.0907  0.1648  -0.7939  0.709
    3.00 -0.5019  0.3822  -0.2431  -0.8684  0.1722  1.5184   0.1195  0.1790  -0.7754  0.707
    3.50 -0.7206  0.3822  -0.2479  -0.8689  0.1722  1.5184   0.1206  0.1629  -0.7673  0.708
    4.00 -0.9383  0.3822  -0.2493  -0.8618  0.1722  1.5184   0.1267  0.1262  -0.7457  0.707
    4.40 -1.0405  0.3822  -0.2559  -0.8472  0.1722  1.5184   0.1655  0.1486  -0.7042  0.717
    5.00 -1.3694  0.3822  -0.2535  -0.8287  0.1722  1.5184   0.2208  0.1648  -0.6955  0.715
    """)
