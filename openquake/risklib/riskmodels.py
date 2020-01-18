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
import ast
import copy
import functools
import collections
from urllib.parse import unquote_plus
import numpy

from openquake.baselib import hdf5
from openquake.baselib.node import Node
from openquake.baselib.general import AccumDict, cached_property
from openquake.hazardlib import valid, nrml, InvalidFile
from openquake.hazardlib.sourcewriter import obj_to_node
from openquake.risklib import scientific

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64

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
    for key in sorted(inputs):
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


def get_risk_models(oqparam, kind='vulnerability fragility consequence '
                    'vulnerability_retrofitted'):
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
            for (imt, riskid), ffl in sorted(newfm.items()):
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
            for riskid, cf in sorted(rm.items()):
                rdict[riskid][loss_type, kind] = cf
        else:  # vulnerability, vulnerability_retrofitted
            cl_risk = oqparam.calculation_mode in (
                'classical', 'classical_risk')
            # only for classical_risk reduce the loss_ratios
            # to make sure they are strictly increasing
            for (imt, riskid), rf in sorted(rm.items()):
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


class RiskModel(object):
    """
    Base class. Can be used in the tests as a mock.

    :param taxonomy: a taxonomy string
    :param risk_functions: a dict (loss_type, kind) -> risk_function
    """
    time_event = None  # used in scenario_risk
    compositemodel = None  # set by get_crmodel

    def __init__(self, calcmode, taxonomy, risk_functions, **kw):
        self.calcmode = calcmode
        self.taxonomy = taxonomy
        self.risk_functions = risk_functions
        vars(self).update(kw)
        steps = kw.get('lrem_steps_per_interval')
        if calcmode in 'classical_risk':
            self.loss_ratios = {
                lt: tuple(vf.mean_loss_ratios_with_steps(steps))
                for (lt, kind), vf in risk_functions.items()}
        if calcmode == 'classical_bcr':
            self.loss_ratios_orig = {
                lt: tuple(vf.mean_loss_ratios_with_steps(steps))
                for (lt, kind), vf in risk_functions.items()
                if kind == 'vulnerability'}
            self.loss_ratios_retro = {
                lt: tuple(vf.mean_loss_ratios_with_steps(steps))
                for (lt, kind), vf in risk_functions.items()
                if kind == 'vulnerability_retrofitted'}

    @property
    def loss_types(self):
        """
        The list of loss types in the underlying vulnerability functions,
        in lexicographic order
        """
        return sorted(lt for (lt, kind) in self.risk_functions)

    def __call__(self, loss_type, assets, gmvs, eids, epsilons):
        meth = getattr(self, self.calcmode)
        res = meth(loss_type, assets, gmvs, eids, epsilons)
        return res

    def __toh5__(self):
        return self.risk_functions, {'taxonomy': self.taxonomy}

    def __fromh5__(self, dic, attrs):
        vars(self).update(attrs)
        self.risk_functions = dic

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.taxonomy)

    # ######################## calculation methods ######################### #

    def classical_risk(
            self, loss_type, assets, hazard_curve, eids=None, eps=None):
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
        vf = self.risk_functions[loss_type, 'vulnerability']
        lratios = self.loss_ratios[loss_type]
        imls = self.hazard_imtls[vf.imt]
        values = get_values(loss_type, assets)
        lrcurves = numpy.array(
            [scientific.classical(vf, imls, hazard_curve, lratios)] * n)
        return rescale(lrcurves, values)

    def event_based_risk(self, loss_type, assets, gmvs, eids, epsilons):
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
        vf = self.risk_functions[loss_type, 'vulnerability']
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

    ebrisk = event_based_risk

    def classical_bcr(self, loss_type, assets, hazard, eids=None, eps=None):
        """
        :param loss_type: the loss type
        :param assets: a list of N assets of the same taxonomy
        :param hazard: an hazard curve
        :param _eps: dummy parameter, unused
        :param _eids: dummy parameter, unused
        :returns: a list of triples (eal_orig, eal_retro, bcr_result)
        """
        if loss_type != 'structural':
            raise NotImplementedError(
                'retrofitted is not defined for ' + loss_type)
        n = len(assets)
        self.assets = assets
        vf = self.risk_functions[loss_type, 'vulnerability']
        imls = self.hazard_imtls[vf.imt]
        vf_retro = self.risk_functions[loss_type, 'vulnerability_retrofitted']
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

    def scenario_risk(self, loss_type, assets, gmvs, eids, epsilons):
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

        vf = self.risk_functions[loss_type, 'vulnerability']
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

    scenario = scenario_risk

    def scenario_damage(self, loss_type, assets, gmvs, eids=None, eps=None):
        """
        :param loss_type: the loss type
        :param assets: a list of A assets of the same taxonomy
        :param gmvs: an array of E ground motion values
        :param eids: an array of E event IDs
        :param eps: dummy parameter, unused
        :returns: an array of shape (A, E, D) elements

        where N is the number of points, E the number of events
        and D the number of damage states.
        """
        ffs = self.risk_functions[loss_type, 'fragility']
        damages = scientific.scenario_damage(ffs, gmvs).T
        return numpy.array([damages] * len(assets))

    event_based_damage = scenario_damage

    def classical_damage(
            self, loss_type, assets, hazard_curve, eids=None, eps=None):
        """
        :param loss_type: the loss type
        :param assets: a list of N assets of the same taxonomy
        :param hazard_curve: an hazard curve array
        :returns: an array of N assets and an array of N x D elements

        where N is the number of points and D the number of damage states.
        """
        ffl = self.risk_functions[loss_type, 'fragility']
        hazard_imls = self.hazard_imtls[ffl.imt]
        damage = scientific.classical_damage(
            ffl, hazard_imls, hazard_curve,
            investigation_time=self.investigation_time,
            risk_investigation_time=self.risk_investigation_time)
        return [a['number'] * damage for a in assets]


