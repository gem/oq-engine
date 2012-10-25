# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from django.contrib.gis.geos import GEOSGeometry
from lxml import etree
from StringIO import StringIO
import os
import tempfile
import unittest

from openquake.db import models
from openquake.calculators.risk.classical import core as classical_core
from openquake.calculators.risk.event_based import core as eb_core
from openquake.calculators.risk.general import BaseRiskCalculator
from openquake.calculators.risk.general import Block
from openquake.calculators.risk.general import ProbabilisticRiskCalculator
from openquake import engine
from openquake import kvs
from openquake import shapes
from openquake.output import hazard
from risklib import vulnerability_function

from tests.utils import helpers


class ProbabilisticEventBasedTestCase(unittest.TestCase, helpers.DbTestCase):

    job = None
    assets = []
    emdl = None

    @classmethod
    def setUpClass(cls):
        path = os.path.join(helpers.SCHEMA_EXAMPLES_DIR, "PEB-exposure.yaml")
        inputs = [("exposure", path)]
        cls.job = cls.setup_classic_job(inputs=inputs)
        [input] = models.inputs4job(cls.job.id, input_type="exposure",
                                    path=path)
        owner = models.OqUser.objects.get(user_name="openquake")
        cls.emdl = input.model()
        if not cls.emdl:
            cls.emdl = models.ExposureModel(
                owner=owner, input=input, description="PEB exposure model",
                category="PEB storages sheds", stco_unit="nuts",
                stco_type="aggregated", reco_unit="pebbles",
                reco_type="aggregated")
            cls.emdl.save()
        values = [22.61, 124.27, 42.93, 29.37, 40.68, 178.47]
        for x, value in zip([float(v) for v in range(20, 27)], values):
            site = shapes.Site(x, x + 11)
            location = GEOSGeometry(site.point.to_wkt())
            asset = models.ExposureData(exposure_model=cls.emdl, taxonomy="ID",
                                        asset_ref="asset_%s" % x, stco=value,
                                        site=location, reco=value * 0.75)
            asset.save()
            cls.assets.append(asset)

    def setUp(self):
        self.params = {}
        self.params["OUTPUT_DIR"] = helpers.OUTPUT_DIR
        self.params["BASE_PATH"] = "."
        self.params["INVESTIGATION_TIME"] = 50.0

        self.job_ctxt = helpers.create_job(
            self.params, base_path=".", job_id=self.job.id,
            oq_job=self.job, oq_job_profile=models.profile4job(self.job.id))
        self.job_id = self.job_ctxt.job_id
        self.job_ctxt.to_kvs()

        self.vulnerability_function2 = vulnerability_function.VulnerabilityFunction([
            0.0, 0.04, 0.08, 0.12, 0.16, 0.2, 0.24, 0.28, 0.32, 0.36,
            0.4, 0.44, 0.48, 0.53, 0.57, 0.61, 0.65, 0.69, 0.73, 0.77, 0.81,
            0.85, 0.89, 0.93, 0.97, 1.01, 1.05, 1.09, 1.13, 1.17, 1.21, 1.25,
            1.29, 1.33, 1.37, 1.41, 1.45, 1.49, 1.54, 1.58, 1.62, 1.66, 1.7,
            1.74, 1.78, 1.82, 1.86, 1.9, 1.94, 1.98, 2.02, 2.06, 2.1, 2.14,
            2.18, 2.22, 2.26, 2.3, 2.34, 2.38, 2.42, 2.46, 2.51, 2.55, 2.59,
            2.63, 2.67, 2.71, 2.75, 2.79, 2.83, 2.87, 2.91, 2.95, 2.99, 3.03,
            3.07, 3.11, 3.15, 3.19, 3.23, 3.27, 3.31, 3.35, 3.39, 3.43, 3.47,
            3.52, 3.56, 3.6, 3.64, 3.68, 3.72, 3.76, 3.8, 3.84, 3.88, 3.92,
            3.96, 4.0], [0.0, 0.0, 0.0, 0.01, 0.04, 0.07, 0.11, 0.15, 0.2,
            0.25, 0.3, 0.35, 0.39, 0.43, 0.47, 0.51, 0.55, 0.58, 0.61, 0.64,
            0.67, 0.69, 0.71, 0.73, 0.75, 0.77, 0.79, 0.8, 0.81, 0.83, 0.84,
            0.85, 0.86, 0.87, 0.88, 0.89, 0.89, 0.9, 0.91, 0.91, 0.92, 0.92,
            0.93, 0.93, 0.94, 0.94, 0.94, 0.95, 0.95, 0.95, 0.95, 0.96, 0.96,
            0.96, 0.96, 0.97, 0.97, 0.97, 0.97, 0.97, 0.97, 0.98, 0.98, 0.98,
            0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.99, 0.99, 0.99, 0.99,
            0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99,
            0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 1.0, 1.0,
            1.0, 1.0, 1.0], [0.0] * 100, "LN")

        # deleting keys in kvs
        kvs.get_client().flushall()

        kvs.set_value_json_encoded(
            kvs.tokens.vuln_key(self.job_id),
            {"ID": self.vulnerability_function2.to_json()})
        kvs.set_value_json_encoded(
            kvs.tokens.vuln_key(self.job_id, retrofitted=True),
            {"ID": self.vulnerability_function2.to_json()})

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def test_compute_bcr(self):
        cfg_path = helpers.demo_file(
            'probabilistic_event_based_risk/config.gem')
        helpers.delete_profile(self.job)
        job_profile, params, sections = engine.import_job_profile(
            cfg_path, self.job)
        job_profile.calc_mode = 'event_based_bcr'
        job_profile.interest_rate = 0.05
        job_profile.asset_life_expectancy = 50
        job_profile.region = GEOSGeometry(shapes.polygon_ewkt_from_coords(
            '0.0, 0.0, 0.0, 2.0, 2.0, 2.0, 2.0, 0.0'))
        job_profile.region_grid_spacing = 0.1
        job_profile.maximum_distance = 200.0
        job_profile.gmf_random_seed = None
        job_profile.save()

        params.update(dict(CALCULATION_MODE='Event Based BCR',
                           INTEREST_RATE='0.05',
                           ASSET_LIFE_EXPECTANCY='50',
                           MAXIMUM_DISTANCE='200.0',
                           REGION_VERTEX=('0.0, 0.0, 0.0, 2.0, '
                                          '2.0, 2.0, 2.0, 0.0'),
                           REGION_GRID_SPACING='0.1'))

        job_ctxt = engine.JobContext(
            params, self.job_id, sections=sections, oq_job_profile=job_profile)

        calculator = eb_core.EventBasedRiskCalculator(job_ctxt)

        self.block_id = 7
        SITE = shapes.Site(1.0, 1.0)
        block = Block(self.job_id, self.block_id, (SITE, ))
        block.to_kvs()

        location = GEOSGeometry(SITE.point.to_wkt())
        asset = models.ExposureData(exposure_model=self.emdl, taxonomy="ID",
                                    asset_ref=22.61, stco=1, reco=123.45,
                                    site=location)
        asset.save()

        calculator.compute_risk(self.block_id)

        result_key = kvs.tokens.bcr_block_key(self.job_id, self.block_id)
        result = kvs.get_value_json_decoded(result_key)
        expected_result = {'bcr': 0.0, 'eal_original': 0.0,
                           'eal_retrofitted': 0.0}
        helpers.assertDeepAlmostEqual(
            self, [[[1, 1], [[expected_result, "22.61"]]]], result)


