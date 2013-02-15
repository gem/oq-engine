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


def get_available_calculators(pkg):
    """
    :param pkg: a Python package
    :return: an OrderedDict {calc_mode: calc_class} built by looking at all the
    calculators in the package.
    """
    calc = {}  # calc_mode -> calc_class
    for modname in get_core_modules(pkg):
        name = modname.split('.')[-2]  # openquake...<name>.core
        mod = importlib.import_module(modname)
        for cls in mod.__dict__.itervalues():
            if inspect.isclass(cls) and 'Calculator' in cls.__name__:
                calc[name] = cls
    return collections.OrderedDict((k, calc[k]) for k in sorted(calc))


def get_calculator_class(pkg, calc_mode):
    """
    :param pkg: a Python package
    :param str calc_mode: a calculator identifier
    :return: a Calculator class
    """
    return get_available_calculators(pkg)[calc_mode]
