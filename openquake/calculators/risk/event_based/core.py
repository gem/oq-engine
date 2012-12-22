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
from openquake.utils import tasks
from openquake.utils import stats


@tasks.oqtask
@general.with_assets
@stats.count_progress('r')
def event_based(job_id, assets, hazard_getter, hazard_id, loss_curve_id):
    """
    Celery task for the event based risk calculator.
    """
    raise NotImplementedError("Implement me, please")


class EventBasedRiskCalculator(general.BaseRiskCalculator):
    """
    Probabilistic Event Based PSHA risk calculator. Computes loss
    curves, loss maps, aggregate losses and insured losses for a given
    set of assets.
    """

    #: The core calculation celery task function
    celery_task = event_based

    def pre_execute(self):
        """
        In Event Based we get the intensity measure type considered
        from the vulnerability model, then we check that the hazard
        calculation includes outputs with that intensity measure type
        """
        super(EventBasedRiskCalculator, self).pre_execute()

        imt = self.rc.model("vulnerability").imt

        hc = self.rc.hazard_output.oq_job.hazard_calculation

        allowed_imts = hc.intensity_measure_types_and_levels.keys()

        if not imt in allowed_imts:
            raise RuntimeError(
                "There is no ground motion field in the intensity measure %s" %
                imt)

    @property
    def hazard_id(self):
        """
        The ID of the :class:`openquake.db.models.GmfCollection`
        object that stores the ground motion fields used by the risk
        calculation
        """

        if not self.rc.hazard_output.is_ground_motion_field():
            raise RuntimeError(
                "The provided hazard output is not a ground motion field")

        return self.rc.hazard_output.gmfcollection.id

    @property
    def hazard_getter(self):
        """
        The hazard getter used by the calculation.

        :returns: A string used to get the hazard getter class from
        `openquake.calculators.risk.hazard_getters.HAZARD_GETTERS`
        """
        return "ground_motion_field"
