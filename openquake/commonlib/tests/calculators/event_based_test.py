import csv
import math
from nose.plugins.attrib import attr

import numpy.testing

from openquake.baselib.general import AccumDict
from openquake.hazardlib.site import FilteredSiteCollection
from openquake.commonlib.util import max_rel_diff_index
from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.qa_tests_data.event_based import (
    blocksize, case_1, case_2, case_4, case_5, case_6, case_7, case_12,
    case_13, case_17, case_18)
from openquake.qa_tests_data.event_based.spatial_correlation import (
    case_1 as sc1, case_2 as sc2, case_3 as sc3)


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
    gmv_close = lambda v: (gmv - half_delta <= v <= gmv + half_delta)
    count = 0
    for gmv_site_1, gmv_site_2 in zip(gmvs_site_1, gmvs_site_2):
        if gmv_close(gmv_site_1) and gmv_close(gmv_site_2):
            count += 1

    prob = 1 - math.exp(- (float(count) / (time_span * num_ses)) * time_span)
    return prob


def get_gmfs_by_imt(fname, sitecol, imts):
    """
    Return a list of dictionaries with a ground motion field per IMT,
    one dictionary per rupture.

    :param fname: path to the CSV file
    :param sitecol: the underlying site collection
    :param imts: the IMTs corresponding to the columns in the CSV file
    """
    dicts = []
    with open(fname) as f:
        for row in csv.reader(f):
            indices = map(int, row[1].split())
            sc = FilteredSiteCollection(indices, sitecol)
            dic = AccumDict()
            for imt, col in zip(imts, row[2:]):
                gmf = numpy.array(map(float, col.split()))
                dic[imt] = sc.expand(gmf, 0)
            dic.tag = row[0]
            dicts.append(dic)
    return sorted(dicts, key=lambda dic: dic.tag)


class EventBasedTestCase(CalculatorTestCase):

    @attr('qa', 'hazard', 'event_based')
    def test_spatial_correlation(self):
        expected = {sc1: [0.99, 0.41],
                    sc2: [0.99, 0.64],
                    sc3: [0.99, 0.22]}

        for case in expected:
            out = self.run_calc(case.__file__, 'job.ini')
            oq = self.calc.oqparam
            self.assertEqual(list(oq.imtls), ['PGA'])

            gmfs = get_gmfs_by_imt(out['0-BooreAtkinson2008.csv'],
                                   self.calc.sitecol, oq.imtls)
            gmvs_site_1 = [gmf['PGA'][0] for gmf in gmfs]
            gmvs_site_2 = [gmf['PGA'][1] for gmf in gmfs]

            joint_prob_0_5 = joint_prob_of_occurrence(
                gmvs_site_1, gmvs_site_2, 0.5, oq.investigation_time,
                oq.ses_per_logic_tree_path)
            joint_prob_1_0 = joint_prob_of_occurrence(
                gmvs_site_1, gmvs_site_2, 1.0, oq.investigation_time,
                oq.ses_per_logic_tree_path)

            p05, p10 = expected[case]
            numpy.testing.assert_almost_equal(joint_prob_0_5, p05, decimal=1)
            numpy.testing.assert_almost_equal(joint_prob_1_0, p10, decimal=1)

    @attr('qa', 'hazard', 'event_based')
    def test_blocksize(self):
        out = self.run_calc(blocksize.__file__, 'job.ini', concurrent_tasks=4)
        self.assertEqualFiles('expected/0-ChiouYoungs2008.csv',
                              out['0-ChiouYoungs2008.csv'], sorted)
        out = self.run_calc(blocksize.__file__, 'job.ini', concurrent_tasks=8)
        self.assertEqualFiles('expected/0-ChiouYoungs2008.csv',
                              out['0-ChiouYoungs2008.csv'], sorted)

    @attr('qa', 'hazard', 'event_based')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/0-SadighEtAl1997.csv',
            out['0-SadighEtAl1997.csv'], sorted)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/0-SadighEtAl1997.csv',
            out['0-SadighEtAl1997.csv'], sorted)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_3(self):  # oversampling
        out = self.run_calc(case_2.__file__, 'job_2.ini', exports='csv')
        self.assertEqualFiles(
            'expected/SadighEtAl1997.csv',
            out['0-SadighEtAl1997.csv'], sorted)
        self.assertEqualFiles(
            'expected/hc-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])
        # NB: we are testing that the file ltr_1.csv is equal to
        # ltr_0.csv, as it should be for the hazard curves
        self.assertEqualFiles(
            'expected/hc-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_1.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_5(self):
        expected = '''\
3-AkkarBommer2010.csv
4-AkkarBommer2010.csv
4-CauzziFaccioli2008.csv
4-ChiouYoungs2008.csv
4-Campbell2003SHARE.csv
4-ToroEtAl2002SHARE.csv
5-AkkarBommer2010.csv
6-ToroEtAl2002SHARE.csv
7-FaccioliEtAl2010.csv'''.split()
        out = self.run_calc(case_5.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname], sorted)

    @attr('qa', 'hazard', 'event_based')
    def test_case_6(self):
        # 2 models x 3 GMPEs, different weights
        expected = [
            'hazard_curve-mean.csv',
            'quantile_curve-0.1.csv',
        ]
        out = self.run_calc(case_6.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'event_based')
    def test_case_7(self):
        # 2 models x 3 GMPEs, 100 samples * 10 SES
        expected = [
            'hazard_curve-mean.csv',
            'quantile_curve-0.1.csv',
            'quantile_curve-0.9.csv',
        ]
        out = self.run_calc(case_7.__file__, 'job.ini', exports='csv')
        mean_eb = self.calc.mean_curves
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])
        mean_cl = self.calc.cl.mean_curves
        for imt in mean_cl:
            reldiff, _index = max_rel_diff_index(
                mean_cl[imt], mean_eb[imt], min_value=0.1)
            self.assertLess(reldiff, 0.41)

    @attr('qa', 'hazard', 'event_based')
    def test_case_12(self):
        out = self.run_calc(case_12.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles('expected/0-SadighEtAl1997.csv',
                              out['0-SadighEtAl1997.csv'], sorted)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1_b2.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1_b2.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_13(self):
        out = self.run_calc(case_13.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles('expected/0-BooreAtkinson2008.csv',
                              out['0-BooreAtkinson2008.csv'], sorted)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_17(self):  # oversampling
        expected = [
            'hazard_curve-smltp_b1-gsimltp_*-ltr_0.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_1.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_2.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_3.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_4.csv',
        ]
        out = self.run_calc(case_17.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname], sorted)

    @attr('qa', 'hazard', 'event_based')
    def test_case_18(self):  # oversampling
        expected = [
            '0-AkkarBommer2010.csv',
            '0-CauzziFaccioli2008.csv',
        ]
        out = self.run_calc(case_18.__file__, 'job_3.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname], sorted)
