# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020 GEM Foundation
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
Module exports :class:`Sung2020`
"""

from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.bayless_abrahamson_2018 import \
        BaylessAbrahamson2018


class SungAbrahamson2020(BaylessAbrahamson2018):
    """
    Implements the Sung and Abrahamson (2020) model for France based on the
    Bayliss and Abrahamson (2018) GMM.
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        # We need the coordinates of the closest point on the rupture in the
        #rupture contexts
        mean, stddevs = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                   stddev_types)

        
        return mean, stddevs

        
        

    

    COEFF = CoeffsTable(sa_damping=5, table="""\
IMT         c1                  c2  c3                  cn                  cM                  c4  c5  c6  chm c7  c8  c9  c10 c11a    c11b    c11c    c11d    c1a s1  s2  s3  s4  s5  s6  f3  f4  f5
f_0.5011872 -3.353  1.27    -0.058  2.704052334 5.951917751 -1.86   7.581799176 0.450402473 3.832962079 -0.0111 -0.472  0.0412  -0.2    0.351393859 0.237750473 0.227042072 0.181767514 -0.022485383    0.55612584  0.427683808 0.411026188 0.412387132 0.423728309 0.423728309 0.996449343 -0.002362854    -0.0199749
f_1.0   -3.42462978 1.27    2.810855246 3.623987533 5.635799252 -1.86   7.5814  0.4517  3.8144  -0.004129651    -1.118379396    0.003872989 -0.2    0.187885794 0.124336361 0.151590949 0.15321913  -0.023136392    0.505564315 0.384704301 0.417188704 0.422589328 0.428586348 0.421909944 0.752487118 -0.023957696    -0.017869964

            
""")
