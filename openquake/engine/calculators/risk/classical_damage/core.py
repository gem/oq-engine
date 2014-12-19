# Copyright (c) 2014, GEM Foundation.
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
Core functionality for the classical damage risk calculator.
"""

from openquake.risklib import workflows

from openquake.engine.calculators import post_processing
from openquake.engine.calculators.risk import (
    base, hazard_getters, validation, writers)
from openquake.engine.utils import calculators


def classical_damage(workflow, getter, outputdict, params, monitor):
    """
    Celery task for the classical risk calculator.

    :param workflow:
      A :class:`openquake.risklib.workflows.RiskModel` instance
    :param getter:
      A HazardGetter instance
    :param outputdict:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (e.g. a LossCurve)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    :param monitor:
      A monitor instance
    For each calculation unit we compute loss curves, loss maps and
    loss fractions. Then if the number of units are bigger than 1, we
    compute mean and quantile artifacts.
    """
    for loss_type in workflow.loss_types:
        with monitor.copy('computing risk'):
            outputs = workflow.compute_all_outputs(getter, loss_type)
            stats = workflow.statistics(
                outputs, params.quantile_loss_curves, post_processing)
        with monitor.copy('saving risk'):
            for out in outputs:
                save_individual_outputs(
                    outputdict.with_args(
                        loss_type=loss_type, hazard_output_id=out.hid),
                    out.output, params)
            if stats is not None:
                save_statistical_output(
                    outputdict.with_args(
                        loss_type=loss_type, hazard_output_id=None),
                    stats, params)


def save_individual_outputs(outputdict, outs, params):
    """
    Save loss curves, loss maps and loss fractions associated with a
    calculation unit

    :param outputdict:
        a :class:`openquake.engine.calculators.risk.writers.OutputDict`
        instance holding the reference to the output container objects
    :param outs:
        a :class:`openquake.risklib.workflows.Classical.Output`
        holding the output data for a calculation unit
    :param params:
        a :class:`openquake.engine.calculators.risk.base.CalcParams`
        holding the parameters for this calculation
    """
    pass


def save_statistical_output(outputdict, stats, params):
    """
    Save statistical outputs (mean and quantile loss curves, mean and
    quantile loss maps, mean and quantile loss fractions) for the
    calculation.

    :param outputdict:
        a :class:`openquake.engine.calculators.risk.writers.OutputDict`
        instance holding the reference to the output container objects
    :param outs:
        a :class:`openquake.risklib.workflows.Classical.StatisticalOutput`
        holding the statistical output data
    :param params:
        a :class:`openquake.engine.calculators.risk.base.CalcParams`
        holding the parameters for this calculation
    """
    pass


@calculators.add('classical_damage')
class ClassicalDamageCalculator(base.RiskCalculator):
    """
    Classical PSHA risk calculator. Computes loss curves and loss maps
    for a given set of assets.
    """

    core = staticmethod(classical_damage)

    validators = base.RiskCalculator.validators + [
        validation.ExposureHasInsuranceBounds]

    output_builders = [writers.LossCurveMapBuilder,
                       writers.ConditionalLossFractionBuilder]

    getter_class = hazard_getters.HazardCurveGetter
