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

import random
from collections import OrderedDict
import numpy

from django import db

from openquake.hazardlib.geo import mesh
from openquake.risklib import api, scientific

from openquake.engine.calculators.risk import hazard_getters
from openquake.engine.calculators.risk import general
from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine import logs
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.calculators import base


@tasks.oqtask
@general.count_progress_risk('r')
def event_based(job_id, hazard,
                task_seed, vulnerability_function,
                output_containers,
                statistical_output_containers,
                conditional_loss_poes, insured_losses,
                time_span, tses,
                loss_curve_resolution, asset_correlation,
                sites_disagg,
                mag_bin_width,
                distance_bin_width,
                coordinate_bin_width,
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
    :param task_seed:
      the seed used to initialize the rng
    :param dict output_containers: a dictionary mapping hazard Output
      ID to a list (a, b, c, d, e) where a is the ID of the
      :class:`openquake.engine.db.models.LossCurve` output container used to
      store the computed loss curves; b is the dictionary poe->ID of
      the :class:`openquake.engine.db.models.LossMap` output container used
      to store the computed loss maps; c is the same as a but for
      insured losses; d and e are the IDs of the magnitude_distance and
      coordinate loss fractions disaggregation matrix (
      :class:`openquake.engine.db.models.LossFraction`), respectively.
    :param conditional_loss_poes:
      The poes taken into accout to compute the loss maps
    :param bool insured_losses: True if insured losses should be computed
    :param time_span: the time span considered
    :param tses: time of the stochastic event set
    :param loss_curve_resolution:
      the curve resolution, i.e. the number of points which defines the loss
      curves
    :param sites_disagg:
      A list of Point objects where the disaggregation should occurr
    :param float mag_bin_width:
      Width of magnitude bins when losses are disaggregated
    :param float distance_bin_width:
      Width of distance bins when losses are disaggregated
    :param float coordinate_bin_width:
      Width of coordinate bins when losses are disaggregated
    :param float asset_correlation: a number ranging from 0 to 1
    representing the correlation between the generated loss ratios
    """

    def profile(name):
        return EnginePerformanceMonitor(
            name, job_id, event_based, tracing=True)

    loss_ratio_curves = OrderedDict()
    event_loss_table = dict()

    rnd = random.Random()
    rnd.seed(task_seed)

    for hazard_output_id, hazard_data in hazard.items():
        hazard_getter, _ = hazard_data

        (loss_curve_id, loss_map_ids, insured_curve_id,
         loss_fractions_magnitude_distance_id, loss_fractions_coords_id) = (
             output_containers[hazard_output_id])

        seed = rnd.randint(0, models.MAX_SINT_32)
        logs.LOG.info("Using seed %s with hazard output %s" % (
            seed, hazard_output_id))

        calculator = api.ProbabilisticEventBased(
            vulnerability_function,
            curve_resolution=loss_curve_resolution,
            time_span=time_span,
            tses=tses,
            seed=seed,
            correlation=asset_correlation)

        with profile('getting input data from db'):
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

        with profile('computing losses and loss curves'):
            loss_ratio_matrix, loss_ratio_curves[hazard_output_id] = (
                calculator(ground_motion_values))

        with profile('writing loss curves'):
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

        with profile('writing and computing loss maps'):
            with db.transaction.commit_on_success(using='reslt_writer'):
                for i, loss_ratio_curve in enumerate(
                        loss_ratio_curves[hazard_output_id]):
                    asset = assets[i]

                    # loss maps
                    for poe in conditional_loss_poes:
                        general.write_loss_map_data(
                            loss_map_ids[poe], asset,
                            scientific.conditional_loss_ratio(
                                loss_ratio_curve.abscissae,
                                loss_ratio_curve.ordinates, poe))

        with profile('writing and computing insured loss curves'):
            with db.transaction.commit_on_success(using='reslt_writer'):
                for i, loss_ratio_curve in enumerate(
                        loss_ratio_curves[hazard_output_id]):
                    asset = assets[i]

                    # insured losses
                    if insured_losses:
                        insured_losses_losses, insured_losses_poes = (
                            scientific.event_based(
                                scientific.insured_losses(
                                    loss_ratio_matrix[i],
                                    asset.value,
                                    asset.deductible,
                                    asset.ins_limit),
                                tses=tses,
                                time_span=time_span,
                                curve_resolution=loss_curve_resolution))

                        # FIXME(lp). Insured losses are still computed
                        # as absolute values.
                        insured_losses_losses /= asset.value

                        general.write_loss_curve(
                            insured_curve_id, asset,
                            insured_losses_poes, insured_losses_losses,
                            scientific.average_loss(
                                insured_losses_losses, insured_losses_poes))

        with profile('computing event loss table'):
            for i, asset in enumerate(assets):
                for j, rupture_id in enumerate(rupture_id_matrix[i]):
                    # update the event loss table of this task
                    loss = loss_ratio_matrix[i][j] * asset.value
                    event_loss_table[rupture_id] = (
                        event_loss_table.get(rupture_id, 0) + loss)

        # compute and save disaggregation
        with profile('computing and writing disaggregation'):
            with db.transaction.commit_on_success(using='reslt_writer'):
                for i, loss_ratio_curve in enumerate(
                        loss_ratio_curves[hazard_output_id]):
                    asset = assets[i]
                    if asset.site in sites_disagg:
                        for j, rupture_id in enumerate(rupture_id_matrix[i]):

                            # As the path of the code is not frequent
                            # (we expect few request for
                            # disaggregation and few elements in
                            # `sites_disagg` this query is performed
                            # here and not directly in the getter
                            rupture = models.SESRupture.objects.get(
                                pk=rupture_id)
                            loss = loss_ratio_matrix[i][j] * asset.value
                            site = asset.site
                            site_mesh = mesh.Mesh(numpy.array([site.x]),
                                                  numpy.array([site.y]), None)

                            magnitude_distance = (
                                numpy.floor(rupture.magnitude / mag_bin_width),
                                numpy.floor(
                                    rupture.surface.get_joyner_boore_distance(
                                        site_mesh))[0] / distance_bin_width)

                            general.write_loss_fraction_data(
                                loss_fractions_magnitude_distance_id,
                                location=asset.site,
                                value="%d,%d" % magnitude_distance,
                                absolute_loss=loss)

                            closest_point = iter(
                                rupture.surface.get_closest_points(
                                    site_mesh)).next()

                            coordinate = (
                                closest_point.longitude / coordinate_bin_width,
                                closest_point.latitude / coordinate_bin_width)

                            general.write_loss_fraction_data(
                                loss_fractions_coords_id,
                                location=asset.site,
                                value="%d,%d" % coordinate,
                                absolute_loss=loss)

    # compute mean and quantile outputs
    if statistical_output_containers:
        weights = [data[1] for _, data in hazard.items()]

        (mean_loss_curve_id, quantile_loss_curve_ids,
         mean_loss_map_ids, quantile_loss_map_ids) = (
             statistical_output_containers)

        with profile('computing and writing statistics'):
            with db.transaction.commit_on_success(using='reslt_writer'):
                general.compute_and_write_statistics(
                    mean_loss_curve_id, quantile_loss_curve_ids,
                    mean_loss_map_ids, quantile_loss_map_ids,
                    None, None,  # no mean/quantile loss fractions
                    weights, assets,
                    numpy.array(loss_ratio_curves.values()),
                    hazard_montecarlo_p, conditional_loss_poes,
                    [],  # no mean/quantile loss fractions
                    "image")

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
        """
          Compute aggregate loss curves and event loss tables
        """

        time_span, tses = self.hazard_times()

        for hazard_output in self.considered_hazard_outputs():

            gmf_sets = hazard_output.gmfcollection.gmfset_set.all()

            aggregate_losses = [
                self.event_loss_table[rupture.id]
                for rupture in models.SESRupture.objects.filter(
                    ses__pk__in=[gmf_set.stochastic_event_set_id
                                 for gmf_set in gmf_sets])
                if rupture.id in self.event_loss_table]

            if aggregate_losses:
                aggregate_loss_losses, aggregate_loss_poes = (
                    scientific.event_based(
                        aggregate_losses, tses=tses, time_span=time_span,
                        curve_resolution=self.rc.loss_curve_resolution))

                models.AggregateLossCurveData.objects.create(
                    loss_curve=models.LossCurve.objects.create(
                        aggregate=True, insured=False,
                        hazard_output=hazard_output,
                        output=models.Output.objects.create_output(
                            self.job,
                            "Aggregate Loss Curve "
                            "for hazard %s" % hazard_output,
                            "agg_loss_curve")),
                    losses=aggregate_loss_losses, poes=aggregate_loss_poes,
                    average_loss=scientific.average_loss(
                        aggregate_loss_losses, aggregate_loss_poes))

        event_loss_table_output = models.Output.objects.create_output(
            self.job, "Event Loss Table", "event_loss")

        with db.transaction.commit_on_success(using='reslt_writer'):
            for rupture_id, aggregate_loss in self.event_loss_table.items():
                models.EventLoss.objects.create(
                    output=event_loss_table_output,
                    rupture_id=rupture_id,
                    aggregate_loss=aggregate_loss)

    def create_getter(self, output, imt, assets):
        """
        See :meth:`..general.BaseRiskCalculator.create_getter`
        """
        if not output.output_type in ('gmf', 'complete_lt_gmf'):
            raise RuntimeError(
                "The provided hazard output is not a ground motion field")

        gmf = output.gmfcollection

        hazard_getter = self.hazard_getter(
            gmf.id, imt, assets, self.rc.best_maximum_distance)
        return (hazard_getter, gmf.lt_realization.weight)

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
                gmfcollection__lt_realization__isnull=False).order_by('id')

    def hazard_times(self):
        """
        Return the hazard investigation time related to the ground
        motion field and the so-called time representative of the
        stochastic event set
        """
        time_span = self.hc.investigation_time
        return time_span, self.hc.ses_per_logic_tree_path * time_span

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
                self.rc.sites_disagg or [],
                self.rc.mag_bin_width,
                self.rc.distance_bin_width,
                self.rc.coordinate_bin_width,
                self.hc.number_of_logic_tree_samples == 0]

    def create_outputs(self, hazard_output):
        """
        Add Insured Curve output containers
        """
        outputs = super(EventBasedRiskCalculator, self).create_outputs(
            hazard_output)

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

        if self.rc.sites_disagg:
            loss_fractions_magnitude_distance_id = (
                models.LossFraction.objects.create(
                    output=models.Output.objects.create_output(
                        self.job,
                        "Loss Fractions by ruptures grouped by range of "
                        "magnitude/distance for hazard %s" % hazard_output,
                        "loss_fraction"),
                    hazard_output=hazard_output,
                    variable="magnitude_distance").id)
            loss_fractions_coords_id = models.LossFraction.objects.create(
                output=models.Output.objects.create_output(
                    self.job,
                    "Loss Fractions by ruptures grouped by range of "
                    "coordinates for hazard %s" % hazard_output,
                    "loss_fraction"),
                hazard_output=hazard_output,
                variable="coordinate").id
        else:
            loss_fractions_magnitude_distance_id = None
            loss_fractions_coords_id = None

        return outputs + [insured_curve_id,
                          loss_fractions_magnitude_distance_id,
                          loss_fractions_coords_id]
