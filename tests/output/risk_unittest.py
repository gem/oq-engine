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
import tempfile
import unittest

from openquake.output import risk as risk_output

from tests.utils import helpers


class AggLossCurveXMLWriterTestCase(unittest.TestCase):
    """Tests for the
    :class:`openquake.output.risk.AggregateLossCurveXMLWriter`.
    """

    def test_serialize(self):
        expected_file = helpers.get_data_path('expected-agg-loss-curve.xml')
        expected_text = open(expected_file, 'r').readlines()

        _, result_xml = tempfile.mkstemp()

        try:
            agg_lc_writer = risk_output.AggregateLossCurveXMLWriter(
                result_xml)

            loss = [1.1, 3.3, 2.2]
            poes = [0.1, 0.3, 0.2]

            agg_lc_writer.serialize(loss, poes)

            actual_text = open(result_xml, 'r').readlines()
            self.assertEqual(expected_text, actual_text)
        finally:
            os.unlink(result_xml)
