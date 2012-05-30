# -*- coding: utf-8 -*-

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


"""
Unit tests for hazard computations with the hazard engine.
Includes:

- hazard curves (with mean and quantile)
- hazard maps (only mean and quantile)
"""

import json
import numpy
import os
import unittest

from openquake import engine
from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake import xml
from openquake.calculators.hazard import CALCULATORS
from openquake.calculators.hazard import general as hazard_general
from openquake.calculators.hazard.classical import core as classical
from openquake.engine import JobContext
from openquake.job import params as job_params
from openquake.job.config import HazardMandatoryParamsValidator
from openquake.job.config import PARAMS
from openquake.kvs import tokens
from openquake.nrml.utils import nrml_schema_file

from tests.utils import helpers

LOG = logs.LOG

MEAN_GROUND_INTENSITY = (
    '{"site":"+35.0000 +35.0000", "intensity": 1.9249e+00,'
    '"site":"+35.0500 +35.0000", "intensity": 1.9623e+00,'
    '"site":"+35.1000 +35.0000", "intensity": 2.0320e+00,'
    '"site":"+35.1500 +35.0000", "intensity": 2.0594e+00}')

TEST_JOB_FILE = helpers.testdata_path('simplecase/config.gem')

NRML_SCHEMA_PATH = nrml_schema_file()

SIMPLE_FAULT_SRC_MODEL_LT = helpers.demo_file(
    'simple_fault_demo_hazard/source_model_logic_tree.xml')
SIMPLE_FAULT_GMPE_LT = helpers.demo_file(
    'simple_fault_demo_hazard/gmpe_logic_tree.xml')
SIMPLE_FAULT_BASE_PATH = os.path.abspath(
    helpers.demo_file('simple_fault_demo_hazard'))


def get_pattern(regexp):
    """Get all the values whose keys satisfy the given regexp.

    Return an empty list if there are no keys satisfying the given regxep.
    """

    values = []

    keys = kvs.get_client().keys(regexp)

    if keys:
        values = kvs.get_client().mget(keys)

    return values


