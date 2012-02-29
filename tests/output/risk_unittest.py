# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


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
