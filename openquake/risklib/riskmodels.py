# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
import inspect
import functools
import numpy

from openquake.baselib.general import CallableDict
from openquake.baselib.hdf5 import ArrayWrapper
from openquake.hazardlib import valid
from openquake.risklib import utils, scientific

U32 = numpy.uint32
F32 = numpy.float32
registry = CallableDict()


def get_values(loss_type, assets, time_event=None):
    """
    :returns:
        a numpy array with the values for the given assets, depending on the
        loss_type.
    """
    return numpy.array([a.value(loss_type, time_event) for a in assets])


class RiskModel(object):
    """
    Base class. Can be used in the tests as a mock.
    """
    time_event = None  # used in scenario_risk
    compositemodel = None  # set by get_risk_model
    kind = None  # must be set in subclasses

    def __init__(self, taxonomy, risk_functions, insured_losses):
        self.taxonomy = taxonomy
        self.risk_functions = risk_functions
        self.insured_losses = insured_losses

    @property
    def loss_types(self):
        """
        The list of loss types in the underlying vulnerability functions,
        in lexicographic order
        """
        return sorted(self.risk_functions)

    def get_loss_types(self, imt):
        """
        :param imt: Intensity Measure Type string
        :returns: loss types with risk functions of the given imt
        """
        return [lt for lt in self.loss_types
                if self.risk_functions[lt].imt == imt]

    def get_output(self, assets, data_by_lt, epsgetter):
        """
        returns an ArrayWrapper of shape (L, ...)
        """
        out = [self(lt, assets, data, epsgetter)
               for lt, data in zip(self.loss_types, data_by_lt)]
        return ArrayWrapper(numpy.array(out), {})

    def __toh5__(self):
        risk_functions = {lt: func for lt, func in self.risk_functions.items()}
        if hasattr(self, 'retro_functions'):
            for lt, func in self.retro_functions.items():
                risk_functions[lt + '_retrofitted'] = func
        return risk_functions, {'taxonomy': self.taxonomy}

    def __fromh5__(self, dic, attrs):
        vars(self).update(attrs)
        self.risk_functions = dic

    def __repr__(self):
        return '<%s%s>' % (self.__class__.__name__, list(self.risk_functions))


def rescale(curves, values):
    """
    Multiply the losses in each curve of kind (losses, poes) by the
    corresponding value.
    """
    n = len(curves)
    assert n == len(values), (n, len(values))
    losses = [curves[i, 0] * values[i] for i in range(n)]
    poes = curves[:, 1]
    return numpy.array([[losses[i], poes[i]] for i in range(n)])


@registry.add('classical_risk', 'classical', 'disaggregation')
class Classical(RiskModel):
    """
    Classical PSHA-Based RiskModel. Computes loss curves and insured curves.
    """
    kind = 'vulnerability'

    def __init__(self, taxonomy, vulnerability_functions,
                 hazard_imtls, lrem_steps_per_interval,
                 conditional_loss_poes, poes_disagg,
                 insured_losses=False):
        """
        :param imt:
            Intensity Measure Type for this riskmodel
        :param taxonomy:
            Taxonomy for this riskmodel
        :param vulnerability_functions:
            Dictionary of vulnerability functions by loss type
        :param hazard_imtls:
            The intensity measure types and levels of the hazard computation
        :param lrem_steps_per_interval:
            Configuration parameter
        :param poes_disagg:
            Probability of Exceedance levels used for disaggregate losses by
            taxonomy.
        :param bool insured_losses:
            ignored since insured loss curves are not implemented

        See :func:`openquake.risklib.scientific.classical` for a description
        of the other parameters.
        """
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions
        self.hazard_imtls = hazard_imtls
        self.lrem_steps_per_interval = lrem_steps_per_interval
        self.conditional_loss_poes = conditional_loss_poes
        self.poes_disagg = poes_disagg
        self.insured_losses = insured_losses
        self.loss_ratios = {
            lt: vf.mean_loss_ratios_with_steps(self.lrem_steps_per_interval)
            for lt, vf in self.risk_functions.items()}

    def __call__(self, loss_type, assets, hazard_curve, _eps=None):
        """
        :param str loss_type:
            the loss type considered
        :param assets:
            assets is an iterator over N
            :class:`openquake.risklib.scientific.Asset` instances
        :param hazard_curve:
            an array of poes
        :param _eps:
            ignored, here only for API compatibility with other calculators
        :returns:
            an array of shape (C, N, 2)
        """
        n = len(assets)
        vf = self.risk_functions[loss_type]
        imls = self.hazard_imtls[vf.imt]
        values = get_values(loss_type, assets)
        lrcurves = numpy.array(
            [scientific.classical(
                vf, imls, hazard_curve, self.lrem_steps_per_interval)] * n)

        # if in the future we wanted to implement insured_losses the
        # following lines could be useful
        # deductibles = [a.deductible(loss_type) for a in assets]
        # limits = [a.insurance_limit(loss_type) for a in assets]
        # insured_curves = rescale(
        # utils.numpy_map(scientific.insured_loss_curve,
        # lrcurves, deductibles, limits), values)
        return rescale(lrcurves, values).transpose(2, 0, 1)
        # transpose array from shape (N, 2, C) -> (C, N, 2)
        # otherwise .get_output would fail


