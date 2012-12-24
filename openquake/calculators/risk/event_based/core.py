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
                imt, time_span, tses,
                loss_curve_resolution, seed, asset_correlation):
    """
    Celery task for the event based risk calculator.
    """
    vulnerability_model = general.fetch_vulnerability_model(job_id)

    # FIXME(lp): refactor risklib. there is no reason to propagate
    # time_span and tses in an hazard getter
    hazard_getter = general.hazard_getter(
        hazard_getter, hazard_id, imt, time_span, tses)

    calculator = api.probabilistic_event_based(
        vulnerability_model,
        curve_resolution=loss_curve_resolution,
        seed=seed,
        correlation_type=asset_correlation)

    # FIXME. Save unmodified calculator, as the decorated one does not
    # support aggregate losses at the moment.
    eb_calculator = calculator

    # if we need to compute the insured losses, we add the proper
    # risklib aggregator
    if insured_losses:
        calculator = api.insured_losses(calculator)

    # if we need to compute the loss maps, we add the proper risk
    # aggregator
    if conditional_loss_poes:
        calculator = api.conditional_losses(conditional_loss_poes, calculator)

    with db.transaction.commit_on_success(using='reslt_writer'):
        logs.LOG.debug(
            'launching compute_on_assets over %d assets' % len(assets))
        for asset_output in api.compute_on_assets(
            assets, hazard_getter, calculator):

            loss_curve = general.write_loss_curve(loss_curve_id, asset_output)

            if asset_output.conditional_losses:
                general.write_loss_map(loss_map_ids, asset_output)

            if asset_output.insured_losses:
                general.write_loss_curve(insured_curve_id, asset_output)

    # poes in event based calculator depends only on the number of
    # ground motion values and the loss curve resolution, which are
    # both constants in the calculation. So, as we poes we take
    general.update_aggregate_losses(
        aggregate_loss_curve_id,
        eb_calculator.aggregate_losses, loss_curve.poes)
event_based.ignore_result = False


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
        Override the default pre_execute to provide more detailed
        validation.

        1) In Event Based we get the intensity measure type considered
        from the vulnerability model, then we check that the hazard
        calculation includes outputs with that intensity measure type

        2) If insured losses are required we check for the presence of
        the deductible and insurance limit
        """
        super(EventBasedRiskCalculator, self).pre_execute()

        hc = self.rc.hazard_output.oq_job.hazard_calculation

        allowed_imts = hc.intensity_measure_types_and_levels.keys()

        if not self.imt in allowed_imts:
            raise RuntimeError(
                "There is no ground motion field in the intensity measure %s" %
                self.imt)

        if self.rc.insured_losses and models.ExposureData.objects.filter(
                exposure_model__id=self.exposure_model_id).filter(
                    (db.models.Q(deductible__isnull=True) |
                     db.models.Q(ins_limit__isnull=True))).exists():
            raise RuntimeError(
                "Deductible or insured limit missing in exposure")

    @property
    def imt(self):
        """
        The intensity measure type considered by this calculator.
        It is got by the vulnerability model
        """
        return self.rc.model("vulnerability").imt

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
        """
        Calculator specific parameters
        """

        hc = self.rc.hazard_calculation

        # atm, no complete_logic_tree gmf are supported
        number_of_realizations = 1

        time_span = hc.investigation_time
        tses = hc.ses_per_logic_tree_path * number_of_realizations * time_span

        return dict(
            insured_losses=self.rc.insured_losses,
            conditional_loss_poes=self.rc.conditional_loss_poes,
            tses=tses,
            time_span=time_span,
            imt=self.imt,
            loss_curve_resolution=self.rc.loss_curve_resolution,
            seed=self.rc.master_seed,
            asset_correlation=self.rc.asset_correlation)

    def create_outputs(self):
        """
        Add Aggregate loss curve and Insured Curve output containers
        """
        outputs = super(EventBasedRiskCalculator, self).create_outputs()

        aggregate_loss_curve = models.LossCurve.objects.create(
                aggregate=True,
                output=models.Output.objects.create_output(
                    self.job, "Aggregate Loss Curve", "agg_loss_curve"))
        outputs['aggregate_loss_curve_id'] = aggregate_loss_curve.id

        # for aggregate loss curve, we need to create also the
        # aggregate loss individual curve object
        models.AggregateLossCurveData.objects.create(
            loss_curve=aggregate_loss_curve)

        outputs['insured_curve_id'] = (
            models.LossCurve.objects.create(
                insured=True,
                output=models.Output.objects.create_output(
                    self.job,
                    "Insured Loss Curve Set",
                    "ins_loss_curve")).id)
        return outputs

    @property
    def hazard_getter(self):
        """
        The hazard getter used by the calculation.

        :returns: A string used to get the hazard getter class from
        `openquake.calculators.risk.hazard_getters.HAZARD_GETTERS`
        """
        return "ground_motion_field"
