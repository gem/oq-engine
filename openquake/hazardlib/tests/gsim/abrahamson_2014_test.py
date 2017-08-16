# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from openquake.hazardlib.gsim.abrahamson_2014 import (
    AbrahamsonEtAl2014, AbrahamsonEtAl2014RegTWN, AbrahamsonEtAl2014RegCHN,
    AbrahamsonEtAl2014RegJPN)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data have been generated from the Matlab implementation available as
# Annex 1 of Abrahamson et al. (2014)


class Abrahamson2014EtAlTestCase(BaseGSIMTestCase):
    """
    Test the default model, the total standard deviation and the within-event
    standard deviation. The between events std is implicitly tested
    """

    GSIM_CLASS = AbrahamsonEtAl2014

    def test_mean(self):
        self.check('ASK14/ASK14_ResMEAN_RegCAL.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('ASK14/ASK14_ResStdTot_RegCAL.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('ASK14/ASK14_ResStdPhi_RegCAL.csv',
                   max_discrep_percentage=0.1)


class Abrahamson2014EtAlRegTWNTestCase(BaseGSIMTestCase):
    """
    Test the modified version of the base model. Regional model for Taiwan.
    Standard deviation model is not tested since it's the same used for the
    default model.
    """

    GSIM_CLASS = AbrahamsonEtAl2014RegTWN

    def test_mean(self):
        self.check('ASK14/ASK14_ResMEAN_RegTWN.csv',
                   max_discrep_percentage=0.3)


class Abrahamson2014EtAlRegCHNTestCase(BaseGSIMTestCase):
    """
    Test the modified version of the base model. Regional model for China.
    Standard deviation model is not tested since it's the same used for the
    default model.
    """

    GSIM_CLASS = AbrahamsonEtAl2014RegCHN

    def test_mean(self):
        self.check('ASK14/ASK14_ResMEAN_RegCHN.csv',
                   max_discrep_percentage=0.1)


class Abrahamson2014EtAlRegJPNTestCase(BaseGSIMTestCase):
    """
    Test the modified version of the base model. Regional model for Japan
    Standard deviation model is not tested since it's the same used for the
    default model.
    """
    GSIM_CLASS = AbrahamsonEtAl2014RegJPN

    def test_mean(self):
        self.check('ASK14/ASK14_ResMEAN_RegJPN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('ASK14/ASK14_ResStdTot_RegJPN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('ASK14/ASK14_ResStdPhi_RegJPN.csv',
                   max_discrep_percentage=0.1)
