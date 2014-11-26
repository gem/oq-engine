# Copyright (c) 2010-2014, GEM Foundation.
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
import collections
import itertools
import numpy

from openquake.hazardlib.geo import mesh
from openquake.risklib import scientific, workflows
from openquake.risklib.utils import numpy_map

from openquake.engine.calculators import post_processing
from openquake.engine.calculators.risk import (
    base, hazard_getters, validation, writers)
from openquake.engine.db import models
from openquake.engine import writer
from openquake.engine.calculators import calculators
from openquake.engine.performance import EnginePerformanceMonitor


def _filter_loss_matrix_assets(loss_matrix, assets, specific_assets):
    # reduce loss_matrix and assets to the specific_assets
    mask = numpy.array([a.asset_ref in specific_assets for a in assets])
    return loss_matrix[mask], numpy.array(assets)[mask]


def event_based(workflow, getter, outputdict, params, monitor):
    """
    Celery task for the event based risk calculator.

    :param job_id: the id of the current
        :class:`openquake.engine.db.models.OqJob`
    :param workflow:
      A :class:`openquake.risklib.workflows.Workflow` instance
    :param getter:
      A :class:`HazardGetter` instance
    :param outputdict:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (e.g. a LossCurve)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    :param monitor:
      A monitor instance
    :returns:
      A dictionary {loss_type: event_loss_table}
    """
    # NB: event_loss_table is a dictionary (loss_type, out_id) -> loss,
    # out_id can be None, and it that case it stores the statistics
    event_loss_table = {}
    specific_assets = set(params.specific_assets)
    statistics = getattr(params, 'statistics', True)  # enabled by default
    # keep in memory the loss_matrix only when specific_assets are set
    workflow.return_loss_matrix = bool(specific_assets)

    # the insert here will work only if specific_assets is set
    inserter = writer.CacheInserter(
        models.EventLossAsset, max_cache_size=10000)
    for loss_type in workflow.loss_types:
        with monitor('computing individual risk'):
            outputs = workflow.compute_all_outputs(getter, loss_type)
            if statistics:
                outputs = list(outputs)  # expand the generator
                # this is needed, otherwise the call to workflow.statistics
                # below will find an empty iterable; notice that by disabling
                # the statistics we can save memory by keeping only one
                # hazard realization at the time
        for out in outputs:
            event_loss_table[loss_type, out.hid] = out.output.event_loss_table
            disagg_outputs = None  # changed if params.sites_disagg is set
            if specific_assets:
                loss_matrix, assets = _filter_loss_matrix_assets(
                    out.output.loss_matrix, out.output.assets, specific_assets)
                if len(assets) == 0:  # no specific_assets
                    continue
                # compute the loss per rupture per asset
                event_loss = models.EventLoss.objects.get(
                    output__oq_job=monitor.job_id,
                    output__output_type='event_loss_asset',
                    loss_type=loss_type, hazard_output=out.hid)
                # losses is E x n matrix, where E is the number of ruptures
                # and n the number of assets in the specific_assets set
                losses = (loss_matrix.transpose() *
                          numpy_map(lambda a: a.value(loss_type), assets))
                # save an EventLossAsset record for each specific asset
                for rup_id, losses_per_rup in zip(
                        getter.rupture_ids, losses):
                    for asset, loss_per_rup in zip(assets, losses_per_rup):
                        ela = models.EventLossAsset(
                            event_loss=event_loss, rupture_id=rup_id,
                            asset=asset, loss=loss_per_rup)
                        inserter.add(ela)
                if params.sites_disagg:
                    with monitor('disaggregating results'):
                        ruptures = [models.SESRupture.objects.get(pk=rid)
                                    for rid in getter.rupture_ids]
                        disagg_outputs = disaggregate(
                            out.output, [r.rupture for r in ruptures], params)

            with monitor('saving individual risk'):
                save_individual_outputs(
                    outputdict.with_args(hazard_output_id=out.hid,
                                         loss_type=loss_type),
                    out.output, disagg_outputs, params)

        if statistics and len(outputs) > 1:
            stats = workflow.statistics(
                outputs, params.quantile_loss_curves, post_processing)

            with monitor('saving risk statistics'):
                save_statistical_output(
                    outputdict.with_args(
                        hazard_output_id=None, loss_type=loss_type),
                    stats, params)
            event_loss_table[loss_type, None] = stats.event_loss_table

    inserter.flush()
    return event_loss_table


