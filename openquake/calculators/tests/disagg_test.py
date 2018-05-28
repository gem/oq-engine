# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
import os
import sys
import unittest
import numpy
from nose.plugins.attrib import attr
from openquake.baselib.general import gettemp
from openquake.hazardlib.probability_map import combine
from openquake.calculators import getters
from openquake.calculators.views import view
from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.qa_tests_data.disagg import (
    case_1, case_2, case_3, case_4, case_5, case_master)


class DisaggregationTestCase(CalculatorTestCase):

    def assert_curves_ok(self, expected, test_dir, fmt='xml', delta=None):
        if sys.platform == 'win32':  # disable concurrency on windows
            out = self.run_calc(test_dir, 'job.ini', exports=fmt,
                                concurrent_tasks='0')
        else:
            out = self.run_calc(test_dir, 'job.ini', exports=fmt)
        got = out['disagg', fmt]
        self.assertEqual(len(expected), len(got))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected_output/%s' % fname, actual)
        return out

    @attr('qa', 'hazard', 'disagg')
    def test_case_1(self):
        out = self.assert_curves_ok(
            ['poe-0.02-rlz-0-PGA-10.1-40.1_Mag.csv',
             'poe-0.02-rlz-0-PGA-10.1-40.1_Mag_Dist.csv',
             'poe-0.02-rlz-0-PGA-10.1-40.1_Lon_Lat.csv',
             'poe-0.02-rlz-0-SA(0.025)-10.1-40.1_Mag.csv',
             'poe-0.02-rlz-0-SA(0.025)-10.1-40.1_Mag_Dist.csv',
             'poe-0.02-rlz-0-SA(0.025)-10.1-40.1_Lon_Lat.csv',
             'poe-0.1-rlz-0-PGA-10.1-40.1_Mag.csv',
             'poe-0.1-rlz-0-PGA-10.1-40.1_Mag_Dist.csv',
             'poe-0.1-rlz-0-PGA-10.1-40.1_Lon_Lat.csv',
             'poe-0.1-rlz-0-SA(0.025)-10.1-40.1_Mag.csv',
             'poe-0.1-rlz-0-SA(0.025)-10.1-40.1_Mag_Dist.csv',
             'poe-0.1-rlz-0-SA(0.025)-10.1-40.1_Lon_Lat.csv'],
            case_1.__file__,
            fmt='csv')

        # check disagg_by_src, poe=0.02, 0.1, imt=PGA, SA(0.025)
        self.assertEqual(len(out['disagg_by_src', 'csv']), 4)
        for fname in out['disagg_by_src', 'csv']:
            self.assertEqualFiles('expected_output/%s' % strip_calc_id(fname),
                                  fname)

        # disaggregation by source group
        rlzs_assoc = self.calc.datastore['csm_info'].get_rlzs_assoc()
        pgetter = getters.PmapGetter(self.calc.datastore, rlzs_assoc)
        pgetter.init()
        pmaps = []
        for grp in sorted(pgetter.dstore['poes']):
            pmaps.append(pgetter.get_mean(grp))
        # make sure that the combination of the contributions is okay
        pmap = pgetter.get_mean()  # total mean map
        cmap = combine(pmaps)  # combination of the mean maps per source group
        for sid in pmap:
            numpy.testing.assert_almost_equal(pmap[sid].array, cmap[sid].array)

    @attr('qa', 'hazard', 'disagg')
    def test_case_2(self):
        # this is a case with disagg_outputs = Mag and 4 realizations
        if sys.platform == 'darwin':
            raise unittest.SkipTest('MacOSX')
        self.assert_curves_ok([
            'rlz-0-PGA--3.0--3.0.xml', 'rlz-0-PGA-0.0-0.0.xml',
            'rlz-1-PGA--3.0--3.0.xml', 'rlz-1-PGA-0.0-0.0.xml',
            'rlz-2-PGA-0.0-0.0.xml', 'rlz-3-PGA-0.0-0.0.xml'],
            case_2.__file__)

        # check that the CSV exporter does not break
        fnames = export(('disagg', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 6)  # number of CSV files

        # check stats
        fnames = export(('disagg-stats', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 2)  # 2 sid x 1 key x 1 poe x 1 imt
        for fname in fnames:
            self.assertEqualFiles(
                'expected_output/%s' % strip_calc_id(fname), fname)

    @attr('qa', 'hazard', 'disagg')
    def test_case_3(self):
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(case_3.__file__, 'job.ini')
        self.assertEqual(str(ctx.exception), '''\
You are trying to disaggregate for poe=0.1.
However the source model #0, 'source_model_test_complex.xml',
produces at most probabilities of 0.0362321 for rlz=#0, IMT=PGA.
The disaggregation PoE is too big or your model is wrong,
producing too small PoEs.''')

    @attr('qa', 'hazard', 'disagg')
    def test_case_4(self):
        # this is case with number of lon/lat bins different for site 0/site 1
        # this exercise sampling
        self.run_calc(case_4.__file__, 'job.ini')

        # check stats
        fnames = export(('disagg-stats', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 64)  # 2 sid x 8 keys x 2 poe x 2 imt

    @attr('qa', 'hazard', 'disagg')
    def test_case_5(self):
        # this exercise gridded nonparametric sources
        self.run_calc(case_5.__file__, 'job.ini')

    @attr('qa', 'hazard', 'disagg')
    def test_case_master(self):
        # this tests exercise the case of a complex logic tree; it also
        # prints the warning on poe_agg very different from the expected poe
        self.run_calc(case_master.__file__, 'job.ini')
        fname = gettemp(view('mean_disagg', self.calc.datastore))
        self.assertEqualFiles('expected/mean_disagg.rst', fname)
        os.remove(fname)

        # check stats
        fnames = export(('disagg-stats', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 192)  # 2 sid x 8 keys x 2 poe x 2 imt
        # = 64 x 3 for mean, quantile-0.15, quantile-0.85

    @attr('qa', 'hazard', 'disagg')
    def test_disagg_by_src(self):
        # this is a case with iml_disagg and disagg_by_src
        self.run_calc(case_master.__file__, 'job1.ini')
        arr = self.calc.datastore[
            'disagg_by_src/iml-0.02-PGA--122.6-38.3'].value
        numpy.testing.assert_almost_equal(arr, [0.6757448, 0.1780308])
