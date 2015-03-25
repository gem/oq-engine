# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.

import inspect
import functools
import collections
import numpy
from scipy import interpolate

from openquake.baselib.general import CallableDict
from openquake.risklib import utils, scientific

Output = collections.namedtuple('Output', 'hid weight loss_type output')

registry = CallableDict()


class Asset(object):
    """
    Describe an Asset as a collection of several values. A value can
    represent a replacement cost (e.g. structural cost, business
    interruption cost) or another quantity that can be considered for
    a risk analysis (e.g. occupants).

    Optionally, a Asset instance can hold also a collection of
    deductible values and insured limits considered for insured losses
    calculations.
    """
    def __init__(self,
                 asset_id,
                 taxonomy,
                 number,
                 location,
                 values,
                 area=1,
                 deductibles=None,
                 insurance_limits=None,
                 retrofitting_values=None):
        """
        :param asset_id:
            an unique identifier of the assets within the given exposure
        :param taxonomy:
            asset taxonomy
        :param number:
            number of apartments of number of people in the given asset
        :param location:
            geographic location of the asset
        :param dict values:
            asset values keyed by loss types
        :param dict deductible:
            deductible values (expressed as a percentage relative to
            the value of the asset) keyed by loss types
        :param dict insurance_limits:
            insured limits values (expressed as a percentage relative to
            the value of the asset) keyed by loss types
        :param dict retrofitting_values:
            asset retrofitting values keyed by loss types
        """
        self.id = asset_id
        self.taxonomy = taxonomy
        self.number = number
        self.location = location
        self.values = values
        self.area = area
        self.retrofitting_values = retrofitting_values
        self.deductibles = deductibles
        self.insurance_limits = insurance_limits

    def value(self, loss_type):
        """
        :returns: the total asset value for `loss_type`
        """
        value = self.values[loss_type]
        return None if value is None else value * self.number * self.area

    def deductible(self, loss_type):
        """
        :returns: the deductible of the asset for `loss_type`
        """
        return self.deductibles[loss_type]

    def insurance_limit(self, loss_type):
        """
        :returns: the deductible of the asset for `loss_type`
        """

        return self.insurance_limits[loss_type]

    def retrofitted(self, loss_type):
        """
        :returns: the asset retrofitted value for `loss_type`
        """
        return self.retrofitting_values[loss_type]

    def __repr__(self):
        return '<Asset %s>' % self.id


class Workflow(object):
    """
    Base class. Can be used in the tests as a mock.
    """
    def __init__(self, imt, taxonomy, risk_functions):
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = risk_functions

    @property
    def loss_types(self):
        """
        The list of loss types in the underlying vulnerability functions,
        in lexicographic order
        """
        return sorted(self.risk_functions)


