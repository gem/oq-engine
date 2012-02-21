import unittest
import os

from tests.attrel.check_attrel import check_attrel


class BaseAttRelTestCase(unittest.TestCase):
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    ATTREL_CLASS = None

    def check(self, filename, max_discrep_percentage):
        assert self.ATTREL_CLASS is not None
        filename = os.path.join(self.BASE_DATA_PATH, filename)
        errors, stats = check_attrel(self.ATTREL_CLASS, filename,
                                     max_discrep_percentage)
        if errors:
            raise AssertionError(stats)
