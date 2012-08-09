# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
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
Module :mod:`nhlib.speedups` contains internal utilities for managing
alternative implementation of the same functionality depending on their
availability.
"""
import inspect


# TODO: document
# TODO: unittest

class SpeedupsRegistry(object):
    def __init__(self):
        self.enabled = True
        self.funcs = {}

    def register(self, func, fastfunc):
        assert inspect.getargspec(func) == inspect.getargspec(fastfunc), \
               "functions signatures are different in %s and %s" % \
               (func, fastfunc)
        self.funcs[func] = (func.func_code, fastfunc.func_code)
        if self.enable:
            func.func_code = fastfunc.func_code

    def enable(self):
        for func in self.funcs:
            origcode, fastcode = self.funcs[func]
            func.func_code = fastcode
        self.enable = True

    def disable(self):
        for func in self.funcs:
            origcode, fastcode = self.funcs[func]
            func.func_code = origcode
        self.enable = False


speedups = SpeedupsRegistry()

register = speedups.register
enable = speedups.enable
disable = speedups.disable

del speedups
