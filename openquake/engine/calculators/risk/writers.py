# -*- coding: utf-8 -*-

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

"""DB writing functionality for Risk calculators."""

import collections
import itertools
from openquake.risklib import scientific
from openquake.engine.db import models


def loss_map(
        loss_type, loss_map_id, assets, losses, std_devs=None, absolute=False):
    """
    Create :class:`openquake.engine.db.models.LossMapData`

    :param int loss_map_id:
        The ID of the output container.
    :param list assets:
        A list of instances of :class:`openquake.engine.db.models.ExposureData`
    :param loss:
        Loss values to be written.
    :param float std_devs:
        Standard devations on each loss.
    :param absolute:
        False if the provided losses are loss ratios
    """

    for i, asset in enumerate(assets):
        loss = losses[i]
        if std_devs is not None:
            std_dev = std_devs[i]
        else:
            std_dev = None

        if not absolute:
            loss *= asset.value(loss_type)
            if std_devs is not None:
                std_dev *= asset.value(loss_type)

        models.LossMapData.objects.create(
            loss_map_id=loss_map_id,
            asset_ref=asset.asset_ref,
            value=loss,
            std_dev=std_dev,
            location=asset.site)


def bcr_distribution(loss_type, bcr_distribution_id, assets, bcr_data):
    """
    Create a new :class:`openquake.engine.db.models.BCRDistributionData` from
    `asset_output` and links it to the output container identified by
    `bcr_distribution_id`.

    :param int bcr_distribution_id:
        The ID of :class:`openquake.engine.db.models.BCRDistribution` instance
        that holds the BCR map.

    :param assets:
        A list of instance of :class:`openquake.engine.db.models.ExposureData`

    :param tuple bcr_data: a 3-tuple with
      1) eal_original: expected annual loss in the original model
      2) eal_retrofitted: expected annual loss in the retrofitted model
      3) bcr: Benefit Cost Ratio parameter.
    """
    for asset, (eal_original, eal_retrofitted, bcr) in zip(assets, bcr_data):
        models.BCRDistributionData.objects.create(
            bcr_distribution_id=bcr_distribution_id,
            asset_ref=asset.asset_ref,
            average_annual_loss_original=eal_original * asset.value(loss_type),
            average_annual_loss_retrofitted=(eal_retrofitted *
                                             asset.value(loss_type)),
            bcr=bcr,
            location=asset.site)


def loss_curve(loss_type, loss_curve_id, assets, curve_data):
    """
    Store :class:`openquake.engine.db.models.LossCurveData`
    where the
    :class:`openquake.engine.db.models.LossCurve` output container is
    identified by `loss_curve_id` and has type `loss_curve` (produced by
    a classical calculation).

    :param str loss_type:
        The loss type of the curve
    :param int loss_curve_id:
        The ID of the output container.
    :param assets:
        A list of N :class:`openquake.engine.db.models.ExposureData` instances
    :param tuple curve_data:
        A tuple of the form (curves, averages) holding a numpy array with N
        loss curve data and N average loss value associated with the curve
    """

    curves, averages = curve_data
    for asset, (losses, poes), average in itertools.izip(
            assets, curves, averages):
        models.LossCurveData.objects.create(
            loss_curve_id=loss_curve_id,
            asset_ref=asset.asset_ref,
            location=asset.site,
            poes=poes,
            loss_ratios=losses,
            asset_value=asset.value(loss_type),
            average_loss_ratio=average,
            stddev_loss_ratio=None)


def event_loss_curve(loss_type, loss_curve_id, assets, curve_data):
    """
    Store :class:`openquake.engine.db.models.LossCurveData`
    where the
    :class:`openquake.engine.db.models.LossCurve` output container is
    identified by `loss_curve_id` and the output type is `event_loss_curve`
    .

    :param str loss_type:
        The loss type of the curve
    :param int loss_curve_id:
        The ID of the output container.
    :param assets:
        A list of N :class:`openquake.engine.db.models.ExposureData` instances
    :param tuple curve_data:
        A tuple of the form (curves, averages, stddevs) holding a numpy array
        loss curve data and N average loss value associated with the curve
    """

    curves, averages, stddevs = curve_data
    for asset, (losses, poes), average, stddev in itertools.izip(
            assets, curves, averages, stddevs):
        models.LossCurveData.objects.create(
            loss_curve_id=loss_curve_id,
            asset_ref=asset.asset_ref,
            location=asset.site,
            poes=poes,
            loss_ratios=losses,
            asset_value=asset.value(loss_type),
            average_loss_ratio=average,
            stddev_loss_ratio=stddev)


