# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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

from openquake.hazardlib.gsim.ita19.bindi_2011_backbone import \
    BindiEtAl2011Ita19Low, BindiEtAl2011Ita19Upp
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class BindiEtAl2011Ita19UppTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BindiEtAl2011Ita19Upp

    # Tables provided by original authors

    def test_mean(self):
        self.check('ITA19/BindiEtAl2011BackboneUPP.csv',
                   max_discrep_percentage=0.1)


class BindiEtAl2011Ita19LowTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BindiEtAl2011Ita19Low

    # Tables provided by original authors

    def test_mean(self):
        self.check('ITA19/BindiEtAl2011BackboneLOW.csv',
                   max_discrep_percentage=0.1)
