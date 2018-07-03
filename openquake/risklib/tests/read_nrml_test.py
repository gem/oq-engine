# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2018 GEM Foundation
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
from openquake.baselib.general import gettemp
from openquake.hazardlib import nrml


class VulnerabilityFunctionTestCase(unittest.TestCase):
    def test_invalid_vf_pmf(self):
        fname = gettemp('''\
<?xml version="1.0" encoding="UTF-8"?> 
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"> 
	<vulnerabilityModel id="Vulnerabilidad" assetCategory="MI_AIS" lossCategory="structural"> 
		<description>Vulnerabilidad Microcomponentes</description> 
		<vulnerabilityFunction id="MI_PTR" dist="PM">
			<imls imt="PGA">0.00 0.10 0.20 0.31 0.41 0.51 0.61 0.71 0.82 0.92 1.02 1.12 1.22 1.33 1.43 1.53 </imls>
			<probabilities lr="0">1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.000000000017">0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.000024">0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.005">0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.067">0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.25">0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.50">0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.72">0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.86">0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.93">0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.97">0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0</probabilities>
			<probabilities lr="0.99">0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0</probabilities>
			<probabilities lr="0.995">0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0</probabilities>
			<probabilities lr="0.998">0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0</probabilities>
			<probabilities lr="0.999">0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0</probabilities>
			<probabilities lr="1">0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1</probabilities>
		</vulnerabilityFunction>
		<vulnerabilityFunction id="MI_TON" dist="PM">
			<imls imt="PGA">0.00 0.10 0.20 0.31 0.41 0.51 0.61 0.71 0.82 0.92 1.02 1.12 1.22 1.33 </imls>
			<probabilities lr="0">1 0 0 0 0 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.0000317">0 1 0 0 0 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.025">0 0 1 0 0 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.0221">0 0 0 1 0 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.531">0 0 0 0 1 0 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.768">0 0 0 0 0 1 0 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.898">0 0 0 0 0 0 1 0 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.958">0 0 0 0 0 0 0 1 0 0 0 0 0 0</probabilities>
			<probabilities lr="0.983">0 0 0 0 0 0 0 0 1 0 0 0 0 0</probabilities>
			<probabilities lr="0.993">0 0 0 0 0 0 0 0 0 1 0 0 0 0</probabilities>
			<probabilities lr="0.997">0 0 0 0 0 0 0 0 0 0 1 0 0 0</probabilities>
			<probabilities lr="0.998">0 0 0 0 0 0 0 0 0 0 0 1 0 0</probabilities>
			<probabilities lr="0.999">0 0 0 0 0 0 0 0 0 0 0 0 1 0</probabilities>
			<probabilities lr="1">0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1</probabilities>
		</vulnerabilityFunction>
	</vulnerabilityModel> 
</nrml>''')
        with self.assertRaises(ValueError) as ctx:
            nrml.to_python(fname)
        self.assertIn('Wrong number of probabilities (expected 14, got 17)',
                      str(ctx.exception))
