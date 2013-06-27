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
from openquake.risklib import scientific, calculators

from django.db import transaction

from openquake.engine.db import models
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.calculators.base import signal_task_complete
from openquake.engine.calculators.risk import base, hazard_getters
from openquake.engine.utils import tasks


@tasks.oqtask
@base.count_progress_risk('r')
def classical(job_id, units, containers, params):
    """
    Celery task for the classical risk calculator.

    :param int job_id:
      ID of the currently running job
    :param dict units:
      A dict of :class:`..base.CalculationUnit` instances keyed by
      loss type string
    :param containers:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (e.g. a LossCurve)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    """
    def profile(name):
        return EnginePerformanceMonitor(name, job_id, classical, tracing=True)

    # Do the job in other functions, such that they can be unit tested
    # without the celery machinery
    with transaction.commit_on_success(using='reslt_writer'):
        for loss_type in units:
            do_classical(
                units[loss_type],
                containers.prepare(loss_type=loss_type),
                params,
                profile)
    num_items = base.get_num_items(units)
    signal_task_complete(job_id=job_id, num_items=num_items)
classical.ignore_result = False


def do_classical(units, containers, params, profile):
    """
    See `classical` for a description of the parameters.

    :param str loss_type:
      the type of losses we are considering

    :param profile:
      a context manager for logging/profiling purposes

    For each calculation unit we compute loss curves, loss maps and
    loss fractions. Then if the number of units are bigger than 1, we
    compute mean and quantile artifacts.
    """

    loss_curves = []
    for unit in units:
        loss_type = unit.loss_type
        with profile('getting hazard'):
            assets, hazard_curves = unit.getter()

        with profile('computing individual risk'):
            outputs = individual_outputs(unit, assets, hazard_curves)
            loss_curves.append(outputs.loss_curves)

        with profile('saving individual risk'):
            containers = containers.prepare(
                loss_type=loss_type,
                hazard_output_id=unit.getter.hazard_output.id)
            save_individual_outputs(containers, outputs, params)

    if len(units) < 2:  # skip statistics if we are working on a single unit
        return

    with profile('computing risk statistics'):
        stats = statistics(outputs, params)

    with profile('saving risk statistics'):
        save_statistical_output(
            containers.prepare(loss_type=loss_type), stats, params)


class UnitOutputs(object):
    """
    Record the results computed in one calculation unit for N assets.

    :attr assets:
      a list of N assets the outputs refer to

    :attr loss_curves:
      a list of N loss curves (where a loss curve is a 2-tuple losses/poes)

    :attr loss_maps:
      a list of P elements holding list of N loss map values where P is the
      number of `conditional_loss_poes`

    :attr loss_maps:
      a list of D elements holding list of N loss map values where D is the
      number of `poes_disagg`

    :attr float weight:
      the weight associated with this output
    """

    def __init__(self, assets, loss_curves, loss_maps, loss_fractions, weight):
        self.assets = assets
        self.loss_curves = loss_curves
        self.loss_maps = loss_maps
        self.loss_fractions = loss_fractions
        self.weight = weight


def individual_outputs(unit, assets, hazard_curves):
    """
    See `do_classical` for a description of the params

    :returns:
      an instance of `AssetsIndividualOutputs`
    """

    curves = unit.calcs['curves'](hazard_curves)
    loss_maps = unit.calcs['maps'](curves)
    fractions = unit.calcs['fractions'](curves)
    weight = unit.getter.weight

    return UnitOutputs(assets, curves, loss_maps, fractions, weight)


def save_individual_outputs(containers, outs, params):
    """
    Save an instance of `UnitOutputs` in the proper `containers`
    """
    containers.write(outs.assets, outs.loss_curves, output_type="loss_curve")

    containers.write_all(
        "poe", params.conditional_loss_poes,
        outs.loss_maps,
        outs.assets,
        output_type="loss_map")

    taxonomies = [a.taxonomy for a in outs.assets]
    containers.write_all(
        "poe", params.poes_disagg,
        outs.loss_fractions, outs.assets, taxonomies,
        output_type="loss_fraction", variable="taxonomy")


