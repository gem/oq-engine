import mock
from nose.tools import assert_equal
from nhlib.gsim import get_available_gsims
from nhlib.gsim.base import GMPE

class FakeModule(object):
    'An object faking a module containing only one subclass of GMPE'
    class AtkinsonBoore2006(GMPE):
        pass
    class IamNotAGMPE():
        pass

def fake_import(modname):
    if modname == 'nhlib.gsim.atkinson_boore_2006':
        return FakeModule
    return type('EmptyFakeModule', (), {})

def test_get_available_gsims():
    with mock.patch('os.listdir') as mock_listdir:
        # returns some file names
        mock_listdir.return_value = [
            '__init__.py', 'base.py', 'atkinson_boore_2006.py', 'zhao_2006.py',
            'README.txt']
        with mock.patch('importlib.import_module', fake_import):
            assert_equal(get_available_gsims(), ['AtkinsonBoore2006'])
