from nhlib.gsim.akkar_bommer_2010 import AkB_2010_AttenRel
from tests.gsim.utils import BaseGSIMTestCase


class AkkarBommer2010TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AkB_2010_AttenRel
    
    # Test data were obtained from a tool given by the authors

    def test_mean_normal(self):
        self.check('AKBO10/AK10_MEDIAN_NM.csv',
                    max_discrep_percentage=0.6) 

"""
    def test_mean_reverse(self):
        self.check('AKBO10/AK10_MEDIAN_RV.csv',
                    max_discrep_percentage=0.6)
                    
    def test_mean_strike_slip(self):
        self.check('AKBO10/AK10_MEDIAN_SS.csv',
                    max_discrep_percentage=0.6)
                    
    def test_std_intra(self):
        self.check('AKBO10/AK10_STD_INTRA.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_inter(self):
        self.check('AKBO10/AK10_STD_INTER.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_total(self):
        self.check('AKBO10/AK10_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)
"""
