# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
import re
import inspect
import functools
import numpy

from openquake.baselib.node import Node
from openquake.baselib.general import CallableDict, AccumDict
from openquake.hazardlib import valid, nrml, InvalidFile
from openquake.hazardlib.sourcewriter import obj_to_node
from openquake.risklib import scientific

U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
registry = CallableDict()

COST_TYPE_REGEX = '|'.join(valid.cost_type.choices)
RISK_TYPE_REGEX = re.compile(
    r'(%s|occupants|fragility)_([\w_]+)' % COST_TYPE_REGEX)


def get_risk_files(inputs):
    """
    :param inputs: a dictionary key -> path name
    :returns: a pair (file_type, {risk_type: path})
    """
    rfs = {}
    job_ini = inputs['job_ini']
    for key in inputs:
        if key == 'fragility':
            # backward compatibily for .ini files with key fragility_file
            # instead of structural_fragility_file
            rfs['fragility/structural'] = inputs[
                'structural_fragility'] = inputs[key]
            del inputs['fragility']
        elif key.endswith(('_fragility', '_vulnerability', '_consequence')):
            match = RISK_TYPE_REGEX.match(key)
            if match and 'retrofitted' not in key and 'consequence' not in key:
                rfs['%s/%s' % (match.group(2), match.group(1))] = inputs[key]
            elif match is None:
                raise ValueError('Invalid key in %s: %s_file' % (job_ini, key))
    return rfs


# ########################### vulnerability ############################## #

def filter_vset(elem):
    return elem.tag.endswith('discreteVulnerabilitySet')


@obj_to_node.add('VulnerabilityFunction')
def build_vf_node(vf):
    """
    Convert a VulnerabilityFunction object into a Node suitable
    for XML conversion.
    """
    nodes = [Node('imls', {'imt': vf.imt}, vf.imls),
             Node('meanLRs', {}, vf.mean_loss_ratios),
             Node('covLRs', {}, vf.covs)]
    return Node(
        'vulnerabilityFunction',
        {'id': vf.id, 'dist': vf.distribution_name}, nodes=nodes)


def get_risk_models(oqparam, kind='vulnerability vulnerability_retrofitted '
                    'fragility consequence'):
    """
    :param oqparam:
        an OqParam instance
    :param kind:
        a space-separated string with the kinds of risk models to read
    :returns:
        a dictionary riskid -> loss_type, kind -> function
    """
    kinds = kind.split()
    rmodels = AccumDict()
    for kind in kinds:
        for key in sorted(oqparam.inputs):
            mo = re.match('(occupants|%s)_%s$' % (COST_TYPE_REGEX, kind), key)
            if mo:
                loss_type = mo.group(1)  # the cost_type in the key
                # can be occupants, structural, nonstructural, ...
                rmodel = nrml.to_python(oqparam.inputs[key])
                if len(rmodel) == 0:
                    raise InvalidFile('%s is empty!' % oqparam.inputs[key])
                rmodels[loss_type, kind] = rmodel
                if rmodel.lossCategory is None:  # NRML 0.4
                    continue
                cost_type = str(rmodel.lossCategory)
                rmodel_kind = rmodel.__class__.__name__
                kind_ = kind.replace('_retrofitted', '')  # strip retrofitted
                if not rmodel_kind.lower().startswith(kind_):
                    raise ValueError(
                        'Error in the file "%s_file=%s": is '
                        'of kind %s, expected %s' % (
                            key, oqparam.inputs[key], rmodel_kind,
                            kind.capitalize() + 'Model'))
                if cost_type != loss_type:
                    raise ValueError(
                        'Error in the file "%s_file=%s": lossCategory is of '
                        'type "%s", expected "%s"' %
                        (key, oqparam.inputs[key],
                         rmodel.lossCategory, loss_type))
    rdict = AccumDict(accum={})
    rdict.limit_states = []
    for (loss_type, kind), rm in sorted(rmodels.items()):
        if kind == 'fragility':
            # build a copy of the FragilityModel with different IM levels
            newfm = rm.build(oqparam.continuous_fragility_discretization,
                             oqparam.steps_per_interval)
            for (imt, riskid), ffl in newfm.items():
                if not rdict.limit_states:
                    rdict.limit_states.extend(rm.limitStates)
                # we are rejecting the case of loss types with different
                # limit states; this may change in the future
                assert rdict.limit_states == rm.limitStates, (
                    rdict.limit_states, rm.limitStates)
                rdict[riskid][loss_type, kind] = ffl
                # TODO: see if it is possible to remove the attribute
                # below, used in classical_damage
                ffl.steps_per_interval = oqparam.steps_per_interval
        elif kind == 'consequence':
            for riskid, cf in rm.items():
                rdict[riskid][loss_type, kind] = cf
        else:  # vulnerability
            cl_risk = oqparam.calculation_mode in (
                'classical', 'classical_risk')
            # only for classical_risk reduce the loss_ratios
            # to make sure they are strictly increasing
            for (imt, riskid), rf in rm.items():
                rdict[riskid][loss_type, kind] = (
                    rf.strictly_increasing() if cl_risk else rf)
    return rdict


