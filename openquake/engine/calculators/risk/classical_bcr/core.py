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

from openquake.risklib import api

from openquake.engine.calculators import base
from openquake.engine.calculators.risk import general
from openquake.engine.calculators.risk.classical import core as classical
from openquake.engine.utils import stats
from openquake.engine.utils import tasks
from openquake.engine import logs
from openquake.engine.db import models
from django.db import transaction


@tasks.oqtask
@stats.count_progress('r')
def classical_bcr(job_id, assets, hazard_getter_name, hazard,
                  vulnerability_function, vulnerability_function_retrofitted,
                  output_containers, lrem_steps_per_interval,
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
    :param str hazard_getter_name: class name of a class defined in the
      :mod:`openquake.engine.calculators.risk.hazard_getters`
      to be instantiated to get the hazard curves
    :param dict hazard:
      A dictionary mapping hazard Output ID to HazardCurve ID
    :param output_containers: A dictionary mapping hazard Output ID to
      a tuple with only the ID of the
      :class:`openquake.engine.db.models.BCRDistribution` output container
      used to store the computed bcr distribution
    :param int lrem_steps_per_interval
      Steps per interval used to compute the Loss Ratio Exceedance matrix
    :param float interest_rate
      The interest rate used in the Cost Benefit Analysis
    :param float asset_life_expectancy
      The life expectancy used for every asset
    """

    calc_original = api.Classical(
        vulnerability_function, lrem_steps_per_interval)
    calc_retrofitted = api.Classical(
        vulnerability_function_retrofitted, lrem_steps_per_interval)

    for hazard_output_id, hazard_data in hazard.items():
        hazard_id, _ = hazard_data
        (bcr_distribution_id,) = output_containers[hazard_output_id]

        hazard_getter = general.hazard_getter(hazard_getter_name, hazard_id)

        calculator = api.BCR(
            calc_original,
            calc_retrofitted,
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
        :class:`openquake.engine.db.models.BCRDistribution` instance and its
        :class:`openquake.engine.db.models.Output` container.

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