# NB: the approach used here relies on the convention of having the
# names of the arguments of the RiskModel class to be equal to the
# names of the parameter in the oqparam object. This is seen as a
# feature, since it forces people to be consistent with the names,
# in the spirit of the 'convention over configuration' philosophy
def get_riskmodel(taxonomy, oqparam, **extra):
    """
    Return an instance of the correct risk model class, depending on the
    attribute `calculation_mode` of the object `oqparam`.

    :param taxonomy:
        a taxonomy string
    :param oqparam:
        an object containing the parameters needed by the RiskModel class
    :param extra:
        extra parameters to pass to the RiskModel class
    """
    extra['hazard_imtls'] = oqparam.imtls
    extra['investigation_time'] = oqparam.investigation_time
    extra['risk_investigation_time'] = oqparam.risk_investigation_time
    extra['lrem_steps_per_interval'] = oqparam.lrem_steps_per_interval
    extra['ignore_covs'] = oqparam.ignore_covs
    extra['time_event'] = oqparam.time_event
    if oqparam.calculation_mode == 'classical_bcr':
        extra['interest_rate'] = oqparam.interest_rate
        extra['asset_life_expectancy'] = oqparam.asset_life_expectancy
    return RiskModel(oqparam.calculation_mode, taxonomy, **extra)


# ######################## CompositeRiskModel #########################

class ValidationError(Exception):
    pass


def _extract(rmdict, kind):
    lst = []
    for riskid, rm in rmdict.items():
        risk_functions = getattr(rm, 'risk_functions', rm)
        for (lt, k), rf in risk_functions.items():
            if k == kind:
                lst.append((riskid, rf))
    return lst


