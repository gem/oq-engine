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
import collections
import numpy
from scipy import interpolate

from openquake.risklib import calculators, utils, scientific

Output = collections.namedtuple('Output', 'hid weight loss_type output')

registry = utils.Register()


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
                 deductibles=None,
                 insurance_limits=None,
                 retrofitting_values=None,
                 epsilons=None):
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
        self.retrofitting_values = retrofitting_values
        self.deductibles = deductibles
        self.insurance_limits = insurance_limits
        self.epsilons = epsilons

    def value(self, loss_type):
        """
        :returns: the asset value for `loss_type`
        """
        return self.values[loss_type]

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
    def __init__(self, vulnerability_functions):
        self.vulnerability_functions = vulnerability_functions

    @property
    def loss_types(self):
        """
        The list of loss types in the underlying vulnerability functions,
        in lexicographic order
        """
        return sorted(self.vulnerability_functions)


@registry.add('classical_risk')
class Classical(Workflow):
    """
    Classical PSHA-Based Workflow.

    1) Compute loss curves, loss maps, loss fractions for each
       realization.
    2) Compute (if more than one realization is given) mean and
       quantiles loss curves, maps and fractions.

    Per-realization Output are saved into
    :class:`openquake.risklib.workflows.Classical.Output` which contains
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
    :class:`openquake.risklib.workflows.Classical.StatisticalOutput`,
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
        'assets loss_curves average_losses '
        'insured_curves average_insured_losses '
        'loss_maps loss_fractions')

    StatisticalOutput = collections.namedtuple(
        'StatisticalOutput',
        'assets mean_curves mean_average_losses '
        'mean_maps mean_fractions quantile_curves quantile_average_losses '
        'quantile_maps quantile_fractions '
        'mean_insured_curves mean_average_insured_losses '
        'quantile_insured_curves quantile_average_insured_losses')

    def __init__(self,
                 vulnerability_functions,
                 lrem_steps_per_interval,
                 conditional_loss_poes,
                 poes_disagg,
                 insured_losses=False):
        """
        :param float poes_disagg:
            Probability of Exceedance levels used for disaggregate losses by
            taxonomy.
        :param bool insured_losses:
            True if insured loss curves should be computed

        See :func:`openquake.risklib.scientific.classical` for a description
        of the other parameters.
        """
        self.vulnerability_functions = vulnerability_functions
        self.curves = dict(
            (loss_type,
             calculators.ClassicalLossCurve(vf, lrem_steps_per_interval))
            for loss_type, vf in vulnerability_functions.items())
        self.maps = calculators.LossMap(conditional_loss_poes)
        self.fractions = calculators.LossMap(poes_disagg)
        self.insured_losses = insured_losses

    def __call__(self, loss_type, assets, hazard_curves):
        """
        :param str loss_type:
            the loss type considered
        :param assets:
            assets is an iterator over N
            :class:`openquake.risklib.workflows.Asset` instances
        :param hazard_curves:
            curves is an iterator over hazard curves (numpy array shaped 2xR).
        :returns:
            a :class:`openquake.risklib.workflows.Classical.Output` instance.
        """
        curves = self.curves[loss_type](hazard_curves)
        average_losses = numpy.array([scientific.average_loss(losses, poes)
                                      for losses, poes in curves])
        maps = self.maps(curves)
        fractions = self.fractions(curves)

        if self.insured_losses and loss_type != 'fatalities':
            deductibles = [a.deductible(loss_type) for a in assets]
            limits = [a.insurance_limit(loss_type) for a in assets]

            insured_curves = utils.numpy_map(
                scientific.insured_loss_curve, curves, deductibles, limits)
            average_insured_losses = [
                scientific.average_loss(losses, poes)
                for losses, poes in insured_curves]
        else:
            insured_curves = None
            average_insured_losses = None

        return self.Output(
            assets,
            curves, average_losses, insured_curves, average_insured_losses,
            maps, fractions)

    def statistics(self, all_outputs, quantiles, post_processing):
        """
        :param quantiles:
            quantile levels used to compute quantile outputs
        :param post_processing:
            an object implementing the following protocol:
            #mean_curve(curves, weights)
            #weighted_quantile_curve(curves, weights, quantile)
            #quantile_curve(curves, quantile)
        :returns:
            a :class:`openquake.risklib.workflows.Classical.StatisticalOutput`
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
            calculators.exposure_statistics(
                [normalize_curves(curves)
                 for curves
                 in numpy.array(loss_curves).transpose(1, 0, 2, 3)],
                self.maps.poes + self.fractions.poes,
                weights, quantiles, post_processing))

        if self.insured_losses:
            loss_curves = [out.insured_curves for out in outputs]
            (mean_insured_curves, mean_average_insured_losses, _,
             quantile_insured_curves, quantile_average_insured_losses, _) = (
                calculators.exposure_statistics(
                    [normalize_curves(curves)
                     for curves
                     in numpy.array(loss_curves).transpose(1, 0, 2, 3)],
                    [], weights, quantiles, post_processing))
        else:
            mean_insured_curves = None
            mean_average_insured_losses = None
            quantile_insured_curves = None
            quantile_average_insured_losses = None

        return self.StatisticalOutput(
            outputs[0].assets,
            mean_curves, mean_average_losses,
            mean_maps[0:len(self.maps.poes)],
            mean_maps[len(self.maps.poes):],
            quantile_curves, quantile_average_losses,
            quantile_maps[:, 0:len(self.maps.poes)],
            quantile_maps[:, len(self.maps.poes):],
            mean_insured_curves, mean_average_insured_losses,
            quantile_insured_curves, quantile_average_insured_losses)

    def compute_all_outputs(self, risk_input, loss_type, getter_monitor):
        """
        :param risk_input:
            a risk_input object
        :param str loss_type:
            a string identifying the loss type we are considering
        :getter_monitor:
            a context manager monitoring the time and resources
            spent the in the computation
        :returns:
            a number of outputs equal to the number of realizations
        """
        all_outputs = []
        for hazard in risk_input.get_hazards():  # for each realization
            with getter_monitor.copy('computing individual risk'):
                all_outputs.append(
                    Output(hazard.hid, hazard.weight, loss_type,
                           self(loss_type, risk_input.assets, hazard.data)))
        return all_outputs


