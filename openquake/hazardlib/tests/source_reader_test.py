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
import unittest
import numpy
from openquake.hazardlib import nrml
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.mfd.multi_mfd import MultiMFD
from openquake.hazardlib.source.multi_point import MultiPointSource
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.geo import NodalPlane
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.source.base import ts_samples_dt
from openquake.hazardlib.source_reader import splitMF


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
