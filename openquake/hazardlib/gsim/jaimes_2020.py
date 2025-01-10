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
Module exports :class:'JaimesEtAl2020SSlab',
               :class:'JaimesEtAl2020SSlabVert',
               :class:'JaimesEtAl2020SSlabVHratio'
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def _compute_mean(C, g, ctx, imt, imc):
    """
    Return the mean value based on the selected intensity measure component
    """
    mag = ctx.mag
    dis = np.where(mag > 6.5, ctx.rrup, ctx.rhypo)
    # near-source saturation term
    delta = 0.0075 * 10 ** (0.507 * mag)
    # depth scaling
    H = np.minimum(ctx.hypo_depth, 75) - 50
    # average distance to the fault surface
    R = np.sqrt(dis ** 2 + delta ** 2)
    if imc == const.IMC.VERTICAL_TO_HORIZONTAL_RATIO:
        # Computes the mean for the 'V/H ratio' according to equation 4,
        # page 1306. The equation predicts the mean value for PGA, PGV,
        # and SA in terms of the natural logarithm.
        mean = C['c1'] + C['c2'] * mag + C['c3'] * R
    else:
        # Computes the mean for the 'horizontal or vertical component'
        # according to equation 1, page 1304. The equation
        # predicts the mean value for PGA, PGV, and SA in terms of
        # the natural logarithm.
        mean = (C['c1'] + C['c2'] * mag + C['c3'] * np.log(R) +
                C['c4'] * R + C['c5'] * H)
        # For PGA and SA, the values are convert from cm/s**2 to 'g'
        if imt != PGV():
            mean = np.log(np.exp(mean) * 1e-2 / g)

    return mean


def _get_stddevs(C, imc):
    """
    Returns the standard deviation values based on the selected
    intensity measure component
    """
    if imc == const.IMC.VERTICAL_TO_HORIZONTAL_RATIO:
        # Standar deviations for the 'V/H ratio component'
        # Between-event variability (Eq. 5b, p. 1308)
        s_b = np.sqrt(
            C['sv_b'] ** 2.0 + 
            C['sh_b'] ** 2.0 -
            2.0 * C['rho_b'] * C['sv_b'] * C['sh_b'])

        # Within-event variability (Eq. 5c, p. 1308)
        s_w = np.sqrt(
            C['sv_w'] ** 2.0 + 
            C['sh_w'] ** 2.0 -
            2.0 * C['rho_w'] * C['sv_w'] * C['sh_w'])

        # Total standard deviation (Eq. 5a, p. 1308)
        s_t = np.sqrt(s_b ** 2.0 + s_w ** 2.0)

        # Return the values
        stds = np.array([s_t, s_b, s_w])
    
    else:
        # Standard deviation for the 'horizontal or vertical component'
        stds = np.array([C['s_t'], C['s_b'], C['s_w']])

    return stds


