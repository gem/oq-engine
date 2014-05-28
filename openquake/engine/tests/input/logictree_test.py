# -*- coding: utf-8 -*-

# Copyright (c) 2010-2014, GEM Foundation.
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
Tests for python logic tree processor.
"""

import os
import os.path
import unittest

from openquake.nrmllib.parsers import SourceModelParser

from openquake.commonlib import logictree
from openquake.commonlib.source import NrmlHazardlibConverter
from openquake.commonlib.general import deep_eq

from openquake.engine.calculators.hazard.general import make_gsim_lt

from openquake.engine.tests.utils import helpers


class LogicTreeProcessorTestCase(unittest.TestCase):
    def setUp(self):
        # this is an example with number_of_logic_tree_samples = 1
        cfg = helpers.get_data_path('classical_job.ini')
        job = helpers.get_job(cfg)
        self.source_model_lt = logictree.SourceModelLogicTree.from_hc(
            job.hazard_calculation)
        self.gmpe_lt = make_gsim_lt(
            job.hazard_calculation,
            ['Active Shallow Crust', 'Subduction Interface'])

    def test_sample_source_model(self):
        [(sm_name, weight, branch_ids)] = self.source_model_lt
        self.assertEqual(sm_name, 'example-source-model.xml')
        self.assertIsNone(weight)
        self.assertEqual(('b1', 'b5', 'b8'), branch_ids)

    def test_sample_gmpe(self):
        [(value, weight, branch_ids)] = self.gmpe_lt
        self.assertEqual(value,
                         {'Subduction Interface': 'SadighEtAl1997',
                          'Active Shallow Crust': 'ChiouYoungs2008'})
        self.assertIsNone(weight)
        self.assertEqual(('b2', 'b3'), branch_ids)


class LogicTreeProcessorParsePathTestCase(unittest.TestCase):
    def setUp(self):
        cfg = helpers.get_data_path('classical_job.ini')
        job = helpers.get_job(cfg)
        self.uncertainties_applied = []

        def apply_uncertainty(branchset, value, source):
            fingerprint = (branchset.uncertainty_type, value)
            self.uncertainties_applied.append(fingerprint)
        self.original_apply_uncertainty = logictree.BranchSet.apply_uncertainty
        logictree.BranchSet.apply_uncertainty = apply_uncertainty

        self.source_model_lt = logictree.SourceModelLogicTree.from_hc(
            job.hazard_calculation)
        self.gmpe_lt = make_gsim_lt(
            job.hazard_calculation,
            ['Active Shallow Crust', 'Subduction Interface'])

    def tearDown(self):
        logictree.BranchSet.apply_uncertainty = self.original_apply_uncertainty

    def test_parse_source_model_logictree_path(self):
        make_apply_un = self.source_model_lt.make_apply_uncertainties
        make_apply_un(['b1', 'b5', 'b8'])(None)
        self.assertEqual(self.uncertainties_applied,
                         [('maxMagGRRelative', -0.2),
                          ('bGRRelative', -0.1)])
        del self.uncertainties_applied[:]
        make_apply_un(['b1', 'b3', 'b6'])(None)
        self.assertEqual(self.uncertainties_applied,
                         [('maxMagGRRelative', 0.2),
                          ('bGRRelative', 0.1)])


class _BaseSourceModelLogicTreeBlackboxTestCase(unittest.TestCase):
    JOB_CONFIG = None

    def _do_test(self, path, expected_result, expected_branch_ids):
        cfg = helpers.get_data_path(self.JOB_CONFIG)
        job = helpers.get_job(cfg)

        nrml_to_hazardlib = NrmlHazardlibConverter(job.hazard_calculation)
        base_path = job.hazard_calculation.base_path

        source_model_lt = logictree.SourceModelLogicTree.from_hc(
            job.hazard_calculation)

        [branch] = source_model_lt.root_branchset.branches
        all_branches = source_model_lt.branches
        path = iter(path)
        while branch.child_branchset is not None:
            nextbranch = all_branches[next(path)]
            branch.child_branchset.sample = (
                lambda nextbranch: lambda rnd: nextbranch)(nextbranch)
            branch = nextbranch
        assert list(path) == []

        [(sm_path, weight, branch_ids)] = source_model_lt
        branch_ids = list(branch_ids)
        self.assertEqual(expected_branch_ids, branch_ids)
        modify_source = source_model_lt.make_apply_uncertainties(branch_ids)

        expected_result_path = os.path.join(base_path, expected_result)
        e_nrml_sources = SourceModelParser(expected_result_path).parse()
        e_hazardlib_sources = [
            nrml_to_hazardlib(source)
            for source in e_nrml_sources]

        original_sm_path = os.path.join(base_path, sm_path)
        a_nrml_sources = SourceModelParser(original_sm_path).parse()
        a_hazardlib_sources = [
            nrml_to_hazardlib(source)
            for source in a_nrml_sources]
        for i, source in enumerate(a_hazardlib_sources):
            modify_source(source)

        self.assertEqual(len(e_hazardlib_sources), len(a_hazardlib_sources))
        for i in xrange(len(e_hazardlib_sources)):
            expected_source = e_hazardlib_sources[i]
            actual_source = a_hazardlib_sources[i]
            self.assertTrue(*deep_eq(expected_source, actual_source))


class RelSMLTBBTestCase(_BaseSourceModelLogicTreeBlackboxTestCase):
    JOB_CONFIG = helpers.get_data_path(
        'LogicTreeRelativeUncertaintiesTest/rel_uncert.ini')

    def test_b4(self):
        self._do_test(['b2', 'b4'], 'result_b4.xml', ['b1', 'b2', 'b4'])

    def test_b5(self):
        self._do_test(['b2', 'b5'], 'result_b5.xml', ['b1', 'b2', 'b5'])

    def test_b6(self):
        self._do_test(['b3', 'b6'], 'result_b6.xml', ['b1', 'b3', 'b6'])

    def test_b7(self):
        self._do_test(['b3', 'b7'], 'result_b7.xml', ['b1', 'b3', 'b7'])


class AbsSMLTBBTestCase(_BaseSourceModelLogicTreeBlackboxTestCase):
    JOB_CONFIG = helpers.get_data_path(
        'LogicTreeAbsoluteUncertaintiesTest/abs_uncert.ini')

    def test_b4(self):
        self._do_test(['b2', 'b4'], 'result_b4.xml', ['b1', 'b2', 'b4'])

    def test_b5(self):
        self._do_test(['b2', 'b5'], 'result_b5.xml', ['b1', 'b2', 'b5'])

    def test_b7(self):
        self._do_test(['b3', 'b7'], 'result_b7.xml', ['b1', 'b3', 'b7'])

    def test_b8(self):
        self._do_test(
            ['b3', 'b6', 'b8'], 'result_b8.xml', ['b1', 'b3', 'b6', 'b8'])

    def test_b9(self):
        self._do_test(
            ['b3', 'b6', 'b9'], 'result_b9.xml', ['b1', 'b3', 'b6', 'b9'])
