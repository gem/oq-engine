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

import numpy

from openquake.risklib.api import Classical
from openquake.risklib.scientific import average_loss, conditional_loss_ratio

from django.db import transaction

from openquake.engine.db import models
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.calculators.base import signal_task_complete
from openquake.engine.calculators.risk import base, writers, hazard_getters
from openquake.engine.utils import tasks
from openquake.engine import logs


@tasks.oqtask
@base.count_progress_risk('r')
def classical(job_id,
              units, containers,
              conditional_loss_poes, quantiles,
              poes_disagg, hazard_montecarlo_p):
    """
    Celery task for the classical risk calculator.

    :param int job_id:
      ID of the currently running job
    :param list units:
      A list of :class:`..base.CalculationUnit`
    :param dict containers: A dictionary mapping
      :class:`..general.OutputKey` to database ID of output containers
    :param conditional_loss_poes:
      The poes taken into account to compute the loss maps
    :param quantiles:
      The quantiles at which we compute quantile curves/maps
    :param poes_disagg:
      The poes taken into account to compute the loss maps for disaggregation
    :param bool hazard_montecarlo_p:
     (meaningful only if curve statistics are computed). Wheter or not
     the hazard calculation is montecarlo based
    """
    def profile(name):
        return EnginePerformanceMonitor(
            name, job_id, event_based, tracing=True)

    # Actuall we do the job in another function, such that it can be
    # unit tested without the celery machinery
    do_classical(units, containers, conditional_loss_poes, quantiles,
                 poes_disagg, hazard_montecarlo_p, profile)
    signal_task_complete(job_id=job_id, num_items=len(units[0].getter.assets))
classical.ignore_result = False


def do_classical(
        units, containers, poes, quantiles, poes_disagg, montecarlo, profile):

    with profile('computing individual risk'):
        assets, curve_matrix, map_matrix, fraction_matrix = individual_outputs(
            units, poes, poes_disagg)

    with profile('saving individual risk'):
        for c, curves, maps, fractions in zip(
                units, curve_matrix, map_matrix, fraction_matrix):
            hid = c.getter.hazard_id
            save_assets(containers, assets,
                        curves, maps, fractions, hazard_output_id=hid)

    if len(units) < 2:  # skip statistics if we are working on a single unit
        return

    with profile('computing risk statistics'):
        (mean_curves, mean_maps, mean_fractions, quantile_curves,
         quantile_maps, quantile_fractions) = statistics(
             units, curves, montecarlo)

    with profile('saving risk statistics'):
        save_assets(containers, assets,
                    mean_curves, mean_maps, mean_fractions,
                    statistics="mean")
        for curves, maps, fractions in zip(
                quantile_curves, quantile_maps, quantile_fractions):
            save_assets(containers, assets,
                        curves, maps, fractions,
                        statistics="quantile",
                        quantile=quantile)


def individual_outputs(units, conditional_loss_poes, poes_disagg):
    loss_curve_matrix = []
    loss_maps = []
    fractions = []

    for unit in units:
        with logs.tracing('getting hazard'):
            assets, hazard_curves, _missings = unit.getter()

        with logs.tracing('hazard id %s' % unit.getter.hazard_id):
            curves = unit.calc(hazard_curves)
            loss_curve_matrix.append(curves)
            loss_maps.append([[(poe, conditional_loss_ratio(losses, poes, poe))
                               for losses, poes in curves]
                              for poe in conditional_loss_poes])
            fractions.append([[(poe, conditional_loss_ratio(losses, poes, poe))
                              for losses, poes in curves]
                             for poe in poes_disagg])
    return assets, loss_curve_matrix, loss_maps, fractions


