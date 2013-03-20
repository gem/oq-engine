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

import numpy

from collections import OrderedDict

from openquake.risklib import api, scientific

from django.db import transaction

from openquake.engine.calculators.risk import hazard_getters
from openquake.engine.calculators import base
from openquake.engine.calculators.risk import general
from openquake.engine.utils import tasks
from openquake.engine import logs


@tasks.oqtask
@general.count_progress_risk('r')
def classical(job_id, hazard, vulnerability_function, output_containers,
              lrem_steps_per_interval, conditional_loss_poes,
              hazard_montecarlo_p):
    """
    Celery task for the classical risk calculator.

    Instantiates risklib calculators, computes losses for the given
    assets and stores the results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param dict hazard:
      A dictionary mapping IDs of
      :class:`openquake.engine.db.models.Output` (with output_type set
      to 'hazard_curve') to a tuple where the first element is an instance of
      :class:`..hazard_getters.HazardCurveGetter`, and the second element is
      the corresponding weight.
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

    calculator = api.Classical(
        vulnerability_function, lrem_steps_per_interval)

    for hazard_output_id, hazard_data in hazard.items():
        # the second item of the tuple is the weight of the hazard (at
        # this moment we are not interested in it)
        hazard_getter, _ = hazard_data

        (loss_curve_id, loss_map_ids,
         mean_loss_curve_id, quantile_loss_curve_ids) = (
             output_containers[hazard_output_id])

        with logs.tracing('getting hazard'):
            assets, hazard_curves, missings = hazard_getter()

        with logs.tracing('computing risk over %d assets' % len(assets)):
            asset_outputs[hazard_output_id] = calculator(hazard_curves)

        with logs.tracing('writing results'):
            with transaction.commit_on_success(using='reslt_writer'):
                for i, loss_ratio_curve in enumerate(
                        asset_outputs[hazard_output_id]):

                    asset = assets[i]

                    # Write Loss Curves
                    general.write_loss_curve(
                        loss_curve_id, asset,
                        loss_ratio_curve.ordinates,
                        loss_ratio_curve.abscissae,
                        scientific.average_loss(
                            loss_ratio_curve.abscissae,
                            loss_ratio_curve.ordinates))

                    # Then conditional loss maps
                    for poe in conditional_loss_poes:
                        general.write_loss_map_data(
                            loss_map_ids[poe], asset,
                            scientific.conditional_loss_ratio(
                                loss_ratio_curve, poe))

    if len(hazard) > 1 and (mean_loss_curve_id or quantile_loss_curve_ids):
        weights = [data[1] for _, data in hazard.items()]

        with logs.tracing('writing curve statistics'):
            with transaction.commit_on_success(using='reslt_writer'):
                loss_ratio_curve_matrix = numpy.array(asset_outputs.values())
                for i, asset in enumerate(assets):
                    general.curve_statistics(
                        asset,
                        loss_ratio_curve_matrix[:,i],
                        weights,
                        mean_loss_curve_id,
                        quantile_loss_curve_ids,
                        hazard_montecarlo_p,
                        assume_equal="support")

    base.signal_task_complete(job_id=job_id,
                              num_items=len(assets) + len(missings))

classical.ignore_result = False


class ClassicalRiskCalculator(general.BaseRiskCalculator):
    """
    Classical PSHA risk calculator. Computes loss curves and loss maps
    for a given set of assets.
    """

    #: celery task
    core_calc_task = classical

    hazard_getter = hazard_getters.HazardCurveGetterPerAsset

    def worker_args(self, taxonomy):
        """
        As we do not need a seed in the classical calculator we just
        have the vulnerability function as extra arg to the celery
        task
        """
        return [self.vulnerability_functions[taxonomy]]

    def create_getter(self, output, imt, assets):
        """
        See :method:`..general.BaseRiskCalculator.create_getter`
        """
        if not output.is_hazard_curve():
            raise RuntimeError(
                "The provided hazard output is not an hazard curve")

        hc = output.hazardcurve

        # The hazard curve either could be associated with a logic
        # tree realization, either is a statistics curve (e.g. a mean
        # curve). In that case, we just set up the weight to None
        if hc.lt_realization:
            weight = hc.lt_realization.weight
        else:
            weight = None

        hazard_getter = self.hazard_getter(
            hc.id, imt, assets, self.rc.best_maximum_distance)

        return (hazard_getter, weight)

    def hazard_outputs(self, hazard_calculation):
        """
        :returns: a list of :class:`openquake.engine.db.models.HazardCurve`
        object that stores the hazard curves associated to
        `hazard_calculation` that are associated with a realization
        """

        return hazard_calculation.oqjob_set.filter(status="complete").latest(
            'last_update').output_set.filter(
                output_type='hazard_curve',
                hazardcurve__lt_realization__isnull=False).order_by('id')

    @property
    def calculator_parameters(self):
        """
        Specific calculator parameters returned as list suitable to be
        passed in task_arg_gen
        """

        return [self.rc.lrem_steps_per_interval,
                self.rc.conditional_loss_poes or [],
                self.hc.number_of_logic_tree_samples == 0]
