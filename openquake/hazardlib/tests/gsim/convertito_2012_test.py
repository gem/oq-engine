# The Hazard Library
# Copyright (C) 2014-2021 GEM Foundation
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
from openquake.hazardlib.gsim.convertito_2012 import ConvertitoEtAl2012Geysers
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class ConvertitoEtAl2012TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ConvertitoEtAl2012Geysers

    def test_all(self):
        self.check('CONV2012/CONV_2012_MEAN.csv',
                   'CONV2012/CONV_2012_STDDEV.csv',
                   max_discrep_percentage=0.1)
