"""Regression tests for uncertainty propagation."""
import unittest
import numpy as np
import tempfile
from pathlib import Path
from types import SimpleNamespace
import h5py
from openquake._unc.hazard_pmf import afes_matrix_from_dstore


class Store(dict):
    """Minimal datastore interface, also accepting real HDF5 datasets."""
    def getitem(self, key):
        return self[key]


class DisaggregationRegressionTest(unittest.TestCase):
    def test_hdf5_disaggregation_axes_and_default_slice(self):
        with tempfile.TemporaryDirectory() as tmp:
            with h5py.File(Path(tmp) / 'disagg.hdf5', 'w') as f:
                # Distinct axis lengths and values expose axis swaps.
                shape = (1, 3, 4, 5, 2, 1, 3)
                mde = np.arange(np.prod(shape)).reshape(shape) / 10000.
                md = mde.sum(axis=3)
                f['mde'] = mde
                f['md'] = md
                store = Store({
                    'sitecol/sids': [0],
                    'oqparam': SimpleNamespace(
                        hazard_imtls={'PGA': [0.1], 'SA(1.0)': [0.2]},
                        investigation_time=50),
                    'disagg-rlzs/Mag_Dist_Eps': f['mde'],
                    'disagg-rlzs/Mag_Dist': f['md'],
                    'weights': np.array([0.2, 0.3, 0.5]),
                    'best_rlzs': np.array([[2, 0, 1]])})
                for atype, raw in [('mde', mde)]:
                    for imti, imt in enumerate(['PGA', 'SA(1.0)']):
                        selected = raw[0, ..., imti, 0, :]
                        expected = -np.log1p(-selected).reshape(-1, 3).T / 50
                        for rlzs in [slice(None), [0, 2]]:
                            with self.subTest(atype=atype, imt=imt,
                                              rlzs=rlzs):
                                _, afes, weights = afes_matrix_from_dstore(
                                    store, imt, atype, rlzs=rlzs)
                                np.testing.assert_allclose(
                                    afes, expected[rlzs])
                                np.testing.assert_allclose(
                                    weights, np.array([0.5, 0.2, 0.3])[rlzs])
