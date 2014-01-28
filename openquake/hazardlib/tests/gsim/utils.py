# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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
import os
import inspect

from openquake.hazardlib.tests.gsim.check_gsim import check_gsim


class BaseGSIMTestCase(unittest.TestCase):
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    GSIM_CLASS = None

    def get_context_attributes(self, ctx):
        att = inspect.getmembers(ctx, lambda a: not(inspect.isroutine(a)))
        att = [
            k for k, v in att if not (k.startswith('__') and k.endswith('__'))
        ]

        return set(att)

    def check(self, filename, max_discrep_percentage):
        assert self.GSIM_CLASS is not None
        filename = os.path.join(self.BASE_DATA_PATH, filename)
        errors, stats, sctx, rctx, dctx = check_gsim(
            self.GSIM_CLASS, open(filename),
            max_discrep_percentage
        )
        s_att = self.get_context_attributes(sctx)
        r_att = self.get_context_attributes(rctx)
        d_att = self.get_context_attributes(dctx)
        self.assertEqual(self.GSIM_CLASS.REQUIRES_SITES_PARAMETERS, s_att)
        self.assertEqual(self.GSIM_CLASS.REQUIRES_RUPTURE_PARAMETERS, r_att)
        self.assertEqual(self.GSIM_CLASS.REQUIRES_DISTANCES, d_att)
        if errors:
            raise AssertionError(stats)
        print
        print stats
