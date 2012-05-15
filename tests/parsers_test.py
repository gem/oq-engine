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


import os
import unittest

import models
import parsers


class SiteModelParserTestCase(unittest.TestCase):
    """Tests for :class:`parsers.SiteModelParser`."""

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

        test_file = os.path.join(
            os.path.dirname(__file__), '..', 'schema/examples/site_model.xml')

        parser = parsers.SiteModelParser(test_file)
        actual = [x for x in parser.parse()]

        self.assertEqual(len(expected), len(actual))

        for i, value in enumerate(expected):
            self.assertEqual(value.__dict__, actual[i].__dict__)
