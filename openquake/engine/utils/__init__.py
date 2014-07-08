"""This is needed for imports to work."""


import decimal
import os
import inspect
import importlib
import collections


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


def get_available_calculators(pkg, job_type):
    """
    :param pkg: a Python package
    :param str job_type: "hazard" or "risk"
    :returns: an OrderedDict {calc_mode: calc_class} built by looking
    at all the calculators in the package.
    """
    clsname = job_type.capitalize() + 'Calculator'
    calc = {}  # calc_mode -> calc_class
    for modname in get_core_modules(pkg):
        name = modname.split('.')[-2]  # openquake...<name>.core
        mod = importlib.import_module(modname)
        for cls in mod.__dict__.itervalues():
            if inspect.isclass(cls) and clsname in cls.__name__:
                calc[name] = cls
    return collections.OrderedDict((k, calc[k]) for k in sorted(calc))


def get_calculator_class(job_type, calc_mode):
    """
    :param str job_type: "hazard" or "risk"
    :param str calc_mode: a calculator identifier
    :returns: a Calculator class
    """
    assert job_type in ("hazard", "risk"), job_type
    pkg = importlib.import_module('openquake.engine.calculators.%s' % job_type)
    return get_available_calculators(pkg, job_type)[calc_mode]


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
