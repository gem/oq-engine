# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2022 GEM Foundation
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

from openquake.hazardlib.gsim.parker_2021 import (
    ParkerEtAl2021SInter, ParkerEtAl2021SSlab)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Tests developed using R code from Grace Parker
# Received 17 September 2020.


class ParkerEtAl2021SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2021SInter

    def test_all(self):
        self.check('NZNSH2022_PARKER20/PARKER2021_INTERFACE_GLO_GNS_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_total_stddev(self):
        self.check('NZNSH2022_PARKER20/PARKER2021_INTERFACE_GLO_GNS_TOTAL_STDDEV_MODIFIED_SIGMA.csv',
                   max_discrep_percentage=0.1)

    def test_total_stddev(self):
        self.check('NZNSH2022_PARKER20/PARKER2021_INTERFACE_GLO_GNS_TOTAL_STDDEV_ORIGINAL_SIGMA.csv',
                   max_discrep_percentage=0.1, which_sigma = "ORIGINAL")

    # def test_intra_event_stddev(self):
    #     self.check('PARKER20/ParkerEtAl2020SInter_INTRA_EVENT_STDDEV.csv',
    #                max_discrep_percentage=0.1)
    #
    # def test_inter_event_stddev(self):
    #     self.check('PARKER20/ParkerEtAl2020SInter_INTER_EVENT_STDDEV.csv',
    #                max_discrep_percentage=0.1)


class ParkerEtAl2021SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ParkerEtAl2021SSlab

    def test_all(self):
        self.check('NZNSH2022_PARKER20/PARKER2021_SLAB_GLO_GNS_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_total_stddev(self):
        self.check('NZNSH2022_PARKER20/PARKER2021_SLAB_GLO_GNS_TOTAL_STDDEV_MODIFIED_SIGMA.csv',
                   max_discrep_percentage=0.1)

    def test_total_stddev(self):
        self.check('NZNSH2022_PARKER20/PARKER2021_SLAB_GLO_GNS_TOTAL_STDDEV_ORIGINAL_SIGMA.csv',
                   max_discrep_percentage=0.1, which_sigma = "ORIGINAL")