@registry.add('event_based_risk', 'event_based', 'event_based_rupture',
              'ucerf_rupture', 'ucerf_risk', 'gmf_ebrisk')
class ProbabilisticEventBased(RiskModel):
    """
    Implements the Probabilistic Event Based riskmodel.
    Computes loss ratios and event IDs.
    """
    kind = 'vulnerability'

    def __init__(
            self, taxonomy, vulnerability_functions,
            conditional_loss_poes, insured_losses=False):
        """
        See :func:`openquake.risklib.scientific.event_based` for a description
        of the input parameters.
        """
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions
        self.conditional_loss_poes = conditional_loss_poes
        self.insured_losses = insured_losses

    def __call__(self, loss_type, assets, gmvs_eids, epsgetter):
        """
        :param str loss_type:
            the loss type considered
        :param assets:
           a list of assets on the same site and with the same taxonomy
        :param gmvs_eids:
           a pair (gmvs, eids) with E values each
        :param epsgetter:
           a callable returning the correct epsilons for the given gmvs
        :returns:
            a :class:
            `openquake.risklib.scientific.ProbabilisticEventBased.Output`
            instance.
        """
        gmvs, eids = gmvs_eids
        E = len(gmvs)
        I = self.insured_losses + 1
        A = len(assets)
        loss_ratios = numpy.zeros((A, E, I), F32)
        vf = self.risk_functions[loss_type]
        means, covs, idxs = vf.interpolate(gmvs)
        for i, asset in enumerate(assets):
            epsilons = epsgetter(asset.ordinal, eids)
            ratios = vf.sample(means, covs, idxs, epsilons)
            loss_ratios[i, idxs, 0] = ratios
            if self.insured_losses and loss_type != 'occupants':
                loss_ratios[i, idxs, 1] = scientific.insured_losses(
                    ratios,  asset.deductible(loss_type),
                    asset.insurance_limit(loss_type))
        return loss_ratios


@registry.add('classical_bcr')
class ClassicalBCR(RiskModel):

    kind = 'vulnerability'

    def __init__(self, taxonomy,
                 vulnerability_functions_orig,
                 vulnerability_functions_retro,
                 hazard_imtls,
                 lrem_steps_per_interval,
                 interest_rate, asset_life_expectancy):
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions_orig
        self.insured_losses = False  # not implemented
        self.retro_functions = vulnerability_functions_retro
        self.assets = []  # set a __call__ time
        self.interest_rate = interest_rate
        self.asset_life_expectancy = asset_life_expectancy
        self.hazard_imtls = hazard_imtls
        self.lrem_steps_per_interval = lrem_steps_per_interval

    def __call__(self, loss_type, assets, hazard, _eps=None, _eids=None):
        """
        :param loss_type: the loss type
        :param assets: a list of N assets of the same taxonomy
        :param hazard: an hazard curve
        :param _eps: dummy parameter, unused
        :param _eids: dummy parameter, unused
        :returns: a list of triples (eal_orig, eal_retro, bcr_result)
        """
        n = len(assets)
        self.assets = assets
        vf = self.risk_functions[loss_type]
        imls = self.hazard_imtls[vf.imt]
        vf_retro = self.retro_functions[loss_type]
        curves_orig = functools.partial(scientific.classical, vf, imls,
                                        steps=self.lrem_steps_per_interval)
        curves_retro = functools.partial(scientific.classical, vf_retro, imls,
                                         steps=self.lrem_steps_per_interval)
        original_loss_curves = utils.numpy_map(curves_orig, [hazard] * n)
        retrofitted_loss_curves = utils.numpy_map(curves_retro, [hazard] * n)

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

        return list(zip(eal_original, eal_retrofitted, bcr_results))


