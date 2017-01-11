# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from openquake.hazardlib.gsim.akkar_2014 import (AkkarEtAlRjb2014,
                                                 AkkarEtAlRepi2014,
                                                 AkkarEtAlRhyp2014)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AkkarEtAlRjb2014TestCase1(BaseGSIMTestCase):
    GSIM_CLASS = AkkarEtAlRjb2014

    # Tables provided by original authors - ensure compatibility with
    # Akkar 2013

    def test_mean(self):
        self.check('AKKAR13/AKKAR2013_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('AKKAR13/AKKAR2013_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('AKKAR13/AKKAR2013_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AKKAR13/AKKAR2013_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class AkkarEtAlRjb2014TestCase2(BaseGSIMTestCase):
    GSIM_CLASS = AkkarEtAlRjb2014

    # Tables created from Matlab code supplied by the original authors

    def test_mean(self):
        self.check('AKKAR14/AKKAR_2014_RJB_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('AKKAR14/AKKAR_2014_RJB_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('AKKAR14/AKKAR_2014_RJB_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AKKAR14/AKKAR_2014_RJB_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class AkkarEtAlRepi2014TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AkkarEtAlRepi2014

    # Tables created from Matlab code supplied by the original authors

    def test_mean(self):
        self.check('AKKAR14/AKKAR_2014_REPI_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('AKKAR14/AKKAR_2014_REPI_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('AKKAR14/AKKAR_2014_REPI_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AKKAR14/AKKAR_2014_REPI_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class AkkarEtAlRhypo2014TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AkkarEtAlRhyp2014

    # Tables created from Matlab code supplied by the original authors

    def test_mean(self):
        self.check('AKKAR14/AKKAR_2014_RHYPO_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('AKKAR14/AKKAR_2014_RHYPO_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('AKKAR14/AKKAR_2014_RHYPO_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AKKAR14/AKKAR_2014_RHYPO_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
