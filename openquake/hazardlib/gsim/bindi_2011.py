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
Module exports :class:`BindiEtAl2011`.
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim import utils
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def _compute_distance(ctx, C):
    """
    Compute the second term of the equation 1 described on paragraph 3:

    ``c1 + c2 * (M-Mref) * log(sqrt(Rjb ** 2 + h ** 2)/Rref) -
         c3*(sqrt(Rjb ** 2 + h ** 2)-Rref)``
    """
    mref = 5.0
    rref = 1.0
    rval = np.sqrt(ctx.rjb ** 2 + C['h'] ** 2)
    return (C['c1'] + C['c2'] * (ctx.mag - mref)) *\
        np.log10(rval / rref) - C['c3'] * (rval - rref)


def _compute_magnitude(ctx, C):
    """
    Compute the third term of the equation 1:

    e1 + b1 * (M-Mh) + b2 * (M-Mh)**2 for M<=Mh
    e1 + b3 * (M-Mh) otherwise
    """
    m_h = 6.75
    b_3 = 0.0
    return np.where(
        ctx.mag <= m_h,
        C["e1"] + C['b1'] * (ctx.mag - m_h) + C['b2'] * (ctx.mag - m_h) ** 2,
        C["e1"] + b_3 * (ctx.mag - m_h))


def _get_delta(coeffs, imt, mag):
    # Get the coefficients needed to compute the delta used for scaling
    tmp = coeffs['a']*mag**2. + coeffs['b']*mag + coeffs['c']
    return tmp


def _get_mechanism(ctx, C):
    """
    Compute the fifth term of the equation 1 described on paragraph :
    Get fault type dummy variables, see Table 1
    """
    SS, NS, RS = utils.get_fault_type_dummy_variables(ctx)
    return C['f1'] * NS + C['f2'] * RS + C['f3'] * SS


def _get_site_amplification(ctx, C):
    """
    Compute the fourth term of the equation 1 described on paragraph :
    The functional form Fs in Eq. (1) represents the site amplification and
    it is given by FS = sj Cj , for j = 1,...,5, where sj are the
    coefficients to be determined through the regression analysis,
    while Cj are dummy variables used to denote the five different EC8
    site classes
    """
    ssa, ssb, ssc, ssd, sse = _get_site_type_dummy_variables(ctx)

    return (C['sA'] * ssa + C['sB'] * ssb + C['sC'] * ssc +
            C['sD'] * ssd + C['sE'] * sse)


def _get_site_type_dummy_variables(ctx):
    """
    Get site type dummy variables, five different EC8 site classes
    he recording ctx are classified into 5 classes,
    based on the shear wave velocity intervals in the uppermost 30 m, Vs30,
    according to the EC8 (CEN 2003):
    class A: Vs30 > 800 m/s
    class B: Vs30 = 360 − 800 m/s
    class C: Vs30 = 180 - 360 m/s
    class D: Vs30 < 180 m/s
    class E: 5 to 20 m of C- or D-type alluvium underlain by
    stiffer material with Vs30 > 800 m/s.
    """
    ssa = np.zeros(len(ctx.vs30))
    ssb = np.zeros(len(ctx.vs30))
    ssc = np.zeros(len(ctx.vs30))
    ssd = np.zeros(len(ctx.vs30))
    sse = np.zeros(len(ctx.vs30))

    # Class E Vs30 = 0 m/s. We fixed this value to define class E
    idx = (np.fabs(ctx.vs30) < 1E-10)
    sse[idx] = 1.0
    # Class D;  Vs30 < 180 m/s.
    idx = (ctx.vs30 >= 1E-10) & (ctx.vs30 < 180.0)
    ssd[idx] = 1.0
    # SClass C; 180 m/s <= Vs30 <= 360 m/s.
    idx = (ctx.vs30 >= 180.0) & (ctx.vs30 < 360.0)
    ssc[idx] = 1.0
    # Class B; 360 m/s <= Vs30 <= 800 m/s.
    idx = (ctx.vs30 >= 360.0) & (ctx.vs30 < 800)
    ssb[idx] = 1.0
    # Class A; Vs30 > 800 m/s.
    idx = (ctx.vs30 >= 800.0)
    ssa[idx] = 1.0
    return ssa, ssb, ssc, ssd, sse


