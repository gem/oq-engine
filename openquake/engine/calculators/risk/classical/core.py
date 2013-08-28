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

import itertools
from openquake.risklib import workflows

from django.db import transaction

from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.calculators import post_processing
from openquake.engine.calculators.risk import (
    base, hazard_getters, validation, writers)


@base.risk_task
def classical(job_id, units, containers, params):
    """
    Celery task for the classical risk calculator.

    :param int job_id:
      ID of the currently running job
    :param list units:
      A list of :class:`openquake.risklib.workflows.CalculationUnit` instances
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
        for unit in units:
            do_classical(
                unit,
                containers.with_args(loss_type=unit.loss_type),
                params,
                profile)


def do_classical(unit, containers, params, profile):
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

    outputs, stats = unit(profile('getting data'),
                          profile('computing individual risk'),
                          post_processing, params.quantiles)

    with profile('saving risk'):
        for out in outputs:
            save_individual_outputs(
                containers.with_args(hazard_output_id=out.hid),
                out.output, params)

        if stats is not None:
            save_statistical_output(
                containers.with_args(hazard_output_id=None), stats, params)


def save_individual_outputs(containers, outs, params):
    """
    Save loss curves, loss maps and loss fractions associated with a
    calculation unit

    :param containers:
        a :class:`openquake.engine.calculators.risk.writers.OutputDict`
        instance holding the reference to the output container objects
    :param outs:
        a :class:`openquake.risklib.workflows.Classical.Output`
        holding the output data for a calculation unit
    :param params:
        a :class:`openquake.engine.calculators.risk.base.CalcParams`
        holding the parameters for this calculation
    """

    containers.write(
        outs.assets,
        (outs.loss_curves, outs.average_losses),
        output_type="loss_curve")

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


def save_statistical_output(containers, stats, params):
    """
    Save statistical outputs (mean and quantile loss curves, mean and
    quantile loss maps, mean and quantile loss fractions) for the
    calculation.

    :param containers:
        a :class:`openquake.engine.calculators.risk.writers.OutputDict`
        instance holding the reference to the output container objects
    :param outs:
        a :class:`openquake.risklib.workflows.Classical.StatisticalOutput`
        holding the statistical output data
    :param params:
        a :class:`openquake.engine.calculators.risk.base.CalcParams`
        holding the parameters for this calculation
    """

    # mean curves, maps and fractions
    containers.write(
        stats.assets, (stats.mean_curves, stats.mean_average_losses),
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
        "quantile", params.quantiles,
        [(c, a) for c, a in itertools.izip(
            stats.quantile_curves, stats.quantile_average_losses)],
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

    validators = base.RiskCalculator.validators + [
        validation.RequireClassicalHazard]

    output_builders = [writers.LossCurveMapBuilder,
                       writers.ConditionalLossFractionBuilder]

    def calculation_unit(self, loss_type, assets):
        """
        :returns:
          a :class:`openquake.risklib.workflows.CalculationUnit`
          instance for the given `loss_type` and `assets` to be run in
          the celery task
        """

        # assume all assets have the same taxonomy
        taxonomy = assets[0].taxonomy
        model = self.risk_models[taxonomy][loss_type]

        return workflows.CalculationUnit(
            loss_type,
            workflows.Classical(
                model.vulnerability_function,
                self.rc.lrem_steps_per_interval,
                self.rc.conditional_loss_poes,
                self.rc.poes_disagg),
            hazard_getters.HazardCurveGetterPerAsset(
                self.rc.hazard_outputs(),
                assets,
                self.rc.best_maximum_distance,
                model.imt))

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