class StatisticalOutputs(object):
    """The statistical outputs computed by the classical calculator.

    :attr list mean_curves:
       Holds N mean loss curves. A loss curve is a 2-ple losses/poes
    :attr list mean_maps:
       Holds P lists, where each of them holds N mean map value
       (P = number of PoEs)
    :attr mean_fractions:
       Holds F lists, where each of them holds N loss fraction value
       (F = number of disagg PoEs)
    :attr list quantile_curves:
       Holds Q lists, where each of them has N quantile loss curves
       (Q = number of quantiles)
    :attr list quantile_maps:
       Holds Q lists, where each of them has P lists. Each of the latter
       holds N quantile map value
    :attr list quantile_fractions:
       Holds Q lists, where each of them has F lists. Each of the latter
       holds N quantile loss fraction value
       """
    def __init__(self, mean_curves, mean_maps, mean_fractions,
                 quantile_curves, quantile_maps, quantile_fractions):
        self.mean_curves = mean_curves
        self.mean_maps = mean_maps
        self.mean_fractions = mean_fractions
        self.quantile_curves = quantile_curves
        self.quantile_maps = quantile_maps
        self.quantile_fractions = quantile_fractions


def statistics(outputs, params):
    """
    :param outputs:
      An instance of `AssetsIndividualOutputs`

    See `classical` for a description of `params`

    :returns:
      an instance of `StatisticalOutputs`

    It makes use of `..base.statistics` to compute curves and maps
    """
    ret = []

    weights = [o.weight for o in outputs]

    # traverse the curve matrix on the second dimension (the assets)
    # accumulating results in `ret`, then return `ret` unzipped
    for loss_ratio_curves in outputs.curve_matrix.transpose(1, 0, 2, 3):

        # get the loss ratios only from the first curve
        loss_ratios, _poes = loss_ratio_curves[0]
        curves_poes = [poes for _losses, poes in loss_ratio_curves]

        mean_curve, quantile_curves, mean_maps, quantile_maps = (
            base.asset_statistics(
                loss_ratios, curves_poes,
                params.quantiles, weights, params.conditional_loss_poes))

        # compute also mean and quantile loss fractions
        losses, poes = mean_curve
        mean_fractions = [
            scientific.conditional_loss_ratio(losses, poes, poe)
            for poe in params.poes_disagg]

        quantile_fractions = [[
            scientific.conditional_loss_ratio(losses, poes, poe)
            for poe in params.poes_disagg]
            for losses, poes in quantile_curves]

        ret.append((mean_curve, mean_maps, mean_fractions,
                    quantile_curves, quantile_maps, quantile_fractions))

    (mean_curve, mean_maps, mean_fractions,
     quantile_curves, quantile_maps, quantile_fractions) = zip(*ret)
    # now all the lists keep N items

    # transpose maps and fractions to have P/F/Q items of N-sized lists
    mean_maps = numpy.array(mean_maps).transpose()
    mean_fractions = numpy.array(mean_fractions).transpose()
    quantile_curves = numpy.array(quantile_curves).transpose(1, 0, 2, 3)
    quantile_maps = numpy.array(quantile_maps).transpose(2, 1, 0)
    quantile_fractions = numpy.array(quantile_fractions).transpose(2, 1, 0)

    return StatisticalOutputs(
        mean_curve, mean_maps,
        mean_fractions, quantile_curves, quantile_maps, quantile_fractions)


def save_statistical_output(containers, stats, params):
    # mean curves, maps and fractions

    containers.write(
        stats.assets, stats.mean_curves,
        output_type="loss_curve", statistics="mean")

    containers.write_all("poe", params.conditional_loss_poes,
                         stats.mean_maps, stats.assets,
                         output_type="loss_map",
                         statistics="mean")

    containers.write_all("poe", params.poes_disagg,
                         stats.mean_fractions,
                         stats.assets,
                         [a.taxonomy for a in stats.assets],
                         output_type="loss_fraction", statistics="mean",
                         variable="taxonomy")

    # quantile curves, maps and fractions
    containers.write_all(
        "quantile", params.quantiles, stats.quantile_curves,
        stats.assets, output_type="loss_curve", statistics="quantile")

    for quantile, maps in zip(params.quantiles, stats.quantile_maps):
        containers.write_all("poe", params.conditional_loss_poes, maps,
                             stats.assets, output_type="loss_map",
                             statistics="quantile", quantile=quantile)

    for quantile, fractions in zip(params.quantiles, stats.quantile_fractions):
        containers.write_all("poe", params.poes_disagg, fractions,
                             stats.assets, [a.taxonomy for a in stats.assets],
                             output_type="loss_fraction",
                             statistics="quantile", quantile=quantile,
                             variable="taxonomy")


