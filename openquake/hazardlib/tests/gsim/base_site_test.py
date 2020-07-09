# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2020 GEM Foundation
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

import numpy
import unittest

from openquake.baselib.hdf5 import read_csv
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.base import (
    get_mean_std, _get_poes_site, _get_poes)
from openquake.baselib.general import gettemp, DictArray
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014

from openquake.hazardlib.site import ampcode_dt
from openquake.hazardlib.site_amplification import AmplFunction
from openquake.hazardlib.tests.site_amplification_function_test import ampl_func


class GetPoesSiteTestCase(unittest.TestCase):
    # Add check that IMT and sigma are the same
    # Add check on IMTs

    def setUp(self):

        fname = gettemp(ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        self.df = AmplFunction(df)

        # Set GMMs
        gmmA = BooreAtkinson2008()
        gmmB = BooreEtAl2014()

        # Set parameters
        dsts = [10., 15., 20., 30., 40.]
        dsts = [10.]
        imts = [PGA(), SA(1.0)]
        sites = Dummy.get_site_collection(len(dsts), vs30=760.0)
        self.mag = 5.5
        rup = Dummy.get_rupture(mag=self.mag)
        dists = DistancesContext()
        dists.rjb = numpy.array(dsts)
        dists.rrup = numpy.array(dsts)
        self.rrup = dists.rrup

        # Compute GM on rock
        # Shape: 2 x 4 (distances) x 2 (IMTs) x 1 (GMMs)
        self.meastd = get_mean_std(sites, rup, dists, imts, [gmmA])
        # Shape: 2 x 4 (distances) x 2 (IMTs) x 2 (GMMs)
        self.meastd = get_mean_std(sites, rup, dists, imts, [gmmA, gmmB])

    def test01(self):

        fname = gettemp(ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        af = AmplFunction.from_dframe(df)

        truncation_level = 3
        sitecode = b'A'

        imls_soil = numpy.log([0.012, 0.052, 0.12, 0.22, 0.52])
        imls_soil = numpy.log(numpy.logspace(-2, 0, num=20))
        imtls_soil = DictArray({'PGA': imls_soil, 'SA(1.0)': imls_soil})

        # The output in this case will be (1, x, 2) i.e. 1 site, number
        # intensity measure levels times 2 and 2 GMMs
        tmp = _get_poes(self.meastd, imtls_soil, truncation_level)

        # This function is rather slow at the moment
        res = _get_poes_site(self.meastd, imtls_soil, truncation_level,
                             af, self.mag, sitecode, self.rrup[0],
                             squeeze=False)

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
