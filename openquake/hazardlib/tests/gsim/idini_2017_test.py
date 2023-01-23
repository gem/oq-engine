# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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

from openquake.hazardlib.gsim.idini_2017 import (
    IdiniEtAl2017SInter,
    IdiniEtAl2017SSlab)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class IdiniEtAl2017SInterTestCase(BaseGSIMTestCase):
    """
    Tests the Idini et al. (2017) GMPE for subduction
    interface earthquakes
    """
    GSIM_CLASS = IdiniEtAl2017SInter
    MEAN_FILE = "Idini2017/IDINI_2017_SINTER_MEAN.csv"
    TOTAL_FILE = "Idini2017/IDINI_2017_SINTER_TOTAL_STDDEV.csv"
    INTER_FILE = "Idini2017/IDINI_2017_SINTER_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "Idini2017/IDINI_2017_SINTER_INTRA_EVENT_STDDEV.csv"

    def test_all(self):
        self.check(self.MEAN_FILE,
                   self.TOTAL_FILE,
                   self.INTER_FILE,
                   self.INTRA_FILE,
                   max_discrep_percentage=0.1)


class IdiniEtAl2017SSlabTestCase(IdiniEtAl2017SInterTestCase):
    """
    Tests the Idini et al. (2017) GMPE for subduction inslab earthquakes
    """
    GSIM_CLASS = IdiniEtAl2017SSlab
    MEAN_FILE = "Idini2017/IDINI_2017_SSLAB_MEAN.csv"
    TOTAL_FILE = "Idini2017/IDINI_2017_SSLAB_TOTAL_STDDEV.csv"
    INTER_FILE = "Idini2017/IDINI_2017_SSLAB_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "Idini2017/IDINI_2017_SSLAB_INTRA_EVENT_STDDEV.csv"
