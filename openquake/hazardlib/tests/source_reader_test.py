# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=missing-docstring

import os
import types
import unittest
import numpy
from openquake.hazardlib import nrml
from openquake.hazardlib.source_group import SourceGroup
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.mfd.multi_mfd import MultiMFD
from openquake.hazardlib.source.multi_point import MultiPointSource
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.geo import NodalPlane
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.source.base import ts_samples_dt
from openquake.hazardlib.lt import apply_uncertainty
from openquake.hazardlib.source_reader import (
    splitMF, add_bangs, check_mfd_variants, check_same_sources,
    content_hash,
    source_with_ts_sets, reduce_sources)


def make_mps():
    npd = PMF([(1, NodalPlane(0, 60, 90))])
    hd = PMF([(1, 10)])
    mesh = Mesh(numpy.array([0., 1., 2.]), numpy.array([0., 0., 0.]))
    mmfd = MultiMFD('incrementalMFD', size=3, min_mag=[4.5],
                    bin_width=[1.0], occurRates=[[0.1], [0.2], [0.3]])
    mps = MultiPointSource('mp1', 'test', 'Active Shallow Crust',
                           mmfd, PeerMSR(), 1.0, 0, 20, npd, hd, mesh)
    # two sets of realizations with different uncertainties, identified
    # by the smallest trt_smr in the field ts (see get_ts_sets)
    mps.ts_samples = numpy.array(
        [(0, 1, 0), (1, 1, 0), (2, 1, 2)], ts_samples_dt)
    mps.bysrc_unc = True
    return mps


class SplitMFTestCase(unittest.TestCase):

    def test_segments_keep_uncertainty_sets(self):
        mps = make_mps()
        sources = [mps]
        splitMF(sources, disagg_by_src=False, blocksize=1)
        self.assertEqual(len(sources), 3)  # one segment per point
        for seg in sources:
            self.assertEqual(seg.bysrc_unc, True)
            self.assertEqual(
                [tuple(t) for t in seg.get_ts_sets()],
                [(0, 1), (2,)])
            self.assertEqual(list(seg.ts_samples['trt_smr']), [0, 1, 2])


QA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    __file__))), 'qa_tests_data')


def get_sources(sms):
    return sorted((sg.trt, src.source_id)
                  for sm in sms for sg in sm.src_groups for src in sg)


class StrideTestCase(unittest.TestCase):
    # reading a source model with strides gives the same sources, while
    # the atomic groups are kept whole in the first reading
    def check(self, fname, conv):
        [whole] = nrml.read_source_models([fname], conv)
        strided = [sm for k in range(3) for sm in nrml.read_source_models(
            [fname], conv, (k, 3))]
        self.assertEqual(get_sources(strided), get_sources([whole]))
        for k, sm in enumerate(strided):
            atomic = [[src.source_id for src in sg]
                      for sg in sm.src_groups if sg.atomic]
            expected = [[src.source_id for src in sg]
                        for sg in whole.src_groups if sg.atomic]
            self.assertEqual(atomic, expected if k == 0 else [])
        return strided

    def test_nrml04(self):
        fname = os.path.join(QA, 'classical_risk/case_4/source_model.xml')
        conv = SourceConverter(50., 2., 4., .1, 10.)
        strided = self.check(fname, conv)
        self.assertEqual([len(get_sources([sm])) for sm in strided],
                         [13, 13, 13])

    def test_mutex(self):
        fname = os.path.join(QA, 'classical/case_27/source_model.xml')
        conv = SourceConverter(50., 1., 1., 1., 10.)
        self.check(fname, conv)


def make_smodel(branch, rates):
    # a source model with a single MultiPointSource with the given rates
    src = make_mps()
    src.mfd = MultiMFD('incrementalMFD', size=3, min_mag=[4.5],
                       bin_width=[1.0], occurRates=rates)
    src.checksum = content_hash(src)
    grp = SourceGroup('Active Shallow Crust', [src])
    return types.SimpleNamespace(branch=branch, src_groups=[grp])


