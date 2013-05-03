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

import collections
import numpy
from openquake.risklib.api import Classical
from openquake.risklib.scientific import conditional_loss_ratio

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
    :param list units:
      A list of :class:`..base.CalculationUnit` to be run
    :param containers:
      An instance of :class:`..base.OutputDict` containing
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
        do_classical(units, containers, params, profile)
    signal_task_complete(job_id=job_id, num_items=len(units[0].getter.assets))
classical.ignore_result = False


def do_classical(units, containers, params, profile):
    """
    See `classical` for a description of the parameters.

    :param profile:
      a context manager for logging/profiling purposes

    For each calculation unit we compute loss curves, loss maps and
    loss fractions. Then if the number of units are bigger than 1, we
    compute mean and quantile artifacts.
    """

    outputs = individual_outputs(
        units, params.conditional_loss_poes, params.poes_disagg, profile)

    with profile('saving individual risk'):
        hids = [unit.getter.hazard_output_id for unit in units]
        save_individual_outputs(containers, hids, outputs, params)

    if len(units) < 2:  # skip statistics if we are working on a single unit
        return

    with profile('computing risk statistics'):
        weights = [unit.getter.weight for unit in units]
        stats = statistics(outputs, weights, params)

    with profile('saving risk statistics'):
        save_statistical_output(containers, stats, params)


class AssetsIndividualOutputs(
        collections.namedtuple(
            'AssetsIndividualOutputs',
            ['assets', 'curve_matrix', 'map_matrix', 'fraction_matrix'])):
    """Record the results computed for ALL the calculation units.

  :attr assets:
    an iterable over the assets considered by the calculation units

  :attr curve_matrix:
    a numpy array shaped N x A (N = number of units, A number of
    assets) where each element is a loss curve. A loss curve is described
    by a tuple (losses, poes)

  :attr map_matrix:
    a numpy array with N x P x A loss map values where P is the number of
    `conditional_loss_poes`

   :attr fraction_matrix:
    a numpy array with N x F x A loss fraction value where F is the number of
    `poes_disagg`
    """


def individual_outputs(units, conditional_loss_poes, poes_disagg, profile):
    """
    See `do_classical` for a description of the params

    :returns:
      an instance of `AssetsIndividualOutputs`
    """
    loss_curve_matrix = []
    loss_maps = []
    fractions = []

    for unit in units:
        with profile('getting hazard'):
            assets, hazard_curves = unit.getter()

        with profile('computing individual risk'):
            curves = unit.calc(hazard_curves)
            loss_curve_matrix.append(curves)
            loss_maps.append([[conditional_loss_ratio(losses, poes, poe)
                               for losses, poes in curves]
                              for poe in conditional_loss_poes])
            fractions.append([[conditional_loss_ratio(losses, poes, poe)
                              for losses, poes in curves]
                             for poe in poes_disagg])
    return AssetsIndividualOutputs(
        assets,
        numpy.array(loss_curve_matrix),
        numpy.array(loss_maps),
        numpy.array(fractions))


def save_individual_outputs(containers, hids, outputs, params):
    """
    Save an instance of `AssetsIndividualOutputs` in the proper
    `containers`
    """
    # loss curves
    containers.write_all(
        "hazard_output_id", hids,
        outputs.curve_matrix, outputs.assets, output_type="loss_curve")

    # loss maps
    for hid, maps in zip(hids, outputs.map_matrix):
        containers.write_all(
            "poe", params.conditional_loss_poes, maps, outputs.assets,
            hazard_output_id=hid, output_type="loss_map")

    # loss fractions
    for hid, fractions in zip(hids, outputs.fraction_matrix):
        containers.write_all(
            "poe", params.poes_disagg, fractions,
            outputs.assets, [a.taxonomy for a in outputs.assets],
            hazard_output_id=hid, output_type="loss_fraction",
            variable="taxonomy")


class StatisticalOutputs(collections.namedtuple(
        'StatisticalOutputs',
        ['assets', 'mean_curves', 'mean_maps', 'mean_fractions',
         'quantile_curves', 'quantile_maps', 'quantile_fractions'])):
    """The statistical outputs computed by the classical calculator.

    :attr list assets:
       the assets (instances of
       :class:`openquake.engine.db.models.ExposureData`) of which outputs
       have been computed
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


def statistics(outputs, weights, params):
    """
    :param outputs:
      An instance of `AssetsIndividualOutputs`

    See `classical` for a description of `params`

    :returns:
      an instance of `StatisticalOutputs`

    It makes use of `..base.statistics` to compute curves and maps
    """
    ret = []

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
        mean_fractions = [
            conditional_loss_ratio(mean_curve[0], mean_curve[1], poe)
            for poe in params.poes_disagg]

        quantile_fractions = [[
            conditional_loss_ratio(quantile_curve[0], quantile_curve[1], poe)
            for poe in params.poes_disagg]
            for quantile_curve in quantile_curves]

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
        outputs.assets, mean_curve, mean_maps,
        mean_fractions, quantile_curves, quantile_maps, quantile_fractions)


def save_statistical_output(containers, stats, params):
    # mean curves, maps and fractions

    containers.write(
        stats.assets, stats.mean_curves,
        output_type="loss_curve", statistics="mean")

    containers.write_all("poe", params.conditional_loss_poes,
                         stats.mean_maps, stats.assets,
                         output_type="loss_map", statistics="mean")

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

    def calculation_units(self, assets):
        """
        :returns:
          a list of instances of `..base.CalculationUnit` for the given
          `assets` to be run in the celery task
        """

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
            if self.rc.hazard_calculation.calculation_mode != 'classical':
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

        if len(self.rc.hazard_outputs()) < 2:
            return containers

        for poe in self.rc.poes_disagg or []:
            containers.set(models.LossFraction.objects.create(
                variable="taxonomy",
                poe=poe,
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
                    poe=poe,
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
