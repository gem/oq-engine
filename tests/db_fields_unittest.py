# -*- coding: utf-8 -*-
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


import unittest

from openquake.db.models import CharArrayField, FloatArrayField


class FloatArrayFieldTestCase(unittest.TestCase):
    """Test for the custom :py:class:`openquake.db.models.FloatArrayField`
    type"""

    def test_get_prep_value(self):
        """Test the proper behavior of
        :py:method:`openquake.db.models.FloatArrayField.get_prep_value`."""
        expected = '{3.14, 10, -0.111}'

        faf = FloatArrayField()
        actual = faf.get_prep_value([3.14, 10, -0.111])

        self.assertEqual(expected, actual)


class CharArrayFieldTestCase(unittest.TestCase):
    """Tests for the custom :py:class:`openquake.db.models.CharArrayField`
    type"""

    def test_get_prep_value(self):
        """Test the proper behavior of
        :py:method:`openquake.db.models.CharArrayField.get_prep_value`."""
        expected = '{"MagPMF", "MagDistPMF", "LatLonPMF"}'

        caf = CharArrayField()
        actual = caf.get_prep_value(['MagPMF', 'MagDistPMF', 'LatLonPMF'])

        self.assertEqual(expected, actual)
