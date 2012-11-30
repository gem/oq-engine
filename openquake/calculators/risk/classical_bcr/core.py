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

"""
Core functionality for the classical PSHA risk calculator.
"""


from openquake.calculators.risk import general
from openquake.calculators.risk.classical import core as classical
from openquake.utils import stats
from openquake.utils import tasks
from openquake import logs


@tasks.oqtask
@general.with_assets
@stats.count_progress('r')
def classical_bcr(job_id, assets, hazard_getter, hazard_id,
                  bcr_distribution_id,
                  lrem_steps_per_interval,
                  asset_life_expectancy,
                  interest_rate):
    logs.LOG.debug('Implement me')


class ClassicalRiskCalculatorWithBCR(classical.ClassicalRiskCalculator):
    celery_task = classical_bcr
