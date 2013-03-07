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

from collections import OrderedDict
import numpy

from django import db

from openquake.risklib import api, scientific

from openquake.engine.calculators.risk import hazard_getters
from openquake.engine.calculators.risk import general
from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine import logs
from openquake.engine.calculators import base


@tasks.oqtask
@general.count_progress_risk('r')
def event_based(job_id, hazard,
                seed, vulnerability_function,
                output_containers,
                conditional_loss_poes, insured_losses,
                time_span, tses,
                loss_curve_resolution, asset_correlation,
                hazard_montecarlo_p):
    """
    Celery task for the event based risk calculator.

    :param job_id: the id of the current
        :class:`openquake.engine.db.models.OqJob`
    :param dict hazard:
      A dictionary mapping IDs of
      :class:`openquake.engine.db.models.Output` (with output_type set
      to 'gmf_collection') to a tuple where the first element is an
      instance of
      :class:`..hazard_getters.GroundMotionValuesGetter`,
      and the second element is the corresponding weight.
    :param seed:
      the seed used to initialize the rng
    :param dict output_containers: a dictionary mapping hazard Output
      ID to a list (a, b, c, d) where a is the ID of the
      :class:`openquake.engine.db.models.LossCurve` output container used to
      store the computed loss curves; b is the dictionary poe->ID of
      the :class:`openquake.engine.db.models.LossMap` output container used
      to store the computed loss maps; c is the same as a but for
      insured losses; d is the ID of the
      :class:`openquake.engine.db.models.AggregateLossCurve` output container
      used to store the computed loss curves
    :param conditional_loss_poes:
      The poes taken into accout to compute the loss maps
    :param bool insured_losses: True if insured losses should be computed
    :param time_span: the time span considered
    :param tses: time of the stochastic event set
    :param loss_curve_resolution: the curve resolution, i.e. the
    number of points which defines the loss curves
    :param float asset_correlation: a number ranging from 0 to 1
    representing the correlation between the generated loss ratios
    """

    loss_ratio_curves = OrderedDict()
    event_loss_table = dict()

    for hazard_output_id, hazard_data in hazard.items():
        hazard_getter, _ = hazard_data

        (loss_curve_id, loss_map_ids,
         mean_loss_curve_id, quantile_loss_curve_ids,
         insured_curve_id, aggregate_loss_curve_id) = (
             output_containers[hazard_output_id])

        # FIXME(lp). We should not pass the exact same seed for
        # different hazard
        calculator = api.ProbabilisticEventBased(
            vulnerability_function,
            curve_resolution=loss_curve_resolution,
            time_span=time_span,
            tses=tses,
            seed=seed,
            correlation=asset_correlation)

        with logs.tracing('getting input data from db'):
            assets, gmvs_ruptures, missings = hazard_getter()

        if len(assets):
            ground_motion_values = numpy.array(gmvs_ruptures)[:, 0]
            rupture_id_matrix = numpy.array(gmvs_ruptures)[:, 1]
        else:
            # we are relying on the fact that if all the hazard_getter
            # in this task will either return some results or they all
            # return an empty result set.
            logs.LOG.info("Exit from task as no asset could be processed")
            base.signal_task_complete(
                job_id=job_id,
                event_loss_table=dict(),
                num_items=len(missings))
            return

        with logs.tracing('computing risk'):
            loss_ratio_matrix, loss_ratio_curves[hazard_output_id] = (
                calculator(ground_motion_values))

        with logs.tracing('writing results'):
            with db.transaction.commit_on_success(using='reslt_writer'):
                for i, loss_ratio_curve in enumerate(
                        loss_ratio_curves[hazard_output_id]):
                    asset = assets[i]

                    # loss curves
                    general.write_loss_curve(
                        loss_curve_id, asset,
                        loss_ratio_curve.ordinates,
                        loss_ratio_curve.abscissae,
                        scientific.average_loss(
                            loss_ratio_curve.abscissae,
                            loss_ratio_curve.ordinates))

                    # loss maps
                    for poe in conditional_loss_poes:
                        general.write_loss_map_data(
                            loss_map_ids[poe], asset,
                            scientific.conditional_loss_ratio(
                                loss_ratio_curve, poe))

                    # insured losses
                    if insured_losses:
                        insured_loss_curve = scientific.event_based(
                            scientific.insured_losses(
                                loss_ratio_matrix[i],
                                asset.value,
                                asset.deductible,
                                asset.ins_limit),
                            tses,
                            time_span,
                            loss_curve_resolution)

                        insured_loss_curve.abscissae = (
                            insured_loss_curve.abscissae / asset.value)

                        general.write_loss_curve(
                            insured_curve_id, asset,
                            insured_loss_curve.ordinates,
                            insured_loss_curve.abscissae,
                            scientific.average_loss(
                                insured_loss_curve.abscissae,
                                insured_loss_curve.ordinates))

                # update the event loss table of this task
                for i, asset in enumerate(assets):
                    for j, rupture_id in enumerate(rupture_id_matrix[i]):
                        loss = loss_ratio_matrix[i][j] * asset.value
                        event_loss_table[rupture_id] = (
                            event_loss_table.get(rupture_id, 0) + loss)

                # update the aggregate losses
                aggregate_losses = sum(
                    loss_ratio_matrix[i] * asset.value
                    for i, asset in enumerate(assets))
                general.update_aggregate_losses(
                    aggregate_loss_curve_id, aggregate_losses)

    # compute mean and quantile loss curves if multiple hazard
    # realizations are computed
    if len(hazard) > 1 and (mean_loss_curve_id or quantile_loss_curve_ids):
        weights = [data[1] for _, data in hazard.items()]

        with logs.tracing('writing curve statistics'):
            with db.transaction.commit_on_success(using='reslt_writer'):
                loss_ratio_curve_matrix = loss_ratio_curves.values()

                # here we are relying on the fact that assets do not
                # change across different logic tree realizations (as
                # the hazard grid does not change, so the hazard
                # getters always returns the same assets)
                for i, asset in enumerate(assets):
                    general.curve_statistics(
                        asset,
                        loss_ratio_curve_matrix[i],
                        weights,
                        mean_loss_curve_id,
                        quantile_loss_curve_ids,
                        hazard_montecarlo_p,
                        assume_equal="image")

    base.signal_task_complete(job_id=job_id,
                              num_items=len(assets) + len(missings),
                              event_loss_table=event_loss_table)
