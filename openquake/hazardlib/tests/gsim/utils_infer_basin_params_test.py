# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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
from openquake.hazardlib.gsim.mgmpe.m9_basin_term import M9BasinTerm
from openquake.hazardlib.gsim.sera_amplification_models import SandikkayaDinsever2018


aae = np.testing.assert_almost_equal

# Mean ground-shaking values array: exp_res[gmm][imt]
exp_sa = np.array([[[-3.81234061, -5.91619801, -8.65816589, -6.68795633],
        [-4.35646244, -5.53095409, -6.52644857, -6.26336196],
        [-5.2039407 , -6.29995409, -7.11054718, -7.00236196]],

       [[-4.73116981, -6.72824192, -8.69828689, -7.52243485],
        [-5.14424676, -6.37286291, -7.60510263, -7.15753586],
        [-5.85932703, -6.80133893, -7.56254085, -7.4240169 ]],

       [[-3.78950463, -5.59057139, -7.84976335, -6.28479896],
        [-4.06627818, -4.97594963, -5.52336528, -5.49927065],
        [-5.00990839, -5.89300293, -6.36237302, -6.50413898]],

       [[-2.76909019, -5.60070667, -5.59552499, -6.18189104],
        [-3.64046668, -6.10966368, -5.44587985, -7.16118529],
        [-4.85599684, -7.19902561, -6.34891709, -8.34581674]],

       [[-0.96141029, -0.71209078, -0.85092839, -0.81884943],
        [-1.77096597, -1.15736712, -0.95839284, -1.48533062],
        [-3.05936274, -2.37822057, -1.7344926 , -2.77019521]],

       [[-4.06944187, -6.39770905, -9.00651784, -7.09112434],
        [-4.52528822, -5.65168192, -6.58700668, -6.21016867],
        [-5.29744138, -6.31514799, -6.90952917, -6.88402605]],

       [[-3.6905391 , -5.83764103, -9.20667681, -6.65951899],
        [-4.33595384, -5.30612459, -6.32926838, -5.94389375],
        [-5.45600259, -6.15868275, -6.61583476, -6.75021051]],

       [[-3.27001138, -4.54167591, -5.01567555, -4.9308921 ],
        [-4.00949556, -4.80854698, -4.68730651, -5.36667996],
        [-5.08053986, -5.78254698, -5.5826234 , -6.41138753]],

       [[-3.41723244, -5.63582436, -8.05359796, -6.31952892],
        [-4.03181004, -5.00650921, -5.24233672, -5.69337001],
        [-5.09420641, -5.99001151, -6.03753227, -6.66291755]],

       [[-4.06160339, -6.40333244, -8.47274909, -7.10676403],
        [-4.0228626 , -5.53579155, -6.30735592, -6.17847322],
        [-4.94900961, -6.30188298, -7.00946152, -6.9523579 ]],

       [[-3.65428892, -5.68926046, -8.83329273, -6.47342019],
        [-4.21528235, -5.02630931, -5.73102101, -5.61037302],
        [-5.33633643, -5.91474404, -6.12312832, -6.46458963]],

       [[-3.78546864, -5.65888348, -8.53990403, -6.44072752],
        [-4.32603582, -5.15461526, -6.21685285, -5.93494921],
        [-5.32974644, -5.89519484, -6.40207779, -6.59572663]],

       [[-3.11978062, -5.3375517 , -8.96487856, -6.29263003],
        [-4.69073292, -5.50921245, -6.61474871, -6.28295883],
        [-5.94221815, -6.39647348, -6.86988255, -7.03816676]],

       [[-4.05749038, -6.3678003 , -8.42519905, -7.0218276 ],
        [-4.60622943, -6.0389822 , -7.316974  , -6.72183947],
        [-5.6331596 , -7.10732888, -8.24269583, -7.61714908]],

       [[-3.98950253, -6.3339154 , -8.51056987, -7.08460762],
        [-4.51588101, -6.2090932 , -7.10027974, -7.0479075 ],
        [-5.39299157, -7.25749588, -7.84893996, -7.92254961]],

       [[-1.54869462, -3.8245714 , -5.293704  , -4.20984636],
        [-2.33761724, -3.72056054, -4.88431736, -4.08556711],
        [-3.55411876, -4.67077352, -5.43751783, -4.97813249]],

       [[-4.21481083, -6.60527079, -8.68189238, -7.34000684],
        [-4.73129616, -6.1820532 , -7.6549745 , -6.91828167],
        [-5.84923187, -7.22578488, -8.53090301, -7.7912997 ]],

       [[-3.81017818, -5.87054779, -8.41343283, -6.66335462],
        [-4.35919525, -5.71917277, -7.55847418, -6.56525867],
        [-5.44339364, -6.71746409, -8.22310968, -7.39925424]],

       [[-3.65901266, -5.71140684, -8.9399117 , -6.54306577],
        [-4.18814331, -5.07179053, -6.12667583, -5.74721983],
        [-5.29466456, -5.98913734, -6.71564569, -6.65077671]],

       [[-3.8706221 , -5.80102281, -8.35673819, -6.60651294],
        [-4.73311134, -6.09431121, -6.87776311, -6.98341559],
        [-5.9180387 , -7.30936694, -7.75339976, -8.20052791]]])

exp_rsd = np.array([[[2.69074546, 3.39114385, 4.38319331, 3.40448974],
        [1.84690449, 2.81494047, 3.88050003, 2.90662908]],

       [[2.74289484, 3.76782175, 5.0764608 , 3.83249798],
        [1.88513738, 3.12466403, 4.20119095, 3.25298778]]])

