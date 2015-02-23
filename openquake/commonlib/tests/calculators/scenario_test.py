import numpy
from numpy.testing import assert_almost_equal as aae
from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8)

from openquake.commonlib.tests.calculators import CalculatorTestCase


def count_close(gmf_value, gmvs_site_one, gmvs_site_two, delta=0.1):
    """
    Count the number of pairs of gmf values
    within the specified range.
    See https://bugs.launchpad.net/openquake/+bug/1097646
    attached Scenario Hazard script.
    """
    lower_bound = gmf_value - delta / 2.
    upper_bound = gmf_value + delta / 2.
    return sum((lower_bound <= v1 <= upper_bound) and
               (lower_bound <= v2 <= upper_bound)
               for v1, v2 in zip(gmvs_site_one, gmvs_site_two))


class ScenarioHazardTestCase(CalculatorTestCase):

    def frequencies(self, case, fst_value, snd_value):
        [gmfs] = self.execute(case.__file__, 'job.ini').values()
        realizations = float(self.calc.oqparam.number_of_ground_motion_fields)
        [imt] = self.calc.oqparam.imtls.keys()
        gmvs_within_range_fst = count_close(
            fst_value, gmfs[imt][0], gmfs[imt][1])
        gmvs_within_range_snd = count_close(
            snd_value, gmfs[imt][0], gmfs[imt][1])
        return (gmvs_within_range_fst / realizations,
                gmvs_within_range_snd / realizations)

    def medians(self, case):
        [gmfs] = self.execute(case.__file__, 'job.ini').values()
        return {imt: map(numpy.median, gmfs[imt]) for imt in gmfs}

    @attr('qa', 'hazard', 'scenario')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini', exports='xml')
        self.assertEqualFiles('expected.xml', out['gmf', 'xml'])

    @attr('qa', 'hazard', 'scenario')
    def test_case_2(self):
        medians = self.medians(case_2)['PGA']
        aae(medians, [0.37412136, 0.19021782, 0.1365383], decimal=2)

    @attr('qa', 'hazard', 'scenario')
    def test_case_3(self):
        medians_dict = self.medians(case_3)
        medians_pga = medians_dict['PGA']
        medians_sa = medians_dict['SA(0.1)']
        aae(medians_pga, [0.48155582, 0.21123045, 0.14484586], decimal=2)
        aae(medians_sa, [0.93913177, 0.40880148, 0.2692668], decimal=2)

    @attr('qa', 'hazard', 'scenario')
    def test_case_4(self):
        medians = self.medians(case_4)['PGA']
        aae(medians, [0.41615372, 0.22797466, 0.1936226], decimal=2)

    @attr('qa', 'hazard', 'scenario')
    def test_case_5(self):
        f1, f2 = self.frequencies(case_5, 0.5, 1.0)
        self.assertAlmostEqual(f1, 0.03, places=2)
        self.assertAlmostEqual(f2, 0.003, places=3)

    @attr('qa', 'hazard', 'scenario')
    def test_case_6(self):
        f1, f2 = self.frequencies(case_6, 0.5, 1.0)
        self.assertAlmostEqual(f1, 0.05, places=2)
        self.assertAlmostEqual(f2, 0.006, places=3)

    @attr('qa', 'hazard', 'scenario')
    def test_case_7(self):
        f1, f2 = self.frequencies(case_7, 0.5, 1.0)
        self.assertAlmostEqual(f1, 0.02, places=2)
        self.assertAlmostEqual(f2, 0.002, places=3)

    @attr('qa', 'hazard', 'scenario')
    def test_case_8(self):
        # test for a GMPE requiring hypocentral depth, since it was
        # broken: https://bugs.launchpad.net/oq-engine/+bug/1334524
        # I am not really checking anything, only that it runs
        f1, f2 = self.frequencies(case_8, 0.5, 1.0)
        self.assertAlmostEqual(f1, 0)
        self.assertAlmostEqual(f2, 0)

    @attr('qa', 'hazard', 'scenario')
    def test_case_9(self):
        # all sites were filtered out
        out = self.run_calc(case_1.__file__, 'job.ini',
                            maximum_distance=0.1, exports='csv')
        self.assertEqualFiles(
            'BooreAtkinson2008_gmf.csv', out['gmf', 'csv'])
