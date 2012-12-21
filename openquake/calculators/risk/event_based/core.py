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

from django import db

from openquake.calculators.risk import general
from openquake.db import models
from openquake.utils import tasks, stats
from openquake import logs

from risklib import api


@tasks.oqtask
@general.with_assets
@stats.count_progress('r')
def event_based(job_id, assets, hazard_getter, hazard_id,
                loss_curve_id, loss_map_ids,
                insured_curve_id, aggregate_loss_curve_id,
                conditional_loss_poes, insured_losses,
                loss_curve_resolution, seed, asset_correlation):
    """
    Celery task for the event based risk calculator.
    """
    vulnerability_model = general.fetch_vulnerability_model(job_id)

    hazard_getter = general.hazard_getter(hazard_getter, hazard_id)

    calculator = api.probabilistic_event_based(
        vulnerability_model, loss_curve_resolution, seed, asset_correlation)

    # if we need to compute the loss maps, we add the proper risk
    # aggregator
    if conditional_loss_poes:
        calculator = api.conditional_losses(conditional_loss_poes, calculator)

    # if we need to compute the insured losses, we add the proper
    # risklib aggregator
    if insured_losses:
        calculator = api.insured_losses(calculator)

    with db.transaction.commit_on_success(using='reslt_writer'):
        logs.LOG.debug(
            'launching compute_on_assets over %d assets' % len(assets))
        for asset_output in api.compute_on_assets(
            assets, hazard_getter, calculator):

            general.write_loss_curve(loss_curve_id, asset_output)

            if asset_output.conditional_losses:
                general.write_loss_map(loss_map_ids, asset_output)

            if asset_output.insured_losses:
                general.write_loss_curve(insured_curve_id, asset_output)

    # by using #filter and #update django prevents possible race conditions
    models.AggregateLossData.objects.filter(
        output__id=aggregate_loss_curve_id).update(
            losses=db.models.F('losses') + calculator.aggregate_losses)
event_based.ignore_result = False


class EventBasedRiskCalculator(general.BaseRiskCalculator):
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
    def calculation_parameters(self):
        return dict(
            loss_curve_resolution=self.rc.loss_curve_resolution,
            seed=self.rc.master_seed,
            asset_correlation=self.rc.asset_correlation)

    def create_outputs(self):
        outputs = super(EventBasedRiskCalculator, self).create_outputs()
        outputs['aggregate_loss_curve_id'] = (
            models.AggregateLossCurveData.objects.create(
                output=models.Output.objects.create_output(
                    self.job,
                    "Aggregate Loss Curve Set",
                    "agg_loss_curve")).id)
        return outputs
