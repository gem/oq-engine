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
import random
import itertools
import numpy
from django import db

from openquake.risklib import api, scientific

from openquake.engine import logs
from openquake.engine.calculators.base import signal_task_complete
from openquake.engine.calculators.risk import base, hazard_getters, writers
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
    :param dict units:
      A dict of :class:`..base.CalculationUnit` instances keyed by
      loss type string
    :param containers:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (in this case only `LossMap`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    """
    def profile(name):
        return EnginePerformanceMonitor(name, job_id, scenario, tracing=True)

    agg = dict()
    insured = dict()
    with db.transaction.commit_on_success(using='reslt_writer'):
        for loss_type in units:
            # in scenario calculation we have only ONE calculation unit
            unit = units[loss_type][0]
            agg[loss_type], insured[loss_type] = do_scenario(
                loss_type, unit, containers, params, profile)
    num_items = base.get_num_items(units)
    signal_task_complete(
        job_id=job_id, num_items=num_items,
        aggregate_losses=agg, insured_losses=insured)
scenario.ignore_result = False


def do_scenario(loss_type, unit, containers, params, profile):
    """
    See `scenario` for a description of the input parameters
    """

    with profile('getting hazard'):
        assets, ground_motion_values = unit.getter()

    if not len(assets):
        logs.LOG.info("Exit from task as no asset could be processed")
        return None, None

    with profile('computing risk'):
        loss_ratio_matrix = unit.calc(ground_motion_values)

        if params.insured_losses:
            insured_loss_matrix = [
                scientific.insured_losses(
                    loss_ratio_matrix[i], asset.value(loss_type),
                    asset.deductible(loss_type),
                    asset.insurance_limit(loss_type))
                for i, asset in enumerate(assets)]

    with profile('saving risk outputs'):
        containers.write(
            assets,
            [losses.mean() for losses in loss_ratio_matrix],
            [losses.std(ddof=1) for losses in loss_ratio_matrix],
            output_type="loss_map",
            loss_type=loss_type,
            hazard_output_id=unit.getter.hazard_output.id,
            insured=False)

        if params.insured_losses:
            containers.write(
                assets,
                [losses.mean() for losses in insured_loss_matrix],
                [losses.std(ddof=1) for losses in insured_loss_matrix],
                itertools.cycle([True]),
                output_type="loss_map",
                loss_type=loss_type,
                hazard_output_id=unit.getter.hazard_output.id,
                insured=True)

    aggregate_losses = sum(loss_ratio_matrix[i] * asset.value(loss_type)
                           for i, asset in enumerate(assets))

    if params.insured_losses:
        insured_losses = (
            numpy.array(insured_loss_matrix).transpose().sum(axis=1))
    else:
        insured_losses = "Not computed"

    return aggregate_losses, insured_losses


class ScenarioRiskCalculator(base.RiskCalculator):
    """
    Scenario Risk Calculator. Computes a Loss Map,
    for a given set of assets.
    """

    core_calc_task = scenario

    def __init__(self, job):
        super(ScenarioRiskCalculator, self).__init__(job)
        self.aggregate_losses = dict()
        self.insured_losses = dict()
        self.rnd = random.Random()
        self.rnd.seed(self.rc.master_seed)

    def validate_hazard(self):
        super(ScenarioRiskCalculator, self).validate_hazard()
        if self.rc.hazard_calculation:
            if self.rc.hazard_calculation.calculation_mode != "scenario":
                raise RuntimeError(
                    "The provided hazard calculation ID "
                    "is not a scenario calculation")
        elif not self.rc.hazard_output.output_type == "gmf_scenario":
            raise RuntimeError(
                "The provided hazard output is not a gmf scenario collection")

    def get_taxonomies(self):
        """
        If insured losses are required we check for the presence of
        the deductible and insurance limit
        """
        taxonomies = super(ScenarioRiskCalculator, self).get_taxonomies()
        if self.rc.insured_losses:
            queryset = self.rc.exposure_model.exposuredata_set.filter(
                (db.models.Q(cost__deductible_absolute__isnull=True) |
                 db.models.Q(cost__insurance_limit_absolute__isnull=True)))
            if queryset.exists():
                logs.LOG.error(
                    "missing insured limits in exposure for assets %s" % (
                        queryset.all()))
                raise RuntimeError(
                    "Deductible or insured limit missing in exposure")
        return taxonomies

    def task_completed_hook(self, message):
        aggregate_losses_dict = message.get('aggregate_losses')

        for loss_type in base.loss_types(self.risk_models):
            aggregate_losses = aggregate_losses_dict.get(loss_type)

            if aggregate_losses is not None:
                if self.aggregate_losses.get(loss_type) is None:
                    self.aggregate_losses[loss_type] = (
                        numpy.zeros(aggregate_losses.shape))
                self.aggregate_losses[loss_type] += aggregate_losses

        if self.rc.insured_losses:
            insured_losses_dict = message.get('insured_losses')
            for loss_type in base.loss_types(self.risk_models):
                insured_losses = insured_losses_dict.get(
                    loss_type)
                if insured_losses is not None:
                    if self.insured_losses.get(loss_type) is None:
                        self.insured_losses[loss_type] = numpy.zeros(
                            insured_losses.shape)
                    self.insured_losses[loss_type] += insured_losses

    def post_process(self):
        for loss_type, aggregate_losses in self.aggregate_losses.items():
            with db.transaction.commit_on_success(using='reslt_writer'):
                models.AggregateLoss.objects.create(
                    output=models.Output.objects.create_output(
                        self.job,
                        "aggregate loss. type=%s" % loss_type,
                        "aggregate_loss"),
                    loss_type=loss_type,
                    mean=numpy.mean(aggregate_losses),
                    std_dev=numpy.std(aggregate_losses, ddof=1))

                if self.rc.insured_losses:
                    insured_losses = self.insured_losses[loss_type]
                    models.AggregateLoss.objects.create(
                        output=models.Output.objects.create_output(
                            self.job,
                            "insured aggregate loss. type=%s" % loss_type,
                            "aggregate_loss"),
                        insured=True,
                        loss_type=loss_type,
                        mean=numpy.mean(insured_losses),
                        std_dev=numpy.std(insured_losses, ddof=1))

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
            api.Scenario(
                model.vulnerability_function,
                seed=self.rnd.randint(0, models.MAX_SINT_32),
                correlation=self.rc.asset_correlation),
            hazard_getters.GroundMotionValuesGetter(
                ho,
                assets,
                self.rc.best_maximum_distance,
                model.imt))
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
        ret = writers.OutputDict()

        for loss_type in base.loss_types(self.risk_models):
            if self.rc.insured_losses:
                ret.set(models.LossMap.objects.create(
                    output=models.Output.objects.create_output(
                        self.job, "Insured Loss Map", "loss_map"),
                    hazard_output=hazard_output,
                    loss_type=loss_type,
                    insured=True))

            ret.set(models.LossMap.objects.create(
                    output=models.Output.objects.create_output(
                        self.job, "Loss Map", "loss_map"),
                    hazard_output=hazard_output,
                    loss_type=loss_type))
        return ret

    def create_statistical_outputs(self):
        """
        Override default behaviour as BCR and scenario calculators do
        not compute mean/quantiles outputs"
        """
        return writers.OutputDict()
