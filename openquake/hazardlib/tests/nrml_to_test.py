# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import pathlib
import shutil
import unittest
import tempfile
from openquake.hazardlib.nrml_to import convert_to

CD = pathlib.Path(__file__).parent


class TestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_multi_fault(self):
        gmodel = CD / 'data/sections/sections_mix.xml'
        smodel = CD / 'data/sections/sources.xml'
        convert_to('csv', [smodel], geometry=gmodel, outdir=self.tmpdir)
        try:
            convert_to('gpkg', [smodel], geometry=gmodel, outdir=self.tmpdir)
        except ImportError as exc:  # missing fiona
            raise unittest.SkipTest(str(exc))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
