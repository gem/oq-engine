"""
Test case for the Kuehn et a (2020) GA subduction model.
Test tables generated using R function as published at
github page
"""
from openquake.hazardlib.gsim.si_2020 import (
    SiEtAl2020SInter,
    SiEtAl2020SSlab)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Interface
class SiEtAl2020SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS =SiEtAl2020SInter
    MEAN_FILE = "si2020/SI2020_INTERFACE_MEAN.csv"
    TOTAL_FILE = "si2020/SI2020_INTERFACE_TOTAL_STDDEV.csv"
    INTER_FILE = "si2020/SI2020_INTERFACE_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "si2020/SI2020_INTERFACE_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

# Intraslab
class SiEtAl2020SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS =SiEtAl2020SSlab
    MEAN_FILE = "si2020/SI2020_INTRASLAB_MEAN.csv"
    TOTAL_FILE = "si2020/SI2020_INTRASLAB_TOTAL_STDDEV.csv"
    INTER_FILE = "si2020/SI2020_INTRASLAB_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "si2020/SI2020_INTRASLAB_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)
