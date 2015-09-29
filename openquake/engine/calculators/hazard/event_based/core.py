# Copyright (c) 2010-2015, GEM Foundation.
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
Core calculator functionality for computing stochastic event sets and ground
motion fields using the 'event-based' method.

Stochastic events sets (which can be thought of as collections of ruptures) are
computed given a set of seismic sources and investigation time span (in years).

For more information on computing stochastic event sets, see
:mod:`openquake.hazardlib.calc.stochastic`.

One can optionally compute a ground motion field (GMF) given a rupture, a site
collection (which is a collection of geographical points with associated soil
parameters), and a ground shaking intensity model (GSIM).

For more information on computing ground motion fields, see
:mod:`openquake.hazardlib.calc.gmf`.
"""
from openquake.calculators import event_based
from openquake.engine import engine
from openquake.engine.calculators import calculators
from openquake.engine.performance import EnginePerformanceMonitor


@calculators.add('event_based')
class EBCalculator(event_based.EventBasedCalculator):
    """
    Event Based hazard calculator.
    """
    def __init__(self, job):
        self.job = job
        oq = job.get_oqparam()
        monitor = EnginePerformanceMonitor('event_based', job.id)
        calc_id = engine.get_calc_id(job.id)
        super(EBCalculator, self).__init__(oq, monitor, calc_id)
        job.ds_calc_dir = self.datastore.calc_dir
        job.save()

    def clean_up(self):
        engine.expose_outputs(self.datastore, self.job)
        super(EBCalculator, self).clean_up()
