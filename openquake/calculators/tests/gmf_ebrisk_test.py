# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017 GEM Foundation
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

from nose.plugins.attrib import attr
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.gmf_ebrisk import case_1


class GmfEbRiskTestCase(CalculatorTestCase):
    @attr('qa', 'risk', 'gmf_ebrisk')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_risk.ini', exports='csv')
        [fname] = out['losses_by_taxon-rlzs', 'csv']
        self.assertEqualFiles('expected/losses_by_taxon.csv', fname)