def loss_fraction(loss_type, loss_fraction_id, assets, values, fractions):
    """
    Create, save and return an instance of
    :class:`openquake.engine.db.models.LossFractionData` associated
    with `loss_fraction_id`, `value`, `location` and `absolute_loss`
    :param int loss_fraction_id:
       an ID to an output container instance
       of type :class:`openquake.engine.db.models.LossFraction
    :param list values:
       A list of value representing the fraction. In case of
       disaggregation by taxonomy it is a taxonomy string.
    :param assets: the assets, the fractions refer to
    :param absolute_losses:
       the absolute loss contributions of `values` in `assets`
    """
    for asset, value, fraction in itertools.izip(assets, values, fractions):
        models.LossFractionData.objects.create(
            loss_fraction_id=loss_fraction_id,
            value=value,
            location=asset.site,
            absolute_loss=fraction * asset.value(loss_type))


###
### Damage Distributions
###

def damage_distribution(assets, fraction_matrix, dmg_state_ids):
    """
    Save the damage distribution for a given asset.
    :param assets:
       a list of ExposureData instances
    :param fraction_matrix:
       numpy array with the damage fractions for each asset
    :param dmg_state_ids:
       a list of  IDs of instances of
       :class:`openquake.engine.db.models.DmgState` ordered by `lsi`
    """
    for fractions, asset in zip(fraction_matrix, assets):
        fractions *= asset.number_of_units
        means, stds = scientific.mean_std(fractions)

        for mean, std, dmg_state_id in zip(means, stds, dmg_state_ids):
            models.DmgDistPerAsset.objects.create(
                dmg_state_id=dmg_state_id,
                mean=mean, stddev=std, exposure_data=asset)


def damage_distribution_per_taxonomy(fractions, dmg_state_ids, taxonomy):
    """
    Save the damage distribution for a given taxonomy, by summing over
    all assets.

    :param fractions: numpy array with the damage fractions
    :param dmg_state_ids:
       a list of  IDs of instances of
       :class:`openquake.engine.db.models.DmgState` ordered by `lsi`
    :param str: the taxonomy string
    """
    means, stddevs = scientific.mean_std(fractions)
    for dmg_state_id, mean, stddev in zip(dmg_state_ids, means, stddevs):
        models.DmgDistPerTaxonomy.objects.create(
            dmg_state_id=dmg_state_id,
            mean=mean, stddev=stddev, taxonomy=taxonomy)


def total_damage_distribution(fractions, dmg_state_ids):
    """
    Save the total distribution, by summing over all assets and taxonomies.

    :param fractions: numpy array with the damage fractions
    :param dmg_state_ids:
       a list of  IDs of instances of
       :class:`openquake.engine.db.models.DmgState` ordered by `lsi`
    """
    means, stds = scientific.mean_std(fractions)
    for mean, std, dmg_state in zip(means, stds, dmg_state_ids):
        models.DmgDistTotal.objects.create(
            dmg_state_id=dmg_state, mean=mean, stddev=std)


# A namedtuple that identifies an Output object in a risk calculation
# E.g. A Quantile LossCurve associated with a specific hazard output is
# OutputKey(output_type="loss_curve",
#           loss_type="structural",
#           hazard_output_id=foo,
#           poe=None,
#           quantile=bar,
#           statistics="quantile",
#           variable=None,
#           insured=False)

OutputKey = collections.namedtuple('OutputKey', [
    'output_type',  # as in :class:`openquake.engine.db.models.Output`
    'loss_type',  # as in risk output outputdict
    'hazard_output_id',  # as in risk output outputdict
    'poe',  # for loss map and classical loss fractions
    'quantile',  # for quantile outputs
    'statistics',  # as in risk output outputdict
    'variable',  # for disaggregation outputs
    'insured',  # as in :class:`openquake.engine.db.models.LossCurve`
])


