# Copyright (c) 2015, GEM Foundation.
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
Core functionality for the classical damage risk calculator.
"""

from openquake.calculators import classical_damage
from openquake.engine import engine
from openquake.engine.calculators import calculators
from openquake.engine.performance import EnginePerformanceMonitor


@calculators.add('classical_damage')
class ClassicalDamageCalculator(classical_damage.ClassicalDamageCalculator):
    """
    Classical PSHA risk calculator. Computes loss curves and loss maps
    for a given set of assets.
    """
    def __init__(self, job):
        self.job = job
        oq = job.get_oqparam()
        monitor = EnginePerformanceMonitor('classical_damage', job.id)
        calc_id = engine.get_calc_id(job.id)
        super(ClassicalDamageCalculator, self).__init__(oq, monitor, calc_id)
        job.ds_calc_dir = self.datastore.calc_dir
        job.save()

    def clean_up(self):
        engine.expose_outputs(self.datastore, self.job)
        super(ClassicalDamageCalculator, self).clean_up()
