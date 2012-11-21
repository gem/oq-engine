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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Core functionality for the classical PSHA risk calculator.
"""

from risklib import api


from openquake.calculators.risk import general
from openquake.calculators.risk.classical import core as classical
from openquake.utils import stats
from openquake.utils import tasks
from openquake import logs
from openquake.db import models
from django.db import transaction


@tasks.oqtask
@general.with_assets
@stats.count_progress('r')
def classical_bcr(job_id, assets, hazard_getter, hazard_id,
                  bcr_distribution_id,
                  lrem_steps_per_interval,
                  asset_life_expectancy,
                  interest_rate):
    """
    Celery task for the BCR risk calculator based on the classical
    calculator.

    Gets the vulnerability models, instantiates risklib calculators
    and stores results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param assets:
      list of Assets to take into account
    :param hazard_getter:
      Strategy used to get the hazard curves
    :param int hazard_id
      ID of the Hazard Output the risk calculation is based on
    :param bcr_distribution_id
      ID of the `openquake.db.models.BCRDistribution` output container used
      to store the computed bcr distribution
    :param int lrem_steps_per_interval
      Steps per interval used to compute the Loss Ratio Exceedance matrix
    :param float interest_rate
      The interest rate used in the Cost Benefit Analysis
    :param float asset_life_expectancy
      The life expectancy used for every asset
    """
    model = general.fetch_vulnerability_model(job_id)
    model_retrofitted = general.fetch_vulnerability_model(
        job_id, "vulnerability_retrofitted")
    hazard_getter = general.hazard_getter(hazard_getter, hazard_id)

    calculator = api.bcr(
        api.classical(model, lrem_steps_per_interval),
        api.classical(model_retrofitted, lrem_steps_per_interval),
        interest_rate,
        asset_life_expectancy)

    with transaction.commit_on_success(using='reslt_writer'):
        logs.LOG.debug(
            'launching compute_on_assets over %d assets' % len(assets))
        for asset_output in api.compute_on_assets(
            assets, hazard_getter, calculator):
            general.write_bcr_distribution(bcr_distribution_id, asset_output)
classical_bcr.ignore_result = False


class ClassicalBCRRiskCalculator(classical.ClassicalRiskCalculator):
    """
    Classical BCR risk calculator. Computes BCR distributions for a
    given set of assets.
    """
    celery_task = classical_bcr

    @property
    def calculation_parameters(self):
        """
        Calculation specific parameters
        """

        rc = self.job.risk_calculation

        return {
            'lrem_steps_per_interval': rc.lrem_steps_per_interval,
            'interest_rate': rc.interest_rate,
            'asset_life_expectancy': rc.asset_life_expectancy
            }

    def create_outputs(self):
        """
        Create BCR Distribution output container
        """
        return dict(
            bcr_distribution_id=models.BCRDistribution.objects.create(
                output=models.Output.objects.create_output(
                    self.job, "BCR Distribution", "bcr_distribution")).pk)

    def store_risk_model(self):
        super(ClassicalBCRRiskCalculator, self).store_risk_model()

        general.store_risk_model(self.job.risk_calculation,
                                 "vulnerability_retrofitted")
