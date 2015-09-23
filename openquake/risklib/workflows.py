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
from __future__ import division
import sys
import inspect
import functools
import collections
import numpy

from openquake.baselib.general import CallableDict
from openquake.commonlib import valid
from openquake.risklib import utils, scientific

registry = CallableDict()


class CostCalculator(object):
    """
    Return the value of an asset for the given loss type depending
    on the cost types declared in the exposure, as follows:

        case 1: cost type: aggregated:
            cost = economic value
        case 2: cost type: per asset:
            cost * number (of assets) = economic value
        case 3: cost type: per area and area type: aggregated:
            cost * area = economic value
        case 4: cost type: per area and area type: per asset:
            cost * area * number = economic value

    The same "formula" applies to retrofitting cost.
    """
    def __init__(self, cost_types, area_types,
                 deduct_abs=True, limit_abs=True):
        for ct in cost_types.values():
            assert ct in ('aggregated', 'per_asset', 'per_area'), ct
        for at in area_types.values():
            assert at in ('aggregated', 'per_asset'), at
        self.cost_types = cost_types
        self.area_types = area_types
        self.deduct_abs = deduct_abs
        self.limit_abs = limit_abs

    def __call__(self, loss_type, values, area, number):
        cost = values[loss_type]
        if cost is None:
            return numpy.nan
        cost_type = self.cost_types[loss_type]
        if cost_type == "aggregated":
            return cost
        if cost_type == "per_asset":
            return cost * number
        if cost_type == "per_area":
            area_type = self.area_types[loss_type]
            if area_type == "aggregated":
                return cost * area
            elif area_type == "per_asset":
                return cost * area * number
        # this should never happen
        raise RuntimeError('Unable to compute cost')

costcalculator = CostCalculator(
    cost_types=dict(structural='per_area'),
    area_types=dict(structural='per_asset'))


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
                 retrofitting_values=None,
                 calc=costcalculator,
                 idx=None):
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
        :param calc:
            cost calculator instance
        :param idx:
            asset collection index
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
        self.calc = calc
        self.idx = idx
        self._cost = {}  # cache for the costs

    def value(self, loss_type, time_event=None):
        """
        :returns: the total asset value for `loss_type`
        """
        if loss_type == 'fatalities':
            return self.values['fatalities_' + str(time_event)]
        try:
            val = self._cost[loss_type]
        except KeyError:
            val = self.calc(loss_type, self.values, self.area, self.number)
            self._cost[loss_type] = val
        return val

    def deductible(self, loss_type):
        """
        :returns: the deductible fraction of the asset cost for `loss_type`
        """
        val = self.calc(loss_type, self.deductibles, self.area, self.number)
        if self.calc.deduct_abs:  # convert to relative value
            return val / self.calc(loss_type, self.values,
                                   self.area, self.number)
        else:
            return val

    def insurance_limit(self, loss_type):
        """
        :returns: the limit fraction of the asset cost for `loss_type`
        """
        val = self.calc(loss_type, self.insurance_limits, self.area,
                        self.number)
        if self.calc.limit_abs:  # convert to relative value
            return val / self.calc(loss_type, self.values,
                                   self.area, self.number)
        else:
            return val

    def retrofitted(self, loss_type, time_event=None):
        """
        :returns: the asset retrofitted value for `loss_type`
        """
        if loss_type == 'fatalities':
            return self.values['fatalities_' + str(time_event)]
        return self.calc(loss_type, self.retrofitting_values,
                         self.area, self.number)

    def __repr__(self):
        return '<Asset %s>' % self.id

    def __str__(self):
        return self.id


def get_values(loss_type, assets, time_event=None):
    """
    :returns:
        a numpy array with the values for the given assets, depending on the
        loss_type.
    """
    if hasattr(assets[0], 'values'):  # special case for oq-lite
        values = numpy.array([a.value(loss_type, time_event)
                              for a in assets])
    else:  # in the engine
        values = numpy.array([a.value(loss_type) for a in assets])
    return values


