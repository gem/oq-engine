from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.banimahd_turkiye_2026 import Banimahd2026Turkiye


class Banimahd2026TurkiyeTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Banimahd2026Turkiye

    def test_mean(self):
        self.check(
            "BANIMAHD2026TURKIYE/BANIMAHD2026TURKIYE_MEAN.csv",
            max_discrep_percentage=0.1,
        )

    def test_std_total(self):
        self.check(
            "BANIMAHD2026TURKIYE/BANIMAHD2026TURKIYE_STD_TOTAL.csv",
            max_discrep_percentage=0.1,
        )
        