class HazardEngineTestCase(unittest.TestCase):
    """The Hazard Engine is a JPype-based wrapper around OpenSHA-lite.
    Most data returned from the engine is via the KVS."""

    def setUp(self):
        self.generated_files = []
        self.kvs_client = kvs.get_client()

    def tearDown(self):
        for cfg in self.generated_files:
            try:
                os.remove(cfg)
            except OSError:
                pass

    def test_generate_hazard_curves_using_classical_psha(self):

        def verify_realization_haz_curves_stored_to_kvs(the_job, keys):
            """ This just tests to make sure there something in the KVS
            for each key in given list of keys. This does NOT test the
            actual results. """
            # TODO (LB): At some point we need to test the actual
            # results to verify they are correct

            realizations = int(
                the_job.params['NUMBER_OF_LOGIC_TREE_SAMPLES'])

            for realization in xrange(0, realizations):
                for site in the_job.sites_to_compute():
                    key = tokens.hazard_curve_poes_key(
                        the_job.job_id, realization, site)
                    self.assertTrue(key in keys, "Missing key %s" % key)

        def verify_mean_haz_curves_stored_to_kvs(the_job, keys):
            """ Make sure that the keys and non-empty values for mean
            hazard curves have been written to KVS."""

            if the_job.params['COMPUTE_MEAN_HAZARD_CURVE'].lower() == 'true':

                LOG.debug("verifying KVS entries for mean hazard curves")
                for site in the_job.sites_to_compute():
                    key = tokens.mean_hazard_curve_key(the_job.job_id, site)
                    self.assertTrue(key in keys, "Missing key %s" % key)

        def verify_mean_haz_maps_stored_to_kvs(the_job, calculator, keys):
            """ Make sure that the keys and non-empty values for mean
            hazard maps have been written to KVS."""

            if (the_job.params[hazard_general.POES_PARAM_NAME] != '' and
                the_job.params['COMPUTE_MEAN_HAZARD_CURVE'].lower() == \
                'true'):

                LOG.debug("verifying KVS entries for mean hazard maps")

                for poe in calculator.poes_hazard_maps:
                    for site in the_job.sites_to_compute():
                        key = tokens.mean_hazard_map_key(
                            the_job.job_id, site, poe)
                        self.assertTrue(key in keys, "Missing key %s" % key)

        def verify_quantile_haz_curves_stored_to_kvs(the_job, calculator,
                                                     keys):
            """ Make sure that the keys and non-empty values for quantile
            hazard curves have been written to KVS."""

            quantiles = calculator.quantile_levels

            LOG.debug("verifying KVS entries for quantile hazard curves, "\
                "%s quantile values" % len(quantiles))

            for quantile in quantiles:
                for site in the_job.sites_to_compute():
                    key = tokens.quantile_hazard_curve_key(
                        the_job.job_id, site, quantile)
                    self.assertTrue(key in keys, "Missing key %s" % key)

        def verify_quantile_haz_maps_stored_to_kvs(the_job, calculator, keys):
            """ Make sure that the keys and non-empty values for quantile
            hazard maps have been written to KVS."""

            quantiles = calculator.quantile_levels

            if (the_job.params[hazard_general.POES_PARAM_NAME] != '' and
                len(quantiles) > 0):

                poes = calculator.poes_hazard_maps

                LOG.debug("verifying KVS entries for quantile hazard maps, "\
                    "%s quantile values, %s PoEs" % (
                    len(quantiles), len(poes)))

                for quantile in quantiles:
                    for poe in poes:
                        for site in the_job.sites_to_compute():
                            key = tokens.quantile_hazard_map_key(
                                the_job.job_id, site, poe, quantile)
                            self.assertTrue(
                                key in keys, "Missing key %s" % key)

        def verify_realization_haz_curves_stored_to_nrml(the_job, calculator):
            """Tests that a NRML file has been written for each realization,
            and that this file validates against the NRML schema.
            Does NOT test if results in NRML file are correct.
            """
            realizations = int(
                the_job.params['NUMBER_OF_LOGIC_TREE_SAMPLES'])
            for realization in xrange(0, realizations):

                nrml_path = os.path.join(
                    "demos/classical_psha_simple/computed_output",
                    calculator.hazard_curve_filename(realization))

                LOG.debug("validating NRML file %s" % nrml_path)

                self.assertTrue(xml.validates_against_xml_schema(
                    nrml_path, NRML_SCHEMA_PATH),
                    "NRML instance file %s does not validate against schema" \
                    % nrml_path)

        def verify_mean_haz_curves_stored_to_nrml(the_job, calculator):
            """Tests that a mean hazard curve NRML file has been written,
            and that this file validates against the NRML schema.
            Does NOT test if results in NRML file are correct.
            """

            if the_job.params['COMPUTE_MEAN_HAZARD_CURVE'].lower() == 'true':
                nrml_path = os.path.join(
                    "demos/classical_psha_simple/computed_output",
                    calculator.mean_hazard_curve_filename())

                LOG.debug("validating NRML file %s" % nrml_path)

                self.assertTrue(xml.validates_against_xml_schema(
                    nrml_path, NRML_SCHEMA_PATH),
                    "NRML instance file %s does not validate against schema" \
                    % nrml_path)

        def verify_mean_haz_maps_stored_to_nrml(the_job):
            """Tests that a mean hazard map NRML file has been written,
            and that this file validates against the NRML schema.
            Does NOT test if results in NRML file are correct.
            """
            if (the_job.params[hazard_general.POES_PARAM_NAME] != '' and
                the_job.params['COMPUTE_MEAN_HAZARD_CURVE'].lower() == \
                'true'):

                for poe in calculator.poes_hazard_maps:
                    nrml_path = os.path.join(
                        "demos/classical_psha_simple/computed_output",
                        calculator.mean_hazard_map_filename(poe))

                    LOG.debug("validating NRML file for mean hazard map %s" \
                        % nrml_path)

                    self.assertTrue(xml.validates_against_xml_schema(
                        nrml_path, NRML_SCHEMA_PATH),
                        "NRML instance file %s does not validate against "\
                        "schema" % nrml_path)

        def verify_quantile_haz_curves_stored_to_nrml(the_job, calculator):
            """Tests that quantile hazard curve NRML files have been written,
            and that these file validate against the NRML schema.
            Does NOT test if results in NRML files are correct.
            """

            for quantile in calculator.quantile_levels:

                nrml_path = os.path.join(
                    "demos/classical_psha_simple/computed_output",
                    calculator.quantile_hazard_curve_filename(quantile))

                LOG.debug("validating NRML file for quantile hazard curve: "\
                    "%s" % nrml_path)

                self.assertTrue(xml.validates_against_xml_schema(
                    nrml_path, NRML_SCHEMA_PATH),
                    "NRML instance file %s does not validate against schema" \
                    % nrml_path)

        def verify_quantile_haz_maps_stored_to_nrml(the_job, calculator):
            """Tests that quantile hazard map NRML files have been written,
            and that these file validate against the NRML schema.
            Does NOT test if results in NRML files are correct.
            """

            quantiles = calculator.quantile_levels

            if (the_job.params[hazard_general.POES_PARAM_NAME] != '' and
                len(quantiles) > 0):

                for poe in calculator.poes_hazard_maps:
                    for quantile in quantiles:
                        nrml_path = os.path.join(
                            "demos/classical_psha_simple/computed_output",
                            calculator.quantile_hazard_map_filename(quantile,
                                                                   poe))

                        LOG.debug("validating NRML file for quantile hazard "\
                            "map: %s" % nrml_path)

                        self.assertTrue(xml.validates_against_xml_schema(
                            nrml_path, NRML_SCHEMA_PATH),
                            "NRML instance file %s does not validate against "\
                            "schema" % nrml_path)

        base_path = helpers.testdata_path("classical_psha_simple")
        path = helpers.testdata_path("classical_psha_simple/config.gem")
        job = engine.prepare_job()
        job_profile, params, sections = engine.import_job_profile(path, job)

        the_job = JobContext(
            params, job.id, sections=sections, base_path=base_path,
            serialize_results_to=['db', 'xml'], oq_job_profile=job_profile,
            oq_job=job)
        the_job.to_kvs()

        calc_mode = job_profile.calc_mode
        calculator = CALCULATORS[calc_mode](the_job)

        used_keys = []
        calculator.execute(used_keys)

        verify_realization_haz_curves_stored_to_kvs(the_job, used_keys)
        verify_realization_haz_curves_stored_to_nrml(the_job, calculator)

        # hazard curves: check results of mean and quantile computation
        verify_mean_haz_curves_stored_to_kvs(the_job, used_keys)
        verify_quantile_haz_curves_stored_to_kvs(the_job, calculator,
                                                 used_keys)

        verify_mean_haz_curves_stored_to_nrml(the_job, calculator)
        verify_quantile_haz_curves_stored_to_nrml(the_job, calculator)

        # hazard maps: check results of mean and quantile computation
        verify_mean_haz_maps_stored_to_kvs(the_job, calculator, used_keys)
        verify_quantile_haz_maps_stored_to_kvs(the_job, calculator, used_keys)

        verify_mean_haz_maps_stored_to_nrml(the_job)
        verify_quantile_haz_maps_stored_to_nrml(the_job, calculator)

    def test_compute_mgm_intensity(self):
        results = []
        block_id = 8801
        site = "Testville,TestLand"

        mgm_intensity = json.JSONDecoder().decode(MEAN_GROUND_INTENSITY)

        job_ids = [helpers.job_from_file(TEST_JOB_FILE).job_id
                   for _ in xrange(4)]
        for job_id in job_ids:
            mgm_key = tokens.mgm_key(job_id, block_id, site)
            self.kvs_client.set(mgm_key, MEAN_GROUND_INTENSITY)

            results.append(classical.compute_mgm_intensity.apply_async(
                args=[job_id, block_id, site]))

        helpers.wait_for_celery_tasks(results)

        for result in results:
            self.assertEqual(mgm_intensity, result.get())


