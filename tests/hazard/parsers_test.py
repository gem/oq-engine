# Copyright (c) 2010-2013, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.


import StringIO
import decimal
import os
import tempfile
import unittest

from lxml import etree

from openquake.nrmllib import models

from tests import _utils
from openquake.nrmllib.hazard import parsers
from openquake.nrmllib.hazard import writers


class SourceModelParserTestCase(unittest.TestCase):
    """
    Tests for the :class:`openquake.nrmllib.parsers.SourceModelParser`
    parser.
    """

    SAMPLE_FILE = 'examples/source_model/mixed.xml'
    BAD_NAMESPACE = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.3">
</nrml>'''

    # The NRML element should be first
    NO_NRML_ELEM_FIRST = '''\
m?ml version='1.0' encoding='utf-8'?>
<sourceModel xmlns="http://openquake.org/xmlns/nrml/0.4" name="test">
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
</nrml>
</sourceModel>'''

    INVALID_SCHEMA = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <sourceModel name="Some Source Model">
        <pointSource id="1" name="point"
         tectonicRegion="Stable Continental Crust">
            <pointGeometry>
                <gml:Point>
                    <gml:pos>-122.0 38.0</gml:pos>
                </gml:Point>
                <upperSeismoDepth>0.0</upperSeismoDepth>
                <lowerSeismoDepth>10.0</lowerSeismoDepth>
            </pointGeometry>
            <magScaleRel>WC1994</magScaleRel>
            <ruptAspectRatio>0.5</ruptAspectRatio>
            <truncGutenbergRichterMFD aValue="-3.5" invalidAttr="foo" bValue="1.0" minMag="5.0" maxMag="6.5" />
            <nodalPlaneDist>
                <nodalPlane probability="0.3" strike="0.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.7" strike="90.0" dip="45.0" rake="90.0" />
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth probability="0.5" depth="4.0" />
                <hypoDepth probability="0.5" depth="8.0" />
            </hypoDepthDist>
        </pointSource>
    </sourceModel>
</nrml>'''

    @classmethod
    def _expected_source_model(cls):
        # Area:
        area_geom = models.AreaGeometry(
            wkt=('POLYGON((-122.5 37.5, -121.5 37.5, -121.5 38.5, -122.5 38.5,'
                 ' -122.5 37.5))'),
            upper_seismo_depth=0.0, lower_seismo_depth=10.0,
        )
        area_mfd = models.IncrementalMFD(
            min_mag=6.55, bin_width=0.1,
            occur_rates=[0.0010614989, 8.8291627E-4, 7.3437777E-4, 6.108288E-4,
                         5.080653E-4],
        )
        area_npd = [
            models.NodalPlane(probability=decimal.Decimal("0.3"), strike=0.0,
                              dip=90.0, rake=0.0),
            models.NodalPlane(probability=decimal.Decimal("0.7"), strike=90.0,
                              dip=45.0, rake=90.0),
        ]
        area_hdd = [
            models.HypocentralDepth(probability=decimal.Decimal("0.5"),
                                    depth=4.0),
            models.HypocentralDepth(probability=decimal.Decimal("0.5"),
                                    depth=8.0),
        ]
        area_src = models.AreaSource(
            id='1', name='Quito', trt='Active Shallow Crust',
            geometry=area_geom, mag_scale_rel='PeerMSR',
            rupt_aspect_ratio=1.5, mfd=area_mfd, nodal_plane_dist=area_npd,
            hypo_depth_dist=area_hdd,
        )

        # Point:
        point_geom = models.PointGeometry(
            wkt='POINT(-122.0 38.0)', upper_seismo_depth=0.0,
            lower_seismo_depth=10.0,
        )
        point_mfd = models.TGRMFD(
            a_val=-3.5, b_val=1.0, min_mag=5.0, max_mag=6.5,
        )
        point_npd = [
            models.NodalPlane(probability=decimal.Decimal("0.3"), strike=0.0,
                              dip=90.0, rake=0.0),
            models.NodalPlane(probability=decimal.Decimal("0.7"), strike=90.0,
                              dip=45.0, rake=90.0),
        ]
        point_hdd = [
            models.HypocentralDepth(probability=decimal.Decimal("0.5"),
                                    depth=4.0),
            models.HypocentralDepth(probability=decimal.Decimal("0.5"),
                                    depth=8.0),
        ]
        point_src = models.PointSource(
            id='2', name='point', trt='Stable Continental Crust',
            geometry=point_geom, mag_scale_rel='WC1994', rupt_aspect_ratio=0.5,
            mfd=point_mfd, nodal_plane_dist=point_npd,
            hypo_depth_dist=point_hdd,
        )

        # Simple:
        simple_geom = models.SimpleFaultGeometry(
            wkt='LINESTRING(-121.82290 37.73010, -122.03880 37.87710)',
            dip=45.0, upper_seismo_depth=10.0, lower_seismo_depth=20.0,
        )
        simple_mfd = models.IncrementalMFD(
            min_mag=5.0, bin_width=0.1,
            occur_rates=[0.0010614989, 8.8291627E-4, 7.3437777E-4, 6.108288E-4,
                         5.080653E-4],
        )
        simple_src = models.SimpleFaultSource(
            id='3', name='Mount Diablo Thrust', trt='Active Shallow Crust',
            geometry=simple_geom, mag_scale_rel='WC1994',
            rupt_aspect_ratio=1.5, mfd=simple_mfd, rake=30.0,
        )

        # Complex:
        complex_geom = models.ComplexFaultGeometry(
            top_edge_wkt=(
                'LINESTRING(-124.704 40.363 0.5493260E+01, '
                '-124.977 41.214 0.4988560E+01, '
                '-125.140 42.096 0.4897340E+01)'),
            bottom_edge_wkt=(
                'LINESTRING(-123.829 40.347 0.2038490E+02, '
                '-124.137 41.218 0.1741390E+02, '
                '-124.252 42.115 0.1752740E+02)'),
            int_edges=[
                ('LINESTRING(-124.704 40.363 0.5593260E+01, '
                 '-124.977 41.214 0.5088560E+01, '
                 '-125.140 42.096 0.4997340E+01)'),
                ('LINESTRING(-124.704 40.363 0.5693260E+01, '
                 '-124.977 41.214 0.5188560E+01, '
                 '-125.140 42.096 0.5097340E+01)'),
            ]
        )
        complex_mfd = models.TGRMFD(
            a_val=-3.5, b_val=1.0, min_mag=5.0, max_mag=6.5)
        complex_src = models.ComplexFaultSource(
            id='4', name='Cascadia Megathrust', trt='Subduction Interface',
            geometry=complex_geom, mag_scale_rel='WC1994',
            rupt_aspect_ratio=2.0, mfd=complex_mfd, rake=30.0,
        )

        # 3 Characteristic Sources:
        char_src_simple = models.CharacteristicSource(
            id='5', name='characteristic source, simple fault', trt='Volcanic',
            mfd=models.TGRMFD(a_val=-3.5, b_val=1.0, min_mag=5.0, max_mag=6.5),
            rake=30.0,
            surface=simple_geom
        )

        char_src_complex = models.CharacteristicSource(
            id='6', name='characteristic source, complex fault',
            trt='Volcanic',
            mfd=models.IncrementalMFD(
                min_mag=5.0, bin_width=0.1,
                occur_rates=[0.0010614989, 8.8291627E-4, 7.3437777E-4,
                             6.108288E-4, 5.080653E-4],
            ),
            rake=60.0,
            surface=complex_geom
        )

        char_src_multi = models.CharacteristicSource(
            id='7', name='characteristic source, multi surface',
            trt='Volcanic',
            mfd=models.TGRMFD(a_val=-3.6, b_val=1.0, min_mag=5.2, max_mag=6.4),
            rake=90.0
        )
        psurface_1 = models.PlanarSurface(
            strike=0.0, dip=90.0,
            top_left=models.Point(longitude=-1.0, latitude=1.0, depth=21.0),
            top_right=models.Point(longitude=1.0, latitude=1.0, depth=21.0),
            bottom_left=models.Point(longitude=-1.0, latitude=-1.0,
                                     depth=59.0),
            bottom_right=models.Point(longitude=1.0, latitude=-1.0,
                                      depth=59.0),
        )
        psurface_2 = models.PlanarSurface(
            strike=20.0, dip=45.0,
            top_left=models.Point(longitude=1.0, latitude=1.0, depth=20.0),
            top_right=models.Point(longitude=3.0, latitude=1.0, depth=20.0),
            bottom_left=models.Point(longitude=1.0, latitude=-1.0, depth=80.0),
            bottom_right=models.Point(longitude=3.0, latitude=-1.0,
                                      depth=80.0),
        )
        char_src_multi.surface = [psurface_1, psurface_2]

        source_model = models.SourceModel()
        source_model.name = 'Some Source Model'
        # Generator:
        source_model.sources = (
            x for x in [area_src, point_src, simple_src, complex_src,
                        char_src_simple, char_src_complex, char_src_multi]
        )
        return source_model

    def test_wrong_namespace(self):
        parser = parsers.SourceModelParser(
            StringIO.StringIO(self.BAD_NAMESPACE))

        self.assertRaises(etree.XMLSyntaxError, parser.parse)

    def test_nrml_elem_not_found(self):
        parser = parsers.SourceModelParser(
            StringIO.StringIO(self.NO_NRML_ELEM_FIRST))

        self.assertRaises(etree.XMLSyntaxError, parser.parse)

    def test_invalid_schema(self):
        parser = parsers.SourceModelParser(
            StringIO.StringIO(self.INVALID_SCHEMA))

        self.assertRaises(etree.XMLSyntaxError, parser.parse)

    def test_parse(self):
        parser = parsers.SourceModelParser(self.SAMPLE_FILE)

        exp_src_model = self._expected_source_model()
        src_model = parser.parse()

        self.assertTrue(*_utils.deep_eq(exp_src_model, src_model))

    def test_probs_sum_to_1(self):
        # We want to test that distribution probabilities sum to 1.
        # Example source model with an area and a point source.
        source_xml = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <sourceModel name="Some Source Model">
        <areaSource id="1" name="Quito" tectonicRegion="Active Shallow Crust">
            <areaGeometry>
                <gml:Polygon>
                    <gml:exterior>
                        <gml:LinearRing>
                            <gml:posList>
                             -122.5 37.5
                             -121.5 37.5
                             -121.5 38.5
                             -122.5 38.5
                            </gml:posList>
                        </gml:LinearRing>
                    </gml:exterior>
                </gml:Polygon>
                <upperSeismoDepth>0.0</upperSeismoDepth>
                <lowerSeismoDepth>10.0</lowerSeismoDepth>
            </areaGeometry>
            <magScaleRel>PeerMSR</magScaleRel>
            <ruptAspectRatio>1.5</ruptAspectRatio>
            <incrementalMFD minMag="6.55" binWidth="0.1">
                <occurRates>0.0010614989 8.8291627E-4 7.3437777E-4
                6.108288E-4 5.080653E-4</occurRates>
            </incrementalMFD>
            <nodalPlaneDist>
                <nodalPlane probability="0.1" strike="1.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.1" strike="2.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.1" strike="3.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.1" strike="4.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.1" strike="5.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.1" strike="6.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.1" strike="7.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.1" strike="8.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.1" strike="9.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.1" strike="10.0" dip="90.0" rake="0.0" />
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth probability="0.3" depth="4.0" />
                <hypoDepth probability="0.3" depth="5.0" />
                <hypoDepth probability="0.3" depth="6.0" />
                <hypoDepth probability="0.1" depth="7.0" />
            </hypoDepthDist>
        </areaSource>
        <pointSource id="2" name="point"
                     tectonicRegion="Stable Continental Crust">
            <pointGeometry>
                <gml:Point>
                    <gml:pos>-122.0 38.0</gml:pos>
                </gml:Point>
                <upperSeismoDepth>0.0</upperSeismoDepth>
                <lowerSeismoDepth>10.0</lowerSeismoDepth>
            </pointGeometry>
            <magScaleRel>WC1994</magScaleRel>
            <ruptAspectRatio>0.5</ruptAspectRatio>
            <truncGutenbergRichterMFD aValue="-3.5"
             bValue="1.0" minMag="5.0" maxMag="6.5" />
            <nodalPlaneDist>
                <nodalPlane probability="0.3" strike="0.0"
                            dip="90.0" rake="0.0" />
                <nodalPlane probability="0.7" strike="90.0"
                            dip="45.0" rake="90.0" />
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth probability="0.5" depth="4.0" />
                <hypoDepth probability="0.5" depth="8.0" />
            </hypoDepthDist>
        </pointSource>
    </sourceModel>
