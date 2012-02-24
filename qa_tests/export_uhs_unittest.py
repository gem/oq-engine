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


import subprocess
import unittest


class ExportUHSTestCase(unittest.TestCase):
    """Exercises the full end-to-end functionality for running a UHS
    calculation and exporting results from the database to files.
    """

    def test_export_uhs(self):
        pass
        # subprocess.call( bin/openquake --config-file demo/uhs/config.gem)
        # subprocess.call( bin/openquake --list-calculations )
        # subprocess.call( bin/openquake --list-outputs XXX )
        # subprocess.call( bin/openquake --export YYY /tmp/blah/ )
        # TODO: need to listen for text output, exit status
        # TODO: parse the text output and check IDs
