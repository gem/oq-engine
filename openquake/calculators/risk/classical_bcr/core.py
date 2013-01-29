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
Core functionality for the classical PSHA risk calculator.
"""

from risklib import api

from openquake.calculators import base
from openquake.calculators.risk import general
from openquake.calculators.risk.classical import core as classical
from openquake.utils import stats
from openquake.utils import tasks
from openquake import logs
from openquake.db import models
from django.db import transaction


@tasks.oqtask
@stats.count_progress('r')
def classical_bcr(job_id, assets, hazard_getter, hazard_id,
                  vulnerability_function, vulnerability_function_retrofitted,
                  bcr_distribution_id, lrem_steps_per_interval,
                  asset_life_expectancy, interest_rate):
    """
    Celery task for the BCR risk calculator based on the classical
    calculator.

    Instantiates risklib calculators, computes BCR and stores the
    results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param assets:
      list of Assets to take into account
    :param hazard_getter:
      Strategy used to get the hazard curves
    :param int hazard_id
      ID of the Hazard Output the risk calculation is based on
    :param bcr_distribution_id
      ID of the :class:`openquake.db.models.BCRDistribution` output
      container used to store the computed bcr distribution
    :param int lrem_steps_per_interval
      Steps per interval used to compute the Loss Ratio Exceedance matrix
    :param float interest_rate
      The interest rate used in the Cost Benefit Analysis
    :param float asset_life_expectancy
      The life expectancy used for every asset
    """
    hazard_getter = general.hazard_getter(hazard_getter, hazard_id)

    calculator = api.BCR(
        api.Classical(vulnerability_function, lrem_steps_per_interval),
        api.Classical(vulnerability_function_retrofitted,
                      lrem_steps_per_interval),
        interest_rate,
        asset_life_expectancy)

    with logs.tracing('getting hazard'):
        hazard_curves = [hazard_getter(asset.site) for asset in assets]

    with logs.tracing('computing risk over %d assets' % len(assets)):
        asset_outputs = calculator(assets, hazard_curves)

    with logs.tracing('writing results'):
        with transaction.commit_on_success(using='reslt_writer'):
            for i, asset_output in enumerate(asset_outputs):
                general.write_bcr_distribution(
                    bcr_distribution_id, assets[i], asset_output)
    base.signal_task_complete(job_id=job_id, num_items=len(assets))
classical_bcr.ignore_result = False


class ClassicalBCRRiskCalculator(classical.ClassicalRiskCalculator):
    """
    Classical BCR risk calculator. Computes BCR distributions for a
    given set of assets.

    :attribute dict vulnerability_functions_retrofitted:
    A dictionary mapping each taxonomy to a vulnerability functions
    for the retrofitted losses computation
    """
    core_calc_task = classical_bcr
    hazard_getter = 'HazardCurveGetterPerAsset'

    def __init__(self, job):
        super(ClassicalBCRRiskCalculator, self).__init__(job)
        self.vulnerability_functions_retrofitted = None

    def worker_args(self, taxonomy):
        return (super(ClassicalBCRRiskCalculator, self).worker_args(taxonomy) +
                [self.vulnerability_functions_retrofitted[taxonomy]])

    @property
    def calculator_parameters(self):
        """
        Specific calculator parameters returned as list suitable to be
        passed in task_arg_gen
        """

        return [self.rc.lrem_steps_per_interval,
                self.rc.asset_life_expectancy, self.rc.interest_rate]

    def create_outputs(self, hazard_output):
        """
        Create BCR Distribution output container, i.e. a
        :class:`openquake.db.models.BCRDistribution` instance and its
        :class:`openquake.db.models.Output` container.

        :returns: A list containing the output container id
        """
        return [
            models.BCRDistribution.objects.create(
                hazard_output=hazard_output,
                output=models.Output.objects.create_output(
                    self.job, "BCR Distribution for hazard %s" % hazard_output,
                    "bcr_distribution")).pk]

    def set_risk_models(self):
        """
        Store both the risk model for the original asset configuration
        and the risk model for the retrofitted one.
        """
        self.vulnerability_functions = self.parse_vulnerability_model()
        self.vulnerability_functions_retrofitted = (
            self.parse_vulnerability_model(True))
