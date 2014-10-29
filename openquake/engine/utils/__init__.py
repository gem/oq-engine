"""This is needed for imports to work."""

import os
import decimal
import operator

from openquake.commonlib.general import CallableDict, import_all


# an ordered dictionary of calculator classes
calculators = CallableDict(operator.attrgetter('calculation_mode'))

import_all('openquake.engine.calculators.hazard')
import_all('openquake.engine.calculators.risk')


def round_float(value):
    """
    Takes a float and rounds it to a fixed number of decimal places.

    This function makes uses of the built-in
    :py:method:`decimal.Decimal.quantize` to limit the precision.

    The 'round-half-even' algorithm is used for rounding.

    This should give us what can be considered 'safe' float values for
    geographical coordinates (to side-step precision and rounding errors).

    :type value: float

    :returns: the input value rounded to a hard-coded fixed number of decimal
    places
    """
    float_decimal_places = 7
    quantize_str = '0.' + '0' * float_decimal_places

    return float(
        decimal.Decimal(str(value)).quantize(
            decimal.Decimal(quantize_str),
            rounding=decimal.ROUND_HALF_EVEN))


def get_core_modules(pkg):
    """
    :param pkg: a Python package
    :return: a sorted list of the fully qualified module names ending in "core"
    """
    modules = []
    pkgdir = pkg.__path__[0]
    for name in os.listdir(pkgdir):
        fullname = os.path.join(pkgdir, name)
        if os.path.isdir(fullname) and os.path.exists(
                os.path.join(fullname, '__init__.py')):  # is subpackage
            if os.path.exists(os.path.join(fullname, 'core.py')):
                modules.append('%s.%s.core' % (pkg.__name__, name))
    return sorted(modules)


class FileWrapper(object):
    """
    Context-managed object which accepts either a path or a file-like object.

    Behaves like a file.
    """

    def __init__(self, dest, mode='r'):
        self._dest = dest
        self._mode = mode
        self._file = None

    def __enter__(self):
        if isinstance(self._dest, (basestring, buffer)):
            self._file = open(self._dest, self._mode)
        else:
            # assume it is a file-like; don't change anything
            self._file = self._dest
        return self._file

    def __exit__(self, *args):
        self._file.close()