@registry.add('event_based_risk')
class ProbabilisticEventBased(Workflow):
    """
    Implements the Probabilistic Event Based workflow

    Per-realization Output are saved into
    :class:`openquake.risklib.workflows.ProbabilisticEventBased.Output`
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
    See :class:`openquake.risklib.workflows.Classical.StatisticalOutput` for
    more details.
    """
    Output = collections.namedtuple(
        'Output',
        "assets loss_matrix loss_curves average_losses stddev_losses "
        "insured_curves average_insured_losses stddev_insured_losses "
        "loss_maps event_loss_table")

    StatisticalOutput = collections.namedtuple(
        'StatisticalOutput',
        'assets mean_curves mean_average_losses '
        'mean_maps quantile_curves quantile_average_losses quantile_maps '
        'mean_insured_curves mean_average_insured_losses '
        'quantile_insured_curves quantile_average_insured_losses '
        'event_loss_table')

    def __init__(
            self,
            vulnerability_functions,
            time_span, tses,
            loss_curve_resolution,
            conditional_loss_poes,
            insured_losses=False,
            return_loss_matrix=True):
        """
        See :func:`openquake.risklib.scientific.event_based` for a description
        of the input parameters. The last parameter is

        :param bool return_loss_matrix:
            if False the loss_matrix is not saved in the Output tuple
            (a trick to save memory in the case of no disaggregation)
        """
        self.vulnerability_functions = vulnerability_functions
        self.curves = calculators.EventBasedLossCurve(
            time_span, tses, loss_curve_resolution)
        self.maps = calculators.LossMap(conditional_loss_poes)
        self.insured_losses = insured_losses
        self.return_loss_matrix = return_loss_matrix

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
           :class:`openquake.risklib.workflows.Asset` instances

        :param ground_motion_values:
           a numpy array with ground_motion_values of shape N x R

        :param epsilons:
           a numpy array with stochastic values of shape N x R

        :param event_ids:
           a numpy array of R event ID (integer)

        :returns:
            a
            :class:`openquake.risklib.workflows.ProbabilisticEventBased.Output`
            instance.
        """
        loss_matrix = self.vulnerability_functions[loss_type].apply_to(
            ground_motion_values, epsilons)

        curves = self.curves(loss_matrix)
        average_losses = numpy.array([scientific.average_loss(losses, poes)
                                      for losses, poes in curves])
        stddev_losses = numpy.std(loss_matrix, axis=1)
        values = utils.numpy_map(lambda a: a.value(loss_type), assets)
        maps = self.maps(curves)
        elt = self.event_loss(loss_matrix.transpose() * values, event_ids)

        if self.insured_losses and loss_type != 'fatalities':
            deductibles = [a.deductible(loss_type) for a in assets]
            limits = [a.insurance_limit(loss_type) for a in assets]
            insured_loss_matrix = utils.numpy_map(
                scientific.insured_losses, loss_matrix, deductibles, limits)
            insured_curves = self.curves(insured_loss_matrix)
            average_insured_losses = [
                scientific.average_loss(losses, poes)
                for losses, poes in insured_curves]
            stddev_insured_losses = numpy.std(insured_loss_matrix, axis=1)
        else:
            insured_curves = None
            average_insured_losses = None
            stddev_insured_losses = None

        return self.Output(
            assets, loss_matrix if self.return_loss_matrix else None,
            curves, average_losses, stddev_losses,
            insured_curves, average_insured_losses, stddev_insured_losses,
            maps, elt)

    def compute_all_outputs(self, risk_input, loss_type, getter_monitor):
        """
        :param risk_input:
            a risk_input object
        :param str loss_type:
            a string identifying the loss type we are considering
        :param getter_monitor:
            a context manager monitoring the time and resources
            spent the in the computation
        :returns:
            a number of outputs equal to the number of realizations
        """
        all_outputs = []
        for hazard in risk_input.get_hazards():  # for each realization
            with getter_monitor.copy('computing individual risk'):
                out = self(loss_type, risk_input.assets, hazard.data,
                           risk_input.get_epsilons(), risk_input.rupture_ids)
                all_outputs.append(
                    Output(hazard.hid, hazard.weight, loss_type, out))
        return all_outputs

    def statistics(self, all_outputs, quantiles, post_processing):
        """
        :returns:
            a :class:`.ProbabilisticEventBased.StatisticalOutput`
            instance holding statistical outputs (e.g. mean loss curves).
        :param quantiles:
            quantile levels used to compute quantile outputs
        :param post_processing:
            an object implementing the following protocol:
            #mean_curve(curves, weights)
            #weighted_quantile_curve(curves, weights, quantile)
            #quantile_curve(curves, quantile)
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
            calculators.exposure_statistics(
                [self._normalize_curves(curves) for curves in curve_matrix],
                self.maps.poes, weights, quantiles, post_processing))
        elt = sum((out.event_loss_table for out in outputs),
                  collections.Counter())

        if self.insured_losses:
            loss_curves = [out.insured_curves for out in outputs]
            (mean_insured_curves, mean_average_insured_losses, _,
             quantile_insured_curves, quantile_average_insured_losses, _) = (
                calculators.exposure_statistics(
                    [self._normalize_curves(curves)
                     for curves
                     in numpy.array(loss_curves).transpose(1, 0, 2, 3)],
                    [], weights, quantiles, post_processing))
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


