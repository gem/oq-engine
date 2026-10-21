# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2026 GEM Foundation
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
import os
import io
import unittest.mock
import numpy
from openquake.hazardlib import nrml
from openquake.hazardlib.geo import Point
from openquake.hazardlib.sourceconverter import update_source_model, \
    SourceConverter

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

multipoint = '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.5"
xmlns:gml="http://www.opengis.net/gml"
>
    <sourceGroup
    rup_interdep="indep"
    src_interdep="indep"
    tectonicRegion="Active Shallow Crust"
    >
        <multiPointSource
        id="mps-0"
        name="multiPointSource-0"
        >
            <multiPointGeometry>
                <gml:posList>
                    1.7985907E+02 -2.6184290E+01 1.7700355E+02 -2.5105110E+01 1.7916000E+02 -3.2569480E+01 1.7710212E+02 -3.0321170E+01 1.7999942E+02 -3.0590970E+01 1.7956252E+02 -2.9152060E+01 1.7987145E+02 -2.9152060E+01
                </gml:posList>
                <upperSeismoDepth>
                    0.0000000E+00
                </upperSeismoDepth>
                <lowerSeismoDepth>
                    6.0000000E+01
                </lowerSeismoDepth>
            </multiPointGeometry>
            <magScaleRel>
                WC1994
            </magScaleRel>
            <ruptAspectRatio>
                2.0000000E+00
            </ruptAspectRatio>
            <multiMFD
            kind="incrementalMFD"
            size="7"
            >
                <min_mag>
                    5.0500000E+00
                </min_mag>
                <bin_width>
                    1.0000000E-01
                </bin_width>
                <occurRates>
                    9.7342763E-06 7.3833916E-06 5.6002593E-06 4.2477639E-06 3.2219041E-06 2.4437954E-06 1.8536045E-06 1.4059482E-06 1.0664035E-06 8.0886078E-07 6.1351617E-07 4.6534842E-07 3.5296406E-07 2.6772117E-07 2.0306494E-07 1.5402357E-07 1.1682598E-07 8.8611820E-08 6.7211547E-08 5.0979565E-08 3.8667702E-08 2.9329225E-08 2.2246046E-08 1.6873496E-08 1.2798448E-08 1.3663516E-04 1.0363697E-04 7.8608034E-05 5.9623734E-05 4.5224253E-05 3.4302331E-05 2.6018118E-05 1.9734590E-05 1.4968571E-05 1.1353574E-05 8.6116191E-06 6.5318627E-06 4.9543796E-06 3.7578679E-06 2.8503208E-06 2.1619517E-06 1.6398277E-06 1.2437997E-06 9.4341481E-07 7.1557461E-07 5.4275915E-07 4.1167964E-07 3.1225660E-07 2.3684480E-07 1.7964540E-07 7.5076083E-05 5.6944770E-05 4.3192275E-05 3.2761087E-05 2.4849093E-05 1.8847892E-05 1.4296016E-05 1.0843444E-05 8.2246890E-06 6.2383784E-06 4.7317735E-06 3.5890225E-06 2.7222526E-06 2.0648127E-06 1.5661483E-06 1.1879143E-06 9.0102607E-07 6.8342301E-07 5.1837235E-07 3.9318239E-07 2.9822655E-07 2.2620309E-07 1.7157372E-07 1.3013766E-07 9.8708655E-08 1.0285083E-05 7.8011756E-06 5.9171460E-06 4.4881206E-06 3.4042132E-06 2.5820758E-06 1.9584894E-06 1.4855027E-06 1.1267451E-06 8.5462960E-07 6.4823155E-07 4.9167984E-07 3.7293628E-07 2.8286998E-07 2.1455523E-07 1.6273889E-07 1.2343649E-07 9.3625857E-08 7.1014665E-08 5.3864207E-08 4.0855686E-08 3.0988799E-08 2.3504823E-08 1.7828270E-08 1.3522639E-08 7.1611734E-05 5.4317081E-05 4.1199188E-05 3.1249343E-05 2.3702444E-05 1.7978165E-05 1.3636333E-05 1.0343079E-05 7.8451647E-06 5.9505115E-06 4.5134282E-06 3.4234089E-06 2.5966356E-06 1.9695329E-06 1.4938792E-06 1.1330986E-06 8.5944867E-07 6.5188679E-07 4.9445231E-07 3.7503919E-07 2.8446503E-07 2.1576506E-07 1.6365653E-07 1.2413252E-07 9.4153793E-08 6.5174061E-05 4.9434144E-05 3.7495509E-05 2.8440124E-05 2.1571668E-05 1.6361984E-05 1.2410469E-05 9.4132681E-06 7.1399087E-06 5.4155790E-06 4.1076850E-06 3.1156550E-06 2.3632061E-06 1.7924780E-06 1.3595841E-06 1.0312366E-06 7.8218690E-07 5.9328419E-07 4.5000258E-07 3.4132433E-07 2.5889250E-07 1.9636845E-07 1.4894432E-07 1.1297339E-07 8.5689659E-08 2.8906642E-05 2.1925519E-05 1.6630378E-05 1.2614044E-05 9.5676787E-06 7.2570283E-06 5.5044135E-06 4.1750654E-06 3.1667627E-06 2.4019710E-06 1.8218809E-06 1.3818860E-06 1.0481525E-06 7.9501751E-07 6.0301613E-07 4.5738420E-07 3.4692324E-07 2.6313925E-07 1.9958958E-07 1.5138753E-07 1.1482655E-07 8.7095270E-08 6.6061252E-08 5.0107073E-08 3.8005922E-08
                </occurRates>
                <lengths>
                    25
                </lengths>
            </multiMFD>
            <nodalPlaneDist>
                <nodalPlane dip="9.0000000E+01" probability="1.0000000E+00" rake="0.0000000E+00" strike="2.7000000E+02"/>
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth depth="5.0000000E+00" probability="7.0000000E-02"/>
                <hypoDepth depth="1.5000000E+01" probability="2.4000000E-01"/>
                <hypoDepth depth="2.5000000E+01" probability="1.2000000E-01"/>
                <hypoDepth depth="3.5000000E+01" probability="5.7000000E-01"/>
            </hypoDepthDist>
        </multiPointSource>
    </sourceGroup>
