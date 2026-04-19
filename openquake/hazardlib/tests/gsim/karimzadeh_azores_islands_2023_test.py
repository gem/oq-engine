import os
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.karimzadeh_azores_islands_2023 import Karimzadeh2023Azores


class Karimzadeh2023AzoresTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Karimzadeh2023Azores

    def test_mean(self):
        self.check(
            "KARIMZADEH2023AZORES/KARIMZADEH2023AZORES_MEAN.csv",
            max_discrep_percentage=0.1,
        )



    def test_std_total(self):
        self.check(
            "KARIMZADEH2023AZORES/KARIMZADEH2023AZORES_STD_TOTAL.csv",
            max_discrep_percentage=0.1,
        )
