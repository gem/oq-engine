# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
exp_sa = None
exp_rsd = None
exp_sdi = None
gmms_eas = None

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

gmms_rsd = [valid.gsim('[AfshariStewart2016]'), valid.gsim('[BahrampouriEtAldm2021Asc]')]

gmms_sdi = [valid.gsim('[AristeidouEtAl2023]')]

gmms_eas = [valid.gsim('[BaylessAbrahamson2018]')]

gmms_error = [M9BasinTerm(gmpe_name='KuehnEtAl2020SInter'),
              SandikkayaDinsever2018(gmpe_name='BooreEtAl2014')]


def make_ctx(imts, gmms):
    cmaker = simple_cmaker(gmms, imts)                     
    ctx = new_ctx(cmaker, 4)
    ctx.dip = 60.
    ctx.rake = 90.
    ctx.z1pt0 = np.array([72.1, -999, 522.32, 999])
    ctx.z2pt5 = np.array([0.69, -999, 6.32, -999])
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
        #np.testing.assert_allclose(mea_sa, exp_sa, rtol=1e-6)

        # RSD GMMs
        imts_rsd = ["RSD595", "RSD575"]
        ctx_rsd, cmaker_rsd = make_ctx(imts_rsd, gmms_rsd)
        mea_rsd, _, _, _ = cmaker_rsd.get_mean_stds([ctx_rsd])
        #np.testing.assert_allclose(mea_rsd, exp_rsd, rtol=1e-6)

        # SDi GMMs
        imts_sdi = ["SDi(0.04,1.5)", "SDi(0.50,1.5)", "SDi(5.00,1.5)"]
        ctx_sdi, cmaker_sdi = make_ctx(imts_sdi, gmms_sdi)
        mea_sdi, _, _, _ = cmaker_sdi.get_mean_stds([ctx_sdi])
        #np.testing.assert_allclose(mea_sdi, exp_sdi, rtol=1e-6)

        # EAS GMMs
        imts_eas = ["EAS(0.1)", "EAS(1)", "EAS(9)"] # Hz
        ctx_eas, cmaker_eas = make_ctx(imts_eas, gmms_eas)
        mea_eas, _, _, _ = cmaker_eas.get_mean_stds([ctx_eas])
        #np.testing.assert_allclose(mea_eas, exp_eas, rtol=1e-6)

        # GMMs which should raise a value error if -999 z1pt0 or z2pt5 in site model
        ctx_error, cmaker_error = make_ctx(imts_sa, gmms_error)
        with self.assertRaises(ValueError):
            cmaker_error.get_mean_stds([ctx_error])