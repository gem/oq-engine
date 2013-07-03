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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Core functionality for the Event Based BCR Risk calculator.
"""

from openquake.risklib import workflows

from openquake.engine.calculators.risk import base, hazard_getters, writers
from openquake.engine.calculators.risk.event_based import core as event_based
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.db import models
from django.db import transaction


@base.risk_task
def event_based_bcr(job_id, units, containers, _params):
    """
    Celery task for the BCR risk calculator based on the event based
    calculator.

    Instantiates risklib calculators, computes bcr
    and stores results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param list units:
      A list of :class:`openquake.risklib.workflows.CalculationUnit` instances
    :param containers:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (in this case only `BCRDistribution`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    """
    def profile(name):
        return EnginePerformanceMonitor(
            name, job_id, event_based_bcr, tracing=True)

    # Do the job in other functions, such that it can be unit tested
    # without the celery machinery
    with transaction.commit_on_success(using='reslt_writer'):
        for unit in units:
            do_event_based_bcr(
                unit,
                containers.with_args(loss_type=unit.loss_type),
                profile)


def do_event_based_bcr(unit, containers, profile):
    """
    See `event_based_bcr` for docstring
    """
    for hazard_output_id, outputs in unit.workflow(
            unit.loss_type,
            unit.getter(profile('getting hazard')),
            profile('computing bcr')):

        with profile('writing results'):
            containers.write(
                unit.workflow.assets,
                outputs,
                output_type="bcr_distribution",
                hazard_output_id=hazard_output_id)


class EventBasedBCRRiskCalculator(event_based.EventBasedRiskCalculator):
    """
    Event based BCR risk calculator. Computes BCR distributions for a
    given set of assets.
    """
    core_calc_task = event_based_bcr

    def __init__(self, job):
        super(EventBasedBCRRiskCalculator, self).__init__(job)
        self.risk_models_retrofitted = None

    def calculation_unit(self, loss_type, assets):
        """
        :returns:
          a list of instances of `..base.CalculationUnit` for the given
          `assets` to be run in the celery task
        """

        # assume all assets have the same taxonomy
        taxonomy = assets[0].taxonomy
        model_orig = self.risk_models[taxonomy][loss_type]
        model_retro = self.risk_models_retrofitted[taxonomy][loss_type]

        time_span, tses = self.hazard_times()

        return workflows.CalculationUnit(
            loss_type,
            workflows.ProbabilisticEventBasedBCR(
                model_orig.vulnerability_function,
                self.rnd.randint(0, models.MAX_SINT_32),
                model_retro.vulnerability_function,
                self.rnd.randint(0, models.MAX_SINT_32),
                self.rc.asset_correlation,
                time_span, tses, self.rc.loss_curve_resolution,
                self.rc.interest_rate,
                self.rc.asset_life_expectancy),
            hazard_getters.BCRGetter(
                hazard_getters.GroundMotionValuesGetter(
                    self.rc.hazard_outputs(),
                    assets,
                    self.rc.best_maximum_distance,
                    model_orig.imt),
                hazard_getters.GroundMotionValuesGetter(
                    self.rc.hazard_outputs(),
                    assets,
                    self.rc.best_maximum_distance,
                    model_retro.imt)))

    def get_taxonomies(self):
        """
        Override the default get_taxonomies to provide more detailed
        validation of the exposure.

        Check that the reco value is present in the exposure
        """
        taxonomies = super(EventBasedBCRRiskCalculator, self).get_taxonomies()

        if (self.rc.exposure_model.exposuredata_set.filter(
                cost__converted_retrofitted_cost__isnull=True)).exists():
            raise ValueError("Some assets do not have retrofitted costs")

        return taxonomies

    @property
    def calculator_parameters(self):
        """
        Specific calculator parameters returned as list suitable to be
        passed in task_arg_gen.
        """
        return base.make_calc_params(
            asset_life_expectancy=self.rc.asset_life_expectancy,
            interest_rate=self.rc.interest_rate)

    def post_process(self):
        """
        No need to compute the aggregate loss curve in the BCR calculator.
        """

    def task_completed_hook(self, _message):
        """
        No need to update event loss tables in the BCR calculator
        """

    def create_outputs(self, hazard_output):
        """
        Create BCR Distribution output container, i.e. a
        :class:`openquake.engine.db.models.BCRDistribution` instance and its
        :class:`openquake.engine.db.models.Output` container.

        :returns: an instance of OutputDict.
        """
        ret = writers.OutputDict()
        for loss_type in base.loss_types(self.risk_models):
            name = "BCR Map. type=%s hazard=%s" % (loss_type, hazard_output)
            ret.set(models.BCRDistribution.objects.create(
                    hazard_output=hazard_output,
                    loss_type=loss_type,
                    output=models.Output.objects.create_output(
                        self.job, name, "bcr_distribution")))

        return ret

    def create_statistical_outputs(self):
        """
        Override default behaviour as BCR and scenario calculators do
        not compute mean/quantiles outputs"
        """
        return writers.OutputDict()

    def pre_execute(self):
        """
        Store both the risk model for the original asset configuration
        and the risk model for the retrofitted one.
        """
        super(EventBasedBCRRiskCalculator, self).pre_execute()
        models_retro = super(
            EventBasedBCRRiskCalculator, self).get_risk_models(
                retrofitted=True)
        self.check_taxonomies(models_retro)
        self.check_imts(base.required_imts(models_retro))
        self.risk_models_retrofitted = models_retro
