# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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
import unittest
import os

from openquake.hazardlib.tests.gsim.check_gsim import check_gsim


class BaseGSIMTestCase(unittest.TestCase):
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    GSIM_CLASS = None

    def check(self, filename, max_discrep_percentage, **kwargs):
        gsim = self.GSIM_CLASS(**kwargs)
        with open(os.path.join(self.BASE_DATA_PATH, filename)) as f:
            errors, stats = check_gsim(gsim, f, max_discrep_percentage)
        if errors:
            raise AssertionError(stats)
        print()
        print(stats)