class MeanHazardCurveComputationTestCase(unittest.TestCase):

    def setUp(self):
        self.params = {}
        self.job = helpers.create_job(self.params)
        self.job_id = self.job.job_id

        self.expected_mean_curve = numpy.array([9.8542200e-01, 9.8196600e-01,
                9.5842000e-01, 9.2639600e-01, 8.6713000e-01, 7.7081800e-01,
                6.3448600e-01, 4.7256800e-01, 3.3523400e-01, 3.1255000e-01,
                1.7832000e-01, 9.0883400e-02, 4.2189200e-02, 1.7874200e-02,
                6.7449200e-03, 2.1658200e-03, 5.3878600e-04, 9.4369400e-05,
                8.9830380e-06])

        self.empty_curve = []

        # deleting server side cached data
        kvs.get_client().flushall()

    def test_process_the_curves_for_a_single_site(self):
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), self.empty_curve)

        self._run([shapes.Site(2.0, 5.0)], 1)

        self._has_computed_mean_curve_for_site(shapes.Site(2.0, 5.0))

    def test_process_the_curves_for_multiple_sites(self):
        sites = [shapes.Site(1.5, 1.0), shapes.Site(2.0, 1.0),
                 shapes.Site(1.5, 1.5), shapes.Site(2.0, 1.5)]

        self._store_hazard_curve_at(sites[0], self.empty_curve)
        self._store_hazard_curve_at(sites[1], self.empty_curve)
        self._store_hazard_curve_at(sites[2], self.empty_curve)
        self._store_hazard_curve_at(sites[3], self.empty_curve)

        self._run(sites, 1)

        self._has_computed_mean_curve_for_site(sites[0])
        self._has_computed_mean_curve_for_site(sites[1])
        self._has_computed_mean_curve_for_site(sites[2])
        self._has_computed_mean_curve_for_site(sites[3])

    def test_computes_the_mean_curve(self):
        hazard_curve_1 = numpy.array([9.8161000e-01, 9.7837000e-01,
                9.5579000e-01, 9.2555000e-01, 8.7052000e-01, 7.8214000e-01,
                6.5708000e-01, 5.0526000e-01, 3.7044000e-01, 3.4740000e-01,
                2.0502000e-01, 1.0506000e-01, 4.6531000e-02, 1.7548000e-02,
                5.4791000e-03, 1.3377000e-03, 2.2489000e-04, 2.2345000e-05,
                4.2696000e-07])

        hazard_curve_2 = numpy.array([9.7309000e-01, 9.6857000e-01,
                9.3853000e-01, 9.0089000e-01, 8.3673000e-01, 7.4057000e-01,
                6.1272000e-01, 4.6467000e-01, 3.3694000e-01, 3.1536000e-01,
                1.8340000e-01, 9.2412000e-02, 4.0202000e-02, 1.4900000e-02,
                4.5924000e-03, 1.1126000e-03, 1.8647000e-04, 1.8882000e-05,
                4.7123000e-07])

        hazard_curve_3 = numpy.array([9.9178000e-01, 9.8892000e-01,
                9.6903000e-01, 9.4030000e-01, 8.8405000e-01, 7.8782000e-01,
                6.4627000e-01, 4.7537000e-01, 3.3168000e-01, 3.0827000e-01,
                1.7279000e-01, 8.8360000e-02, 4.2766000e-02, 1.9643000e-02,
                8.1923000e-03, 2.9157000e-03, 7.9955000e-04, 1.5233000e-04,
                1.5582000e-05])

        hazard_curve_4 = numpy.array([9.8885000e-01, 9.8505000e-01,
                9.5972000e-01, 9.2494000e-01, 8.6030000e-01, 7.5574000e-01,
                6.1009000e-01, 4.4217000e-01, 3.0543000e-01, 2.8345000e-01,
                1.5760000e-01, 8.0225000e-02, 3.8681000e-02, 1.7637000e-02,
                7.2685000e-03, 2.5474000e-03, 6.8347000e-04, 1.2596000e-04,
                1.2853000e-05])

        hazard_curve_5 = numpy.array([9.9178000e-01, 9.8892000e-01,
                9.6903000e-01, 9.4030000e-01, 8.8405000e-01, 7.8782000e-01,
                6.4627000e-01, 4.7537000e-01, 3.3168000e-01, 3.0827000e-01,
                1.7279000e-01, 8.8360000e-02, 4.2766000e-02, 1.9643000e-02,
                8.1923000e-03, 2.9157000e-03, 7.9955000e-04, 1.5233000e-04,
                1.5582000e-05])

        mean_hazard_curve = hazard_general.compute_mean_curve([
                hazard_curve_1, hazard_curve_2, hazard_curve_3,
                hazard_curve_4, hazard_curve_5])

        self.assertTrue(numpy.allclose(
                self.expected_mean_curve, mean_hazard_curve))

    def test_an_empty_hazard_curve_produces_an_empty_mean_curve(self):
        hazard_curve = []
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve)

        self._run([shapes.Site(2.0, 5.0)], 1)

        result = kvs.get_value_json_decoded(
                kvs.tokens.mean_hazard_curve_key(
                self.job_id, shapes.Site(2.0, 5.0)))

        # no values
        self.assertTrue(numpy.allclose([], numpy.array(result)))

    def test_reads_and_stores_the_mean_curve_in_kvs(self):
        site = shapes.Site(2.0, 5.0)

        hazard_curve_1 = [
            0.98161, 0.97837, 0.95579, 0.92555, 0.87052, 0.78214, 0.65708,
            0.50526, 0.37044, 0.3474, 0.20502, 0.10506, 0.046531, 0.017548,
            0.0054791, 0.0013377, 0.00022489, 2.2345e-05, 4.2696e-07, ]
        hazard_curve_2 = [
            0.97309, 0.96857, 0.93853, 0.90089, 0.83673, 0.74057, 0.61272,
            0.46467, 0.33694, 0.31536, 0.1834, 0.092412, 0.040202, 0.0149,
            0.0045924, 0.0011126, 0.00018647, 1.8882e-05, 4.7123e-07, ]
        hazard_curve_3 = [
            0.99178, 0.98892, 0.96903, 0.9403, 0.88405, 0.78782, 0.64627,
            0.47537, 0.33168, 0.30827, 0.17279, 0.08836, 0.042766, 0.019643,
            0.0081923, 0.0029157, 0.00079955, 0.00015233, 1.5582e-05, ]
        hazard_curve_4 = [
            0.98885, 0.98505, 0.95972, 0.92494, 0.8603, 0.75574, 0.61009,
            0.44217, 0.30543, 0.28345, 0.1576, 0.080225, 0.038681, 0.017637,
            0.0072685, 0.0025474, 0.00068347, 0.00012596, 1.2853e-05, ]
        hazard_curve_5 = [
            0.99178, 0.98892, 0.96903, 0.9403, 0.88405, 0.78782, 0.64627,
            0.47537, 0.33168, 0.30827, 0.17279, 0.08836, 0.042766, 0.019643,
            0.0081923, 0.0029157, 0.00079955, 0.00015233, 1.5582e-05, ]

        self._store_hazard_curve_at(site, hazard_curve_1, 0)
        self._store_hazard_curve_at(site, hazard_curve_2, 1)
        self._store_hazard_curve_at(site, hazard_curve_3, 2)
        self._store_hazard_curve_at(site, hazard_curve_4, 3)
        self._store_hazard_curve_at(site, hazard_curve_5, 4)

        self._run([site], 5)

        result = kvs.get_value_json_decoded(
                kvs.tokens.mean_hazard_curve_key(self.job_id, site))

        # values are correct
        self.assertTrue(numpy.allclose(self.expected_mean_curve, result))

    def _run(self, sites, realizations):
        hazard_general.compute_mean_hazard_curves(
                self.job.job_id, sites, realizations)

    def _store_hazard_curve_at(self, site, curve, realization=0):
        kvs.set_value_json_encoded(
                kvs.tokens.hazard_curve_poes_key(self.job_id, realization,
                site), curve)

    def _has_computed_mean_curve_for_site(self, site):
        self.assertTrue(kvs.get_client().get(kvs.tokens.mean_hazard_curve_key(
                self.job_id, site)) != None)


