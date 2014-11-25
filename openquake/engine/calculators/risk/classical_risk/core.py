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
Core functionality for the classical PSHA risk calculator.
"""

import itertools
from openquake.risklib import workflows

from openquake.engine.calculators import post_processing
from openquake.engine.calculators.risk import (
    base, hazard_getters, validation, writers)
from openquake.engine.calculators import calculators


def classical(workflow, getter, outputdict, params, monitor):
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
        with monitor('computing risk'):
            outputs = workflow.compute_all_outputs(getter, loss_type)
            stats = workflow.statistics(
                outputs, params.quantile_loss_curves, post_processing)
        with monitor('saving risk'):
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
    outputdict.write(
        outs.assets,
        (outs.loss_curves, outs.average_losses),
        output_type="loss_curve")

    if outs.insured_curves is not None:
        outputdict.write(
            outs.assets,
            (outs.insured_curves, outs.average_insured_losses),
            insured=True,
            output_type="loss_curve")

    outputdict.write_all(
        "poe", params.conditional_loss_poes,
        outs.loss_maps,
        outs.assets,
        output_type="loss_map")

    taxonomies = [a.taxonomy for a in outs.assets]
    outputdict.write_all(
        "poe", params.poes_disagg,
        outs.loss_fractions, outs.assets, taxonomies,
        output_type="loss_fraction", variable="taxonomy")


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

    # mean curves, maps and fractions
    outputdict.write(
        stats.assets, (stats.mean_curves, stats.mean_average_losses),
        output_type="loss_curve", statistics="mean")

    outputdict.write_all("poe", params.conditional_loss_poes,
                         stats.mean_maps, stats.assets,
                         output_type="loss_map",
                         statistics="mean")

    outputdict.write_all("poe", params.poes_disagg,
                         stats.mean_fractions,
                         stats.assets,
                         [a.taxonomy for a in stats.assets],
                         output_type="loss_fraction", statistics="mean",
                         variable="taxonomy")

    # quantile curves, maps and fractions
    outputdict.write_all(
        "quantile", params.quantile_loss_curves,
        [(c, a) for c, a in itertools.izip(
            stats.quantile_curves, stats.quantile_average_losses)],
        stats.assets, output_type="loss_curve", statistics="quantile")

    for quantile, maps in zip(
            params.quantile_loss_curves, stats.quantile_maps):
        outputdict.write_all("poe", params.conditional_loss_poes, maps,
                             stats.assets, output_type="loss_map",
                             statistics="quantile", quantile=quantile)

    for quantile, fractions in zip(
            params.quantile_loss_curves, stats.quantile_fractions):
        outputdict.write_all("poe", params.poes_disagg, fractions,
                             stats.assets, [a.taxonomy for a in stats.assets],
                             output_type="loss_fraction",
                             statistics="quantile", quantile=quantile,
                             variable="taxonomy")

    # mean and quantile insured curves
    if stats.mean_insured_curves is not None:
        outputdict.write(
            stats.assets, (stats.mean_insured_curves,
                           stats.mean_average_insured_losses),
            output_type="loss_curve", statistics="mean", insured=True)

        outputdict.write_all(
            "quantile", params.quantile_loss_curves,
            [(c, a) for c, a in itertools.izip(
                stats.quantile_insured_curves,
                stats.quantile_average_insured_losses)],
            stats.assets,
            output_type="loss_curve", statistics="quantile", insured=True)


@calculators.add('classical_risk')
class ClassicalRiskCalculator(base.RiskCalculator):
    """
    Classical PSHA risk calculator. Computes loss curves and loss maps
    for a given set of assets.
    """

    core = staticmethod(classical)

    validators = base.RiskCalculator.validators + [
        validation.RequireClassicalHazard,
        validation.ExposureHasInsuranceBounds]

    output_builders = [writers.LossCurveMapBuilder,
                       writers.ConditionalLossFractionBuilder]

    getter_class = hazard_getters.HazardCurveGetter

    def get_workflow(self, vulnerability_functions):
        """
        :param vulnerability_functions:
            a dictionary of vulnerability functions
        :returns:
            an instance of
            :class:`openquake.risklib.workflows.Classical`
        """
        return workflows.Classical(
            vulnerability_functions,
            self.rc.lrem_steps_per_interval,
            self.rc.conditional_loss_poes,
            self.rc.poes_disagg,
            self.rc.insured_losses)
