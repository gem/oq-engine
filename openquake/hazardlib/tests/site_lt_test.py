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
from openquake.baselib import InvalidFile, hdf5
from openquake.hazardlib import logictree
from openquake.hazardlib.gsim_lt import GsimLogicTree
from openquake.hazardlib.logictree import (
    SourceModelLogicTree, FullLogicTree)
from openquake.hazardlib.site_lt import (
    SiteModelLogicTree, SiteModelsEpistemic)


# Valid 2-branch site-model logic tree with branchsets directly under <logicTree>
FLAT_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <logicTree logicTreeID="lt_site">
    <logicTreeBranchSet uncertaintyType="siteModel" branchSetID="bs">
      <logicTreeBranch branchID="rock">
        <uncertaintyModel>rock.csv</uncertaintyModel>
        <uncertaintyWeight>0.6</uncertaintyWeight>
      </logicTreeBranch>
      <logicTreeBranch branchID="soil">
        <uncertaintyModel>soil.csv</uncertaintyModel>
        <uncertaintyWeight>0.4</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
  </logicTree>
</nrml>'''

# Same tree wrapped in <logicTreeBranchingLevel> (older NRML nesting)
WRAPPED_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <logicTree logicTreeID="lt_site">
    <logicTreeBranchingLevel branchingLevelID="bl1">
      <logicTreeBranchSet uncertaintyType="siteModel" branchSetID="bs">
        <logicTreeBranch branchID="rock">
          <uncertaintyModel>rock.csv</uncertaintyModel>
          <uncertaintyWeight>0.6</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="soil">
          <uncertaintyModel>soil.csv</uncertaintyModel>
          <uncertaintyWeight>0.4</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
    </logicTreeBranchingLevel>
  </logicTree>
</nrml>'''

# Branch weights sum to 1.1 instead of 1.0, should be rejected by the parser
BAD_WEIGHT_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <logicTree logicTreeID="lt_site">
    <logicTreeBranchSet uncertaintyType="siteModel" branchSetID="bs">
      <logicTreeBranch branchID="rock">
        <uncertaintyModel>rock.csv</uncertaintyModel>
        <uncertaintyWeight>0.7</uncertaintyWeight>
      </logicTreeBranch>
      <logicTreeBranch branchID="soil">
        <uncertaintyModel>soil.csv</uncertaintyModel>
        <uncertaintyWeight>0.4</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
  </logicTree>
</nrml>'''

# uncertaintyType is gmpeModel not siteModel, should be rejected
WRONG_UTYPE_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <logicTree logicTreeID="lt_site">
    <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="bs">
      <logicTreeBranch branchID="b1">
        <uncertaintyModel>Foo</uncertaintyModel>
        <uncertaintyWeight>1.0</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
  </logicTree>
</nrml>'''


def _write(text):
    fd, path = tempfile.mkstemp(suffix='.xml', text=True)
    os.close(fd)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path


class SiteModelLogicTreeTest(unittest.TestCase):

    def test_parses_both_flat_and_branchinglevel_layouts(self):
        # Two accepted NRML nestings should yield identical branches
        flat = SiteModelLogicTree(_write(FLAT_XML))
        wrap = SiteModelLogicTree(_write(WRAPPED_XML))
        self.assertEqual(flat.branch_ids, wrap.branch_ids)
        numpy.testing.assert_allclose(flat.weights, wrap.weights)

    def test_rejects_wrong_uncertainty_type(self):
        with self.assertRaises(InvalidFile) as ctx:
            SiteModelLogicTree(_write(WRONG_UTYPE_XML))
        self.assertIn('siteModel', str(ctx.exception))

    def test_rejects_weights_not_summing_to_one(self):
        with self.assertRaises(InvalidFile) as ctx:
            SiteModelLogicTree(_write(BAD_WEIGHT_XML))
        self.assertIn('sum to', str(ctx.exception))