class QuantileHazardCurveComputationTestCase(unittest.TestCase):

    def setUp(self):
        self.params = dict(
            CALCULATION_MODE='Hazard',
            SOURCE_MODEL_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_SRC_MODEL_LT,
            GMPE_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_GMPE_LT,
            BASE_PATH=SIMPLE_FAULT_BASE_PATH)

        self.job_ctxt = helpers.create_job(self.params)
        self.calculator = classical.ClassicalHazardCalculator(self.job_ctxt)
        self.job_id = self.job_ctxt.job_id

        self.expected_curve = numpy.array([9.9178000e-01, 9.8892000e-01,
                9.6903000e-01, 9.4030000e-01, 8.8405000e-01, 7.8782000e-01,
                6.4897250e-01, 4.8284250e-01, 3.4531500e-01, 3.2337000e-01,
                1.8880500e-01, 9.5574000e-02, 4.3707250e-02, 1.9643000e-02,
                8.1923000e-03, 2.9157000e-03, 7.9955000e-04, 1.5233000e-04,
                1.5582000e-05])

        # deleting server side cached data
        kvs.get_client().flushall()

    def _store_dummy_hazard_curve(self, site):
        hazard_curve = [0.98161, 0.97837]

        self._store_hazard_curve_at(site, hazard_curve, 0)

    def test_no_quantiles_when_no_parameter_specified(self):
        self.assertEqual([], self.calculator.quantile_levels)

    def test_no_computation_when_the_parameter_is_empty(self):
        self._run([], 1, [])

        self._no_stored_values_for("%s" %
                kvs.tokens.QUANTILE_HAZARD_CURVE_KEY_TOKEN)

    def test_computes_all_the_levels_specified(self):
        self._store_dummy_hazard_curve(shapes.Site(2.0, 5.0))

        self._run([shapes.Site(2.0, 5.0)], 1, [0.25, 0.50, 0.75])

        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.25)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.75)

    def test_computes_just_the_quantiles_in_range(self):
        self.job_ctxt.params[hazard_general.QUANTILE_PARAM_NAME] = (
            '-0.33 0.00 0.25 0.50 0.75 1.00 1.10')

        self.assertEqual([0.00, 0.25, 0.50, 0.75, 1.00],
            self.calculator.quantile_levels)

    def test_just_numeric_values_are_allowed(self):
        self.job_ctxt.params[hazard_general.QUANTILE_PARAM_NAME] = (
            '-0.33 0.00 XYZ 0.50 ;;; 1.00 BBB')

        self.assertEqual([0.00, 0.50, 1.00], self.calculator.quantile_levels)

    def test_accepts_also_signs(self):
        self.job_ctxt.params[hazard_general.QUANTILE_PARAM_NAME] = (
            '-0.33 +0.0 XYZ +0.5 +1.00')

        self.assertEqual([0.00, 0.50, 1.00], self.calculator.quantile_levels)

    def test_process_all_the_sites_given(self):
        self._store_dummy_hazard_curve(shapes.Site(1.5, 1.0))
        self._store_dummy_hazard_curve(shapes.Site(2.0, 1.0))
        self._store_dummy_hazard_curve(shapes.Site(1.5, 1.5))
        self._store_dummy_hazard_curve(shapes.Site(2.0, 1.5))

        self._run([shapes.Site(1.5, 1.0), shapes.Site(2.0, 1.0),
                   shapes.Site(1.5, 1.5), shapes.Site(2.0, 1.5)],
                  1, [0.25, 0.50])

        self._has_computed_quantile_for_site(shapes.Site(1.5, 1.0), 0.25)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 1.0), 0.25)
        self._has_computed_quantile_for_site(shapes.Site(1.5, 1.5), 0.25)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 1.5), 0.25)

        self._has_computed_quantile_for_site(shapes.Site(1.5, 1.0), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 1.0), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(1.5, 1.5), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 1.5), 0.50)

    def test_computes_the_quantile_curve(self):
        hazard_curve_1 = numpy.array([9.8161000e-01, 9.7837000e-01,
                9.5579000e-01, 9.2555000e-01, 8.7052000e-01, 7.8214000e-01,
                6.5708000e-01, 5.0526000e-01, 3.7044000e-01, 3.4740000e-01,
                2.0502000e-01, 1.0506000e-01, 4.6531000e-02, 1.7548000e-02,
                5.4791000e-03, 1.3377000e-03, 2.2489000e-04, 2.2345000e-05,
                4.2696000e-07])

        hazard_curve_2 = numpy.array([9.7309000e-01, 9.6857000e-01,
                9.3853000e-01, 9.0089000e-01, 8.3673000e-01, 7.4057000e-01,
                6.1272000e-01, 4.6467000e-01, 3.3694000e-01, 3.1536000e-01,
                1.8340000e-01, 9.2412000e-02, 4.0202000e-02, 1.4900000e-02,
                4.5924000e-03, 1.1126000e-03, 1.8647000e-04, 1.8882000e-05,
                4.7123000e-07])

        hazard_curve_3 = numpy.array([9.9178000e-01, 9.8892000e-01,
                9.6903000e-01, 9.4030000e-01, 8.8405000e-01, 7.8782000e-01,
                6.4627000e-01, 4.7537000e-01, 3.3168000e-01, 3.0827000e-01,
                1.7279000e-01, 8.8360000e-02, 4.2766000e-02, 1.9643000e-02,
                8.1923000e-03, 2.9157000e-03, 7.9955000e-04, 1.5233000e-04,
                1.5582000e-05])

        hazard_curve_4 = numpy.array([9.8885000e-01, 9.8505000e-01,
                9.5972000e-01, 9.2494000e-01, 8.6030000e-01, 7.5574000e-01,
                6.1009000e-01, 4.4217000e-01, 3.0543000e-01, 2.8345000e-01,
                1.5760000e-01, 8.0225000e-02, 3.8681000e-02, 1.7637000e-02,
                7.2685000e-03, 2.5474000e-03, 6.8347000e-04, 1.2596000e-04,
                1.2853000e-05])

        hazard_curve_5 = numpy.array([9.9178000e-01, 9.8892000e-01,
                9.6903000e-01, 9.4030000e-01, 8.8405000e-01, 7.8782000e-01,
                6.4627000e-01, 4.7537000e-01, 3.3168000e-01, 3.0827000e-01,
                1.7279000e-01, 8.8360000e-02, 4.2766000e-02, 1.9643000e-02,
                8.1923000e-03, 2.9157000e-03, 7.9955000e-04, 1.5233000e-04,
                1.5582000e-05])

        quantile_hazard_curve = hazard_general.compute_quantile_curve([
                hazard_curve_1, hazard_curve_2, hazard_curve_3,
                hazard_curve_4, hazard_curve_5], 0.75)

        # TODO (ac): Check if this tolerance is enough
        self.assertTrue(numpy.allclose(
                self.expected_curve, quantile_hazard_curve, atol=0.005))

    def test_an_empty_hazard_curve_produces_an_empty_quantile_curve(self):
        hazard_curve = []
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve)

        self._run([shapes.Site(2.0, 5.0)], 1, [0.75])

        result = kvs.get_value_json_decoded(
                kvs.tokens.quantile_hazard_curve_key(
                self.job_id, shapes.Site(2.0, 5.0), 0.75))

        # no values
        self.assertTrue(numpy.allclose([], numpy.array(result)))

    def test_reads_and_stores_the_quantile_curve_in_kvs(self):
        hazard_curve_1 = [
            0.98161, 0.97837, 0.95579, 0.92555, 0.87052, 0.78214, 0.65708,
            0.50526, 0.37044, 0.3474, 0.20502, 0.10506, 0.046531, 0.017548,
            0.0054791, 0.0013377, 0.00022489, 2.2345e-05, 4.2696e-07, ]
        hazard_curve_2 = [
            0.97309, 0.96857, 0.93853, 0.90089, 0.83673, 0.74057, 0.61272,
            0.46467, 0.33694, 0.31536, 0.1834, 0.092412, 0.040202, 0.0149,
            0.0045924, 0.0011126, 0.00018647, 1.8882e-05, 4.7123e-07, ]
        hazard_curve_3 = [
            0.99178, 0.98892, 0.96903, 0.9403, 0.88405, 0.78782, 0.64627,
            0.47537, 0.33168, 0.30827, 0.17279, 0.08836, 0.042766, 0.019643,
            0.0081923, 0.0029157, 0.00079955, 0.00015233, 1.5582e-05, ]
        hazard_curve_4 = [
            0.98885, 0.98505, 0.95972, 0.92494, 0.8603, 0.75574, 0.61009,
            0.44217, 0.30543, 0.28345, 0.1576, 0.080225, 0.038681, 0.017637,
            0.0072685, 0.0025474, 0.00068347, 0.00012596, 1.2853e-05, ]
        hazard_curve_5 = [
            0.99178, 0.98892, 0.96903, 0.9403, 0.88405, 0.78782, 0.64627,
            0.47537, 0.33168, 0.30827, 0.17279, 0.08836, 0.042766, 0.019643,
            0.0081923, 0.0029157, 0.00079955, 0.00015233, 1.5582e-05, ]

        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_1, 0)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_2, 1)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_3, 2)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_4, 3)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_5, 4)

        self._run([shapes.Site(2.0, 5.0)], 5, [0.75])

        result = kvs.get_value_json_decoded(
                kvs.tokens.quantile_hazard_curve_key(
                self.job_id, shapes.Site(2.0, 5.0), 0.75))

        # values are correct
        self.assertTrue(numpy.allclose(self.expected_curve, result,
                                       atol=0.005))

    def _run(self, sites, realizations, quantiles):
        hazard_general.compute_quantile_hazard_curves(
                self.job_ctxt.job_id, sites, realizations, quantiles)

    def _store_hazard_curve_at(self, site, curve, realization=0):
        kvs.set_value_json_encoded(
                kvs.tokens.hazard_curve_poes_key(self.job_id, realization,
                site), curve)

    def _no_stored_values_for(self, pattern):
        self.assertEqual([], get_pattern(pattern))

    def _has_computed_quantile_for_site(self, site, value):
        self.assertTrue(get_pattern(kvs.tokens.quantile_hazard_curve_key(
            self.job_id, site, value)))


