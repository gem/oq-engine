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

# pylint: disable=W0232

"""
This module performs risk calculations using the deterministic
event based approach.
"""

from openquake.risk.job import RiskJobMixin


class DeterministicEventBasedMixin:
    """Deterministic Event Based method for performing risk calculations.

    Note that this mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the job configuration file."""

    def execute(self):
        """Entry point for triggering the computation."""

        print "Deterministic Event Based risk"

        return [True]


RiskJobMixin.register("Deterministic", DeterministicEventBasedMixin)
