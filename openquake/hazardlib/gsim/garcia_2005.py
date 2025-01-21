# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:'GarciaEtAl2005SSlab',
:class:'GarciaEtAl2005SSlabVert'
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import SA, PGA, PGV


def _compute_mean(C, g, ctx, imt):
    """
    Compute mean according to equation on Table 2, page 2275.
    """
    mag = ctx.mag
    hypo_depth = ctx.hypo_depth
    delta = 0.00750 * 10 ** (0.507 * mag)

    # computing R for different values of mag
    R = np.where(mag < 6.5, np.sqrt(ctx.rhypo ** 2 + delta ** 2),
                 np.sqrt(ctx.rrup ** 2 + delta ** 2))

    mean = (
        # 1st term
        C['c1'] + C['c2'] * mag +
        # 2nd term
        C['c3'] * R -
        # 3rd term
        C['c4'] * np.log10(R) +
        # 4th term
        C['c5'] * hypo_depth)
    # convert from base 10 to base e
    if imt == PGV():
        mean = np.log(10 ** mean)
    else:
        # convert from cm/s**2 to g
        mean = np.log((10 ** mean) * 1e-2 / g)
    return mean


def _get_stddevs(C):
    """
    Return standard deviations as defined in table 2, pag 2275.
    """
    # the standard deviation values are converted from base 10 to base e
    stds = np.array([C['s_t'], C['s_e'], C['s_r']])
    return np.log(10 ** stds)


