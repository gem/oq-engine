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

from openquake.output import uhs as uhs_output

from tests.utils import helpers


class UHSXMLWriterTestCase(unittest.TestCase):
    """Tests for :class:`openquake.output.uhs.UHSXMLWriter`."""

    def test_serialize(self):
        expected_file = helpers.get_data_path('expected-uhs-export.xml')
        expected_text = open(expected_file, 'r').readlines()

        _, result_xml = tempfile.mkstemp()

        periods = [0.025, 0.45, 2.5]
        timespan = 50.0

        data = [
            (0.1, '/some/path/uhs_poe:0.1.hdf5'),
            (0.02, '/some/path/uhs_poe:0.02.hdf5'),
        ]

        try:
            uhs_writer = uhs_output.UHSXMLWriter(result_xml, periods, timespan)

            uhs_writer.serialize(data)

            actual_text = open(result_xml, 'r').readlines()
            self.assertEqual(expected_text, actual_text)
        finally:
            os.unlink(result_xml)
