import mock
import unittest
import numpy
from openquake.baselib.general import writetmp
from openquake.commonlib import readinput, readers
from openquake.risklib import riskinput
from openquake.commonlib.calculators import event_based
from openquake.qa_tests_data.event_based_risk import case_2


class MockAssoc(object):
    csm_info = mock.Mock()
    csm_info.get_trt_id.return_value = 0

    def __iter__(self):
        return iter([])

    def combine(self, dicts):
        return []

    def __getitem__(self, key):
        return []

rlzs_assoc = MockAssoc()


class RiskInputTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oqparam = readinput.get_oqparam(
            'job_haz.ini,job_risk.ini', pkg=case_2)
        cls.sitecol, cls.assets_by_site = readinput.get_sitecol_assets(
            cls.oqparam, readinput.get_exposure(cls.oqparam))
        cls.riskmodel = readinput.get_risk_model(cls.oqparam)

    def test_assetcol(self):
        expected = writetmp('''\
asset_ref:|S20:,site_id:uint32:,structural:float64:,deductible~structural:float64:,insurance_limit~structural:float64:
a0,0,3000,25,100
a1,1,2000,0.1,0.2
a2,2,1000,0.02,0.08
a3,2,5000,1000,3000
a4,3,500000,1000,3000
''')
        assetcol = riskinput.build_asset_collection(self.assets_by_site)
        numpy.testing.assert_equal(
            assetcol, readers.read_composite_array(expected))

    def test_get_all(self):
        self.assertEqual(
            list(self.riskmodel.get_imt_taxonomies()),
            [('PGA', ['RM']), ('SA(0.2)', ['RC']), ('SA(0.5)', ['W'])])
        self.assertEqual(len(self.sitecol), 4)
        hazard_by_site = [{}] * 4

        ri_PGA = self.riskmodel.build_input(
            'PGA', hazard_by_site, self.assets_by_site)
        assets, hazards, epsilons = ri_PGA.get_all(rlzs_assoc)
        self.assertEqual([a.id for a in assets], ['a0', 'a3', 'a4'])
        self.assertEqual(set(a.taxonomy for a in assets), set(['RM']))
        self.assertEqual(epsilons, [None, None, None])

        ri_SA_02 = self.riskmodel.build_input(
            'SA(0.2)', hazard_by_site, self.assets_by_site)
        assets, hazards, epsilons = ri_SA_02.get_all(rlzs_assoc)
        self.assertEqual([a.id for a in assets], ['a1'])
        self.assertEqual(set(a.taxonomy for a in assets), set(['RC']))
        self.assertEqual(epsilons, [None])

        ri_SA_05 = self.riskmodel.build_input(
            'SA(0.5)', hazard_by_site, self.assets_by_site)
        assets, hazards, epsilons = ri_SA_05.get_all(rlzs_assoc)
        self.assertEqual([a.id for a in assets], ['a2'])
        self.assertEqual(set(a.taxonomy for a in assets), set(['W']))
        self.assertEqual(epsilons, [None])

    def test_from_ruptures(self):
        oq = self.oqparam
        correl_model = readinput.get_correl_model(oq)
        rupcalc = event_based.EventBasedRuptureCalculator(oq)
        rupcalc.run()

        # this is case with a single SES collection
        ses_ruptures = rupcalc.datastore['sescollection'][0].values()

        gsims_by_trt_id = rupcalc.rlzs_assoc.get_gsims_by_trt_id()

        eps_dict = riskinput.make_eps_dict(
            self.assets_by_site, len(ses_ruptures), oq.master_seed,
            oq.asset_correlation)

        [ri] = self.riskmodel.build_inputs_from_ruptures(
            self.sitecol, ses_ruptures, gsims_by_trt_id, oq.truncation_level,
            correl_model, eps_dict, 1)

        assets, hazards, epsilons = ri.get_all(rlzs_assoc, self.assets_by_site)
        self.assertEqual([a.id for a in assets],
                         ['a0', 'a1', 'a2', 'a3', 'a4'])
        self.assertEqual(set(a.taxonomy for a in assets),
                         set(['RM', 'RC', 'W']))
        self.assertEqual(map(len, epsilons), [20] * 5)