class MeanQuantileHazardMapsComputationTestCase(unittest.TestCase):

    def setUp(self):
        self.params = dict(
            CALCULATION_MODE='Hazard',
            REFERENCE_VS30_VALUE=500,
            SOURCE_MODEL_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_SRC_MODEL_LT,
            GMPE_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_GMPE_LT,
            BASE_PATH=SIMPLE_FAULT_BASE_PATH)

        self.imls = [5.0000e-03, 7.0000e-03,
                1.3700e-02, 1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 2.0300e-01,
                2.8400e-01, 3.9700e-01, 5.5600e-01, 7.7800e-01, 1.0900e+00,
                1.5200e+00, 2.1300e+00]

        self.job_ctxt = helpers.create_job(self.params)
        self.calculator = classical.ClassicalHazardCalculator(self.job_ctxt)
        self.job_id = self.job_ctxt.job_id

        self.empty_mean_curve = []

        # deleting server side cached data
        kvs.get_client().flushall()

        mean_curve = [9.8728e-01, 9.8266e-01, 9.4957e-01,
                9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01, 3.6143e-01,
                2.4231e-01, 2.2452e-01, 1.2831e-01, 7.0352e-02, 3.6060e-02,
                1.6579e-02, 6.4213e-03, 2.0244e-03, 4.8605e-04, 8.1752e-05,
                7.3425e-06]

        self.site = shapes.Site(2.0, 5.0)
        self._store_curve_at(self.site, mean_curve)

    def test_no_poes_when_no_parameter_specified(self):
        self.assertEqual([], self.calculator.poes_hazard_maps)

    def test_no_computation_when_the_parameter_is_empty(self):
        self._run([])

        self._no_stored_values_for("%s" %
                kvs.tokens.MEAN_HAZARD_MAP_KEY_TOKEN)

    def test_computes_all_the_levels_specified(self):
        self._run([0.10, 0.20, 0.50])

        self._has_computed_IML_for_site(self.site, 0.10)
        self._has_computed_IML_for_site(self.site, 0.20)
        self._has_computed_IML_for_site(self.site, 0.50)

    def test_computes_the_iml(self):
        mean_curve = [9.8784e-01, 9.8405e-01, 9.5719e-01, 9.1955e-01,
                8.5019e-01, 7.4038e-01, 5.9153e-01, 4.2626e-01, 2.9755e-01,
                2.7731e-01, 1.6218e-01, 8.8035e-02, 4.3499e-02, 1.9065e-02,
                7.0442e-03, 2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]

        sites = [shapes.Site(2.0, 5.0), shapes.Site(3.0, 3.0)]

        self._store_curve_at(sites[1], mean_curve)

        self._run([0.10], sites)

        im_level = self._get_iml_at(sites[0], 0.10)

        self.assertTrue(numpy.allclose([1.6789e-01],
                numpy.array(im_level), atol=0.005))

        im_level = self._get_iml_at(sites[1], 0.10)

        self.assertTrue(numpy.allclose([1.9078e-01],
                numpy.array(im_level), atol=0.005))

    def test_when_poe_is_too_high_the_min_iml_is_taken(self):
        # highest value is 9.8728e-01
        self._run([0.99])

        im_level = self._get_iml_at(self.site, 0.99)

        self.assertTrue(numpy.allclose([5.0000e-03],
                numpy.array(im_level)))

    def test_when_poe_is_too_low_the_max_iml_is_taken(self):
        # lowest value is 7.3425e-06
        self._run([0.00])

        im_level = self._get_iml_at(self.site, 0.00)

        self.assertTrue(numpy.allclose([2.1300e+00],
                numpy.array(im_level)))

    def test_quantile_hazard_maps_computation(self):
        self.params[hazard_general.POES_PARAM_NAME] = "0.10"
        self.params[hazard_general.QUANTILE_PARAM_NAME] = "0.25 0.50 0.75"

        curve_1 = [9.8784e-01, 9.8405e-01, 9.5719e-01, 9.1955e-01,
                8.5019e-01, 7.4038e-01, 5.9153e-01, 4.2626e-01, 2.9755e-01,
                2.7731e-01, 1.6218e-01, 8.8035e-02, 4.3499e-02, 1.9065e-02,
                7.0442e-03, 2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]

        curve_2 = [9.8784e-01, 9.8405e-01, 9.5719e-01, 9.1955e-01,
                8.5019e-01, 7.4038e-01, 5.9153e-01, 4.2626e-01, 2.9755e-01,
                2.7731e-01, 1.6218e-01, 8.8035e-02, 4.3499e-02, 1.9065e-02,
                7.0442e-03, 2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]

        sites = [shapes.Site(3.0, 3.0), shapes.Site(3.5, 3.5)]

        # keys for sites[0]
        key_1 = kvs.tokens.quantile_hazard_curve_key(
                self.job_id, sites[0], 0.25)

        key_2 = kvs.tokens.quantile_hazard_curve_key(
                self.job_id, sites[0], 0.50)

        key_3 = kvs.tokens.quantile_hazard_curve_key(
                self.job_id, sites[0], 0.75)

        # keys for sites[1]
        key_4 = kvs.tokens.quantile_hazard_curve_key(
                self.job_id, sites[1], 0.25)

        key_5 = kvs.tokens.quantile_hazard_curve_key(
                self.job_id, sites[1], 0.50)

        key_6 = kvs.tokens.quantile_hazard_curve_key(
                self.job_id, sites[1], 0.75)

        # setting values in kvs
        kvs.set_value_json_encoded(key_1, curve_1)
        kvs.set_value_json_encoded(key_2, curve_1)
        kvs.set_value_json_encoded(key_3, curve_1)

        kvs.set_value_json_encoded(key_4, curve_2)
        kvs.set_value_json_encoded(key_5, curve_2)
        kvs.set_value_json_encoded(key_6, curve_2)

        hazard_general.compute_quantile_hazard_maps(
            self.job_ctxt.job_id, sites, [0.25, 0.50, 0.75], self.imls,
            [0.10])

        # asserting imls have been produced for all poes and quantiles
        self.assertTrue(kvs.get_client().get(
            kvs.tokens.quantile_hazard_map_key(
                self.job_id, sites[0], 0.10, 0.25)))

        self.assertTrue(kvs.get_client().get(
            kvs.tokens.quantile_hazard_map_key(
                self.job_id, sites[0], 0.10, 0.50)))

        self.assertTrue(kvs.get_client().get(
            kvs.tokens.quantile_hazard_map_key(
                self.job_id, sites[0], 0.10, 0.75)))

        self.assertTrue(kvs.get_client().get(
            kvs.tokens.quantile_hazard_map_key(
                self.job_id, sites[1], 0.10, 0.25)))

        self.assertTrue(kvs.get_client().get(
            kvs.tokens.quantile_hazard_map_key(
                self.job_id, sites[1], 0.10, 0.50)))

        self.assertTrue(kvs.get_client().get(
            kvs.tokens.quantile_hazard_map_key(
                self.job_id, sites[1], 0.10, 0.75)))

    def _get_iml_at(self, site, poe):
        return kvs.get_value_json_decoded(
                kvs.tokens.mean_hazard_map_key(self.job_id, site, poe))

    def _run(self, poes, sites=None):
        if sites is None:
            sites = [self.site]

        hazard_general.compute_mean_hazard_maps(self.job_ctxt.job_id, sites,
                                                self.imls, poes)

    def _no_stored_values_for(self, pattern):
        self.assertEqual([], get_pattern(pattern))

    def _store_curve_at(self, site, mean_curve):
        kvs.set_value_json_encoded(
                kvs.tokens.mean_hazard_curve_key(
                self.job_id, site), mean_curve)

    def _has_computed_IML_for_site(self, site, poe):
        self.assertTrue(kvs.get_client().get(kvs.tokens.mean_hazard_map_key(
            self.job_id, site, poe)))


