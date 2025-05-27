# The Hazard Library
# Copyright (C) 2025-2025 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest


class PyprojTestCase(unittest.TestCase):

    # NOTE: we found that sometimes broken pyproj wheels cause a very tricky behavior,
    # so the order in which some libraries are imported causes different behaviors.
    # We had a case in which importing hazardlib and then pyproj caused the application
    # to suddenly exit without giving any kind of error message.
    def test_import_hazardlib_then_pyproj(self):
        import openquake.hazardlib  # noqa
        import pyproj  # noqa

    def test_import_pyproj_then_hazardlib(self):
        import pyproj  # noqa
        import openquake.hazardlib  # noqa
