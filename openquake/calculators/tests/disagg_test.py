# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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
from openquake.baselib import hdf5
from openquake.baselib.general import gettemp
from openquake.hazardlib.probability_map import combine
from openquake.hazardlib.contexts import read_ctxs
from openquake.calculators import getters
from openquake.calculators.views import view
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.tests.classical_test import check_disagg_by_src
from openquake.qa_tests_data.disagg import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_master)

aae = numpy.testing.assert_almost_equal


class DisaggregationTestCase(CalculatorTestCase):

    def assert_curves_ok(self, expected, test_dir, fmt='xml', delta=None):
        self.run_calc(test_dir, 'job.ini', calculation_mode='classical')
        hc_id = self.calc.datastore.calc_id
        out = self.run_calc(test_dir, 'job.ini', exports=fmt,
                            hazard_calculation=str(hc_id))
        got = out['disagg', fmt]
        self.assertEqual(len(expected), len(got))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected_output/%s' % fname, actual)
        return out

    def test_case_1(self):
        self.assert_curves_ok(
            ['rlz-0-PGA-sid-0-poe-0_Lon_Lat.csv',
             'rlz-0-PGA-sid-0-poe-0_Mag.csv',
             'rlz-0-PGA-sid-0-poe-0_Mag_Dist.csv',
             'rlz-0-PGA-sid-0-poe-1_Lon_Lat.csv',
             'rlz-0-PGA-sid-0-poe-1_Mag.csv',
             'rlz-0-PGA-sid-0-poe-1_Mag_Dist.csv',
             'rlz-0-SA(0.025)-sid-0-poe-0_Lon_Lat.csv',
             'rlz-0-SA(0.025)-sid-0-poe-0_Mag.csv',
             'rlz-0-SA(0.025)-sid-0-poe-0_Mag_Dist.csv',
             'rlz-0-SA(0.025)-sid-0-poe-1_Lon_Lat.csv',
             'rlz-0-SA(0.025)-sid-0-poe-1_Mag.csv',
             'rlz-0-SA(0.025)-sid-0-poe-1_Mag_Dist.csv'],
            case_1.__file__,
            fmt='csv')

        # disaggregation by source group
        rlzs = self.calc.datastore['full_lt'].get_realizations()
        ws = [rlz.weight for rlz in rlzs]
        sids = self.calc.sitecol.sids
        oq = self.calc.oqparam
        pgetter = getters.PmapGetter(self.calc.datastore, ws, sids,
                                     oq.imtls, oq.poes)
        pgetter.init()
        pmaps = []
        for grp in sorted(self.calc.datastore['poes']):
            pmaps.append(pgetter.get_mean(grp))
        # make sure that the combination of the contributions is okay
        pmap = pgetter.get_mean()  # total mean map
        cmap = combine(pmaps)  # combination of the mean maps per source group
        for sid in pmap:
            numpy.testing.assert_almost_equal(pmap[sid].array, cmap[sid].array)

        check_disagg_by_src(self.calc.datastore)

    def test_case_2(self):
        # this is a case with disagg_outputs = Mag and 4 realizations
        # site #0 is partially discarded
        if sys.platform == 'darwin':
            raise unittest.SkipTest('MacOSX')
        self.assert_curves_ok(
            ['rlz-0-SA(0.1)-sid-0.xml',
             'rlz-0-SA(0.1)-sid-1.xml',
             'rlz-1-SA(0.1)-sid-0.xml',
             'rlz-1-SA(0.1)-sid-1.xml',
             'rlz-2-SA(0.1)-sid-1.xml',
             'rlz-3-SA(0.1)-sid-1.xml'],
            case_2.__file__)

        # check that the CSV exporter does not break
        fnames = export(('disagg', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles(
                'expected_output/%s' % strip_calc_id(fname), fname)

        # test extract disagg_layer for Mag
        aw = extract(self.calc.datastore, 'disagg_layer?kind=Mag&'
                     'imt=SA(0.1)&poe_id=0')
        self.assertEqual(aw.dtype.names,
                         ('site_id', 'lon', 'lat',
                          'lon_bins', 'lat_bins', 'Mag-SA(0.1)-None',
                          'iml-SA(0.1)-None'))

        # check the custom_site_id
        aw = extract(self.calc.datastore, 'sitecol?field=custom_site_id')
        self.assertEqual(list(aw), [100, 200])

    def test_case_3(self):
        # a case with poes_disagg too large
        with self.assertRaises(SystemExit) as ctx:
            self.run_calc(case_3.__file__, 'job.ini')
        self.assertEqual(str(ctx.exception),
                         'Cannot do any disaggregation: zero hazard')

    def test_case_4(self):
        # this is case with number of lon/lat bins different for site 0/site 1
        # this exercise sampling
        self.run_calc(case_4.__file__, 'job.ini')

        fnames = export(('disagg', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 32)  # 1 sid x 8 keys x 2 poe x 2 imt
        for fname in fnames:
            if 'Mag_Dist' in fname and 'Eps' not in fname:
                self.assertEqualFiles(
                    'expected_output/%s' % strip_calc_id(fname), fname)

    def test_case_5(self):
        # test gridded nonparametric sources
        self.run_calc(case_5.__file__, 'job.ini')
        fnames = export(('disagg', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

        # there is a collapsed nonparametric source with len(probs_occur)==3

    def test_case_6(self):
        # test with international date line
        self.run_calc(case_6.__file__, 'job.ini')

        # test CSV export
        fnames = export(('disagg', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

        # test the CSVs are readable
        for fname in fnames:
            hdf5.read_csv(fname)

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

        check_disagg_by_src(self.calc.datastore)

    def test_case_7(self):
        # test with 7+2 ruptures of two source models, 1 GSIM, 1 site
        self.run_calc(case_7.__file__, 'job.ini')
        ctxs0 = read_ctxs(self.calc.datastore, 'mag_7.70', gidx=0)[0]
        ctxs1 = read_ctxs(self.calc.datastore, 'mag_7.70', gidx=1)[0]
        self.assertEqual(len(ctxs0), 7)  # rlz-0, the closest to the mean
        self.assertEqual(len(ctxs1), 2)  # rlz-1, the one to discard
        # checking that the wrong realization is indeed discarded
        pd = self.calc.datastore['performance_data'][:]
        pd = pd[pd['operation'] == b'disaggregate']
        self.assertEqual(pd['counts'], 1)  # because g_by_z is empty

        haz = self.calc.datastore['hmap4'][0, 0, :, 0]  # shape NMPZ
        self.assertEqual(haz[0], 0)  # shortest return period => 0 hazard
        self.assertEqual(haz[1], 0.18757115242025785)
        
    def test_case_master(self):
        # this tests exercise the case of a complex logic tree
        self.run_calc(case_master.__file__, 'job.ini')
        fname = gettemp(view('mean_disagg', self.calc.datastore))
        self.assertEqualFiles('expected/mean_disagg.rst', fname)
        os.remove(fname)

        fnames = export(('disagg', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 64)  # 2 sid x 8 keys x 2 poe x 2 imt
        for fname in fnames:
            if 'Mag_Dist' in fname and 'Eps' not in fname:
                self.assertEqualFiles(
                    'expected_output/%s' % strip_calc_id(fname), fname)

        check_disagg_by_src(self.calc.datastore)