class MFDVariantsTestCase(unittest.TestCase):
    # the same source in 3 files, two of them with the same MFD
    def test_variants(self):
        smdict = {'a.xml': make_smodel('b1', [[0.1], [0.2], [0.3]]),
                  'b.xml': make_smodel('b2', [[0.2], [0.4], [0.6]]),
                  'c.xml': make_smodel('b3', [[0.1], [0.2], [0.3]])}
        self.assertEqual(add_bangs(smdict), ['mp1'])
        with self.assertLogs(level='WARNING') as cm:
            found = check_mfd_variants(smdict, 'ssmLT.xml')
        self.assertEqual(found, ['mp1'])
        self.assertIn('mp1: 2 MultiMFD variants in a.xml b.xml c.xml',
                      cm.output[0])
        self.assertIn('oq check_input job.ini --better-smlt', cm.output[0])

    # different geometries are not MFD variants
    def test_no_variants(self):
        smdict = {'a.xml': make_smodel('b1', [[0.1], [0.2], [0.3]]),
                  'b.xml': make_smodel('b2', [[0.2], [0.4], [0.6]])}
        smdict['b.xml'].src_groups[0][0].upper_seismogenic_depth = 5.
        for smodel in smdict.values():
            src = smodel.src_groups[0][0]
            src.checksum = content_hash(src)
        add_bangs(smdict)
        self.assertEqual(check_mfd_variants(smdict, 'ssmLT.xml'), [])


class DifferentIDsTestCase(unittest.TestCase):
    # the same geometry with different IDs and different MFDs in two
    # files: the copies cannot be merged, but a warning is logged
    def test_different_ids_and_mfds(self):
        smdict = {'a.xml': make_smodel('b1', [[0.1], [0.2], [0.3]]),
                  'b.xml': make_smodel('b2', [[0.2], [0.4], [0.6]])}
        src = smdict['b.xml'].src_groups[0][0]
        src.source_id = 'mp2'
        src.checksum = content_hash(src)
        with self.assertLogs(level='WARNING') as cm:
            check_same_sources(smdict, 'ssmLT.xml')
        self.assertIn('1 sources appear in different source models with '
                      'different IDs, the same geometry and different MFDs',
                      cm.output[0])
        self.assertIn('likely variants of a base source', cm.output[0])
        self.assertIn('mp1[a.xml]', cm.output[0])
        self.assertIn('mp2[b.xml]', cm.output[0])

    # with the same MFD it is the check_input error, not this warning
    def test_different_ids_same_mfd(self):
        smdict = {'a.xml': make_smodel('b1', [[0.1], [0.2], [0.3]]),
                  'b.xml': make_smodel('b2', [[0.1], [0.2], [0.3]])}
        src = smdict['b.xml'].src_groups[0][0]
        src.source_id = 'mp2'
        src.checksum = content_hash(src)
        with self.assertLogs(level='WARNING') as cm:
            check_same_sources(smdict, 'ssmLT.xml')
        self.assertEqual(len(cm.output), 1)
        self.assertNotIn('different MFDs', cm.output[0])


class ReduceSourcesTestCase(unittest.TestCase):
    # identical copies of a source in two files, as produced by moving
    # the MFD variants in the logic tree: each copy has a single
    # signature, so its field ts is 0 before the reduction
    def reduce(self, sig1, sig2):
        src = make_mps()
        rows = []
        copy1 = source_with_ts_sets(src, [(0, 1, sig1), (1, 1, sig1)], rows)
        copy2 = source_with_ts_sets(src, [(2, 1, sig2), (3, 1, sig2)], rows)
        [red] = reduce_sources([copy1, copy2])
        self.bysrc_unc = red.bysrc_unc
        return red.get_ts_sets()

    def test_different_signatures(self):
        # the sets of realizations with different uncertainties are kept
        sets = self.reduce((('bs1', '1'),), (('bs1', '2'),))
        self.assertEqual(sets, ((0, 1), (2, 3)))

    def test_same_signature(self):
        # the copies with the same uncertainties share a single set
        sets = self.reduce((('bs1', '1'),), (('bs1', '1'),))
        self.assertEqual(sets, ((0, 1, 2, 3),))

    def test_one_copy_without_uncertainties(self):
        # the copies are merged even if only one of them is modified
        sets = self.reduce((), (('bs1', '1'),))
        self.assertEqual(sets, ((0, 1), (2, 3)))
        self.assertTrue(self.bysrc_unc)


class MultiMFDAbsoluteTestCase(unittest.TestCase):
    # the uncertainty replacing the MFDs of all the points of a
    # multiPointSource, used to move MultiMFD variants into the logic tree
    def test_apply(self):
        src = make_mps()
        value = ('incrementalMFD', 3, dict(
            min_mag=[4.5], bin_width=[1.0], occurRates=[[.2], [.3], [.4]]))
        apply_uncertainty('multiMFDAbsolute', src, value)
        rates = list(src.mfd.get_annual_occurrence_rates())
        self.assertEqual(rates, [(4.5, .2), (4.5, .3), (4.5, .4)])

    def test_wrong_size(self):
        value = ('incrementalMFD', 2, dict(
            min_mag=[4.5], bin_width=[1.0], occurRates=[[.2], [.3]]))
        with self.assertRaises(ValueError):
            apply_uncertainty('multiMFDAbsolute', make_mps(), value)