class ClassicalPSHABasedTestCase(unittest.TestCase, helpers.DbTestCase):

    def setUp(self):
        self.block_id = 7
        self.job = self.setup_classic_job()
        self.job_id = self.job.id

    def tearDown(self):
        if self.job:
            self.teardown_job(self.job)

    def _compute_risk_classical_psha_setup(self):
        SITE = shapes.Site(1.0, 1.0)
        # deletes all keys from kvs
        kvs.get_client().flushall()

        # at the moment the hazard part doesn't do exp on the 'x'
        # so it's done on the risk part. To adapt the calculation
        # we do the reverse of the exp, i.e. log(x)
        self.hazard_curve = [
            (SITE,
             {'IMLValues': [0.001, 0.080, 0.170, 0.260, 0.360,
                            0.550, 0.700],
              'PoEValues': [0.99, 0.96, 0.89, 0.82, 0.70, 0.40, 0.01],
              'statistics': 'mean'})]

        # Vitor provided this Vulnerability Function
        imls_1 = [0.03, 0.04, 0.07, 0.1, 0.12, 0.22, 0.37, 0.52]
        loss_ratios_1 = [0.001, 0.022, 0.051, 0.08, 0.1, 0.2, 0.405, 0.700]
        covs_1 = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        self.vuln_function = vulnerability_function.VulnerabilityFunction(
            imls_1, loss_ratios_1, covs_1, "LN")

        imls_2 = [0.1, 0.2, 0.4, 0.6]
        loss_ratios_2 = [0.05, 0.08, 0.2, 0.4]
        covs_2 = [0.5, 0.3, 0.2, 0.1]
        self.vuln_function_2 = vulnerability_function.VulnerabilityFunction(
            imls_2, loss_ratios_2, covs_2, "LN")

        self.asset_1 = {"taxonomy": "ID", "assetValue": 124.27}

        self.region = shapes.RegionConstraint.from_simple(
                (0.0, 0.0), (2.0, 2.0))

        block = Block(self.job_id, self.block_id, (SITE, ))
        block.to_kvs()

        writer = hazard.HazardCurveDBWriter('test_path.xml', self.job_id)
        writer.serialize(self.hazard_curve)

        kvs.set_value_json_encoded(
                kvs.tokens.vuln_key(self.job_id),
                {"ID": self.vuln_function.to_json()})
        kvs.set_value_json_encoded(
                kvs.tokens.vuln_key(self.job_id, retrofitted=True),
                {"ID": self.vuln_function.to_json()})

    def test_compute_risk_in_the_classical_psha_calculator(self):
        """
            tests ClassicalRiskCalculator.compute_risk by retrieving
            all the loss curves in the kvs and checks their presence
        """
        helpers.delete_profile(self.job)
        cls_risk_cfg = helpers.demo_file(
            'classical_psha_based_risk/config.gem')
        job_profile, params, sections = engine.import_job_profile(
            cls_risk_cfg, self.job)

        # We need to adjust a few of the parameters for this test:
        params['REGION_VERTEX'] = '0.0, 0.0, 0.0, 2.0, 2.0, 2.0, 2.0, 0.0'
        job_profile.region = GEOSGeometry(shapes.polygon_ewkt_from_coords(
            params['REGION_VERTEX']))
        job_profile.save()

        job_ctxt = engine.JobContext(
            params, self.job_id, sections=sections, oq_job_profile=job_profile)

        self._compute_risk_classical_psha_setup()

        calculator = classical_core.ClassicalRiskCalculator(job_ctxt)
        calculator.vuln_curves = {"ID": self.vuln_function}

        block = Block.from_kvs(self.job_id, self.block_id)

        # computes the loss curves and puts them in kvs
        calculator.compute_risk(self.block_id)

        for point in block.grid(job_ctxt.region):
            assets = BaseRiskCalculator.assets_for_cell(
                self.job_id, point.site)
            for asset in assets:
                loss_ratio_key = kvs.tokens.loss_ratio_key(
                    self.job_id, point.row, point.column, asset.asset_ref)

                self.assertTrue(kvs.get_client().get(loss_ratio_key))

                loss_key = kvs.tokens.loss_curve_key(
                    self.job_id, point.row, point.column, asset.asset_ref)

                self.assertTrue(kvs.get_client().get(loss_key))

    def test_compute_bcr_in_the_classical_psha_calculator(self):
        self._compute_risk_classical_psha_setup()
        helpers.delete_profile(self.job)
        bcr_config = helpers.demo_file('benefit_cost_ratio/config.gem')
        job_profile, params, sections = engine.import_job_profile(
            bcr_config, self.job)

        # We need to adjust a few of the parameters for this test:
        job_profile.imls = [
            0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527,
            0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778]
        params['ASSET_LIFE_EXPECTANCY'] = '50'
        job_profile.asset_life_expectancy = 50
        params['REGION_VERTEX'] = '0.0, 0.0, 0.0, 2.0, 2.0, 2.0, 2.0, 0.0'
        job_profile.region = GEOSGeometry(shapes.polygon_ewkt_from_coords(
            params['REGION_VERTEX']))
        job_profile.save()

        job_ctxt = engine.JobContext(
            params, self.job_id, sections=sections, oq_job_profile=job_profile)

        calculator = classical_core.ClassicalRiskCalculator(job_ctxt)

        [input] = models.inputs4job(self.job.id, input_type="exposure")
        emdl = input.model()
        if not emdl:
            emdl = models.ExposureModel(
                owner=self.job.owner, input=input,
                description="c-psha test exposure model",
                category="c-psha power plants", stco_unit="watt",
                stco_type="aggregated", reco_unit="joule",
                reco_type="aggregated")
            emdl.save()

        assets = emdl.exposuredata_set.filter(asset_ref="rubcr")
        if not assets:
            asset = models.ExposureData(exposure_model=emdl, taxonomy="ID",
                                        asset_ref="rubcr", stco=1, reco=123.45,
                                        site=GEOSGeometry("POINT(1.0 1.0)"))
            asset.save()

        Block.from_kvs(self.job_id, self.block_id)
        calculator.compute_risk(self.block_id)

        result_key = kvs.tokens.bcr_block_key(self.job_id, self.block_id)
        res = kvs.get_value_json_decoded(result_key)
        expected_result = {'bcr': 0.0, 'eal_original': 0.003032,
                           'eal_retrofitted': 0.003032}

        helpers.assertDeepAlmostEqual(
            self, res, [[[1, 1], [[expected_result, "rubcr"]]]])