@registry.add('classical_risk')
class Classical(Workflow):
    """
    Classical PSHA-Based Workflow.

    1) Compute loss curves, loss maps, loss fractions for each
       realization.
    2) Compute (if more than one realization is given) mean and
       quantiles loss curves, maps and fractions.

    Per-realization Output are saved into
    :class:`openquake.risklib.scientific.Classical.Output` which contains
    the several fields:

    :attr assets:
      an iterable over N assets the outputs refer to
    :attr loss_curves:
      a numpy array of N loss curves. If the curve resolution is R, the final
      shape of the array will be (N, 2, R), where the `two` accounts for
      the losses/poes dimensions
    :attr average_losses:
      a numpy array of N average loss values
    :attr insured_curves:
      a numpy array of N insured loss curves, shaped (N, 2, R)
    :attr average_insured_losses:
      a numpy array of N average insured loss values
    :attr loss_maps:
      a numpy array of P elements holding N loss maps where P is the
      number of `conditional_loss_poes` considered. Shape: (P, N)
    :attr loss_fractions:
      a numpy array of D elements holding N loss fraction values where D is the
      number of `poes_disagg`. Shape: (D, N)

    The statistical outputs are stored into
    :class:`openquake.risklib.scientific.Classical.StatisticalOutput`,
    which holds the following fields:

    :attr assets:
      an iterable of N assets the outputs refer to
    :attr mean_curves:
       A numpy array with N mean loss curves. Shape: (N, 2)
    :attr mean_average_losses:
       A numpy array with N mean average loss values
    :attr mean_maps:
       A numpy array with P mean loss maps. Shape: (P, N)
    :attr mean_fractions:
       A numpy array with F mean fractions, where F is the number of PoEs
       used for disaggregation. Shape: (F, N)
    :attr quantile_curves:
       A numpy array with Q quantile curves (Q = number of quantiles).
       Shape: (Q, N, 2, R)
    :attr quantile_average_losses:
       A numpy array shaped (Q, N) with average losses
    :attr quantile_maps:
       A numpy array with Q quantile maps shaped (Q, P, N)
    :attr quantile_fractions:
       A numpy array with Q quantile maps shaped (Q, F, N)
    :attr mean_insured_curves:
       A numpy array with N mean insured loss curves. Shape: (N, 2)
    :attr mean_average_insured_losses:
       A numpy array with N mean average insured loss values
    :attr quantile_insured_curves:
       A numpy array with Q quantile insured curves (Q = number of quantiles).
       Shape: (Q, N, 2, R)
    :attr quantile_average_insured_losses:
       A numpy array shaped (Q, N) with average insured losses
    """

    Output = collections.namedtuple(
        'Output',
        'assets loss_type loss_curves average_losses '
        'insured_curves average_insured_losses '
        'loss_maps loss_fractions')

    StatisticalOutput = collections.namedtuple(
        'StatisticalOutput',
        'assets mean_curves mean_average_losses '
        'mean_maps mean_fractions quantile_curves quantile_average_losses '
        'quantile_maps quantile_fractions '
        'mean_insured_curves mean_average_insured_losses '
        'quantile_insured_curves quantile_average_insured_losses')

    def __init__(self, imt, taxonomy, vulnerability_functions,
                 hazard_imtls, lrem_steps_per_interval,
                 conditional_loss_poes, poes_disagg,
                 insured_losses=False):
        """
        :param float poes_disagg:
            Probability of Exceedance levels used for disaggregate losses by
            taxonomy.
        :param hazard_imtls:
            the intensity measure type and levels of the hazard computation
        :param bool insured_losses:
            True if insured loss curves should be computed

        See :func:`openquake.risklib.scientific.classical` for a description
        of the other parameters.
        """
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions
        imls = hazard_imtls[self.imt]
        self.curves = dict(
            (loss_type,
             functools.partial(scientific.classical, vf, imls,
                               steps=lrem_steps_per_interval))
            for loss_type, vf in vulnerability_functions.items())
        self.conditional_loss_poes = conditional_loss_poes
        self.poes_disagg = poes_disagg
        self.insured_losses = insured_losses

    def __call__(self, loss_type, assets, hazard_curves, _epsilons=None,
                 _tags=None):
        """
        :param str loss_type:
            the loss type considered
        :param assets:
            assets is an iterator over N
            :class:`openquake.risklib.scientific.Asset` instances
        :param hazard_curves:
            an iterator over N arrays with the poes
        :param _epsilons:
            ignored, here only for API compatibility with other calculators
        :returns:
            a :class:`openquake.risklib.scientific.Classical.Output` instance.
        """
        curves = utils.numpy_map(self.curves[loss_type], hazard_curves)
        average_losses = utils.numpy_map(scientific.average_loss, curves)
        maps = scientific.loss_map_matrix(self.conditional_loss_poes, curves)
        fractions = scientific.loss_map_matrix(self.poes_disagg, curves)

        if self.insured_losses and loss_type != 'fatalities':
            deductibles = [a.deductible(loss_type) for a in assets]
            limits = [a.insurance_limit(loss_type) for a in assets]

            insured_curves = utils.numpy_map(
                scientific.insured_loss_curve, curves, deductibles, limits)
            average_insured_losses = utils.numpy_map(
                scientific.average_loss, insured_curves)
        else:
            insured_curves = None
            average_insured_losses = None

        return self.Output(
            assets, loss_type,
            curves, average_losses, insured_curves, average_insured_losses,
            maps, fractions)

    def statistics(self, all_outputs, quantiles):
        """
        :param quantiles:
            quantile levels used to compute quantile outputs
        :returns:
            a :class:`openquake.risklib.scientific.Classical.StatisticalOutput`
            instance holding statistical outputs (e.g. mean loss curves).
        """
        if len(all_outputs) == 1:  # single realization
            return

        outputs = []
        weights = []
        loss_curves = []
        for out in all_outputs:
            outputs.append(out.output)
            weights.append(out.weight)
            loss_curves.append(out.output.loss_curves)

        def normalize_curves(curves):
            losses = curves[0][0]
            return [losses, [poes for _losses, poes in curves]]

        (mean_curves, mean_average_losses, mean_maps,
         quantile_curves, quantile_average_losses, quantile_maps) = (
            scientific.exposure_statistics(
                [normalize_curves(curves) for curves
                 in numpy.array(loss_curves).transpose(1, 0, 2, 3)],
                self.conditional_loss_poes + self.poes_disagg,
                weights, quantiles))

        if self.insured_losses:
            loss_curves = [out.insured_curves for out in outputs]
            (mean_insured_curves, mean_average_insured_losses, _,
             quantile_insured_curves, quantile_average_insured_losses, _) = (
                scientific.exposure_statistics(
                    [normalize_curves(curves) for curves
                     in numpy.array(loss_curves).transpose(1, 0, 2, 3)],
                    [], weights, quantiles))
        else:
            mean_insured_curves = None
            mean_average_insured_losses = None
            quantile_insured_curves = None
            quantile_average_insured_losses = None

        return self.StatisticalOutput(
            outputs[0].assets,
            mean_curves, mean_average_losses,
            mean_maps[0:len(self.conditional_loss_poes)],
            mean_maps[len(self.conditional_loss_poes):],
            quantile_curves, quantile_average_losses,
            quantile_maps[:, 0:len(self.conditional_loss_poes)],
            quantile_maps[:, len(self.conditional_loss_poes):],
            mean_insured_curves, mean_average_insured_losses,
            quantile_insured_curves, quantile_average_insured_losses)

    def compute_all_outputs(self, getter, loss_type):
        """
        :param getter:
            a getter object
        :param str loss_type:
            a string identifying the loss type we are considering
        :returns:
            a number of outputs equal to the number of realizations
        """
        all_outputs = []
        for hazard in getter.get_hazards():  # for each realization
            all_outputs.append(
                Output(hazard.hid, hazard.weight, loss_type,
                       self(loss_type, getter.assets, hazard.data)))
        return all_outputs


