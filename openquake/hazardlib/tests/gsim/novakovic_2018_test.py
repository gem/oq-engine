# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from openquake.hazardlib.gsim.novakovic_2018 import (
    NovakovicEtAl2018)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Verification tables created using the .xls spreadsheet provided as an
# electronic supplement to the BSSA paper
# NOTE: These tests use the "default" Oklahoma adjustment table, from
# which the between-event and within-event sigma are taken (and combined
# to provide the total sigma)

class NovakovicEtAl2018Test(BaseGSIMTestCase):
    GSIM_CLASS = NovakovicEtAl2018

    def test_all(self):
        self.check('NEA18/NEA18_MEAN.csv',
                   'NEA18/NEA18_TOTAL_STDDEV.csv',
                   'NEA18/NEA18_INTER_EVENT_STDDEV.csv',
                   'NEA18/NEA18_INTRA_EVENT_STDDEV.csv',
                   max_discrep_percentage=0.01)
