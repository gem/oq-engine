# -*- coding: utf-8 -*-

# Copyright (c) 2013, GEM Foundation.
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

import collections
import numpy
from scipy import interpolate

from openquake.risklib import calculators, utils, scientific


#: A calculation unit a risklib.workflow, a getter that
#: retrieves the data to work on, and the type of losses we are considering
CalculationUnit = collections.namedtuple(
    'CalculationUnit',
    'loss_type workflow getter')


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
                 values,
                 deductibles=None,
                 insurance_limits=None,
                 retrofitting_values=None):
        """
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
        self.values = values
        self.retrofitting_values = retrofitting_values
        self.deductibles = deductibles
        self.insurance_limits = insurance_limits

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


class Classical(object):
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
    :attr mean_maps:
       A numpy array with P mean loss maps. Shape: (P, N)
    :attr mean_fractions:
       A numpy array with F mean fractions, where F is the number of PoEs
       used for disaggregation. Shape: (F, N)
    :attr quantile_curves:
       A numpy array with Q quantile curves (Q = number of quantiles).
       Shape: (Q, N, 2, R)
    :attr quantile_maps:
       A numpy array with Q quantile maps shaped (Q, P, N)
    :attr quantile_fractions:
       A numpy array with Q quantile maps shaped (Q, F, N)
    """

    Output = collections.namedtuple(
        'Output',
        'assets loss_curves loss_maps loss_fractions')

    StatisticalOutput = collections.namedtuple(
        'StatisticalOutput',
        'assets mean_curves mean_maps mean_fractions quantile_curves '
        'quantile_maps quantile_fractions')

    def __init__(self,
                 vulnerability_function,
                 lrem_steps_per_interval,
                 conditional_loss_poes,
                 poes_disagg):
        """
        :param float poes_disagg:
            Probability of Exceedance levels used for disaggregate losses by
            taxonomy.

        See :func:`openquake.risklib.scientific.classical` for a description
        of the other parameters.
        """
        self.curves = calculators.ClassicalLossCurve(
            vulnerability_function, lrem_steps_per_interval)
        self.maps = calculators.LossMap(conditional_loss_poes)
        self.fractions = calculators.LossMap(poes_disagg)

        # needed to compute statistics
        self._loss_curves = None
        self._assets = None

    def __call__(self, data, calc_monitor=None):
        """
        A generator of :class:`openquake.risklib.workflows.Classical.Output`
        instances.

        :param data:
           an iterator over tuples with form (hid, assets, curves) where
           at each iteration a realization of hazard data is considered,
           hid identifies the id of the hazard realization, assets is an
           iterator over N assets, and curves is an iterator over N hazard
           curves.

        :param calc_monitor:
           a context manager the user can provide to log/monitor each
           single output computation.

        :NOTE: this function will collect all the loss curves as a
        side effect in the field `_loss_curves` (if the number of realizations
        is bigger than 1).
        """
        loss_curves = []

        monitor = calc_monitor or DummyMonitor()

        for hid, assets, hazard_curves in data:
            with monitor:
                curves = self.curves(hazard_curves)
                maps = self.maps(curves)
                fractions = self.fractions(curves)

                loss_curves.append(curves)
                self._assets = assets

                yield hid, self.Output(assets, curves, maps, fractions)

        if len(loss_curves) > 1:
            self._loss_curves = numpy.array(loss_curves).transpose(1, 0, 2, 3)

    def statistics(self, weights, quantiles, post_processing):
        """
        :returns:
            a :class:`openquake.risklib.workflows.Classical.StatisticalOutput`
            instance holding statistical outputs (e.g. mean loss curves).
        :param weights:
            a collection of weights associated with each realization, to
            allow the user to compute weighted means, weighted quantiles, etc.
        :param quantiles:
            quantile levels used to compute quantile outputs
        :param post_processing:
            an object implementing the following protocol:
            #mean_curve(curves, weights)
            #weighted_quantile_curve(curves, weights, quantile)
            #quantile_curve(curves, quantile)
        """
        if self._loss_curves is None:
            return

        curve_resolution = self._loss_curves.shape[3]

        mean_curves = numpy.zeros((0, 2, curve_resolution))
        mean_maps = numpy.zeros((len(self.maps.poes), 0))
        mean_fractions = numpy.zeros((len(self.fractions.poes), 0))
        quantile_curves = numpy.zeros((len(quantiles), 0, 2, curve_resolution))
        quantile_maps = numpy.zeros((len(quantiles), len(self.maps.poes), 0))
        quantile_fractions = numpy.zeros(
            (len(quantiles), len(self.fractions.poes), 0))

        # for each asset get all the loss curves and compute per asset
        # statistics
        for loss_ratio_curves in self._loss_curves:
            # get the loss ratios only from the first curve
            loss_ratios, _poes = loss_ratio_curves[0]
            curves_poes = [poes for _losses, poes in loss_ratio_curves]

            _mean_curve, _quantile_curves, _mean_maps, _quantile_maps = (
                calculators.asset_statistics(
                    loss_ratios, curves_poes,
                    quantiles, weights, self.maps.poes, post_processing))

            # compute also mean and quantile loss fractions
            _mean_fractions, _quantile_fractions = (
                calculators.asset_statistic_fractions(
                    self.fractions.poes, _mean_curve, _quantile_curves))

            mean_curves = numpy.vstack(
                (mean_curves, _mean_curve[numpy.newaxis, :]))
            mean_maps = numpy.hstack((mean_maps, _mean_maps[:, numpy.newaxis]))
            mean_fractions = numpy.hstack(
                (mean_fractions, _mean_fractions[:, numpy.newaxis]))
            quantile_curves = numpy.hstack(
                (quantile_curves, _quantile_curves[:, numpy.newaxis]))
            quantile_maps = numpy.dstack(
                (quantile_maps, _quantile_maps[:, :, numpy.newaxis]))
            quantile_fractions = numpy.dstack(
                (quantile_fractions, _quantile_fractions[:, :, numpy.newaxis]))

        return self.StatisticalOutput(
            self._assets,
            mean_curves, mean_maps,
            mean_fractions, quantile_curves, quantile_maps, quantile_fractions)