@registry.add('event_based_risk')
class ProbabilisticEventBased(Workflow):
    """
    Implements the Probabilistic Event Based workflow

    Per-realization Output are saved into
    :class:`openquake.risklib.scientific.ProbabilisticEventBased.Output`
    which contains the several fields:

    :attr assets:
      an iterable over N assets the outputs refer to

    :attr loss_matrix:
      an array of losses shaped N x E (where E is the number of events)

    :attr loss_curves:
      a numpy array of N loss curves. If the curve resolution is R, the final
      shape of the array will be (N, 2, R), where the `two` accounts for
      the losses/poes dimensions

    :attr average_losses:
      a numpy array of N average loss values

    :attr stddev_losses:
      a numpy array holding N standard deviation of losses

    :attr insured_curves:
      a numpy array of N insured loss curves, shaped (N, 2, R)

    :attr average_insured_losses:
      a numpy array of N average insured loss values

    :attr stddev_insured_losses:
      a numpy array holding N standard deviation of losses

    :attr loss_maps:
      a numpy array of P elements holding N loss maps where P is the
      number of `conditional_loss_poes` considered. Shape: (P, N)

    :attr dict event_loss_table:
      a dictionary mapping event ids to aggregate loss values

    The statistical outputs are stored into
    :class:`.ProbabilisticEventBased.StatisticalOutput`.
    See :class:`openquake.risklib.scientific.Classical.StatisticalOutput` for
    more details.
    """
    Output = collections.namedtuple(
        'Output',
        "assets loss_type loss_matrix loss_curves average_losses stddev_losses"
        " insured_curves average_insured_losses stddev_insured_losses"
        " loss_maps event_loss_table")

    StatisticalOutput = collections.namedtuple(
        'StatisticalOutput',
        'assets mean_curves mean_average_losses '
        'mean_maps quantile_curves quantile_average_losses quantile_maps '
        'mean_insured_curves mean_average_insured_losses '
        'quantile_insured_curves quantile_average_insured_losses '
        'event_loss_table')

    def __init__(
            self, imt, taxonomy,
            vulnerability_functions,
            risk_investigation_time,
            tses,
            loss_curve_resolution,
            conditional_loss_poes,
            insured_losses=False):
        """
        See :func:`openquake.risklib.scientific.event_based` for a description
        of the input parameters.
        """
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions
        self.curves = functools.partial(
            scientific.event_based, curve_resolution=loss_curve_resolution,
            time_span=risk_investigation_time, tses=tses)
        self.conditional_loss_poes = conditional_loss_poes
        self.insured_losses = insured_losses
        self.return_loss_matrix = True

    def event_loss(self, loss_matrix, event_ids):
        """
        :param loss_matrix:
           a numpy array of losses shaped N x E, where E is the number
           of events and N the number of samplings

        :param event_ids:
           a numpy array holding E event ids

        :returns:
            a :class:`collections.Counter` with the sums of the loss matrix
            per each event_id
        """
        return collections.Counter(
            dict(zip(event_ids, numpy.sum(loss_matrix, axis=1))))

    def __call__(self, loss_type, assets, ground_motion_values, epsilons,
                 event_ids):
        """
        :param str loss_type: the loss type considered

        :param assets:
           assets is an iterator over
           :class:`openquake.risklib.scientific.Asset` instances

        :param ground_motion_values:
           a numpy array with ground_motion_values of shape N x R

        :param epsilons:
           a numpy array with stochastic values of shape N x R

        :param event_ids:
           a numpy array of R event ID (integer)

        :returns:
            a :class:
            `openquake.risklib.scientific.ProbabilisticEventBased.Output`
            instance.
        """
        loss_matrix = self.risk_functions[loss_type].apply_to(
            ground_motion_values, epsilons)

        curves = utils.numpy_map(self.curves, loss_matrix)
        average_losses = utils.numpy_map(scientific.average_loss, curves)
        stddev_losses = numpy.std(loss_matrix, axis=1)
        values = utils.numpy_map(lambda a: a.value(loss_type), assets)
        maps = scientific.loss_map_matrix(self.conditional_loss_poes, curves)
        elt = self.event_loss(loss_matrix.transpose() * values, event_ids)

        if self.insured_losses and loss_type != 'fatalities':
            deductibles = [a.deductible(loss_type) for a in assets]
            limits = [a.insurance_limit(loss_type) for a in assets]
            insured_loss_matrix = utils.numpy_map(
                scientific.insured_losses, loss_matrix, deductibles, limits)
            insured_curves = utils.numpy_map(self.curves, insured_loss_matrix)
            average_insured_losses = utils.numpy_map(
                scientific.average_loss, insured_curves)
            stddev_insured_losses = numpy.std(insured_loss_matrix, axis=1)
        else:
            insured_curves = None
            average_insured_losses = None
            stddev_insured_losses = None

        return self.Output(
            assets, loss_type,
            loss_matrix if self.return_loss_matrix else None,
            curves, average_losses, stddev_losses,
            insured_curves, average_insured_losses, stddev_insured_losses,
            maps, elt)

    def compute_all_outputs(self, getter, loss_type):
        """
        :param getter:
            a getter object
        :param str loss_type:
            a string identifying the loss type we are considering
        :returns:
            a number of outputs equal to the number of realizations
        """
        for hazard in getter.get_hazards():  # for each realization
            out = self(loss_type, getter.assets, hazard.data,
                       getter.get_epsilons(), getter.rupture_ids)
            yield Output(hazard.hid, hazard.weight, loss_type, out)

    def statistics(self, all_outputs, quantiles):
        """
        :returns:
            a :class:`.ProbabilisticEventBased.StatisticalOutput`
            instance holding statistical outputs (e.g. mean loss curves).
        :param quantiles:
            quantile levels used to compute quantile outputs
        """
        if len(all_outputs) == 1:  # single realization
            return

        outputs = []
        weights = []
        loss_curves = []
        for out in all_outputs:
            outputs.append(out.output)
            weights.append(out.weight)
            loss_curves.append(out.output.loss_curves)

        curve_matrix = numpy.array(loss_curves).transpose(1, 0, 2, 3)

        (mean_curves, mean_average_losses, mean_maps,
         quantile_curves, quantile_average_losses, quantile_maps) = (
            scientific.exposure_statistics(
                [self._normalize_curves(curves) for curves in curve_matrix],
                self.conditional_loss_poes, weights, quantiles))
        elt = sum((out.event_loss_table for out in outputs),
                  collections.Counter())

        if self.insured_losses:
            loss_curves = [out.insured_curves for out in outputs]
            (mean_insured_curves, mean_average_insured_losses, _,
             quantile_insured_curves, quantile_average_insured_losses, _) = (
                scientific.exposure_statistics(
                    [self._normalize_curves(curves)
                     for curves
                     in numpy.array(loss_curves).transpose(1, 0, 2, 3)],
                    [], weights, quantiles))
        else:
            mean_insured_curves = None
            mean_average_insured_losses = None
            quantile_insured_curves = None
            quantile_average_insured_losses = None

        return self.StatisticalOutput(
            outputs[0].assets, mean_curves, mean_average_losses, mean_maps,
            quantile_curves, quantile_average_losses, quantile_maps,
            mean_insured_curves, mean_average_insured_losses,
            quantile_insured_curves, quantile_average_insured_losses,
            elt)

    def _normalize_curves(self, curves):
        non_trivial_curves = [(losses, poes)
                              for losses, poes in curves if losses[-1] > 0]
        if not non_trivial_curves:  # no damage. all trivial curves
            return curves[0][0], [poes for _losses, poes in curves]
        else:  # standard case
            max_losses = [losses[-1]  # we assume non-decreasing losses
                          for losses, _poes in non_trivial_curves]
            reference_curve = non_trivial_curves[numpy.argmax(max_losses)]
            loss_ratios = reference_curve[0]
            curves_poes = [interpolate.interp1d(
                losses, poes, bounds_error=False, fill_value=0)(loss_ratios)
                for losses, poes in curves]
        return loss_ratios, curves_poes