</nrml>'''
        parser = parsers.SourceModelParser(StringIO.StringIO(source_xml))

        src_model = list(parser.parse())

        for src in src_model:
            self.assertEqual(
                1.0, sum([x.probability for x in src.hypo_depth_dist]))
            self.assertEqual(
                1.0, sum([x.probability for x in src.nodal_plane_dist]))


class SiteModelParserTestCase(unittest.TestCase):
    """Tests for :class:`parsers.SiteModelParser`."""

    SAMPLE_FILE = 'examples/site_model.xml'

    INVALID_SCHEMA = '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.3">
    <siteModel>
        <site lon="-122.5" lat="37.5" vs30="800.0" vs30Type="measured" z1pt0="100.0" z2pt5="5.0" />
        <site lon="-122.6" lat="37.6" vs30="801.0" vs30Type="measured" z1pt0="101.0" z2pt5="5.1" />
        <site lon="-122.7" lat="37.7" vs30="802.0" vs30Type="measured" z1pt0="102.0" z2pt5="5.2" />
        <site lon="-122.8" lat="37.8" vs30="803.0" vs30Type="measured" z1pt0="103.0" z2pt5="5.3" />
        <site lon="-122.9" lat="37.9" vs30="804.0" vs30Type="measured" z1pt0="104.0" z2pt5="5.4" />
    </siteModel>
</nrml>'''

    def test_invalid_schema(self):
        parser = parsers.SiteModelParser(
            StringIO.StringIO(self.INVALID_SCHEMA))

        # parser.parse() is a generator
        # parsing is lazy, hence the call to `list`
        self.assertRaises(etree.XMLSyntaxError, list, parser.parse())

    def test_parse(self):
        expected_raw = [
            {'z2pt5': 5.0, 'z1pt0': 100.0, 'vs30': 800.0,
             'wkt': 'POINT(-122.5 37.5)', 'vs30_type': 'measured'},
            {'z2pt5': 5.1, 'z1pt0': 101.0, 'vs30': 801.0,
             'wkt': 'POINT(-122.6 37.6)', 'vs30_type': 'measured'},
            {'z2pt5': 5.2, 'z1pt0': 102.0, 'vs30': 802.0,
             'wkt': 'POINT(-122.7 37.7)', 'vs30_type': 'measured'},
            {'z2pt5': 5.3, 'z1pt0': 103.0, 'vs30': 803.0,
             'wkt': 'POINT(-122.8 37.8)', 'vs30_type': 'measured'},
            {'z2pt5': 5.4, 'z1pt0': 104.0, 'vs30': 804.0,
             'wkt': 'POINT(-122.9 37.9)', 'vs30_type': 'measured'},
        ]
        expected = [models.SiteModel(**x) for x in expected_raw]

        parser = parsers.SiteModelParser(self.SAMPLE_FILE)
        actual = [x for x in parser.parse()]

        self.assertTrue(*_utils.deep_eq(expected, actual))