def get_values(loss_type, assets, time_event=None):
    """
    :returns:
        a numpy array with the values for the given assets, depending on the
        loss_type.
    """
    if loss_type == 'occupants':
        return assets['occupants_%s' % time_event]
    else:
        return assets['value-' + loss_type]


class RiskModel(object):
    """
    Base class. Can be used in the tests as a mock.
    """
    time_event = None  # used in scenario_risk
    compositemodel = None  # set by get_risk_model
    kind = None  # must be set in subclasses

    def __init__(self, taxonomy, fragility_functions, vulnerability_functions):
        self.taxonomy = taxonomy
        self.fragility_functions = fragility_functions
        self.vulnerability_functions = vulnerability_functions

    @property
    def risk_functions(self):
        """
        :returns: fragility or vulnerability functions depending on the kind
        """
        return getattr(self, self.kind + '_functions')

    @property
    def loss_types(self):
        """
        The list of loss types in the underlying vulnerability functions,
        in lexicographic order
        """
        return sorted(lt for (lt, kind) in self.risk_functions)

    def get_loss_types(self, imt):
        """
        :param imt: Intensity Measure Type string
        :returns: loss types with risk functions of the given imt
        """
        return [lt for lt in self.loss_types
                if self.risk_functions[lt].imt == imt]

    def __toh5__(self):
        dic = self.risk_functions.copy()
        if hasattr(self, 'retro_functions'):
            dic.update(self.retro_functions)
        if hasattr(self, 'consequence_functions'):
            dic.update(self.consequence_functions)
        return dic, {'taxonomy': self.taxonomy}

    def __fromh5__(self, dic, attrs):
        vars(self).update(attrs)
        setattr(self, self.kind + '_functions', dic)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.taxonomy)


loss_poe_dt = numpy.dtype([('loss', F64), ('poe', F64)])


def rescale(curves, values):
    """
    Multiply the losses in each curve of kind (losses, poes) by the
    corresponding value.

    :param curves: an array of shape (A, 2, C)
    :param values: an array of shape (A,)
    """
    A, _, C = curves.shape
    assert A == len(values), (A, len(values))
    array = numpy.zeros((A, C), loss_poe_dt)
    array['loss'] = [c * v for c, v in zip(curves[:, 0], values)]
    array['poe'] = curves[:, 1]
    return array


@registry.add('classical_risk', 'classical', 'disaggregation')
class Classical(RiskModel):
    """
    Classical PSHA-Based RiskModel. Computes loss curves and insured curves.
    """
    kind = 'vulnerability'

    def __init__(self, taxonomy, fragility_functions, vulnerability_functions,
                 hazard_imtls, lrem_steps_per_interval,
                 conditional_loss_poes, poes_disagg):
        """
        :param imt:
            Intensity Measure Type for this riskmodel
        :param taxonomy:
            Taxonomy for this riskmodel
        :param fragility_functions:
            Dictionary of fragility functions by loss type
        :param vulnerability_functions:
            Dictionary of vulnerability functions by loss type
        :param hazard_imtls:
            The intensity measure types and levels of the hazard computation
        :param lrem_steps_per_interval:
            Configuration parameter
        :param poes_disagg:
            Probability of Exceedance levels used for disaggregate losses by
            taxonomy.

        See :func:`openquake.risklib.scientific.classical` for a description
        of the other parameters.
        """
        self.taxonomy = taxonomy
        self.fragility_functions = fragility_functions
        self.vulnerability_functions = vulnerability_functions
        self.hazard_imtls = hazard_imtls
        self.lrem_steps_per_interval = lrem_steps_per_interval
        self.conditional_loss_poes = conditional_loss_poes
        self.poes_disagg = poes_disagg
        self.loss_ratios = {
            lt: tuple(vf.mean_loss_ratios_with_steps(lrem_steps_per_interval))
            for (lt, kind), vf in vulnerability_functions.items()}

    def __call__(self, loss_type, assets, hazard_curve, eids=None, eps=None):
        """
        :param str loss_type:
            the loss type considered
        :param assets:
            assets is an iterator over A
            :class:`openquake.risklib.scientific.Asset` instances
        :param hazard_curve:
            an array of poes
        :param eids:
            ignored, here only for API compatibility with other calculators
        :param eps:
            ignored, here only for API compatibility with other calculators
        :returns:
            a composite array (loss, poe) of shape (A, C)
        """
        n = len(assets)
        vf = self.vulnerability_functions[loss_type, self.kind]
        lratios = self.loss_ratios[loss_type]
        imls = self.hazard_imtls[vf.imt]
        values = get_values(loss_type, assets)
        lrcurves = numpy.array(
            [scientific.classical(vf, imls, hazard_curve, lratios)] * n)
        return rescale(lrcurves, values)


