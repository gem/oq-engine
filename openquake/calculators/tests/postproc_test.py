# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2023, GEM Foundation
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

#from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.postproc import case_mrd


class PostProcTestCase(CalculatorTestCase):
    def test_mrd(self):
        self.run_calc(case_mrd.__file__, 'job.ini', postproc_func='dummy')
        hc_id = str(self.calc.datastore.calc_id)

        self.run_calc(case_mrd.__file__, 'job.ini', hazard_calculation_id=hc_id)
        mrd = self.calc.datastore['mrd'][:]
        # NB: this changes a lot depending on the machine!
        assert abs(mrd.mean() - 8.166417e-05) < 1e-5
