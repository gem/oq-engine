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

    def initialize(self, *args, **kwargs):
        """Implement this method in subclasses to record pre-execution stats,
        estimate the calculation size, etc."""

    def pre_execute(self, *args, **kwargs):
        """Implement this method in subclasses to perform pre-execution
        functions, such as instantiating objects need for the calculation and
        loading calculation data into a cache."""

    def execute(self, *args, **kwargs):
        """This is only method that subclasses are required to implement. This
        should contain all of the calculation logic."""
        raise NotImplementedError()

    def post_execute(self, *args, **kwargs):
        """Implement this method in subclasses to perform post-execution
           functions, such as result serialization."""

    def clean_up(self, *args, **kwargs):
        """Implement this method in subclasses to perform clean-up actions
           like garbage collection, etc."""


class CalculatorNext(object):
    """
    Base class for all calculators.

    :param job: :class:`openquake.db.models.OqJob` instance.
    """

    def __init__(self, job):
        self.job = job

    def pre_execute(self):
        """
        Override this method in subclasses to record pre-execution stats,
        initialize result records, perform detailed parsing of input data, etc.
        """

    def execute(self):
        """
        This is the only method that subclasses are required to implement. This
        should contain all of the core calculation logic concerned with
        splitting up and distributing work.
        """
        raise NotImplementedError()

    def post_execute(self):
        """
        Override this method in subclasses to any necessary post-execution
        actions, such as the consolidation of partial results.
        """

    def post_process(self):
        """
        Override this method in subclasses to perform post processing steps,
        such as computing mean results from a set of curves or plotting maps.
        """

    def export(self, *args, **kwargs):
        """Implement this method in subclasses to write results
           to places other than the database."""

    def clean_up(self, *args, **kwargs):
        """Implement this method in subclasses to perform clean-up actions
           like garbage collection, etc."""
