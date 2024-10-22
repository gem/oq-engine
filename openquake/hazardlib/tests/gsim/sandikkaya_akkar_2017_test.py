# The Hazard Library
# Copyright (C) 2013-2023 GEM Foundation
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

from openquake.hazardlib.gsim.sandikkaya_akkar_2017 import (SandikkayaAkkar2017Rjb,
                                                 SandikkayaAkkar2017Repi,
                                                 SandikkayaAkkar2017Rhyp)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepancy percentages to be applied to all tests
MEAN_DISCREP = 0.1

class SandikkayaAkkar2017RjbTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SandikkayaAkkar2017Rjb

    # Tables provided by original authors - ensure compatibility with
    # Sandikkaya and Akkar 2017

    def test_all(self):
        self.check('SA17/SA17_RJB_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP)


class SandikkayaAkkar2017RepiTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SandikkayaAkkar2017Repi

    # Tables created from Excel file supplied by the original authors

    def test_all(self):
        self.check('SA17/SA17_REPI_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP)


class SandikkayaAkkar2017RhypTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SandikkayaAkkar2017Rhyp

    # Tables created from Excel file supplied by the original authors

    def test_all(self):
        self.check('SA17/SA17_RHYPO_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP)


