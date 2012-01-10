# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""Base code for calculator classes."""


class Calculator(object):
    """Base abstract class for all calculators."""

    def __init__(self, calc_proxy):
        """
        :param calc_proxy: :class:`openquake.engine.CalculationProxy` instance.
        """
        self.calc_proxy = calc_proxy

    def analyze(self):
        """Implement this method in subclasses to record pre-execution stats,
        estimate the calculation size, etc."""

    def pre_execute(self):
        """Implement this method in subclasses to perform pre-execution
        functions, such as instantiating objects need for the calculation and
        loading calculation data into a cache."""

    def execute(self):
        """This is only method that subclasses are required to implement. This
        should contain all of the calculation logic."""
        raise NotImplementedError()

    def post_execute(self):
        """Implement this method in subclasses to perform post-execution
        functions, such as result serialization and garbage collection."""
