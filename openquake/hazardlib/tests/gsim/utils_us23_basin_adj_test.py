# The Hazard Library
# Copyright (C) 2012-2024 GEM Foundation
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
                     [-5.51471534, -6.71435625, -7.42008363]],

                    [[-4.4961401 , -6.90354114, -9.1704392 ],
                     [-4.63795079, -6.2103382 , -8.0068908 ],
                     [-5.66174089, -7.06528288, -8.48453249]],

                    [[-4.3697711 , -6.77717214, -9.0440702 ],
                     [-4.87470779, -6.35831133, -8.0068908 ],
                     [-5.94409889, -7.24175663, -8.07374331]],

                    [[-4.2549802 , -6.63321606, -8.87962362],
                     [-4.16121733, -5.82549419, -7.68603107],
                     [-4.94338881, -6.57681856, -8.15619706]],

                    [[-4.10630526, -6.53500941, -8.77537358],
                     [-3.95831828, -6.04455764, -7.85456617],
                     [-4.64245446, -6.83630271, -8.3485733 ]],

                    [[-4.1286112 , -6.50684706, -8.75325462],
                     [-4.39797433, -5.97346732, -7.68603107],
                     [-5.22574681, -6.75329231, -7.74540788]],

                    [[-3.78353627, -5.91619801, -8.66217995],
                     [-4.4371146 , -5.50137959, -6.52644857],
                     [-5.2961146 , -6.26168121, -7.11054718]],

                    [[-3.81234061, -5.91619801, -8.65816589],
                     [-4.35646244, -5.49346344, -6.52644857],
                     [-5.2039407 , -6.25143678, -7.11054718]],

                    [[-0.96141029, -0.71209078, -0.85092839],
                     [-1.77096597, -1.15736712, -0.95839284],
                     [-3.05936274, -2.37822057, -1.7344926 ]],

                    [[-0.96141029, -0.71209078, -0.85092839],
                     [-1.77096597, -1.15736712, -0.95839284],
                     [-3.05936274, -2.37822057, -1.7344926 ]],

                    [[-3.41920968, -5.63581494, -8.24612451],
                     [-3.95142704, -5.00650921, -5.24233594],
                     [-4.99773441, -5.99001151, -6.03753215]],

                    [[-3.41723244, -5.63582436, -8.05359796],
                     [-4.03181004, -5.00650921, -5.24233672],
                     [-5.09420641, -5.99001151, -6.03753227]],

                    [[-3.78546864, -5.65888348, -8.53990403],
                     [-4.33459936, -5.13940084, -6.21685285],
                     [-5.35569267, -5.84909742, -6.40207779]],

                    [[-3.78546864, -5.65888348, -8.53990403],
                     [-4.32603582, -5.13532842, -6.21685285],
                     [-5.32974644, -5.83675861, -6.40207779]],
                     
                     [[-3.78353627, -5.91619801, -8.66217995],
                      [-4.4371146 , -5.50137959, -6.52644857],
                      [-5.2961146 , -6.26168121, -7.11054718]]])


class USBasinAdjustmentTestCase(unittest.TestCase):       

    def test_all(self):
        """
        Test the execution and correctness of values of the m9 basin adjustment
        argument and (for the ZhaoEtAl2006 and AtkinsonMacias2009 GMMs) the
        Campbell and Bozorgnia 2014 basin term argument.

        Also check the USGS basin scaling adjustments for all GMMs added to
        as required for the US 2023 model.
        """
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

        # KuehnEtAl2020SInterSeattle vs KuehnEtAl2020SInterCascadia vs Seattle SInter Adj
        k20_def_sea_int = valid.gsim('[KuehnEtAl2020SInter]\nregion="Sea"')
        k20_def_cas_int = valid.gsim('[KuehnEtAl2020SInter]\nregion="CAS"')
        k20_adj_sea_int = valid.gsim('[KuehnEtAl2020SInter]\nregion="Sea"\n'
                                     'm9_basin_term="true"\n'
                                     'usgs_basin_scaling="true"')

        # KuehnEtAl2020SSlabSeattle vs KuehnEtAl2020SSlabCascadia vs Seattle SSlab Adj
        k20_def_sea_sslab = valid.gsim('[KuehnEtAl2020SSlab]\nregion="Sea"')
        k20_def_cas_sslab = valid.gsim('[KuehnEtAl2020SSlab]\nregion="CAS"')
        k20_adj_sea_sslab = valid.gsim('[KuehnEtAl2020SSlab]\nregion="Sea"\n'
                                       'm9_basin_term="true"\n'
                                       'usgs_basin_scaling="true"')

        # NGAWest2 GMMs with/without USGS basin scaling
        ask14_adj = valid.gsim('[AbrahamsonEtAl2014]\nusgs_basin_scaling="true"')
        ask14_def = valid.gsim('[AbrahamsonEtAl2014]')
        bssa14_adj = valid.gsim('[BooreEtAl2014]\nusgs_basin_scaling="true"')
        bssa14_def = valid.gsim('[BooreEtAl2014]')
        cb14_adj = valid.gsim('[CampbellBozorgnia2014]\nusgs_basin_scaling="true"')    
        cb14_def = valid.gsim('[CampbellBozorgnia2014]')   
        cy14_adj = valid.gsim('[ChiouYoungs2014]\nusgs_basin_scaling="true"')
        cy14_def = valid.gsim('[ChiouYoungs2014]')

        # US NSHMP 2014 GMM with passing of an additional arguments for base GMM
        nshmp14_ask14_adj = valid.gsim('[NSHMP2014]\ngmpe_name="AbrahamsonEtAl2014"\n'
                                       'sgn=0\nusgs_basin_scaling="true"')
        
        # Make the ctx
        imts = ['PGA', 'SA(1.0)', 'SA(2.0)']
        cmaker = simple_cmaker([ag_adj, ag_def,
                                k20_adj, k20_def,
                                p20_adj, p20_def,
                                a09_adj, a09_def,
                                z06_adj, z06_def,
                                k20_def_sea_int,
                                k20_def_cas_int,
                                k20_adj_sea_int,
                                k20_def_sea_sslab,
                                k20_def_cas_sslab,
                                k20_adj_sea_sslab,
                                ask14_adj, ask14_def,
                                bssa14_adj, bssa14_def,
                                cb14_adj, cb14_def,
                                cy14_adj, cy14_def,
                                nshmp14_ask14_adj],
                                imts)                       
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
        