exp_sdi = np.array([[[-5.52120458, -6.68802662, -7.82248146, -7.55460669],
        [-1.48257926, -2.86888468, -4.372265  , -3.73713563],
        [ 0.13016982, -0.77145137, -0.9125226 , -1.50113413]]])

exp_eas = np.array([[[ -7.44038109,  -7.81254508,  -7.7051751 ,  -8.21975198],
        [ -5.26629654,  -6.03927373,  -6.92350931,  -6.80483416],
        [ -6.42157878,  -9.14085666, -13.63368481,  -9.99642298]]])


gmms_sa = [valid.gsim('[AbrahamsonEtAl2014]'),
           valid.gsim('[AbrahamsonGulerce2020SInter]\nregion="CAS"'),
           valid.gsim('[AbrahamsonSilva2008]'),
           valid.gsim('[AristeidouEtAl2024]'),
           valid.gsim('[BooreEtAl2014]'),
           valid.gsim('[BozorgniaCampbell2016]'),
           valid.gsim('[Bradley2013]'),
           valid.gsim('[CampbellBozorgnia2008]'),
           valid.gsim('[CampbellBozorgnia2014]'),
           valid.gsim('[ChaoEtAl2020SInter]'),
           valid.gsim('[ChiouYoungs2008]'),
           valid.gsim('[ChiouYoungs2014]'),
           valid.gsim('[HassaniAtkinson2020Asc]'),
           valid.gsim('[KuehnEtAl2020SInter]\nregion="NZL"'), # z1pt0
           valid.gsim('[KuehnEtAl2020SInter]\nregion="JPN"'), # z2pt5
           valid.gsim('[CB14BasinTerm]\ngmpe_name="AtkinsonMacias2009"'),
           valid.gsim('[NZNSHM2022_KuehnEtAl2020SInter]'),
           valid.gsim('[ParkerEtAl2020SInter]\nregion="Cascadia"'),
           valid.gsim('[PhungEtAl2020Asc]'),
           valid.gsim('[SiEtAl2020SInter]'),
           ]

gmms_rsd = [valid.gsim('[AfshariStewart2016]'),
            valid.gsim('[BahrampouriEtAldm2021Asc]')]

gmms_sdi = [valid.gsim('[AristeidouEtAl2023]')]

gmms_eas = [valid.gsim('[BaylessAbrahamson2018]')]

gmms_error = [M9BasinTerm(gmpe_name='KuehnEtAl2020SInter'),
              SandikkayaDinsever2018(gmpe_name='BooreEtAl2014')]


def make_ctx(imts, gmms):
    cmaker = simple_cmaker(gmms, imts)                     
    ctx = new_ctx(cmaker, 4)
    ctx.dip = 60.
    ctx.rake = 90.
    ctx.z1pt0 = np.array([72.1, -999., 522.32, -999])
    ctx.z2pt5 = np.array([0.69, -999., 6.32, -999])
    ctx.rrup = np.array([50., 200., 500., 250.])
    ctx.vs30 = np.array([800., 400., 200., 600.])
    ctx.vs30measured = 1
    return ctx, cmaker


class InferBasinParamTestCase(unittest.TestCase):       

    def test_all(self):
        """
        Test the execution and correctness of values for GMMs which
        use basin terms, with a site model with some -999 z1pt0 and
        z2pt5 values, to force use of values computed from the vs30
        to basin param relationships within each GMM.
        """
        # SA GMMs
        imts_sa = ['PGA', 'SA(1.0)', 'SA(2.0)']
        ctx_sa, cmaker_sa = make_ctx(imts_sa, gmms_sa)
        mea_sa, _, _, _ = cmaker_sa.get_mean_stds([ctx_sa])
        np.testing.assert_allclose(mea_sa, exp_sa, rtol=1e-6)

        # RSD GMMs
        imts_rsd = ["RSD595", "RSD575"]
        ctx_rsd, cmaker_rsd = make_ctx(imts_rsd, gmms_rsd)
        mea_rsd, _, _, _ = cmaker_rsd.get_mean_stds([ctx_rsd])
        np.testing.assert_allclose(mea_rsd, exp_rsd, rtol=1e-6)

        # SDi GMMs
        imts_sdi = ["SDi(0.04,1.5)", "SDi(0.50,1.5)", "SDi(5.00,1.5)"]
        ctx_sdi, cmaker_sdi = make_ctx(imts_sdi, gmms_sdi)
        mea_sdi, _, _, _ = cmaker_sdi.get_mean_stds([ctx_sdi])
        np.testing.assert_allclose(mea_sdi, exp_sdi, rtol=1e-6)

        # EAS GMMs
        imts_eas = ["EAS(0.1)", "EAS(1)", "EAS(9)"] # Hz
        ctx_eas, cmaker_eas = make_ctx(imts_eas, gmms_eas)
        mea_eas, _, _, _ = cmaker_eas.get_mean_stds([ctx_eas])
        np.testing.assert_allclose(mea_eas, exp_eas, rtol=1e-6)

        # GMMs which should raise a value error if -999 z1pt0 or z2pt5 in site model
        ctx_error, cmaker_error = make_ctx(imts_sa, gmms_error)
        with self.assertRaises(ValueError):
            cmaker_error.get_mean_stds([ctx_error])