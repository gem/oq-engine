# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from openquake.risk.job.probabilistic import ProbabilisticEventMixin
from openquake.parser import exposure
from utils import test


TEST_FILE = 'exposure-portfolio.xml'


class EpsilonTestCase(unittest.TestCase):
    """Tests the method:`epsilon` in class:`ProbabilisticEventMixin`"""

    def setUp(self):
        self.exposure_parser = exposure.ExposurePortfolioFile(
            os.path.join(test.SCHEMA_EXAMPLES_DIR, TEST_FILE))
        self.mixin = ProbabilisticEventMixin()

    def test_uncorrelated(self):
        """In case of uncorrelated jobs we should obtain an independent
        `epsilon` value for each asset."""
        samples = []
        self.mixin.__dict__['ASSET_CORRELATION'] = False
        for _, asset in self.exposure_parser:
            sample = self.mixin.epsilon(asset)
            self.assertTrue(
                sample not in samples,
                "%s is already in %s" % (sample, samples))
            samples.append(sample)

    def test_correlated(self):
        """In case of uncorrelated jobs we should obtain an independent
        `epsilon` value for each asset."""
        import pdb
        samples = []
        self.mixin.__dict__['ASSET_CORRELATION'] = True
        for _, asset in self.exposure_parser:
            pdb.set_trace()
            sample = self.mixin.epsilon(asset)
            self.assertTrue(
                sample not in samples,
                "%s is already in %s" % (sample, samples))
            samples.append(sample)