class ClassicalRiskCalculator(base.RiskCalculator):
    """
    Classical PSHA risk calculator. Computes loss curves and loss maps
    for a given set of assets.
    """

    #: celery task
    core_calc_task = classical

    def calculation_units(self, loss_type, assets):
        """
        :returns:
          a list of instances of `..base.CalculationUnit` for the given
          `assets` to be run in the celery task
        """

        # assume all assets have the same taxonomy
        taxonomy = assets[0].taxonomy
        model = self.risk_models[taxonomy][loss_type]

        return [base.CalculationUnit(
            loss_type,
            dict(curves=calculators.ClassicalLossCurve(
                model.vulnerability_function,
                self.rc.lrem_steps_per_interval),
                maps=calculators.LossMap(self.rc.conditional_loss_poes),
                fractions=calculators.LossMap(self.rc.poes_disagg)),
            hazard_getters.HazardCurveGetterPerAsset(
                ho,
                assets,
                self.rc.best_maximum_distance,
                model.imt))
                for ho in self.rc.hazard_outputs()]

    def validate_hazard(self):
        """
        Checks that the given hazard has hazard curves
        """
        super(ClassicalRiskCalculator, self).validate_hazard()
        if self.rc.hazard_calculation:
            if self.rc.hazard_calculation.calculation_mode != 'classical':
                raise RuntimeError(
                    "The provided hazard calculation ID "
                    "is not a classical calculation")
        elif not self.rc.hazard_output.is_hazard_curve():
            raise RuntimeError(
                "The provided hazard output is not an hazard curve")

    def create_outputs(self, hazard_output):
        """
        Create outputs container objects.

        In classical risk, we finalize the output containers by adding
        ids of loss_fractions
        """
        containers = super(ClassicalRiskCalculator, self).create_outputs(
            hazard_output)

        for loss_type in base.loss_types(self.risk_models):
            for poe in self.rc.poes_disagg or []:
                containers.set(models.LossFraction.objects.create(
                    hazard_output_id=hazard_output.id,
                    variable="taxonomy",
                    loss_type=loss_type,
                    output=models.Output.objects.create_output(
                        self.job,
                        "loss fractions. type=%s poe=%s hazard=%s" % (
                            loss_type, poe, hazard_output.id),
                        "loss_fraction"),
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

        if len(self.rc.hazard_outputs()) < 2:
            return containers

        for loss_type in base.loss_types(self.risk_models):
            for poe in self.rc.poes_disagg or []:
                name = "mean loss fractions. type=%s poe=%.4f" % (
                    loss_type, poe)
                containers.set(models.LossFraction.objects.create(
                    variable="taxonomy",
                    poe=poe,
                    loss_type=loss_type,
                    output=models.Output.objects.create_output(
                        job=self.job,
                        display_name=name,
                        output_type="loss_fraction"),
                    statistics="mean"))

        for loss_type in base.loss_types(self.risk_models):
            for quantile in self.rc.quantile_loss_curves or []:
                for poe in self.rc.poes_disagg or []:
                    name = ("quantile(%.4f) loss fractions "
                            "loss_type=%s poe=%.4f" % (
                                quantile, loss_type, poe))
                    containers.set(models.LossFraction.objects.create(
                        variable="taxonomy",
                        poe=poe,
                        loss_type=loss_type,
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

        return base.make_calc_params(
            conditional_loss_poes=self.rc.conditional_loss_poes or [],
            quantiles=self.rc.quantile_loss_curves or [],
            poes_disagg=self.rc.poes_disagg or [])
