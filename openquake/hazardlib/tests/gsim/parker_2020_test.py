# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2020 GEM Foundation
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

from openquake.hazardlib.gsim.parker_2020 import \
    ParkerEtAl2020SInter, \
    ParkerEtAl2020SInterAleutian, \
    ParkerEtAl2020SInterAlaska, \
    ParkerEtAl2020SInterCascadiaOut, \
    ParkerEtAl2020SInterCascadiaSeattle, \
    ParkerEtAl2020SInterCascadia, \
    ParkerEtAl2020SInterCAMN, \
    ParkerEtAl2020SInterCAMS, \
    ParkerEtAl2020SInterJapanPac, \
    ParkerEtAl2020SInterJapanPhi, \
    ParkerEtAl2020SInterSAN, \
    ParkerEtAl2020SInterSAS, \
    ParkerEtAl2020SInterTaiwanE, \
    ParkerEtAl2020SInterTaiwanW, \
    ParkerEtAl2020SSlab, \
    ParkerEtAl2020SSlabAleutian, \
    ParkerEtAl2020SSlabAlaska, \
    ParkerEtAl2020SSlabCascadiaOut, \
    ParkerEtAl2020SSlabCascadiaSeattle, \
    ParkerEtAl2020SSlabCascadia, \
    ParkerEtAl2020SSlabCAMN, \
    ParkerEtAl2020SSlabCAMS, \
    ParkerEtAl2020SSlabJapanPac, \
    ParkerEtAl2020SSlabJapanPhi, \
    ParkerEtAl2020SSlabSAN, \
    ParkerEtAl2020SSlabSAS, \
    ParkerEtAl2020SSlabTaiwanE, \
    ParkerEtAl2020SSlabTaiwanW

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Tests developed using R code from Grace Parker
# Received 17 September 2020.


class ParkerEtAl2020SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInter

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInter_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_total_stddev(self):
        self.check('PARKER20/ParkerEtAl2020SInter_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.1)

    def test_intra_event_stddev(self):
        self.check('PARKER20/ParkerEtAl2020SInter_INTRA_EVENT_STDDEV.csv',
                   max_discrep_percentage=0.1)

    def test_inter_event_stddev(self):
        self.check('PARKER20/ParkerEtAl2020SInter_INTER_EVENT_STDDEV.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterAleutianTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterAleutian

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterAleutian_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterAlaskaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterAlaska

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterAlaska_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterCascadiaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterCascadia

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterCascadia_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterCascadiaOutTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterCascadiaOut

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterCascadiaOut_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterCascadiaSeattleTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterCascadiaSeattle

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterCascadiaSeattle_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterCAMNTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterCAMN

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterCAMN_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterCAMSTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterCAMS

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterCAMS_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterJapanPacTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterJapanPac

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterJapanPac_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterJapanPhiTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterJapanPhi

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterJapanPhi_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterSANTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterSAN

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterSAN_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterSASTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterSAS

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterSAS_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterTaiwanETestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterTaiwanE

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterTaiwanE_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SInterTaiwanWTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterTaiwanW

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SInterTaiwanW_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlab

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlab_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabAleutianTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabAleutian

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabAleutian_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabAlaskaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabAlaska

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabAlaska_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabCascadiaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabCascadia

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabCascadia_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabCascadiaOutTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabCascadiaOut

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabCascadiaOut_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabCascadiaSeattleTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabCascadiaSeattle

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabCascadiaSeattle_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabCAMNTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabCAMN

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabCAMN_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabCAMSTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabCAMS

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabCAMS_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabJapanPacTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabJapanPac

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabJapanPac_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabJapanPhiTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabJapanPhi

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabJapanPhi_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabSANTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabSAN

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabSAN_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabSASTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabSAS

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabSAS_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabTaiwanETestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabTaiwanE

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabTaiwanE_MEAN.csv',
                   max_discrep_percentage=0.1)


class ParkerEtAl2020SSlabTaiwanWTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabTaiwanW

    def test_mean(self):
        self.check('PARKER20/ParkerEtAl2020SSlabTaiwanW_MEAN.csv',
                   max_discrep_percentage=0.1)
