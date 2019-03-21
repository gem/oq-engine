# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
import math

import numpy.testing

from openquake.baselib.general import group_array, gettemp
from openquake.baselib.datastore import read
from openquake.hazardlib import nrml
from openquake.hazardlib.sourceconverter import RuptureConverter
from openquake.commonlib.util import max_rel_diff_index
from openquake.calculators.views import view
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.event_based import get_mean_curves
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.classical import case_18 as gmpe_tables
from openquake.qa_tests_data.event_based import (
    blocksize, case_1, case_2, case_3, case_4, case_5, case_6, case_7,
    case_8, case_9, case_10, case_12, case_13, case_14, case_15, case_16,
    case_17,  case_18, case_19, case_20, case_21, mutex)
from openquake.qa_tests_data.event_based.spatial_correlation import (
    case_1 as sc1, case_2 as sc2, case_3 as sc3)


def strip_calc_id(fname):
    name = os.path.basename(fname)
    return re.sub(r'_\d+\.', '.', name)


def joint_prob_of_occurrence(gmvs_site_1, gmvs_site_2, gmv, time_span,
                             num_ses, delta_gmv=0.1):
    """
    Compute the Poissonian probability of a ground shaking value to be in the
    range [``gmv`` - ``delta_gmv`` / 2, ``gmv`` + ``delta_gmv`` / 2] at two
    different locations within a given ``time_span``.

    :param gmvs_site_1, gmvs_site_2:
        Lists of ground motion values (as floats) for two different sites.
    :param gmv:
        Reference value for computing joint probability.
    :param time_span:
        `investigation_time` parameter from the calculation which produced
        these ground motion values.
    :param num_ses:
        `ses_per_logic_tree_path` parameter from the calculation which produced
        these ground motion values. In other words, the total number of
        stochastic event sets.
    :param delta_gmv:
        the interval to consider
    """
    assert len(gmvs_site_1) == len(gmvs_site_2)
    half_delta = float(delta_gmv) / 2

    def gmv_close(v):
        return (gmv - half_delta <= v <= gmv + half_delta)
    count = 0
    for gmv_site_1, gmv_site_2 in zip(gmvs_site_1, gmvs_site_2):
        if gmv_close(gmv_site_1) and gmv_close(gmv_site_2):
            count += 1

    prob = 1 - math.exp(- (float(count) / num_ses))
    return prob


