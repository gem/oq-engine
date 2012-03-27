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

from openquake.output.scenario_damage import DmgDistPerAssetXMLWriter

from tests.utils import helpers


class UHSXMLWriterTestCase(unittest.TestCase):

    def test_serialize(self):
        # expected_file = helpers.get_data_path('expected-uhs-export.xml')
        # expected_text = open(expected_file, 'r').readlines()

        damage_states = ["no_damage", "slight", "moderate", "extensive"]
        writer = DmgDistPerAssetXMLWriter("", "end_branch_label", damage_states)

        writer.serialize(None)