class ParameterizeSitesTestCase(unittest.TestCase):
    """Tests relating to BaseHazardCalculator.parameterize_sites()."""

    def test_parameterize_sites_no_site_model(self):
        job_ctxt = helpers.prepare_job_context(
            helpers.demo_file('simple_fault_demo_hazard/config.gem')
        )

        calc = classical.ClassicalHazardCalculator(job_ctxt)

        jsites = calc.parameterize_sites(job_ctxt.sites_to_compute())

        # expected params:
        jp = job_ctxt.oq_job_profile

        exp_sadigh = job_params.REVERSE_ENUM_MAP[jp.sadigh_site_type]
        exp_vs30 = jp.reference_vs30_value
        exp_vs30_type = jp.vs30_type
        exp_z1pt0 = jp.depth_to_1pt_0km_per_sec
        exp_z2pt5 = jp.reference_depth_to_2pt5km_per_sec_param

        for jsite in jsites:
            self.assertEqual(
                exp_vs30, jsite.getParameter('Vs30').getValue().value
            )
            self.assertEqual(
                exp_vs30_type, jsite.getParameter('Vs30 Type').getValue()
            )
            self.assertEqual(
                exp_z1pt0,
                jsite.getParameter('Depth 1.0 km/sec').getValue().value
            )
            self.assertEqual(
                exp_z2pt5,
                jsite.getParameter('Depth 2.5 km/sec').getValue().value
            )
            self.assertEqual(
                exp_sadigh, jsite.getParameter('Sadigh Site Type').getValue()
            )

    def test_parameterize_sites_with_site_model(self):
        job_ctxt = helpers.prepare_job_context(
            helpers.demo_file(
                'simple_fault_demo_hazard/config_with_site_model.gem'
            )
        )

        calc = classical.ClassicalHazardCalculator(job_ctxt)
        calc.initialize()

        # This tests to ensure that the `initialize` implementation for this
        # calculator properly stores the site model in the DB.

        # NOTE: If this test ever breaks, it's probably because the
        # ClassicalHazardCalculator is no longer calling the `initalize` code
        # in its super class (BaseHazardCalculator).
        site_model = hazard_general.get_site_model(job_ctxt.oq_job.id)
        self.assertIsNotNone(site_model)

        set_params_patch = helpers.patch(
            'openquake.calculators.hazard.general.set_java_site_parameters'
        )
        closest_data_patch = helpers.patch(
            'openquake.calculators.hazard.general.get_closest_site_model_data'
        )
        sp_mock = set_params_patch.start()
        cd_mock = closest_data_patch.start()

        try:
            calc.parameterize_sites(job_ctxt.sites_to_compute())

            exp_call_count = len(job_ctxt.sites_to_compute())
            self.assertEqual(exp_call_count, sp_mock.call_count)
            self.assertEqual(exp_call_count, cd_mock.call_count)

        finally:
            # tear down the patches
            set_params_patch.stop()
            closest_data_patch.stop()


