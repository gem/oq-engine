# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2020 GEM Foundation
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
#
# Test tables elaboratated from data provided directly from the authors.
#

from openquake.hazardlib.gsim.lanzano_2020 import LanzanoEtAl2020_ref
from openquake.hazardlib.gsim.lanzano_2020 import LanzanoEtAl2020_EC8
from openquake.hazardlib.gsim.lanzano_2020 import LanzanoEtAl2020_Cluster
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class LanzanoEtAl2020_ref_TestCase(BaseGSIMTestCase):

    GSIM_CLASS = LanzanoEtAl2020_ref
    # Tables provided by original authors
    MEAN_FILE = "LAN2020/LAN2020_REF_MEAN.csv"
    STD_FILE = "LAN2020/LAN2020_REF_STD_TOTAL.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=0.1)


class LanzanoEtAl2020_EC8_TestCase(BaseGSIMTestCase):

    GSIM_CLASS = LanzanoEtAl2020_EC8
    # Tables provided by original authors
    MEAN_FILE = "LAN2020/LAN2020_EC8_MEAN.csv"
    STD_FILE = "LAN2020/LAN2020_EC8_STD_TOTAL.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=0.1)


class LanzanoEtAl2020_Cluster_TestCase(BaseGSIMTestCase):

    GSIM_CLASS = LanzanoEtAl2020_Cluster
    # Tables provided by original authors
    MEAN_FILE = "LAN2020/LAN2020_CLUSTER_MEAN.csv"
    STD_FILE = "LAN2020/LAN2020_CLUSTER_STD_TOTAL.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=0.1)
