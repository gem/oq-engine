"""Precision and integration tests for probability-to-rate conversion."""
from decimal import Decimal, localcontext
from types import SimpleNamespace
import unittest

import numpy as np

from openquake._unc.analysis import Analysis
from openquake._unc.dsg_mde import get_afes_from_dstore
from openquake._unc.hazard_pmf import afes_matrix_from_dstore
from openquake._unc.processing.sampling import sampling
from openquake._unc.utils import probabilities_to_rates


def reference_rates(poes, time):
    """Use decimal arithmetic as an independent numerical reference."""
    with localcontext() as ctx:
        ctx.prec = 90
        rates = [-((Decimal(1) - Decimal.from_float(float(p))).ln()) /
                 Decimal.from_float(float(time)) for p in np.ravel(poes)]
    return np.array([float(rate) for rate in rates]).reshape(np.shape(poes))


class Store(dict):
    """Minimal datastore interface for conversion integration tests."""
    def getitem(self, key):
        return self[key]


class RateConversionTest(unittest.TestCase):
    def test_float64_precision(self):
        poes = np.array([0., 1e-40, 1e-25, 1e-16, 1e-8, .2, .99999999,
                         np.nextafter(1., 0.)])
        rates = probabilities_to_rates(poes, 50.)
        np.testing.assert_allclose(rates, reference_rates(poes, 50.),
                                   rtol=5e-16, atol=0)
        self.assertTrue((rates[1:] > 0).all())
        self.assertTrue(np.isfinite(rates).all())

    def test_float32_promoted_and_input_preserved(self):
        poes = np.array([0., 1e-30, 1e-8, .2, np.nextafter(
            np.float32(1), np.float32(0))], dtype=np.float32)
        original = poes.copy()
        poes.flags.writeable = False
        rates = probabilities_to_rates(poes, 50.)
        self.assertEqual(rates.dtype, np.dtype('float64'))
        np.testing.assert_allclose(rates, reference_rates(poes, 50.),
                                   rtol=5e-16, atol=0)
        np.testing.assert_array_equal(poes, original)

    def test_shapes_and_scalar(self):
        self.assertEqual(probabilities_to_rates(.2, 1.).shape, ())
        self.assertEqual(probabilities_to_rates(np.zeros((2, 3)), 1.).shape,
                         (2, 3))
        self.assertEqual(probabilities_to_rates(np.empty((0, 2)), 1.).shape,
                         (0, 2))

    def test_invalid_probabilities(self):
        for value in [-1e-12, 1.00001, np.nan, np.inf, -np.inf]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'Probabilities'):
                    probabilities_to_rates([value], 50.)
        with self.assertRaisesRegex(ValueError, 'infinite rate'):
            probabilities_to_rates([1.], 50.)

    def test_invalid_investigation_time(self):
        for time in [0., -1., np.nan, np.inf, [50.], None, 'invalid']:
            with self.subTest(time=time):
                with self.assertRaisesRegex(ValueError, 'Investigation time'):
                    probabilities_to_rates([.2], time)


class RateConversionIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.poes = np.array([0., 1e-25, 1e-8, .99999999])
        self.expected = reference_rates(self.poes, 50.)
        curves = self.poes.reshape(1, 1, 1, -1).copy()
        disagg = self.poes.reshape(1, -1, 1, 1, 1).copy()
        curves.flags.writeable = False
        disagg.flags.writeable = False
        self.store = Store({
            'oqparam': SimpleNamespace(investigation_time=50.,
                                      hazard_imtls={'PGA': [.1, .2, .3, .4]},
                                      imtls={'PGA': [.1, .2, .3, .4]}),
            'sitecol/sids': [0], 'weights': np.array([1.]),
            'hcurves-rlzs': curves, 'disagg-rlzs/Mag': disagg,
            'best_rlzs': np.array([[0]]),
            'disagg-bins/Mag': np.arange(5.),
            'disagg-bins/Dist': np.arange(2.),
            'disagg-bins/Eps': np.arange(2.)})
        self.analysis = Analysis([], [], {'a': self.store}, 'analysis.xml', 10)

    def test_hazard_and_disaggregation_readers(self):
        for atype in ['hcurves', 'm']:
            with self.subTest(atype=atype):
                _, rates, _ = afes_matrix_from_dstore(
                    self.store, 'PGA', atype)
                np.testing.assert_allclose(rates[0], self.expected,
                                           rtol=5e-16, atol=0)
        _, rates, _, _ = get_afes_from_dstore(self.store, 'Mag', 0)
        np.testing.assert_allclose(rates[:, 0], self.expected,
                                   rtol=5e-16, atol=0)

    def test_sampling_preserves_rates(self):
        _, rates = sampling(self.analysis, {}, 3)
        np.testing.assert_allclose(rates[0, 0, :, 0, :],
                                   np.tile(self.expected, (3, 1)),
                                   rtol=5e-16, atol=0)

    def test_analysis_reference_rates(self):
        poes = self.poes.reshape(-1, 1, 1).copy()
        poes.flags.writeable = False
        rates, indices = self.analysis.extract_afes_rlzs(poes, np.array([1.]))
        self.assertEqual(indices, [1, 2, 3])
        np.testing.assert_allclose(rates, self.expected[1:],
                                   rtol=5e-16, atol=0)
