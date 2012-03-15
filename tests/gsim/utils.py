import unittest
import os

from tests.gsim.check_attrel import check_gsim


class BaseGSIMTestCase(unittest.TestCase):
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    GSIM_CLASS = None

    def check(self, filename, max_discrep_percentage):
        assert self.GSIM_CLASS is not None
        filename = os.path.join(self.BASE_DATA_PATH, filename)
        errors, stats = check_gsim(self.GSIM_CLASS, open(filename),
                                   max_discrep_percentage)
        if errors:
            raise AssertionError(stats)
        print
        print stats