class OutputDict(dict):
    """
    A dict keying OutputKey instances to database ID, with convenience
    setter and getter methods to manage Output outputdict.

    It also automatically links an Output type with its specific
    writer.

    Risk Calculators create OutputDict instances with Output IDs keyed
    by OutputKey instances.

    Worker tasks compute results than get the proper writer and use it
    to actually write the results
    """

    def get(self,
            output_type=None, loss_type=None, hazard_output_id=None, poe=None,
            quantile=None, statistics=None, variable=None, insured=False):
        """
        Get the ID associated with the `OutputKey` instance built with the
        given kwargs.
        """
        return self[OutputKey(output_type, loss_type, hazard_output_id, poe,
                              quantile, statistics, variable, insured)]

    def with_args(self, **kwargs):
        clone = self.__class__(self)
        clone.kwargs = self.kwargs
        clone.kwargs.update(kwargs)
        return clone

    def __init__(self, *args, **kwargs):
        super(OutputDict, self).__init__(*args, **kwargs)
        self.kwargs = dict()

    def write(self, *args, **kwargs):
        """
        1) Get the ID associated with the `OutputKey` instance built with
        the given kwargs.
        2) Get a writer function from the `writers` module with
        function name given by the `output_type` argument.
        3) Call such function with the given positional arguments.
        """
        kwargs.update(self.kwargs)
        output_id = self.get(**kwargs)
        globals().get(kwargs['output_type'])(
            kwargs.pop('loss_type'), output_id, *args)

    def write_all(self, arg, values, items,
                  *initial_args, **initial_kwargs):
        """
        Call iteratively `write`.

        In each call, the keyword arguments are built by merging
        `initial_kwargs` with a dict storing the association between
        `arg` and the value taken iteratively from `values`. The
        positional arguments are built by chaining `initial_args` with
        a value taken iteratively from `items`.

        :param str arg: a keyword argument to be passed to `write`

        :param list values: a list of keyword argument values to be
        passed to `write`

        :param list items: a list of positional arguments to be passed
        to `write`
        """
        if not len(values) or not len(items):
            return
        for value, item in itertools.izip(values, items):
            kwargs = {arg: value}
            kwargs.update(initial_kwargs)
            args = list(initial_args) + [item]
            self.write(*args, **kwargs)

    def set(self, container):
        """Store an ID (got from `container`) keyed by a new
        `OutputKey` built with the attributes guessed on `container`

        :param container: a django model instance of an output
        container (e.g. a LossCurve)
        """
        hazard_output_id = getattr(container, "hazard_output_id")
        loss_type = getattr(container, "loss_type")
        poe = getattr(container, "poe", None)
        quantile = getattr(container, "quantile", None)
        statistics = getattr(container, "statistics", None)
        variable = getattr(container, "variable", None)
        insured = getattr(container, "insured", False)

        key = OutputKey(
            output_type=container.output.output_type,
            loss_type=loss_type,
            hazard_output_id=hazard_output_id,
            poe=poe,
            quantile=quantile,
            statistics=statistics,
            variable=variable,
            insured=insured)

        assert super(OutputDict, self).get(
            key, None) is None, "OutputDict can not be updated"

        self[key] = container.id

    def extend(self, output_list):
        for o in output_list:
            self.set(o)
        return self


class OutputBuilder(object):
    def __init__(self, calculator):
        self.calc = calculator

    def statistical_outputs(self, _loss_type):
        return OutputDict()

    def individual_outputs(self, _loss_type, _hazard_output):
        return OutputDict()


def combine_builders(builders):
    outputs = OutputDict()

    if not builders:
        return outputs

    a_builder = builders[0]
    hazard_outputs = a_builder.calc.rc.hazard_outputs()
    # now a special case for event_based_fr
    if a_builder.calc.rc.calculation_mode == 'event_based_fr':
        hos = []
        for ho in hazard_outputs:
            for rlz in ho.ses.lt_model:
                gmf = models.Gmf.objects.get(lt_realization=rlz)
                hos.append(gmf.output)
        hazard_outputs = hos

    for builder in builders:
        for loss_type in a_builder.calc.loss_types:
            if len(hazard_outputs) > 1:
                outputs.extend(builder.statistical_outputs(loss_type))

            for hazard in hazard_outputs:
                outputs.extend(builder.individual_outputs(loss_type, hazard))

    return outputs


