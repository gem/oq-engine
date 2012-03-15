from nhe.attrel.sadigh_1997 import SadighEtAl1997

from tests.attrel.utils import BaseAttRelTestCase


class SadighEtAl1997TestCase(BaseAttRelTestCase):
    ATTREL_CLASS = SadighEtAl1997

    # test data was generated using opensha implementation of GMPE.

    def test_mean(self):
        # NB: this test fail because data files contain
        # logarithms of amplitudes!
        # TODO: fix test data files
        self.check('SADIGH97/SADIGH1997_MEAN.csv',
                    max_discrep_percentage=0.12)

    def test_total_stddev(self):
        self.check('SADIGH97/SADIGH1997_TOTAL_STDDEV.csv',
                   max_discrep_percentage=1e-10)
