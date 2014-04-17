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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Core functionality for the Event Based BCR Risk calculator.
"""
from django.db import transaction

from openquake.risklib import workflows

from openquake.engine.calculators.risk import (
    hazard_getters, writers, validation)
from openquake.engine.calculators.risk.event_based import core as event_based
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.utils import tasks


@tasks.oqtask
def event_based_bcr(job_id, risk_model, loss_types, outputdict, _params):
    """
    Celery task for the BCR risk calculator based on the event based
    calculator.

    Instantiates risklib calculators, computes bcr
    and stores results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param list risk_models:
      A list of :class:`openquake.risklib.workflows.CalculationUnit` instances
    :param outputdict:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (in this case only `BCRDistribution`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    """
    monitor = EnginePerformanceMonitor(
        None, job_id, event_based_bcr, tracing=True)

    # Do the job in other functions, such that it can be unit tested
    # without the celery machinery
    with transaction.commit_on_success(using='job_init'):
        for loss_type in loss_types:
            risk_model.loss_type = loss_type
            do_event_based_bcr(
                risk_model,
                outputdict.with_args(loss_type=loss_type),
                monitor)


def do_event_based_bcr(risk_model, outputdict, monitor):
    """
    See `event_based_bcr` for docstring
    """
    outputs = risk_model.compute_outputs(monitor.copy('getting hazard'))

    with monitor.copy('writing results'):
        for out in outputs:
            outputdict.write(
                risk_model. workflow.assets,
                out.output,
                output_type="bcr_distribution",
                hazard_output_id=out.hid)


class EventBasedBCRRiskCalculator(event_based.EventBasedRiskCalculator):
    """
    Event based BCR risk calculator. Computes BCR distributions for a
    given set of assets.
    """
    core_calc_task = event_based_bcr

    validators = event_based.EventBasedRiskCalculator.validators + [
        validation.ExposureHasRetrofittedCosts]

    output_builders = [writers.BCRMapBuilder]

    getter_cls = hazard_getters.GroundMotionValuesGetter

    def __init__(self, job):
        super(EventBasedBCRRiskCalculator, self).__init__(job)
        self.risk_models_retrofitted = None

    def get_workflow(self, taxonomy):
        model_orig = self.risk_models[taxonomy]
        model_retro = self.risk_models_retrofitted[taxonomy]
        time_span, tses = self.hazard_times()
        return workflows.ProbabilisticEventBasedBCR(
            model_orig.vulnerability_function,
            model_retro.vulnerability_function,
            time_span, tses, self.rc.loss_curve_resolution,
            self.rc.interest_rate,
            self.rc.asset_life_expectancy)

    def post_process(self):
        """
        No need to compute the aggregate loss curve in the BCR calculator.
        """

    def task_completed(self, event_loss_tables):
        """
        No need to update event loss tables in the BCR calculator
        """
        self.log_percent(event_loss_tables)

    def pre_execute(self):
        """
        Store both the risk model for the original asset configuration
        and the risk model for the retrofitted one.
        """
        super(EventBasedBCRRiskCalculator, self).pre_execute()
        self.risk_models_retrofitted = self.get_risk_models(retrofitted=True)