class GarciaEtAl2005SSlab(GMPE):
    """
    Implements GMPE developed by Garcia, D., Singh, S. K., Harraiz, M,
    Ordaz, M., and Pacheco, J. F. and published in BSSA as:

    "Inslab earthquakes of Central Mexico: Peak ground-motion parameters and
    response spectra", vol. 95, No. 6, pp. 2272-2282."

    The original formulation predict peak ground acceleration (PGA), in
    cm/s*s, peak ground velocity PGV (cm/s) and 5% damped pseudo-acceleration
    response spectra (PSA) in cm/s*s for the geometric average of the
    maximum component of the two horizontal component of ground motion (see
    last paragraph of Summary in pag. 2272

    The GMPE predicted values for Mexican inslab events and NEHRP B site
    condition.
    """

    #: Supported tectonic region type is subduction intraslab,
    #: given that the equations have been derived using Mexican inslab
    #: events
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration. See Table 2 in page 1865
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {SA, PGA, PGV}

    #: Supported intensity measure component is the geometric average of
    #  the maximum of the two horizontal components
    #: :attr:`openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`,
    #: see Data processing in page 2274.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    #: See Tables 2 and 3, page 2275.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: No site parameters required
    #: All data from 51 hard (NEHRP B) sites
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and focal depth
    #: See equation (1) in pag 2274
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is Rrup (closest distance to fault surface for
    #: the larger events, Mw > 6.5) or Rhypo (hypocentral distance for the
    #: rest (both in kilometers) as explained in page 2274
    REQUIRES_DISTANCES = {'rrup', 'rhypo'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _compute_mean(C, g, ctx, imt)
            sig[m], tau[m], phi[m] = _get_stddevs(C)

    #: Equation coefficients for geometric average of the maximum of the two
    #: horizontal components, as described in Table 2 on pp. 2275, but
    #: generated from a Fortran implementation code provided by Daniel Garcia
    #: (higher precision than in the paper).
    #: The original IMT values are defined as frequencies values.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT   c1       c2        c3       c4   c5       s_t      s_r      s_e
    0.04  0.02645  0.58792  -0.00430  1.0  0.00700  0.31829  0.30777  0.08115
    0.05  0.10949  0.58046  -0.00433  1.0  0.00753  0.33560  0.32329  0.09005
    0.07  0.22907  0.56961  -0.00429  1.0  0.00826  0.33640  0.32126  0.09979
    0.10  0.40746  0.54939  -0.00414  1.0  0.00774  0.33431  0.31785  0.10358
    0.20  0.05215  0.58676  -0.00369  1.0  0.00689  0.27971  0.24464  0.13559
    0.30 -0.26507  0.62932  -0.00331  1.0  0.00485  0.27649  0.22833  0.15592
    0.40 -0.55235  0.64414  -0.00280  1.0  0.00483  0.27187  0.23607  0.13484
    0.50 -0.81731  0.67453  -0.00243  1.0  0.00351  0.26432  0.24081  0.10898
    0.75 -1.31580  0.70924  -0.00198  1.0  0.00371  0.27422  0.25957  0.08843
    1.00 -1.75050  0.75555  -0.00168  1.0  0.00296  0.27728  0.26232  0.08985
    1.50 -2.30120  0.80760  -0.00144  1.0  0.00167  0.28030  0.26085  0.10261
    2.00 -2.75190  0.84564  -0.00123  1.0  0.00137  0.26353  0.24282  0.10240
    3.00 -3.34700  0.89255  -0.00092  1.0  0.00085  0.26279  0.22360  0.13806
    4.00 -3.87460  0.93748  -0.00079  1.0  0.00093  0.25328  0.22226  0.12147
    5.00 -4.26750  0.96929  -0.00074  1.0  0.00104  0.24643  0.21638  0.11793
    pga  -0.23170  0.58726  -0.00394  1.0  0.00767  0.28520  0.26662  0.10123
    pgv  -2.35950  0.70759  -0.00235  1.0  0.00436  0.25745  0.23917  0.09529
    """)


class GarciaEtAl2005SSlabVert(GarciaEtAl2005SSlab):
    """
    Extend :class:`GarciaEtAl2005SSlab`

    Implements GMPE developed by Garcia, D., Singh, S. K., Harraiz, M,
    Ordaz, M., and Pacheco, J. F. and published in BSSA as:

    "Inslab earthquakes of Central Mexico: Peak ground-motion parameters and r
    esponse spectra", vol. 95, No. 6, pp. 2272-2282."

    The original formulation predict peak ground acceleration (PGA), in
    cm/s*s, peak ground velocity PGV (cm/s) and 5% damped pseudo-acceleration
    response spectra (PSA) in cm/s*s for the vertical component of ground
    motion (see last paragraph of Summary in pag. 2272

    The GMPE predicted values for Mexican inslab events and NEHRP B site
    """

    #: Equation coefficients for Vertical Component, as described in Table 3
    #: on pp 2275.
    #: The original imt values are defined as frequencies values
    COEFFS = CoeffsTable(sa_damping=5, table="""\
     IMT    c1     c2      c3      c4     c5      s_t   s_r   s_e
     0.04  -0.300  0.620  -0.0041  1.00   0.0060  0.31  0.30  0.07
     0.05  -0.200  0.620  -0.0043  1.00   0.0070  0.32  0.31  0.08
     0.07  -0.060  0.600  -0.0041  1.00   0.0070  0.32  0.31  0.09
     0.10  -0.040  0.590  -0.0039  1.00   0.0070  0.31  0.29  0.11
     0.20  -0.070  0.590  -0.0033  1.00   0.0040  0.26  0.22  0.14
     0.30  -0.200  0.600  -0.0029  1.00   0.0030  0.26  0.22  0.15
     0.40  -0.700  0.640  -0.0022  1.00   0.0030  0.26  0.23  0.13
     0.50  -0.900  0.660  -0.0018  1.00   0.0020  0.26  0.23  0.11
     0.75  -1.300  0.690  -0.0014  1.00   0.0020  0.25  0.22  0.11
     1.00  -1.800  0.750  -0.0010  1.00   0.0010  0.27  0.24  0.12
     1.50  -2.400  0.800  -0.0008  1.00   0.0004  0.26  0.23  0.12
     2.00  -2.800  0.830  -0.0006  1.00  -0.0005  0.27  0.24  0.14
     3.00  -3.300  0.880  -0.0005  1.00  -0.0004  0.28  0.23  0.17
     4.00  -4.000  0.950  -0.0004  1.00  -0.0003  0.27  0.23  0.15
     5.00  -4.400  0.980  -0.0003  1.00  -0.0002  0.26  0.22  0.14
     pga   -0.400  0.600  -0.0036  1.00   0.0060  0.27  0.25  0.11
     pgv   -2.400  0.700  -0.0018  1.00   0.0020  0.24  0.21  0.11
    """)