class SiteModelsEpistemicTest(unittest.TestCase):

    dt = numpy.dtype([('lon', float), ('lat', float), ('vs30', float)])

    def _arr(self, lon, lat, vs30):
        return numpy.array(
            list(zip(lon, lat, vs30)), self.dt)

    def test_lonlat_mismatch_is_rejected(self):
        # Make sure non-identical lon/lat raises error
        a = self._arr([-65., -64.], [0., 0.], [760., 760.])
        b = self._arr([-65., -63.], [0., 0.], [400., 400.])
        with self.assertRaises(InvalidFile) as ctx:
            SiteModelsEpistemic(['A', 'B'], [0.6, 0.4], [a, b])
        self.assertIn('identical (lon, lat)', str(ctx.exception))

    def test_shortener_uses_base183_and_is_unique(self):
        # The site leg of the composite path uses BASE183, consistent
        # with the SSC and GSIM shorteners; short chars must be unique
        site = self._arr([-65.], [0.], [760.])
        names = ['b%d' % i for i in range(30)] # Make 30 branch names
        weights = numpy.full(30, 1.0 / 30) # Assign weight to each
        smep = SiteModelsEpistemic(names, weights, [site] * 30)
        chars = list(smep.shortener.values())
        self.assertEqual(len(chars), len(set(chars))) # Unique per branch


class ReduceFullWithSiteLTTest(unittest.TestCase):
    """
    Check that reduce_full handles the site leg correctly.
    """

    def _full_lt_with_site_lt(self):
        # Create site model LT
        dt = numpy.dtype([('lon', float), ('lat', float), ('vs30', float)])
        a = numpy.array([(-65., 0., 760.)], dt)
        b = numpy.array([(-65., 0., 360.)], dt)
        smep = SiteModelsEpistemic(
            ['rock', 'soil'], [0.6, 0.4], [a, b],
            tree_filename='site_lt.xml', branchset_id='bs_site')

        # Trivial single-branch SSC and GSIM
        full_lt = FullLogicTree.fake(GsimLogicTree.from_('[FromFile]'))
        full_lt.source_model_lt = SourceModelLogicTree.fake()

        # Set the site model LT
        full_lt.site_model_lt = smep

        return full_lt, smep

    def test_site_branch_shared_across_cluster_is_marked_reducible(self):
        # Make full LT
        full_lt, smep = self._full_lt_with_site_lt()

        # Two rlzs both pinned to rock: the soil branch is unused
        rock_short = smep.shortener['rock']
        paths = ['A~A~%s' % rock_short, 'A~A~%s' % rock_short]
        res = logictree.reduce_full(full_lt, paths)

        # Site LT filename in the result with 'rock' as sole survivor
        self.assertIn('site_lt.xml', res)
        self.assertEqual(res['site_lt.xml'], {'bs_site': ['rock']})

        # Before = 1 (ssc) * 1 (gsim) * 2 (site) = 2
        before, _after = res['size_before_after']
        self.assertEqual(before, 2)

    def test_multiple_site_branches_in_cluster_not_reducible(self):
        # Make full LT
        full_lt, smep = self._full_lt_with_site_lt()

        # Two rlzs on different site branches: nothing to reduce
        paths = ['A~A~%s' % smep.shortener['rock'],
                 'A~A~%s' % smep.shortener['soil']]
        res = logictree.reduce_full(full_lt, paths)
        
        # Site LT absent from result = not reducible (both branches used)
        self.assertNotIn('site_lt.xml', res)


class FullLogicTreeRoundtripTest(unittest.TestCase):
    """
    __toh5__/__fromh5__ must preserve the site-model logic tree
    metadata so that reading from the datastore reconstructs an
    equivalent FullLogicTree.
    """
    def _build(self):
        # Trivial single-branch SSC and GSIM, plus a 2-branch site LT
        dt = numpy.dtype([('lon', float), ('lat', float), ('vs30', float)])
        a = numpy.array([(-65., 0., 760.)], dt)
        b = numpy.array([(-65., 0., 360.)], dt)
        full_lt = FullLogicTree.fake(GsimLogicTree.from_('[FromFile]'))
        full_lt.source_model_lt = SourceModelLogicTree.fake()
        full_lt.site_model_lt = SiteModelsEpistemic(
            ['rock', 'soil'], [0.6, 0.4], [a, b],
            filenames=['rock.csv', 'soil.csv'],
            tree_filename='site_lt.xml', branchset_id='bs_site')
        
        return full_lt

    def _roundtrip(self, full_lt):
        # Write the FullLogicTree to a temp HDF5 and read it back
        fd, path = tempfile.mkstemp(suffix='.hdf5')
        os.close(fd)
        with hdf5.File(path, 'w') as f:
            f['flt'] = full_lt
        with hdf5.File(path, 'r') as f:
            return f['flt']

    def test_roundtrip_with_site_lt_preserves_metadata(self):
        # names, weights, filenames, tree_filename, branchset_id
        # must all survive the __toh5__/__fromh5__ cycle
        full_lt = self._build()
        reloaded = self._roundtrip(full_lt)
        smep = reloaded.site_model_lt
        self.assertIsNotNone(smep)
        self.assertEqual(smep.names, ['rock', 'soil'])
        numpy.testing.assert_allclose(smep.weights, [0.6, 0.4])
        self.assertEqual(smep.filenames, ['rock.csv', 'soil.csv'])
        self.assertEqual(smep.filename, 'site_lt.xml')
        self.assertEqual(smep.branchset_id, 'bs_site')


