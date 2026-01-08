# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2025, GEM Foundation
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
from openquake.hazardlib.valid import gsim, modified_gsim
    
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


BASE_GMM = gsim("Lin2009")


class AbrahamsonBhasin2020TestCase(BaseGSIMTestCase):
    GSIM = modified_gsim(
        BASE_GMM,
        conditional_gmpe={
            "PGV": {"gmpe": {"AbrahamsonBhasin2020": {}}}})

    def test_all(self):
        self.check('AB20/General.csv',
                   max_discrep_percentage=0.2,
                   std_discrep_percentage=0.1)

class AbrahamsonBhasin2020PGATestCase(BaseGSIMTestCase):
    GSIM = modified_gsim(
        BASE_GMM,
        conditional_gmpe={
            "PGV": {"gmpe": {"AbrahamsonBhasin2020PGA": {}}}})

    def test_all(self):
        self.check('AB20/PGAbased.csv',
                   max_discrep_percentage=0.2,
                   std_discrep_percentage=0.1)

class AbrahamsonBhasin2020SA1TestCase(BaseGSIMTestCase):
    GSIM = modified_gsim(
        BASE_GMM,
        conditional_gmpe={
            "PGV": {"gmpe": {"AbrahamsonBhasin2020SA1": {}}}})

    def test_all(self):
        self.check('AB20/SA1based.csv',
                   max_discrep_percentage=0.2,
                   std_discrep_percentage=0.1)
