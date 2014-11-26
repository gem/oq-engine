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
from openquake.risklib import workflows

from openquake.engine.calculators.risk import writers, validation
from openquake.engine.calculators.risk.event_based_risk \
    import core as event_based
from openquake.engine.calculators import calculators


def event_based_bcr(workflow, getter, outputdict, params, monitor):
    """
    Celery task for the BCR risk calculator based on the event based
    calculator.

    Instantiates risklib calculators, computes bcr
    and stores results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param workflow:
      A :class:`openquake.risklib.workflows.Workflow` instance
    :param getter:
      A HazardGetter instance
    :param outputdict:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (in this case only `BCRDistribution`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    :param monitor:
      A monitor instance
    """
    for loss_type in workflow.loss_types:
        with monitor('computing risk'):
            outputs = workflow.compute_all_outputs(getter, loss_type)
        outputdict = outputdict.with_args(loss_type=loss_type)
        with monitor('saving risk'):
            for out in outputs:
                outputdict.write(
                    workflow.assets,
                    out.output,
                    output_type="bcr_distribution",
                    hazard_output_id=out.hid)


@calculators.add('event_based_bcr')
class EventBasedBCRRiskCalculator(event_based.EventBasedRiskCalculator):
    """
    Event based BCR risk calculator. Computes BCR distributions for a
    given set of assets.
    """
    core = staticmethod(event_based_bcr)

    validators = event_based.EventBasedRiskCalculator.validators + [
        validation.ExposureHasRetrofittedCosts]

    output_builders = [writers.BCRMapBuilder]

    bcr = True

    def get_workflow(self, vf_orig, vf_retro):
        """
        :param vf_orig:
            original vulnerability function
        :param vf_orig:
            retrofitted vulnerability functions
        :returns:
            an instance of
            :class:`openquake.risklib.workflows.ProbabilisticEventBasedBCR`
        """
        time_span, tses = self.hazard_times()
        return workflows.ProbabilisticEventBasedBCR(
            vf_orig, vf_retro,
            time_span, tses, self.rc.loss_curve_resolution,
            self.rc.interest_rate,
            self.rc.asset_life_expectancy)

    def post_process(self):
        """
        No need to compute the aggregate loss curve in the BCR calculator.
        """

    def agg_result(self, acc, event_loss_tables):
        """
        No need to update event loss tables in the BCR calculator
        """
        return acc
