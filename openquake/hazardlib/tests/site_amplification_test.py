# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import numpy
from openquake.baselib.hdf5 import read_csv
from openquake.baselib.general import gettemp
from openquake.hazardlib.site_amplification import Amplifier

trivial_ampl_func = '''#,,,,,,,"vs30_ref=760, imls=[.001, .01, .05, .1, .2, .5, 1., 1.21]"
amplification,level,PGA,SA(0.3),SA(0.6),SA(1.0),SA(1.5)
A,0,1,1,1,1,1
A,1,1,1,1,1,1
A,2,1,1,1,1,1
A,3,1,1,1,1,1
A,4,1,1,1,1,1
A,5,1,1,1,1,1
A,6,1,1,1,1,1
A,7,1,1,1,1,1
'''

simple_ampl_func = '''#,,,,,,,"vs30_ref=760, imls=[.001, .01, .05, .1, .2, .5, 1., 1.21]"
amplification,level,PGA,SA(0.3),SA(0.6),SA(1.0),SA(1.5),sigma_PGA,sigma_SA(0.3),sigma_SA(0.6),sigma_SA(1.0),sigma_SA(1.5)
A,0,1.01,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,1,1.05,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,2,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,3,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,4,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,5,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,6,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,7,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
'''


class AmplifierTestCase(unittest.TestCase):
    imls = [.001, .002, .005, .01, .02, .05, .1, .2, .5, 1., 1.2]
    soil_levels = numpy.array([.002, .005, .01, .02, .05, .1, .2])
    imtls = {'PGA': imls, 'SA(0.1)': imls, 'SA(0.2)': imls, 'SA(0.5)': imls}
    hcurve = [[.999, .995, .99, .98, .95, .9, .8, .7, .1, .05, .01],  # PGA
              [.999, .995, .99, .98, .95, .9, .8, .7, .1, .05, .01],  # SA(0.1)
              [.999, .995, .99, .98, .95, .9, .8, .7, .1, .05, .01],  # SA(0.2)
              [.999, .995, .99, .98, .95, .9, .8, .7, .1, .05, .01]]  # SA(0.5)

    def test_trivial(self):
        # using the heaviside function, i.e. amplify_one has contributions
        # only for soil_intensity < rock_intensity
        fname = gettemp(trivial_ampl_func)
        aw = read_csv(fname, {'amplification': 'S2', 'level': numpy.uint8,
                              None: numpy.float64})
        a = Amplifier(self.imtls, aw, self.soil_levels)
        poes = a.amplify_one(b'A', 'SA(0.1)', self.hcurve[1])
        numpy.testing.assert_allclose(
            poes, [0.9825, 0.975, 0.955, 0.915, 0.84, 0.74, 0.39],
            atol=1E-6)
        poes = a.amplify_one(b'A', 'SA(0.2)', self.hcurve[2])
        numpy.testing.assert_allclose(
            poes, [0.9825, 0.975, 0.955, 0.915, 0.84, 0.74, 0.39],
            atol=1E-6)
        poes = a.amplify_one(b'A', 'SA(0.5)', self.hcurve[3])
        numpy.testing.assert_allclose(
            poes, [0.9825, 0.975, 0.955, 0.915, 0.84, 0.74, 0.39], atol=1E-6)

    def test_simple(self):
        fname = gettemp(simple_ampl_func)
        aw = read_csv(fname, {'amplification': 'S2', 'level': numpy.uint8,
                              None: numpy.float64})
        a = Amplifier(self.imtls, aw, self.soil_levels)
        poes = a.amplify_one(b'A', 'SA(0.1)', self.hcurve[1])
        numpy.testing.assert_allclose(
            poes, [0.982699, 0.975398, 0.960744, 0.924573, 0.84, 0.74, 0.39],
            atol=1E-6)
        poes = a.amplify_one(b'A', 'SA(0.2)', self.hcurve[2])
        numpy.testing.assert_allclose(
            poes, [0.982699, 0.975398, 0.960744, 0.924573, 0.84, 0.74, 0.39],
            atol=1E-6)
        poes = a.amplify_one(b'A', 'SA(0.5)', self.hcurve[3])
        numpy.testing.assert_allclose(
            poes, [0.9825, 0.975, 0.955, 0.915, 0.84, 0.74, 0.39], atol=1E-6)
