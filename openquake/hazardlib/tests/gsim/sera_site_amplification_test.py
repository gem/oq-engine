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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>

from openquake.hazardlib.gsim.sera_amplification_models import (
    PitilakisEtAl2018, PitilakisEtAl2020, Eurocode8Amplification,
    Eurocode8AmplificationDefault, SandikkayaDinsever2018)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


MAX_DISCREP = 0.01


class PitilakisEtAl2018TestCase(BaseGSIMTestCase):
    GSIM_CLASS = PitilakisEtAl2018

    def test_all(self):
        self.check("sera_site/Pitilakis2018Amplification_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb")


class PitilakisEtAl2020TestCase(BaseGSIMTestCase):
    GSIM_CLASS = PitilakisEtAl2020

    def test_all(self):
        self.check("sera_site/Pitilakis2020Amplification_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb")


class Eurocode8AmplificationTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Eurocode8Amplification

    def test_all(self):
        self.check("sera_site/Eurocode8Amplification_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb")


class Eurocode8AmplificationDefaultTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Eurocode8AmplificationDefault

    def test_all(self):
        self.check("sera_site/EurocodeDefaultAmplification_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb")


class SandikkayaDinsever2018TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SandikkayaDinsever2018

    def test_all(self):
        self.check("sera_site/SandikkayaDinsever2018_DEFAULT_PHI0_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb")

    def test_std_intra(self):
        self.check("sera_site/SandikkayaDinsever2018_"
                   "DEFAULT_PHI0_INTRA_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb")


class SandikkayaDinsever2018RegionTestCase(BaseGSIMTestCase):
    """
    Tests the case when a regional coefficient adaptation is used
    """
    GSIM_CLASS = SandikkayaDinsever2018

    def test_all(self):
        self.check(
            "sera_site/SandikkayaDinsever2018_DEFAULT_PHI0_ckWA_MEAN.csv",
            max_discrep_percentage=MAX_DISCREP,
            gmpe_name="BindiEtAl2014Rjb", region="WA")


class SandikkayaDinsever2018InputPhi0TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SandikkayaDinsever2018

    def test_std_intra(self):
        input_phi0 = {"PGA": 1.0, "SA(0.03)": 0.9, "SA(0.2)": 0.8,
                      "SA(0.5)": 0.7, "SA(1.0)": 0.6, "SA(1.25)": 0.55,
                      "SA(3.0)": 0.5}
        self.check("sera_site/"
                   "SandikkayaDinsever2018_INPUT_PHI0_INTRA_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_name="BindiEtAl2014Rjb", phi_0=input_phi0)
