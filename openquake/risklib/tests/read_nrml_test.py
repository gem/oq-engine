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

    def test_duplicated_id_vm(self):
        fname = gettemp('''\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
<vulnerabilityModel id="vm-hazus" assetCategory="buildings" lossCategory="structural">
<description> structural vulnerability model for global database</description>

<vulnerabilityFunction id="CR-PC_LWAL-DNO_H1" dist="LN">
<imls imt="PGA"> 0.05 0.051933 0.053941 0.056026 0.058192 0.060442 0.062778 0.065205 0.067726 0.070344 0.073064 0.075889 0.078822 0.08187 0.085035 0.088322 0.091737 0.095283 0.098967 0.102793 0.106767 0.110894 0.115181 0.119634 0.124259 0.129063 0.134053 0.139235 0.144618 0.150209 0.156016 0.162047 0.168312 0.174819 0.181577 0.188597 0.195888 0.203461 0.211327 0.219497 0.227982 0.236796 0.245951 0.255459 0.265335 0.275593 0.286247 0.297313 0.308807 0.320746 0.333146 0.346025 0.359402 0.373296 0.387728 0.402717 0.418286 0.434457 0.451253 0.468699 0.486818 0.505639 0.525186 0.54549 0.566578 0.588482 0.611233 0.634863 0.659406 0.684899 0.711377 0.738878 0.767443 0.797112 0.827928 0.859936 0.893181 0.927711 0.963576 1.00083 1.03952 1.07971 1.12145 1.1648 1.20983 1.2566 1.30519 1.35564 1.40805 1.46249 1.51903 1.57775 1.63875 1.7021 1.7679 1.83625 1.90724 1.98097 2.05756 2.1371 </imls>
<meanLRs> 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1e-06 1e-06 1e-06 2e-06 4e-06 6e-06 1e-05 1.5e-05 2.3e-05 3.5e-05 5.2e-05 7.6e-05 0.000112 0.000161 0.000229 0.000321 0.000445 0.00061 0.000826 0.001105 0.00146 0.001907 0.002463 0.003145 0.003973 0.004966 0.006143 0.007525 0.009131 0.010981 0.013094 0.015492 0.018197 0.021233 0.02463 0.028422 0.032651 0.037367 0.042629 0.048508 0.055089 0.062465 0.070742 0.080036 0.090473 0.102183 0.115298 0.129951 0.146268 0.164362 0.184333 0.206256 0.230179 0.256115 0.284042 0.31389 0.345547 0.378852 0.413597 0.449529 0.486356 0.52375 0.56136 0.598817 0.63575 0.671796 0.70661 0.739878 0.771326 0.800729 0.827913 0.852763 0.875219 0.895278 0.912986 0.928433 0.941747 </meanLRs>
<covLRs> 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 </covLRs>
</vulnerabilityFunction>

<vulnerabilityFunction dist="LN" id="CR-PC_LWAL-DUM_H1">
<imls imt="PGA">0.05 0.3 0.35 0.4 0.45 0.5 0.55 0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 1 1.05 1.1 1.15 1.2 1.25 1.3 1.35 1.4 1.45 1.5 1.55 1.6 1.65 1.7 1.75 1.8 1.85 1.9 1.95 2 2.05 2.1 2.15 2.2 2.25 2.3 2.35 2.4 2.45 2.5 2.55 2.6 2.7 2.75 2.85 2.95 3.05 3.15 3.3 3.5 3.7 4 5</imls>
<meanLRs>0.000 0.005 0.010 0.018 0.030 0.045 0.062 0.083 0.106 0.132 0.159 0.188 0.217 0.247 0.278 0.308 0.338 0.368 0.397 0.426 0.454 0.480 0.506 0.531 0.555 0.5786 0.600 0.621 0.641 0.660 0.678 0.696 0.712 0.727 0.742 0.756 0.769 0.782 0.793 0.804 0.815 0.825 0.834 0.843 0.851 0.859 0.867 0.874 0.887 0.893 0.904 0.913 0.922 0.930 0.940 0.951 0.960 0.970 0.988</meanLRs>
<covLRs>0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000</covLRs>
</vulnerabilityFunction>
	
<vulnerabilityFunction dist="LN" id="CR-PC_LWAL-DNO_H1">
<imls imt="PGA">0.05 0.200 0.3 0.35 0.4 0.45 0.5 0.55 0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 1 1.05 1.1 1.15 1.2 1.25 1.3 1.35 1.4 1.45 1.5 1.55 1.6 1.65 1.7 1.75 1.8 1.85 1.9 1.95 2 2.05 2.1 2.15 2.2 2.25 2.3 2.35 2.4 2.45 2.5 2.55 2.6 2.85 3.1 3.55 4.9</imls>
<meanLRs>0.000 0.050 0.122 0.165 0.210 0.256 0.302 0.347 0.390 0.431 0.469 0.505 0.539 0.5717 0.600 0.628 0.653 0.676 0.698 0.718 0.737 0.754 0.770 0.785 0.798 0.811 0.823 0.834 0.844 0.854 0.862 0.871 0.878 0.889 0.8927 0.8986 0.904 0.909 0.914 0.919 0.923 0.928 0.931 0.9355 0.938 0.942 0.945 0.948 0.9509 0.961 0.970 0.980 0.993</meanLRs>
<covLRs>0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000</covLRs>
</vulnerabilityFunction>

</vulnerabilityModel>
</nrml>''')
        with self.assertRaises(nrml.InvalidFile) as ctx:
            nrml.to_python(fname)
        self.assertIn('Duplicated vulnerabilityFunctionID: CR-PC_LWAL-DNO_H1',
                      str(ctx.exception))
