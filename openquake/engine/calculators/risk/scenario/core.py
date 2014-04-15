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
Core functionality for the scenario risk calculator.
"""
import random
import itertools
import numpy
from django import db

from openquake.risklib import workflows
from openquake.engine.calculators.risk import (
    base, hazard_getters, validation, writers)
from openquake.engine.db import models
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.utils import tasks


@tasks.oqtask
def scenario(job_id, risk_models, outputdict, _params):
    """
    Celery task for the scenario risk calculator.

    :param int job_id:
      ID of the currently running job
    :param list units:
      A list of :class:`openquake.risklib.workflows.CalculationUnit` instances
    :param outputdict:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (in this case only `LossMap`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    """
    monitor = EnginePerformanceMonitor(None, job_id, scenario, tracing=True)

    agg = dict()
    insured = dict()
    with db.transaction.commit_on_success(using='job_init'):
        for risk_model in risk_models:
            loss_type = risk_model.loss_type
            agg[loss_type], insured[loss_type] = do_scenario(
                risk_model,
                outputdict.with_args(
                    loss_type=loss_type,
                    output_type="loss_map"),
                monitor)
    return agg, insured


def do_scenario(risk_model, outputdict, monitor):
    """
    See `scenario` for a description of the input parameters
    """
    [output] = risk_model.compute_outputs(monitor.copy('getting data'))

    (assets, loss_ratio_matrix, aggregate_losses,
     insured_loss_matrix, insured_losses) = output.output

    with monitor.copy('saving risk outputs'):
        outputdict.write(
            assets,
            loss_ratio_matrix.mean(axis=1),
            loss_ratio_matrix.std(ddof=1, axis=1),
            hazard_output_id=risk_model.getters[0].hid,
            insured=False)

        if insured_loss_matrix is not None:
            outputdict.write(
                assets,
                insured_loss_matrix.mean(axis=1),
                insured_loss_matrix.std(ddof=1, axis=1),
                itertools.cycle([True]),
                hazard_output_id=risk_model.getters[0].hid,
                insured=True)

    return aggregate_losses, insured_losses


class ScenarioRiskCalculator(base.RiskCalculator):
    """
    Scenario Risk Calculator. Computes a Loss Map,
    for a given set of assets.
    """

    core_calc_task = scenario

    validators = base.RiskCalculator.validators + [
        validation.RequireScenarioHazard,
        validation.ExposureHasInsuranceBounds,
        validation.ExposureHasTimeEvent]

    output_builders = [writers.LossMapBuilder]

    def __init__(self, job):
        super(ScenarioRiskCalculator, self).__init__(job)
        self.aggregate_losses = dict()
        self.insured_losses = dict()

    def task_completed(self, task_result):
        self.log_percent(task_result)
        aggregate_losses_dict, insured_losses_dict = task_result

        for loss_type in models.loss_types(self.risk_models):
            aggregate_losses = aggregate_losses_dict.get(loss_type)

            if aggregate_losses is not None:
                if self.aggregate_losses.get(loss_type) is None:
                    self.aggregate_losses[loss_type] = (
                        numpy.zeros(aggregate_losses.shape))
                self.aggregate_losses[loss_type] += aggregate_losses

        if self.rc.insured_losses:
            for loss_type in models.loss_types(self.risk_models):
                insured_losses = insured_losses_dict.get(
                    loss_type)
                if insured_losses is not None:
                    if self.insured_losses.get(loss_type) is None:
                        self.insured_losses[loss_type] = numpy.zeros(
                            insured_losses.shape)
                    self.insured_losses[loss_type] += insured_losses

    def post_process(self):
        for loss_type, aggregate_losses in self.aggregate_losses.items():
            with db.transaction.commit_on_success(using='job_init'):
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

    def init_risk_model(self, model, assets):
        """
        """
        [ho] = self.rc.hazard_outputs()
        model.workflow = workflows.Scenario(
            model.vulnerability_function,
            self.rc.master_seed,
            self.rc.asset_correlation,
            self.rc.insured_losses)
        model.getters = [
            hazard_getters.ScenarioGetter(
                ho, assets, self.rc.best_maximum_distance, model.imt)]
