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
Core functionality for the scenario risk calculator.
"""
import itertools
import numpy
from django import db

from openquake.risklib import api, scientific

from openquake.engine import logs
from openquake.engine.calculators.base import signal_task_complete
from openquake.engine.calculators.risk import base, hazard_getters
from openquake.engine.utils import tasks
from openquake.engine.db import models
from openquake.engine.performance import EnginePerformanceMonitor


@tasks.oqtask
@base.count_progress_risk('r')
def scenario(job_id, units, containers, params):
    """
    Celery task for the scenario risk calculator.

    :param int job_id:
      ID of the currently running job
    :param list units:
      A list of :class:`..base.CalculationUnit` to be run
    :param containers:
      An instance of :class:`..base.OutputDict` containing
      output container instances (in this case only `LossMap`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    """
    def profile(name):
        return EnginePerformanceMonitor(name, job_id, scenario, tracing=True)

    # in scenario calculation we have only ONE calculation unit
    unit = units[0]

    with db.transaction.commit_on_success(using='reslt_writer'):
        agg, insured = do_scenario(unit, containers, params, profile)
    signal_task_complete(
        job_id=job_id, num_items=len(unit.getter.assets),
        aggregate_losses=agg, insured_aggregate_losses=insured)
scenario.ignore_result = False


def do_scenario(unit, containers, params, profile):
    """
    See `scenario` for a description of the input parameters
    """

    with profile('getting hazard'):
        assets, ground_motion_values, _ = unit.getter()

    if not len(assets):
        logs.LOG.info("Exit from task as no asset could be processed")
        return

    with profile('computing risk'):
        loss_ratio_matrix = unit.calc(ground_motion_values)

        if params.insured_losses:
            insured_loss_matrix = [
                scientific.insured_losses(
                    loss_ratio_matrix[i], asset.value,
                    asset.deductible, asset.ins_limit)
                for i, asset in enumerate(assets)]

    with profile('saving risk outputs'):
        containers.write(
            assets,
            [losses.mean() for losses in loss_ratio_matrix],
            [losses.std(ddof=1) for losses in loss_ratio_matrix],
            output_type="loss_map",
            hazard_output_id=unit.getter.hazard_output_id,
            insured=False)

        if params.insured_losses:
            containers.write(
                assets,
                [losses.mean() for losses in insured_loss_matrix],
                [losses.std(ddof=1) for losses in insured_loss_matrix],
                itertools.cycle([True]),
                output_type="loss_map",
                hazard_output_id=unit.getter.hazard_output_id,
                insured=True)

    aggregate_losses = sum(loss_ratio_matrix[i] * asset.value
                           for i, asset in enumerate(assets))

    if params.insured_losses:
        insured_aggregate_losses = (
            numpy.array(insured_loss_matrix).transpose().sum(axis=1))
    else:
        insured_aggregate_losses = "Not computed"

    return aggregate_losses, insured_aggregate_losses


class ScenarioRiskCalculator(base.RiskCalculator):
    """
    Scenario Risk Calculator. Computes a Loss Map,
    for a given set of assets.
    """

    core_calc_task = scenario

    def __init__(self, job):
        super(ScenarioRiskCalculator, self).__init__(job)
        self.aggregate_losses = None
        self.insured_aggregate_losses = None

    def pre_execute(self):
        """
        Override the default pre_execute to provide more detailed
        validation.

        2) If insured losses are required we check for the presence of
        the deductible and insurance limit
        """
        if self.rc.hazard_calculation:
            if self.rc.hazard_calculation.calculation_mode != "scenario":
                raise RuntimeError(
                    "The provided hazard calculation ID "
                    "is not a scenario calculation")
        elif not self.rc.hazard_output.output_type == "gmf_scenario":
            raise RuntimeError(
                "The provided hazard output is not a gmf scenario collection")

        super(ScenarioRiskCalculator, self).pre_execute()

        if self.rc.insured_losses:
            queryset = self.rc.exposure_model.exposuredata_set.filter(
                (db.models.Q(deductible__isnull=True) |
                 db.models.Q(ins_limit__isnull=True)))
            if queryset.exists():
                logs.LOG.error(
                    "missing insured limits in exposure for assets %s" % (
                        queryset.all()))
                raise RuntimeError(
                    "Deductible or insured limit missing in exposure")

    def task_completed_hook(self, message):
        aggregate_losses = message.get('aggregate_losses')

        if aggregate_losses is not None:
            if self.aggregate_losses is None:
                self.aggregate_losses = numpy.zeros(aggregate_losses.shape)
            self.aggregate_losses += aggregate_losses

        if self.rc.insured_losses:
            insured_aggregate_losses = message.get('insured_aggregate_losses')

            if insured_aggregate_losses is not None:
                if self.insured_aggregate_losses is None:
                    self.insured_aggregate_losses = numpy.zeros(
                        insured_aggregate_losses.shape)
                self.insured_aggregate_losses += insured_aggregate_losses

    def post_process(self):
        with db.transaction.commit_on_success(using='reslt_writer'):
            if self.aggregate_losses is not None:
                models.AggregateLoss.objects.create(
                    output=models.Output.objects.create_output(
                        self.job, "Aggregate Loss",
                        "aggregate_loss"),
                    mean=numpy.mean(self.aggregate_losses),
                    std_dev=numpy.std(self.aggregate_losses, ddof=1))

            if (self.rc.insured_losses and
                self.insured_aggregate_losses is not None):
                models.AggregateLoss.objects.create(
                    output=models.Output.objects.create_output(
                        self.job, "Insured Aggregate Loss",
                        "aggregate_loss"),
                    insured=True,
                    mean=numpy.mean(self.insured_aggregate_losses),
                    std_dev=numpy.std(self.insured_aggregate_losses, ddof=1))

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
            api.Scenario(
                vulnerability_function,
                seed=self.rnd.randint(0, models.MAX_SINT_32),
                correlation=self.rc.asset_correlation),
            hazard_getters.GroundMotionScenarioGetter(
                ho,
                assets,
                self.rc.best_maximum_distance,
                self.taxonomy_imt[taxonomy]))
                for ho in self.rc.hazard_outputs()]

    @property
    def calculator_parameters(self):
        """
        Provides calculator specific params coming from
        :class:`openquake.engine.db.RiskCalculation`
        """

        return base.make_calc_params(insured_losses=self.rc.insured_losses)

    def create_outputs(self, hazard_output):
        """
        Create the the output of a ScenarioRisk calculator
        which is a LossMap.
        """
        ret = base.OutputDict()

        if self.rc.insured_losses:
            ret.set(models.LossMap.objects.create(
                output=models.Output.objects.create_output(
                    self.job, "Insured Loss Map", "loss_map"),
                hazard_output=hazard_output,
                insured=True))

        ret.set(models.LossMap.objects.create(
                output=models.Output.objects.create_output(
                    self.job, "Loss Map", "loss_map"),
                hazard_output=hazard_output))
        return ret

    def create_statistical_outputs(self):
        """
        Override default behaviour as BCR and scenario calculators do
        not compute mean/quantiles outputs"
        """
        return base.OutputDict()
