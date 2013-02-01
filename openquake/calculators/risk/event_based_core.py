# Copyright (c) 2010-2013, GEM Foundation.
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

from risklib import api, scientific

from openquake.calculators.risk import general
from openquake.db import models
from openquake.utils import tasks, stats
from openquake import logs
from openquake.calculators import base


@tasks.oqtask
@stats.count_progress('r')
def event_based(job_id, assets, hazard_getter, hazard,
                seed, vulnerability_function,
                output_containers,
                conditional_loss_poes, insured_losses,
                imt, time_span, tses,
                loss_curve_resolution, asset_correlation):
    """
    Celery task for the event based risk calculator.

    :param job_id: the id of the current :class:`openquake.db.models.OqJob`
    :param assets: the list of `:class:risklib.scientific.Asset`
    instances considered
    :param hazard_getter: the name of an hazard getter to be used
    :param dict hazard:
      A dictionary mapping hazard Output ID to GmfCollection ID
    :param seed: the seed used to initialize the rng

    :param dict output_containers: a dictionary mapping hazard Output
      ID to a list (a, b, c, d) where a is the ID of the
      :class:`openquake.db.models.LossCurve` output container used to
      store the computed loss curves; b is the dictionary poe->ID of
      the :class:`openquake.db.models.LossMap` output container used
      to store the computed loss maps; c is the same as a but for
      insured losses; d is the ID of the
      :class:`openquake.db.models.AggregateLossCurve` output container
      used to store the computed loss curves
    :param conditional_loss_poes:
      The poes taken into accout to compute the loss maps
    :param bool insured_losses: True if insured losses should be computed
    :param str imt: the imt used to filter ground motion fields
    :param time_span: the time span considered
    :param tses: time of the stochastic event set
    :param loss_curve_resolution: the curve resolution, i.e. the
    number of points which defines the loss curves
    :param float asset_correlation: a number ranging from 0 to 1
    representing the correlation between the generated loss ratios
    """

    for hazard_output_id, hazard_data in hazard.items():
        hazard_id, _ = hazard_data

        (loss_curve_id, loss_map_ids,
         insured_curve_id, aggregate_loss_curve_id) = (
             output_containers[hazard_output_id])

        hazard_getter = general.hazard_getter(hazard_getter, hazard_id, imt)

        calculator = api.ProbabilisticEventBased(
            vulnerability_function,
            curve_resolution=loss_curve_resolution,
            time_span=time_span,
            tses=tses,
            seed=seed,
            correlation=asset_correlation)

        if insured_losses:
            calculator = api.InsuredLosses(calculator)

        # if we need to compute the loss maps, we add the proper risk
        # aggregator
        if conditional_loss_poes:
            calculator = api.ConditionalLosses(
                conditional_loss_poes, calculator)

        with logs.tracing('getting hazard'):
            ground_motion_fields = [hazard_getter(asset.site)
                                    for asset in assets]

        with logs.tracing('computing risk over %d assets' % len(assets)):
            asset_outputs = calculator(assets, ground_motion_fields)

        with logs.tracing('writing results'):
            with db.transaction.commit_on_success(using='reslt_writer'):
                for i, asset_output in enumerate(asset_outputs):
                    general.write_loss_curve(
                        loss_curve_id, assets[i], asset_output)

                    if asset_output.conditional_losses:
                        general.write_loss_map(
                            loss_map_ids, assets[i], asset_output)

                    if asset_output.insured_losses:
                        general.write_loss_curve(
                            insured_curve_id, assets[i], asset_output)

        losses = sum(asset_output.losses for asset_output in asset_outputs)
        general.update_aggregate_losses(aggregate_loss_curve_id, losses)

    base.signal_task_complete(job_id=job_id, num_items=len(assets))
event_based.ignore_result = False


