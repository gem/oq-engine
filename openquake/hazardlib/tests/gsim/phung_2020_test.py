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

from openquake.hazardlib.gsim.phung_2020 import (
    PhungEtAl2020Asc, PhungEtAl2020SInter, PhungEtAl2020SSlab)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Tests developed using original MATLAB code
# Received 3 November 2020.


class PhungEtAl2020AscTestCase(BaseGSIMTestCase):
    GSIM_CLASS = PhungEtAl2020Asc

    def test_all(self):
        self.check('PHUNG20/PhungEtAl2020Asc_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_all_tw(self):
        self.check('PHUNG20/PhungEtAl2020Asc_MEAN2.csv',
                   max_discrep_percentage=0.1,
                   aftershocks=True, d_dpp=1.8, region='tw')

    def test_all_ca(self):
        self.check('PHUNG20/PhungEtAl2020Asc_MEAN3.csv',
                   max_discrep_percentage=0.1, region='ca')

    def test_all_jp_stddevs(self):
        self.check('PHUNG20/PhungEtAl2020Asc_MEAN4.csv',
                   max_discrep_percentage=0.1, region='jp')


class PhungEtAl2020SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = PhungEtAl2020SInter

    def test_all(self):
        self.check('PHUNG20/PhungEtAl2020SInter_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_stddev(self):
        self.check('PHUNG20/PhungEtAl2020SInter_STDDEV.csv',
                   max_discrep_percentage=0.1)

    def test_all2(self):
        self.check('PHUNG20/PhungEtAl2020SInter_MEAN2.csv',
                   max_discrep_percentage=0.1, region='tw')

    def test_stddev2(self):
        self.check('PHUNG20/PhungEtAl2020SInter_STDDEV2.csv',
                   max_discrep_percentage=0.1, region='tw')


class PhungEtAl2020SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = PhungEtAl2020SSlab

    def test_all(self):
        self.check('PHUNG20/PhungEtAl2020SSlab_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_all2(self):
        self.check('PHUNG20/PhungEtAl2020SSlab_MEAN2.csv',
                   max_discrep_percentage=0.1, region='tw')
