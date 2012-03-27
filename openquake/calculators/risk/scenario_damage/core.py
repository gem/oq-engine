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

# pylint: disable=W0232

"""
This module performs risk calculations using the scenario
damage assessment approach.
"""

from openquake import logs
from openquake.calculators.risk import general


LOGGER = logs.LOG


class ScenarioDamageRiskCalculator(general.BaseRiskCalculator):
    """Scenario Damage method for performing risk calculations."""

    def pre_execute(self):
        pass

    def execute(self):
        """Entry point for triggering the computation."""

        LOGGER.debug("Executing scenario damage risk computation [TODO]")