class EventBasedRiskCalculator(general.BaseRiskCalculator):
    """
    Probabilistic Event Based PSHA risk calculator. Computes loss
    curves, loss maps, aggregate losses and insured losses for a given
    set of assets.
    """

    #: The core calculation celery task function
    core_calc_task = event_based

    hazard_getter = "GroundMotionValuesGetter"

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

        hc = self.rc.get_hazard_calculation()

        allowed_imts = hc.intensity_measure_types_and_levels.keys()

        if not self.imt in allowed_imts:
            raise RuntimeError(
                "There is no ground motion field in the intensity measure %s" %
                self.imt)

        if (self.rc.insured_losses and
            self.exposure_model.exposuredata_set.filter(
                (db.models.Q(deductible__isnull=True) |
                 db.models.Q(ins_limit__isnull=True))).exists()):
            raise RuntimeError(
                "Deductible or insured limit missing in exposure")

    def post_process(self):
        for hazard_output in self.considered_hazard_outputs():
            loss_curve = models.LossCurve.objects.get(
                hazard_output=hazard_output,
                aggregate=True, output__oq_job=self.job)
            curve_data = loss_curve.aggregatelosscurvedata

            tses, time_span = self.hazard_times()

            aggregate_loss_curve = scientific.event_based(
                curve_data.losses, tses, time_span,
                curve_resolution=self.rc.loss_curve_resolution)

            curve_data.losses = aggregate_loss_curve.abscissae.tolist()
            curve_data.poes = aggregate_loss_curve.ordinates.tolist()
            curve_data.save()

    def hazard_output(self, output):
        """
        :returns: a tuple with the ID and the weight of the
        :class:`openquake.db.models.GmfCollection` object that stores
        the ground motion fields associated with `output`.
        """

        if not output.is_ground_motion_field():
            raise RuntimeError(
                "The provided hazard output is not a ground motion field")

        gmf = output.gmfcollection

        if gmf.lt_realization:
            weight = gmf.lt_realization.weight
        else:
            weight = None
        return (gmf.id, weight)

    def hazard_outputs(self, hazard_calculation):
        """
        :returns: a list of :class:`openquake.db.models.Output` hazard
        object that stores the ground motion fields associated with
        `hazard_calculation` and a logic tree realization
        """
        return hazard_calculation.oqjob_set.filter(status="complete").latest(
            'last_update').output_set.filter(
                output_type='gmf',
                gmfcollection__lt_realization__isnull=False,
                gmfcollection__complete_logic_tree_gmf=False).order_by('id')

    def hazard_times(self):
        """
        Return the hazard investigation time related to the ground
        motion field and the so-called time representative of the
        stochastic event set
        """
        hc = self.rc.get_hazard_calculation()

        # atm, no complete_logic_tree gmf are supported
        realizations_nr = 1

        time_span = hc.investigation_time
        return (time_span,
                hc.ses_per_logic_tree_path * realizations_nr * time_span)

    @property
    def calculator_parameters(self):
        """
        Calculator specific parameters
        """

        time_span, tses = self.hazard_times()

        if self.rc.asset_correlation is None:
            correlation = 0
        else:
            correlation = self.rc.asset_correlation
        return [self.rc.conditional_loss_poes,
                self.rc.insured_losses,
                self.imt, time_span, tses,
                self.rc.loss_curve_resolution, correlation]

    def create_outputs(self, hazard_output):
        """
        Add Aggregate loss curve and Insured Curve output containers
        """
        outputs = super(EventBasedRiskCalculator, self).create_outputs(
            hazard_output)

        aggregate_loss_curve = models.LossCurve.objects.create(
            aggregate=True,
            hazard_output=hazard_output,
            output=models.Output.objects.create_output(
                self.job, "Aggregate Loss Curve for hazard %s" % hazard_output,
                "agg_loss_curve"))

        # for aggregate loss curve, we need to create also the
        # aggregate loss individual curve object
        models.AggregateLossCurveData.objects.create(
            loss_curve=aggregate_loss_curve)

        if self.rc.insured_losses:
            insured_curve_id = (
                models.LossCurve.objects.create(
                    insured=True,
                    hazard_output=hazard_output,
                    output=models.Output.objects.create_output(
                        self.job,
                        "Insured Loss Curve Set for hazard %s" % hazard_output,
                        "ins_loss_curve")
                ).id)
        else:
            insured_curve_id = None

        return outputs + [insured_curve_id, aggregate_loss_curve.id]
