# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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

from openquake.hazardlib.gsim.chao_2020 import (
    ChaoEtAl2020SInter, ChaoEtAl2020SSlab, ChaoEtAl2020Asc)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Tests developed using MATLAB code from Shu-Hsien Chao
# Received 9 October 2020.


class ChaoEtAl2020SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChaoEtAl2020SInter

    def test_mean(self):
        self.check('CHAO20/ChaoEtAl2020SInter_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_mean2(self):
        self.check('CHAO20/ChaoEtAl2020SInter_MEAN2.csv',
                   max_discrep_percentage=0.1,
                   manila=True, geology=False)


class ChaoEtAl2020SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChaoEtAl2020SSlab

    def test_mean(self):
        self.check('CHAO20/ChaoEtAl2020SSlab_MEAN.csv',
                   max_discrep_percentage=0.1,
                   aftershocks=True, manila=True)

    def test_stddev(self):
        self.check('CHAO20/ChaoEtAl2020SSlab_STDDEV.csv',
                   max_discrep_percentage=0.1)


class ChaoEtAl2020AscTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChaoEtAl2020Asc

    def test_mean(self):
        self.check('CHAO20/ChaoEtAl2020Asc_MEAN.csv',
                   max_discrep_percentage=0.1, aftershocks=True)

    def test_mean2(self):
        self.check('CHAO20/ChaoEtAl2020Asc_MEAN2.csv',
                   max_discrep_percentage=0.1)

    def test_stddev(self):
        self.check('CHAO20/ChaoEtAl2020Asc_STDDEV.csv',
                   max_discrep_percentage=0.1)
