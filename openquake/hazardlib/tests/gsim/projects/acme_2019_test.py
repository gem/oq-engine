
import os
import numpy as np
import unittest

from openquake.hazardlib import contexts
from openquake.hazardlib.imt import SA
from openquake.hazardlib.gsim.projects.acme_2019 import AlAtikSigmaModel
from openquake.hazardlib.gsim.yenier_atkinson_2015 import get_sof_adjustment


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'projects')


class AlAtikSigmaModelTest(unittest.TestCase):

    def test01(self):
        filename = os.path.join(DATA_PATH, 'kappa.txt')
        gmm = AlAtikSigmaModel(gmpe_name='BindiEtAl2014Rjb',
                               kappa_file=filename,
                               kappa_val='high')
        ctx = contexts.RuptureContext()
        ctx.rup_id = 0
        ctx.mag = 6.0
        ctx.vs30 = np.array([760.] * 4)
        ctx.rjb = ctx.rrup = np.array([1., 10., 30., 70.])
        ctx.hypo_depth = np.array([10., 10., 30., 70.])
        ctx.rake = np.array([30.] * 4)
        ctx.sids = np.arange(4)
        contexts.get_mean_stds(gmm, ctx, [SA(0.1)], truncation_level=0)

    def test02(self):
        # checks if gmpe is always being evaluated at vs30=760
        # see HID 2.6.2
        filename = os.path.join(DATA_PATH, 'kappa.txt')
        gmm = AlAtikSigmaModel(gmpe_name='YenierAtkinson2015ACME2019',
                               kappa_file=filename,
                               kappa_val='high')
        ctx = contexts.RuptureContext()
        ctx.rup_id = 0
        ctx.mag = 6.0
        ctx.rjb = ctx.rrup = np.array([1., 10., 30., 70.])
        ctx.hypo_depth = np.array([10., 10., 30., 70.])
        ctx.rake = 30.
        ctx.vs30 = np.array([760.] * 4)
        ctx.sids = np.arange(4)
        imt = SA(0.1)
        mean_760 = contexts.get_mean_stds(
            gmm, ctx, [imt], truncation_level=0)[0]

        ctx.vs30 = np.array([1500.] * 4)
        mean_1500 = contexts.get_mean_stds(
            gmm, ctx, [imt], truncation_level=0)[0]
        np.testing.assert_allclose(mean_760, mean_1500)


class GetSoFTestCase(unittest.TestCase):
    MSG = 'Wrong style-of-faulting coefficient'

    def test_short_period(self):
        # Normal
        rake = -90
        period = 0.01
        expected = 0.8401
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # Reverse
        rake = 90
        expected = 1.0612
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # SS
        rake = 0
        expected = 0.8843
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)

    def test_long_period(self):
        # Normal
        rake = -90
        period = 2.0
        expected = 0.9775
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # Reverse
        rake = 90
        expected = 0.9882
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # SS
        rake = 0
        expected = 1.0289
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