@registry.add('event_loss')
class EventLoss(ProbabilisticEventBased):
    """
    Implements the Event Loss workflow

    Per-realization Output are saved into
    :class:`openquake.risklib.workflows.EventLoss.Output`
    which contains several fields:

    :attr assets:
      an iterable over N assets the outputs refer to

    :attr dict event_loss_table:
      a dictionary mapping event ids to aggregate loss values

    """
    Output = collections.namedtuple(
        'Output', "assets loss_type event_loss_per_asset tags")

    def __call__(self, loss_type, assets, ground_motion_values, epsilons,
                 event_ids):
        """
        :param str loss_type: the loss type considered

        :param assets:
           assets is an iterator over
           :class:`openquake.risklib.scientific.Asset` instances

        :param ground_motion_values:
           a numpy array with ground_motion_values of shape N x R

        :param epsilons:
           a numpy array with stochastic values of shape N x R

        :param event_ids:
           a numpy array of R event ID (integer)

        :returns:
            a :class:
            `openquake.risklib.workflows.EventLoss.Output`
            instance.
        """
        loss_matrix = self.risk_functions[loss_type].apply_to(
            ground_motion_values, epsilons)
        values = utils.numpy_map(lambda a: a.value(loss_type), assets)
        ela = loss_matrix.T * values  # matrix with R x N elements
        return self.Output(assets, loss_type, ela, event_ids)