@registry.add('classical_bcr')
class ClassicalBCR(Workflow):
    def __init__(self,
                 vulnerability_functions_orig,
                 vulnerability_functions_retro,
                 lrem_steps_per_interval,
                 interest_rate, asset_life_expectancy):
        self.vulnerability_functions = vulnerability_functions_orig
        self.assets = None  # set a __call__ time
        self.interest_rate = interest_rate
        self.asset_life_expectancy = asset_life_expectancy
        self.curves_orig = dict(
            (loss_type,
             calculators.ClassicalLossCurve(vf, lrem_steps_per_interval))
            for loss_type, vf in vulnerability_functions_orig.items())
        self.curves_retro = dict(
            (loss_type,
             calculators.ClassicalLossCurve(vf, lrem_steps_per_interval))
            for loss_type, vf in vulnerability_functions_retro.items())

    def __call__(self, loss_type, assets, hazard):
        self.assets = assets

        original_loss_curves = self.curves_orig[loss_type](hazard)
        retrofitted_loss_curves = self.curves_retro[loss_type](hazard)

        eal_original = [
            scientific.average_loss(losses, poes)
            for losses, poes in original_loss_curves]

        eal_retrofitted = [
            scientific.average_loss(losses, poes)
            for losses, poes in retrofitted_loss_curves]

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
    def __init__(self,
                 vulnerability_functions_orig,
                 vulnerability_functions_retro,
                 time_span, tses, loss_curve_resolution,
                 interest_rate, asset_life_expectancy):
        self.vulnerability_functions = vulnerability_functions_orig
        self.assets = None  # set a __call__ time
        self.interest_rate = interest_rate
        self.asset_life_expectancy = asset_life_expectancy
        self.vf_orig = vulnerability_functions_orig
        self.vf_retro = vulnerability_functions_retro
        self.curves = calculators.EventBasedLossCurve(
            time_span, tses, loss_curve_resolution)

    def __call__(self, loss_type, assets, gmfs, epsilons, event_ids):
        self.assets = assets
        original_loss_curves = self.curves(
            self.vf_orig[loss_type].apply_to(gmfs, epsilons))
        retrofitted_loss_curves = self.curves(
            self.vf_retro[loss_type].apply_to(gmfs, epsilons))

        eal_original = [
            scientific.average_loss(losses, poes)
            for losses, poes in original_loss_curves]

        eal_retrofitted = [
            scientific.average_loss(losses, poes)
            for losses, poes in retrofitted_loss_curves]

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
    def __init__(self, vulnerability_functions, insured_losses):
        self.vulnerability_functions = vulnerability_functions
        self.insured_losses = insured_losses

    def __call__(self, loss_type, assets, ground_motion_values, epsilons):
        values = numpy.array([a.value(loss_type) for a in assets])

        loss_ratio_matrix = self.vulnerability_functions[loss_type].apply_to(
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

        return (assets, loss_ratio_matrix, aggregate_losses,
                insured_loss_matrix, insured_losses)


@registry.add('scenario_damage')
class Damage(Workflow):
    def __init__(self, fragility_functions):
        # NB: we call the fragility_functions vulnerability_functions
        # for API compatibility
        self.vulnerability_functions = fragility_functions

    def __call__(self, loss_type, assets, gmfs, _epsilons=None):
        """
        :param loss_type: the string 'damage'
        :param assets: a list of N assets of the same taxonomy
        :param gmfs: an array of N x R elements
        :returns: an array of N assets and an array of N x R x D elements

        where N is the number of points, R the number of realizations
        and D the number of damage states.
        """
        ffs = self.vulnerability_functions['damage']
        outs = numpy.array(
            [[scientific.scenario_damage(ffs, gmv) for gmv in gmvs]
             for gmvs in gmfs])
        return assets, outs


# NB: the approach used here relies on the convention of having the
# names of the arguments of the workflow class to be equal to the
# names of the parameter in the oqparam object. This is view as a
# feature, since it forces people to be consistent with the names,
# in the spirit of the 'convention over configuration' philosophy
def get_workflow(oqparam, **extra):
    """
    Return an instance of the correct workflow class, depending on the
    attribute `calculation_mode` of the object `oqparam`.

    :param oqparam:
        an object containing the parameters needed by the workflow class
    :param extra:
        extra parameters to pass to the workflow class
    """
    workflow_class = registry[oqparam.calculation_mode]
    # arguments needed to instantiate the workflow class
    argnames = inspect.getargspec(workflow_class.__init__).args[1:]
    # arguments extracted from oqparam
    known_args = vars(oqparam)
    all_args = {}
    for argname in argnames:
        if argname in known_args:
            all_args[argname] = known_args[argname]
    all_args.update(extra)
    return workflow_class(**all_args)


class RiskInput(object):
    """
    Contains all the assets and hazard values associated to a given
    imt and site.
    """
    def __init__(self, imt, site_id, hazard, assets):
        self.imt = imt
        self.site_id = site_id
        self.hazard = hazard
        self.assets_by_taxo = collections.defaultdict(list)
        for asset in assets:
            self.assets_by_taxo[asset.taxonomy].append(asset)
        self.weight = len(assets)

    @property
    def taxonomy(self):
        """
        Return the taxonomy associated to the assets in the risk input
        object, if it is unique; raise a ValueError otherwise.
        """
        num_taxonomies = len(self.assets_by_taxo)
        if num_taxonomies == 0:
            raise ValueError('The risk input object has no assets!')
        elif num_taxonomies > 1:
            raise ValueError('The risk input object has more than one '
                             'taxonomy: %s' % self.assets_by_taxo.keys())
        return self.assets_by_taxo.values()[0][0].taxonomy

    def get_assets(self, taxonomy=None):
        """Return the assets, if there is a single taxonomy"""
        return self.assets_by_taxo[taxonomy or self.taxonomy]

    def get_hazards(self, taxonomy=None):
        """
        Return the underlying hazard as a list of N repeated arrays,
        where N is the number of assets
        """
        return [self.hazard] * len(self.get_assets(taxonomy))

    def get_epsilons(self, taxonomy=None):
        """
        Return the epsilons associated to the underlying assets as
        a numpy array of N x E elements, where N is the number of assets
        and E the number of events.
        """
        return [asset.epsilons for asset in self.get_assets(taxonomy)]


class RiskModel(collections.Mapping):
    """
    A container (imt, taxonomy) -> workflow
    """
    def __init__(self, workflows, damage_states=None):
        self.damage_states = damage_states  # not None for damage calculations
        self._workflows = workflows

    def __getitem__(self, imt_taxo):
        return self._workflows[imt_taxo]

    def __iter__(self):
        return iter(sorted(self._workflows))

    def __len__(self):
        return len(self._workflows)

    def gen_outputs(self, riskinputs):
        """
        Yield the output generated by each risk input and loss type
        """
        for (imt, taxonomy), workflow in self.iteritems():
            for ri in riskinputs:
                if imt == ri.imt and taxonomy in ri.assets_by_taxo:
                    assets = ri.get_assets(taxonomy)
                    hazards = ri.get_hazards(taxonomy)
                    epsilons = ri.get_epsilons(taxonomy)
                    for loss_type in workflow.loss_types:
                        yield loss_type, workflow(
                            loss_type, assets, hazards, epsilons)
