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

from openquake.hazardlib.gsim.edwards_fah_2013f import (EdwardsFah2013Foreland10MPa,
                                                        EdwardsFah2013Foreland20MPa,
                                                        EdwardsFah2013Foreland30MPa,
                                                        EdwardsFah2013Foreland50MPa,
                                                        EdwardsFah2013Foreland60MPa,
                                                        EdwardsFah2013Foreland75MPa,
                                                        EdwardsFah2013Foreland90MPa,
                                                        EdwardsFah2013Foreland120MPa)

from openquake.hazardlib.gsim.edwards_fah_2013f import (EdwardsFah2013Foreland10MPaMR,
                                                        EdwardsFah2013Foreland20MPaMR,
                                                        EdwardsFah2013Foreland30MPaMR,
                                                        EdwardsFah2013Foreland50MPaMR,
                                                        EdwardsFah2013Foreland60MPaMR,
                                                        EdwardsFah2013Foreland75MPaMR,
                                                        EdwardsFah2013Foreland90MPaMR,
                                                        EdwardsFah2013Foreland120MPaMR)


from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class EdwardsFah2013Foreland10MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland10MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd10_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.65) 
                    
class EdwardsFah2013Foreland20MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland20MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd20_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.65) 
                    
class EdwardsFah2013Foreland30MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland30MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd30_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.65) 
                    
class EdwardsFah2013Foreland50MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland50MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd50_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.65) 
                    
class EdwardsFah2013Foreland60MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland60MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd60_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.65) 

class EdwardsFah2013Foreland75MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland75MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd75_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.65) 
                    
class EdwardsFah2013Foreland90MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland90MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd90_table.csv',
                    max_discrep_percentage=0.55)  
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.65) 

class EdwardsFah2013Foreland120MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland120MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd120_table.csv',
                    max_discrep_percentage=0.55)                                     
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.65) 
                                      

class EdwardsFah2013Foreland10MPaTestCaseMR(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland10MPaMR

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd10_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.65) 
                    
class EdwardsFah2013Foreland20MPaTestCaseMR(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland20MPaMR

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd20_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.65) 
                    
class EdwardsFah2013Foreland30MPaTestCaseMR(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland30MPaMR

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd30_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.65) 
                    
class EdwardsFah2013Foreland50MPaTestCaseMR(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland50MPaMR

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd50_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.65) 
                    
class EdwardsFah2013Foreland60MPaTestCaseMR(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland60MPaMR

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd60_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.65) 

class EdwardsFah2013Foreland75MPaTestCaseMR(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland75MPaMR

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd75_table.csv',
                    max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.65) 
                    
class EdwardsFah2013Foreland90MPaTestCaseMR(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland90MPaMR

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd90_table.csv',
                    max_discrep_percentage=0.55)  
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.65) 

class EdwardsFah2013Foreland120MPaTestCaseMR(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland120MPaMR

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13f/for_sd120_table.csv',
                    max_discrep_percentage=0.55)                                     
    def test_std_total(self):
        self.check('EF13f/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.65) 
                                      
