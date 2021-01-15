# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
Module exports :class:`BindiEtAl2011scaled`.
"""

from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.bindi_2011 import BindiEtAl2011


class BindiEtAl2011scaled(BindiEtAl2011):
    """
    Implements scaled GMPE developed by D.Bindi, F.Pacor, L.Luzi, R.Puglia,
    M.Massa, G. Ameri, R. Paolucci and published as "Ground motion
    prediction equations derived from the Italian strong motion data",
    Bull Earthquake Eng, DOI 10.1007/s10518-011-9313-z.
    SA are given up to 2 s.
    The regressions are developed considering the geometrical mean of the
    as-recorded horizontal components
    """
    #: Coefficients from SA from Table 1
    #: Coefficients from PGA e PGV from Table 5

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT        e1         c1    c2            h           c3         b1          b2     sA       sB        sC       sD       sE         f1        f2         f3    f4    SigmaB   SigmaW  SigmaTot
    pgv     2.346    -1.5170    0.3260     7.879    0.000000     0.2360    -0.00686    0.0    0.2050    0.269    0.321    0.428    -0.0308    0.0754    -0.0446    0.0    0.194    0.270     0.332
    pga     3.714    -1.9400    0.4130    10.322    0.000134    -0.2620    -0.07070    0.0    0.1620    0.240    0.105    0.570    -0.0503    0.1050    -0.0544    0.0    0.172    0.290     0.337
    0.04    3.766    -1.9760    0.4220     9.445    0.000270    -0.3150    -0.07870    0.0    0.1610    0.240    0.060    0.614    -0.0442    0.1060    -0.0615    0.0    0.154    0.307     0.343
    0.07    3.947    -2.0500    0.4460     9.810    0.000758    -0.3750    -0.07730    0.0    0.1540    0.235    0.057    0.536    -0.0454    0.1030    -0.0576    0.0    0.152    0.324     0.358
    0.10    3.841    -1.7940    0.4150     9.500    0.002550    -0.2900    -0.06510    0.0    0.1780    0.247    0.037    0.599    -0.0656    0.1110    -0.0451    0.0    0.154    0.328     0.363
    0.15    3.850    -1.5210    0.3200     9.163    0.003720    -0.0987    -0.05740    0.0    0.1740    0.240    0.148    0.740    -0.0755    0.1230    -0.0477    0.0    0.179    0.318     0.365
    0.20    3.805    -1.3790    0.2800     8.502    0.003840     0.0094    -0.05170    0.0    0.1560    0.234    0.115    0.556    -0.0733    0.1060    -0.0328    0.0    0.209    0.320     0.382
    0.30    3.813    -1.4140    0.2550     8.215    0.002190     0.1240    -0.04350    0.0    0.2010    0.244    0.213    0.301    -0.0564    0.0877    -0.0313    0.0    0.218    0.290     0.363
    0.40    3.605    -1.2620    0.2330     6.760    0.002190     0.2250    -0.04060    0.0    0.2290    0.255    0.226    0.202    -0.0565    0.0927    -0.0363    0.0    0.210    0.279     0.349
    0.50    3.582    -1.1810    0.1840     5.992    0.001860     0.3840    -0.02500    0.0    0.2180    0.280    0.263    0.168    -0.0599    0.0850    -0.0252    0.0    0.203    0.283     0.349
    0.70    3.544    -1.1720    0.1540     5.574    0.000942     0.5290    -0.01850    0.0    0.2100    0.303    0.496    0.134    -0.0461    0.0896    -0.0435    0.0    0.212    0.283     0.354
    0.80    3.384    -1.1150    0.1630     4.998    0.000909     0.5450    -0.02150    0.0    0.2100    0.304    0.621    0.150    -0.0457    0.0795    -0.0338    0.0    0.213    0.284     0.355
    1.00    3.319    -1.1140    0.1400     5.002    0.000254     0.5990    -0.02700    0.0    0.2210    0.332    0.707    0.152    -0.0298    0.0660    -0.0362    0.0    0.222    0.283     0.360
    2.00    2.592    -1.0090    0.1930     4.373    0.000164     0.5970    -0.03670    0.0    0.2450    0.352    0.540    0.226    0.00512    0.0350    -0.0401    0.0    0.211    0.308     0.373
    2.75    2.385    -1.0430    0.1830     4.581   -0.000617     0.6780    -0.01820    0.0    0.2320    0.335    0.416    0.232    0.01350    0.0263    -0.0398    0.0    0.203    0.310     0.370
    4.00    2.117    -1.0840    0.2000     4.876   -0.000843     0.6740    -0.00621    0.0    0.1950    0.300    0.350    0.230    0.02950    0.0255    -0.0550    0.0    0.197    0.300     0.359
    """)