class JaimesEtAl2020SSlab(GMPE):
    """
    Implements GMPE developed by Jaimes et al. (2020) for Mexican 
    intermediate-depth intraslab earthquake and published as:

    Jaimes M. A., García-Soto A. D. (2020) "Updated ground motion prediction
    model for Mexican intermediate-depth intraslab earthquakes including V/H
    ratios" Earthq. Spectra, 36(3):1298-1330. doi:10.1177/8755293019899947.

    The original formulation predict peak ground acceleration, PGA (cm/s**2),
    peak ground velocity, PGV (cm/s), and 5% damped pseudo-acceleration
    response spectra, PSA (cm/s**2), for the quadratic mean of the two 
    horizontal component of ground motion (see the 'Regression Analysis' 
    section on page 1304).
    
    The GMPE predicted values for Mexican intraslab events at rock sites
    (NEHRP B site condition).
    """

    #: Supported tectonic region type is subduction intraslab,
    #: given that the equations have been derived using Mexican intraslab
    #: events.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Supported intensity measure types are peak ground acceleration,
    #: peak ground velocity and spectral acceleration. See Table 2 in 
    #: page 1306.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the average of
    #  the two horizontal components.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total. See Table 2, page 1306.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT}

    #: No site parameters required
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is the magnitude and focal depth
    #: See equation 1 in page 1304
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is Rrup (closest distance to fault surface)
    #: for large events (Mw>6.5) or Rhypo (hypocentral distance) for the rest,
    #: both in kilometers, as explained in page 1304
    REQUIRES_DISTANCES = {'rrup', 'rhypo'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # Type of intensity measure component
        imc = self.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _compute_mean(C, g, ctx, imt, imc)
            sig[m], tau[m], phi[m] = _get_stddevs(C, imc)

    #: Regression coefficients for geometric average of the maximum of the two
    #: horizontal components, as described in Table 2, page 1306.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    c1      c2       c3    c4      c5      s_b   s_w   s_t      
    0.01   0.1824  1.3569  -1.0  -0.0084   0.0266  0.36  0.60  0.70
    0.02   0.3380  1.3502  -1.0  -0.0086   0.0262  0.37  0.61  0.71
    0.06   1.2826  1.2732  -1.0  -0.0088   0.0263  0.47  0.69  0.83
    0.08   1.5138  1.2680  -1.0  -0.0088   0.0272  0.42  0.69  0.81
    0.10   1.5392  1.2800  -1.0  -0.0085   0.0284  0.34  0.70  0.78
    0.20   0.4035  1.4283  -1.0  -0.0081   0.0284  0.34  0.57  0.67
    0.30  -0.7722  1.5597  -1.0  -0.0075   0.0231  0.34  0.53  0.63
    0.40  -1.4572  1.5975  -1.0  -0.0063   0.0216  0.30  0.54  0.62
    0.50  -2.0213  1.6378  -1.0  -0.0055   0.0153  0.24  0.54  0.59
    0.60  -2.3061  1.6297  -1.0  -0.0048   0.0178  0.21  0.56  0.60
    0.70  -2.5725  1.6332  -1.0  -0.0043   0.0165  0.20  0.58  0.61
    0.80  -3.0802  1.6927  -1.0  -0.0043   0.0137  0.21  0.57  0.61
    0.90  -3.5864  1.7458  -1.0  -0.0040   0.0134  0.21  0.57  0.61
    1.00  -3.9575  1.7752  -1.0  -0.0036   0.0123  0.19  0.57  0.61
    2.00  -6.2968  1.9592  -1.0  -0.0029   0.0072  0.18  0.54  0.57
    3.00  -7.5722  2.0386  -1.0  -0.0021   0.0044  0.26  0.49  0.55
    4.00  -8.7329  2.1320  -1.0  -0.0017   0.0046  0.22  0.49  0.53
    5.00  -9.6803  2.2118  -1.0  -0.0016   0.0041  0.19  0.48  0.51
    pga    0.1571  1.3581  -1.0  -0.0084   0.0268  0.35  0.60  0.70
    pgv   -5.0446  1.6401  -1.0  -0.0054   0.0135  0.25  0.54  0.60
    """)


class JaimesEtAl2020SSlabVert(JaimesEtAl2020SSlab):
    """
    Extend :class:'JaimesEtAl2020SSlab'

    Implements GMPE developed by Jaimes et al. (2020) for Mexican
    intermediate-depth intraslab earthquake and published as:

    Jaimes M. A., García-Soto A. D. (2020) "Updated ground motion prediction
    model for Mexican intermediate-depth intraslab earthquakes including V/H
    ratios" Earthq. Spectra, 36(3):1298-1330. doi:10.1177/8755293019899947.

    The original formulation predict peak ground acceleration, PGA (cm/s**2),
    peak ground velocity, PGV (cm/s), and 5% damped pseudo-acceleration
    response spectra, PSA (cm/s**2), for the vertical component of ground
    motion (see the 'Regression Analysis' section on page 1304).

    The GMPE predicted values for Mexican intraslab events at rock
    sites (NEHRP B site condition).
    """

    #: Supported intensity measure component is the vertical component.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VERTICAL

    #: Regression coefficients for vertical component, as described in Table 3,
    #: page 1307.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    c1      c2       c3    c4       c5      s_b   s_w   s_t 
    0.01   0.0312  1.3219  -1.0  -0.0080   0.0212  0.30  0.56  0.63
    0.02   0.2511  1.3173  -1.0  -0.0083   0.0208  0.32  0.58  0.66
    0.06   1.1118  1.2644  -1.0  -0.0088   0.0244  0.43  0.66  0.79
    0.08   1.1182  1.2876  -1.0  -0.0088   0.0258  0.34  0.66  0.74
    0.10   0.9560  1.3089  -1.0  -0.0085   0.0284  0.30  0.64  0.71
    0.20   0.2518  1.3753  -1.0  -0.0075   0.0204  0.29  0.53  0.61
    0.30  -0.3711  1.4290  -1.0  -0.0067   0.0146  0.29  0.51  0.59
    0.40  -1.2375  1.4938  -1.0  -0.0053   0.0133  0.24  0.52  0.57
    0.50  -1.7755  1.5277  -1.0  -0.0043   0.0076  0.21  0.54  0.58
    0.60  -2.1792  1.5471  -1.0  -0.0038   0.0093  0.22  0.54  0.58
    0.70  -2.5892  1.5791  -1.0  -0.0036   0.0102  0.19  0.54  0.57
    0.80  -3.1819  1.6390  -1.0  -0.0029   0.0077  0.21  0.53  0.57
    0.90  -3.6870  1.6933  -1.0  -0.0027   0.0074  0.19  0.54  0.58
    1.00  -3.9478  1.7053  -1.0  -0.0024   0.0075  0.20  0.55  0.58
    2.00  -6.2754  1.9082  -1.0  -0.0017   0.0006  0.23  0.53  0.58
    3.00  -7.2002  1.9455  -1.0  -0.0015   0.0007  0.32  0.50  0.60
    4.00  -8.6980  2.0912  -1.0  -0.0012   0.0014  0.27  0.51  0.58
    5.00  -9.9448  2.2137  -1.0  -0.0009  -0.0001  0.24  0.50  0.55    
    pga   -0.0082  1.3218  -1.0  -0.0079   0.0215  0.30  0.56  0.63
    pgv   -5.2592  1.6119  -1.0  -0.0044   0.0054  0.20  0.49  0.53
    """)