class RuptureModelParserTestCase(unittest.TestCase):
    SAMPLE_FILES = ['examples/simple-fault-rupture.xml',
                    'examples/complex-fault-rupture.xml']

    EXPECTED_MODELS = [
        models.SimpleFaultRuptureModel(
            magnitude=7.65,
            rake=15.0,
            hypocenter=[0.0, 0.0, 15.0],
            geometry=models.SimpleFaultGeometry(
                wkt='LINESTRING(-124.704 40.363, -124.977 41.214, -125.140 42.096)',
                dip=50.0,
                upper_seismo_depth=12.5,
                lower_seismo_depth=19.5)),

        models.ComplexFaultRuptureModel(
            magnitude=9.0,
            rake=0.0,
            hypocenter=[-124.977, 41.214, 0.5088560E+01],
            geometry=models.ComplexFaultGeometry(
                top_edge_wkt='LINESTRING(-124.704 40.363 0.5493260E+01, -124.977 41.214 0.4988560E+01, -125.140 42.096 0.4897340E+01)',
                bottom_edge_wkt='LINESTRING(-123.829 40.347 0.2038490E+02, -124.137 41.218 0.1741390E+02, -124.252 42.115 0.1752740E+02)',
                int_edges=['LINESTRING(-124.704 40.363 0.5593260E+01, -124.977 41.214 0.5088560E+01, -125.140 42.096 0.4997340E+01)', 'LINESTRING(-124.704 40.363 0.5693260E+01, -124.977 41.214 0.5188560E+01, -125.140 42.096 0.5097340E+01)']
                )),
        ]

    INVALID_1 = '''<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">

    <simpeFaultRupture>
        <magnitude type="Mw">7.65</magnitude>
        <rake>15.0</rake>

        <simpleFaultGeometry>
            <faultTrace>
                <gml:LineString srsName="urn:ogc:def:crs:EPSG::4326">
                    <gml:posList>
                        -124.704 40.363 0.1
                        -124.977 41.214 0.1
                        -125.140 42.096 0.1
                    </gml:posList>
                </gml:LineString>
            </faultTrace>
            <dip>50.0</dip>
            <upperSeismoDepth>12.5</upperSeismoDepth>
            <lowerSeismoDepth>19.5</lowerSeismoDepth>
        </simpleFaultGeometry>
    </simpleFaultRupture>
</nrml>
'''  # there is a mispelled simpeFaultRupture here

    INVALID_2 = '''<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">

    <bcrMap sourceModelTreePath="b1|b2" gsimTreePath="b1|b2"
            lossCategory="economic_loss" unit="EUR" interestRate="1.0"
            assetLifeExpectancy="20">

        <node>
            <gml:Point>
                <gml:pos>-116.0 41.0</gml:pos>
            </gml:Point>

            <bcr assetRef="asset_1" ratio="15.23" aalOrig="1.1" aalRetr="1.0" />
            <bcr assetRef="asset_2" ratio="25.23" aalOrig="2.1" aalRetr="2.0" />
        </node>

        <node>
            <gml:Point>
                <gml:pos>-116.0 42.0</gml:pos>
            </gml:Point>

            <bcr assetRef="asset_3" ratio="64.23" aalOrig="2.1" aalRetr="2.0" />
        </node>
    </bcrMap>
</nrml>
'''  # you are trying to parse a bcrMap with a RuptureParser!

    def test_parse(self):
        for fname, expected_model in zip(
                self.SAMPLE_FILES, self.EXPECTED_MODELS):
            parser = parsers.RuptureModelParser(fname)
            model = parser.parse()
            self.assertTrue(*_utils.deep_eq(model, expected_model))

    def test_invalid(self):
        inv1 = StringIO.StringIO(self.INVALID_1)
        self.assertRaises(etree.XMLSyntaxError,
                          parsers.RuptureModelParser(inv1).parse)

        inv2 = StringIO.StringIO(self.INVALID_2)
        self.assertRaises(ValueError,
                          parsers.RuptureModelParser(inv2).parse)


