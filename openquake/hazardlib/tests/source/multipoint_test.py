# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2020 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import numpy
from openquake.baselib import hdf5, general
from openquake.hazardlib.sourcewriter import obj_to_node
from openquake.hazardlib.mfd.multi_mfd import MultiMFD
from openquake.hazardlib.source.multi import MultiPointSource
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.geo import NodalPlane
from openquake.hazardlib.pmf import PMF


class MultiPointTestCase(unittest.TestCase):

    def test(self):
        npd = PMF([(0.5, NodalPlane(1, 20, 3)),
                   (0.5, NodalPlane(2, 2, 4))])
        hd = PMF([(1, 14)])
        mesh = Mesh(numpy.array([0, 1]), numpy.array([0.5, 1]))
        mmfd = MultiMFD('incrementalMFD',
                        size=2,
                        min_mag=[4.5],
                        bin_width=[2.0],
                        occurRates=[[.3, .1], [.4, .2, .1]])
        mps = MultiPointSource('mp1', 'multi point source',
                               'Active Shallow Crust',
                               mmfd, PeerMSR(), 1.0,
                               10, 20, npd, hd, mesh)
        # test the splitting
        splits = list(mps)
        self.assertEqual(len(splits), 2)
        for split in splits:
            self.assertEqual(split.et_id, mps.et_id)

        got = obj_to_node(mps).to_str()
        print(got)
        exp = '''\
multiPointSource{id='mp1', name='multi point source'}
  multiPointGeometry
    gml:posList [0.0, 0.5, 1.0, 1.0]
    upperSeismoDepth 10
    lowerSeismoDepth 20
  magScaleRel 'PeerMSR'
  ruptAspectRatio 1.0
  multiMFD{kind='incrementalMFD', size=2}
    bin_width [2.0]
    min_mag [4.5]
    occurRates [0.3, 0.1, 0.4, 0.2, 0.1]
    lengths [2, 3]
  nodalPlaneDist
    nodalPlane{dip=20, probability=0.5, rake=3, strike=1}
    nodalPlane{dip=2, probability=0.5, rake=4, strike=2}
  hypoDepthDist
    hypoDepth{depth=14, probability=1.0}
'''
        self.assertEqual(got, exp)

        # test serialization to and from hdf5
        tmp = general.gettemp(suffix='.hdf5')
        with hdf5.File(tmp, 'w') as f:
            f[mps.source_id] = mps
        with hdf5.File(tmp, 'r') as f:
            f[mps.source_id]

        # test the bounding box
        bbox = mps.get_bounding_box(maxdist=100)
        numpy.testing.assert_almost_equal(
            (-0.8994569916564479, -0.39932, 1.8994569916564479, 1.89932),
            bbox)
