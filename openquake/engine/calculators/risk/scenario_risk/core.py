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
Core functionality for the scenario risk calculator.
"""
import itertools
import numpy

from openquake.baselib.general import AccumDict
from openquake.engine.calculators.risk import (
    base, hazard_getters, validation, writers)
from openquake.engine.db import models
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.calculators import calculators


def workflow_argdict(loss_type, assets, gmfs, epsilons):
    """
    :param loss_type:
        loss type string
    :param assets:
        list of N assets
    :param gmfs:
        list of N ground motion arrays
    :param epsilons:
        list of N epsilon arrays
    :returns:
        a dictionary with the loss_type and three lists with N - M elements,
        where M is the number of assets without value (usually 0).
    """
    dic = AccumDict(assets=[], ground_motion_values=[], epsilons=[],
                    loss_type=loss_type)
    for asset, gmvs, epsilon in zip(assets, gmfs, epsilons):
        if asset.value(loss_type) is not None:
            dic += {'assets': [asset],
                    'ground_motion_values': [gmvs],
                    'epsilons': [epsilon]}
    return dic


def scenario(workflow, getter, outputdict, params, monitor):
    """
    Celery task for the scenario risk calculator.

    :param list workflow:
      A :class:`openquake.risklib.workflows.Workflow` instance
    :param getter:
      A HazardGetter instance
    :param outputdict:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (in this case only `LossMap`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    :param monitor:
      A monitor instance
    """
    assets = getter.assets
    gmfs = getter.get_data()
    epsilons = getter.get_epsilons()
    agg, ins = {}, {}
    for loss_type in workflow.loss_types:
        with monitor('computing risk'):
            argdict = workflow_argdict(loss_type, assets, gmfs, epsilons)
            if not argdict['assets']:  # no costs
                continue
            outputdict = outputdict.with_args(
                loss_type=loss_type, output_type="loss_map")
            out = workflow(**argdict)
            agg[loss_type] = out.aggregate_losses
        ins[loss_type] = out.insured_losses

        with monitor('saving risk'):
            outputdict.write(
                assets,
                out.loss_matrix.mean(axis=1),
                out.loss_matrix.std(ddof=1, axis=1),
                hazard_output_id=getter.hid,
                insured=False)

            if out.insured_loss_matrix is not None:
                outputdict.write(
                    assets,
                    out.insured_loss_matrix.mean(axis=1),
                    out.insured_loss_matrix.std(ddof=1, axis=1),
                    itertools.cycle([True]),
                    hazard_output_id=getter.hid,
                    insured=True)

    return agg, ins


@calculators.add('scenario_risk')
class ScenarioRiskCalculator(base.RiskCalculator):
    """
    Scenario Risk Calculator. Computes a Loss Map,
    for a given set of assets.
    """

    core = staticmethod(scenario)

    validators = base.RiskCalculator.validators + [
        validation.ExposureHasInsuranceBounds,
        validation.ExposureHasTimeEvent]

    output_builders = [writers.LossMapBuilder]

    getter_class = hazard_getters.GroundMotionGetter

    def __init__(self, job):
        super(ScenarioRiskCalculator, self).__init__(job)
        self.acc = ({}, {})  # aggregate_losses and insured_losses accumulators

    @EnginePerformanceMonitor.monitor
    def agg_result(self, acc, task_result):
        aggregate_losses_acc, insured_losses_acc = acc[0].copy(), acc[1].copy()
        aggregate_losses_dict, insured_losses_dict = task_result

        for loss_type in self.loss_types:
            aggregate_losses = aggregate_losses_dict.get(loss_type)

            if aggregate_losses is not None:
                if aggregate_losses_acc.get(loss_type) is None:
                    aggregate_losses_acc[loss_type] = (
                        numpy.zeros(aggregate_losses.shape))
                aggregate_losses_acc[loss_type] += aggregate_losses

        if self.oqparam.insured_losses:
            for loss_type in self.loss_types:
                insured_losses = insured_losses_dict.get(
                    loss_type)
                if insured_losses is not None:
                    if insured_losses_acc.get(loss_type) is None:
                        insured_losses_acc[loss_type] = numpy.zeros(
                            insured_losses.shape)
                    insured_losses_acc[loss_type] += insured_losses
        return aggregate_losses_acc, insured_losses_acc

    def post_process(self):
        aggregate_losses_acc, insured_losses_acc = self.acc
        for loss_type, aggregate_losses in aggregate_losses_acc.items():
            models.AggregateLoss.objects.create(
                output=models.Output.objects.create_output(
                    self.job,
                    "aggregate loss. type=%s" % loss_type,
                    "aggregate_loss"),
                loss_type=loss_type,
                mean=numpy.mean(aggregate_losses),
                std_dev=numpy.std(aggregate_losses, ddof=1))

            if self.oqparam.insured_losses:
                insured_losses = insured_losses_acc[loss_type]
                models.AggregateLoss.objects.create(
                    output=models.Output.objects.create_output(
                        self.job,
                        "insured aggregate loss. type=%s" % loss_type,
                        "aggregate_loss"),
                    insured=True,
                    loss_type=loss_type,
                    mean=numpy.mean(insured_losses),
                    std_dev=numpy.std(insured_losses, ddof=1))