class GMFScenarioParserTestCase(unittest.TestCase):
    SAMPLE_FILE = 'examples/gmf-scenario.xml'
    EXPECTED = [
        ('SA(0.025)', '{0.2}', 'POINT(0.0 0.0)'),
        ('SA(0.025)', '{1.4}', 'POINT(1.0 0.0)'),
        ('SA(0.025)', '{0.6}', 'POINT(0.0 1.0)'),
        ('PGA', '{0.2,0.3}', 'POINT(0.0 0.0)'),
        ('PGA', '{1.4,1.5}', 'POINT(1.0 0.0)'),
        ('PGA', '{0.6,0.7}', 'POINT(0.0 1.0)'),
        ('PGV', '{0.2}', 'POINT(0.0 0.0)'),
        ('PGV', '{1.4}', 'POINT(1.0 0.0)'),
        ('PGV', '{0.6}', 'POINT(0.0 1.0)')]

    def test_parse(self):
        parser = parsers.GMFScenarioParser(self.SAMPLE_FILE)
        self.assertEqual(list(parser.parse()), self.EXPECTED)


class HazardCurveParserTestCase(unittest.TestCase):
    EXPECTED_CURVE_1 = models.HazardCurveData(
        models.Location(-122.5, 37.5), [9.8728e-01, 9.8266e-01, 9.4957e-01]
    )
    EXPECTED_CURVE_2 = models.HazardCurveData(
        models.Location(-123.5, 37.5), [9.8728e-02, 9.8266e-02, 9.4957e-02]
    )

    EXPECTED = {
        'examples/hazard-curves-pga.xml': models.HazardCurveModel(
            **{'imls': [0.005, 0.007, 0.0137],
               'imt': 'PGA',
               'investigation_time': '50.0',
               'quantile_value': None,
               'sa_damping': None,
               'sa_period': None,
               'statistics': None,
               'gsimlt_path': 'b1_b7',
               'smlt_path': 'b1_b2_b3',
               'data_iter': iter([EXPECTED_CURVE_1, EXPECTED_CURVE_2])}
        ),
        'examples/hazard-curves-sa.xml': models.HazardCurveModel(
            **{'imls': [0.005, 0.007, 0.0137],
               'imt': 'SA',
               'investigation_time': '50.0',
               'quantile_value': None,
               'sa_damping': '5.0',
               'sa_period': '0.025',
               'statistics': None,
               'gsimlt_path': 'b1_b2',
               'smlt_path': 'b1_b2_b4',
               'data_iter': iter([EXPECTED_CURVE_1, EXPECTED_CURVE_2])}
        ),
        'examples/hazard-curves-quantile.xml': models.HazardCurveModel(
            **{'imls': [0.005, 0.007, 0.0137],
               'imt': 'PGD',
               'investigation_time': '50.0',
               'quantile_value': '0.6',
               'sa_damping': None,
               'sa_period': None,
               'statistics': 'quantile',
               'gsimlt_path': None,
               'smlt_path': None,
               'data_iter': iter([EXPECTED_CURVE_1, EXPECTED_CURVE_2])}
        ),
        'examples/hazard-curves-mean.xml': models.HazardCurveModel(
            **{'imls': [0.005, 0.007, 0.0137],
               'imt': 'PGD',
               'investigation_time': '50.0',
               'quantile_value': None,
               'sa_damping': None,
               'sa_period': None,
               'statistics': 'mean',
               'gsimlt_path': None,
               'smlt_path': None,
               'data_iter': iter([EXPECTED_CURVE_1, EXPECTED_CURVE_2])}
        ),
    }

    def test_parse(self):
        for curve, expected in self.EXPECTED.iteritems():
            parser = parsers.HazardCurveXMLParser(curve)
            model = parser.parse()
            equal, err = _utils.deep_eq(expected, model)
            self.assertTrue(equal, err)

    def test_chain_parse_serialize(self):
        # Chain a parser together to with a serializer and test that the
        # produced XML is unchanged.
        for example in ('hazard-curves-mean.xml', 'hazard-curves-pga.xml',
                        'hazard-curves-quantile.xml', 'hazard-curves-sa.xml'):
            infile = os.path.join('tests/data', example)
            hcp = parsers.HazardCurveXMLParser(infile)
            parsed_model = hcp.parse()
            _, outfile = tempfile.mkstemp()
            try:
                hcw = writers.HazardCurveXMLWriter(
                    outfile, **parsed_model.metadata
                )
                hcw.serialize(parsed_model)

                _utils.assert_xml_equal(infile, outfile)
            finally:
                os.unlink(outfile)

    def test_geojson_parsing(self):
        # Test geojson parsing by comparing the
        # parsed values from the xml and geojson parsers.
        # The xml parser is already well tested, so this should
        # be sufficient.
        example_xml = [
            'examples/hazard-curves-pga.xml',
            'examples/hazard-curves-sa.xml',
            'examples/hazard-curves-quantile.xml',
            'examples/hazard-curves-mean.xml',
        ]
        example_geojson = [
            'examples/hazard-curves-pga.geojson',
            'examples/hazard-curves-sa.geojson',
            'examples/hazard-curves-quantile.geojson',
            'examples/hazard-curves-mean.geojson',
        ]
        for xml, geo in zip(example_xml, example_geojson):
            xp = parsers.HazardCurveXMLParser(xml)
            gp = parsers.HazardCurveGeoJSONParser(geo)

            equal, err = _utils.deep_eq(xp.parse(), gp.parse())
            self.assertTrue(equal, err)