class CompositeRiskModel(collections.abc.Mapping):
    """
    A container (riskid, kind) -> riskmodel

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param fragdict:
        a dictionary riskid -> loss_type -> fragility functions
    :param vulndict:
        a dictionary riskid -> loss_type -> vulnerability function
    :param consdict:
        a dictionary riskid -> loss_type -> consequence functions
    """
    @classmethod
    def read(cls, dstore):
        """
        :param dstore: a DataStore instance
        :returns: a :class:`CompositeRiskModel` instance
        """
        oqparam = dstore['oqparam']
        crm = dstore.getitem('risk_model')
        riskdict = AccumDict(accum={})
        riskdict.limit_states = crm.attrs['limit_states']
        cons_model = {}  # cname_by -> taxo, loss_type -> coeffs
        # TODO: populate it
        for quoted_id, rm in crm.items():
            riskid = unquote_plus(quoted_id)
            for lt_kind in rm:
                lt, kind = lt_kind.rsplit('-', 1)
                rf = dstore['risk_model/%s/%s' % (quoted_id, lt_kind)]
                if kind == 'fragility':  # rf is a FragilityFunctionList
                    try:
                        rf = rf.build(
                            riskdict.limit_states,
                            oqparam.continuous_fragility_discretization,
                            oqparam.steps_per_interval)
                    except ValueError as err:
                        raise ValueError('%s: %s' % (riskid, err))
                    riskdict[riskid][lt, kind] = rf
                else:  # rf is a vulnerability function
                    rf.seed = oqparam.master_seed
                    rf.init()
                    if lt.endswith('_retrofitted'):
                        # strip _retrofitted, since len('_retrofitted') = 12
                        riskdict[riskid][
                            lt[:-12], 'vulnerability_retrofitted'] = rf
                    else:
                        riskdict[riskid][lt, 'vulnerability'] = rf
        crm = CompositeRiskModel(oqparam, riskdict, cons_model)
        crm.tmap = ast.literal_eval(dstore.get_attr('risk_model', 'tmap'))
        return crm

    def __init__(self, oqparam, riskdict, consdict):
        self.damage_states = []
        self.cons_model = consdict
        self._riskmodels = {}  # riskid -> crmodel
        if oqparam.calculation_mode.endswith('_bcr'):
            # classical_bcr calculator
            for riskid, risk_functions in sorted(riskdict.items()):
                self._riskmodels[riskid] = get_riskmodel(
                    riskid, oqparam, risk_functions=risk_functions)
        elif (_extract(riskdict, 'fragility') or
              'damage' in oqparam.calculation_mode):
            # classical_damage/scenario_damage calculator
            if oqparam.calculation_mode in ('classical', 'scenario'):
                # case when the risk files are in the job_hazard.ini file
                oqparam.calculation_mode += '_damage'
                if 'exposure' not in oqparam.inputs:
                    raise RuntimeError(
                        'There are risk files in %r but not '
                        'an exposure' % oqparam.inputs['job_ini'])

            self.damage_states = ['no_damage'] + list(riskdict.limit_states)
            for riskid, ffs_by_lt in sorted(riskdict.items()):
                self._riskmodels[riskid] = get_riskmodel(
                    riskid, oqparam, risk_functions=ffs_by_lt)
        else:
            # classical, event based and scenario calculators
            for riskid, vfs in sorted(riskdict.items()):
                for vf in vfs.values():
                    # set the seed; this is important for the case of
                    # VulnerabilityFunctionWithPMF
                    vf.seed = oqparam.random_seed
                self._riskmodels[riskid] = get_riskmodel(
                    riskid, oqparam, risk_functions=vfs)
        self.init(oqparam)

    def compute_csq(self, asset, fractions, loss_type):
        """
        :param asset: asset record
        :param fractions: array of probabilies of shape (E, D)
        :param loss_type: loss type as a string
        :returns: a dict consequence_name -> array of length E
        """
        csq = {}  # cname -> values per event
        for byname, coeffs in self.cons_model.items():
            if len(coeffs):
                cname, tagname = byname.split('_by_')
                func = scientific.consequence[cname]
                coeffs = coeffs[asset[tagname] - 1][loss_type]
                csq[cname] = func(coeffs, asset, fractions[:, 1:], loss_type)
        return csq

    def init(self, oqparam):
        self.imtls = oqparam.imtls
        imti = {imt: i for i, imt in enumerate(oqparam.imtls)}
        self.lti = {}  # loss_type -> idx
        self.covs = 0  # number of coefficients of variation
        # build a sorted list with all the loss_types contained in the model
        ltypes = set()
        for rm in self.values():
            ltypes.update(rm.loss_types)
        self.loss_types = sorted(ltypes)
        self.taxonomies = set()
        self.distributions = set()
        for riskid, rm in self._riskmodels.items():
            self.taxonomies.add(riskid)
            rm.compositemodel = self
            for lt, rf in rm.risk_functions.items():
                if hasattr(rf, 'distribution_name'):
                    self.distributions.add(rf.distribution_name)
                if hasattr(rf, 'init'):  # vulnerability function
                    rf.seed = oqparam.master_seed  # setting the seed
                    rf.init()
                # save the number of nonzero coefficients of variation
                if hasattr(rf, 'covs') and rf.covs.any():
                    self.covs += 1
            missing = set(self.loss_types) - set(
                lt for lt, kind in rm.risk_functions)
            if missing:
                raise ValidationError(
                    'Missing vulnerability function for taxonomy %s and loss'
                    ' type %s' % (riskid, ', '.join(missing)))
            rm.imti = {lt: imti[rm.risk_functions[lt, kind].imt]
                       for lt, kind in rm.risk_functions
                       if kind in 'vulnerability fragility'}
        self.curve_params = self.make_curve_params(oqparam)
        iml = collections.defaultdict(list)
        for riskid, rm in self._riskmodels.items():
            for lt, rf in rm.risk_functions.items():
                if hasattr(rf, 'imt'):
                    iml[rf.imt].append(rf.imls[0])
        self.min_iml = {imt: min(iml[imt]) for imt in iml}

    def eid_dmg_dt(self):
        """
        :returns: a dtype (eid, dmg)
        """
        L = len(self.lti)
        D = len(self.damage_states)
        return numpy.dtype([('eid', U32), ('dmg', (F32, (L, D)))])

    def aid_eid_dd_dt(self):
        """
        :returns: a dtype (aid, eid, dd)
        """
        L = len(self.lti)
        D1 = len(self.damage_states) - 1
        return numpy.dtype(
            [('aid', U32), ('eid', U32), ('dd', (F32, (L, D1)))])

    def vectorize_cons_model(self, tagcol):
        """
        Convert the dictionaries tag -> coeffs in the consequence model
        into vectors tag index -> coeffs (one per cname)
        """
        for cname_by_tagname, dic in self.cons_model.items():
            cname, tagname = cname_by_tagname.split('_by_')
            tagidx = tagcol.get_tagidx(tagname)
            items = sorted((tagidx[tag], cf) for tag, cf in dic.items())
            self.cons_model[cname_by_tagname] = numpy.array(
                [it[1] for it in items])

    @cached_property
    def taxonomy_dict(self):
        """
        :returns: a dict taxonomy string -> taxonomy index
        """
        # .taxonomy must be set by the engine
        tdict = {taxo: idx for idx, taxo in enumerate(self.taxonomy)}
        return tdict

    def get_consequences(self):
        """
        :returns: the list of available consequences
        """
        csq = []
        for cname_by_tagname, arr in self.cons_model.items():
            if len(arr):
                csq.append(cname_by_tagname.split('_by_')[0])
        return csq

    def make_curve_params(self, oqparam):
        # the CurveParams are used only in classical_risk, classical_bcr
        # NB: populate the inner lists .loss_types too
        cps = []
        for l, loss_type in enumerate(self.loss_types):
            if oqparam.calculation_mode in ('classical', 'classical_risk'):
                curve_resolutions = set()
                lines = []
                allratios = []
                for taxo in sorted(self):
                    rm = self[taxo]
                    rf = rm.risk_functions.get((loss_type, 'vulnerability'))
                    if rf and loss_type in rm.loss_ratios:
                        ratios = rm.loss_ratios[loss_type]
                        allratios.append(ratios)
                        curve_resolutions.add(len(ratios))
                        lines.append('%s %d' % (rf, len(ratios)))
                if len(curve_resolutions) > 1:
                    # number of loss ratios is not the same for all taxonomies:
                    # then use the longest array; see classical_risk case_5
                    allratios.sort(key=len)
                    for rm in self.values():
                        if rm.loss_ratios[loss_type] != allratios[-1]:
                            rm.loss_ratios[loss_type] = allratios[-1]
                            # logging.debug(f'Redefining loss ratios for {rm}')
                cp = scientific.CurveParams(
                    l, loss_type, max(curve_resolutions), allratios[-1], True
                ) if curve_resolutions else scientific.CurveParams(
                    l, loss_type, 0, [], False)
            else:  # used only to store the association l -> loss_type
                cp = scientific.CurveParams(l, loss_type, 0, [], False)
            cps.append(cp)
            self.lti[loss_type] = l
        return cps

    def get_loss_ratios(self):
        """
        :returns: a 1-dimensional composite array with loss ratios by loss type
        """
        lst = [('user_provided', numpy.bool)]
        for cp in self.curve_params:
            lst.append((cp.loss_type, F32, len(cp.ratios)))
        loss_ratios = numpy.zeros(1, numpy.dtype(lst))
        for cp in self.curve_params:
            loss_ratios['user_provided'] = cp.user_provided
            loss_ratios[cp.loss_type] = tuple(cp.ratios)
        return loss_ratios

    def __getitem__(self, taxo):
        return self._riskmodels[taxo]

    def get_rmodels_weights(self, taxidx):
        """
        :returns: a list of weighted risk models for the given taxonomy index
        """
        rmodels, weights = [], []
        for key, weight in self.tmap[taxidx]:
            rmodels.append(self._riskmodels[key])
            weights.append(weight)
        return rmodels, weights

    def __iter__(self):
        return iter(sorted(self._riskmodels))

    def __len__(self):
        return len(self._riskmodels)

    def reduce(self, taxonomies):
        """
        :param taxonomies: a set of taxonomies
        :returns: a new CompositeRiskModel reduced to the given taxonomies
        """
        new = copy.copy(self)
        new._riskmodels = {}
        for riskid, rm in self._riskmodels.items():
            if riskid in taxonomies:
                new._riskmodels[riskid] = rm
                rm.compositemodel = new
        return new

    def __toh5__(self):
        loss_types = hdf5.array_of_vstr(self.loss_types)
        limit_states = hdf5.array_of_vstr(self.damage_states[1:]
                                          if self.damage_states else [])
        attrs = dict(covs=self.covs, loss_types=loss_types,
                     limit_states=limit_states,
                     tmap=repr(getattr(self, 'tmap', [])))
        rf = next(iter(self.values()))
        if hasattr(rf, 'loss_ratios'):
            for lt in self.loss_types:
                attrs['loss_ratios_' + lt] = rf.loss_ratios[lt]
        dic = self._riskmodels.copy()
        for k, v in self.cons_model.items():
            if len(v):
                dic[k] = v
        return dic, attrs

    def __repr__(self):
        lines = ['%s: %s' % item for item in sorted(self.items())]
        return '<%s(%d, %d)\n%s>' % (
            self.__class__.__name__, len(lines), self.covs, '\n'.join(lines))
