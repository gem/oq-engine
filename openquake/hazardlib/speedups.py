# The Hazard Library
# Copyright (C) 2012-2016 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.speedups` contains internal utilities for
managing alternative implementation of the same functionality depending on
their availability.
"""
import inspect


class SpeedupsRegistry(object):
    """
    Speedups registry allows to manage alternative implementations
    of functions. Typical use case for it is something like this:

    .. code-block:: python

        # in the module namespace

        def do_foo(foo, bar):
            # code in pure python
            ...

        def do_bar(baz, quux):
            # code in pure python
            ...

        # in the end of the module

        try:
            import _foobar_speedups
        except ImportError:
            import warnings
            warnings.warn("foobar speedups are not available", RuntimeWarning)
        else:
            from openquake.hazardlib import speedups

            def _c_do_foo(foo, bar):
                return _foobar_speedups.do_foo(foo, bar)
            speedups.register(do_foo, _c_do_foo)
            del _c_do_foo

            def _c_do_bar(baz, quux):
                return _foobar_speedups.do_foo(baz, quux)
            speedups.register(do_bar, _c_do_bar)
            del _c_do_bar

    Global registry is being used here. All speedups are enabled by default.
    In order to disable them, use :meth:`disable`.
    """
    def __init__(self):
        self.enabled = True
        self.funcs = {}

    def register(self, func, altfunc):
        """
        Add a function and its alternative implementation to the registry.

        If registry is enabled, function code will be substituted
        by an alternative implementation immediately.

        :param func:
            A function object to patch.
        :param altfunc:
            An alternative implementation of the function. Must have
            the same signature and is supposed to behave exactly
            the same way as ``func``.
        """
        assert inspect.getargspec(func) == inspect.getargspec(altfunc), \
            "functions signatures are different in %s and %s" % \
            (func, altfunc)
        self.funcs[func] = (func.__code__, altfunc.__code__)
        if self.enabled:
            # here we substitute the "func_code" attribute of the function,
            # which allows us not to worry of when and how is this function
            # being imported by other modules
            func.__code__ = altfunc.__code__

    def enable(self):
        """
        Set implementation to "alternative" for all the registered functions.
        """
        for func in self.funcs:
            origcode, altcode = self.funcs[func]
            func.__code__ = altcode
        self.enabled = True

    def disable(self):
        """
        Set implementation to "original" for all the registered functions.
        """
        for func in self.funcs:
            origcode, altcode = self.funcs[func]
            func.__code__ = origcode
        self.enabled = False


global_registry = SpeedupsRegistry()

#: Global (default) registry :meth:`register`.
register = global_registry.register
#: Global (default) registry :meth:`enable`.
enable = global_registry.enable
#: Global (default) registry :meth:`disable`.
disable = global_registry.disable