class List(list):
    """List subclass to which you can add attribute"""
    # this is ugly, but we already did that, and there is no other easy way


def out_by_rlz(workflow, assets, hazards, epsilons, tags, loss_type):
    """
    :param workflow: a Workflow instance
    :param assets: an array of assets of homogeneous taxonomy
    :param hazards: an array of dictionaries per each asset
    :param epsilons: an array of epsilons per each asset
    :param tags: rupture tags

    Yield lists out_by_rlz
    """
    out_by_rlz = List()
    # extract the realizations from the first asset
    for rlz in sorted(hazards[0]):
        hazs = [haz[rlz] for haz in hazards]  # hazard per each asset
        out = workflow(loss_type, assets, hazs, epsilons, tags)
        out.hid = rlz.ordinal
        out.weight = rlz.weight
        out_by_rlz.append(out)
    return out_by_rlz


class Workflow(object):
    """
    Base class. Can be used in the tests as a mock.
    """
    time_event = None  # used in scenario_risk
    riskmodel = None  # set by get_risk_model

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

    def gen_out_by_rlz(self, assets, hazards, epsilons, tags):
        """
        :param assets: an array of assets of homogeneous taxonomy
        :param hazards: an array of dictionaries per each asset
        :param epsilons: an array of epsilons per each asset
        :param tags: rupture tags

        Yield lists out_by_rlz.
        """
        for loss_type in self.loss_types:
            assets_ = assets
            epsilons_ = epsilons
            values = get_values(loss_type, assets, self.time_event)
            ok = ~numpy.isnan(values)
            if not ok.any():
                # there are no assets with a value
                continue
            # there may be assets without a value
            missing_value = not ok.all()
            if missing_value:
                assets_ = assets[ok]
                hazards = hazards[ok]
                epsilons_ = epsilons[ok]
            yield out_by_rlz(
                self, assets_, hazards, epsilons_, tags, loss_type)

    def __repr__(self):
        return '<%s%s>' % (self.__class__.__name__, list(self.risk_functions))


