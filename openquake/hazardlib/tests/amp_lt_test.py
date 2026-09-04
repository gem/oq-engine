# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import os
import tempfile
import unittest
import numpy
import pandas as pd

from openquake.baselib import InvalidFile, hdf5
from openquake.hazardlib.amp_lt import AmplificationLogicTree
from openquake.hazardlib.site_amplification import AmplificationModel
from openquake.hazardlib.gsim_lt import GsimLogicTree
from openquake.hazardlib.logictree import SourceModelLogicTree, FullLogicTree


# Valid 2-branch amp LT: branchsets directly under <logicTree>
FLAT_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <logicTree logicTreeID="lt_ampl">
    <logicTreeBranchSet uncertaintyType="amplificationModel" branchSetID="bs">
      <logicTreeBranch branchID="low">
        <uncertaintyModel>af_low.csv</uncertaintyModel>
        <uncertaintyWeight>0.4</uncertaintyWeight>
      </logicTreeBranch>
      <logicTreeBranch branchID="high">
        <uncertaintyModel>af_high.csv</uncertaintyModel>
        <uncertaintyWeight>0.6</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
  </logicTree>
</nrml>'''

# Branch weights sum to 1.1 instead of 1.0, should be rejected by the parser
BAD_WEIGHT_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <logicTree logicTreeID="lt_ampl">
    <logicTreeBranchSet uncertaintyType="amplificationModel" branchSetID="bs">
      <logicTreeBranch branchID="low">
        <uncertaintyModel>af_low.csv</uncertaintyModel>
        <uncertaintyWeight>0.7</uncertaintyWeight>
      </logicTreeBranch>
      <logicTreeBranch branchID="high">
        <uncertaintyModel>af_high.csv</uncertaintyModel>
        <uncertaintyWeight>0.4</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
  </logicTree>
</nrml>'''

# uncertaintyType is gmpeModel not amplificationModel, should be rejected
WRONG_UTYPE_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <logicTree logicTreeID="lt_ampl">
    <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="bs">
      <logicTreeBranch branchID="b1">
        <uncertaintyModel>AbrahamsonEtAl2014</uncertaintyModel>
        <uncertaintyWeight>1.0</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
  </logicTree>
</nrml>'''

# Two branches sharing the same branchID, should be rejected
DUP_BRID_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <logicTree logicTreeID="lt_ampl">
    <logicTreeBranchSet uncertaintyType="amplificationModel" branchSetID="bs">
      <logicTreeBranch branchID="low">
        <uncertaintyModel>af_low.csv</uncertaintyModel>
        <uncertaintyWeight>0.4</uncertaintyWeight>
      </logicTreeBranch>
      <logicTreeBranch branchID="low">
        <uncertaintyModel>af_high.csv</uncertaintyModel>
        <uncertaintyWeight>0.6</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
  </logicTree>
</nrml>'''

# <logicTree> with no <logicTreeBranchSet> at all
NO_BSET_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <logicTree logicTreeID="lt_ampl">
  </logicTree>
