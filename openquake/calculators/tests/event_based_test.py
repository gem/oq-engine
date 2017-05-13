# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from __future__ import division
import os
import re
import math
from nose.plugins.attrib import attr

import numpy.testing

from openquake.baselib.general import group_array, writetmp
from openquake.hazardlib import nrml
from openquake.hazardlib.sourceconverter import RuptureConverter
from openquake.commonlib.datastore import read
from openquake.commonlib.util import max_rel_diff_index
from openquake.calculators.views import rst_table
from openquake.calculators.export import export
from openquake.calculators.event_based import get_mean_curves
from openquake.calculators.tests import CalculatorTestCase, REFERENCE_OS
from openquake.qa_tests_data.event_based import (
    blocksize, case_1, case_2, case_3, case_4, case_5, case_6, case_7,
    case_8, case_12, case_13, case_17, case_18)
from openquake.qa_tests_data.event_based.spatial_correlation import (
    case_1 as sc1, case_2 as sc2, case_3 as sc3)


def strip_calc_id(fname):
    name = os.path.basename(fname)
    return re.sub('_\d+\.', '.', name)


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

    @attr('qa', 'hazard', 'event_based')
    def test_spatial_correlation(self):
        expected = {sc1: [0.99, 0.41],
                    sc2: [0.99, 0.64],
                    sc3: [0.99, 0.22]}

        for case in expected:
            self.run_calc(case.__file__, 'job.ini')
            oq = self.calc.oqparam
            self.assertEqual(list(oq.imtls), ['PGA'])
            dstore = read(self.calc.datastore.calc_id)
            gmf = group_array(
                dstore['gmf_data/grp-00/BooreAtkinson2008()'], 'sid')
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

    @attr('qa', 'hazard', 'event_based')
    def test_blocksize(self):
        # here the <AreaSource 1> is light and not split
        out = self.run_calc(blocksize.__file__, 'job.ini',
                            concurrent_tasks='3', exports='csv')
        [fname] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

        # here the <AreaSource 1> is heavy and split
        out = self.run_calc(blocksize.__file__, 'job.ini',
                            concurrent_tasks='4', exports='csv')
        [fname] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

    @attr('qa', 'hazard', 'event_based')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini', exports='csv,xml')

        [fname] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

        [fname] = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

        [fname] = export(('gmf_data/4294967296', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/gmf-65536.csv', fname)

        # test that the .npz export runs
        export(('gmf_data', 'npz'), self.calc.datastore)

        [fname] = out['hcurves', 'xml']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-PGA.xml', fname)

    @attr('qa', 'hazard', 'event_based')
    def test_minimum_intensity(self):
        out = self.run_calc(case_2.__file__, 'job.ini', exports='csv',
                            minimum_intensity='0.4')

        [fname] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/minimum-intensity-gmf-data.csv', fname)

    @attr('qa', 'hazard', 'event_based')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job.ini', exports='csv')
        [fname] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

    @attr('qa', 'hazard', 'event_based')
    def test_case_2bis(self):  # oversampling
        out = self.run_calc(case_2.__file__, 'job_2.ini', exports='csv,xml')
        [fname] = out['gmf_data', 'csv']  # 2 realizations, 1 TRT
        self.assertEqualFiles('expected/gmf-data-bis.csv', fname)

        ltr0 = out['gmf_data', 'xml'][0]
        self.assertEqualFiles('expected/gmf-smltp_b1-gsimltp_b1-ltr_0.xml',
                              ltr0)

        ltr = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hc-smltp_b1-gsimltp_b1-ltr_0.csv', ltr[0])
        self.assertEqualFiles(
            'expected/hc-smltp_b1-gsimltp_b1-ltr_1.csv', ltr[1])

    @attr('qa', 'hazard', 'event_based')
    def test_case_3(self):  # 1 site, 1 rupture, 2 GSIMs
        out = self.run_calc(case_3.__file__, 'job.ini', exports='csv')
        [f] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', f)

    @attr('qa', 'hazard', 'event_based')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job.ini', exports='csv')
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

    @attr('qa', 'hazard', 'event_based')
    def test_case_5(self):
        out = self.run_calc(case_5.__file__, 'job.ini', exports='csv')
        [fname] = out['gmf_data', 'csv']
        if REFERENCE_OS:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                                  delta=1E-6)

        [fname] = export(('ruptures', 'csv'), self.calc.datastore)
        if REFERENCE_OS:
            self.assertEqualFiles('expected/ruptures.csv', fname)

    @attr('qa', 'hazard', 'event_based')
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

        [fname] = out['realizations', 'csv']
        self.assertEqualFiles('expected/realizations.csv', fname)

        # test for the mean gmv
        got = writetmp(rst_table(self.calc.datastore['gmdata'].value))
        self.assertEqualFiles('expected/gmdata.csv', got)

    @attr('qa', 'hazard', 'event_based')
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
        for imt in mean_cl.dtype.fields:
            reldiff, _index = max_rel_diff_index(
                mean_cl[imt], mean_eb[imt], min_value=0.1)
            self.assertLess(reldiff, 0.20)

    @attr('qa', 'hazard', 'event_based')
    def test_case_8(self):
        out = self.run_calc(case_8.__file__, 'job.ini', exports='csv')
        [fname] = out['ruptures', 'csv']
        if REFERENCE_OS:
            self.assertEqualFiles('expected/rup_data.csv', fname)

    @attr('qa', 'hazard', 'event_based')
    def test_case_12(self):
        out = self.run_calc(case_12.__file__, 'job.ini', exports='csv')
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1_b2.csv', fname)

    @attr('qa', 'hazard', 'event_based')
    def test_case_13(self):
        out = self.run_calc(case_13.__file__, 'job.ini', exports='csv')
        [fname] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

    @attr('qa', 'hazard', 'event_based')
    def test_case_17(self):  # oversampling and save_ruptures
        expected = [
            'hazard_curve-mean.csv',
            'hazard_curve-rlz-001.csv',
            'hazard_curve-rlz-002.csv',
            'hazard_curve-rlz-003.csv',
            'hazard_curve-rlz-004.csv',
        ]
        # test --hc functionality, i.e. that the ruptures are read correctly
        out = self.run_calc(case_17.__file__, 'job.ini,job.ini', exports='csv')
        fnames = out['hcurves', 'csv']
        for exp, got in zip(expected, fnames):
            self.assertEqualFiles('expected/%s' % exp, got)

        # check that a single rupture file is exported even if there are
        # several collections
        [fname] = export(('ruptures', 'xml'), self.calc.datastore)
        self.assertEqualFiles('expected/ses.xml', fname)

        # check that the exported file is parseable
        rupcoll = nrml.parse(fname, RuptureConverter(1))
        self.assertEqual(list(rupcoll), [1])  # one group
        self.assertEqual(len(rupcoll[1]), 3)  # three EBRuptures

    @attr('qa', 'hazard', 'event_based')
    def test_case_18(self):  # oversampling, 3 realizations
        out = self.run_calc(case_18.__file__, 'job.ini', exports='csv')
        [fname] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-6)

    @attr('qa', 'hazard', 'event_based')
    def test_overflow(self):
        too_many_imts = {'SA(%s)' % period: [0.1, 0.2, 0.3]
                         for period in numpy.arange(0.1,  1, 0.001)}
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(
                case_1.__file__, 'job.ini',
                intensity_measure_types_and_levels=str(too_many_imts))
        self.assertEqual(str(ctx.exception),
                         'The event based calculator is restricted '
                         'to 256 imts, got 900')
