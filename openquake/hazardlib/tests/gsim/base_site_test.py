# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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

import unittest
import numpy
from openquake.baselib.hdf5 import read_csv
from openquake.hazardlib.gsim.base import _get_poes
from openquake.baselib.general import gettemp, DictArray
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.site import ampcode_dt
from openquake.hazardlib.site_amplification import AmplFunction, get_poes_site
from openquake.hazardlib.tests.site_amplification_function_test import ampl_func


class GetPoesSiteTestCase(unittest.TestCase):
    # Add check that IMT and sigma are the same
    # Add check on IMTs

    def test01(self):
        fname = gettemp(ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')

        gmmA = BooreAtkinson2008()
        cmaker = simple_cmaker([gmmA], ['PGA', 'SA(1.0)'])
        ctx = cmaker.new_ctx(5)
        ctx.rrup = [10., 15., 20., 30., 40.]
        ctx.rjb = [10., 15., 20., 30., 40.]
        ctx.vs30 = 760.
        ctx.mag = 5.5
        ctx.ampcode = b'A'
        meastd = cmaker.get_mean_stds([ctx])[:2, 0]  # shape (M, N)

        imls_soil = numpy.log([0.012, 0.052, 0.12, 0.22, 0.52])
        imls_soil = numpy.log(numpy.logspace(-2, 0, num=20))
        cmaker.loglevels = ll = DictArray(
            {'PGA': imls_soil, 'SA(1.0)': imls_soil})
        cmaker.oq.af = AmplFunction.from_dframe(df)
        cmaker.truncation_level = tl = 3.

        # The output in this case will be (1, x, 2) i.e. 1 site, number
        # intensity measure levels times 2 and 2 GMMs
        tmp = _get_poes(meastd, ll.array, tl)
        res = get_poes_site(meastd, cmaker, ctx)

        if False:
            import matplotlib.pyplot as plt
            plt.plot(numpy.exp(imls_soil), res[0, 0:len(imls_soil), 0], '-o',
                     label='soil')
            plt.plot(numpy.exp(imls_soil), tmp[0, 0:len(imls_soil), 0], '-o',
                     label='rock')
            plt.legend()
            plt.xscale('log')
            plt.yscale('log')
            plt.grid(which='both')
            plt.show()
