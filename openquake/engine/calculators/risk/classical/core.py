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

from openquake.risklib import workflows

from django.db import transaction

from openquake.engine.db import models
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.calculators import post_processing
from openquake.engine.calculators.risk import base, hazard_getters


@base.risk_task
def classical(job_id, units, containers, params):
    """
    Celery task for the classical risk calculator.

    :param int job_id:
      ID of the currently running job
    :param list units:
      A list of :class:`openquake.risklib.workflow.CalculationUnit` instances
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

    for hazard_output_id, outputs in unit.workflow(
            unit.getter(profile('getting data')),
            profile('computing individual risk')):
        with profile('saving individual risk'):
            save_individual_outputs(
                containers.with_args(hazard_output_id=hazard_output_id),
                params,
                outputs)

    with profile('computing risk statistics'):
        stats = unit.workflow.statistics(
            unit.getter.weights(),
            params.quantiles,
            post_processing)

    with profile('saving risk statistics'):
        if stats is not None:
            save_statistical_output(
                containers.with_args(hazard_output_id=None), stats, params)


def save_individual_outputs(containers, params, outs):
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
