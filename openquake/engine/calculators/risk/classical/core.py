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
from openquake.risklib.scientific import conditional_loss_ratio

from django.db import transaction

from openquake.engine.db import models
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.calculators.base import signal_task_complete
from openquake.engine.calculators.risk import base, hazard_getters
from openquake.engine.utils import tasks
from openquake.engine import logs


@tasks.oqtask
@base.count_progress_risk('r')
def classical(job_id,
              units, containers,
              conditional_loss_poes, quantiles, poes_disagg):
    """
    Celery task for the classical risk calculator.

    :param int job_id:
      ID of the currently running job
    :param list units:
      A list of :class:`..base.CalculationUnit`
    :param dict containers:
      A dictionary mapping :class:`..general.OutputKey` to database ID
      of output containers (e.g. a LossCurve)
    :param conditional_loss_poes:
      The poes taken into account to compute the loss maps
    :param quantiles:
      The quantiles at which we compute quantile curves/maps
    :param poes_disagg:
      The poes taken into account to compute the loss maps for disaggregation
    """
    def profile(name):
        return EnginePerformanceMonitor(name, job_id, classical, tracing=True)

    # Actuall we do the job in other functions, such that it can be
    # unit tested without the celery machinery
    with transaction.commit_on_success(using='reslt_writer'):
        do_classical(
            units, containers,
            conditional_loss_poes, poes_disagg, quantiles,
            profile)
    signal_task_complete(job_id=job_id, num_items=len(units[0].getter.assets))
classical.ignore_result = False


def do_classical(units, containers, poes, poes_disagg, quantiles, profile):
    """
    See `classical` for a description of the parameters.

    For each calculation unit we compute loss curves, loss maps and
    loss fractions. Then if the number of units are bigger than 1, we
    compute mean and quantile artifacts.
    """
    with profile('computing individual risk'):
        assets, curves, map_matrix, fraction_matrix = individual_outputs(
            units, poes, poes_disagg)

    with profile('saving individual risk'):
        hids = [unit.getter.hazard_output_id for unit in units]

        # curves, maps and fractions
        containers.write_all(
            "hazard_output_id", hids, curves, assets, output_type="loss_curve")
        for hid, maps in zip(hids, map_matrix):
            containers.write_all(
                "poe", poes, maps, assets,
                hazard_output_id=hid, output_type="loss_map")
        for hid, fractions in zip(hids, fraction_matrix):
            containers.write_all("poe", poes_disagg, fractions,
                                 assets, [a.taxonomy for a in assets],
                                 hazard_output_id=hid,
                                 output_type="loss_fraction")

    if len(units) < 2:  # skip statistics if we are working on a single unit
        return

    with profile('computing risk statistics'):
        (mean_curves, mean_maps, mean_fractions, quantile_curves,
         quantile_maps, quantile_fractions) = statistics(
             curves, quantiles, units, poes, poes_disagg)

    with profile('saving risk statistics'):
        # mean curves, maps and fractions
        containers.write(
            assets, mean_curves, output_type="loss_curve", statistics="mean")
        containers.write_all("poe", poes, mean_maps,
                             assets, output_type="loss_map", statistics="mean")
        containers.write_all("poe", poes_disagg, mean_fractions, assets,
                             [a.taxonomy for a in assets],
                             output_type="loss_fraction", statistics="mean")

        # quantile curves, maps and fractions
        containers.write_all(
            "quantile", quantiles, quantile_curves,
            assets, output_type="loss_curve", statistics="quantile")
        for quantile, maps, fractions in zip(
                quantiles, quantile_maps, quantile_fractions):
            containers.write_all("poe", poes, maps,
                                 assets, output_type="loss_map",
                                 statistics="quantile", quantile=quantile)
            containers.write_all("poe", poes_disagg, fractions,
                                 assets, [a.taxonomy for a in assets],
                                 output_type="loss_fraction",
                                 statistics="quantile", quantile=quantile)


def individual_outputs(units, conditional_loss_poes, poes_disagg):
    """
    See `classical` for a description of the params

    :returns:
       a tuple with
       1) the assets got from the getter
       2) a numpy array with loss curves shaped N x A (N = number of
          units, A number of assets). A loss curve is described by a
          tuple (losses, poes).
       3) a numpy array with N x P x A loss map value where P is the
       number of `poes`
       4) a numpy array with N x F x A loss fraction value where F is the
       number of `poes_disagg`
    """
    loss_curve_matrix = []
    loss_maps = []
    fractions = []

    for unit in units:
        with logs.tracing('getting hazard'):
            assets, hazard_curves, _missings = unit.getter()

        with logs.tracing('hazard id %s' % unit.getter.hazard_id):
            curves = unit.calc(hazard_curves)
            loss_curve_matrix.append(curves)
            loss_maps.append([[conditional_loss_ratio(losses, poes, poe)
                               for losses, poes in curves]
                              for poe in conditional_loss_poes])
            fractions.append([[conditional_loss_ratio(losses, poes, poe)
                              for losses, poes in curves]
                             for poe in poes_disagg])
    return (assets,
            numpy.array(loss_curve_matrix),
            numpy.array(loss_maps),
            numpy.array(fractions))


def statistics(curve_matrix, quantiles, units, poes, poes_disagg):
    """
    :param curve_matrix:
      A numpy array with shape N x A where N is the number of the
      units (hazard realizations) and A is the number of assets.

    :returns: a tuple with
      1) N mean curve
      2) N x P mean map
      3) N x F mean fractions
      4) N x Q quantile curves
      5) N x Q x P quantile maps
      6) N x Q x F quantile fractions
    """
    weights = [unit.getter.weight for unit in units]
    ret = []

    # traverse the curve matrix on the second dimension (the assets)
    for loss_ratio_curves in curve_matrix.transpose():

        # get the loss ratios only from the first curve
        loss_ratios, _poes = loss_ratio_curves[0]
        curves_poes = [poes for _losses, poes in loss_ratio_curves]

        mean_curve, quantile_curves, mean_maps, quantile_maps = (
            base.site_statistics(
                loss_ratios, curves_poes, quantiles, weights, poes))

        # compute also mean and quantile loss fractions
        mean_fractions = [
            conditional_loss_ratio(mean_curve[0], mean_curve[1], poe)
            for poe in poes_disagg]

        quantile_fractions = [[
            conditional_loss_ratio(quantile_curve[0], quantile_curve[1], poe)
            for poe in poes_disagg]
            for quantile_curve in quantile_curves]

        ret.append(mean_curve, mean_maps, mean_fractions,
                   quantile_curves, quantile_maps, quantile_fractions)

    return zip(*ret)


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
          an instance of `..base.CalculationUnit` for the given `assets`
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

        if len(self.rc.hazard_outputs()) < 2:
            return containers

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
                self.rc.poes_disagg or []]
