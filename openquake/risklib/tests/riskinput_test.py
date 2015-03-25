import unittest

from openquake.commonlib import readinput
from openquake.risklib import riskinput
from openquake.commonlib.calculators import event_based
from openquake.qa_tests_data.event_based_risk import case_2


class RiskInputTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oqparam = readinput.get_oqparam(
            'job_haz.ini,job_risk.ini', pkg=case_2)
        cls.sitecol, cls.assets_by_site = readinput.get_sitecol_assets(
            cls.oqparam, readinput.get_exposure(cls.oqparam))
        cls.riskmodel = readinput.get_risk_model(cls.oqparam)

    def test_get_all(self):
        self.assertEqual(
            list(self.riskmodel.get_imt_taxonomies()),
            [('PGA', ['RM']), ('SA(0.2)', ['RC']), ('SA(0.5)', ['W'])])
        self.assertEqual(len(self.sitecol), 4)
        hazard_by_site = [None] * 4

        ri_PGA = self.riskmodel.build_input(
            'PGA', hazard_by_site, self.assets_by_site)
        assets, hazards, epsilons = ri_PGA.get_all()
        self.assertEqual([a.id for a in assets], ['a0', 'a3', 'a4'])
        self.assertEqual(set(a.taxonomy for a in assets), set(['RM']))
        self.assertEqual(epsilons, [None, None, None])

        ri_SA_02 = self.riskmodel.build_input(
            'SA(0.2)', hazard_by_site, self.assets_by_site)
        assets, hazards, epsilons = ri_SA_02.get_all()
        self.assertEqual([a.id for a in assets], ['a1'])
        self.assertEqual(set(a.taxonomy for a in assets), set(['RC']))
        self.assertEqual(epsilons, [None])

        ri_SA_05 = self.riskmodel.build_input(
            'SA(0.5)', hazard_by_site, self.assets_by_site)
        assets, hazards, epsilons = ri_SA_05.get_all()
        self.assertEqual([a.id for a in assets], ['a2'])
        self.assertEqual(set(a.taxonomy for a in assets), set(['W']))
        self.assertEqual(epsilons, [None])

    def test_from_ruptures(self):
        oq = self.oqparam
        correl_model = readinput.get_correl_model(oq)
        rupcalc = event_based.EventBasedRuptureCalculator(oq)
        # this is case with a single TRT
        [(trt_id, ses_ruptures)] = rupcalc.run()['ruptures_by_trt'].items()

        gsims = rupcalc.rlzs_assoc.get_gsims_by_trt_id()[trt_id]

        eps_dict = riskinput.make_eps_dict(
            self.assets_by_site, len(ses_ruptures), oq.master_seed,
            getattr(oq, 'asset_correlation', 0))

        ri = self.riskmodel.build_input_from_ruptures(
            self.sitecol, self.assets_by_site, ses_ruptures,
            gsims, oq.truncation_level, correl_model, eps_dict)

        assets, hazards, epsilons = ri.get_all()
        self.assertEqual([a.id for a in assets],
                         ['a0', 'a1', 'a2', 'a3', 'a4'])
        self.assertEqual(set(a.taxonomy for a in assets),
                         set(['RM', 'RC', 'W']))
        self.assertEqual(map(len, epsilons), [20] * 5)
