# -*- coding: utf-8 -*-
# Copyright (c) 2010-2011, GEM Foundation.
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
        expected = '{"magpmf", "magdistpmf", "latlonpmf"}'

        caf = CharArrayField()
        actual = caf.get_prep_value(['magpmf', 'magdistpmf', 'latlonpmf'])

        self.assertEqual(expected, actual)