class LossCurveMapBuilder(OutputBuilder):
    """
    Create output outputdict for Loss Curves, Insured Loss Curves and
    Loss Maps
    """
    LOSS_CURVE_TYPE = "loss_curve"

    def individual_outputs(self, loss_type, hazard_output):
        lc = [models.LossCurve.objects.create(
            hazard_output_id=hazard_output.id,
            loss_type=loss_type,
            output=models.Output.objects.create_output(
                self.calc.job,
                "loss curves. type=%s, hazard=%s" % (
                    loss_type, hazard_output.id), self.LOSS_CURVE_TYPE))]

        maps = [models.LossMap.objects.create(
            hazard_output_id=hazard_output.id,
            loss_type=loss_type,
            output=models.Output.objects.create_output(
                self.calc.job,
                "loss maps. type=%s poe=%s, hazard=%s" % (
                    loss_type, poe, hazard_output.id),
                "loss_map"), poe=poe)
                for poe in self.calc.rc.conditional_loss_poes or []]

        if loss_type != "fatalities" and self.calc.rc.insured_losses:
            ins = [
                models.LossCurve.objects.create(
                    insured=True,
                    loss_type=loss_type,
                    hazard_output=hazard_output,
                    output=models.Output.objects.create_output(
                        self.calc.job,
                        "insured loss curves. type=%s hazard %s" % (
                            loss_type, hazard_output),
                        self.LOSS_CURVE_TYPE))]
        else:
            ins = []

        return lc + maps + ins

    def statistical_outputs(self, loss_type):
        mean_loss_curve = [models.LossCurve.objects.create(
            output=models.Output.objects.create_output(
                job=self.calc.job,
                display_name='Mean Loss Curves. type=%s' % loss_type,
                output_type='loss_curve'),
            statistics='mean', loss_type=loss_type)]

        if loss_type != "fatalities" and self.calc.rc.insured_losses:
            mean_insured_loss_curve = [models.LossCurve.objects.create(
                output=models.Output.objects.create_output(
                    job=self.calc.job,
                    display_name='Mean Insured Curves. type=%s' % loss_type,
                    output_type='loss_curve'),
                statistics='mean', insured=True, loss_type=loss_type)]
        else:
            mean_insured_loss_curve = []

        quantile_loss_curves = []
        quantile_insured_loss_curves = []
        for quantile in self.calc.rc.quantile_loss_curves or []:
            quantile_loss_curves.append(models.LossCurve.objects.create(
                output=models.Output.objects.create_output(
                    job=self.calc.job,
                    display_name='%s Quantile Loss Curves. type=%s' % (
                        quantile, loss_type),
                    output_type='loss_curve'),
                statistics='quantile',
                quantile=quantile,
                loss_type=loss_type))
            if loss_type != "fatalities" and self.calc.rc.insured_losses:
                quantile_insured_loss_curves.append(
                    models.LossCurve.objects.create(
                        output=models.Output.objects.create_output(
                            job=self.calc.job,
                            display_name=(
                                '%s Quantile Insured Loss Curves. type=%s' % (
                                    quantile, loss_type)),
                            output_type='loss_curve'),
                        statistics='quantile',
                        insured=True,
                        quantile=quantile,
                        loss_type=loss_type))

        mean_loss_maps = []
        for poe in self.calc.rc.conditional_loss_poes or []:
            mean_loss_maps.append(models.LossMap.objects.create(
                output=models.Output.objects.create_output(
                    job=self.calc.job,
                    display_name="Mean Loss Map type=%s poe=%.4f" % (
                        loss_type, poe),
                    output_type="loss_map"),
                statistics="mean",
                loss_type=loss_type,
                poe=poe))

        quantile_loss_maps = []
        for quantile in self.calc.rc.quantile_loss_curves or []:
            for poe in self.calc.rc.conditional_loss_poes or []:
                name = "%.4f Quantile Loss Map type=%s poe=%.4f" % (
                    quantile, loss_type, poe)
                quantile_loss_maps.append(models.LossMap.objects.create(
                    output=models.Output.objects.create_output(
                        job=self.calc.job,
                        display_name=name,
                        output_type="loss_map"),
                    statistics="quantile",
                    quantile=quantile,
                    loss_type=loss_type,
                    poe=poe))

        return (mean_loss_curve + quantile_loss_curves +
                mean_loss_maps + quantile_loss_maps +
                mean_insured_loss_curve + quantile_insured_loss_curves)


