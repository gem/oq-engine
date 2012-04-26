# Copyright (c) 2010-2012, GEM Foundation.
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
import unittest

from nrml import exceptions
from nrml import models
from nrml import parsers


class SourceModelParserTestCase(unittest.TestCase):
    """Tests for the :class:`nrml.parsers.SourceModelParser` parser."""

    SAMPLE_FILE = 'nrml/schema/examples/source_model/mixed.xml'
    BAD_NAMESPACE = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.3"
      gml:id="n1">
</nrml>'''

    # The NRML element should be first
    NO_NRML_ELEM_FIRST = '''\
<?xml version='1.0' encoding='utf-8'?>
<sourceModel xmlns="http://openquake.org/xmlns/nrml/0.4" name="test">
    <nrml xmlns:gml="http://www.opengis.net/gml"
          xmlns="http://openquake.org/xmlns/nrml/0.3"
          gml:id="n1">
    </nrml>
</sourceModel>'''

    NO_SRC_MODEL = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4"
      gml:id="n1">
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
            models.NodalPlane(probability=0.3, strike=0.0, dip=90.0,
                              rake=0.0),
            models.NodalPlane(probability=0.7, strike=90.0, dip=45.0,
                              rake=90.0),
        ]
        area_hdd = [
            models.HypocentralDepth(probability=0.5, depth=4.0),
            models.HypocentralDepth(probability=0.5, depth=8.0),
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
            models.NodalPlane(probability=0.3, strike=0.0, dip=90.0,
                              rake=0.0),
            models.NodalPlane(probability=0.7, strike=90.0, dip=45.0,
                              rake=90.0),
        ]
        point_hdd = [
            models.HypocentralDepth(probability=0.5, depth=4.0),
            models.HypocentralDepth(probability=0.5, depth=8.0),
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
            min_mag=6.55, bin_width=0.1,
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
                'LINESTRING(-124.704  40.363  0.5493260E+01, '
                '-124.977  41.214  0.4988560E+01, '
                '-125.140  42.096  0.4897340E+01)'),
            bottom_edge_wkt=(
                'LINESTRING(-123.829  40.347  0.2038490E+02, '
                '-124.137  41.218  0.1741390E+02, '
                '-124.252  42.115  0.1752740E+02)'),
            int_edges=[
                ('LINESTRING(-124.704  40.363  0.5593260E+01, '
                 '-124.977  41.214  0.5088560E+01, '
                 '-125.140  42.096  0.4997340E+01)'),
                ('LINESTRING(-124.704  40.363  0.5693260E+01, ' 
                 '-124.977  41.214  0.5188560E+01, '
                 '-125.140  42.096  0.5097340E+01'),
            ]
        )
        complex_mfd = models.TGRMFD(
            a_val=-3.5, b_val=1.0, min_mag=5.0, max_mag=6.5)
        complex_src = models.ComplexFaultSource(
            id='4', name='Cascadia Megathrust', trt='Subduction Interface',
            geometry=complex_geom, mag_scale_rel='WC1994',
            rupt_aspect_ratio=2.0, mfd=complex_mfd, rake=30.0,
        )

        source_model = models.SourceModel()
        source_model.name = 'Some Source Model'
        # Generator:
        source_model.sources = (
            x for x in [area_src, point_src, simple_src, complex_src]
        )
        return source_model

    def test_wrong_namespace(self):
        test_file = StringIO.StringIO(self.BAD_NAMESPACE)

        parser = parsers.SourceModelParser(test_file)

        self.assertRaises(exceptions.UnexpectedNamespaceError, parser.parse)

    def test_nrml_elem_not_found(self):
        test_file = StringIO.StringIO(self.NO_NRML_ELEM_FIRST)

        parser = parsers.SourceModelParser(test_file)

        self.assertRaises(exceptions.UnexpectedElementError, parser.parse)

    def test_no_source_model_elem(self):
        test_file = StringIO.StringIO(self.NO_SRC_MODEL)

        parser = parsers.SourceModelParser(test_file)

        try:
            parser.parse()
        except exceptions.NrmlError, err:
            self.assertEqual('<sourceModel> element not found.', err.message)
        else:
            self.fail('NrmlError not raised.')

    def test_parse(self):
        parser = parsers.SourceModelParser(self.SAMPLE_FILE)

        exp_src_model = self._expected_source_model()
        src_model = parser.parse()

        self.assertEqual('Some Source Model', src_model.name)
