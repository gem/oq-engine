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
    def __init__(self, values, deductibles=None, insured_limits=None):
        self.values = values
        self.deductibles = deductibles
        self.insured_limits = insured_limits

    def value(self, loss_type):
        return self.values[loss_type]

    def deductible(self, loss_type):
        return self.deductibles[loss_type]

    def insured_limit(self, loss_type):
        return self.insured_limits[loss_type]


class Classical(object):
    """
    Classical PSHA-Based Workflow.

    Compute loss curves, loss maps, loss fractions for each
    realization.

    Then, (if more than one realization is given) it computes mean and
    quantiles loss curves, maps and fractions.
    """

    """
    Output:

    Hold the results computed in one calculation unit for N assets.

    :attr assets:
      a list of N assets the outputs refer to

    :attr loss_curves:
      a list of N loss curves (where a loss curve is a 2-tuple losses/poes)

    :attr loss_maps:
      a list of P elements holding list of N loss map values where P is the
      number of `conditional_loss_poes`

    :attr loss_fractions:
      a list of D elements holding list of N loss map values where D is the
      number of `poes_disagg`
    """

    Output = collections.namedtuple(
        'Output',
        'assets loss_curves loss_maps loss_fractions')

    """
    The statistical outputs computed by the classical calculator.

    :attr assets:
      a list of N assets the outputs refer to

    :attr list mean_curves:
       Holds N mean loss curves. A loss curve is a 2-ple losses/poes
    :attr list mean_maps:
       Holds P lists, where each of them holds N mean map value
       (P = number of PoEs)
    :attr mean_fractions:
       Holds F lists, where each of them holds N loss fraction value
       (F = number of disagg PoEs)
    :attr list quantile_curves:
       Holds Q lists, where each of them has N quantile loss curves
       (Q = number of quantiles)
    :attr list quantile_maps:
       Holds Q lists, where each of them has P lists. Each of the latter
       holds N quantile map value
    :attr list quantile_fractions:
       Holds Q lists, where each of them has F lists. Each of the latter
       holds N quantile loss fraction value
    """
    StatisticalOutput = collections.namedtuple(
        'StatisticalOutput',
        'assets mean_curves mean_maps mean_fractions quantile_curves '
        'quantile_maps quantile_fractions')

    def __init__(self,
                 vulnerability_function,
                 lrem_steps_per_interval,
                 conditional_loss_poes,
                 poes_disagg):
        self.curves = calculators.ClassicalLossCurve(
            vulnerability_function, lrem_steps_per_interval)
        self.maps = calculators.LossMap(conditional_loss_poes)
        self.fractions = calculators.LossMap(poes_disagg)

        # needed to compute statistics
        self._loss_curves = None
        self._assets = None

    def __call__(self, data, calc_monitor=None):
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
        if self._loss_curves is None:
            return

        ret = []

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
                    self.fractions.poes, _mean_curve,
                    _quantile_curves, quantiles))

            ret.append((_mean_curve, _mean_maps, _mean_fractions,
                        _quantile_curves, _quantile_maps, _quantile_fractions))

        # zip all the per-asset statistics to have per-type statistics
        (mean_curves, mean_maps, mean_fractions,
         quantile_curves, quantile_maps, quantile_fractions) = zip(*ret)

        mean_curves = numpy.array(mean_curves)

        # transpose maps and fractions in order to end up with P x N
        # matrix of loss map values, where P is the number of poes and
        # N is the number of assets
        mean_maps = numpy.array(mean_maps).transpose()
        mean_fractions = numpy.array(mean_fractions).transpose()

        # swap the first and the second dimension of quantile curves
        # to end up with a matrix with Q x N Loss curves where a Q is
        # the number of quantiles
        quantile_curves = numpy.array(quantile_curves).transpose(1, 0, 2, 3)

        # swap the first and the third dimension of quantile maps to
        # end up with a matrix of Q x P x N loss map values
        quantile_maps = numpy.array(quantile_maps).transpose(1, 2, 0)

        quantile_fractions = numpy.array(quantile_fractions).transpose(
            2, 1, 0)

        return self.StatisticalOutput(
            self._assets,
            mean_curves, mean_maps,
            mean_fractions, quantile_curves, quantile_maps, quantile_fractions)


class ProbabilisticEventBased(object):
    """
    Implements the probabilistic event based workflow
    """

    """
    Record the results computed in one calculation units for N assets.

    :attr assets:
      a list of N assets the outputs refer to

    :attr loss_matrix:
      an array of losses with dimension N x R
      (where R is the number of ruptures)

    :attr loss_curves:
      a list of N loss curves (where a loss curve is a 2-tuple losses/poes)

    :attr insured_curves:
      a list of N insured loss curves

    :attr loss_maps:
      a list of P elements holding list of N loss map values where P is the
      number of `conditional_loss_poes`
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
            insured_losses):
        self.assets = None
        self._loss_curves = None
        self.event_loss_table = collections.Counter()

        self.losses = calculators.ProbabilisticLoss(
            vulnerability_function, seed, asset_correlation)
        self.curves = calculators.EventBasedLossCurve(
            time_span, tses, loss_curve_resolution)
        self.maps = calculators.LossMap(conditional_loss_poes)
        self.insured_losses = insured_losses
        self.event_loss = calculators.EventLossTable()

    def __call__(self, loss_type, data, monitor=None):
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
        if self._loss_curves is None:
            return

        ret = []

        for curves in self._loss_curves:
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
                    losses, poes,
                    bounds_error=False, fill_value=0)(loss_ratios)
                    for losses, poes in curves]
            mean_curve, quantile_curves, mean_maps, quantile_maps = (
                calculators.asset_statistics(
                    loss_ratios, curves_poes,
                    quantiles, weights, self.maps.poes, post_processing))

            ret.append((mean_curve, mean_maps, quantile_curves, quantile_maps))

        (mean_curves, mean_maps, quantile_curves, quantile_maps) = zip(*ret)
        # now all the lists keep N items

        # transpose maps and fractions to have P/F/Q items of N-sized lists
        mean_maps = numpy.array(mean_maps).transpose()

        if (len(quantile_curves) and len(quantile_curves[0])):
            quantile_curves = numpy.array(
                quantile_curves).transpose(1, 0, 2, 3)
        else:
            quantile_curves = None

        if (len(quantile_maps) and len(quantile_maps[0])):
            quantile_maps = numpy.array(quantile_maps).transpose(2, 1, 0)
        else:
            quantile_maps = None

        return self.StatisticalOutput(
            self.assets, mean_curves, mean_maps,
            quantile_curves, quantile_maps)


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