class EventLossCurveMapBuilder(LossCurveMapBuilder):
    LOSS_CURVE_TYPE = "event_loss_curve"


class LossMapBuilder(OutputBuilder):
    def individual_outputs(self, loss_type, hazard_output):
        loss_maps = [models.LossMap.objects.create(
            output=models.Output.objects.create_output(
                self.calc.job, "Loss Map", "loss_map"),
            hazard_output=hazard_output,
            loss_type=loss_type)]

        if self.calc.rc.insured_losses:
            loss_maps.append(models.LossMap.objects.create(
                output=models.Output.objects.create_output(
                    self.calc.job, "Insured Loss Map", "loss_map"),
                hazard_output=hazard_output,
                loss_type=loss_type,
                insured=True))

        return loss_maps


class BCRMapBuilder(OutputBuilder):
    def individual_outputs(self, loss_type, hazard_output):
        return [models.BCRDistribution.objects.create(
                hazard_output=hazard_output,
                loss_type=loss_type,
                output=models.Output.objects.create_output(
                    self.calc.job,
                    "BCR Map. type=%s hazard=%s" % (loss_type, hazard_output),
                    "bcr_distribution"))]


class LossFractionBuilder(OutputBuilder):
    def individual_outputs(self, loss_type, hazard_output):
        variables = ["magnitude_distance", "coordinate"]

        loss_fractions = []
        if self.calc.sites_disagg:
            for variable in variables:
                name = ("loss fractions. type=%s variable=%s "
                        "hazard=%s" % (loss_type, hazard_output, variable))
                loss_fractions.append(
                    models.LossFraction.objects.create(
                        output=models.Output.objects.create_output(
                            self.calc.job, name, "loss_fraction"),
                        hazard_output=hazard_output,
                        loss_type=loss_type,
                        variable=variable))

        return loss_fractions


class ConditionalLossFractionBuilder(OutputBuilder):
    def statistical_outputs(self, loss_type):
        loss_fractions = []
        for poe in self.calc.rc.poes_disagg or []:
            loss_fractions.append(models.LossFraction.objects.create(
                variable="taxonomy",
                poe=poe,
                loss_type=loss_type,
                output=models.Output.objects.create_output(
                    job=self.calc.job,
                    display_name="Mean Loss Fractions. type=%s poe=%.4f" % (
                        loss_type, poe),
                    output_type="loss_fraction"),
                statistics="mean"))

        for quantile in self.calc.rc.quantile_loss_curves or []:
            for poe in self.calc.rc.poes_disagg or []:
                loss_fractions.append(models.LossFraction.objects.create(
                    variable="taxonomy",
                    poe=poe,
                    loss_type=loss_type,
                    output=models.Output.objects.create_output(
                        job=self.calc.job,
                        display_name=("%.4f Quantile Loss Fractions "
                                      "loss_type=%s poe=%.4f" % (
                                          quantile, loss_type, poe)),
                        output_type="loss_fraction"),
                    statistics="quantile",
                    quantile=quantile))

        return loss_fractions

    def individual_outputs(self, loss_type, hazard_output):
        loss_fractions = []

        for poe in self.calc.rc.poes_disagg or []:
            loss_fractions.append(models.LossFraction.objects.create(
                hazard_output_id=hazard_output.id,
                variable="taxonomy",
                loss_type=loss_type,
                output=models.Output.objects.create_output(
                    self.calc.job,
                    "loss fractions. type=%s poe=%s hazard=%s" % (
                        loss_type, poe, hazard_output.id),
                    "loss_fraction"),
                poe=poe))

        return loss_fractions