class RiskJobGeneralTestCase(unittest.TestCase):
    def _make_job(self, params):
        self.job = helpers.create_job(params, base_path=".")
        self.job_id = self.job.job_id
        self.job.to_kvs()

    def _prepare_bcr_result(self):
        self.job.blocks_keys = [19, 20]
        kvs.set_value_json_encoded(kvs.tokens.bcr_block_key(self.job_id, 19), [
            ((-1.1, 19.0), [
                ({'bcr': 35.1, 'eal_original': 12.34, 'eal_retrofitted': 4},
                 'assetID-191'),
                ({'bcr': 35.2, 'eal_original': 2.5, 'eal_retrofitted': 2.2},
                 'assetID-192'),
            ])
        ])
        kvs.set_value_json_encoded(kvs.tokens.bcr_block_key(self.job_id, 20), [
            ((2.3, 20.0), [
                ({'bcr': 35.1, 'eal_original': 1.23, 'eal_retrofitted': 0.3},
                 'assetID-201'),
                ({'bcr': 35.2, 'eal_original': 4, 'eal_retrofitted': 0.4},
                 'assetID-202'),
            ])
        ])

    def test_asset_bcr_per_site(self):
        self._make_job({})
        self._prepare_bcr_result()

        job = BaseRiskCalculator(self.job)

        bcr_per_site = job.asset_bcr_per_site()
        self.assertEqual(bcr_per_site, [
            (shapes.Site(-1.1, 19.0), [
                [{u'bcr': 35.1, 'eal_original': 12.34, 'eal_retrofitted': 4},
                 u'assetID-191'],
                [{u'bcr': 35.2, 'eal_original': 2.5, 'eal_retrofitted': 2.2},
                 u'assetID-192']
            ]),
            (shapes.Site(2.3, 20.0), [
                [{u'bcr': 35.1, 'eal_original': 1.23, 'eal_retrofitted': 0.3},
                 u'assetID-201'],
                [{u'bcr': 35.2, 'eal_original': 4, 'eal_retrofitted': 0.4},
                 u'assetID-202']
            ])
        ])

    def test_write_output_bcr(self):
        self._make_job({})
        self._prepare_bcr_result()

        job = ProbabilisticRiskCalculator(self.job)

        expected_result = """\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.3"
      gml:id="undefined">
  <riskResult gml:id="undefined">
    <benefitCostRatioMap gml:id="undefined" endBranchLabel="undefined"
                         lossCategory="undefined" unit="undefined"
                         interestRate="0.12" assetLifeExpectancy="50">
      <BCRNode gml:id="mn_1">
        <site>
          <gml:Point srsName="epsg:4326">
            <gml:pos>-1.1 19.0</gml:pos>
          </gml:Point>
        </site>
        <benefitCostRatioValue assetRef="assetID-191">
          <expectedAnnualLossOriginal>12.34</expectedAnnualLossOriginal>
          <expectedAnnualLossRetrofitted>4</expectedAnnualLossRetrofitted>
          <benefitCostRatio>35.1</benefitCostRatio>
        </benefitCostRatioValue>
        <benefitCostRatioValue assetRef="assetID-192">
          <expectedAnnualLossOriginal>2.5</expectedAnnualLossOriginal>
          <expectedAnnualLossRetrofitted>2.2</expectedAnnualLossRetrofitted>
          <benefitCostRatio>35.2</benefitCostRatio>
        </benefitCostRatioValue>
      </BCRNode>
      <BCRNode gml:id="mn_2">
        <site>
          <gml:Point srsName="epsg:4326">
            <gml:pos>2.3 20.0</gml:pos>
          </gml:Point>
        </site>
        <benefitCostRatioValue assetRef="assetID-201">
          <expectedAnnualLossOriginal>1.23</expectedAnnualLossOriginal>
          <expectedAnnualLossRetrofitted>0.3</expectedAnnualLossRetrofitted>
          <benefitCostRatio>35.1</benefitCostRatio>
        </benefitCostRatioValue>
        <benefitCostRatioValue assetRef="assetID-202">
          <expectedAnnualLossOriginal>4</expectedAnnualLossOriginal>
          <expectedAnnualLossRetrofitted>0.4</expectedAnnualLossRetrofitted>
          <benefitCostRatio>35.2</benefitCostRatio>
        </benefitCostRatioValue>
      </BCRNode>
    </benefitCostRatioMap>
  </riskResult>
</nrml>"""

        output_dir = tempfile.mkdtemp()
        try:
            job.job_ctxt.params = {'OUTPUT_DIR': output_dir,
                                       'INTEREST_RATE': '0.12',
                                       'ASSET_LIFE_EXPECTANCY': '50'}
            job.job_ctxt._base_path = '.'

            resultfile = os.path.join(output_dir, 'bcr-map.xml')

            try:
                job.write_output_bcr()
                result = open(resultfile).read()
            finally:
                if os.path.exists(resultfile):
                    os.remove(resultfile)
        finally:
            os.rmdir(output_dir)

        result = StringIO(result)
        expected_result = StringIO(expected_result)

        events1 = [(elem.tag, elem.attrib, elem.text)
                   for (_, elem) in etree.iterparse(result)]
        events2 = [(elem.tag, elem.attrib, elem.text)
                   for (_, elem) in etree.iterparse(expected_result)]
        self.assertEqual(events1, events2)
