from numpy.testing import assert_almost_equal as aae
from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_damage import (
    case_1, case_2, case_3, case_4)

from openquake.commonlib.tests.calculators import CalculatorTestCase


class ScenarioDamageTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'scenario_damage')
    def _test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini')
        self.assertEqualFiles('expected.xml', out['gmf_xml'])

    @attr('qa', 'risk', 'scenario_damage')
    def _test_case_2(self):
        medians = self.medians(case_2)['PGA']
        aae(medians, [0.37412136, 0.19021782, 0.1365383], decimal=2)

    @attr('qa', 'risk', 'scenario_damage')
    def _test_case_3(self):
        medians_dict = self.medians(case_3)
        medians_pga = medians_dict['PGA']
        medians_sa = medians_dict['SA(0.1)']
        aae(medians_pga, [0.48155582, 0.21123045, 0.14484586], decimal=2)
        aae(medians_sa, [0.93913177, 0.40880148, 0.2692668], decimal=2)

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job_haz.ini,job_risk.ini')
        self.assertEqualFiles(
            'expected_dmg_dist_per_asset.xml', out['dmg_dist_per_asset_xml'])
        self.assertEqualFiles(
            'expected_dmg_dist_per_taxonomy.xml',
            out['dmg_dist_per_taxonomy_xml'])
        self.assertEqualFiles(
            'expected_dmg_dist_total.xml', out['dmg_dist_total_xml'])
        self.assertEqualFiles(
            'expected_collapse_map.xml', out['collapse_map_xml'])
