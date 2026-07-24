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
from openquake.baselib import InvalidFile
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
        flat_path = _write(FLAT_XML)
        wrap_path = _write(WRAPPED_XML)
        try:
            flat = SiteModelLogicTree(flat_path)
            wrap = SiteModelLogicTree(wrap_path)
            self.assertEqual(flat.branch_ids, wrap.branch_ids)
            numpy.testing.assert_allclose(flat.weights, wrap.weights)
        finally:
            os.unlink(flat_path)
            os.unlink(wrap_path)

    def test_rejects_wrong_uncertainty_type(self):
        path = _write(WRONG_UTYPE_XML)
        try:
            with self.assertRaises(InvalidFile) as ctx:
                SiteModelLogicTree(path)
            self.assertIn('siteModel', str(ctx.exception))
        finally:
            os.unlink(path)

    def test_rejects_weights_not_summing_to_one(self):
        path = _write(BAD_WEIGHT_XML)
        try:
            with self.assertRaises(InvalidFile) as ctx:
                SiteModelLogicTree(path)
            self.assertIn('sum to', str(ctx.exception))
        finally:
            os.unlink(path)


class SiteModelsEpistemicTest(unittest.TestCase):

    dt = numpy.dtype([('lon', float), ('lat', float), ('vs30', float)])

    def _arr(self, lon, lat, vs30):
        return numpy.array(
            list(zip(lon, lat, vs30)), self.dt)

    def test_lonlat_mismatch_is_rejected(self):
        # The load-bearing epistemic invariant: all branches must
        # reference the same physical sites
        a = self._arr([-65., -64.], [0., 0.], [760., 760.])
        b = self._arr([-65., -63.], [0., 0.], [400., 400.])
        with self.assertRaises(InvalidFile) as ctx:
            SiteModelsEpistemic(['A', 'B'], [0.6, 0.4], [a, b])
        self.assertIn('identical (lon, lat)', str(ctx.exception))

    def test_shortener_uses_base183_and_is_unique(self):
        # The site leg of the composite path uses BASE183, consistent
        # with the SSC and GSIM shorteners; short chars must be unique
        a = self._arr([-65.], [0.], [760.])
        names = ['b%d' % i for i in range(30)]
        weights = numpy.full(30, 1.0 / 30)
        smep = SiteModelsEpistemic(names, weights, [a] * 30)
        chars = list(smep.shortener.values())
        self.assertEqual(len(chars), len(set(chars)))