@registry.add('scenario_risk', 'scenario')
class Scenario(RiskModel):
    """
    Implements the Scenario riskmodel. Computes the loss matrix.
    """
    kind = 'vulnerability'

    def __init__(self, taxonomy, vulnerability_functions,
                 insured_losses, time_event=None):
        self.taxonomy = taxonomy
        self.risk_functions = vulnerability_functions
        self.insured_losses = insured_losses
        self.time_event = time_event

    def __call__(self, loss_type, assets, gmvs_eids, epsgetter):
        gmvs, eids = gmvs_eids
        epsilons = [epsgetter(asset.ordinal, eids) for asset in assets]
        values = get_values(loss_type, assets, self.time_event)
        ok = ~numpy.isnan(values)
        if not ok.any():
            # there are no assets with a value
            return
        # there may be assets without a value
        missing_value = not ok.all()
        if missing_value:
            assets = assets[ok]
            epsilons = epsilons[ok]

        E = len(epsilons[0])
        I = self.insured_losses + 1

        # a matrix of A x E x I elements
        loss_matrix = numpy.empty((len(assets), E, I))
        loss_matrix.fill(numpy.nan)

        vf = self.risk_functions[loss_type]
        means, covs, idxs = vf.interpolate(gmvs)
        loss_ratio_matrix = numpy.zeros((len(assets), E))
        for i, eps in enumerate(epsilons):
            loss_ratio_matrix[i, idxs] = vf.sample(means, covs, idxs, eps)
        loss_matrix[:, :, 0] = (loss_ratio_matrix.T * values).T

        if self.insured_losses and loss_type != "occupants":
            deductibles = [a.deductible(loss_type) for a in assets]
            limits = [a.insurance_limit(loss_type) for a in assets]
            insured_loss_ratio_matrix = utils.numpy_map(
                scientific.insured_losses, loss_ratio_matrix,
                deductibles, limits)
            loss_matrix[:, :, 1] = (insured_loss_ratio_matrix.T * values).T

        return loss_matrix


@registry.add('scenario_damage')
class Damage(RiskModel):
    """
    Implements the ScenarioDamage riskmodel. Computes the damages.
    """
    kind = 'fragility'

    def __init__(self, taxonomy, fragility_functions):
        self.taxonomy = taxonomy
        self.risk_functions = fragility_functions
        self.insured_losses = False  # not implemented

    def __call__(self, loss_type, assets, gmvs_eids, _eps=None):
        """
        :param loss_type: the loss type
        :param assets: a list of N assets of the same taxonomy
        :param gmvs_eids: pairs (gmvs, eids), each one with E elements
        :param _eps: dummy parameter, unused
        :returns: N arrays of E x D elements

        where N is the number of points, E the number of events
        and D the number of damage states.
        """
        ffs = self.risk_functions[loss_type]
        damages = scientific.scenario_damage(ffs, gmvs_eids[0])  # shape (D, E)
        return [damages.T] * len(assets)


@registry.add('classical_damage')
class ClassicalDamage(Damage):
    """
    Implements the ClassicalDamage riskmodel. Computes the damages.
    """
    kind = 'fragility'

    def __init__(self, taxonomy, fragility_functions,
                 hazard_imtls, investigation_time,
                 risk_investigation_time):
        self.taxonomy = taxonomy
        self.risk_functions = fragility_functions
        self.insured_losses = False  # not implemented
        self.hazard_imtls = hazard_imtls
        self.investigation_time = investigation_time
        self.risk_investigation_time = risk_investigation_time

    def __call__(self, loss_type, assets, hazard_curve, _eps=None):
        """
        :param loss_type: the loss type
        :param assets: a list of N assets of the same taxonomy
        :param hazard_curve: an hazard curve array
        :returns: an array of N assets and an array of N x D elements

        where N is the number of points and D the number of damage states.
        """
        ffl = self.risk_functions[loss_type]
        hazard_imls = self.hazard_imtls[ffl.imt]
        damage = scientific.classical_damage(
            ffl, hazard_imls, hazard_curve,
            investigation_time=self.investigation_time,
            risk_investigation_time=self.risk_investigation_time)
        return [a.number * damage for a in assets]


# NB: the approach used here relies on the convention of having the
# names of the arguments of the riskmodel class to be equal to the
# names of the parameter in the oqparam object. This is view as a
# feature, since it forces people to be consistent with the names,
# in the spirit of the 'convention over configuration' philosophy
def get_riskmodel(taxonomy, oqparam, **extra):
    """
    Return an instance of the correct riskmodel class, depending on the
    attribute `calculation_mode` of the object `oqparam`.

    :param taxonomy:
        a taxonomy string
    :param oqparam:
        an object containing the parameters needed by the riskmodel class
    :param extra:
        extra parameters to pass to the riskmodel class
    """
    riskmodel_class = registry[oqparam.calculation_mode]
    # arguments needed to instantiate the riskmodel class
    argnames = inspect.getargspec(riskmodel_class.__init__).args[3:]

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

    return riskmodel_class(taxonomy, **all_args)
