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

from risklib import api


@tasks.oqtask
@general.with_assets
@stats.count_progress('r')
def event_based(job_id, assets, hazard_getter, hazard_id,
                loss_curve_id, loss_map_ids, insured_curve_id,
                conditional_loss_poes, insured_losses,
                loss_curve_resolution, seed, asset_correlation):
    """
    Celery task for the event based risk calculator.
    """
    general.loss_curve_calculator(
        api.probabilistic_event_based,
        job_id, assets, hazard_getter, hazard_id,
        loss_curve_id, loss_map_ids, insured_curve_id,
        conditional_loss_poes, insured_losses,
        loss_curve_resolution, seed, asset_correlation)
event_based.ignore_result = False


class EventBasedRiskCalculator(general.BaseRiskCalculator):
    #: The core calculation celery task function
    celery_task = event_based

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
    def calculation_parameters(self):
        return dict(
            loss_curve_resolution=self.rc.loss_curve_resolution,
            seed=self.rc.master_seed,
            asset_correlation=self.rc.asset_correlation)

    def create_outputs(self):
        """
        Add loss map ids when conditional loss poes are specified
        """
        outputs = super(ClassicalRiskCalculator, self).create_outputs()
        poes = self.rc.conditional_loss_poes or []

        def create_loss_map(poe):
            """
            Given a poe create a loss map output container associated
            with the current job
            """
            return models.LossMap.objects.create(
                 output=models.Output.objects.create_output(
                     self.job,
                     "Loss Map Set with poe %s" % poe,
                     "loss_map"),
                     poe=poe).pk
        outputs['loss_map_ids'] = dict((poe, create_loss_map(poe))
                                       for poe in poes)
        return outputs
