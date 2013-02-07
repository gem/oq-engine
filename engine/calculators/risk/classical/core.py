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

from collections import OrderedDict

from django.db import transaction

from openquake.engine.db import models
from openquake.engine.calculators import base
from openquake.engine.calculators.risk import general
from openquake.engine.utils import tasks, stats
from openquake.engine import logs
from openquake.risklib import api


@tasks.oqtask
@stats.count_progress('r')
def classical(job_id, assets, hazard_getter_name, hazard,
              vulnerability_function,
              output_containers,
              lrem_steps_per_interval, conditional_loss_poes,
              hazard_montecarlo_p):
    """
    Celery task for the classical risk calculator.

    Instantiates risklib calculators, computes losses for the given
    assets and stores the results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param assets:
      iterator over :class:`openquake.engine.db.models.ExposureData` to take
      into account
    :param str hazard_getter_name: class name of a class defined in the
      :mod:`openquake.engine.calculators.risk.hazard_getters` to be
      instantiated to get the hazard curves
    :param dict hazard:
      A dictionary mapping hazard Output ID to HazardCurve ID
    :param dict output_containers: A dictionary mapping hazard
      Output ID to a tuple (a, b) where a is the ID of the
      :class:`openquake.engine.db.models.LossCurve` output container used to
      store the computed loss curves and b is a dictionary that maps poe to ID
      of the :class:`openquake.engine.db.models.LossMap` used to store
      the loss maps
    :param int lrem_steps_per_interval:
      Steps per interval used to compute the Loss Ratio Exceedance matrix
    :param conditional_loss_poes:
      The poes taken into account to compute the loss maps
    :param bool hazard_montecarlo_p:
     (meaningful only if curve statistics are computed). Wheter or not
     the hazard calculation is montecarlo based
    """

    asset_outputs = OrderedDict()

    for hazard_output_id, hazard_data in hazard.items():
        hazard_id, _ = hazard_data
        (loss_curve_id, loss_map_ids,
         mean_loss_curve_id, quantile_loss_curve_ids) = (
             output_containers[hazard_output_id])

        hazard_getter = general.hazard_getter(hazard_getter_name, hazard_id)

        calculator = api.Classical(
            vulnerability_function, lrem_steps_per_interval)

        # if we need to compute the loss maps, we add the proper risk
        # aggregator
        if conditional_loss_poes:
            calculator = api.ConditionalLosses(
                conditional_loss_poes, calculator)

        with logs.tracing('getting hazard'):
            hazard_curves = [hazard_getter(asset.site) for asset in assets]

        with logs.tracing('computing risk over %d assets' % len(assets)):
            asset_outputs[hazard_output_id] = calculator(assets, hazard_curves)

        with logs.tracing('writing results'):
            with transaction.commit_on_success(using='reslt_writer'):
                for i, asset_output in enumerate(
                        asset_outputs[hazard_output_id]):
                    general.write_loss_curve(
                        loss_curve_id, assets[i], asset_output)

                    if asset_output.conditional_losses:
                        general.write_loss_map(
                            loss_map_ids, assets[i], asset_output)

    if len(hazard) > 1 and (mean_loss_curve_id or quantile_loss_curve_ids):
        weights = [data[1] for _, data in hazard.items()]

        with logs.tracing('writing curve statistics'):
            with transaction.commit_on_success(using='reslt_writer'):
                for i, asset in enumerate(assets):
                    general.curve_statistics(
                        asset,
                        [asset_output[i].loss_ratio_curve
                         for asset_output in asset_outputs.values()],
                        weights,
                        mean_loss_curve_id,
                        quantile_loss_curve_ids,
                        hazard_montecarlo_p,
                        assume_equal="support")

    base.signal_task_complete(job_id=job_id, num_items=len(assets))

classical.ignore_result = False


class ClassicalRiskCalculator(general.BaseRiskCalculator):
    """
    Classical PSHA risk calculator. Computes loss curves and loss maps
    for a given set of assets.
    """

    #: celery task
    core_calc_task = classical

    hazard_getter = 'HazardCurveGetterPerAsset'

    def worker_args(self, taxonomy):
        """
        As we do not need a seed in the classical calculator we just
        have the vulnerability function as extra arg to the celery
        task
        """
        return [self.vulnerability_functions[taxonomy]]

    def hazard_output(self, output):
        """
        :returns: a tuple with the ID and the weight associated with the
        :class:`openquake.engine.db.models.HazardCurve` object that stores
        the hazard curves associated to `output`
        """
        if not output.is_hazard_curve():
            raise RuntimeError(
                "The provided hazard output is not an hazard curve")

        hc = output.hazardcurve
        if hc.lt_realization:
            weight = hc.lt_realization.weight
        else:
            weight = None
        return (hc.id, weight)

    def hazard_outputs(self, hazard_calculation):
        """
        :returns: a list of :class:`openquake.engine.db.models.HazardCurve`
        object that stores the hazard curves associated to
        `hazard_calculation` that are associated with a realization
        """

        imt, sa_period, sa_damping = models.parse_imt(self.imt)
        return hazard_calculation.oqjob_set.filter(status="complete").latest(
            'last_update').output_set.filter(
                output_type='hazard_curve',
                hazardcurve__imt=imt,
                hazardcurve__sa_period=sa_period,
                hazardcurve__sa_damping=sa_damping,
                hazardcurve__lt_realization__isnull=False).order_by('id')

    @property
    def calculator_parameters(self):
        """
        Specific calculator parameters returned as list suitable to be
        passed in task_arg_gen
        """

        return [self.rc.lrem_steps_per_interval,
                self.rc.conditional_loss_poes,
                self.hc.number_of_logic_tree_samples == 0]