</nrml>
'''

manymultipoint = '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.5"
xmlns:gml="http://www.opengis.net/gml"
>
    <sourceGroup
    rup_interdep="indep"
    src_interdep="indep"
    tectonicRegion="Subduction IntraSlab"
    >
        <multiPointSource
        id="mps-0"
        name="multiPointSource-0"
        >
            <multiPointGeometry>
                <gml:posList>
                    1.5124125E+02 -6.4315600E+00 1.5124125E+02 -6.4315600E+00 1.5055269E+02 -6.7489500E+00
                </gml:posList>
                <upperSeismoDepth>
                    1.0000000E+01
                </upperSeismoDepth>
                <lowerSeismoDepth>
                    4.2300000E+01
                </lowerSeismoDepth>
            </multiPointGeometry>
            <magScaleRel>
                StrasserIntraslab
            </magScaleRel>
            <ruptAspectRatio>
                1.0000000E+00
            </ruptAspectRatio>
            <multiMFD
            kind="incrementalMFD"
            size="3"
            >
                <min_mag>
                    5.1000000E+00
                </min_mag>
                <bin_width>
                    2.0000000E-01
                </bin_width>
                <occurRates>
                    9.1484712E-05 5.1416486E-05 2.8897233E-05 1.6240901E-05 9.1277553E-06 5.1300058E-06 2.8831798E-06 1.6204125E-06 9.1070864E-07 5.1183894E-07 2.8766511E-07 1.6167432E-07 9.0864642E-08 5.1067993E-08 1.6403767E-08 3.9207734E-05 2.2035637E-05 1.2384528E-05 6.9603862E-06 3.9118951E-06 2.1985739E-06 1.2356485E-06 6.9446251E-07 3.9030370E-07 2.1935955E-07 1.2328505E-07 6.9288996E-08 3.8941990E-08 2.1886283E-08 7.0301859E-09 9.1484712E-05 5.1416486E-05 2.8897233E-05 1.6240901E-05 9.1277553E-06 5.1300058E-06 2.8831798E-06 1.6204125E-06 9.1070864E-07 5.1183894E-07 2.8766511E-07 1.6167432E-07 9.0864642E-08 5.1067993E-08 1.6403767E-08
                </occurRates>
                <lengths>
                    15
                </lengths>
            </multiMFD>
            <nodalPlaneDist>
                <nodalPlane dip="3.0600000E+01" probability="7.0000000E-01" rake="9.0000000E+01" strike="2.4720000E+02"/>
                <nodalPlane dip="3.0600000E+01" probability="3.0000000E-01" rake="-9.0000000E+01" strike="2.4720000E+02"/>
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth depth="3.3642197E+01" probability="1.0000000E+00"/>
            </hypoDepthDist>
        </multiPointSource>
        <multiPointSource
        id="mps-1"
        name="multiPointSource-1"
        >
            <multiPointGeometry>
                <gml:posList>
                    1.5124837E+02 -6.3836000E+00 1.5124837E+02 -6.3836000E+00 1.5055982E+02 -6.7009800E+00 1.5055982E+02 -6.7009800E+00
                </gml:posList>
                <upperSeismoDepth>
                    1.0000000E+01
                </upperSeismoDepth>
                <lowerSeismoDepth>
                    4.6000000E+01
                </lowerSeismoDepth>
            </multiPointGeometry>
            <magScaleRel>
                StrasserIntraslab
            </magScaleRel>
            <ruptAspectRatio>
                1.0000000E+00
            </ruptAspectRatio>
            <multiMFD
            kind="incrementalMFD"
            size="4"
            >
                <min_mag>
                    5.1000000E+00
                </min_mag>
                <bin_width>
                    2.0000000E-01
                </bin_width>
                <occurRates>
                    9.1484712E-05 5.1416486E-05 2.8897233E-05 1.6240901E-05 9.1277553E-06 5.1300058E-06 2.8831798E-06 1.6204125E-06 9.1070864E-07 5.1183894E-07 2.8766511E-07 1.6167432E-07 9.0864642E-08 5.1067993E-08 1.6403767E-08 3.9207734E-05 2.2035637E-05 1.2384528E-05 6.9603862E-06 3.9118951E-06 2.1985739E-06 1.2356485E-06 6.9446251E-07 3.9030370E-07 2.1935955E-07 1.2328505E-07 6.9288996E-08 3.8941990E-08 2.1886283E-08 7.0301859E-09 9.1484712E-05 5.1416486E-05 2.8897233E-05 1.6240901E-05 9.1277553E-06 5.1300058E-06 2.8831798E-06 1.6204125E-06 9.1070864E-07 5.1183894E-07 2.8766511E-07 1.6167432E-07 9.0864642E-08 5.1067993E-08 1.6403767E-08 3.9207734E-05 2.2035637E-05 1.2384528E-05 6.9603862E-06 3.9118951E-06 2.1985739E-06 1.2356485E-06 6.9446251E-07 3.9030370E-07 2.1935955E-07 1.2328505E-07 6.9288996E-08 3.8941990E-08 2.1886283E-08 7.0301859E-09
                </occurRates>
                <lengths>
                    15
                </lengths>
            </multiMFD>
            <nodalPlaneDist>
                <nodalPlane dip="3.0600000E+01" probability="7.0000000E-01" rake="9.0000000E+01" strike="2.4720000E+02"/>
                <nodalPlane dip="3.0600000E+01" probability="3.0000000E-01" rake="-9.0000000E+01" strike="2.4720000E+02"/>
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth depth="2.7731648E+01" probability="1.0000000E+00"/>
            </hypoDepthDist>
        </multiPointSource>
        <multiPointSource
        id="mps-2"
        name="multiPointSource-2"
        >
            <multiPointGeometry>
                <gml:posList>
                    1.5057406E+02 -6.6050500E+00 1.5057406E+02 -6.6050500E+00
                </gml:posList>
                <upperSeismoDepth>
                    1.0000000E+01
                </upperSeismoDepth>
                <lowerSeismoDepth>
                    5.6500000E+01
                </lowerSeismoDepth>
            </multiPointGeometry>
            <magScaleRel>
                StrasserIntraslab
            </magScaleRel>
            <ruptAspectRatio>
                1.0000000E+00
            </ruptAspectRatio>
            <multiMFD
            kind="incrementalMFD"
            size="2"
            >
                <min_mag>
                    5.1000000E+00
                </min_mag>
                <bin_width>
                    2.0000000E-01
                </bin_width>
                <occurRates>
                    9.1484712E-05 5.1416486E-05 2.8897233E-05 1.6240901E-05 9.1277553E-06 5.1300058E-06 2.8831798E-06 1.6204125E-06 9.1070864E-07 5.1183894E-07 2.8766511E-07 1.6167432E-07 9.0864642E-08 5.1067993E-08 1.6403767E-08 3.9207734E-05 2.2035637E-05 1.2384528E-05 6.9603862E-06 3.9118951E-06 2.1985739E-06 1.2356485E-06 6.9446251E-07 3.9030370E-07 2.1935955E-07 1.2328505E-07 6.9288996E-08 3.8941990E-08 2.1886283E-08 7.0301859E-09
                </occurRates>
                <lengths>
                    15
                </lengths>
            </multiMFD>
            <nodalPlaneDist>
                <nodalPlane dip="3.0600000E+01" probability="7.0000000E-01" rake="9.0000000E+01" strike="2.4720000E+02"/>
                <nodalPlane dip="3.0600000E+01" probability="3.0000000E-01" rake="-9.0000000E+01" strike="2.4720000E+02"/>
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth depth="1.5910549E+01" probability="1.0000000E+00"/>
            </hypoDepthDist>
        </multiPointSource>
        <multiPointSource
        id="mps-3"
        name="multiPointSource-3"
        >
            <multiPointGeometry>
                <gml:posList>
                    1.5126260E+02 -6.2876600E+00 1.5126260E+02 -6.2876600E+00
                </gml:posList>
                <upperSeismoDepth>
                    1.0000000E+01
                </upperSeismoDepth>
                <lowerSeismoDepth>
                    5.7900000E+01
                </lowerSeismoDepth>
            </multiPointGeometry>
            <magScaleRel>
                StrasserIntraslab
            </magScaleRel>
            <ruptAspectRatio>
                1.0000000E+00
            </ruptAspectRatio>
            <multiMFD
            kind="incrementalMFD"
            size="2"
            >
                <min_mag>
                    5.1000000E+00
                </min_mag>
                <bin_width>
                    2.0000000E-01
                </bin_width>
                <occurRates>
                    9.1484712E-05 5.1416486E-05 2.8897233E-05 1.6240901E-05 9.1277553E-06 5.1300058E-06 2.8831798E-06 1.6204125E-06 9.1070864E-07 5.1183894E-07 2.8766511E-07 1.6167432E-07 9.0864642E-08 5.1067993E-08 1.6403767E-08 3.9207734E-05 2.2035637E-05 1.2384528E-05 6.9603862E-06 3.9118951E-06 2.1985739E-06 1.2356485E-06 6.9446251E-07 3.9030370E-07 2.1935955E-07 1.2328505E-07 6.9288996E-08 3.8941990E-08 2.1886283E-08 7.0301859E-09
                </occurRates>
                <lengths>
                    15
                </lengths>
            </multiMFD>
            <nodalPlaneDist>
                <nodalPlane dip="3.0600000E+01" probability="7.0000000E-01" rake="9.0000000E+01" strike="2.4720000E+02"/>
                <nodalPlane dip="3.0600000E+01" probability="3.0000000E-01" rake="-9.0000000E+01" strike="2.4720000E+02"/>
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth depth="1.5910549E+01" probability="1.0000000E+00"/>
            </hypoDepthDist>
        </multiPointSource>
    </sourceGroup>
</nrml>
'''