event_based.ignore_result = False


class EventBasedRiskCalculator(general.BaseRiskCalculator):
    """
    Probabilistic Event Based PSHA risk calculator. Computes loss
    curves, loss maps, aggregate losses and insured losses for a given
    set of assets.
    """

    #: The core calculation celery task function
    core_calc_task = event_based

    hazard_getter = hazard_getters.GroundMotionValuesGetter

    def __init__(self, job):
        super(EventBasedRiskCalculator, self).__init__(job)
        self.event_loss_table = dict()

    def task_completed_hook(self, message):
        """
        Updates the event loss table
        """
        for rupture_id, aggregate_loss in message['event_loss_table'].items():
            self.event_loss_table[rupture_id] = (
                self.event_loss_table.get(rupture_id, 0) + aggregate_loss)

    def pre_execute(self):
        """
        Override the default pre_execute to provide more detailed
        validation.

        2) If insured losses are required we check for the presence of
        the deductible and insurance limit
        """
        super(EventBasedRiskCalculator, self).pre_execute()

        if (self.rc.insured_losses and
            self.rc.exposure_model.exposuredata_set.filter(
                (db.models.Q(deductible__isnull=True) |
                 db.models.Q(ins_limit__isnull=True))).exists()):
            raise RuntimeError(
                "Deductible or insured limit missing in exposure")

    def post_process(self):
        # compute aggregate loss curves
        for hazard_output in self.considered_hazard_outputs():
            loss_curve = models.LossCurve.objects.get(
                hazard_output=hazard_output,
                aggregate=True, output__oq_job=self.job)
            curve_data = loss_curve.aggregatelosscurvedata

            tses, time_span = self.hazard_times()

            # Finalize the aggregate losses by running the event based
            # algorithm on it and by computing the average loss

            if len(curve_data.losses):
                aggregate_loss_curve = scientific.event_based(
                    curve_data.losses, tses, time_span,
                    curve_resolution=self.rc.loss_curve_resolution)

                curve_data.losses = aggregate_loss_curve.abscissae.tolist()
                curve_data.poes = aggregate_loss_curve.ordinates.tolist()
                curve_data.average_loss = scientific.average_loss(
                    curve_data.losses, curve_data.poes)
                curve_data.save()

        event_loss_table_output = models.Output.objects.create_output(
            self.job, "Event Loss Table", "event_loss")

        for rupture_id, aggregate_loss in self.event_loss_table.items():
            models.EventLoss.objects.create(
                output=event_loss_table_output,
                rupture_id=rupture_id,
                aggregate_loss=aggregate_loss)

    def create_getter(self, output, assets):
        """
        See :method:`..general.BaseRiskCalculator.create_getter`
        """
        if not output.output_type in ('gmf', 'complete_lt_gmf'):
            raise RuntimeError(
                "The provided hazard output is not a ground motion field")

        gmf = output.gmfcollection

        if gmf.lt_realization:
            weight = gmf.lt_realization.weight
        else:
            weight = None

        hazard_getter = self.hazard_getter(
            gmf.id, self.imt, assets, self.rc.best_maximum_distance)
        return (hazard_getter, weight)

    def hazard_outputs(self, hazard_calculation):
        """
        :returns: a list of :class:`openquake.engine.db.models.Output` hazard
        object that stores the ground motion fields associated with
        `hazard_calculation` and a logic tree realization
        """

        # In order to avoid a big joint to filter per imt now, we let
        # the hazard getter do the job
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
        # atm, no complete_logic_tree gmf are supported
        realizations_nr = 1

        time_span = self.hc.investigation_time
        return (time_span,
                self.hc.ses_per_logic_tree_path * realizations_nr * time_span)

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

        return [self.rc.conditional_loss_poes or [],
                self.rc.insured_losses,
                time_span, tses,
                self.rc.loss_curve_resolution, correlation,
                self.hc.number_of_logic_tree_samples == 0]

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
            loss_curve=aggregate_loss_curve,
            average_loss=0)

        if self.rc.insured_losses:
            insured_curve_id = (
                models.LossCurve.objects.create(
                    insured=True,
                    hazard_output=hazard_output,
                    output=models.Output.objects.create_output(
                        self.job,
                        "Insured Loss Curve Set for hazard %s" % hazard_output,
                        "loss_curve")
                ).id)
        else:
            insured_curve_id = None

        return outputs + [insured_curve_id, aggregate_loss_curve.id]
