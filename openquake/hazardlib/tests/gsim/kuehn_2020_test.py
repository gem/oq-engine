"""
Test case for the Kuehn et a (2020) GA subduction model.
Test tables generated using R function as published at
github page
"""
from openquake.hazardlib.gsim.kuehn_2020 import (
    KuehnEtAl2020SInter,
    KuehnEtAl2020SSlab)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Interface
class KuehnEtAl2020SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInter
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)