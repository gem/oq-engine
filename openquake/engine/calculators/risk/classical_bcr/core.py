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
Core functionality for the classical PSHA risk calculator.
"""

from django.db import transaction
from openquake.risklib import workflows

from openquake.engine.calculators.risk import (
    hazard_getters, writers, validation)
from openquake.engine.calculators.risk.classical import core as classical
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.utils import tasks


@tasks.oqtask
def classical_bcr(job_id, risk_models, outputdict, _params):
    """
    Celery task for the BCR risk calculator based on the classical
    calculator.

    Instantiates risklib calculators, computes BCR and stores the
    results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param list risk_models:
      A list of :class:`openquake.risklib.workflows.CalculationUnit`
    :param outputdict:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (in this case only `BCRDistribution`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    """
    monitor = EnginePerformanceMonitor(
        None, job_id, classical_bcr, tracing=True)

    # Do the job in other functions, such that it can be unit tested
    # without the celery machinery
    with transaction.commit_on_success(using='job_init'):
        for risk_model in risk_models:
            do_classical_bcr(
                risk_model,
                outputdict.with_args(loss_type=risk_model.loss_type),
                monitor)


def do_classical_bcr(risk_model, outputdict, monitor):
    outputs = risk_model.compute_outputs(monitor.copy('getting hazard'))

    with monitor.copy('writing results'):
        for out in outputs:
            outputdict.write(
                risk_model.workflow.assets,
                out.output,
                output_type="bcr_distribution",
                hazard_output_id=out.hid)


class ClassicalBCRRiskCalculator(classical.ClassicalRiskCalculator):
    """
    Classical BCR risk calculator. Computes BCR distributions for a
    given set of assets.

    :attr dict vulnerability_functions_retrofitted:
        A dictionary mapping each taxonomy to a vulnerability functions for the
        retrofitted losses computation
    """
    core_calc_task = classical_bcr

    validators = classical.ClassicalRiskCalculator.validators + [
        validation.ExposureHasRetrofittedCosts]

    output_builders = [writers.BCRMapBuilder]

    def __init__(self, job):
        super(ClassicalBCRRiskCalculator, self).__init__(job)
        self.risk_models_retrofitted = None

    def init_risk_model(self, model, assets):
        """
        Set the attributes .workflow and .getters
        """
        taxonomy = assets[0].taxonomy  # all the assets have the same taxonomy
        model_orig = self.risk_models[taxonomy][model.loss_type]
        model_retro = self.risk_models_retrofitted[taxonomy][model.loss_type]
        max_dist = self.rc.best_maximum_distance
        model.workflow = workflows.ClassicalBCR(
            model_orig.vulnerability_function,
            model_retro.vulnerability_function,
            self.rc.lrem_steps_per_interval,
            self.rc.interest_rate,
            self.rc.asset_life_expectancy)
        model.getters = [
            hazard_getters.BCRGetter(
                hazard_getters.HazardCurveGetterPerAsset(
                    ho, assets, max_dist, model_orig.imt),
                hazard_getters.HazardCurveGetterPerAsset(
                    ho, assets, max_dist, model_retro.imt))
            for ho in self.rc.hazard_outputs()]

    def pre_execute(self):
        """
        Store both the risk model for the original asset configuration
        and the risk model for the retrofitted one.
        """
        super(ClassicalBCRRiskCalculator, self).pre_execute()
        self.risk_models_retrofitted = self.get_risk_models(retrofitted=True)
