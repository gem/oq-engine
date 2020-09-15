"""
Test case for the Kuehn et a (2020) GA subduction model.
Test tables generated using R function as published at
github page
"""
from openquake.hazardlib.gsim.kuehn_2020 import (
    KuehnEtAl2020SInter,
    KuehnEtAl2020SInterAlaska,
    KuehnEtAl2020SInterCascadia,
    KuehnEtAl2020SInterNewZealand,
    KuehnEtAl2020SInterTaiwan,
    KuehnEtAl2020SSlab,
    KuehnEtAl2020SSlabAlaska,
    KuehnEtAl2020SSlabCascadia,
    KuehnEtAl2020SSlabNewZealand,
    KuehnEtAl2020SSlabTaiwan)
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

# Interface Alaska
class KuehnEtAl2020SInterAlaskaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInterAlaska
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_ALASKA_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_ALASKA_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INTERFACE_ALASKA_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INTERFACE_ALASKA_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

# Interface Cascadia
class KuehnEtAl2020SInterCascadiaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInterCascadia
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_CASCADIA_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_CASCADIA_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INTERFACE_CASCADIA_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INTERFACE_CASCADIA_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

# Interface Central America and Mexico

# Interface Japan


# Interface New Zealand
class KuehnEtAl2020SInterNewZealandTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInterNewZealand
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_NEWZEALAND_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_NEWZEALAND_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INTERFACE_NEWZEALAND_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INTERFACE_NEWZEALAND_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

# Interface South America

# Interface Taiwan
class KuehnEtAl2020SInterTaiwanTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInterTaiwan
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_TAIWAN_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_TAIWAN_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INTERFACE_TAIWAN_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INTERFACE_TAIWAN_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

# Interface
class KuehnEtAl2020SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlab
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

# Intraslab Alaska
class KuehnEtAl2020SSlabAlaskaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlabAlaska
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_ALASKA_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_ALASKA_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_ALASKA_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_ALASKA_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

# Intraslab Cascadia
class KuehnEtAl2020SSlabCascadiaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlabCascadia
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_CASCADIA_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_CASCADIA_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_CASCADIA_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_CASCADIA_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

# Intraslab Central America and Mexico

# Intraslab Japan


# Intraslab New Zealand
class KuehnEtAl2020SSlabNewZealandTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlabNewZealand
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_NEWZEALAND_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_NEWZEALAND_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_NEWZEALAND_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_NEWZEALAND_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

# Intraslab South America

# Intraslab Taiwan
class KuehnEtAl2020SSlabTaiwanTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlabTaiwan
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_TAIWAN_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_TAIWAN_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_TAIWAN_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_TAIWAN_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

