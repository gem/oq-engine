# coding=utf-8
# Copyright (c) 2010-2012, GEM Foundation.
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

import os
import unittest
import StringIO
import collections

from nrml.risk import writers
from tests import _utils


POINT = collections.namedtuple("Point", "x y")
LOSS_CURVE = collections.namedtuple(
    "LossCurve", "poes losses location asset_ref loss_ratios")


class LossCurveXMLWriterTestCase(unittest.TestCase):

    filename = "loss_curves.xml"

    def remove_file(self):
        try:
            os.remove(self.filename)
        except OSError:
            pass

    def setUp(self):
        self.remove_file()

    def tearDown(self):
        self.remove_file()

    def test_serialize_an_empty_model(self):
        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4"/>
""")

        writer = writers.LossCurveXMLWriter(self.filename,
            investigation_time=10.0, statistics="mean")

        writer.serialize([])

        _utils.assert_xml_equal(expected, self.filename)
        _utils.validates_against_xml_schema(self.filename)

    def test_serialize_a_model(self):
        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossCurves investigationTime="10.0" sourceModelTreePath="b1_b2_b3" gsimTreePath="b1_b2" unit="USD">
    <lossCurve assetRef="asset_1">
      <gml:Point>
        <gml:pos>1.0 1.5</gml:pos>
      </gml:Point>
      <poEs>1.0 0.5 0.1</poEs>
      <losses>10.0 20.0 30.0</losses>
    </lossCurve>
    <lossCurve assetRef="asset_2">
      <gml:Point>
        <gml:pos>2.0 2.5</gml:pos>
      </gml:Point>
      <poEs>1.0 0.3 0.2</poEs>
      <losses>20.0 30.0 40.0</losses>
    </lossCurve>
  </lossCurves>
</nrml>
""")

        writer = writers.LossCurveXMLWriter(self.filename,
            investigation_time=10.0, source_model_tree_path="b1_b2_b3",
            gsim_tree_path="b1_b2", unit="USD")

        data = [
            LOSS_CURVE(asset_ref="asset_1", location=POINT(1.0, 1.5),
                poes=[1.0, 0.5, 0.1], losses=[10.0, 20.0, 30.0],
                loss_ratios=None),

            LOSS_CURVE(asset_ref="asset_2", location=POINT(2.0, 2.5),
                poes=[1.0, 0.3, 0.2], losses=[20.0, 30.0, 40.0],
                loss_ratios=None),
        ]

        writer.serialize(data)

        _utils.assert_xml_equal(expected, self.filename)
        _utils.validates_against_xml_schema(self.filename)

    def test_serialize_statistics_metadata(self):
        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossCurves investigationTime="10.0" statistics="quantile" quantileValue="0.5" unit="USD">
    <lossCurve assetRef="asset_1">
      <gml:Point>
        <gml:pos>1.0 1.5</gml:pos>
      </gml:Point>
      <poEs>1.0 0.5 0.1</poEs>
      <losses>10.0 20.0 30.0</losses>
      <lossRatios>0.4 0.6 0.8</lossRatios>
    </lossCurve>
  </lossCurves>
</nrml>
""")

        writer = writers.LossCurveXMLWriter(self.filename,
            investigation_time=10.0, statistics="quantile",
            quantile_value=0.50, unit="USD")

        data = [LOSS_CURVE(asset_ref="asset_1", location=POINT(1.0, 1.5),
            poes=[1.0, 0.5, 0.1], losses=[10.0, 20.0, 30.0],
            loss_ratios=[0.4, 0.6, 0.8])]

        writer.serialize(data)

        _utils.assert_xml_equal(expected, self.filename)
        _utils.validates_against_xml_schema(self.filename)

    def test_quantile_metadata_validation(self):
        # `statistics` must be "quantile" or "mean".
        self.assertRaises(
            ValueError, writers.LossCurveXMLWriter, self.filename,
            investigation_time=10.0, statistics="UNKNOWN")

        # when "quantile" is used, `quantile_value` must be
        # specified as well.
        self.assertRaises(
            ValueError, writers.LossCurveXMLWriter, self.filename,
            investigation_time=10.0, statistics="quantile")

        writers.LossCurveXMLWriter(self.filename, investigation_time=50.0,
            statistics="quantile", quantile_value=0.50)

        writers.LossCurveXMLWriter(self.filename, investigation_time=50.0,
            statistics="mean")

    def test_logic_tree_metadata_validation(self):
        # logic tree parameters must be both specified.
        self.assertRaises(
            ValueError, writers.LossCurveXMLWriter, self.filename,
            investigation_time=10.0, source_model_tree_path="b1|b2")

        self.assertRaises(
            ValueError, writers.LossCurveXMLWriter, self.filename,
            investigation_time=10.0, gsim_tree_path="b1|b2")

        writers.LossCurveXMLWriter(self.filename,
            investigation_time=10.0, source_model_tree_path="b1_b2_b3",
            gsim_tree_path="b1_b2")

    def test_logic_tree_or_statistics_metadata_validation(self):
        # logic tree parameters or statistics, not both.
        self.assertRaises(
            ValueError, writers.LossCurveXMLWriter, self.filename,
            investigation_time=10.0, source_model_tree_path="b1|b2",
            statistics="mean")

        self.assertRaises(
            ValueError, writers.LossCurveXMLWriter, self.filename,
            investigation_time=10.0, gsim_tree_path="b1|b2",
            statistics="mean")