def save_individual_outputs(outputdict, outputs, disagg_outputs, params):
    """
    Save loss curves, loss maps and loss fractions associated with a
    calculation unit

    :param outputdict:
        a :class:`openquake.engine.calculators.risk.writers.OutputDict`
        instance holding the reference to the output container objects
    :param outputs:
        a :class:`openquake.risklib.workflows.ProbabilisticEventBased.Output`
        holding the output data for a calculation unit
    :param disagg_outputs:
        a :class:`.DisaggregationOutputs` holding the disaggreation
        output data for a calculation unit
    :param params:
        a :class:`openquake.engine.calculators.risk.base.CalcParams`
        holding the parameters for this calculation
    """

    outputdict.write(
        outputs.assets,
        (outputs.loss_curves, outputs.average_losses, outputs.stddev_losses),
        output_type="event_loss_curve")

    outputdict.write_all(
        "poe", params.conditional_loss_poes,
        outputs.loss_maps,
        outputs.assets,
        output_type="loss_map")

    if disagg_outputs is not None:
        # FIXME. We should avoid synthetizing the generator
        assets = list(disagg_outputs.assets_disagg)
        outputdict.write(
            assets,
            disagg_outputs.magnitude_distance,
            disagg_outputs.fractions,
            output_type="loss_fraction",
            variable="magnitude_distance")
        outputdict.write(
            assets,
            disagg_outputs.coordinate, disagg_outputs.fractions,
            output_type="loss_fraction",
            variable="coordinate")

    if outputs.insured_curves is not None:
        outputdict.write(
            outputs.assets,
            (outputs.insured_curves, outputs.average_insured_losses,
             outputs.stddev_insured_losses),
            output_type="event_loss_curve", insured=True)


def save_statistical_output(outputdict, stats, params):
    """
    Save statistical outputs (mean and quantile loss curves, mean and
    quantile loss maps) for the calculation.

    :param outputdict:
        a :class:`openquake.engine.calculators.risk.writers.OutputDict`
        instance holding the reference to the output container objects
    :param stats:
        :class:
        `openquake.risklib.workflows.ProbabilisticEventBased.StatisticalOutput`
        holding the statistical output data
    :param params:
        a :class:`openquake.engine.calculators.risk.base.CalcParams`
        holding the parameters for this calculation
    """

    outputdict.write(
        stats.assets, (stats.mean_curves, stats.mean_average_losses),
        output_type="loss_curve", statistics="mean")

    outputdict.write_all(
        "poe", params.conditional_loss_poes, stats.mean_maps,
        stats.assets, output_type="loss_map", statistics="mean")

    # quantile curves and maps
    outputdict.write_all(
        "quantile", params.quantile_loss_curves,
        [(c, a) for c, a in itertools.izip(stats.quantile_curves,
                                           stats.quantile_average_losses)],
        stats.assets, output_type="loss_curve", statistics="quantile")

    if params.quantile_loss_curves:
        for quantile, maps in zip(
                params.quantile_loss_curves, stats.quantile_maps):
            outputdict.write_all(
                "poe", params.conditional_loss_poes, maps,
                stats.assets, output_type="loss_map",
                statistics="quantile", quantile=quantile)

    # mean and quantile insured curves
    if stats.mean_insured_curves is not None:
        outputdict.write(
            stats.assets, (stats.mean_insured_curves,
                           stats.mean_average_insured_losses),
            output_type="loss_curve", statistics="mean", insured=True)

        outputdict.write_all(
            "quantile", params.quantile_loss_curves,
            [(c, a) for c, a in itertools.izip(
                stats.quantile_insured_curves,
                stats.quantile_average_insured_losses)],
            stats.assets,
            output_type="loss_curve", statistics="quantile", insured=True)