@registry.add('classical_risk')
class Classical(Workflow):
    """
    Classical PSHA-Based Workflow.

    1) Compute loss curves, loss maps, loss fractions for each
       realization.
    2) Compute (if more than one realization is given) mean and
       quantiles loss curves, maps and fractions.

    Per-realization Outputs contain the following fields:

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
    :class:`openquake.risklib.scientific.Output`,
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

        return scientific.Output(
            assets, loss_type, loss_curves=curves,
            average_losses=average_losses, insured_curves=insured_curves,
            average_insured_losses=average_insured_losses,
            loss_maps=maps, loss_fractions=fractions)

    def statistics(self, all_outputs, quantiles):
        """
        :param quantiles:
            quantile levels used to compute quantile outputs
        :returns:
            a :class:`openquake.risklib.scientific.Output`
            instance holding statistical outputs (e.g. mean loss curves).
        """
        if len(all_outputs) == 1:  # single realization
            return
        stats = scientific.StatsBuilder(
            quantiles, self.conditional_loss_poes, self.poes_disagg)
        return stats.build(all_outputs)

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
            out = self(loss_type, getter.assets, hazard.data)
            out.hid = hazard.hid
            out.weight = hazard.weight
            all_outputs.append(out)
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
      an array of losses shaped N x T (where T is the number of events)

    :attr loss_curves:
      a numpy array of N loss curves. If the curve resolution is C, the final
      shape of the array will be (N, 2, C), where the `two` accounts for
      the losses/poes dimensions

    :attr average_losses:
      a numpy array of N average loss values

    :attr stddev_losses:
      a numpy array holding N standard deviation of losses

    :attr insured_curves:
      a numpy array of N insured loss curves, shaped (N, 2, C)

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
    :class:`openquake.risklib.scientific.Output` objects.
    """
    def __init__(
            self, imt, taxonomy,
            vulnerability_functions,
            investigation_time,
            risk_investigation_time,
            number_of_logic_tree_samples,
            ses_per_logic_tree_path,
            loss_curve_resolution,
            conditional_loss_poes,
            insured_losses=False,
            loss_ratios=()):
        """
        See :func:`openquake.risklib.scientific.event_based` for a description
        of the input parameters.
        """
        time_span = risk_investigation_time or investigation_time
        self.ses_ratio = time_span / (
            investigation_time * ses_per_logic_tree_path)
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions
        self.loss_curve_resolution = loss_curve_resolution
        self.curves = functools.partial(
            scientific.event_based, curve_resolution=loss_curve_resolution,
            ses_ratio=self.ses_ratio)
        self.conditional_loss_poes = conditional_loss_poes
        self.insured_losses = insured_losses
        self.return_loss_matrix = True
        self.loss_ratios = loss_ratios

    def event_loss(self, loss_matrix, event_ids):
        """
        :param loss_matrix:
           a numpy array of losses shaped N x T, where T is the number
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
        n = len(assets)
        loss_matrix = self.risk_functions[loss_type].apply_to(
            ground_motion_values, epsilons)
        # sum on ruptures; compute the fractional losses
        average_losses = loss_matrix.sum(axis=1) * self.ses_ratio
        values = get_values(loss_type, assets)
        ela = loss_matrix.T * values  # matrix with T x N elements
        if self.insured_losses and loss_type != 'fatalities':
            deductibles = numpy.array(
                [a.deductible(loss_type) for a in assets])
            limits = numpy.array(
                [a.insurance_limit(loss_type) for a in assets])
            ilm = utils.numpy_map(
                scientific.insured_losses, loss_matrix, deductibles, limits)
        else:  # build a NaN matrix of size N x T
            ilm = numpy.empty((n, len(ground_motion_values[0])))
            ilm.fill(numpy.nan)
        ila = ilm.T * values
        average_insured_losses = ilm.sum(axis=1) * self.ses_ratio
        cb = self.riskmodel.curve_builders[self.riskmodel.lti[loss_type]]
        return scientific.Output(
            assets, loss_type,
            event_loss_per_asset=ela,
            insured_loss_per_asset=ila,
            average_losses=average_losses,
            average_insured_losses=average_insured_losses,
            counts_matrix=cb.build_counts(loss_matrix),
            insured_counts_matrix=cb.build_counts(ilm),
            tags=event_ids)

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
            out.hid = hazard.hid
            out.weight = hazard.weight
            yield out

    def statistics(self, all_outputs, quantiles):
        """
        :returns:
            a :class:`openquake.risklib.scientific.Output`
            instance holding statistical outputs (e.g. mean loss curves).
        :param quantiles:
            quantile levels used to compute quantile outputs
        """
        if len(all_outputs) == 1:  # single realization
            return
        stats = scientific.StatsBuilder(
            quantiles, self.conditional_loss_poes, [],
            scientific.normalize_curves_eb)
        out = stats.build(all_outputs)
        out.event_loss_table = sum(
            (out.event_loss_table for out in all_outputs),
            collections.Counter())
        return out


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

        return scientific.Output(
            assets, loss_type,
            data=list(zip(eal_original, eal_retrofitted, bcr_results)))

    compute_all_outputs = (Classical.compute_all_outputs if sys.version > '3'
                           else Classical.compute_all_outputs.__func__)


@registry.add('event_based_bcr')
class ProbabilisticEventBasedBCR(Workflow):
    def __init__(self, imt, taxonomy,
                 vulnerability_functions_orig,
                 vulnerability_functions_retro,
                 investigation_time,
                 risk_investigation_time,
                 number_of_logic_tree_samples,
                 ses_per_logic_tree_path,
                 loss_curve_resolution,
                 interest_rate, asset_life_expectancy):
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions_orig
        self.assets = None  # set a __call__ time
        self.interest_rate = interest_rate
        self.asset_life_expectancy = asset_life_expectancy
        self.vf_orig = vulnerability_functions_orig
        self.vf_retro = vulnerability_functions_retro
        time_span = risk_investigation_time or investigation_time
        self.curves = functools.partial(
            scientific.event_based, curve_resolution=loss_curve_resolution,
            time_span=time_span, tses=time_span * ses_per_logic_tree_path)
        # TODO: add multiplication by number_of_logic_tree_samples or 1

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

        return scientific.Output(
            assets, loss_type,
            data=list(zip(eal_original, eal_retrofitted, bcr_results)))

    compute_all_outputs = (
        ProbabilisticEventBased.compute_all_outputs if sys.version > '3' else
        ProbabilisticEventBased.compute_all_outputs.__func__)


@registry.add('scenario_risk')
class Scenario(Workflow):
    """
    Implements the Scenario workflow
    """
    def __init__(self, imt, taxonomy, vulnerability_functions,
                 insured_losses, time_event=None):
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions
        self.insured_losses = insured_losses
        self.time_event = time_event

    def __call__(self, loss_type, assets, ground_motion_values, epsilons,
                 _tags=None):
        values = get_values(loss_type, assets, self.time_event)

        # a matrix of N x R elements
        loss_ratio_matrix = self.risk_functions[loss_type].apply_to(
            ground_motion_values, epsilons)
        # another matrix of N x R elements
        loss_matrix = (loss_ratio_matrix.T * values).T
        # an array of R elements
        aggregate_losses = loss_matrix.sum(axis=0)

        if self.insured_losses and loss_type != "fatalities":
            deductibles = [a.deductible(loss_type) for a in assets]
            limits = [a.insurance_limit(loss_type) for a in assets]
            insured_loss_ratio_matrix = utils.numpy_map(
                scientific.insured_losses,
                loss_ratio_matrix, deductibles, limits)
            insured_loss_matrix = (insured_loss_ratio_matrix.T * values).T

            # aggregating per asset, getting a vector of R elements
            insured_losses = insured_loss_matrix.sum(axis=0)
        else:
            insured_loss_matrix = None
            insured_losses = None
        return scientific.Output(
            assets, loss_type, loss_matrix=loss_matrix,
            loss_ratio_matrix=loss_ratio_matrix,
            aggregate_losses=aggregate_losses,
            insured_loss_matrix=insured_loss_matrix,
            insured_losses=insured_losses)


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
        return scientific.Output(assets, 'damage', damages=damages)

    def gen_out_by_rlz(self, assets, hazards, epsilons, tags):
        """
        :param assets: an array of assets of homogeneous taxonomy
        :param hazards: an array of dictionaries per each asset
        :param epsilons: an array of epsilons per each asset
        :param tags: rupture tags

        Yield a single list of outputs
        """
        yield out_by_rlz(self, assets, hazards, epsilons, tags, 'damage')


@registry.add('classical_damage')
class ClassicalDamage(Damage):
    """
    Implements the ClassicalDamage workflow
    """
    def __init__(self, imt, taxonomy, fragility_functions,
                 hazard_imtls, investigation_time,
                 risk_investigation_time):
        self.imt = imt
        self.taxonomy = taxonomy
        self.risk_functions = fragility_functions
        self.curves = functools.partial(
            scientific.classical_damage,
            fragility_functions['damage'], hazard_imtls[imt],
            investigation_time=investigation_time,
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
        return scientific.Output(assets, 'damage', damages=damages)

    compute_all_outputs = (
        Classical.compute_all_outputs if sys.version > '3' else
        Classical.compute_all_outputs.__func__)


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
    known_args = set(name for name, value in
                     inspect.getmembers(oqparam.__class__)
                     if isinstance(value, valid.Param))
    all_args = {}
    for argname in argnames:
        if argname in known_args:
            all_args[argname] = getattr(oqparam, argname)

    if 'hazard_imtls' in argnames:  # special case
        all_args['hazard_imtls'] = oqparam.imtls
    all_args.update(extra)
    missing = set(argnames) - set(all_args)
    if missing:
        raise TypeError('Missing parameter: %s' % ', '.join(missing))

    return workflow_class(imt, taxonomy, **all_args)
