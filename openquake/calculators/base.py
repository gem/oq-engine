# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


"""Base code for calculator classes."""


class Calculator(object):
    """Base abstract class for all calculators."""

    def __init__(self, job_ctxt):
        """
        :param job_ctxt: :class:`openquake.engine.JobContext` instance.
        """
        self.job_ctxt = job_ctxt

    def initialize(self):
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
