# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from openquake import shapes
from openquake.risk.job.probabilistic import ProbabilisticEventMixin
from openquake.risk import probabilistic_event_based as prob
from openquake.parser import exposure
from utils import test


TEST_FILE = "exposure-portfolio.xml"
NUMBER_OF_SAMPLES_FROM_CONFIG = "10"


class EpsilonTestCase(unittest.TestCase):
    """Tests the `epsilon` method in class `ProbabilisticEventMixin`"""

    def setUp(self):
        self.exposure_parser = exposure.ExposurePortfolioFile(
            os.path.join(test.SCHEMA_EXAMPLES_DIR, TEST_FILE))
        self.mixin = ProbabilisticEventMixin()

    def test_uncorrelated(self):
        """For uncorrelated jobs we sample epsilon values per asset.
        
        A new sample should be drawn for each asset irrespective of any
        building typology similarities.
        """
        samples = []
        for _, asset in self.exposure_parser:
            sample = self.mixin.epsilon(asset)
            self.assertTrue(
                sample not in samples,
                "%s is already in %s" % (sample, samples))
            self.assertTrue(
                isinstance(sample, float), "Invalid sample (%s)" % sample)
            samples.append(sample)

    def test_correlated(self):
        """For correlated jobs we sample epsilon values per building typology.
        
        A sample should be drawn whenever an asset with a new building typology
        is encountered. Assets of the same typology should share sample values.
        Please not that building typologies and structure categories are
        roughly equivalent.
        """
        samples = dict()
        self.mixin.__dict__["ASSET_CORRELATION"] = "perfect"
        for _, asset in self.exposure_parser:
            sample = self.mixin.epsilon(asset)
            category = asset["structureCategory"]
            # This is either the first time we see this structure category or
            # the sample is identical to the one originally drawn for this
            # structure category.
            if category not in samples:
                samples[category] = sample
            else:
                self.assertTrue(sample == samples[category])
        # Make sure we used at least two structure categories in this test.
        self.assertTrue(len(samples.keys()) > 1)
        # Are all samples valid values?
        for category, sample in samples.iteritems():
            self.assertTrue(
                isinstance(sample, float),
                "Invalid sample (%s) for category %s" % (sample, category))

    def test_incorrect_configuration_setting(self):
        """The correctness of the asset correlation configuration is enforced.
        
        If the `ASSET_CORRELATION` parameter is set in the job configuration
        file it should have a correct value ("perfect").
        """
        self.mixin.__dict__["ASSET_CORRELATION"] = "this-is-wrong"
        for _, asset in self.exposure_parser:
            self.assertRaises(ValueError, self.mixin.epsilon, asset)
            break

    def test_correlated_with_no_structure_category(self):
        """For correlated jobs assets require a structure category property."""
        self.mixin.__dict__["ASSET_CORRELATION"] = "perfect"
        for _, asset in self.exposure_parser:
            del asset["structureCategory"]
            e = self.assertRaises(ValueError, self.mixin.epsilon, asset)
            break


class SamplesFromConfigTestCase(unittest.TestCase):
    """Tests for the functionality that reads the the number of samples
    for the probabilistic scenario from the configuration file."""

    def setUp(self):
        vuln_function = shapes.VulnerabilityFunction([
                (0.01, (0.001, 0.00)),
                (0.04, (0.022, 0.00)),
                (0.07, (0.051, 0.00)),
                (0.10, (0.080, 0.00))])

        self.gmfs = {"IMLs": (0.0872, 0.2288, 0.5655, 0.2118),
                "TSES": 200, "TimeSpan": 50}

        # TODO (ac): We should consider injecting the scientific
        # modules into the mixins to ease testing

        # a loss ratio curve computed with the default
        # number of samples specified in the probablistic_event_based module
        self.loss_ratio_curve_default = \
                prob.compute_loss_ratio_curve(vuln_function, self.gmfs)

        # a loss ratio curve computed with a number
        # of samples set to NUMBER_OF_SAMPLES_FROM_CONFIG
        self.loss_ratio_curve_config = prob.compute_loss_ratio_curve(
                vuln_function, self.gmfs, NUMBER_OF_SAMPLES_FROM_CONFIG)

        self.mixin = ProbabilisticEventMixin()

        self.mixin.id = 1234
        self.mixin.vuln_curves = {"ID": vuln_function}
        self.asset = {"vulnerabilityFunctionReference": "ID", "assetID": "ID"}

    def test_without_parameter_we_use_the_default_value(self):
        self.assertEqual(self.loss_ratio_curve_default,
                self._compute_loss_ratio_curve())
    
    def test_with_empty_parameter_we_use_the_default_value(self):
        self.mixin.__dict__["PROB_NUM_OF_SAMPLES"] = ""
        
        self.assertEqual(self.loss_ratio_curve_default,
                self._compute_loss_ratio_curve())

    def test_we_use_the_parameter_when_specified(self):
        self.mixin.__dict__["PROB_NUM_OF_SAMPLES"] = \
                NUMBER_OF_SAMPLES_FROM_CONFIG

        self.assertEqual(self.loss_ratio_curve_config,
                self._compute_loss_ratio_curve())

    def test_default_value_with_wrong_parameter(self):
        self.mixin.__dict__["PROB_NUM_OF_SAMPLES"] = "this-is-wrong"

        self.assertEqual(self.loss_ratio_curve_default,
                self._compute_loss_ratio_curve())

    def _compute_loss_ratio_curve(self):
        return self.mixin.compute_loss_ratio_curve(
                1, 1, self.asset, self.gmfs)