def statistics(units, curve_matrix, montecarlo):
    weights = [unit.getter.weight for unit in units]

    for i, asset in enumerate(assets):
        loss_ratio_curves = loss_ratio_curve_matrix[:, i]

        if assume_equal == 'support':
            # get the loss ratios only from the first curve
            loss_ratios, _poes = loss_ratio_curves[0]
            curves_poes = [poes for _losses, poes in loss_ratio_curves]
        elif assume_equal == 'image':
            non_trivial_curves = [(losses, poes)
                                  for losses, poes in loss_ratio_curves
                                  if losses[-1] > 0]
            if not non_trivial_curves:  # no damage. all trivial curves
                logs.LOG.info("No damages in asset %s" % asset)
                loss_ratios, _poes = loss_ratio_curves[0]
                curves_poes = [poes for _losses, poes in loss_ratio_curves]
            else:  # standard case
                max_losses = [losses[-1]  # we assume non-decreasing losses
                              for losses, _poes in non_trivial_curves]
                reference_curve = non_trivial_curves[numpy.argmax(max_losses)]
                loss_ratios = reference_curve[0]
                curves_poes = [interpolate.interp1d(
                    losses, poes, bounds_error=False, fill_value=0)(
                        loss_ratios)
                    for losses, poes in loss_ratio_curves]
        else:
            raise NotImplementedError

        quantiles_poes = dict()

        for quantile, quantile_loss_curve_id in (
                quantile_loss_curve_ids.items()):
            if hazard_montecarlo_p:
                q_curve = post_processing.weighted_quantile_curve(
                    curves_poes, weights, quantile)
            else:
                q_curve = post_processing.quantile_curve(curves_poes, quantile)

            quantiles_poes[quantile] = q_curve.tolist()

            loss_curve(
                quantile_loss_curve_id,
                asset,
                quantiles_poes[quantile],
                loss_ratios,
                scientific.average_loss(loss_ratios, quantiles_poes[quantile]))

        # then mean loss curve
        mean_poes = None
        if mean_loss_curve_id:
            mean_curve = post_processing.mean_curve(curves_poes, weights)
            mean_poes = mean_curve.tolist()

            loss_curve(
                mean_loss_curve_id,
                asset,
                mean_poes,
                loss_ratios,
                scientific.average_loss(loss_ratios, mean_poes))

        for poe in conditional_loss_poes:
            loss_map_data(
                mean_loss_map_ids[poe],
                asset,
                scientific.conditional_loss_ratio(loss_ratios, mean_poes, poe))
            for quantile, poes in quantiles_poes.items():
                loss_map_data(
                    quantile_loss_map_ids[quantile][poe],
                    asset,
                    scientific.conditional_loss_ratio(loss_ratios, poes, poe))

        # mean and quantile loss fractions (only disaggregation by
        # taxonomy is supported here)
        for poe in poes_disagg:
            loss_fraction_data(
                mean_loss_fraction_ids[poe],
                value=asset.taxonomy,
                location=asset.site,
                absolute_loss=scientific.conditional_loss_ratio(
                    loss_ratios, mean_poes, poe) * asset.value)
            for quantile, poes in quantiles_poes.items():
                loss_fraction_data(
                    quantile_loss_fraction_ids[quantile][poe],
                    value=asset.taxonomy,
                    location=asset.site,
                    absolute_loss=scientific.conditional_loss_ratio(
                        loss_ratios, poes, poe) * asset.value)

    with logs.tracing('writing results'):
        with transaction.commit_on_success(using='reslt_writer'):
            for i, (losses, poes) in enumerate(
                    asset_outputs[c.getter.hazard_id]):

                asset = assets[i]

                # Write Loss Curves
                writers.loss_curve(
                    containers.get(
                        output_type="loss_curve",
                        hazard_output_id=c.getter.hazard_output_id),
                    asset,
                    poes, losses,
                    scientific.average_loss(losses, poes))

                # Then conditional loss maps
                for poe in conditional_loss_poes:
                    writers.loss_map_data(
                        containers.get(
                            output_type="loss_map",
                            hazard_output_id=c.getter.hazard_output_id,
                            poe=poe),
                        asset,
                        scientific.conditional_loss_ratio(
                            losses, poes, poe))

                # Then loss fractions
                for poe in poes_disagg:
                    writers.loss_fraction_data(
                        containers.get(
                            output_type="loss_fraction",
                            hazard_output_id=c.getter.hazard_output_id,
                            poe=poe),
                        location=asset.site,
                        value=asset.taxonomy,
                        absolute_loss=scientific.conditional_loss_ratio(
                            losses, poes, poe) * asset.value)


