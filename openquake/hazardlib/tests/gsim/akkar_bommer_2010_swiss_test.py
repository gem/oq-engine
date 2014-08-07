# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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

from openquake.hazardlib.gsim.akkar_bommer_2010    import AkkarBommer2010SWISS01
from openquake.hazardlib.gsim.akkar_bommer_2010    import AkkarBommer2010SWISS04
from openquake.hazardlib.gsim.akkar_bommer_2010    import AkkarBommer2010SWISS08
from openquake.hazardlib.gsim.akkar_bommer_2010    import AkkarBommer2010SWISS01T
from openquake.hazardlib.gsim.akkar_bommer_2010    import AkkarBommer2010SWISS04T
from openquake.hazardlib.gsim.akkar_bommer_2010    import AkkarBommer2010SWISS08T

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AkkarBommer2010SWISS01TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AkkarBommer2010SWISS01
#~ 
    #~ # Test data were obtained from a tool given by the authors
    #~ # The data of the values of the mean PGA and SA are in m/s2.
#~ 
    def test_mean(self):
        self.check('AKBO10Swiss/AK10_MEAN_VsK01_Corr.csv', max_discrep_percentage=0.50)

    def test_std_total(self):
        self.check('AKBO10Swiss/AK10_STD_TOTAL_SigmaSS-TMR.csv',
                    max_discrep_percentage=0.10)
#~ 
class AkkarBommer2010SWISS04TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AkkarBommer2010SWISS04
#~ 
    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in m/s2.
#~ 
    def test_mean(self):
        self.check('AKBO10Swiss/AK10_MEAN_VsK04_Corr.csv', max_discrep_percentage=0.50)
 
    def test_std_total(self):
        self.check('AKBO10Swiss/AK10_STD_TOTAL_SigmaSS-TMR.csv',
                    max_discrep_percentage=0.10)
                    #~ 
class AkkarBommer2010SWISS08TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AkkarBommer2010SWISS08
 #~ 
    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in m/s2.
 #~ 
    def test_mean(self):
        self.check('AKBO10Swiss/AK10_MEAN_VsK08_Corr.csv', max_discrep_percentage=0.50)

    def test_std_total(self):
        self.check('AKBO10Swiss/AK10_STD_TOTAL_SigmaSS-TMR.csv',
                    max_discrep_percentage=0.10)

class AkkarBommer2010SWISS01TTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AkkarBommer2010SWISS01T

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in m/s2.

    def test_mean(self):
        self.check('AKBO10Swiss/AK10_MEAN_VsK01_Corr.csv',
                    max_discrep_percentage=0.6)
    def test_std_total(self):
        self.check('AKBO10Swiss/AK10_STD_TOTAL_SigmaSS_T.csv', max_discrep_percentage=0.1)
                    
class AkkarBommer2010SWISS04TTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AkkarBommer2010SWISS04T
#~ 
    #~ # Test data were obtained from a tool given by the authors
    #~ # The data of the values of the mean PGA and SA are in m/s2.
#~ 
    def test_mean(self):
        self.check('AKBO10Swiss/AK10_MEAN_VsK04_Corr.csv',
                    max_discrep_percentage=0.6)
    def test_std_total(self):
        self.check('AKBO10Swiss/AK10_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.1)
class AkkarBommer2010SWISS08TTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AkkarBommer2010SWISS08T
#~ 
    #~ # Test data were obtained from a tool given by the authors
    #~ # The data of the values of the mean PGA and SA are in m/s2.
#~ 
    def test_mean(self):
        self.check('AKBO10Swiss/AK10_MEAN_VsK08_Corr.csv',
                    max_discrep_percentage=0.6)
    def test_std_total(self):
        self.check('AKBO10Swiss/AK10_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.1)
