from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.mohammadi_turkiye_2023 import Mohammadi2023Turkiye


class Mohammadi2023TurkiyeTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Mohammadi2023Turkiye

    def test_mean(self):
        self.check(
            "MOHAMMADI2023TURKIYE/MOHAMMADI2023TURKIYE_MEAN.csv",
            max_discrep_percentage=0.1,
        )

    def test_std_total(self):
        self.check(
            "MOHAMMADI2023TURKIYE/MOHAMMADI2023TURKIYE_STD_TOTAL.csv",
            max_discrep_percentage=0.1,
        )
