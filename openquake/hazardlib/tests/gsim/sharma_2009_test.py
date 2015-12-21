# The Hazard Library
# Copyright (C) 2012-2015, GEM Foundation
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

from openquake.hazardlib.gsim.sharma_2009 import SharmaEtAl2009
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class SharmaEtAl2009TestCase(BaseGSIMTestCase):
    """
    Test data were obtained via personal communications with the
    lead author in the form of an Excel spreadsheet. The most
    significant modification required to obtain the ``MEAN_FILE``
    was to convert from m/s^2 to g. Results were also verified
    against the published versions of Figures 6-9, digitized using
    http://arohatgi.info/WebPlotDigitizer/ app/. Agreement was
    excellent at 0.04 s for all magitudes, distances, mechanisms,
    and site conditions (Figure 6). For other periods (Figures 7-9)
    the results diverged, up to about 20%. Finally, in personal
    communication with the lead author, alternative versions of
    Figures 7-9 were provided which visually match both this
    implementation and the author-generated ``MEAN_FILE`` well.
    
    There is no plot of residuals as a function of frequency, so
    there's absolutely nothing to verify that against. That said,
    sigma provided is a simple lookup per spectral acceleration
    period.
    """

    GSIM_CLASS = SharmaEtAl2009
    MEAN_FILE = 'SDBK09/SDBK09_MEAN.csv'
    SIGMA_FILE = 'SDBK09/SDBK09_STD_TOTAL.csv'

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=1e-4)

    def test_std_total(self):
        self.check(self.SIGMA_FILE, max_discrep_percentage=1e-4)