</nrml>'''


# Helper for writing dummy LT XMLs
def _write(text):
    fd, path = tempfile.mkstemp(suffix='.xml', text=True)
    os.close(fd)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path


class AmplificationLogicTreeTest(unittest.TestCase):

    def _assert_rejects(self, xml, error_tail):
        # Helper that writes xml to a temp file with AmplificationLogicTree
        # expected to raise InvalidFile with msg of "<temp_path>: <error_tail>"
        path = _write(xml)
        with self.assertRaises(InvalidFile) as ctx:
            AmplificationLogicTree(path)
        self.assertEqual(str(ctx.exception), '%s: %s' % (path, error_tail))

    def test_parses_flat_layout(self):
        # Two branches with weights summing to 1.0
        flat = AmplificationLogicTree(_write(FLAT_XML))
        self.assertEqual(flat.branch_ids, ['low', 'high'])
        numpy.testing.assert_allclose(flat.weights, [0.4, 0.6])

    def test_rejects_wrong_uncertainty_type(self):
        self._assert_rejects(
            WRONG_UTYPE_XML,
            'only uncertaintyType="amplificationModel" is supported'
            " in an amplification logic tree, got 'gmpeModel'")

    def test_rejects_weights_not_summing_to_one(self):
        self._assert_rejects(
            BAD_WEIGHT_XML,
            'amplificationModel branch weights sum to 1.1, expected 1.0')

    def test_rejects_duplicate_branch_ids(self):
        self._assert_rejects(
            DUP_BRID_XML,
            "duplicate branchID(s) in amplification logic tree: ['low']")

    def test_rejects_missing_branchset(self):
        self._assert_rejects(
            NO_BSET_XML,
            'no amplificationModel branchset found')

    def test_is_amp_lt_true(self):
        # Should load fine as valid amp LT
        self.assertTrue(AmplificationLogicTree.is_amp_lt(_write(FLAT_XML)))

    def test_is_amp_lt_false(self):
        # Should be rejected as valid amp LT
        self.assertFalse(AmplificationLogicTree.is_amp_lt(_write(WRONG_UTYPE_XML)))     


class AmplificationModelTest(unittest.TestCase):

    def _build_amp_df(self, ampcodes, levels, pga_vals, sigma_vals):
        # Build an amp DataFrame indexed by ampcode,
        # as produced by AmplificationFunction.read_df
        rows = []
        for code in ampcodes:
            for lvl, pga, sig in zip(levels, pga_vals, sigma_vals):
                rows.append((code, lvl, pga, sig))
        df = pd.DataFrame(
            rows,
            columns=['ampcode', 'level', 'PGA', 'sigma_PGA']
            ).set_index('ampcode')
        return df

    def test_shortener_uses_base183_and_is_unique(self):
        # The amp leg of the composite path uses BASE183, consistent
        # with the SSC and GSIM shorteners; short chars must be unique
        df = self._build_amp_df(['A'], [0.01, 0.1], [2.0, 1.5], [0.1, 0.2])
        names = ['b%d' % i for i in range(30)] # 30 branch names
        weights = numpy.full(30, 1.0 / 30)
        amep = AmplificationModel(names, weights, [df] * 30)
        chars = list(amep.shortener.values())
        self.assertEqual(len(chars), len(set(chars))) # Unique per branch


class FullLogicTreeRoundtripTest(unittest.TestCase):

    def _build_lt(self):
        df = pd.DataFrame(
            {'level': [0.01, 0.1],
             'PGA': [2.0, 1.5],
             'sigma_PGA': [0.1, 0.2]},
             index=pd.Index(['A', 'A'], name='ampcode')
             )
        full_lt = FullLogicTree.fake(GsimLogicTree.from_('[FromFile]'))
        full_lt.source_model_lt = SourceModelLogicTree.fake()
        full_lt.amp_lt = AmplificationModel(
            ['low', 'high'], [0.4, 0.6], [df, df],
            filenames=['amp_low.csv', 'amp_high.csv'],
            tree_filename='amp_lt.xml', branchset_id='bs_ampl'
            )
        return full_lt

    def _roundtrip(self, full_lt):
        fd, path = tempfile.mkstemp(suffix='.hdf5')
        os.close(fd)
        with hdf5.File(path, 'w') as f:
            f['flt'] = full_lt
        with hdf5.File(path, 'r') as f:
            return f['flt']

    def test_roundtrip_preserves_dstore(self):
        # dstore info survives __toh5__/__fromh5__
        full_lt = self._build_lt()
        reloaded = self._roundtrip(full_lt)
        amep = reloaded.amp_lt
        self.assertIsNotNone(amep)
        self.assertEqual(amep.names, ['low', 'high'])
        numpy.testing.assert_allclose(amep.weights, [0.4, 0.6])
        self.assertEqual(amep.filenames, ['amp_low.csv', 'amp_high.csv'])
        self.assertEqual(amep.filename, 'amp_lt.xml')
        self.assertEqual(amep.branchset_id, 'bs_ampl')


class GetRealizationsWithAmpLTTest(unittest.TestCase):

    def _build_lt(self, num_samples=0, sampling_method='early_weights'):
        df = pd.DataFrame(
            {'level': [0.01, 0.1],
             'PGA': [2.0, 1.5],
             'sigma_PGA': [0.1, 0.2]},
            index=pd.Index(['A', 'A'], name='ampcode')
            )
        full_lt = FullLogicTree.fake(GsimLogicTree.from_('[FromFile]'))
        full_lt.source_model_lt = SourceModelLogicTree.fake()
        full_lt.source_model_lt.num_samples = num_samples
        full_lt.source_model_lt.sampling_method = sampling_method
        full_lt.amp_lt = AmplificationModel(
            ['low', 'high'], [0.4, 0.6], [df, df])
        full_lt.init()
        return full_lt

    def test_full_enumeration_produces_outer_product(self):
        # 1 SSC * 1 GMM * 2 AMPL = 2 rlzs, weights = w_ssc * w_gmm * w_ampl
        full_lt = self._build_lt(num_samples=0)
        rlzs = full_lt.get_realizations()
        self.assertEqual(len(rlzs), 2)
        self.assertTrue(all(r.ampl_rlz is not None for r in rlzs))
        weights = sorted(float(r.weight[0]) for r in rlzs)
        numpy.testing.assert_allclose(weights, [0.4, 0.6], atol=1e-6)
        numpy.testing.assert_allclose(
            sum(float(r.weight[0]) for r in rlzs), 1.0, atol=1e-6)

    def test_rlz_path_has_three_legs(self):
        # Branch_path gains a third "~"" separated leg
        full_lt = self._build_lt(num_samples=0)
        for r in full_lt.rlzs:
            self.assertEqual(r['branch_path'].count('~'), 2)

    def test_early_weights_sampling_produces_uniform_weights(self):
        # early_weights: num_samples rlzs each with weight 1/num_samples
        full_lt = self._build_lt(num_samples=4)
        rlzs = full_lt.get_realizations()
        self.assertEqual(len(rlzs), 4)
        self.assertTrue(all(r.ampl_rlz is not None for r in rlzs))
        for r in rlzs:
            numpy.testing.assert_allclose(float(r.weight[0]), 1.0 / 4)

    def test_late_weights_sampling_preserves_tree_weights(self):
        # late_weights: rlz weights follow branch-weight ratios, sum to 1
        full_lt = self._build_lt(
            num_samples=100, sampling_method='late_weights')
        rlzs = full_lt.get_realizations()
        self.assertEqual(len(rlzs), 100)
        numpy.testing.assert_allclose(
            sum(float(r.weight[0]) for r in rlzs), 1.0, atol=1e-6)
        # Two distinct weights (one per branch) whose ratio matches 0.6/0.4
        distinct = sorted({round(float(r.weight[0]), 9) for r in rlzs})
        self.assertEqual(len(distinct), 2)
        numpy.testing.assert_allclose(
            distinct[1] / distinct[0], 0.6 / 0.4, atol=1e-6)
