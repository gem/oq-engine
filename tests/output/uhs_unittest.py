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
