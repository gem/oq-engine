
# Copyright (c) 2010-2014, GEM Foundation.
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
from openquake.commonlib import nrml


def number_of(elem_name, tree):
    """
    Given an element name (including the namespaces prefix, if applicable),
    return the number of occurrences of the element in a given XML document.
    """
    expr = '//%s' % elem_name
    return len(tree.xpath(expr, namespaces=nrml.PARSE_NS_MAP))


class BaseExportTestCase(unittest.TestCase):
    def _test_exported_file(self, filename):
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(os.path.isabs(filename))
        self.assertTrue(os.path.getsize(filename) > 0)
