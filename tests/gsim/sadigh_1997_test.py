from nhe.gsim.sadigh_1997 import SadighEtAl1997

from tests.gsim.utils import BaseGSIMTestCase


class SadighEtAl1997TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SadighEtAl1997

    # test data was generated using opensha implementation of GMPE.

    def test_mean_rock(self):
        self.check('SADIGH97/SADIGH1997_ROCK_MEAN.csv',
                    max_discrep_percentage=0.4)

    def test_total_stddev_rock(self):
        self.check('SADIGH97/SADIGH1997_ROCK_STD_TOTAL.csv',
                   max_discrep_percentage=1e-10)

    def test_mean_soil(self):
        self.check('SADIGH97/SADIGH1997_SOIL_MEAN.csv',
                    max_discrep_percentage=0.5)

    def test_total_stddev_soil(self):
        self.check('SADIGH97/SADIGH1997_SOIL_STD_TOTAL.csv',
                   max_discrep_percentage=1e-10)
