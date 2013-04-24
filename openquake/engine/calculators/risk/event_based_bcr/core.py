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

import random
import numpy

from openquake.risklib import api, scientific

from openquake.engine.calculators.base import signal_task_complete
from openquake.engine.calculators.risk import base, writers
from openquake.engine.calculators.risk.event_based import core as event_based
from openquake.engine.utils import tasks
from openquake.engine import logs
from openquake.engine.db import models
from django.db import transaction


@tasks.oqtask
@base.count_progress_risk('r')
def event_based_bcr(job_id, hazard, task_seed,
                    vulnerability_function, imt,
                    vulnerability_function_retrofitted, imt_retrofitted,
                    output_containers, _statistical_output_containers,
                    time_span, tses,
                    loss_curve_resolution, asset_correlation,
                    asset_life_expectancy, interest_rate):
    """
    Celery task for the BCR risk calculator based on the event based
    calculator.

    Instantiates risklib calculators, computes bcr
    and stores results to db in a single transaction.

    :param int job_id:
        ID of the currently running job.
    :param dict hazard:
      A dictionary mapping IDs of
      :class:`openquake.engine.db.models.Output` (with output_type set
      to 'gmf_collection') to a tuple where the first element is a list
      of list (one for each asset) with the ground motion values used by the
      calculation, and the second element is the corresponding weight.
    :param str imt: the imt in long string form, i.e. SA(0.1)
    :param str imt_retrofitted:
      the imt used to get hazard in the retrofitted case
    :param output_containers: A dictionary mapping hazard Output ID to
      a tuple with only the ID of the
      :class:`openquake.engine.db.models.BCRDistribution` output container
      used to store the computed bcr distribution
    :param statistical_output_containers: not used at this moment
    :param float time_span:
        Time Span of the hazard calculation.
    :param float tses:
        Time of the Stochastic Event Set.
    :param int loss_curve_resolution:
        Resolution of the computed loss curves (number of points).
    :param int task_seed:
        Seed used to generate random values.
    :param float asset_correlation:
        asset correlation (0 uncorrelated, 1 perfectly correlated).
    :param float interest_rate
        The interest rate used in the Cost Benefit Analysis.
    :param float asset_life_expectancy
        The life expectancy used for every asset.
    """

    rnd = random.Random()
    rnd.seed(task_seed)

    for hazard_output_id, hazard_data in hazard.items():
        hazard_getter, _ = hazard_data
        bcr_distribution_id = output_containers[hazard_output_id][0]

        seed = rnd.randint(0, models.MAX_SINT_32)
        calc_original = api.ProbabilisticEventBased(
            vulnerability_function, curve_resolution=loss_curve_resolution,
            time_span=time_span, tses=tses,
            seed=seed, correlation=asset_correlation)

        seed = rnd.randint(0, models.MAX_SINT_32)
        calc_retrofitted = api.ProbabilisticEventBased(
            vulnerability_function_retrofitted,
            curve_resolution=loss_curve_resolution,
            time_span=time_span, tses=tses,
            seed=seed, correlation=asset_correlation)

        with logs.tracing('getting hazard'):
            assets, gmvs_ruptures, missings = hazard_getter(imt)
            # assets and missings do not change with imt
            _, gmvs_ruptures_retrofitted, __ = hazard_getter(imt_retrofitted)

            if len(assets):
                gmvs = numpy.array(gmvs_ruptures)[:, 0]
                gmvs_retrofitted = numpy.array(gmvs_ruptures_retrofitted)[:, 0]
            else:
                # we are relying on the fact that if all the
                # hazard_getter in this task will either return some
                # results or they all return an empty result set.
                logs.LOG.info("Exit from task as no asset could be processed")
                signal_task_complete(job_id=job_id, num_items=len(missings))
                return

        with logs.tracing('computing bcr'):
            _, original_loss_curves = calc_original(gmvs)
            _, retrofitted_loss_curves = calc_retrofitted(gmvs_retrofitted)

            eal_original = [
                scientific.average_loss(*original_loss_curves[i].xy)
                for i in range(len(assets))]

            eal_retrofitted = [
                scientific.average_loss(*retrofitted_loss_curves[i].xy)
                for i in range(len(assets))]

            bcr_results = [
                scientific.bcr(
                    eal_original[i], eal_retrofitted[i],
                    interest_rate, asset_life_expectancy,
                    asset.value, asset.retrofitting_cost)
                for i, asset in enumerate(assets)]

        with logs.tracing('writing results'):
            with transaction.commit_on_success(using='reslt_writer'):
                for i, asset in enumerate(assets):
                    writers.bcr_distribution(
                        bcr_distribution_id, asset,
                        eal_original[i], eal_retrofitted[i], bcr_results[i])

    signal_task_complete(job_id=job_id, num_items=len(assets) + len(missings))

event_based_bcr.ignore_result = False


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

    def taxonomy_args(self, taxonomy):
        return (super(EventBasedBCRRiskCalculator, self).taxonomy_args(
            taxonomy) + [self.vulnerability_functions_retrofitted[taxonomy],
                         self.taxonomy_imt_retrofitted[taxonomy]])

    @property
    def calculator_parameters(self):
        """
        Specific calculator parameters returned as list suitable to be
        passed in task_arg_gen.
        """
        time_span, tses = self.hazard_times()

        if self.rc.asset_correlation is None:
            correlation = 0
        else:
            correlation = self.rc.asset_correlation

        return [time_span, tses,
                self.rc.loss_curve_resolution, correlation,
                self.rc.asset_life_expectancy,
                self.rc.interest_rate]

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
        return [
            models.BCRDistribution.objects.create(
                hazard_output=hazard_output,
                output=models.Output.objects.create_output(
                    self.job,
                    "BCR Distribution for hazard %s" % hazard_output,
                    "bcr_distribution")).pk
        ]

    def create_statistical_outputs(self):
        """
        Override default behaviour as BCR and scenario calculators do
        not compute mean/quantiles outputs"
        """
        pass

    def set_risk_models(self):
        """
        Store both the risk model for the original asset configuration
        and the risk model for the retrofitted one.
        """
        self.vulnerability_functions, self.taxonomy_imt = (
            self.get_vulnerability_model())
        (self.vulnerability_functions_retrofitted,
         self.taxonomy_imt_retrofitted) = self.get_vulnerability_model(True)
