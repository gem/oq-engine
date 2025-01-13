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
Module exports :class:'ArroyoEtAl2010SInter'
"""
import numpy as np
from scipy.constants import g
from scipy.special import exp1

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _compute_mean(C, g, ctx):
    """
    Compute mean according to equation 8a, page 773.
    """
    mag = ctx.mag
    dis = ctx.rrup

    # computing r02 parameter and the average distance to the fault surface
    ro2 = 1.4447e-5 * np.exp(2.3026 * mag)
    avg = np.sqrt(dis ** 2 + ro2)

    # computing fourth term of Eq. 8a, page 773.
    trm4 = (exp1(C['c4'] * dis) - exp1(C['c4'] * avg)) / ro2

    # computing the mean
    mean = C['c1'] + C['c2'] * mag + C['c3'] * np.log(trm4)

    # convert from cm/s**2 to 'g'
    mean = np.log(np.exp(mean) * 1e-2 / g)
    return mean


def _get_stddevs(C):
    """
    Return standard deviations as defined in table 2, page 776.
    """
    stds = np.array([C['s_t'], C['s_e'], C['s_r']])
    return stds


class ArroyoEtAl2010SInter(GMPE):
    """
    Implements GMPE developed by Arroyo et al. (2010) for Mexican
    subduction interface events and published as:

    Arroyo D., García D., Ordaz M., Mora M. A., and Singh S. K. (2010)
    "Strong ground-motion relations for Mexican interplate earhquakes",
    J. Seismol., 14:769-785.

    The original formulation predict peak ground acceleration (PGA), in
    cm/s**2, and 5% damped pseudo-acceleration response spectra (PSA) in
    cm/s**2 for the geometric average of the maximum component of the two
    horizontal component of ground motion.

    The GMPE predicted values for Mexican interplate events at rock sites
    (NEHRP B site condition) in the forearc region.
    """

    #: Supported tectonic region type is subduction interface,
    #: given that the equations have been derived using Mexican interface
    #: events.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration. See Table 2 in page 776.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric average of
    #  the maximum of the two horizontal components.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total. See Table 2, page 776.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT}

    #: No site parameters required
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is the magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rrup (closest distance to fault surface)
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _compute_mean(C, g, ctx)
            sig[m], tau[m], phi[m] = _get_stddevs(C)

    #: Equation coefficients for geometric average of the maximum of the two
    #: horizontal components, as described in Table 2 on page 776.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT     c1      c2      c3      c4      g_e     bias     s_t     s_e     s_r
    0.040   3.8123  0.8636  0.5578  0.0150  0.3962  -0.0254  0.8228  0.5179  0.6394
    0.045   4.0440  0.8489  0.5645  0.0150  0.3874  -0.0285  0.8429  0.5246  0.6597
    0.050   4.1429  0.8580  0.5725  0.0150  0.3731  -0.0181  0.8512  0.5199  0.6740
    0.055   4.3092  0.8424  0.5765  0.0150  0.3746   0.0004  0.8583  0.5253  0.6788
    0.060   4.3770  0.8458  0.5798  0.0150  0.4192  -0.0120  0.8591  0.5563  0.6547
    0.065   4.5185  0.8273  0.5796  0.0150  0.3888  -0.0226  0.8452  0.5270  0.6607
    0.070   4.4591  0.8394  0.5762  0.0150  0.3872  -0.0346  0.8423  0.5241  0.6594
    0.075   4.5939  0.8313  0.5804  0.0150  0.3775  -0.0241  0.8473  0.5205  0.6685
    0.080   4.4832  0.8541  0.5792  0.0150  0.3737  -0.0241  0.8421  0.5148  0.6664
    0.085   4.5062  0.8481  0.5771  0.0150  0.3757  -0.0138  0.8344  0.5115  0.6593
    0.090   4.4648  0.8536  0.5742  0.0150  0.4031  -0.0248  0.8304  0.5273  0.6415
    0.095   4.3940  0.8580  0.5712  0.0150  0.4097   0.0040  0.8294  0.5309  0.6373
    0.100   4.3391  0.8620  0.5666  0.0150  0.3841  -0.0045  0.8254  0.5116  0.6477
    0.120   4.0505  0.8933  0.5546  0.0150  0.3589  -0.0202  0.7960  0.4768  0.6374
    0.140   3.5599  0.9379  0.5350  0.0150  0.3528  -0.0293  0.7828  0.4650  0.6298
    0.160   3.1311  0.9736  0.5175  0.0150  0.3324  -0.0246  0.7845  0.4523  0.6409
    0.180   2.7012  1.0030  0.4985  0.0150  0.3291  -0.0196  0.7717  0.4427  0.6321
    0.200   2.5485  0.9988  0.4850  0.0150  0.3439  -0.0250  0.7551  0.4428  0.6116
    0.220   2.2699  1.0125  0.4710  0.0150  0.3240  -0.0205  0.7431  0.4229  0.6109
    0.240   1.9130  1.0450  0.4591  0.0150  0.3285  -0.0246  0.7369  0.4223  0.6039
    0.260   1.7181  1.0418  0.4450  0.0150  0.3595  -0.0220  0.7264  0.4356  0.5814
    0.280   1.4039  1.0782  0.4391  0.0150  0.3381  -0.0260  0.7209  0.4191  0.5865
    0.300   1.1080  1.1038  0.4287  0.0150  0.3537  -0.0368  0.7198  0.4281  0.5787
    0.320   1.0652  1.0868  0.4208  0.0150  0.3702  -0.0345  0.7206  0.4384  0.5719
    0.340   0.8319  1.1088  0.4142  0.0150  0.3423  -0.0381  0.7264  0.4250  0.5891
    0.360   0.4965  1.1408  0.4044  0.0150  0.3591  -0.0383  0.7255  0.4348  0.5808
    0.380   0.3173  1.1388  0.3930  0.0150  0.3673  -0.0264  0.7292  0.4419  0.5800
    0.400   0.2735  1.1533  0.4067  0.0134  0.3956  -0.0317  0.7272  0.4574  0.5653
    0.450   0.0990  1.1662  0.4127  0.0117  0.3466  -0.0267  0.7216  0.4249  0.5833
    0.500  -0.0379  1.2206  0.4523  0.0084  0.3519  -0.0338  0.7189  0.4265  0.5788
    0.550  -0.3512  1.2445  0.4493  0.0076  0.3529  -0.0298  0.7095  0.4215  0.5707
    0.600  -0.6897  1.2522  0.4421  0.0067  0.3691  -0.0127  0.7084  0.4304  0.5627
    0.650  -0.6673  1.2995  0.4785  0.0051  0.3361  -0.0192  0.7065  0.4096  0.5756
    0.700  -0.7154  1.3263  0.5068  0.0034  0.3200  -0.0243  0.7070  0.3999  0.5830
    0.750  -0.7015  1.2994  0.5056  0.0029  0.3364  -0.0122  0.7092  0.4113  0.5778
    0.800  -0.8581  1.3205  0.5103  0.0023  0.3164  -0.0337  0.6974  0.3923  0.5766
    0.850  -0.9712  1.3375  0.5201  0.0018  0.3435  -0.0244  0.6906  0.4047  0.5596
    0.900  -1.0970  1.3532  0.5278  0.0012  0.3306  -0.0275  0.6923  0.3980  0.5665
    0.950  -1.2346  1.3687  0.5345  0.0007  0.3264  -0.0306  0.6863  0.3921  0.5632
    1.000  -1.2600  1.3652  0.5426  0.0001  0.3194  -0.0183  0.6798  0.3842  0.5608
    1.100  -1.7687  1.4146  0.5342  0.0001  0.3336  -0.0229  0.6701  0.3871  0.5471
    1.200  -2.1339  1.4417  0.5263  0.0001  0.3445  -0.0232  0.6697  0.3931  0.5422
    1.300  -2.4122  1.4577  0.5201  0.0001  0.3355  -0.0231  0.6801  0.3939  0.5544
    1.400  -2.5442  1.4618  0.5242  0.0001  0.3759  -0.0039  0.6763  0.4146  0.5343
    1.500  -2.8509  1.4920  0.5220  0.0001  0.3780  -0.0122  0.6765  0.4159  0.5335
    1.600  -3.0887  1.5157  0.5215  0.0001  0.3937  -0.0204  0.6674  0.4187  0.5197
    1.700  -3.4884  1.5750  0.5261  0.0001  0.4130  -0.0208  0.6480  0.4164  0.4965
    1.800  -3.7195  1.5966  0.5255  0.0001  0.3967  -0.0196  0.6327  0.3985  0.4914
    1.900  -4.0141  1.6162  0.5187  0.0001  0.4248  -0.0107  0.6231  0.4062  0.4726
    2.000  -4.1908  1.6314  0.5199  0.0001  0.3967  -0.0133  0.6078  0.3828  0.4721
    2.500  -5.1104  1.7269  0.5277  0.0001  0.4302  -0.0192  0.6001  0.3936  0.4530
    3.000  -5.5926  1.7515  0.5298  0.0001  0.4735  -0.0319  0.6029  0.4148  0.4375
    3.500  -6.1202  1.8077  0.5402  0.0001  0.4848  -0.0277  0.6137  0.4273  0.4405
    4.000  -6.5318  1.8353  0.5394  0.0001  0.5020  -0.0368  0.6201  0.4393  0.4376
    4.500  -6.9744  1.8685  0.5328  0.0001  0.5085  -0.0539  0.6419  0.4577  0.4500
    5.000  -7.1389  1.8721  0.5376  0.0001  0.5592  -0.0534  0.6701  0.5011  0.4449
    pga     2.4862  0.9392  0.5061  0.0150  0.3850  -0.0181  0.7500  0.4654  0.5882
    """)