class GetRealizationsWithSiteLTTest(unittest.TestCase):
    """
    FullLogicTree.get_realizations must produce the outer product
    ssc * gsim * site with correctly multiplied weights, and each
    LtRealization must carry a .site_rlz attribute.
    """
    def _build(self, num_samples=0, sampling_method='early_weights'):
        # Trivial single-branch SSC and GSIM + 2-branch site LT
        dt = numpy.dtype([('lon', float), ('lat', float), ('vs30', float)])
        a = numpy.array([(-65., 0., 760.)], dt)
        b = numpy.array([(-65., 0., 360.)], dt)
        full_lt = FullLogicTree.fake(GsimLogicTree.from_('[FromFile]'))
        full_lt.source_model_lt = SourceModelLogicTree.fake()
        full_lt.source_model_lt.num_samples = num_samples
        full_lt.source_model_lt.sampling_method = sampling_method
        full_lt.site_model_lt = SiteModelsEpistemic(
            ['rock', 'soil'], [0.6, 0.4], [a, b])

        # Re-run init to pick up the site LT and num_samples
        full_lt.init()

        return full_lt

    def test_full_enumeration_produces_outer_product(self):
        # 1 SSC * 1 GSIM * 2 SITE = 2 rlzs, weights = w_ssc * w_gmm * w_site
        full_lt = self._build(num_samples=0)
        rlzs = full_lt.get_realizations()
        self.assertEqual(len(rlzs), 2)

        # Each rlz has a non-None site_rlz
        self.assertTrue(all(r.site_rlz is not None for r in rlzs))

        # Weights = site weights (SSC and GSIM are both 1.0)
        weights = sorted(r.weight[0] for r in rlzs)
        numpy.testing.assert_allclose(weights, [0.4, 0.6], atol=1e-6)
        numpy.testing.assert_allclose(
            sum(r.weight[0] for r in rlzs), 1.0, atol=1e-6)

    def test_early_weights_sampling_produces_uniform_weights(self):
        # early_weights forces uniform 1/num_samples weight per rlz
        full_lt = self._build(num_samples=4)
        rlzs = full_lt.get_realizations()
        self.assertEqual(len(rlzs), 4)
        self.assertTrue(all(r.site_rlz is not None for r in rlzs))
        for r in rlzs:
            numpy.testing.assert_allclose(r.weight[0], 1.0 / 4)

    def test_late_weights_sampling_preserves_tree_weights(self):
        # late_weights draws branches uniformly and keeps each rlz's
        # tree weight product (rescaled to sum to 1 across all rlzs)
        full_lt = self._build(num_samples=100,
                              sampling_method='late_weights')
        rlzs = full_lt.get_realizations()
        self.assertEqual(len(rlzs), 100)
        self.assertTrue(all(r.site_rlz is not None for r in rlzs))

        # Weights sum to 1
        numpy.testing.assert_allclose(
            sum(r.weight[0] for r in rlzs), 1.0, atol=1e-6)

        # Exactly two distinct weights appear (rock and soil) and their
        # ratio equals the tree weight ratio 0.6 / 0.4 = 1.5
        distinct = sorted(set(round(float(r.weight[0]), 9) for r in rlzs))
        self.assertEqual(len(distinct), 2)
        numpy.testing.assert_allclose(
            distinct[1] / distinct[0], 0.6 / 0.4, atol=1e-6)