class EventBasedTestCase(CalculatorTestCase):

    def test_spatial_correlation(self):
        expected = {sc1: [0.99, 0.41],
                    sc2: [0.99, 0.64],
                    sc3: [0.99, 0.22]}

        for case in expected:
            self.run_calc(case.__file__, 'job.ini')
            oq = self.calc.oqparam
            self.assertEqual(list(oq.imtls), ['PGA'])
            dstore = read(self.calc.datastore.calc_id)
            gmf = group_array(dstore['gmf_data/data'], 'sid')
            gmvs_site_0 = gmf[0]['gmv']
            gmvs_site_1 = gmf[1]['gmv']
            joint_prob_0_5 = joint_prob_of_occurrence(
                gmvs_site_0, gmvs_site_1, 0.5, oq.investigation_time,
                oq.ses_per_logic_tree_path)
            joint_prob_1_0 = joint_prob_of_occurrence(
                gmvs_site_0, gmvs_site_1, 1.0, oq.investigation_time,
                oq.ses_per_logic_tree_path)

            p05, p10 = expected[case]
            numpy.testing.assert_almost_equal(joint_prob_0_5, p05, decimal=1)
            numpy.testing.assert_almost_equal(joint_prob_1_0, p10, decimal=1)

    def test_blocksize(self):
        # here the <AreaSource 1> is light and not split
        out = self.run_calc(blocksize.__file__, 'job.ini',
                            concurrent_tasks='3', exports='csv')
        [fname, _, sitefile] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)
        self.assertEqualFiles('expected/sites.csv', sitefile)

        # here the <AreaSource 1> is heavy and split
        out = self.run_calc(blocksize.__file__, 'job.ini',
                            concurrent_tasks='4', exports='csv')
        [fname, sig_eps, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)
        self.assertEqualFiles('expected/sig-eps.csv', sig_eps)

    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini', exports='csv,xml')

        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

        [fname] = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

        [fname] = export(('gmf_scenario/rup-0', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/gmf-rlz-0-PGA.csv', fname)

        # test that the .npz export runs
        export(('gmf_data', 'npz'), self.calc.datastore)

        export(('hcurves', 'xml'), self.calc.datastore)

        [fname] = out['hcurves', 'xml']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-PGA.xml', fname)

        # test gsim_by_imt
        out = self.run_calc(case_1.__file__, 'job.ini',
                            ses_per_logic_tree_path='20',
                            gsim_logic_tree_file='gsim_by_imt_logic_tree.xml',
                            exports='csv')

        # testing event_info
        einfo = dict(extract(self.calc.datastore, 'event_info/0'))
        self.assertEqual(einfo['trt'], 'active shallow crust')
        self.assertEqual(einfo['rupture_class'],
                         'ParametricProbabilisticRupture')
        self.assertEqual(einfo['surface_class'], 'PlanarSurface')
        self.assertEqual(einfo['serial'], 1066)
        self.assertEqual(str(einfo['gsim']),
                         '[MultiGMPE."PGA".AkkarBommer2010]\n'
                         '[MultiGMPE."SA(0.1)".SadighEtAl1997]')
        self.assertEqual(einfo['rlzi'], 0)
        self.assertEqual(einfo['grp_id'], 0)
        self.assertEqual(einfo['occurrence_rate'], 1.0)
        self.assertEqual(list(einfo['hypo']), [0., 0., 4.])

        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gsim_by_imt.csv', fname)

    def test_case_1_ruptures(self):
        self.run_calc(case_1.__file__, 'job_ruptures.ini')
        self.assertEqual(len(self.calc.datastore['ruptures']), 1)

    def test_minimum_intensity(self):
        out = self.run_calc(case_2.__file__, 'job.ini', exports='csv',
                            minimum_intensity='0.2')

        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/minimum-intensity-gmf-data.csv', fname)

    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job.ini', exports='csv')
        [gmfs, sig_eps, _sitefile] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', gmfs)
        # this is a case with truncation_level=0: sig-eps.csv must be empty
        self.assertEqualFiles('expected/sig-eps.csv', sig_eps)

        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

    def test_case_2bis(self):  # oversampling
        out = self.run_calc(case_2.__file__, 'job_2.ini', exports='csv,xml')
        [fname, _, _] = out['gmf_data', 'csv']  # 2 realizations, 1 TRT
        self.assertEqualFiles('expected/gmf-data-bis.csv', fname)
        self.assertEqual(out['gmf_data', 'xml'], [])  # exported removed
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles('expected/hc-mean.csv', fname)

    def test_case_3(self):  # 1 site, 1 rupture, 2 GSIMs
        out = self.run_calc(case_3.__file__, 'job.ini', exports='csv')
        [f, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', f)

    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job.ini', exports='csv')
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

        # exercise preclassical
        self.run_calc(case_4.__file__, 'job.ini',
                      calculation_mode='preclassical')

    def test_case_5(self):
        out = self.run_calc(case_5.__file__, 'job.ini', exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-6)

        [fname] = export(('ruptures', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/ruptures.csv', fname, delta=1E-6)

    def test_case_6(self):
        # 2 models x 3 GMPEs, different weights
        expected = [
            'hazard_curve-mean.csv',
            'quantile_curve-0.1.csv',
        ]
        out = self.run_calc(case_6.__file__, 'job.ini', exports='csv')
        fnames = out['hcurves', 'csv']
        for exp, got in zip(expected, fnames):
            self.assertEqualFiles('expected/%s' % exp, got)

        [fname] = export(('realizations', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/realizations.csv', fname)

    def test_case_7(self):
        # 2 models x 3 GMPEs, 10 samples * 40 SES
        expected = [
            'hazard_curve-mean.csv',
            'quantile_curve-0.1.csv',
            'quantile_curve-0.9.csv',
        ]
        out = self.run_calc(case_7.__file__, 'job.ini', exports='csv')
        fnames = out['hcurves', 'csv']
        mean_eb = get_mean_curves(self.calc.datastore)
        for exp, got in zip(expected, fnames):
            self.assertEqualFiles('expected/%s' % exp, got)
        mean_cl = get_mean_curves(self.calc.cl.datastore)
        reldiff, _index = max_rel_diff_index(
            mean_cl, mean_eb, min_value=0.1)
        self.assertLess(reldiff, 0.20)

        # FIXME: investigate why max_gmf_size is not stored
        # exp = self.calc.datastore.get_attr('events', 'max_gmf_size')
        # self.assertEqual(exp, 375496)

    def test_case_8(self):
        out = self.run_calc(case_8.__file__, 'job.ini', exports='csv')
        [fname] = out['ruptures', 'csv']
        self.assertEqualFiles('expected/rup_data.csv', fname)

    def test_case_9(self):
        # example with correlation: the site collection must not be filtered
        self.run_calc(case_9.__file__, 'job.ini', exports='csv')
        # this is a case where there are 2 ruptures and 1 gmv per site
        self.assertEqual(len(self.calc.datastore['gmf_data/data']), 51)

    def test_case_10(self):
        # this is a case with multiple files in the smlt uncertaintyModel
        # and with sampling
        self.run_calc(case_10.__file__, 'job.ini')
        [fname] = export(('realizations', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/realizations.csv', fname)

    def test_case_12(self):
        out = self.run_calc(case_12.__file__, 'job.ini', exports='csv')
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1_b2.csv', fname)

    def test_case_13(self):
        out = self.run_calc(case_13.__file__, 'job.ini', exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

    def test_case_14(self):
        # sampling of a logic tree of kind `on_each_source`
        out = self.run_calc(case_14.__file__, 'job.ini', exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

    def test_case_15(self):
        # an example for Japan testing also the XML rupture exporter
        self.run_calc(case_15.__file__, 'job.ini')
        [fname] = export(('ruptures', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/ruptures.csv', fname)
        [fname] = export(('ruptures', 'xml'), self.calc.datastore)
        self.assertEqualFiles('expected/ruptures.xml', fname)

    def test_case_16(self):
        # an example with site model raising warnings and autogridded exposure
        self.run_calc(case_16.__file__, 'job.ini',
                      ground_motion_fields='false')
        hid = str(self.calc.datastore.calc_id)
        self.run_calc(case_16.__file__, 'job.ini', hazard_calculation_id=hid)
        tmp = gettemp(view('global_gmfs', self.calc.datastore))
        self.assertEqualFiles('expected/global_gmfs.txt', tmp)

    def test_case_17(self):  # oversampling and save_ruptures
        # also, the grp-00 does not produce ruptures
        expected = [
            'hazard_curve-mean.csv',
            'hazard_curve-rlz-001.csv',
            'hazard_curve-rlz-002.csv',
            'hazard_curve-rlz-003.csv',
            'hazard_curve-rlz-004.csv',
        ]
        # test the --hc functionality, i.e. that ruptures are read correctly
        out = self.run_calc(case_17.__file__, 'job.ini,job.ini', exports='csv')
        fnames = out['hcurves', 'csv']
        for exp, got in zip(expected, fnames):
            self.assertEqualFiles('expected/%s' % exp, got)

        # check that a single rupture file is exported even if there are
        # several collections
        [fname] = export(('ruptures', 'xml'), self.calc.datastore.parent)
        self.assertEqualFiles('expected/ses.xml', fname)

        # check that the exported file is parseable
        rupcoll = nrml.to_python(fname, RuptureConverter(1))
        self.assertEqual(list(rupcoll), [1])  # one group
        self.assertEqual(len(rupcoll[1]), 3)  # three EBRuptures

    def test_case_18(self):  # oversampling, 3 realizations
        out = self.run_calc(case_18.__file__, 'job.ini', exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-6)

    def test_case_19(self):  # test for Vancouver using the NRCan15SiteTerm
        self.run_calc(case_19.__file__, 'job.ini')
        [gmf, _, _] = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/gmf-data.csv', gmf)

        # a test with grid and site model
        self.run_calc(case_19.__file__, 'job_grid.ini')
        self.assertEqual(len(self.calc.datastore['ruptures']), 1)

    def test_case_20(self):  # test for Vancouver using the NRCan15SiteTerm
        self.run_calc(case_20.__file__, 'job.ini')
        [gmf, _, _] = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/gmf-data.csv', gmf)

        # run again the GMF calculation, but this time from stored ruptures
        hid = str(self.calc.datastore.calc_id)
        self.run_calc(case_20.__file__, 'job.ini', hazard_calculation_id=hid)
        [gmf, _, _] = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/gmf-data-from-ruptures.csv', gmf)

    def test_case_21(self):
        self.run_calc(case_21.__file__, 'job.ini', exports='csv,xml')
        self.run_calc(case_21.__file__, 'job.ini',
                      ses_per_logic_tree_path='10',
                      number_of_logic_tree_samples='0')

    def test_overflow(self):
        too_many_imts = {'SA(%s)' % period: [0.1, 0.2, 0.3]
                         for period in numpy.arange(0.1,  1, 0.001)}
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(
                case_2.__file__, 'job.ini',
                intensity_measure_types_and_levels=str(too_many_imts))
        self.assertEqual(str(ctx.exception),
                         'The event based calculator is restricted '
                         'to 256 imts, got 900')

    def test_mutex(self):
        out = self.run_calc(mutex.__file__, 'job.ini', exports='csv,xml')
        [fname] = out['ruptures', 'xml']
        self.assertEqualFiles('expected/ses.xml', fname, delta=1E-6)
        [fname] = out['ruptures', 'csv']
        self.assertEqualFiles('expected/ruptures.csv', fname, delta=1E-6)

    def test_gmpe_tables(self):
        out = self.run_calc(
            gmpe_tables.__file__, 'job.ini',
            calculation_mode='event_based',
            investigation_time='100',
            exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf.csv', fname, delta=1E-6)
