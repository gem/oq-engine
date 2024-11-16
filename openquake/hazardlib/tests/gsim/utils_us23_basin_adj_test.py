# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import unittest

from openquake.hazardlib.tests.gsim.mgmpe.dummy import new_ctx
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib import valid


aae = np.testing.assert_almost_equal

# Mean ground-shaking values array: exp_res[gmm][imt]
exp_res = np.array([[[-4.73116981, -6.72824192, -8.69828689], # Same as unmod
                     [-4.31482484, -6.18652969, -7.60510263], # because no m9
                     [-4.9958659 , -6.60735866, -7.56254085]],

                    [[-4.73116981, -6.72824192, -8.69828689],
                     [-4.31482484, -6.18652969, -7.60510263],
                     [-4.9958659 , -6.60735866, -7.56254085]],

                    [[-4.30139546, -6.7907388 , -9.06618916], # Diff at SA(2.0)
                     [-4.04986555, -6.30736791, -8.1754259 ], # for basin sites
                     [-5.25095171, -7.1626911 , -8.07374331]],# as M9 term

                    [[-4.30139546, -6.7907388 , -9.06618916],
                     [-4.04986555, -6.30736791, -8.1754259 ],
                     [-4.84923156, -7.1626911 , -8.67690874]],

                    [[-3.81017818, -5.87054779, -8.41343283], # Diff at SA(2.0)
                     [-4.35919525, -5.71917277, -7.55847418], # for basin sites
                     [-5.12024646, -6.28641178, -7.8999625 ]],# as M9 term

                    [[-3.81017818, -5.87054779, -8.41343283],
                     [-4.35919525, -5.71917277, -7.55847418],
                     [-5.44339364, -6.71746409, -8.22310968]],

                    [[-1.35815033, -3.78220564, -5.293704  ], # Diff at SA(2.0)
                     [-1.86104115, -3.63337845, -4.88431736], # for basin sites
                     [-2.76449958, -4.58047065, -5.15474589]],# as M9 term

                    [[-1.35815033, -3.78220564, -5.293704  ],
                     [-1.86104115, -3.63337845, -4.88431736],
                     [-3.04727152, -4.58047065, -5.43751783]],

                    [[-3.24198747, -5.33995289, -7.7114568 ], # Diff at SA(2.0)
                     [-3.99888001, -5.62453024, -6.19501105], # for basin sites
                     [-4.72509616, -6.62405339, -7.13731168]],# as M9 term

                    [[-3.24198747, -5.33995289, -7.7114568 ],
                     [-3.99888001, -5.62453024, -6.19501105],
                     [-5.0078681 , -6.62405339, -7.42008363]]])


class USBasinAdjustmentTestCase(unittest.TestCase):       

    def test_all(self):
        """
        Test the execution and correctness of values of the m9 basin adjustment
        argument and (for the ZhaoEtAl2006 and AtkinsonMacias2009 GMMs) the
        Campbell and Bozorgnia 2014 basin term argument.
        """
        # Just test the interface subclasses

        # AbrahamsonGulerce2020SInter (all adj vs no adj)
        ag_adj = valid.gsim('[AbrahamsonGulerce2020SInter]\nregion="CAS"\n'
                             'usgs_basin_scaling="true"')
        ag_def = valid.gsim('[AbrahamsonGulerce2020SInter]\nregion="CAS"')

        # KuehnEtAl2020SInter (all adj vs no adj)
        k20_adj = valid.gsim('[KuehnEtAl2020SInter]\nregion="CAS"\n'
                             'm9_basin_term="true"\nusgs_basin_scaling="true"')
        k20_def = valid.gsim('[KuehnEtAl2020SInter]\nregion="CAS"')

        # ParkerEtAl2020SInterB (all adj vs no adj)
        p20_adj = valid.gsim('[ParkerEtAl2020SInterB]\nregion="Cascadia"\n'
                             'basin="out"\nm9_basin_term="true"\n'
                             'usgs_basin_scaling="true"')
        p20_def = valid.gsim('[ParkerEtAl2020SInterB]\nregion="Cascadia"\n'
                             'basin="out"')
        
        # AtkinsonMacias2009 (m9 and cb14 vs cb14)
        a09_adj = valid.gsim('[AtkinsonMacias2009]\ncb14_basin_term="true"\n'
                              'm9_basin_term="true"')
        a09_def = valid.gsim('[AtkinsonMacias2009]\ncb14_basin_term="true"')

        # ZhaoEtAl2006SInter (m9 and cb14 vs cb14)
        z06_adj = valid.gsim('[ZhaoEtAl2006SInter]\ncb14_basin_term="true"\n'
                              'm9_basin_term="true"')
        z06_def = valid.gsim('[ZhaoEtAl2006SInter]\ncb14_basin_term="true"')

        # Make the ctx
        imts = ['PGA', 'SA(1.0)', 'SA(2.0)']
        cmaker = simple_cmaker([ag_adj, ag_def,
                                k20_adj, k20_def,
                                p20_adj, p20_def,
                                a09_adj, a09_def,
                                z06_adj, z06_def], imts)                       
        ctx = new_ctx(cmaker, 3)
        ctx.dip = 60.
        ctx.rake = 90.
        ctx.z1pt0 = np.array([522.32, 516.98, 522.32])
        ctx.z2pt5 = np.array([6.32, 3.53, 6.32])
        ctx.rrup = np.array([50., 200., 500.])
        ctx.vs30 = np.array([800., 400., 200.])
        ctx.vs30measured = 1
        mea, _, _, _ = cmaker.get_mean_stds([ctx])