class DisaggregationOutputs(object):
    def __init__(self, assets_disagg, magnitude_distance,
                 coordinate, fractions):
        self.assets_disagg = assets_disagg
        self.magnitude_distance = magnitude_distance
        self.coordinate = coordinate
        self.fractions = fractions


def disaggregate(outputs, ruptures, params):
    """
    Compute disaggregation outputs given the individual `outputs` and `params`

    :param outputs:
      an instance of
      :class:`openquake.risklib.workflows.ProbabilisticEventBased.Output`
    :param params:
      an instance of :class:`..base.CalcParams`
    :param list rupture_ids:
      a list of :class:`openquake.engine.db.models.SESRupture` IDs
    :returns:
      an instance of :class:`DisaggregationOutputs`
    """
    def disaggregate_site(site, loss_ratios):
        for fraction, rupture in zip(loss_ratios, ruptures):
            s = rupture.surface
            m = mesh.Mesh(numpy.array([site.x]), numpy.array([site.y]), None)

            mag = numpy.floor(rupture.magnitude / params.mag_bin_width)
            dist = numpy.floor(
                s.get_joyner_boore_distance(m))[0] / params.distance_bin_width

            closest_point = iter(s.get_closest_points(m)).next()
            lon = closest_point.longitude / params.coordinate_bin_width
            lat = closest_point.latitude / params.coordinate_bin_width

            yield "%d,%d" % (mag, dist), "%d,%d" % (lon, lat), fraction

    assets_disagg = []
    disagg_matrix = []
    for asset, losses in zip(outputs.assets, outputs.loss_matrix):
        if (asset.site.x, asset.site.y) in params.sites_disagg:
            disagg_matrix.extend(list(disaggregate_site(asset.site, losses)))

            # FIXME. the functions in
            # openquake.engine.calculators.risk.writers requires an
            # asset per each row in the disaggregation matrix. To this
            # aim, we repeat the assets that will be passed to such
            # functions
            assets_disagg = itertools.chain(
                assets_disagg,
                itertools.repeat(asset, len(ruptures)))

    if assets_disagg:
        magnitudes, coordinates, fractions = zip(*disagg_matrix)
    else:
        magnitudes, coordinates, fractions = [], [], []

    return DisaggregationOutputs(
        assets_disagg, magnitudes, coordinates, fractions)


