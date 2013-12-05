import mock
import unittest
from nose.tools import assert_equal
from openquake.hazardlib.gsim import get_available_gsims
from openquake.hazardlib.gsim.base import GMPE


class FakeModule(object):
    'An object faking a module containing only one subclass of GMPE'
    class AtkinsonBoore2006(GMPE):
        pass

    class BooreAtkinson2008(GMPE):
        pass

    class IamNotAGMPE():
        pass


def fake_import(modname):
    if modname == 'openquake.hazardlib.gsim.atkinson_boore_2006':
        return FakeModule
    return type('EmptyFakeModule', (), {})


class AvailableGSIMTestCase(unittest.TestCase):

    def test_get_available_gsims(self):
        with mock.patch('os.listdir') as mock_listdir:
            # returns some file names
            mock_listdir.return_value = [
                '__init__.py', 'base.py', 'atkinson_boore_2006.py',
                'zhao_2006.py', 'README.txt']
            with mock.patch('importlib.import_module', fake_import):
                assert_equal(get_available_gsims().keys(),
                             ['AtkinsonBoore2006', 'BooreAtkinson2008'])
                assert_equal(get_available_gsims().values(),
                             [FakeModule.AtkinsonBoore2006,
                              FakeModule.BooreAtkinson2008])
