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

from nhlib import correlation

from openquake.calculators.hazard import general as haz_general
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks

#: Ground motion correlation model map
GM_CORRELATION_MODEL_MAP = {
    'JB2009': correlation.JB2009CorrelationModel,
}


@utils_tasks.oqtask
@stats.progress_indicator('h')
def stochastic_event_sets(job_id, lt_rlz_id, src_ids):
    """
    Celery task for the stochastic event set calculator.

    Samples logic trees and calls the stochastic event set calculator.

    Once stochastic event sets are calculated, results will be saved to the
    database. See :class:`openquake.db.models.SESCollection`.

    Once all of this work is complete, a signal will be sent via AMQP to let
    the control noe know that the work is complete. (If there is any work left
    to be dispatched, this signal will indicate to the control node that more
    work can be enqueued.)

    :param int job_id:
        ID of the currently running job.
    :param lt_rlz_id:
        Id of logic tree realization model to calculate for.
    :param src_ids:
        List of ids of parsed source models from which we will generate
        stochastic event sets/ruptures.
    """


class EventBasedHazardCalculator(haz_general.BaseHazardCalculatorNext):
    """
    Probabilistic Event-Based hazard calculator. Computes stochastic event sets
    and (optionally) ground motion fields.
    """

    core_calc_task = stochastic_event_sets

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails: parsing and
        initializing sources, parsing and initializing the site model (if there
        is one), and generating logic tree realizations. (The latter piece
        basically defines the work to be done in the `execute` phase.)
        """

        # Parse logic trees and create source Inputs.
        self.initialize_sources()

        # Deal with the site model and compute site data for the calculation
        # (if a site model was specified, that is).
        self.initialize_site_model()

        # Now bootstrap the logic tree realizations and related data.
        # This defines for us the "work" that needs to be done when we reach
        # the `execute` phase.
        self.initialize_realizations()

    def execute(self):
        # TODO: implement me
        print "execute"

    def post_execute(self):
        # TODO: implement me
        print "post_execute"

    def post_process(self):
        # TODO: implement me
        print "post_process"