@calculators.add('event_based_risk')
class EventBasedRiskCalculator(base.RiskCalculator):
    """
    Probabilistic Event Based PSHA risk calculator. Computes loss
    curves, loss maps, aggregate losses and insured losses for a given
    set of assets.
    """

    core = staticmethod(event_based)

    # FIXME(lp). Validate sites_disagg to ensure non-empty outputs
    validators = base.RiskCalculator.validators + [
        validation.RequireEventBasedHazard,
        validation.ExposureHasInsuranceBounds]

    output_builders = [writers.EventLossCurveMapBuilder,
                       writers.LossFractionBuilder]
    getter_class = hazard_getters.GroundMotionGetter

    def __init__(self, job):
        super(EventBasedRiskCalculator, self).__init__(job)
        # accumulator for the event loss tables
        self.acc = collections.defaultdict(collections.Counter)
        self.sites_disagg = self.job.get_param('sites_disagg')
        self.specific_assets = self.job.get_param('specific_assets')

    def pre_execute(self):
        """
        Base pre_execute + build Event Loss Asset outputs if needed
        """
        super(EventBasedRiskCalculator, self).pre_execute()
        for hazard_output in self.rc.hazard_outputs():
            for loss_type in self.loss_types:
                models.EventLoss.objects.create(
                    output=models.Output.objects.create_output(
                        self.job,
                        "Event Loss Table type=%s, hazard=%s" % (
                            loss_type, hazard_output.id),
                        "event_loss"),
                    loss_type=loss_type,
                    hazard_output=hazard_output)
                if self.specific_assets:
                    models.EventLoss.objects.create(
                        output=models.Output.objects.create_output(
                            self.job,
                            "Event Loss Asset type=%s, hazard=%s" % (
                                loss_type, hazard_output.id),
                            "event_loss_asset"),
                        loss_type=loss_type,
                        hazard_output=hazard_output)

    @EnginePerformanceMonitor.monitor
    def agg_result(self, acc, event_loss_table):
        """
        Updates the event loss table
        """
        newdict = acc.copy()
        for (loss_type, out_id), counter in event_loss_table.iteritems():
            try:
                c = newdict[loss_type, out_id]
            except KeyError:
                pass
            else:
                newdict[loss_type, out_id] = c + counter
        return newdict

    def post_process(self):
        """
          Compute aggregate loss curves and event loss tables
        """
        with self.monitor('post processing'):
            inserter = writer.CacheInserter(models.EventLossData,
                                            max_cache_size=10000)
            time_span, tses = self.hazard_times()
            for (loss_type, out_id), event_loss_table in self.acc.items():
                if out_id:  # values for individual realizations
                    hazard_output = models.Output.objects.get(pk=out_id)
                    event_loss = models.EventLoss.objects.get(
                        output__oq_job=self.job,
                        output__output_type='event_loss',
                        loss_type=loss_type, hazard_output=hazard_output)
                    if isinstance(hazard_output.output_container,
                                  models.SESCollection):
                        ses_coll = hazard_output.output_container
                        rupture_ids = ses_coll.get_ruptures().values_list(
                            'id', flat=True)
                    else:  # extract the SES collection from the Gmf
                        rupture_ids = models.SESRupture.objects.filter(
                            rupture__ses_collection__trt_model__lt_model=
                            hazard_output.output_container.
                            lt_realization.lt_model).values_list(
                            'id', flat=True)
                    for rupture_id in rupture_ids:
                        if rupture_id in event_loss_table:
                            inserter.add(
                                models.EventLossData(
                                    event_loss_id=event_loss.id,
                                    rupture_id=rupture_id,
                                    aggregate_loss=event_loss_table[
                                        rupture_id]))
                    inserter.flush()

                    aggregate_losses = [
                        event_loss_table[rupture_id]
                        for rupture_id in rupture_ids
                        if rupture_id in event_loss_table]

                    if aggregate_losses:
                        aggregate_loss_losses, aggregate_loss_poes = (
                            scientific.event_based(
                                aggregate_losses, tses=tses,
                                time_span=time_span,
                                curve_resolution=self.rc.loss_curve_resolution
                            ))

                        models.AggregateLossCurveData.objects.create(
                            loss_curve=models.LossCurve.objects.create(
                                aggregate=True, insured=False,
                                hazard_output=hazard_output,
                                loss_type=loss_type,
                                output=models.Output.objects.create_output(
                                    self.job,
                                    "aggregate loss curves. "
                                    "loss_type=%s hazard=%s" % (
                                        loss_type, hazard_output),
                                    "agg_loss_curve")),
                            losses=aggregate_loss_losses,
                            poes=aggregate_loss_poes,
                            average_loss=scientific.average_loss(
                                aggregate_loss_losses, aggregate_loss_poes),
                            stddev_loss=numpy.std(aggregate_losses))

    def get_workflow(self, vulnerability_functions):
        """
        :param vulnerability_functions:
            a dictionary of vulnerability functions
        :returns:
            an instance of
            :class:`openquake.risklib.workflows.ProbabilisticEventBased`
        """
        time_span, tses = self.hazard_times()
        return workflows.ProbabilisticEventBased(
            vulnerability_functions,
            time_span, tses,
            self.rc.loss_curve_resolution,
            self.rc.conditional_loss_poes,
            self.rc.insured_losses)

    def hazard_times(self):
        """
        Return the hazard investigation time related to the ground
        motion field and the so-called time representative of the
        stochastic event set
        """
        return (self.rc.investigation_time,
                self.hc.ses_per_logic_tree_path * self.hc.investigation_time)
