# Copyright (c) 2010-2012, GEM Foundation.
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

from risklib import api

from openquake.calculators import base
from openquake.calculators.risk import general
from openquake.calculators.risk.event_based import core as event_based
from openquake.utils import stats
from openquake.utils import tasks
from openquake import logs
from openquake.db import models
from django.db import transaction


@tasks.oqtask
@stats.count_progress('r')
def event_based_bcr(job_id, assets, hazard_getter, hazard_id,
                    bcr_distribution_id, imt, time_span, tses,
                    loss_curve_resolution, seed, asset_correlation,
                    asset_life_expectancy, interest_rate):
    """
    Celery task for the BCR risk calculator based on the event based
    calculator.

    Gets the vulnerability models, instantiates risklib calculators
    and stores results to db in a single transaction.

    :param int job_id:
        ID of the currently running job.
    :param assets:
        list of assets to compute.
    :param hazard_getter:
        Strategy used to get the hazard inputs (ground motion fields).
    :param int hazard_id
        ID of the hazard output the risk calculation is based on.
    :param int bcr_distribution_id
        ID of the :class:`openquake.db.models.BCRDistribution` output
        container used to store the computed BCR distribution.
    :param float imt:
        Intensity Measure Type to take into account.
    :param float time_span:
        Time Span of the hazard calculation.
    :param float tses:
        Time of the Stochastic Event Set.
    :param int loss_curve_resolution:
        Resolution of the computed loss curves (number of points).
    :param int seed:
        Seed used to generate random values.
    :param int asset_correlation:
        Type of assets correlation (0 uncorrelated,
        1 perfectly correlated).
    :param float interest_rate
        The interest rate used in the Cost Benefit Analysis.
    :param float asset_life_expectancy
        The life expectancy used for every asset.
    """
    model = general.fetch_vulnerability_model(job_id)
    model_retrofitted = general.fetch_vulnerability_model(job_id, True)

    hazard_getter = general.hazard_getter(
        hazard_getter, hazard_id, imt, time_span, tses)

    calculator = api.probabilistic_event_based(
        model, curve_resolution=loss_curve_resolution,
        seed=seed, correlation_type=asset_correlation)

    calculator_retrofitted = api.probabilistic_event_based(
        model_retrofitted, curve_resolution=loss_curve_resolution,
        seed=seed, correlation_type=asset_correlation)

    bcr_calculator = api.bcr(calculator, calculator_retrofitted,
        interest_rate, asset_life_expectancy)

    with transaction.commit_on_success(using="reslt_writer"):
        logs.LOG.debug(
            "launching compute_on_assets over %d assets" % len(assets))

        for asset_output in api.compute_on_assets(
            assets, hazard_getter, bcr_calculator):
            general.write_bcr_distribution(bcr_distribution_id, asset_output)
    base.signal_task_complete(job_id=job_id, num_items=len(assets))

event_based_bcr.ignore_result = False


class EventBasedBCRRiskCalculator(event_based.EventBasedRiskCalculator):
    """
    Event based BCR risk calculator. Computes BCR distributions for a
    given set of assets.
    """
    core_calc_task = event_based_bcr

    @property
    def calculator_parameters(self):
        """
        Specific calculator parameters returned as list suitable to be
        passed in task_arg_gen.
        """

        time_span, tses = self.hazard_times()

        return [
            self.imt, time_span, tses, self.rc.loss_curve_resolution,
            self.rc.master_seed, self.rc.asset_correlation,
            self.rc.lrem_steps_per_interval, self.rc.asset_life_expectancy,
            self.rc.interest_rate
        ]

    def post_process(self):
        """
        No need to compute the aggregate loss curve in the BCR calculator.
        """

    def create_outputs(self):
        """
        Create BCR Distribution output container, i.e. a
        :class:`openquake.db.models.BCRDistribution` instance and its
        :class:`openquake.db.models.Output` container.

        :returns: A list containing the output container id.
        """
        return [
            models.BCRDistribution.objects.create(
            output=models.Output.objects.create_output(
            self.job, "BCR Distribution", "bcr_distribution")).pk
        ]

    def store_risk_model(self):
        """
        Store both the risk model for the original asset configuration
        and the risk model for the retrofitted one.
        """
        super(EventBasedBCRRiskCalculator, self).store_risk_model()
        general.store_risk_model(self.rc, "vulnerability_retrofitted")