@registry.add('classical_bcr')
class ClassicalBCR(Workflow):
    def __init__(self, imt, taxonomy,
                 vulnerability_functions_orig,
                 vulnerability_functions_retro,
                 hazard_imtls,
                 lrem_steps_per_interval,
                 interest_rate, asset_life_expectancy):
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions_orig
        self.assets = None  # set a __call__ time
        self.interest_rate = interest_rate
        self.asset_life_expectancy = asset_life_expectancy
        imls = hazard_imtls[self.imt]
        self.curves_orig = dict(
            (loss_type,
             functools.partial(scientific.classical, vf, imls,
                               steps=lrem_steps_per_interval))
            for loss_type, vf in vulnerability_functions_orig.items())
        self.curves_retro = dict(
            (loss_type,
             functools.partial(scientific.classical, vf, imls,
                               steps=lrem_steps_per_interval))
            for loss_type, vf in vulnerability_functions_retro.items())

    def __call__(self, loss_type, assets, hazard):
        self.assets = assets

        original_loss_curves = utils.numpy_map(
            self.curves_orig[loss_type], hazard)
        retrofitted_loss_curves = utils.numpy_map(
            self.curves_retro[loss_type], hazard)

        eal_original = utils.numpy_map(
            scientific.average_loss, original_loss_curves)

        eal_retrofitted = utils.numpy_map(
            scientific.average_loss, retrofitted_loss_curves)

        bcr_results = [
            scientific.bcr(
                eal_original[i], eal_retrofitted[i],
                self.interest_rate, self.asset_life_expectancy,
                asset.value(loss_type), asset.retrofitted(loss_type))
            for i, asset in enumerate(assets)]

        return zip(eal_original, eal_retrofitted, bcr_results)

    compute_all_outputs = Classical.compute_all_outputs.im_func


