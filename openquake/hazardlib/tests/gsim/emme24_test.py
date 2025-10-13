# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
#
# Test data provided by Baran Guryuva (model author)
#
#

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.emme24 import (
    EMME24BB_GMM1SGM1, 
    EMME24BB_GMM1SGM2,
    EMME24BB_GMM1SGM3,
    EMME24BB_GMM2SGM1,
    EMME24BB_GMM2SGM2,
    EMME24BB_GMM2SGM3,
    EMME24BB_GMM3SGM1,
    EMME24BB_GMM3SGM2,
    EMME24BB_GMM3SGM3,
    EMME24BB_GMM4SGM1,
    EMME24BB_GMM4SGM2,
    EMME24BB_GMM4SGM3,
    EMME24BB_GMM5SGM1,
    EMME24BB_GMM5SGM2,
    EMME24BB_GMM5SGM3,
    )


class EMME24BB_GMM1SGM1_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM1SGM1

    def test_mean(self):
        self.check('BBEMME/BBEMME1_SGM1_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME1_SGM1_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME1_SGM1_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME1_SGM1_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM1SGM2_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM1SGM2

    def test_mean(self):
        self.check('BBEMME/BBEMME1_SGM2_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME1_SGM2_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME1_SGM2_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME1_SGM2_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24_BBGMM1SGM3_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM1SGM3

    def test_mean(self):
        self.check('BBEMME/BBEMME1_SGM3_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME1_SGM3_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME1_SGM3_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME1_SGM3_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24_BBGMM2SGM1_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM2SGM1

    def test_mean(self):
        self.check('BBEMME/BBEMME2_SGM1_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME2_SGM1_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME2_SGM1_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME2_SGM1_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM2SGM2_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM2SGM2

    def test_mean(self):
        self.check('BBEMME/BBEMME2_SGM2_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME2_SGM2_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME2_SGM2_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME2_SGM2_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM2SGM3_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM2SGM3

    def test_mean(self):
        self.check('BBEMME/BBEMME2_SGM3_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME2_SGM3_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME2_SGM3_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME2_SGM3_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM3SGM1_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM3SGM1

    def test_mean(self):
        self.check('BBEMME/BBEMME3_SGM1_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME3_SGM1_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME3_SGM1_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME3_SGM1_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM3SGM2_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM3SGM2

    def test_mean(self):
        self.check('BBEMME/BBEMME3_SGM2_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME3_SGM2_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME3_SGM2_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME3_SGM2_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM3SGM3_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM3SGM3

    def test_mean(self):
        self.check('BBEMME/BBEMME3_SGM3_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME3_SGM3_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME3_SGM3_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME3_SGM3_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM4SGM1_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM4SGM1

    def test_mean(self):
        self.check('BBEMME/BBEMME4_SGM1_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME4_SGM1_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME4_SGM1_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME4_SGM1_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM4SGM2_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM4SGM2

    def test_mean(self):
        self.check('BBEMME/BBEMME4_SGM2_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME4_SGM2_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME4_SGM2_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME4_SGM2_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM4SGM3_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM4SGM3

    def test_mean(self):
        self.check('BBEMME/BBEMME4_SGM3_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME4_SGM3_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME4_SGM3_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME4_SGM3_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM5SGM1_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM5SGM1

    def test_mean(self):
        self.check('BBEMME/BBEMME5_SGM1_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME5_SGM1_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME5_SGM1_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME5_SGM1_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM5SGM2_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM5SGM2

    def test_mean(self):
        self.check('BBEMME/BBEMME5_SGM2_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME5_SGM2_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME5_SGM2_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME5_SGM2_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)


class EMME24BB_GMM5SGM3_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = EMME24BB_GMM5SGM3

    def test_mean(self):
        self.check('BBEMME/BBEMME5_SGM3_MEAN.csv',
                   max_discrep_percentage=0.2)

    def test_inter_event_stddev(self):
        self.check('BBEMME/BBEMME5_SGM3_STD_INTER.csv',
                   max_discrep_percentage=0.2)

    def test_intra_event_stddev(self):
        self.check('BBEMME/BBEMME5_SGM3_STD_INTRA.csv',
                   max_discrep_percentage=0.2)

    def test_total_event_stddev(self):
        self.check('BBEMME/BBEMME5_SGM3_STD_TOTAL.csv',
                   max_discrep_percentage=0.2)
