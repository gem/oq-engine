#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2017, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import os
import io
import unittest
from openquake.hazardlib import nrml
from openquake.hazardlib.sourceconverter import update_source_model

testdir = os.path.join(os.path.dirname(__file__), 'source_model')

expected = '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.5"
xmlns:gml="http://www.opengis.net/gml"
>
    <sourceGroup
    name="group 1"
    tectonicRegion="Active Shallow Crust"
    >
        
        <multiPointSource
        id="mps-0"
        name="multiPointSource-0"
        >
            <multiPointGeometry>
                <gml:posList>
                    -7.0899780E+01 -1.8157140E+01 -7.1899780E+01 -1.8157140E+01
                </gml:posList>
                <upperSeismoDepth>
                    0.0000000E+00
                </upperSeismoDepth>
                <lowerSeismoDepth>
                    3.8000000E+01
                </lowerSeismoDepth>
            </multiPointGeometry>
            <magScaleRel>
                WC1994
            </magScaleRel>
            <ruptAspectRatio>
                1.0000000E+00
            </ruptAspectRatio>
            <multiMFD
            kind="truncGutenbergRichterMFD"
            size="2"
            >
                <min_mag>
                    4.5000000E+00
                </min_mag>
                <max_mag>
                    8.2000000E+00
                </max_mag>
                <a_val>
                    1.9473715E+00
                </a_val>
                <b_val>
                    1.0153966E+00
                </b_val>
            </multiMFD>
            <nodalPlaneDist>
                <nodalPlane dip="9.0000000E+01" probability="5.0000000E-01" rake="-9.0000000E+01" strike="1.3500000E+02"/>
                <nodalPlane dip="6.0000000E+01" probability="5.0000000E-01" rake="9.0000000E+01" strike="1.3500000E+02"/>
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth depth="5.5000000E+00" probability="2.3200000E-01"/>
                <hypoDepth depth="1.6500000E+01" probability="9.8000000E-02"/>
                <hypoDepth depth="2.7500000E+01" probability="6.7000000E-01"/>
            </hypoDepthDist>
        </multiPointSource>
    </sourceGroup>
</nrml>
'''


class PointToMultiPointTestCase(unittest.TestCase):
    def test(self):
        testfile = os.path.join(testdir, 'two-point-sources.xml')
        sm = nrml.read(testfile).sourceModel
        update_source_model(sm)
        with io.BytesIO() as f:
            nrml.write(sm, f)
            got = f.getvalue().decode('utf-8')
            print(got)
            self.assertEqual(got, expected)