@registry.add('event_based_bcr')
class ProbabilisticEventBasedBCR(Workflow):
    def __init__(self, imt, taxonomy,
                 vulnerability_functions_orig,
                 vulnerability_functions_retro,
                 risk_investigation_time, tses, loss_curve_resolution,
                 interest_rate, asset_life_expectancy):
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions_orig
        self.assets = None  # set a __call__ time
        self.interest_rate = interest_rate
        self.asset_life_expectancy = asset_life_expectancy
        self.vf_orig = vulnerability_functions_orig
        self.vf_retro = vulnerability_functions_retro
        self.curves = functools.partial(
            scientific.event_based, curve_resolution=loss_curve_resolution,
            time_span=risk_investigation_time, tses=tses)

    def __call__(self, loss_type, assets, gmfs, epsilons, event_ids):
        self.assets = assets

        original_loss_curves = utils.numpy_map(
            self.curves, self.vf_orig[loss_type].apply_to(gmfs, epsilons))
        retrofitted_loss_curves = utils.numpy_map(
            self.curves, self.vf_retro[loss_type].apply_to(gmfs, epsilons))

        eal_original = utils.numpy_map(
            scientific.average_loss, original_loss_curves)
        eal_retrofitted = utils.numpy_map(
            scientific.average_loss, retrofitted_loss_curves)

        bcr_results = [
            scientific.bcr(
                eal_original[i], eal_retrofitted[i],
                self.interest_rate, self.asset_life_expectancy,
                asset.value(loss_type), asset.retrofitted(loss_type))
            for i, asset in enumerate(assets)]

        return zip(eal_original, eal_retrofitted, bcr_results)

    compute_all_outputs = ProbabilisticEventBased.compute_all_outputs.im_func


@registry.add('scenario_risk')
class Scenario(Workflow):
    """
    Implements the Scenario workflow
    """
    Output = collections.namedtuple(
        'Output',
        "assets loss_type loss_matrix aggregate_losses "
        "insured_loss_matrix insured_losses")

    def __init__(self, imt, taxonomy, vulnerability_functions, insured_losses):
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions
        self.insured_losses = insured_losses

    def __call__(self, loss_type, assets, ground_motion_values, epsilons,
                 _tags=None):
        if loss_type == 'fatalities' and hasattr(assets[0], 'values'):
            # this is called only in oq-lite
            values = numpy.array([a.values[loss_type] for a in assets])
        else:
            values = numpy.array([a.value(loss_type) for a in assets])

        # a matrix of N x R elements
        loss_ratio_matrix = self.risk_functions[loss_type].apply_to(
            ground_motion_values, epsilons)

        # aggregating per asset, getting a vector of R elements
        aggregate_losses = numpy.sum(
            loss_ratio_matrix.transpose() * values, axis=1)
        if self.insured_losses and loss_type != "fatalities":
            deductibles = [a.deductible(loss_type) for a in assets]
            limits = [a.insurance_limit(loss_type) for a in assets]
            insured_loss_ratio_matrix = utils.numpy_map(
                scientific.insured_losses,
                loss_ratio_matrix, deductibles, limits)

            insured_loss_matrix = (
                insured_loss_ratio_matrix.transpose() * values).transpose()

            insured_losses = numpy.array(insured_loss_matrix).sum(axis=0)
        else:
            insured_loss_matrix = None
            insured_losses = None
        return self.Output(
            assets, loss_type, loss_ratio_matrix, aggregate_losses,
            insured_loss_matrix, insured_losses)


