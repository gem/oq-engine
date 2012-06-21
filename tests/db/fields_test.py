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


import pickle
import unittest

from django import forms

from openquake.db import fields


class FloatArrayFormFieldTestCase(unittest.TestCase):

    def setUp(self):
        self.form_field = fields.FloatArrayFormField()

    def test_clean(self):
        # a general succesful case with some mixed input which can be cast to
        # floats
        value = [0.0, 1, -17L, '5.1']

        expected = [0.0, 1.0, -17.0, 5.1]

        self.assertEqual(expected, self.form_field.clean(value))

    def test_clean_empty_list(self):
        self.assertEqual([], self.form_field.clean([]))

    def test_clean_no_list_tuple_or_string(self):
        value = object()

        self.assertRaises(forms.ValidationError, self.form_field.clean, value)

    def test_clean_list_of_non_floats(self):
        value = ['a', 5]

        self.assertRaises(forms.ValidationError, self.form_field.clean, value)

    def test_clean_str_list(self):
        value = '1.1 -5.78, 0 ,  7'

        expected = [1.1, -5.78, 0.0, 7.0]

        self.assertEqual(expected, self.form_field.clean(value))

    def test_clean_str_list_invalid(self):
        value = 'a 5'

        self.assertRaises(forms.ValidationError, self.form_field.clean, value)


class FloatArrayFieldTestCase(unittest.TestCase):
    """Test for the custom :py:class:`openquake.db.models.FloatArrayField`
    type"""

    def test_get_prep_value(self):
        """Test the proper behavior of
        :py:method:`openquake.db.models.FloatArrayField.get_prep_value`."""
        expected = '{3.14, 10, -0.111}'

        faf = fields.FloatArrayField()
        actual = faf.get_prep_value([3.14, 10, -0.111])

        self.assertEqual(expected, actual)


class CharArrayFieldTestCase(unittest.TestCase):
    """Tests for the custom :py:class:`openquake.db.models.CharArrayField`
    type"""

    def test_get_prep_value(self):
        """Test the proper behavior of
        :py:method:`openquake.db.models.CharArrayField.get_prep_value`."""
        expected = '{"MagPMF", "MagDistPMF", "LatLonPMF"}'

        caf = fields.CharArrayField()
        actual = caf.get_prep_value(['MagPMF', 'MagDistPMF', 'LatLonPMF'])

        self.assertEqual(expected, actual)


class PickleFieldTestCase(unittest.TestCase):
    def test_to_python(self):
        field = fields.PickleField()
        data = {'foo': None, (1, False): 'baz'}
        self.assertEqual(field.to_python(buffer(pickle.dumps(data))), data)
        self.assertIs(data, data)
        empty_buffer = buffer('')
        self.assertIs(empty_buffer, empty_buffer)

    def test_get_prep_value(self):
        field = fields.PickleField()
        data = {'foo': None, (1, False): 'baz'}
        self.assertEqual(pickle.loads(field.get_db_prep_value(data)), data)
