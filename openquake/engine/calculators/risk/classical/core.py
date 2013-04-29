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

from openquake.engine.db import models
from openquake.engine.calculators.base import signal_task_complete
from openquake.engine.calculators.risk import base, writers, hazard_getters
from openquake.engine.utils import tasks
from openquake.engine import logs


@tasks.oqtask
@base.count_progress_risk('r')
def classical(job_id, hazard, vulnerability_function, imt,
              output_containers, statistical_output_containers,
              lrem_steps_per_interval, conditional_loss_poes,
              poes_disagg, hazard_montecarlo_p):
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
    :param str imt: the imt in long string form, i.e. SA(0.1)
    :param dict output_containers: A dictionary mapping hazard
      Output ID to a tuple (a, b) where a is the ID of the
      :class:`openquake.engine.db.models.LossCurve` output container used to
      store individual loss curves and b is a dictionary that maps poe to ID
      of the :class:`openquake.engine.db.models.LossMap` used to store
      the individual loss maps
    :param dict statistical_output_containers: A tuple with four elements:
      1) the ID of a mean loss curve (
      :class:`openquake.engine.db.models.LossCurve`)
      2) a dict mapping quantile levels to instances of
      :class:`openquake.engine.db.models.LossCurve`
      3) a dict mapping poes to instances of
      :class:`openquake.engine.db.models.LossMap`
      4) a dict mapping quantile levels to dictionary mapping poes to instances
      of :class:`openquake.engine.db.models.LossMap`
    :param int lrem_steps_per_interval:
      Steps per interval used to compute the Loss Ratio Exceedance matrix
    :param conditional_loss_poes:
      The poes taken into account to compute the loss maps
    :param poes_disagg:
      The poes taken into account to compute the loss maps for disaggregation
    :param bool hazard_montecarlo_p:
     (meaningful only if curve statistics are computed). Wheter or not
     the hazard calculation is montecarlo based
    """

    asset_outputs = OrderedDict()

    calculator = api.Classical(vulnerability_function, lrem_steps_per_interval)

    for hazard_output_id, hazard_data in hazard.items():
        # the second item of the tuple is the weight of the hazard (at
        # this moment we are not interested in it)
        hazard_getter, _ = hazard_data

        loss_curve_id, loss_map_ids, loss_fraction_ids = (
            output_containers[hazard_output_id])

        with logs.tracing('getting hazard'):
            assets, hazard_curves, missings = hazard_getter(imt)

        with logs.tracing('computing risk over %d assets' % len(assets)):
            asset_outputs[hazard_output_id] = calculator(hazard_curves)

        with logs.tracing('writing results'):
            with transaction.commit_on_success(using='reslt_writer'):
                for i, (losses, poes) in enumerate(
                        asset_outputs[hazard_output_id]):

                    asset = assets[i]

                    # Write Loss Curves
                    writers.loss_curve(
                        loss_curve_id, asset,
                        poes, losses,
                        scientific.average_loss(losses, poes))

                    # Then conditional loss maps
                    for poe in conditional_loss_poes:
                        writers.loss_map_data(
                            loss_map_ids[poe], asset,
                            scientific.conditional_loss_ratio(
                                losses, poes, poe))

                    # Then loss fractions
                    for poe in poes_disagg:
                        writers.loss_fraction_data(
                            loss_fraction_ids[poe],
                            location=asset.site,
                            value=asset.taxonomy,
                            absolute_loss=scientific.conditional_loss_ratio(
                                losses, poes, poe) * asset.value)

    if statistical_output_containers:
        weights = [data[1] for _, data in hazard.items()]

        (mean_loss_curve_id, quantile_loss_curve_ids,
         mean_loss_map_ids, quantile_loss_map_ids,
         mean_loss_fraction_ids, quantile_loss_fraction_ids) = (
             statistical_output_containers)

        with logs.tracing('writing statistics'):
            with transaction.commit_on_success(using='reslt_writer'):
                writers.curve_statistics(
                    mean_loss_curve_id, quantile_loss_curve_ids,
                    mean_loss_map_ids, quantile_loss_map_ids,
                    mean_loss_fraction_ids, quantile_loss_fraction_ids,
                    weights, assets, numpy.array(asset_outputs.values()),
                    hazard_montecarlo_p, conditional_loss_poes,
                    poes_disagg, "support")

    signal_task_complete(job_id=job_id, num_items=len(assets) + len(missings))

classical.ignore_result = False


class ClassicalRiskCalculator(base.RiskCalculator):
    """
    Classical PSHA risk calculator. Computes loss curves and loss maps
    for a given set of assets.
    """

    #: celery task
    core_calc_task = classical

    hazard_getter = hazard_getters.HazardCurveGetterPerAsset

    def taxonomy_args(self, taxonomy):
        """
        As we do not need a seed in the classical calculator we just
        have the vulnerability function as extra arg to the celery
        task
        """
        return [self.vulnerability_functions[taxonomy],
                self.taxonomy_imt[taxonomy]]

    def create_getter(self, output, assets):
        """
        See :meth:`..base.RiskCalculator.create_getter`
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
            hc.id, assets, self.rc.best_maximum_distance)

        return (hazard_getter, weight)

    def create_outputs(self, hazard_output):
        """
        Create outputs container objects.

        In classical risk, we finalize the output containers by adding
        loss_fraction_ids, a dict that maps poes (coming from
        poe_disagg) to IDs of newly created instances
        :class:`openquake.engine.db.models.LossFraction`
        """
        loss_fraction_ids = dict(
            (poe, models.LossFraction.objects.create(
                hazard_output_id=hazard_output.id,
                variable="taxonomy",
                output=models.Output.objects.create_output(
                    self.job,
                    "Loss Fractions with poe %s for hazard %s" % (
                        poe, hazard_output.id),
                    "loss_fraction"),
                poe=poe).pk)
            for poe in self.rc.poes_disagg or [])

        # the base class provides individual loss curve/map ids
        containers = super(ClassicalRiskCalculator, self).create_outputs(
            hazard_output)

        return containers + [loss_fraction_ids]

    def create_statistical_outputs(self):
        """
        Create statistics output containers.

        In classical risk we need also loss fraction ids for aggregate
        results
        """
        mean_loss_fraction_ids = dict(
            (poe,
             models.LossFraction.objects.create(
                 variable="taxonomy",
                 output=models.Output.objects.create_output(
                     job=self.job,
                     display_name="Mean Loss Fractions poe=%.4f" % poe,
                     output_type="loss_fraction"),
                 statistics="mean").id)
            for poe in self.rc.poes_disagg or [])

        quantile_loss_fraction_ids = dict(
            (quantile,
             dict(
                 (poe, models.LossFraction.objects.create(
                     variable="taxonomy",
                     output=models.Output.objects.create_output(
                         job=self.job,
                         display_name="Quantile Loss Fractions "
                                      "poe=%.4f q=%.4f" % (poe, quantile),
                         output_type="loss_fraction"),
                     statistics="quantile",
                     quantile=quantile).id)
                 for poe in self.rc.poes_disagg or []))
            for quantile in self.rc.quantile_loss_curves or [])

        containers = super(
            ClassicalRiskCalculator, self).create_statistical_outputs()

        return (containers +
                [mean_loss_fraction_ids, quantile_loss_fraction_ids])

    def hazard_outputs(self, hazard_calculation):
        """
        :returns:
            A list of :class:`openquake.engine.db.models.HazardCurve` object
            that stores the hazard curves associated to `hazard_calculation`
            that are associated with a realization.
        """

        return hazard_calculation.oqjob_set.filter(status="complete").latest(
            'last_update').output_set.filter(
                output_type='hazard_curve_multi',
                hazardcurve__lt_realization__isnull=False).order_by('id')

    @property
    def calculator_parameters(self):
        """
        Specific calculator parameters returned as list suitable to be
        passed in task_arg_gen
        """

        return [self.rc.lrem_steps_per_interval,
                self.rc.conditional_loss_poes or [],
                self.rc.poes_disagg or [],
                self.hc.number_of_logic_tree_samples == 0]
