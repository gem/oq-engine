# The Hazard Library
# Copyright (C) 2016-2020 GEM Foundation
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

import unittest
import numpy as np

from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.const import TRT
from openquake.baselib.hdf5 import read_csv
from openquake.hazardlib.site import ampcode_dt
from openquake.baselib.general import gettemp, DictArray
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.probability_map import ProbabilityCurve
from openquake.hazardlib.site_amplification import AmplFunction, Amplifier
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.source.non_parametric import \
        NonParametricSeismicSource

ampl_func_convolution_const = '''\
#,,,,,,,"vs30_ref=760"
ampcode,level,PGA,SA(1.0),sigma_PGA,sigma_SA(1.0)
A,     0.001,1.10,1.0,    0.20,      0.2
A,     0.010,1.10,1.0,    0.20,      0.2
A,     0.050,1.10,1.0,    0.20,      0.2
A,     0.100,1.10,1.0,    0.20,      0.2
A,     0.500,1.10,1.0,    0.20,      0.2
A,     1.000,1.10,1.0,    0.20,      0.2
'''

ampl_func_convolution = '''\
#,,,,,,,"vs30_ref=760"
ampcode,level,PGA,SA(1.0),sigma_PGA,sigma_SA(1.0)
A,     0.001,1.00,1.0,    0.20,      0.2
A,     0.010,1.10,1.0,    0.20,      0.2
A,     0.050,1.20,1.0,    0.20,      0.2
A,     0.100,1.30,1.0,    0.20,      0.2
A,     0.500,1.40,1.0,    0.20,      0.2
A,     1.000,1.50,1.0,    0.20,      0.2
'''

ampl_func_kernel = '''\
#,,,,,,,"vs30_ref=760"
ampcode,from_mag,from_rrup,level,PGA,SA(1.0),sigma_PGA,sigma_SA(1.0)
A,      4.0,      0.0,     0.001,1.00,1.0,    0.20,      0.2
A,      4.0,      0.0,     0.010,1.10,1.0,    0.20,      0.2
A,      4.0,      0.0,     0.050,1.20,1.0,    0.20,      0.2
A,      4.0,      0.0,     0.100,1.30,1.0,    0.20,      0.2
A,      4.0,      0.0,     0.500,1.40,1.0,    0.20,      0.2
A,      4.0,      0.0,     1.000,1.50,1.0,    0.20,      0.2
A,      5.5,     20.0,     0.004,1.03,1.0,    0.20,      0.2
A,      5.5,     20.0,     0.014,1.13,1.0,    0.20,      0.2
A,      5.5,     20.0,     0.054,1.23,1.0,    0.30,      0.2
A,      5.5,     20.0,     0.104,1.33,1.0,    0.20,      0.2
A,      5.5,     20.0,     0.504,1.43,1.0,    0.20,      0.2
A,      5.5,     20.0,     1.004,1.53,1.0,    0.20,      0.2
'''

ampl_func_kernel_const = '''\
#,,,,,,,"vs30_ref=760"
ampcode,from_mag,from_rrup,level,PGA,SA(1.0),sigma_PGA,sigma_SA(1.0)
A,      4.0,      0.0,     0.001,1.10,1.0,    0.20,      0.2
A,      4.0,      0.0,     0.010,1.10,1.0,    0.20,      0.2
A,      4.0,      0.0,     0.050,1.10,1.0,    0.20,      0.2
A,      4.0,      0.0,     0.100,1.10,1.0,    0.20,      0.2
A,      4.0,      0.0,     0.500,1.10,1.0,    0.20,      0.2
A,      4.0,      0.0,     1.000,1.10,1.0,    0.20,      0.2
'''


class HazardCurvesKernelTestCase(unittest.TestCase):
    """
    Test the consistency of results obtained using the convolution and
    kernel methods.
    """

    def setUp(self):

        # Create the non-parametric source
        rupture = Dummy.get_rupture(mag=7.0)
        pmf = PMF([(0.2, 0), (0.8, 1)])
        data = [(rupture, pmf)]
        trt = TRT.ACTIVE_SHALLOW_CRUST
        src = NonParametricSeismicSource('1', 'test', trt, data)

        # Create the sites
        #sites = Dummy.get_site_collection(2, vs30=[760, 760], ampcode=[b'A', b'A'])
        sites = Dummy.get_site_collection(1, vs30=760, ampcode=b'A')
        sites.array.flags.writeable = True
        sites.array['lon'][0] = 0.1
        sites.array.flags.writeable = False

        self.sites = sites
        self.srcs = [src]

    def test_consistency(self):

        # Create the amplification function object
        fname = gettemp(ampl_func_kernel_const)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: np.float64},
                      index='ampcode')
        af = AmplFunction.from_dframe(df)

        # Intensity measure types and GMM
        imls_test = np.logspace(-1.2, -0.2, num=20)
        imls_rock = np.linspace(0.005, 2.0, num=40)
        #imls_rock = np.logspace(-2, 0, num=30)
        imtls = {'PGA': imls_test}
        imtls_rock = {'PGA': imls_rock}
        imtls_conv = DictArray({'PGA': imls_rock})
        gsims = {TRT.ACTIVE_SHALLOW_CRUST: BooreAtkinson2008()}

        # Compute hazard curves using the kernel method - Output is a
        # probability map
        hc_ker = calc_hazard_curves(self.srcs, self.sites, imtls, gsims, af=af)

        # Compute hazard curves on rock
        hc_rock = calc_hazard_curves(self.srcs, self.sites, imtls_rock, gsims)

        # Create the list of probability curves
        pcurves = []
        for i, hc in enumerate(hc_rock):
            pcurves.append(ProbabilityCurve(np.expand_dims(hc[0], 1)))

        # Create the amplifier for the convolution method
        fname = gettemp(ampl_func_convolution_const)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: np.float64},
                      index='ampcode')
        ampl = Amplifier(imtls_conv, df, imls_test)

        # Compute hazard using the convolution approach
        hc_con = ampl.amplify(b'A', pcurves)

        # NOTE The percentual difference is around 7.0%. For the time being
        # we accept this but it would be worth investigating this difference
        # further
        tmpc = np.squeeze(hc_con[0].array)
        tmpk = np.squeeze(hc_ker[0][0])

        if True:
            import matplotlib.pyplot as plt
            _ = plt.figure()
            plt.plot(imls_rock, hc_rock[0][0], '--', label='rock1')
            plt.plot(imls_test, hc_con[0].array, label='con1')
            plt.plot(imls_test, hc_ker[0][0], label='ker1')
            plt.xlabel('IMLs')
            plt.ylabel('Probability of exceedance')
            plt.legend()
            plt.grid(which='both')
            dff = max(abs(tmpc-tmpk))
            txt = 'Max absolute difference: {:7.5e}'.format(dff)
            plt.text(0.005, 1.5, txt)
            plt.show()

        # Check the match between the results provided by the two methods
        np.testing.assert_allclose(tmpc, tmpk, atol=7.0e-3)
