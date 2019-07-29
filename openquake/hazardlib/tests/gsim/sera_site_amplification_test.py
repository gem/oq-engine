# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>

from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.sera_amplification_models import (
    PitilakisEtAl2018, Eurocode8Amplification, Eurocode8AmplificationDefault,
    SandikkayaDinsever2018)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


MAX_DISCREP = 0.01


class PitilakisEtAl2018TestCase(BaseGSIMTestCase):
    GSIM_CLASS = PitilakisEtAl2018

    def test_mean(self):
        self.check("sera_site_amp/Pitilakis2018Amplification_MEAN.csv"
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb")


class Eurocode8AmplificationTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Eurocode8Amplification

    def test_mean(self):
        self.check("sera_site_amp/Eurocode8Amplification_MEAN.csv"
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb")


class Eurocode8AmplificationDefaultTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Eurocode8AmplificationDefault

    def test_mean(self):
        self.check("sera_site_amp/EurocodeDefaultAmplification_MEAN.csv"
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb")


class SandikkayaDinsever2018TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SandikkayaDinsever2018

    def test_mean(self):
        self.check("sera_site_amp/SandikkayaDinsever2018_DEFAULT_PHI0_MEAN.csv"
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb")

