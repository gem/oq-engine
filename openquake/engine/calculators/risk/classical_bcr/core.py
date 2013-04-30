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

from openquake.risklib import scientific, utils
from openquake.risklib.api import Classical

from openquake.engine.calculators.base import signal_task_complete
from openquake.engine.calculators.risk import base, hazard_getters
from openquake.engine.calculators.risk.classical import core as classical
from openquake.engine.utils import tasks
from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.performance import EnginePerformanceMonitor
from django.db import transaction


@tasks.oqtask
@base.count_progress_risk('r')
def classical_bcr(
        job_id, units, containers, asset_life_expectancy, interest_rate):
    """
    Celery task for the BCR risk calculator based on the classical
    calculator.

    Instantiates risklib calculators, computes BCR and stores the
    results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param list units:
      A list of :class:`..base.CalculationUnit` to be run
    :param dict containers:
      A dictionary mapping :class:`..general.OutputKey` to database ID
      of output containers (in this case only `BCRDistribution`)
    :param float interest_rate
      The interest rate used in the Cost Benefit Analysis
    :param float asset_life_expectancy
      The life expectancy used for every asset
    """

    def profile(name):
        return EnginePerformanceMonitor(
            name, job_id, classical_bcr, tracing=True)

    # Actuall we do the job in other functions, such that it can be
    # unit tested without the celery machinery
    with transaction.commit_on_success(using='reslt_writer'):
        do_classical_bcr(
            units, containers, asset_life_expectancy, interest_rate, profile)
    signal_task_complete(job_id=job_id, num_items=len(units[0].getter.assets))
classical_bcr.ignore_result = False


def do_classical_bcr(
        units, containers, asset_life_expectancy, interest_rate, profile):
    for unit_orig, unit_retro in utils.pairwise(units):
        with profile('getting hazard'):
            assets, hazard_curves, _missings = unit_orig.getter()
            _, hazard_curves_retrofitted, __ = unit_retro.getter()

        with profile('computing bcr'):
            original_loss_curves = unit_orig.calc(hazard_curves)
            retrofitted_loss_curves = unit_retro.calc(
                hazard_curves_retrofitted)

            eal_original = [
                scientific.average_loss(losses, poes)
                for losses, poes in original_loss_curves]

            eal_retrofitted = [
                scientific.average_loss(losses, poes)
                for losses, poes in retrofitted_loss_curves]

            bcr_results = [
                scientific.bcr(
                    eal_original[i], eal_retrofitted[i],
                    interest_rate, asset_life_expectancy,
                    asset.value, asset.retrofitting_cost)
                for i, asset in enumerate(assets)]

        with logs.tracing('writing results'):
            containers.write(
                assets, zip(eal_original, eal_retrofitted, bcr_results),
                output_type="bcr_distribution",
                hazard_output_id=unit_orig.getter.hazard_output_id)


class ClassicalBCRRiskCalculator(classical.ClassicalRiskCalculator):
    """
    Classical BCR risk calculator. Computes BCR distributions for a
    given set of assets.

    :attr dict vulnerability_functions_retrofitted:
        A dictionary mapping each taxonomy to a vulnerability functions for the
        retrofitted losses computation
    """
    core_calc_task = classical_bcr

    def __init__(self, job):
        super(ClassicalBCRRiskCalculator, self).__init__(job)
        self.vulnerability_functions_retrofitted = None
        self.taxonomy_imt_retrofitted = dict()

    def calculation_units(self, assets):
        units = []

        taxonomy = assets[0].taxonomy
        vf_orig = self.vulnerability_functions[taxonomy]
        vf_retro = self.vulnerability_functions_retrofitted[taxonomy]

        for ho in self.rc.hazard_outputs():
            units.extend([
                base.CalculationUnit(
                    Classical(
                        vulnerability_function=vf_orig,
                        steps=self.rc.lrem_steps_per_interval),
                    hazard_getters.HazardCurveGetterPerAsset(
                        ho,
                        assets,
                        self.rc.best_maximum_distance,
                        self.taxonomy_imt[taxonomy])),
                base.CalculationUnit(
                    Classical(
                        vulnerability_function=vf_retro,
                        steps=self.rc.lrem_steps_per_interval),
                    hazard_getters.HazardCurveGetterPerAsset(
                        ho,
                        assets,
                        self.rc.best_maximum_distance,
                        self.taxonomy_imt_retrofitted[taxonomy]))])
        return units

    @property
    def calculator_parameters(self):
        """
        Specific calculator parameters returned as list suitable to be
        passed in task_arg_gen
        """

        return [self.rc.asset_life_expectancy, self.rc.interest_rate]

    def create_outputs(self, hazard_output):
        """
        Create BCR Distribution output container, i.e. a
        :class:`openquake.engine.db.models.BCRDistribution` instance and its
        :class:`openquake.engine.db.models.Output` container.

        :returns: A list containing the output container id
        """
        ret = base.OutputDict()

        ret.set(models.BCRDistribution.objects.create(
                hazard_output=hazard_output,
                output=models.Output.objects.create_output(
                    self.job, "BCR Distribution for hazard %s" % hazard_output,
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
