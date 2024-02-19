# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
import re
import numpy
from openquake.baselib import hdf5
from openquake.baselib.general import gettemp
from openquake.hazardlib.contexts import read_ctx_by_grp
from openquake.calculators.views import view, text_table
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.qa_tests_data.disagg import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8, case_9,
    case_10, case_11, case_12, case_13, case_14, case_master)

aae = numpy.testing.assert_almost_equal

RLZCOL = re.compile(r'rlz\d+')


def compute_mean(fname, *keys):
    keys = [k.lower() for k in keys]
    aw = hdf5.read_csv(fname, {'imt': str, 'poe': str, None: float})
    dframe = aw.to_dframe()
    out = []
    rlzcols = [col for col in dframe.columns if RLZCOL.match(col)]
    for key, df in dframe.groupby(keys):
        rlzs = [df[col].to_numpy() for col in rlzcols]
        [avg] = numpy.average(rlzs, weights=aw.weights, axis=0)
        out.append((key, avg))
    return out


class DisaggregationTestCase(CalculatorTestCase):

    def assert_curves_ok(self, expected, test_dir, fmt='csv', delta=None):
        self.run_calc(test_dir, 'job.ini', calculation_mode='classical')
        hc_id = self.calc.datastore.calc_id
        self.run_calc(test_dir, 'job.ini', exports=fmt,
                      hazard_calculation_id=str(hc_id))
        got = export(('disagg-rlzs', fmt), self.calc.datastore)
        self.assertEqual(len(expected), len(got))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected_output/%s' % fname, actual)

    def test_case_1(self):
        # case with split_source=false and collapse_level=2
        self.assert_curves_ok(
            ['Lon_Lat-0.csv', 'Mag-0.csv', 'Mag_Dist-0.csv'], case_1.__file__)

    def test_case_2(self):
        # this is a case with disagg_outputs = Mag and 4 realizations
        # site #0 is partially discarded
        self.assert_curves_ok(['Mag-0.csv', 'Mag-1.csv'], case_2.__file__)

        # check we can read the exported files and compute the mean
        compute_mean(os.path.join(os.path.dirname(case_2.__file__),
                                  'expected_output/Mag-0.csv'), 'Mag')

        # test extract disagg_layer for Mag
        aw = extract(self.calc.datastore, 'disagg_layer?kind=Mag&'
                     'imt=SA(0.1)&poe_id=0')
        self.assertEqual(aw.dtype.names,
                         ('site_id', 'lon', 'lat',
                          'lon_bins', 'lat_bins', 'Mag-SA(0.1)-None',
                          'iml-SA(0.1)-None'))

        # check the custom_site_id
        aw = extract(self.calc.datastore, 'sitecol?field=custom_site_id')
        self.assertEqual(list(aw), [b'A', b'B'])

        # check the site_model backarc and vs30measured fields
        sitecol = self.calc.datastore['sitecol']
        numpy.testing.assert_equal(sitecol.vs30measured, [0, 1])
        numpy.testing.assert_equal(sitecol.backarc, [0, 1])

    def test_case_3(self):
        # a case with poes_disagg too large
        with self.assertRaises(SystemExit) as ctx:
            self.run_calc(case_3.__file__, 'job.ini')
        self.assertEqual(str(ctx.exception),
                         'Cannot do any disaggregation: zero hazard')

    def test_case_4(self):
        # a case with number of lon/lat bins different for site 0/site 1
        # this exercises sampling and empty CSV files not being saved
        self.run_calc(case_4.__file__, 'job.ini')
        fnames = export(('disagg-stats', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 11)
        for fname in fnames:
            if 'Mag_Dist' in fname and 'Eps' not in fname:
                self.assertEqualFiles(
                    'expected_output/%s' % strip_calc_id(fname), fname)

    def test_case_5(self):
        # test gridded nonparametric sources
        self.run_calc(case_5.__file__, 'job.ini')
        fnames = export(('disagg-rlzs', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

        # there is a collapsed nonparametric source with len(probs_occur)==3

    def test_case_6(self):
        # test with international date line and disagg_by_src
        self.run_calc(case_6.__file__, 'job.ini')

        # test CSV export
        fnames = export(('disagg-rlzs', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

        # test the CSVs are readable
        for fname in fnames:
            hdf5.read_csv(fname, {'imt': str, None: float})

        # test extract disagg_layer for Lon_Lat
        aw = extract(self.calc.datastore, 'disagg_layer?kind=Lon_Lat&'
                     'imt=PGA&poe_id=0')
        self.assertEqual(
            aw.dtype.names,
            ('site_id', 'lon', 'lat', 'lon_bins', 'lat_bins',
             'Lon_Lat-PGA-0.002105', 'iml-PGA-0.002105'))

        aae(aw.mag, [6.5, 6.75, 7., 7.25])
        aae(aw.dist, [0., 25., 50., 75., 100., 125., 150., 175., 200.,
                      225., 250., 275., 300.])
        aae(aw.eps, [-3., 3.])  # 6 bins -> 1 bin
        self.assertEqual(aw.trt, [b'Active Shallow Crust'])

    def test_case_7(self):
        # test with 7+2 ruptures of two source models, 1 GSIM, 1 site
        self.run_calc(case_7.__file__, 'job.ini')
        ctx = read_ctx_by_grp(self.calc.datastore)
        self.assertEqual(len(ctx[0]), 7)  # rlz-0, the closest to the mean
        self.assertEqual(len(ctx[1]), 2)  # rlz-1, the one to discard

        haz = self.calc.datastore['hmap3'][0, 0]  # shape NMP
        self.assertEqual(haz[0], 0)  # shortest return period => 0 hazard
        aae(haz[1], 0.13311564, decimal=6)

        # test normal disaggregation
        [fname] = export(('disagg-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/TRT-0.csv', fname)

        # test conditional disaggregation
        [fname] = export(('disagg-rlzs-traditional', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/TRT-traditional-0.csv', fname)

    def test_case_8(self):
        # test epsilon star
        self.run_calc(case_8.__file__, 'job.ini')

        # test mre results
        [fname] = export(('disagg-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/Mag_Dist_Eps-0.csv', fname)

        # test calculation with uneven user defined magnitude bin edges
        self.run_calc(case_8.__file__, 'job_a.ini')

        # Test mr results. Comparing against the results of the first
        # calculation in this test. The first value for magnitude 5.8 remains
        # the same. The contributions for magnitudes 6.5 and 6.7 are combined
        # into a single value corresponding to 1 - (1-p1) * (1-p2) and the last
        # value is also the same provided to magnitude 7 in the first
        # calculation
        [fname] = export(('disagg-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/Mag_Dist-0.csv', fname)

    def test_case_9(self):
        # test mutex disaggregation. Results checked against hand-computed
        # values by Marco Pagani - 2022.06.28
        self.run_calc(case_9.__file__, 'job.ini', concurrent_tasks='2')
        [f1, f2] = export(('disagg-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/Mag-0.csv', f1)
        self.assertEqualFiles('expected/Mag_Dist_Eps-0.csv', f2)

        # extract API
        aw = extract(self.calc.datastore, 'disagg?kind=Mag&site_id=0&'
                     'imt=SA(0.1)&poe_id=0&spec=rlzs')
        self.assertEqual(len(aw.mag), 4)
        self.assertEqual(aw.shape, (4, 1, 1))

        aw = extract(self.calc.datastore, 'disagg?kind=Mag_Dist_Eps&site_id=0&'
                     'imt=SA(0.1)&poe_id=0&spec=rlzs')
        self.assertEqual(len(aw.dist), 10)
        self.assertEqual(len(aw.eps), 6)
        self.assertEqual(aw.shape, (4, 10, 6, 1, 1))

    def test_case_10(self):
        # test single magnitude
        self.run_calc(case_10.__file__, 'job.ini')
        [fname] = export(('disagg-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/Mag-0.csv', fname)

    def test_case_11(self):
        # test mutex disagg by src when sources grouped by prefix
        # MDE results use same values as test_case_9
        self.run_calc(case_11.__file__, 'job.ini')
        [fname] = export(('disagg-rlzs', 'csv'), self.calc.datastore)
        #if platform.machine() == 'arm64':
        #    raise unittest.SkipTest('Temporarily skipped')
        self.assertEqualFiles('expected/Mag_Dist_Eps-0.csv', fname)

    def test_case_12(self):
        # check source IDs with :, . and ;
        self.run_calc(case_12.__file__, 'job.ini')

    def test_case_13(self):
        # check split_by_mag, essential with GMPETable
        self.run_calc(case_13.__file__, 'job.ini')

    def test_case_14(self):
        # check split_by_mag with NGAEastUSGS, see bug
        # https://github.com/gem/oq-engine/issues/8780
        self.run_calc(case_14.__file__, 'job.ini')

    def test_case_master(self):
        # this tests exercise the case of a complex logic tree
        self.run_calc(case_master.__file__, 'job.ini')
        fname = gettemp(text_table(view('mean_disagg', self.calc.datastore)))
        self.assertEqualFiles('expected/mean_disagg.rst', fname)
        os.remove(fname)

        fnames = export(('disagg-stats', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 22)
        for fname in fnames:
            if 'Mag_Dist' in fname and 'Eps' not in fname:
                self.assertEqualFiles(
                    'expected_output/%s' % strip_calc_id(fname), fname)
