"""Regression tests for uncertainty propagation."""
import unittest
import numpy as np
from openquake._unc.convolution import HistoGroup
import tempfile
from pathlib import Path
import h5py


class HistogramRegressionTest(unittest.TestCase):
    def test_export_missing_columns(self):
        h = HistoGroup([np.array([1., 0.]), None], [-2, None], [1, None])
        mat, afes = h.to_matrix()
        np.testing.assert_equal(mat[:, 0], [1., 0.])
        self.assertTrue(np.isnan(mat[:, 1]).all())
        self.assertEqual(len(afes), 2)
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / 'histograms.hdf5')
            h.save(path)
            with h5py.File(path, 'r') as saved:
                np.testing.assert_equal(saved['histograms'][:], mat)
                self.assertTrue(np.isnan(saved['mininum_power'][1]))
                self.assertTrue(np.isnan(saved['number_of_powers'][1]))
