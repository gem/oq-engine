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
exp_res = np.array([[[-4.73116981, -6.72824192, -8.69828689],
                     [-5.14424676, -6.37286291, -7.60510263],
                     [-5.85932703, -6.80133893, -7.56254085]],

                    [[-4.73116981, -6.72824192, -8.69828689],
                     [-5.14424676, -6.37286291, -7.60510263],
                     [-5.85932703, -6.80133893, -7.56254085]],

                    [[-4.3697711 , -6.77717214, -9.0440702 ],
                     [-4.87470779, -6.44046012, -8.1754259 ],
                     [-5.94409889, -7.33906319, -8.07374331]],

                    [[-4.34746516, -6.80533449, -9.06618916],
                     [-4.43505174, -6.42940165, -8.1754259 ],
                     [-5.36080654, -7.32476703, -8.67690874]],

                    [[-3.81017818, -5.87054779, -8.41343283],
                     [-4.35919525, -5.71917277, -7.55847418],
                     [-5.44339364, -6.71746409, -7.8999625 ]],

                    [[-3.81017818, -5.87054779, -8.41343283],
                     [-4.35919525, -5.71917277, -7.55847418],
                     [-5.44339364, -6.71746409, -8.22310968]],

                    [[-1.54869462, -3.8245714 , -5.293704  ],
                     [-2.33761724, -3.72056054, -4.88431736],
                     [-3.55411876, -4.67077352, -5.15474589]],

                    [[-1.54869462, -3.8245714 , -5.293704  ],
                     [-2.33761724, -3.72056054, -4.88431736],
                     [-3.55411876, -4.67077352, -5.43751783]],

                    [[-3.43253177, -5.38231865, -7.7114568 ],
                     [-4.4754561 , -5.71171233, -6.19501105],
                     [-5.51471534, -6.71435625, -7.13731168]],

                    [[-3.43253177, -5.38231865, -7.7114568 ],
                     [-4.4754561 , -5.71171233, -6.19501105],
                     [-5.51471534, -6.71435625, -7.42008363]]])


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
                             'm9_basin_term="true"\n'
                             'usgs_basin_scaling="true"')
        p20_def = valid.gsim('[ParkerEtAl2020SInterB]\nregion="Cascadia"')
        
        # AtkinsonMacias2009 (m9 and cb14 vs m9)
        a09_adj = valid.gsim('[AtkinsonMacias2009]\ncb14_basin_term="true"\n'
                              'm9_basin_term="true"')
        a09_def = valid.gsim('[AtkinsonMacias2009]\ncb14_basin_term="true"')

        # ZhaoEtAl2006SInter (m9 and cb14 vs m9)
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
        ctx.z1pt0 = np.array([72.1, 457.77, 522.32])
        ctx.z2pt5 = np.array([0.69, 1.75, 6.32])
        ctx.rrup = np.array([50., 200., 500.])
        ctx.vs30 = np.array([800., 400., 200.])
        ctx.vs30measured = 1
        mea, _, _, _ = cmaker.get_mean_stds([ctx])
        aae(mea, exp_res)

        