class IMLTestCase(unittest.TestCase):
    """
    Tests that every Intensity Measure Type
    declared in ``openquake.db.models.OqJobProfile.IMT_CHOICES``
    has a correct corresponding function
    in ``openquake.hazard.general.IML_SCALING`` mapping
    and is allowed to be the configuration parameter value
    for ``INTENSITY_MEASURE_TYPE``.
    """
    def test_scaling_definitions(self):
        from openquake.db.models import OqJobProfile
        from openquake.job.params import ENUM_MAP
        from openquake.calculators.hazard.general import IML_SCALING
        enum_map_reversed = dict((val, key) for (key, val) in ENUM_MAP.items())
        imt_config_names = [enum_map_reversed[imt]
                            for (imt, imt_verbose) in OqJobProfile.IMT_CHOICES
                            if imt in enum_map_reversed]
        self.assertEqual(set(IML_SCALING) - set(imt_config_names), set())
        self.assertEqual(set(imt_config_names), set(IML_SCALING))
        for imt in imt_config_names:
            self.assertTrue(callable(IML_SCALING[imt]))
            self.assertTrue(hasattr(self, 'test_imt_%s' % imt),
                            'please test imt %s' % imt)

    def _test_imt(self, imt, function):
        sample_imt = [1.2, 3.4, 5.6]
        double_array = hazard_general.get_iml_list(sample_imt, imt)
        actual_result = [val.value for val in double_array]
        expected_result = map(function, sample_imt)
        self.assertEqual(actual_result, expected_result)

    def test_imt_PGA(self):
        self._test_imt('PGA', numpy.log)

    def test_imt_SA(self):
        self._test_imt('SA', numpy.log)

    def test_imt_PGV(self):
        self._test_imt('PGV', numpy.log)

    def test_imt_PGD(self):
        self._test_imt('PGD', numpy.log)

    def test_imt_IA(self):
        self._test_imt('IA', numpy.log)

    def test_imt_RSD(self):
        self._test_imt('RSD', numpy.log)

    def test_imt_MMI(self):
        self._test_imt('MMI', lambda val: val)
