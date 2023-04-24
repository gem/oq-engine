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

from openquake.hazardlib.gsim.parker_2020 import (
    ParkerEtAl2020SInter, ParkerEtAl2020SInterB,
    ParkerEtAl2020SSlab, ParkerEtAl2020SSlabB)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Tests developed using R code from Grace Parker
# Received 17 September 2020.


class ParkerEtAl2020SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInter

    def test_all(self):
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

    def test_aleutian(self):
        self.check('PARKER20/ParkerEtAl2020SInterAleutian_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='AK', saturation_region='Aleutian')

    def test_alaska(self):
        self.check('PARKER20/ParkerEtAl2020SInterAlaska_MEAN.csv',
                   max_discrep_percentage=0.1, region='AK')

    def test_camn(self):
        self.check('PARKER20/ParkerEtAl2020SInterCAMN_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='CAM', saturation_region="CAM_N")

    def test_cams(self):
        self.check('PARKER20/ParkerEtAl2020SInterCAMS_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='CAM', saturation_region="CAM_S")

    def test_san(self):
        self.check('PARKER20/ParkerEtAl2020SInterSAN_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='SA', saturation_region='SA_N')

    def test_sas(self):
        self.check('PARKER20/ParkerEtAl2020SInterSAS_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='SA', saturation_region='SA_S')

    def test_taiwane(self):
        self.check('PARKER20/ParkerEtAl2020SInterTaiwanE_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='TW', saturation_region='TW_E')

    def test_taiwanw(self):
        self.check('PARKER20/ParkerEtAl2020SInterTaiwanW_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='TW', saturation_region='TW_W')


class ParkerEtAl2020SInterBTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SInterB

    def test_cascadia(self):
        self.check('PARKER20/ParkerEtAl2020SInterCascadia_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='Cascadia')

    def test_cascadiaout(self):
        self.check('PARKER20/ParkerEtAl2020SInterCascadiaOut_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='Cascadia', basin='out')

    def test_cascadiaseattle(self):
        self.check('PARKER20/ParkerEtAl2020SInterCascadiaSeattle_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='Cascadia', basin='Seattle')

    def test_japanpac(self):
        self.check('PARKER20/ParkerEtAl2020SInterJapanPac_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='JP', saturation_region='JP_Pac')

    def test_japanphi(self):
        self.check('PARKER20/ParkerEtAl2020SInterJapanPhi_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='JP', saturation_region='JP_Phi')


class ParkerEtAl2020SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlab

    def test_all(self):
        self.check('PARKER20/ParkerEtAl2020SSlab_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_aleutian(self):
        self.check('PARKER20/ParkerEtAl2020SSlabAleutian_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='AK', saturation_region='Aleutian')

    def test_alaska(self):
        self.check('PARKER20/ParkerEtAl2020SSlabAlaska_MEAN.csv',
                   max_discrep_percentage=0.1, region='AK')

    def test_camn(self):
        self.check('PARKER20/ParkerEtAl2020SSlabCAMN_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='CAM', saturation_region="CAM_N")

    def test_cams(self):
        self.check('PARKER20/ParkerEtAl2020SSlabCAMS_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='CAM', saturation_region="CAM_S")

    def test_san(self):
        self.check('PARKER20/ParkerEtAl2020SSlabSAN_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='SA', saturation_region='SA_N')

    def test_sas(self):
        self.check('PARKER20/ParkerEtAl2020SSlabSAS_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='SA', saturation_region='SA_S')

    def test_taiwane(self):
        self.check('PARKER20/ParkerEtAl2020SSlabTaiwanE_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='TW', saturation_region='TW_E')

    def test_taiwanw(self):
        self.check('PARKER20/ParkerEtAl2020SSlabTaiwanW_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='TW', saturation_region='TW_W')


class ParkerEtAl2020SSlabBTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2020SSlabB

    def test_cascadia(self):
        self.check('PARKER20/ParkerEtAl2020SSlabCascadia_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='Cascadia')

    def test_cascadiaout(self):
        self.check('PARKER20/ParkerEtAl2020SSlabCascadiaOut_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='Cascadia', basin='out')

    def test_cascadiaseattle(self):
        self.check('PARKER20/ParkerEtAl2020SSlabCascadiaSeattle_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='Cascadia', basin='Seattle')

    def test_japanpac(self):
        self.check('PARKER20/ParkerEtAl2020SSlabJapanPac_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='JP', saturation_region='JP_Pac')

    def test_japanphi(self):
        self.check('PARKER20/ParkerEtAl2020SSlabJapanPhi_MEAN.csv',
                   max_discrep_percentage=0.1,
                   region='JP', saturation_region='JP_Phi')
