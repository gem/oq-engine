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

import numpy
import os
import unittest

from openquake import engine
from openquake import kvs
from openquake import logs
from openquake import xml
from openquake.calculators.hazard import CALCULATORS
from openquake.calculators.hazard import general as hazard_general
from openquake.calculators.hazard.scenario import core as scenario
from openquake.engine import JobContext
from openquake.export import psha
from openquake.job import params as job_params
from openquake.kvs import tokens
from openquake.nrml.utils import nrml_schema_file

from tests.utils import helpers

LOG = logs.LOG

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

    @helpers.skipit
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
                the_job.params['COMPUTE_MEAN_HAZARD_CURVE'].lower() ==
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

            LOG.debug("verifying KVS entries for quantile hazard curves, "
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

                LOG.debug("verifying KVS entries for quantile hazard maps, "
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

                nrml_path = psha.nrml_path(calculator.job_ctxt, "curve",
                                           realization)

                LOG.debug("validating NRML file %s" % nrml_path)

                self.assertTrue(xml.validates_against_xml_schema(
                    nrml_path, NRML_SCHEMA_PATH),
                    "NRML instance file %s does not validate against schema"
                    % nrml_path)

        def verify_mean_haz_curves_stored_to_nrml(the_job, calculator):
            """Tests that a mean hazard curve NRML file has been written,
            and that this file validates against the NRML schema.
            Does NOT test if results in NRML file are correct.
            """

            if the_job.params['COMPUTE_MEAN_HAZARD_CURVE'].lower() == 'true':
                nrml_path = psha.nrml_path(calculator.job_ctxt, "mean")

                LOG.debug("validating NRML file %s" % nrml_path)

                self.assertTrue(xml.validates_against_xml_schema(
                    nrml_path, NRML_SCHEMA_PATH),
                    "NRML instance file %s does not validate against schema"
                    % nrml_path)

        def verify_mean_haz_maps_stored_to_nrml(the_job):
            """Tests that a mean hazard map NRML file has been written,
            and that this file validates against the NRML schema.
            Does NOT test if results in NRML file are correct.
            """
            if (the_job.params[hazard_general.POES_PARAM_NAME] != '' and
                the_job.params['COMPUTE_MEAN_HAZARD_CURVE'].lower() ==
                'true'):

                for poe in calculator.poes_hazard_maps:
                    _, nrml_path, _ = psha.hms_meta(
                        calculator.job_ctxt, "mean", (poe,))

                    LOG.debug("validating NRML file for mean hazard map %s"
                        % nrml_path)

                    self.assertTrue(xml.validates_against_xml_schema(
                        nrml_path, NRML_SCHEMA_PATH),
                        "NRML instance file %s does not validate against "
                        "schema" % nrml_path)

        def verify_quantile_haz_curves_stored_to_nrml(the_job, calculator):
            """Tests that quantile hazard curve NRML files have been written,
            and that these file validate against the NRML schema.
            Does NOT test if results in NRML files are correct.
            """

            for quantile in calculator.quantile_levels:

                nrml_path = psha.nrml_path(calculator.job_ctxt, "quantile",
                                           quantile)
                LOG.debug("validating NRML file for quantile hazard curve: "
                    "%s" % nrml_path)

                self.assertTrue(xml.validates_against_xml_schema(
                    nrml_path, NRML_SCHEMA_PATH),
                    "NRML instance file %s does not validate against schema"
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
                        _, nrml_path, _ = psha.hms_meta(
                            calculator.job_ctxt, "quantile", (poe, quantile))

                        LOG.debug("validating NRML file for quantile hazard "
                            "map: %s" % nrml_path)

                        self.assertTrue(xml.validates_against_xml_schema(
                            nrml_path, NRML_SCHEMA_PATH),
                            "NRML instance file %s does not validate against "
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

        calculator.execute()
        calculator.post_execute()
        used_keys = []
        calculator.clean_up(used_keys)

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


class ParameterizeSitesTestCase(unittest.TestCase):
    """Tests relating to BaseHazardCalculator.parameterize_sites()."""

    def test_parameterize_sites_no_site_model(self):
        job_ctxt = helpers.prepare_job_context(
            helpers.demo_file('scenario_risk/config.gem')
        )

        calc = scenario.ScenarioHazardCalculator(job_ctxt)

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