class ProbabilisticEventBased(object):
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

    :attr insured_curves:
      a numpy array of N insured loss curves, shaped (N, 2, R)

    :attr loss_maps:
      a numpy array of P elements holding N loss maps where P is the
      number of `conditional_loss_poes` considered. Shape: (P, N)

    The statistical outputs are stored into
    :class:`.ProbabilisticEventBased.StatisticalOutput`.
    See :class:`openquake.risklib.workflows.Classical.StatisticalOutput` for
    more details.
    """
    Output = collections.namedtuple(
        'Output',
        'assets loss_matrix loss_curves insured_curves loss_maps')

    StatisticalOutput = collections.namedtuple(
        'StatisticalOutput',
        'assets mean_curves mean_maps quantile_curves quantile_maps')

    def __init__(
            self,
            vulnerability_function,
            seed, asset_correlation,
            time_span, tses,
            loss_curve_resolution,
            conditional_loss_poes,
            insured_losses=False):
        """
        See :func:`openquake.risklib.scientific.event_based` for a description
        of the input parameters
        """
        self.assets = None
        self._loss_curves = None
        self.event_loss_table = collections.Counter()

        self.losses = calculators.ProbabilisticLoss(
            vulnerability_function, seed, asset_correlation)
        self.curves = calculators.EventBasedLossCurve(
            time_span, tses, loss_curve_resolution)
        self.maps = calculators.LossMap(conditional_loss_poes)
        self.event_loss = calculators.EventLossTable()

        self.insured_losses = insured_losses

    def __call__(self, loss_type, data, monitor=None):
        """
        A generator of
        :class:`openquake.risklib.workflows.ProbabilisticEventBased.Output`
        instances.

        :param str loss_type: the loss type considered

        :param data:
           an iterator over tuples with form (hid, assets, (gmvs, events))
           where at each iteration a realization of hazard data is considered,
           hid identifies the id of the hazard realization, assets is an
           iterator over N assets, events is an array of E event ids,
           gmvs is an array N x E ground motion values.

        :param calc_monitor:
           a context manager the user can provide to log/monitor each
           single output computation.

        :NOTE: this function will collect all the loss curves as a
        side effect in the field `_loss_curves` (if the number of realizations
        is bigger than 1).
        """

        monitor = monitor or DummyMonitor()
        loss_curves = []

        for hid, assets, (ground_motion_values, rupture_ids) in data:
            self.assets = assets

            with monitor:
                loss_matrix = self.losses(ground_motion_values)

                curves = self.curves(loss_matrix)
                loss_curves.append(curves)

                values = utils.numpy_map(lambda a: a.value(loss_type),
                                         assets)
                maps = self.maps(curves)

                self.event_loss_table += self.event_loss(
                    loss_matrix.transpose() * values, rupture_ids)

                if self.insured_losses and loss_type != 'fatalities':
                    deductibles = map(lambda a: a.deductible(loss_type),
                                      assets)
                    limits = map(lambda a: a.insurance_limit(loss_type),
                                 assets)

                    insured_curves = self.curves(
                        utils.numpy_map(
                            scientific.insured_losses,
                            loss_matrix, deductibles, limits))
                else:
                    insured_curves = None

            yield hid, self.Output(
                assets, loss_matrix, curves, insured_curves, maps)

        if len(loss_curves) > 1:
            self._loss_curves = numpy.array(loss_curves).transpose(1, 0, 2, 3)

    def statistics(self, weights, quantiles, post_processing):
        """
        :returns:
            a :class:`.ProbabilisticEventBased.StatisticalOutput`
            instance holding statistical outputs (e.g. mean loss curves).
        :param weights:
            a collection of weights associated with each realization, to
            allow the user to compute weighted means, weighted quantiles, etc.
        :param quantiles:
            quantile levels used to compute quantile outputs
        :param post_processing:
            an object implementing the following protocol:
            #mean_curve(curves, weights)
            #weighted_quantile_curve(curves, weights, quantile)
            #quantile_curve(curves, quantile)
        """
        if self._loss_curves is None:
            return

        curve_resolution = self._loss_curves.shape[3]
        mean_curves = numpy.zeros((0, 2, curve_resolution))
        mean_maps = numpy.zeros((len(self.maps.poes), 0))
        quantile_curves = numpy.zeros((len(quantiles), 0, 2, curve_resolution))
        quantile_maps = numpy.zeros((len(quantiles), len(self.maps.poes), 0))

        for curves in self._loss_curves:
            loss_ratios, curves_poes = self._normalize_curves(curves)
            _mean_curve, _quantile_curves, _mean_maps, _quantile_maps = (
                calculators.asset_statistics(
                    loss_ratios, curves_poes,
                    quantiles, weights, self.maps.poes, post_processing))

            mean_curves = numpy.vstack(
                (mean_curves, _mean_curve[numpy.newaxis, :]))
            mean_maps = numpy.hstack((mean_maps, _mean_maps[:, numpy.newaxis]))
            quantile_curves = numpy.hstack(
                (quantile_curves, _quantile_curves[:, numpy.newaxis]))
            quantile_maps = numpy.dstack(
                (quantile_maps, _quantile_maps[:, :, numpy.newaxis]))

        return self.StatisticalOutput(
            self.assets, mean_curves, mean_maps,
            quantile_curves, quantile_maps)

    def _normalize_curves(self, curves):
        non_trivial_curves = [(losses, poes)
                              for losses, poes in curves if losses[-1] > 0]
        if not non_trivial_curves:  # no damage. all trivial curves
            loss_ratios, _poes = curves[0]
            curves_poes = [poes for _losses, poes in curves]
        else:  # standard case
            max_losses = [losses[-1]  # we assume non-decreasing losses
                          for losses, _poes in non_trivial_curves]
            reference_curve = non_trivial_curves[numpy.argmax(max_losses)]
            loss_ratios = reference_curve[0]
            curves_poes = [interpolate.interp1d(
                losses, poes, bounds_error=False, fill_value=0)(loss_ratios)
                for losses, poes in curves]
        return loss_ratios, curves_poes


class ClassicalBCR(object):
    def __init__(self,
                 vulnerability_function_orig,
                 vulnerability_function_retro,
                 lrem_steps_per_interval,
                 interest_rate, asset_life_expectancy):
        self.assets = None
        self.interest_rate = interest_rate
        self.asset_life_expectancy = asset_life_expectancy
        self.curves_orig = calculators.ClassicalLossCurve(
            vulnerability_function_orig,
            lrem_steps_per_interval)
        self.curves_retro = calculators.ClassicalLossCurve(
            vulnerability_function_retro,
            lrem_steps_per_interval)

    def __call__(self, loss_type, data, monitor=None):
        monitor = monitor or DummyMonitor()
        for hid, assets, orig, retro in data:
            self.assets = assets
            with monitor:
                original_loss_curves = self.curves_orig(orig)
                retrofitted_loss_curves = self.curves_retro(retro)

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

            yield hid, zip(eal_original, eal_retrofitted, bcr_results)


class ProbabilisticEventBasedBCR(object):
    def __init__(self,
                 vulnerability_function_orig,
                 seed_orig,
                 vulnerability_function_retro,
                 seed_retro,
                 asset_correlation,
                 time_span, tses, loss_curve_resolution,
                 interest_rate, asset_life_expectancy):
        self.assets = None
        self.interest_rate = interest_rate
        self.asset_life_expectancy = asset_life_expectancy
        self.losses_orig = calculators.ProbabilisticLoss(
            vulnerability_function_orig,
            seed_orig,
            asset_correlation)
        self.losses_retro = calculators.ProbabilisticLoss(
            vulnerability_function_retro,
            seed_retro,
            asset_correlation)
        self.curves = calculators.EventBasedLossCurve(
            time_span, tses, loss_curve_resolution)

    def __call__(self, loss_type, data, monitor=None):
        monitor = monitor or DummyMonitor()
        for hid, assets, (orig, _), (retro, __) in data:
            self.assets = assets
            with monitor:
                original_loss_curves = self.curves(self.losses_orig(orig))
                retrofitted_loss_curves = self.curves(self.losses_retro(retro))

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

            yield hid, zip(eal_original, eal_retrofitted, bcr_results)


class Scenario(object):
    def __init__(self,
                 vulnerability_function,
                 seed, asset_correlation,
                 insured_losses):
        self.losses = calculators.ProbabilisticLoss(
            vulnerability_function, seed, asset_correlation)
        self.insured_losses = insured_losses

    def __call__(self, loss_type, data, monitor=None):
        hid, assets, gmvs = data.next()
        values = numpy.array([a.value(loss_type) for a in assets])

        with monitor or DummyMonitor():
            loss_ratio_matrix = self.losses(gmvs)
            aggregate_losses = numpy.sum(
                loss_ratio_matrix.transpose() * values, axis=1)

            if self.insured_losses and loss_type != "fatalities":
                deductibles = utils.numpy_map(
                    lambda a: a.deductible(loss_type), assets)
                limits = utils.numpy_map(
                    lambda a: a.insurance_limit(loss_type), assets)
                insured_loss_ratio_matrix = utils.numpy_map(
                    scientific.insured_losses,
                    loss_ratio_matrix,
                    deductibles,
                    limits)

                insured_loss_matrix = (
                    insured_loss_ratio_matrix.transpose() * values)

                insured_losses = numpy.array(insured_loss_matrix).sum(axis=1)
            else:
                insured_loss_matrix = None
                insured_losses = None

        return (hid, assets, loss_ratio_matrix, aggregate_losses,
                insured_loss_matrix, insured_losses)


class DummyMonitor(object):
    """
    This class makes it easy to disable the monitoring
    in client code. Disabling the monitor can improve the performance.
    """
    def __enter__(self):
        return self

    def __exit__(self, _etype, _exc, _tb):
        pass