class BindiEtAl2011(GMPE):
    """
    Implements GMPE developed by D.Bindi, F.Pacor, L.Luzi, R.Puglia,
    M.Massa, G. Ameri, R. Paolucci and published as "Ground motion
    prediction equations derived from the Italian strong motion data",
    Bull Earthquake Eng, DOI 10.1007/s10518-011-9313-z.
    SA are given up to 2 s.
    The regressions are developed considering the geometrical mean of the
    as-recorded horizontal components
    """
    #: Supported tectonic region type is 'active shallow crust' because the
    #: equations have been derived from data from Italian database ITACA, as
    #: explained in the 'Introduction'.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is RRup (eq. 1).
    REQUIRES_DISTANCES = {'rjb'}

    sgn = 0

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = (_compute_magnitude(ctx, C) +
                     _compute_distance(ctx, C) +
                     _get_site_amplification(ctx, C) +
                     _get_mechanism(ctx, C))

            # Convert units to g,
            # but only for PGA and SA (not PGV):
            if imt.string.startswith(('PGA', 'SA')):
                mean[m] = np.log((10.0 ** (imean - 2.0)) / g)
            else:
                # PGV
                mean[m] = np.log(10.0 ** imean)

            # Return stddevs in terms of natural log scaling
            sig[m] = np.log(10.0 ** C['SigmaTot'])
            tau[m] = np.log(10.0 ** C['SigmaB'])
            phi[m] = np.log(10.0 ** C['SigmaW'])

            if self.sgn:
                mean[m] += self.sgn * _get_delta(
                    self.COEFFS_DELTA[imt], imt, ctx.mag)

    #: Coefficients from SA from Table 1
    #: Coefficients from PGA e PGV from Table 5

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT        e1         c1    c2            h           c3         b1          b2     sA       sB        sC       sD       sE         f1        f2         f3    f4    SigmaB   SigmaW  SigmaTot
    pgv     2.305    -1.5170    0.3260     7.879    0.000000     0.2360    -0.00686    0.0    0.2050    0.269    0.321    0.428    -0.0308    0.0754    -0.0446    0.0    0.194    0.270     0.332
    pga     3.672    -1.9400    0.4130    10.322    0.000134    -0.2620    -0.07070    0.0    0.1620    0.240    0.105    0.570    -0.0503    0.1050    -0.0544    0.0    0.172    0.290     0.337
    0.04    3.725    -1.9760    0.4220     9.445    0.000270    -0.3150    -0.07870    0.0    0.1610    0.240    0.060    0.614    -0.0442    0.1060    -0.0615    0.0    0.154    0.307     0.343
    0.07    3.906    -2.0500    0.4460     9.810    0.000758    -0.3750    -0.07730    0.0    0.1540    0.235    0.057    0.536    -0.0454    0.1030    -0.0576    0.0    0.152    0.324     0.358
    0.10    3.796    -1.7940    0.4150     9.500    0.002550    -0.2900    -0.06510    0.0    0.1780    0.247    0.037    0.599    -0.0656    0.1110    -0.0451    0.0    0.154    0.328     0.363
    0.15    3.799    -1.5210    0.3200     9.163    0.003720    -0.0987    -0.05740    0.0    0.1740    0.240    0.148    0.740    -0.0755    0.1230    -0.0477    0.0    0.179    0.318     0.365
    0.20    3.750    -1.3790    0.2800     8.502    0.003840     0.0094    -0.05170    0.0    0.1560    0.234    0.115    0.556    -0.0733    0.1060    -0.0328    0.0    0.209    0.320     0.382
    0.25    3.699    -1.3400    0.2540     7.912    0.003260     0.0860    -0.04570    0.0    0.1820    0.245    0.154    0.414    -0.0568    0.1100    -0.0534    0.0    0.212    0.308     0.374
    0.30    3.753    -1.4140    0.2550     8.215    0.002190     0.1240    -0.04350    0.0    0.2010    0.244    0.213    0.301    -0.0564    0.0877    -0.0313    0.0    0.218    0.290     0.363
    0.35    3.600    -1.3200    0.2530     7.507    0.002320     0.1540    -0.04370    0.0    0.2200    0.257    0.243    0.235    -0.0523    0.0905    -0.0382    0.0    0.221    0.283     0.359
    0.40    3.549    -1.2620    0.2330     6.760    0.002190     0.2250    -0.04060    0.0    0.2290    0.255    0.226    0.202    -0.0565    0.0927    -0.0363    0.0    0.210    0.279     0.349
    0.45    3.550    -1.2610    0.2230     6.775    0.001760     0.2920    -0.03060    0.0    0.2260    0.271    0.237    0.181    -0.0597    0.0886    -0.0289    0.0    0.204    0.284     0.350
    0.50    3.526    -1.1810    0.1840     5.992    0.001860     0.3840    -0.02500    0.0    0.2180    0.280    0.263    0.168    -0.0599    0.0850    -0.0252    0.0    0.203    0.283     0.349
    0.60    3.561    -1.2300    0.1780     6.382    0.001140     0.4360    -0.02270    0.0    0.2190    0.296    0.355    0.142    -0.0559    0.0790    -0.0231    0.0    0.203    0.283     0.348
    0.70    3.485    -1.1720    0.1540     5.574    0.000942     0.5290    -0.01850    0.0    0.2100    0.303    0.496    0.134    -0.0461    0.0896    -0.0435    0.0    0.212    0.283     0.354
    0.80    3.325    -1.1150    0.1630     4.998    0.000909     0.5450    -0.02150    0.0    0.2100    0.304    0.621    0.150    -0.0457    0.0795    -0.0338    0.0    0.213    0.284     0.355
    0.90    3.318    -1.1370    0.1540     5.231    0.000483     0.5630    -0.02630    0.0    0.2120    0.315    0.680    0.154    -0.0351    0.0715    -0.0364    0.0    0.214    0.286     0.357
    1.00    3.264    -1.1140    0.1400     5.002    0.000254     0.5990    -0.02700    0.0    0.2210    0.332    0.707    0.152    -0.0298    0.0660    -0.0362    0.0    0.222    0.283     0.360
    1.25    2.896    -0.9860    0.1730     4.340    0.000783     0.5790    -0.03360    0.0    0.2440    0.365    0.717    0.183    -0.0207    0.0614    -0.0407    0.0    0.227    0.290     0.368
    1.50    2.675    -0.9600    0.1920     4.117    0.000802     0.5750    -0.03530    0.0    0.2510    0.375    0.667    0.203    -0.0140    0.0505    -0.0365    0.0    0.218    0.303     0.373
    1.75    2.584    -1.0060    0.2050     4.505    0.000427     0.5740    -0.03710    0.0    0.2520    0.357    0.593    0.220    0.00154    0.0370    -0.0385    0.0    0.219    0.305     0.376
    2.00    2.537    -1.0090    0.1930     4.373    0.000164     0.5970    -0.03670    0.0    0.2450    0.352    0.540    0.226    0.00512    0.0350    -0.0401    0.0    0.211    0.308     0.373
    2.50    2.425    -1.0290    0.1790     4.484   -0.000348     0.6550    -0.02620    0.0    0.2440    0.336    0.460    0.229    0.00561    0.0275    -0.0331    0.0    0.212    0.309     0.375
    2.75    2.331    -1.0430    0.1830     4.581   -0.000617     0.6780    -0.01820    0.0    0.2320    0.335    0.416    0.232    0.01350    0.0263    -0.0398    0.0    0.203    0.310     0.370
    4.00    2.058    -1.0840    0.2000     4.876   -0.000843     0.6740    -0.00621    0.0    0.1950    0.300    0.350    0.230    0.02950    0.0255    -0.0550    0.0    0.197    0.300     0.359
    """)

    COEFFS_DELTA = CoeffsTable(sa_damping=5, table="""
    imt   a      b     c
    pga   0.101 -1.136 3.555
    pgv   0.066 -0.741 2.400
    0.05  0.105 -1.190 3.691
    0.1   0.112 -1.284 4.001
    0.15  0.094 -1.033 3.177
    0.2   0.085 -0.907 2.831
    0.3   0.086 -0.927 2.869
    0.4   0.088 -0.974 3.076
    0.5   0.083 -0.916 2.933
    0.75  0.073 -0.808 2.628
    1.00  0.066 -0.736 2.420
    2.00  0.041 -0.512 1.888
    3.00  0.050 -0.616 2.193
    4.00  0.076 -0.906 3.046
    """)


class BindiEtAl2011Ita19Low(BindiEtAl2011):
    """
    Implements the lower term of the ITA19 backbone model.
    """
    sgn = -1


class BindiEtAl2011Ita19Upp(BindiEtAl2011):
    """
    Implements the upper term of the ITA19 backbone model.
    """
    sgn = +1
