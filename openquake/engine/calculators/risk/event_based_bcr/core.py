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

from openquake.risklib import api, scientific, utils

from openquake.engine.calculators.base import signal_task_complete
from openquake.engine.calculators.risk import base, hazard_getters
from openquake.engine.calculators.risk.event_based import core as event_based
from openquake.engine.utils import tasks
from openquake.engine import logs
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.db import models
from django.db import transaction


@tasks.oqtask
@base.count_progress_risk('r')
def event_based_bcr(job_id, units, containers, params):
    """
    Celery task for the BCR risk calculator based on the event based
    calculator.

    Instantiates risklib calculators, computes bcr
    and stores results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param list units:
      A list of :class:`..base.CalculationUnit` to be run
    :param containers:
      An instance of :class:`..base.OutputDict` containing
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
        do_event_based_bcr(units, containers, params, profile)
    signal_task_complete(job_id=job_id, num_items=len(units[0].getter.assets))
event_based_bcr.ignore_result = False


def do_event_based_bcr(units, containers, params, profile):
    """
    See `event_based_bcr` for docstring
    """
    for unit_orig, unit_retro in utils.pairwise(units):
        with profile('getting hazard'):
            assets, (gmvs, _) = unit_orig.getter()
            if len(assets) == 0:
                logs.LOG.info("Exit from task as no asset could be processed")
                return

            _, (gmvs_retro, _) = unit_retro.getter()

        with profile('computing bcr'):
            _, original_loss_curves = unit_orig.calc(gmvs)
            _, retrofitted_loss_curves = unit_retro.calc(gmvs_retro)

            eal_original = [
                scientific.average_loss(losses, poes)
                for losses, poes in original_loss_curves]

            eal_retrofitted = [
                scientific.average_loss(losses, poes)
                for losses, poes in retrofitted_loss_curves]

            bcr_results = [
                scientific.bcr(
                    eal_original[i], eal_retrofitted[i],
                    params.interest_rate, params.asset_life_expectancy,
                    asset.value, asset.retrofitting_cost)
                for i, asset in enumerate(assets)]

        with profile('writing results'):
            containers.write(
                assets, zip(eal_original, eal_retrofitted, bcr_results),
                output_type="bcr_distribution",
                hazard_output_id=unit_orig.getter.hazard_output_id)


class EventBasedBCRRiskCalculator(event_based.EventBasedRiskCalculator):
    """
    Event based BCR risk calculator. Computes BCR distributions for a
    given set of assets.
    """
    core_calc_task = event_based_bcr

    def __init__(self, job):
        super(EventBasedBCRRiskCalculator, self).__init__(job)
        self.vulnerability_functions_retrofitted = None
        self.taxonomy_imt_retrofitted = dict()

    def calculation_units(self, assets):
        """
        :returns:
          a list of instances of `..base.CalculationUnit` for the given
          `assets` to be run in the celery task
        """

        # assume all assets have the same taxonomy
        taxonomy = assets[0].taxonomy
        vf_orig = self.vulnerability_functions[taxonomy]
        vf_retro = self.vulnerability_functions_retrofitted[taxonomy]

        time_span, tses = self.hazard_times()

        units = []

        for ho in self.rc.hazard_outputs():
            units.extend([
                base.CalculationUnit(
                    api.ProbabilisticEventBased(
                        vf_orig,
                        curve_resolution=self.rc.loss_curve_resolution,
                        time_span=time_span,
                        tses=tses,
                        seed=self.rnd.randint(0, models.MAX_SINT_32),
                        correlation=self.rc.asset_correlation),
                hazard_getters.GroundMotionValuesGetter(
                    ho,
                    assets,
                    self.rc.best_maximum_distance,
                    self.taxonomy_imt[taxonomy])),
                base.CalculationUnit(
                    api.ProbabilisticEventBased(
                        vf_retro,
                        curve_resolution=self.rc.loss_curve_resolution,
                        time_span=time_span,
                        tses=tses,
                        seed=self.rnd.randint(0, models.MAX_SINT_32),
                        correlation=self.rc.asset_correlation),
                hazard_getters.GroundMotionValuesGetter(
                    ho,
                    assets,
                    self.rc.best_maximum_distance,
                    self.taxonomy_imt_retrofitted[taxonomy]))])
        return units

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

        :returns: A list containing the output container id.
        """
        ret = base.OutputDict()
        ret.set(models.BCRDistribution.objects.create(
                hazard_output=hazard_output,
                output=models.Output.objects.create_output(
                    self.job,
                    "BCR Distribution for hazard %s" % hazard_output,
                    "bcr_distribution")))
        return ret

    def create_statistical_outputs(self):
        """
        Override default behaviour as BCR and scenario calculators do
        not compute mean/quantiles outputs"
        """
        return base.OutputDict()

    def set_risk_models(self):
        """
        Store both the risk model for the original asset configuration
        and the risk model for the retrofitted one.
        """
        self.vulnerability_functions, self.taxonomy_imt = (
            self.get_vulnerability_model())
        (self.vulnerability_functions_retrofitted,
         self.taxonomy_imt_retrofitted) = self.get_vulnerability_model(True)