@registry.add('event_based_risk', 'event_based', 'event_based_rupture',
              'ebrisk', 'ucerf_rupture', 'ucerf_hazard', 'ucerf_risk')
class ProbabilisticEventBased(RiskModel):
    """
    Implements the Probabilistic Event Based riskmodel.
    Computes loss ratios and event IDs.
    """
    kind = 'vulnerability'

    def __init__(self, taxonomy, fragility_functions, vulnerability_functions,
                 conditional_loss_poes, ignore_covs):
        self.taxonomy = taxonomy
        self.fragility_functions = fragility_functions
        self.vulnerability_functions = vulnerability_functions
        self.conditional_loss_poes = conditional_loss_poes
        self.ignore_covs = ignore_covs

    def __call__(self, loss_type, assets, gmvs, eids, epsilons):
        """
        :param str loss_type:
            the loss type considered
        :param assets:
           a list of assets on the same site and with the same taxonomy
        :param gmvs_eids:
           a pair (gmvs, eids) with E values each
        :param epsilons:
           a matrix of epsilons of shape (A, E) (or an empty tuple)
        :returns:
            an array of loss ratios of shape (A, E)
        """
        E = len(gmvs)
        A = len(assets)
        loss_ratios = numpy.zeros((A, E), F32)
        vf = self.vulnerability_functions[loss_type, self.kind]
        means, covs, idxs = vf.interpolate(gmvs)
        if len(means) == 0:  # all gmvs are below the minimum imls, 0 ratios
            pass
        elif self.ignore_covs or covs.sum() == 0 or len(epsilons) == 0:
            # the ratios are equal for all assets
            ratios = vf.sample(means, covs, idxs, None)  # right shape
            for a in range(A):
                loss_ratios[a, idxs] = ratios
        else:
            # take into account the epsilons
            for a, asset in enumerate(assets):
                loss_ratios[a, idxs] = vf.sample(
                    means, covs, idxs, epsilons[a])
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
        self.vulnerability_functions = vulnerability_functions_orig
        self.retro_functions = vulnerability_functions_retro
        self.assets = []  # set a __call__ time
        self.interest_rate = interest_rate
        self.asset_life_expectancy = asset_life_expectancy
        self.hazard_imtls = hazard_imtls
        self.lrem_steps_per_interval = lrem_steps_per_interval
        self.loss_ratios_orig = {
            lt: tuple(vf.mean_loss_ratios_with_steps(lrem_steps_per_interval))
            for (lt, kind), vf in vulnerability_functions_orig.items()}
        self.loss_ratios_retro = {
            lt: tuple(vf.mean_loss_ratios_with_steps(lrem_steps_per_interval))
            for (lt, kind), vf in vulnerability_functions_retro.items()}

    def __call__(self, loss_type, assets, hazard, eids=None, eps=None):
        """
        :param loss_type: the loss type
        :param assets: a list of N assets of the same taxonomy
        :param hazard: an hazard curve
        :param _eps: dummy parameter, unused
        :param _eids: dummy parameter, unused
        :returns: a list of triples (eal_orig, eal_retro, bcr_result)
        """
        if loss_type != 'structural':
            raise NotImplemented('retrofitted is not defined for ' + loss_type)
        n = len(assets)
        self.assets = assets
        vf = self.vulnerability_functions[loss_type, self.kind]
        imls = self.hazard_imtls[vf.imt]
        vf_retro = self.retro_functions[loss_type, self.kind + '_retrofitted']
        curves_orig = functools.partial(
            scientific.classical, vf, imls,
            loss_ratios=self.loss_ratios_orig[loss_type])
        curves_retro = functools.partial(
            scientific.classical, vf_retro, imls,
            loss_ratios=self.loss_ratios_retro[loss_type])
        original_loss_curves = numpy.array([curves_orig(hazard)] * n)
        retrofitted_loss_curves = numpy.array([curves_retro(hazard)] * n)

        eal_original = numpy.array([scientific.average_loss(lc)
                                    for lc in original_loss_curves])

        eal_retrofitted = numpy.array([scientific.average_loss(lc)
                                       for lc in retrofitted_loss_curves])

        bcr_results = [
            scientific.bcr(
                eal_original[i], eal_retrofitted[i],
                self.interest_rate, self.asset_life_expectancy,
                asset['value-' + loss_type], asset['retrofitted'])
            for i, asset in enumerate(assets)]
        return list(zip(eal_original, eal_retrofitted, bcr_results))