@registry.add('scenario_damage')
class Damage(Workflow):
    """
    Implements the ScenarioDamage workflow
    """
    def __init__(self, imt, taxonomy, fragility_functions):
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = fragility_functions

    def __call__(self, loss_type, assets, gmfs, _epsilons=None, _tags=None):
        """
        :param loss_type: the string 'damage'
        :param assets: a list of N assets of the same taxonomy
        :param gmfs: an array of N x R elements
        :returns: an array of N assets and an array of N x R x D elements

        where N is the number of points, R the number of realizations
        and D the number of damage states.
        """
        ffs = self.risk_functions['damage']
        damages = numpy.array(
            [[scientific.scenario_damage(ffs, gmv) for gmv in gmvs]
             for gmvs in gmfs])
        return assets, damages


@registry.add('classical_damage')
class ClassicalDamage(Workflow):
    """
    Implements the ClassicalDamage workflow
    """
    Output = collections.namedtuple('Output', "assets damages")

    def __init__(self, imt, taxonomy, fragility_functions,
                 hazard_imtls, hazard_investigation_time,
                 risk_investigation_time):
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = fragility_functions
        self.curves = functools.partial(
            scientific.classical_damage,
            fragility_functions['damage'], hazard_imtls[imt],
            hazard_investigation_time=hazard_investigation_time,
            risk_investigation_time=risk_investigation_time)

    def __call__(self, loss_type, assets, hazard_curves, _epsilons=None,
                 _tags=None):
        """
        :param loss_type: the string 'damage'
        :param assets: a list of N assets of the same taxonomy
        :param hazard_curves: an array of N x R elements
        :returns: an array of N assets and an array of N x D elements

        where N is the number of points and D the number of damage states.
        """
        fractions = utils.numpy_map(self.curves, hazard_curves)
        damages = [asset.number * fraction
                   for asset, fraction in zip(assets, fractions)]
        return self.Output(assets, damages)

    compute_all_outputs = Classical.compute_all_outputs.im_func


# NB: the approach used here relies on the convention of having the
# names of the arguments of the workflow class to be equal to the
# names of the parameter in the oqparam object. This is view as a
# feature, since it forces people to be consistent with the names,
# in the spirit of the 'convention over configuration' philosophy
def get_workflow(imt, taxonomy, oqparam, **extra):
    """
    Return an instance of the correct workflow class, depending on the
    attribute `calculation_mode` of the object `oqparam`.

    :param imt:
        an intensity measure type string
    :param taxonomy:
        a taxonomy string
    :param oqparam:
        an object containing the parameters needed by the workflow class
    :param extra:
        extra parameters to pass to the workflow class
    """
    workflow_class = registry[oqparam.calculation_mode]
    # arguments needed to instantiate the workflow class
    argnames = inspect.getargspec(workflow_class.__init__).args[3:]

    # arguments extracted from oqparam
    known_args = vars(oqparam)
    all_args = {}
    for argname in argnames:
        if argname in known_args:
            all_args[argname] = known_args[argname]

    if 'hazard_imtls' in argnames:  # special case
        all_args['hazard_imtls'] = getattr(
            oqparam, 'hazard_imtls', oqparam.imtls)
    all_args.update(extra)
    missing = set(argnames) - set(all_args)
    if missing:
        raise TypeError('Missing parameter: %s' % ', '.join(missing))
    return workflow_class(imt, taxonomy, **all_args)