class ClassicalRiskCalculator(base.RiskCalculator):
    """
    Classical PSHA risk calculator. Computes loss curves and loss maps
    for a given set of assets.
    """

    #: celery task
    core_calc_task = classical

    def calculation_units(self, assets):

        # TODO: comment better

        # assume all assets have the same taxonomy
        taxonomy = assets[0].taxonomy
        vulnerability_function = self.vulnerability_functions[taxonomy]

        return [base.CalculationUnit(
            Classical(
                vulnerability_function=vulnerability_function,
                steps=self.rc.lrem_steps_per_interval),
            hazard_getters.HazardCurveGetterPerAsset(
                ho,
                assets,
                self.rc.best_maximum_distance,
                self.taxonomy_imt[taxonomy]))
                for ho in self.rc.hazard_outputs()]

    def pre_execute(self):
        """
        Checks that the given hazard is an hazard curve
        """
        if self.rc.hazard_calculation:
            if self.rc.hazard_calculation.calc_mode != 'classical':
                raise RuntimeError(
                    "The provided hazard calculation ID "
                    "is not a classical calculation")
        elif not self.rc.hazard_output.is_hazard_curve():
            raise RuntimeError(
                "The provided hazard output is not an hazard curve")
        super(ClassicalRiskCalculator, self).pre_execute()

    def create_outputs(self, hazard_output):
        """
        Create outputs container objects.

        In classical risk, we finalize the output containers by adding
        ids of loss_fractions
        """
        containers = super(ClassicalRiskCalculator, self).create_outputs(
            hazard_output)

        for poe in self.rc.poes_disagg or []:
            containers.set(models.LossFraction.objects.create(
                hazard_output_id=hazard_output.id,
                variable="taxonomy",
                output=models.Output.objects.create_output(
                    self.job,
                    "Loss Fractions with poe %s for hazard %s" % (
                        poe, hazard_output.id), "loss_fraction"),
                poe=poe))
        return containers

    def create_statistical_outputs(self):
        """
        Create statistics output containers.

        In classical risk we need also loss fraction ids for aggregate
        results
        """

        containers = super(
            ClassicalRiskCalculator, self).create_statistical_outputs()

        for poe in self.rc.poes_disagg or []:
            containers.set(models.LossFraction.objects.create(
                variable="taxonomy",
                output=models.Output.objects.create_output(
                    job=self.job,
                    display_name="Mean Loss Fractions poe=%.4f" % poe,
                    output_type="loss_fraction"),
                statistics="mean"))

        for quantile in self.rc.quantile_loss_curves or []:
            for poe in self.rc.poes_disagg or []:
                name = "Quantile Loss Fractions poe=%.4f q=%.4f" % (
                    poe, quantile)
                containers.set(models.LossFraction.objects.create(
                    variable="taxonomy",
                    output=models.Output.objects.create_output(
                        job=self.job,
                        display_name=name,
                        output_type="loss_fraction"),
                    statistics="quantile",
                    quantile=quantile))

        return containers

    @property
    def calculator_parameters(self):
        """
        Specific calculator parameters returned as list suitable to be
        passed in task_arg_gen
        """

        return [self.rc.conditional_loss_poes or [],
                self.rc.quantile_loss_curves or [],
                self.rc.poes_disagg or [],
                self.hc.number_of_logic_tree_samples == 0]