@registry.add('scenario_risk', 'scenario')
class Scenario(RiskModel):
    """
    Implements the Scenario riskmodel. Computes the loss matrix.
    """
    kind = 'vulnerability'

    def __init__(self, taxonomy, fragility_functions, vulnerability_functions,
                 time_event=None):
        self.taxonomy = taxonomy
        self.fragility_functions = fragility_functions
        self.vulnerability_functions = vulnerability_functions
        self.time_event = time_event

    def __call__(self, loss_type, assets, gmvs, eids, epsilons):
        """
        :returns: an array of shape (A, E)
        """
        values = get_values(loss_type, assets, self.time_event)
        ok = ~numpy.isnan(values)
        if not ok.any():
            # there are no assets with a value
            return numpy.zeros(0)
        # there may be assets without a value
        missing_value = not ok.all()
        if missing_value:
            assets = assets[ok]
            epsilons = epsilons[ok]

        E = len(eids)

        # a matrix of A x E elements
        loss_matrix = numpy.empty((len(assets), E))
        loss_matrix.fill(numpy.nan)

        vf = self.vulnerability_functions[loss_type, self.kind]
        means, covs, idxs = vf.interpolate(gmvs)
        loss_ratio_matrix = numpy.zeros((len(assets), E))
        if len(epsilons):
            for a, eps in enumerate(epsilons):
                loss_ratio_matrix[a, idxs] = vf.sample(means, covs, idxs, eps)
        else:
            ratios = vf.sample(means, covs, idxs, numpy.zeros(len(means), F32))
            for a in range(len(assets)):
                loss_ratio_matrix[a, idxs] = ratios
        loss_matrix[:, :] = (loss_ratio_matrix.T * values).T
        return loss_matrix


@registry.add('scenario_damage', 'multi_risk')
class Damage(RiskModel):
    """
    Implements the ScenarioDamage riskmodel. Computes the damages.
    """
    kind = 'fragility'

    def __init__(self, taxonomy, fragility_functions,
                 vulnerability_functions, consequence_functions):
        self.taxonomy = taxonomy
        self.fragility_functions = fragility_functions
        self.vulnerability_functions = vulnerability_functions
        self.consequence_functions = consequence_functions

    def __call__(self, loss_type, assets, gmvs, eids=None, eps=None):
        """
        :param loss_type: the loss type
        :param assets: a list of A assets of the same taxonomy
        :param gmvs_eids: pairs (gmvs, eids), each one with E elements
        :param _eps: dummy parameter, unused
        :returns: an array of shape (A, E, D + 1) elements

        where N is the number of points, E the number of events
        and D the number of damage states.
        """
        ffs = self.fragility_functions[loss_type, self.kind]
        damages = scientific.scenario_damage(ffs, gmvs).T
        E, D = damages.shape
        dmg_csq = numpy.zeros((E, D + 1))
        dmg_csq[:, :D] = damages
        c_model = self.consequence_functions.get((loss_type, 'consequence'))
        if c_model:  # compute consequences
            means = [0] + [par[0] for par in c_model.params]
            # NB: we add a 0 in front for nodamage state
            dmg_csq[:, D] = damages @ means  # consequence ratio
        return numpy.array([dmg_csq] * len(assets))


@registry.add('classical_damage')
class ClassicalDamage(Damage):
    """
    Implements the ClassicalDamage riskmodel. Computes the damages.
    """
    kind = 'fragility'

    def __init__(self, taxonomy, fragility_functions, vulnerability_functions,
                 consequence_functions, hazard_imtls, investigation_time,
                 risk_investigation_time):
        self.taxonomy = taxonomy
        self.fragility_functions = fragility_functions
        self.vulnerability_functions = vulnerability_functions
        self.consequence_functions = consequence_functions
        self.hazard_imtls = hazard_imtls
        self.investigation_time = investigation_time
        self.risk_investigation_time = risk_investigation_time
        assert risk_investigation_time, risk_investigation_time

    def __call__(self, loss_type, assets, hazard_curve, eids=None, eps=None):
        """
        :param loss_type: the loss type
        :param assets: a list of N assets of the same taxonomy
        :param hazard_curve: an hazard curve array
        :returns: an array of N assets and an array of N x D elements

        where N is the number of points and D the number of damage states.
        """
        ffl = self.fragility_functions[loss_type, self.kind]
        hazard_imls = self.hazard_imtls[ffl.imt]
        damage = scientific.classical_damage(
            ffl, hazard_imls, hazard_curve,
            investigation_time=self.investigation_time,
            risk_investigation_time=self.risk_investigation_time)
        return [a['number'] * damage for a in assets]


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
    argnames = inspect.getfullargspec(riskmodel_class.__init__).args[3:]

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
