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


from openquake.db.models import model_equals
from openquake.db.models import Organization

from tests.utils.helpers import skipit


class ModelEqualsTestCase(unittest.TestCase):
    """Tests for :function:`model_equals`, a function to compare the contents
    of two Django models objects."""

    def setUp(self):
        self.org = Organization(name='test_name', address='test_address',
                                url='http://www.test.com')
        self.org.save()

        # Now query two fresh copies of this record from the DB to test with:
        self.o1 = Organization.objects.get(id=self.org.id)
        self.o2 = Organization.objects.get(id=self.org.id)


    def test_model_equals(self):
        self.assertTrue(model_equals(self.o1, self.o2))

    def test_model_equals_with_ignore(self):
        self.o1.name = 'something different'
        self.assertTrue(model_equals(self.o1, self.o2, ignore=('name',)))

    def test_model_equals_with_many_ignores(self):
        self.o1.name = 'something different'
        self.o1.url = 'http://www.somethingdiff.com'
        self.assertTrue(model_equals(self.o1, self.o2, ignore=('name', 'url')))

    def test_model_equals_ignore_id(self):
        """Comparing two models with different ids is a special case, thus a
        separate test.

        This is a special case because it is very likely that we could have
        multiple records with the same contents but different ids. An example
        of this would be two :class:`openquake.db.models.OqJobProfile`
        records that contain the exact same config parameters, just different
        database ids. """
        self.o1.id = 1
        self.o2.id = 2

        self.assertTrue(model_equals(self.o1, self.o2, ignore=('id',)))

    def test_model_equals_with_invalid_ignores(self):
        self.assertTrue(model_equals(
            self.o1, self.o2, ignore=('not_an_attr',)))

    def test__state_is_always_ignored(self):
        # Set some fake _state values on the model objects:
        self.o1._state = 'fake_state'
        self.o2._state = 'other_fake_state'

        # Sanity check: make sure _state is in the object dict.
        self.assertTrue(self.o1.__dict__.has_key('_state'))
        self.assertTrue(self.o2.__dict__.has_key('_state'))

        # Sanity check 2: Make sure the object dict _state is correctly set.
        self.assertEquals('fake_state', self.o1.__dict__['_state'])
        self.assertEquals('other_fake_state', self.o2.__dict__['_state'])

        # Now finally compare the two objects:
        self.assertTrue(model_equals(self.o1, self.o2))

    @skipit
    def test_model_equals_with_geometry(self):
        # TODO: Write me.
        self.assertTrue(False)