class PointToMultiPointTestCase(unittest.TestCase):
    def test_simple(self):
        testfile = os.path.join(testdir, 'two-point-sources.xml')
        sm = nrml.read(testfile).sourceModel
        update_source_model(sm, testfile)
        with io.BytesIO() as f:
            nrml.write(sm, f)
            got = f.getvalue().decode('utf-8')
            self.assertEqual(got, expected)

    def test_complex(self):
        testfile = os.path.normpath(os.path.join(
            testdir, '../../../qa_tests_data/logictree/case_30/ssm/shallow/'
            'gridded_seismicity_source_4.xml'))
        sm = nrml.read(testfile).sourceModel
        update_source_model(sm, testfile)
        with io.BytesIO() as f:
            nrml.write(sm, f)
            got = f.getvalue().decode('utf-8')
            self.assertEqual(got, multipoint)

    def test_many_lsd(self):
        testfile = os.path.join(testdir, 'points.xml')
        sm = nrml.read(testfile).sourceModel
        update_source_model(sm, testfile)
        with io.BytesIO() as f:
            nrml.write(sm, f)
            got = f.getvalue().decode('utf-8')
            self.assertEqual(got, manymultipoint)


class SourceConverterTestCase(unittest.TestCase):

    def test_wrong_trt(self):
        """ Test consistency between group and sources TRTs """
        testfile = os.path.join(testdir, 'wrong-trt.xml')
        with self.assertRaises(ValueError) as ctx:
            nrml.to_python(testfile)
        self.assertIn('node pointSource: Found Cratonic, expected '
                      'Active Shallow Crust, line 67', str(ctx.exception))

    def test_tom_poisson_not_defined(self):
        """ Read area source without tom """
        testfile = os.path.join(testdir, 'area-source.xml')
        sc = SourceConverter(area_source_discretization=10.)
        sg = nrml.to_python(testfile, sc)
        src = sg[0].sources[0]
        self.assertEqual(src.temporal_occurrence_model.time_span, 50,
                         "Wrong time span in the temporal occurrence model")

    def test_tom_poisson_no_rate(self):
        testfile = os.path.join(testdir, 'tom_poisson_no_rate.xml')
        sc = SourceConverter(area_source_discretization=10.)
        sg = nrml.to_python(testfile, sc)
        src = sg[0].sources[0]
        msg = "Wrong time span in the temporal occurrence model"
        self.assertEqual(src.temporal_occurrence_model.time_span, 50, msg)

    def test_wrong_source_type(self):
        """ Test that only nonparametric sources are used with mutex ruptures
        """
        testfile = os.path.join(testdir, 'rupture_mutex_wrong.xml')
        with self.assertRaises(ValueError):
            nrml.to_python(testfile)

    def test_non_parametric_mutex(self):
        """ Test non-parametric source with mutex ruptures """
        fname = 'nonparametric-source-mutex-ruptures.xml'
        testfile = os.path.join(testdir, fname)
        grp = nrml.to_python(testfile)[0]
        src = grp[0]
        expected = numpy.array([0.2, 0.8])
        computed = numpy.array([src.data[0][0].weight, src.data[1][0].weight])
        numpy.testing.assert_equal(computed, expected)

    def test_tom_poisson_with_rate(self):
        testfile = os.path.join(testdir, 'tom_poisson_with_rate.xml')
        sc = SourceConverter(area_source_discretization=10.)
        sg = nrml.to_python(testfile, sc)
        src = sg[0].sources[0]
        msg = "Wrong time span in the temporal occurrence model"
        self.assertEqual(src.temporal_occurrence_model.time_span, 50, msg)
        msg = "Wrong occurrence rate in the temporal occurrence model"
        self.assertEqual(src.temporal_occurrence_model.occurrence_rate,
                         0.01, msg)

    def test_source_group_with_tom(self):
        testfile = os.path.join(testdir, 'source_group_with_tom.xml')
        sc = SourceConverter(area_source_discretization=10.)
        sg = nrml.to_python(testfile, sc)
        msg = "Wrong occurrence rate in the temporal occurrence model"
        expected = sg[0].temporal_occurrence_model.occurrence_rate
        self.assertEqual(expected, 0.01, msg)
        msg = "Wrong cluster definition"
        self.assertEqual(sg[0].cluster, False, msg)

    def test_source_group_cluster(self):
        testfile = os.path.join(testdir, 'source_group_cluster.xml')
        sc = SourceConverter(area_source_discretization=10.)
        sg = nrml.to_python(testfile, sc)
        msg = "Wrong cluster definition"
        self.assertEqual(sg[0].cluster, True, msg)

    def test_dupl_values_npdist(self):
        testfile = os.path.join(testdir, 'wrong-npdist.xml')
        with unittest.mock.patch('logging.info') as w:
            nrml.to_python(testfile)
        self.assertEqual(
            'There were repeated values %s in %s:%s', w.call_args[0][0])

    def test_dupl_values_hddist(self):
        testfile = os.path.join(testdir, 'wrong-hddist.xml')
        with unittest.mock.patch('logging.info') as w:
            nrml.to_python(testfile)
        self.assertEqual(
            'There were repeated values %s in %s:%s', w.call_args[0][0])

    def test_mfd_with_slip_rate(self):
        testfile = os.path.join(testdir, 'source_with_slip_rate.xml')
        src = nrml.to_python(testfile).src_groups[0][0]
        self.assertAlmostEqual(src.mfd.a_val, 3.9720437839539255)


class MultiFaultSourceModelTestCase(unittest.TestCase):
    """ Tests reading a multi fault model """

    def test_load_mfs(self):
        datadir = os.path.join(os.path.dirname(__file__), 'data', 'sections')
        sec_xml = os.path.join(datadir, 'sections_kite.xml')
        src_xml = os.path.join(datadir, 'sources.xml')
        conv = SourceConverter()
        sec = nrml.to_python(sec_xml, conv).sections  # s1 and s2
        expected = [Point(11, 45, 0), Point(11, 45.5, 10)]
        # Check geometry info
        self.assertEqual(expected[0], sec['s2'].profiles[0].points[0])
        self.assertEqual(expected[1], sec['s2'].profiles[0].points[1])
        ssm = nrml.to_python(src_xml, conv)
        self.assertIsInstance(ssm, nrml.SourceModel)
