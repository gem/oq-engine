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

from openquake.hazardlib.gsim.edwards_fah_2013a import (
                                                    EdwardsFah2013Alpine10MPa,   EdwardsFah2013Alpine20MPa,
                                                    EdwardsFah2013Alpine30MPa,   EdwardsFah2013Alpine50MPa,
                                                    EdwardsFah2013Alpine60MPa,   EdwardsFah2013Alpine75MPa,
                                                    EdwardsFah2013Alpine90MPa,   EdwardsFah2013Alpine120MPa
                                                    )
from openquake.hazardlib.gsim.edwards_fah_2013a import (

                                                    EdwardsFah2013Alpine10MPaMR, EdwardsFah2013Alpine20MPaMR,
                                                    EdwardsFah2013Alpine30MPaMR, EdwardsFah2013Alpine50MPaMR,
                                                    EdwardsFah2013Alpine60MPaMR, EdwardsFah2013Alpine75MPaMR,
                                                    EdwardsFah2013Alpine90MPaMR, EdwardsFah2013Alpine120MPaMR
                                                    )
                                                    
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class EdwardsFah2013Alpine10MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine10MPa
 
   # Test data were obtained from a tool given by the authors
   # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd10_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_T.csv',
                    max_discrep_percentage=0.60)    

class EdwardsFah2013Alpine20MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine20MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd20_table.csv', max_discrep_percentage=0.600)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_T.csv', max_discrep_percentage=0.60)
                    
class EdwardsFah2013Alpine30MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine30MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd30_table.csv', max_discrep_percentage=0.600)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_T.csv', max_discrep_percentage=0.60)
                            
class EdwardsFah2013Alpine50MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine50MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd50_table.csv', max_discrep_percentage=0.600)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_T.csv', max_discrep_percentage=0.60)

class EdwardsFah2013Alpine60MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine60MPa
 
    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.
    def test_mean(self):
        self.check('EF13a/alp_sd60_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_T.csv', max_discrep_percentage=0.60)  
        
class EdwardsFah2013Alpine75MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine75MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd75_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_T.csv', max_discrep_percentage=0.60)
                    
class EdwardsFah2013Alpine90MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine90MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd90_table.csv', max_discrep_percentage=0.55)  
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_T.csv', max_discrep_percentage=0.60)
        
class EdwardsFah2013Alpine120MPaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine120MPa

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd120_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_T.csv', max_discrep_percentage=0.60)
        
class EdwardsFah2013Alpine60MPaMRTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine60MPaMR
 
   # Test data were obtained from a tool given by the authors
   # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd60_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.61)   


"""
Testing the single station GMPEs magnitude-distance dependent 
"""

class EdwardsFah2013Alpine10MPaMRTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine10MPaMR
 
   # Test data were obtained from a tool given by the authors
   # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd10_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.61)  

class EdwardsFah2013Alpine20MPaMRTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine20MPaMR
 
   # Test data were obtained from a tool given by the authors
   # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd20_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.61)

class EdwardsFah2013Alpine30MPaMRTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine30MPaMR
 
   # Test data were obtained from a tool given by the authors
   # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd30_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.61)
                      
class EdwardsFah2013Alpine50MPaMRTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine50MPaMR
 
   # Test data were obtained from a tool given by the authors
   # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd50_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.61)

class EdwardsFah2013Alpine75MPaMRTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine75MPaMR
 
   # Test data were obtained from a tool given by the authors
   # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd75_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.61)  

class EdwardsFah2013Alpine90MPaMRTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine90MPaMR
 
   # Test data were obtained from a tool given by the authors
   # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd90_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.61)
                      
class EdwardsFah2013Alpine120MPaMRTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine120MPaMR
 
   # Test data were obtained from a tool given by the authors
   # The data of the values of the mean PGA and SA are in cm/s2.

    def test_mean(self):
        self.check('EF13a/alp_sd120_table.csv', max_discrep_percentage=0.55)
    def test_std_total(self):
        self.check('EF13a/EF13_STD_TOTAL_SigmaSS_TMR.csv',
                    max_discrep_percentage=0.61)  