class JaimesEtAl2020SSlabVHratio(JaimesEtAl2020SSlab):
    """
    Extend :class:'JaimesEtAl2020SSlab'

    Implements GMPE developed by Jaimes et al. (2020) for Mexican 
    intermediate-depth intraslab earthquake and published as:

    Jaimes M. A., García-Soto A. D. (2020) "Updated ground motion prediction
    model for Mexican intermediate-depth intraslab earthquakes including V/H
    ratios" Earthq. Spectra, 36(3):1298-1330. doi:10.1177/8755293019899947.

    The original formulation predict peak ground acceleration, PGA (cm/s**2),
    peak ground velocity, PGV (cm/s), and 5% damped pseudo-acceleration
    response spectra, PSA (cm/s**2), for the V/H ratio (see the 'Regression 
    Analysis' section on page 1304).
    
    The GMPE predicted values for Mexican intraslab events at rock 
    sites (NEHRP B site condition).
    """

    #: Supported intensity measure component is the V/H ratio.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VERTICAL_TO_HORIZONTAL_RATIO

    #: Regression coefficients for V/H ratios, as described in Table 4,
    #: page 1307. The residuals between-event and within-event of the horizontal 
    # and vertical components were added to compute the between-event, within-event, 
    # and total standard deviations of the V/H ratios through the equation: 5b, 5c, 
    # and 5a (see page 1308).

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    c1       c2      c3      s_t   rho_b  rho_w  sh_b  sh_w  sv_b  sv_w
    0.01  -0.6431   0.0274  0.0005  0.33  0.743  0.844  0.36  0.60  0.30  0.56
    0.02  -0.6546   0.0313  0.0005  0.33  0.739  0.846  0.37  0.61  0.32  0.58
    0.06  -0.6953   0.0557  0.0002  0.36  0.800  0.859  0.47  0.69  0.43  0.66
    0.08  -0.8216   0.0705  0.0001  0.37  0.828  0.845  0.42  0.69  0.34  0.66
    0.10  -1.0478   0.0834  0.0003  0.36  0.822  0.851  0.34  0.70  0.30  0.64
    0.20  -0.5523  -0.0033  0.0005  0.38  0.758  0.772  0.34  0.57  0.29  0.53
    0.30  -0.0408  -0.0732  0.0006  0.37  0.704  0.770  0.34  0.53  0.29  0.51
    0.40  -0.3026  -0.0322  0.0008  0.36  0.677  0.794  0.30  0.54  0.24  0.52
    0.50  -0.2276  -0.0467  0.0011  0.35  0.685  0.789  0.24  0.54  0.21  0.54
    0.60  -0.1963  -0.0406  0.0009  0.36  0.732  0.788  0.21  0.56  0.22  0.54
    0.70  -0.3090  -0.0192  0.0007  0.39  0.764  0.759  0.20  0.58  0.19  0.54
    0.80  -0.4643  -0.0075  0.0013  0.39  0.759  0.750  0.21  0.57  0.21  0.53
    0.90  -0.4893  -0.0008  0.0012  0.40  0.775  0.745  0.21  0.57  0.19  0.54
    1.00  -0.3117  -0.0284  0.0012  0.41  0.796  0.736  0.19  0.57  0.20  0.55
    2.00  -0.1883  -0.0218  0.0009  0.40  0.813  0.728  0.18  0.54  0.23  0.53
    3.00   0.0552  -0.0502  0.0006  0.42  0.819  0.655  0.26  0.49  0.32  0.50
    4.00  -0.2465  -0.0060  0.0006  0.42  0.812  0.660  0.22  0.49  0.27  0.51
    5.00  -0.5119   0.0321  0.0008  0.41  0.731  0.670  0.19  0.48  0.24  0.50
    pga   -0.6488   0.0250  0.0005  0.32  0.746  0.847  0.35  0.60  0.30  0.56
    pgv   -0.7475   0.0318  0.0012  0.33  0.700  0.804  0.25  0.54  0.20  0.49
    """)
