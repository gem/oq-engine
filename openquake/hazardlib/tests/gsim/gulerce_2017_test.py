# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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

from openquake.hazardlib.gsim.gulerce_2017 import (
    GulerceEtAl2017, GulerceEtAl2017RegTWN, GulerceEtAl2017RegITA,
    GulerceEtAl2017RegMID, GulerceEtAl2017RegCHN, GulerceEtAl2017RegJPN)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data for verification have been generated from the excel file provided
# as EQS supplementary material in Gulerce et al. (2017).

# Take note of the following bugs in the 'GKAS_2016_September_26_v1' Sheet of
# the supplemental excel file:
# 1. Formula error in Column CI, i.e. IMTs other than Sa(0.01s) did not include
#       regional delta

# Adjusted tolerance to a less strict value of 0.1% since stddev constants in
# COEFFS table were rounded off to 4 significant figures for brevity, which
# sacrificed some accuracy.


class GulerceEtAl2017TestCase(BaseGSIMTestCase):
    """
    Test the default California model, the total standard deviation and the
    within-event standard deviation. The between-event std is implicitly tested
    """
    GSIM_CLASS = GulerceEtAl2017

    def test_all(self):
        self.check('GKAS16/GKAS16_ResMEAN_RegCAL.csv',
                   'GKAS16/GKAS16_ResStdTot_RegCAL.csv',
                   'GKAS16/GKAS16_ResStdPhi_RegCAL.csv',
                   max_discrep_percentage=0.1)


class GulerceEtAl2017RegTWNTestCase(BaseGSIMTestCase):
    """
    Test the modified version of the base model. Regional model for Taiwan.
    Standard deviation model is not tested since it's the same used for the
    default model.
    """
    GSIM_CLASS = GulerceEtAl2017RegTWN

    def test_mean(self):
        self.check('GKAS16/GKAS16_ResMEAN_RegTWN.csv',
                   max_discrep_percentage=0.1)


class GulerceEtAl2017RegITATestCase(BaseGSIMTestCase):
    """
    Test the modified version of the base model. Regional model for Italy.
    Standard deviation model is not tested since it's the same used for the
    default model.
    """
    GSIM_CLASS = GulerceEtAl2017RegITA

    def test_mean(self):
        self.check('GKAS16/GKAS16_ResMEAN_RegITA.csv',
                   max_discrep_percentage=0.1)


class GulerceEtAl2017RegMIDTestCase(BaseGSIMTestCase):
    """
    Test the modified version of the base model. Regional model for Middle East
    Standard deviation model is not tested since it's the same used for the
    default model.
    """
    GSIM_CLASS = GulerceEtAl2017RegMID

    def test_mean(self):
        self.check('GKAS16/GKAS16_ResMEAN_RegMID.csv',
                   max_discrep_percentage=0.1)


class GulerceEtAl2017RegCHNTestCase(BaseGSIMTestCase):
    """
    Test the modified version of the base model. Regional model for China.
    Standard deviation model is not tested since it's the same used for the
    default model.
    """
    GSIM_CLASS = GulerceEtAl2017RegCHN

    def test_mean(self):
        self.check('GKAS16/GKAS16_ResMEAN_RegCHN.csv',
                   max_discrep_percentage=0.1)


class GulerceEtAl2017RegJPNTestCase(BaseGSIMTestCase):
    """
    Test the modified version of the mean and standard deviation model for
    the base (California) model. Regional model for Japan.
    """
    GSIM_CLASS = GulerceEtAl2017RegJPN

    def test_all(self):
        self.check('GKAS16/GKAS16_ResMEAN_RegJPN.csv',
                   'GKAS16/GKAS16_ResStdTot_RegJPN.csv',
                   'GKAS16/GKAS16_ResStdPhi_RegJPN.csv',
                   max_discrep_percentage=0.1)
