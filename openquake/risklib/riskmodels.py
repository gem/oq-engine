# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
import json
import copy
import logging
import functools
import collections
import numpy
import pandas

from openquake.baselib import hdf5
from openquake.baselib.node import Node
from openquake.baselib.general import AccumDict, cached_property
from openquake.hazardlib import nrml, InvalidFile
from openquake.hazardlib.sourcewriter import obj_to_node
from openquake.risklib import scientific

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64

lts = numpy.concatenate([scientific.LOSSTYPE, scientific.PERILTYPE])
LTYPE_REGEX = '|'.join(lt for lt in lts if '+' not in lt and '_ins' not in lt)
RISK_TYPE_REGEX = re.compile(r'(%s)_([\w_]+)' % LTYPE_REGEX)


def _assert_equal(d1, d2):
    d1.pop('loss_type', None)
    d2.pop('loss_type', None)
    assert sorted(d1) == sorted(d2), (sorted(d1), sorted(d2))
    for k, v in d1.items():
        if isinstance(v, dict):
            _assert_equal(v, d2[k])
        else:
            assert v == d2[k], (v, d2[k])


def get_risk_files(inputs):
    """
    :param inputs: a dictionary key -> path name
    :returns: a dictionary "peril/kind/cost_type" -> fname
    """
    rfs = {}
    job_ini = inputs['job_ini']
    for key in sorted(inputs):
        if key == 'fragility':
            # backward compatibily for .ini files with key fragility_file
            # instead of structural_fragility_file
            rfs['groundshaking/fragility/structural'] = inputs[
                'structural_fragility'] = inputs[key]
            del inputs['fragility']
        elif key.endswith(('_fragility', '_vulnerability', '_vulnerability_retrofitted')):
            match = RISK_TYPE_REGEX.match(key)
            if match:
                kind = match.group(2)  # fragility or vulnerability
                value = inputs[key]
                if isinstance(value, dict):  # cost_type -> fname
                    peril = match.group(1)
                    for cost_type, fname in value.items():
                        rfs[f'{peril}/{kind}/{cost_type}'] = fname
                else:
                    cost_type = match.group(1)
                    rfs[f'groundshaking/{kind}/{cost_type}'] = value
            else:
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


def group_by_lt(funclist):
    """
    Converts a list of objects with attribute .loss_type into a dictionary
    peril -> loss_type -> risk_function
    """
    dic = AccumDict(accum = []) # peril -> lt -> rf
    for rf in funclist:
        dic[rf.loss_type].append(rf)
    for lt, lst in dic.items():
        if len(lst) == 1:
            dic[lt] = lst[0]
        elif lst[1].kind == 'fragility':
            # EventBasedDamageTestCase.test_case_11
            cf, ffl = lst
            ffl.cf = cf
            dic[lt] = ffl
        elif lst[1].kind == 'vulnerability_retrofitted':
            vf, retro = lst
            vf.retro = retro
            dic[lt] = vf
        else:
            raise RuntimeError(lst)
    return dic


class RiskFuncList(list):
    """
    A list of risk functions with attributes .id, .loss_type, .kind
    """
    def groupby_id(self):
        """
        :returns: dictionary id -> peril -> loss_type -> risk_function
        """
        ddic = AccumDict(accum=AccumDict(accum=[]))
        dic = AccumDict(accum=[])
        for rf in self:
            dic[rf.id, rf.peril].append(rf)
        for (riskid, peril), rfs in dic.items():
            ddic[riskid][peril] = group_by_lt(rfs)
        num_perils = {riskid: len(ddic[riskid]) for riskid in ddic}
        if len(set(num_perils.values())) > 1:
            raise ValueError(f'{num_perils=}')
        return ddic


def get_risk_functions(oqparam):
    """
    :param oqparam:
        an OqParam instance
    :returns:
        a list of risk functions
    """
    job_ini = oqparam.inputs['job_ini']
    rmodels = AccumDict()  # (peril, loss_type, kind) -> rmodel
    for key, fname in get_risk_files(oqparam.inputs).items():
        peril, kind, loss_type = key.split('/')  # ex. groundshaking/vulnerability/structural
        rmodel = nrml.to_python(fname)
        if len(rmodel) == 0:
            raise InvalidFile(f'{job_ini}: {fname} is empty!')
        rmodels[peril, loss_type, kind] = rmodel
        if rmodel.lossCategory is None:  # NRML 0.4
            continue
        cost_type = str(rmodel.lossCategory)
        rmodel_kind = rmodel.__class__.__name__
        kind_ = kind.replace('_retrofitted', '')  # strip retrofitted
        if not rmodel_kind.lower().startswith(kind_):
            raise ValueError(
                f'Error in the file "{key}_file={fname}": is '
                f'of kind {rmodel_kind}, expected {kind.capitalize() + "Model"}')
        if cost_type != loss_type:
            raise ValueError(
                f'Error in the file "{key}_file={fname}": lossCategory is of '
                f'type "{rmodel.lossCategory}", expected "{loss_type}"')
    cl_risk = oqparam.calculation_mode in ('classical', 'classical_risk')
    rlist = RiskFuncList()
    rlist.limit_states = []
    for (peril, loss_type, kind), rm in sorted(rmodels.items()):
        if kind == 'fragility':
            for (imt, riskid), ffl in sorted(rm.items()):
                if not rlist.limit_states:
                    rlist.limit_states.extend(rm.limitStates)
                # we are rejecting the case of loss types with different
                # limit states; this may change in the future
                assert rlist.limit_states == rm.limitStates, (
                    rlist.limit_states, rm.limitStates)
                ffl.peril = peril
                ffl.loss_type = loss_type
                ffl.kind = kind
                rlist.append(ffl)
        else:  # vulnerability, vulnerability_retrofitted
            # only for classical_risk reduce the loss_ratios
            # to make sure they are strictly increasing
            for (imt, riskid), rf in sorted(rm.items()):
                rf = rf.strictly_increasing() if cl_risk else rf
                rf.peril = peril
                rf.loss_type = loss_type
                rf.kind = kind
                rlist.append(rf)
    return rlist


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


class PerilDict(dict):
    """
    >>> pd = PerilDict({('groundshaking', 'structural'): .23})
    >>> pd['structural']
    0.23
    >>> pd['structurl']
    Traceback (most recent call last):
    ...
    KeyError: ('groundshaking', 'structurl')
    """
    def __getitem__(self, lt):
        if isinstance(lt, tuple):
            return dict.__getitem__(self, lt)
        else:  # assume lt is a loss_type string
            return dict.__getitem__(self, ('groundshaking', lt))


class RiskModel(object):
    """
    Base class. Can be used in the tests as a mock.

    :param taxonomy: a taxonomy string
    :param risk_functions: a dict peril -> (loss_type, kind) -> risk_function
    """
    time_event = None  # used in scenario_risk
    compositemodel = None  # set by get_crmodel
    alias = None  # set in save_crmodel

    def __init__(self, calcmode, taxonomy, risk_functions, **kw):
        self.calcmode = calcmode
        self.taxonomy = taxonomy
        self.risk_functions = risk_functions
        vars(self).update(kw)  # updates risk_investigation_time too
        steps = kw.get('lrem_steps_per_interval')
        if calcmode in ('classical', 'classical_risk'):
            self.loss_ratios = {
                lt: tuple(vf.mean_loss_ratios_with_steps(steps))
                for lt, vf in risk_functions['groundshaking'].items()}
        if calcmode == 'classical_bcr':
            self.loss_ratios_orig = {}
            self.loss_ratios_retro = {}
            for lt, vf in risk_functions['groundshaking'].items():
                self.loss_ratios_orig[lt] = tuple(
                    vf.mean_loss_ratios_with_steps(steps))
                self.loss_ratios_retro[lt] = tuple(
                    vf.retro.mean_loss_ratios_with_steps(steps))

        # set imt_by_lt
        self.imt_by_lt = {}  # dictionary loss_type -> imt
        for lt, rf in risk_functions['groundshaking'].items():
            if rf.kind in ('vulnerability', 'fragility'):
                self.imt_by_lt[lt] = rf.imt

    @property
    def loss_types(self):
        """
        The list of loss types in the underlying vulnerability functions,
        in lexicographic order
        """
        return sorted(self.risk_functions['groundshaking'])

    def __call__(self, assets, gmf_df, rndgen=None):
        meth = getattr(self, self.calcmode)
        res = {(peril, lt): meth(peril, lt, assets, gmf_df, rndgen)
               for peril in self.risk_functions for lt in self.loss_types}
        # for event_based_risk `res` is loss_type -> DataFrame(eid, aid, loss)
        return PerilDict(res)

    def __toh5__(self):
        return self.risk_functions, {'taxonomy': self.taxonomy}

    def __fromh5__(self, dic, attrs):
        vars(self).update(attrs)
        assert 'groundshaking' in dic, list(dic)
        self.risk_functions = dic

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.taxonomy)

    # ######################## calculation methods ######################### #

    def classical_risk(self, peril, loss_type, assets, hazard_curve, rng=None):
        """
        :param str loss_type:
            the loss type considered
        :param assets:
            assets is an iterator over A
            :class:`openquake.risklib.scientific.Asset` instances
        :param hazard_curve:
            an array of poes
        :param eps:
            ignored, here only for API compatibility with other calculators
        :returns:
            a composite array (loss, poe) of shape (A, C)
        """
        n = len(assets)
        vf = self.risk_functions[peril][loss_type]
        lratios = self.loss_ratios[loss_type]
        imls = self.hazard_imtls[vf.imt]
        poes = hazard_curve[self.hazard_imtls(vf.imt)]
        if loss_type == 'occupants':
            values = assets['occupants_avg'].to_numpy()
        else:
            values = assets['value-' + loss_type].to_numpy()
        rtime = self.risk_investigation_time or self.investigation_time
        lrcurves = numpy.array(
            [scientific.classical(
                vf, imls, poes, lratios, self.investigation_time, rtime)] * n)
        return rescale(lrcurves, values)

    def classical_bcr(self, peril, loss_type, assets, hazard, rng=None):
        """
        :param loss_type: the loss type
        :param assets: a list of N assets of the same taxonomy
        :param hazard: a dictionary col -> hazard curve
        :param _eps: dummy parameter, unused
        :returns: a list of triples (eal_orig, eal_retro, bcr_result)
        """
        if loss_type != 'structural':
            raise NotImplementedError(
                'retrofitted is not defined for ' + loss_type)
        n = len(assets)
        self.assets = assets
        vf = self.risk_functions[peril][loss_type]
        imls = self.hazard_imtls[vf.imt]
        poes = hazard[self.hazard_imtls(vf.imt)]
        rtime = self.risk_investigation_time or self.investigation_time
        curves_orig = functools.partial(
            scientific.classical, vf, imls,
            loss_ratios=self.loss_ratios_orig[loss_type],
            investigation_time=self.investigation_time,
            risk_investigation_time=rtime)
        curves_retro = functools.partial(
            scientific.classical, vf.retro, imls,
            loss_ratios=self.loss_ratios_retro[loss_type],
            investigation_time=self.investigation_time,
            risk_investigation_time=rtime)
        original_loss_curves = numpy.array([curves_orig(poes)] * n)
        retrofitted_loss_curves = numpy.array([curves_retro(poes)] * n)
        eal_original = numpy.array([scientific.average_loss(lc)
                                    for lc in original_loss_curves])
        eal_retrofitted = numpy.array([scientific.average_loss(lc)
                                       for lc in retrofitted_loss_curves])
        bcr_results = [
            scientific.bcr(
                eal_original[i], eal_retrofitted[i],
                self.interest_rate, self.asset_life_expectancy,
                asset['value-' + loss_type], asset['retrofitted'])
            for i, asset in enumerate(assets.to_records())]
        return list(zip(eal_original, eal_retrofitted, bcr_results))

    def classical_damage(self, peril, loss_type, assets, hazard_curve, rng=None):
        """
        :param loss_type: the loss type
        :param assets: a list of N assets of the same taxonomy
        :param hazard_curve: a dictionary col -> hazard curve
        :returns: an array of N x D elements

        where N is the number of points and D the number of damage states.
        """
        ffl = self.risk_functions[peril][loss_type]
        imls = self.hazard_imtls[ffl.imt]
        poes = hazard_curve[self.hazard_imtls(ffl.imt)]
        rtime = self.risk_investigation_time or self.investigation_time
        damage = scientific.classical_damage(
            ffl, imls, poes, investigation_time=self.investigation_time,
            risk_investigation_time=rtime,
            steps_per_interval=self.steps_per_interval)
        damages = numpy.array([a['value-number'] * damage
                               for a in assets.to_records()])
        return damages

    def event_based_risk(self, peril, loss_type, assets, gmf_df, rndgen):
        """
        :returns: a DataFrame with columns eid, eid, loss
        """
        imt = self.imt_by_lt[loss_type]
        col = self.alias.get(imt, imt)
        sid = assets['site_id']
        if loss_type == 'occupants':
            val = assets['occupants_%s' % self.time_event].to_numpy()
        else:
            val = assets['value-' + loss_type].to_numpy()
        asset_df = pandas.DataFrame(dict(aid=assets.index, val=val), sid)
        vf = self.risk_functions[peril][loss_type]
        return vf(asset_df, gmf_df, col, rndgen,
                  self.minimum_asset_loss.get(loss_type, 0.))

    scenario = ebrisk = scenario_risk = event_based_risk

    def scenario_damage(self, peril, loss_type, assets, gmf_df, rng=None):
        """
        :param loss_type: the loss type
        :param assets: a list of A assets of the same taxonomy
        :param gmf_df: a DataFrame of GMFs
        :param epsilons: dummy parameter, unused
        :returns: an array of shape (A, E, D) elements

        where N is the number of points, E the number of events
        and D the number of damage states.
        """
        imt = self.imt_by_lt[loss_type]
        col = self.alias.get(imt, imt)
        gmvs = gmf_df[col].to_numpy()
        ffs = self.risk_functions[peril][loss_type]
        damages = scientific.scenario_damage(ffs, gmvs).T
        return numpy.array([damages] * len(assets))

    event_based_damage = scenario_damage


# NB: the approach used here relies on the convention of having the
# names of the arguments of the RiskModel class to be equal to the
# names of the parameter in the oqparam object. This is seen as a
# feature, since it forces people to be consistent with the names,
# in the spirit of the 'convention over configuration' philosophy
def get_riskmodel(taxonomy, oqparam, risk_functions):
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
    extra = {'hazard_imtls': oqparam.imtls}
    extra['investigation_time'] = oqparam.investigation_time
    extra['risk_investigation_time'] = oqparam.risk_investigation_time
    extra['lrem_steps_per_interval'] = oqparam.lrem_steps_per_interval
    extra['steps_per_interval'] = oqparam.steps_per_interval
    extra['time_event'] = oqparam.time_event
    extra['minimum_asset_loss'] = oqparam.minimum_asset_loss
    if oqparam.calculation_mode == 'classical_bcr':
        extra['interest_rate'] = oqparam.interest_rate
        extra['asset_life_expectancy'] = oqparam.asset_life_expectancy
    return RiskModel(oqparam.calculation_mode, taxonomy, risk_functions, **extra)


# used only in riskmodels_test
def get_riskcomputer(dic, alias, limit_states=()):
    # builds a RiskComputer instance from a suitable dictionary
    rc = scientific.RiskComputer.__new__(scientific.RiskComputer)
    rc.D = len(limit_states) + 1
    rc.wdic = {}
    rfs = AccumDict(accum=[])
    steps = dic.get('lrem_steps_per_interval', 1)
    lts = set()
    riskid_perils = set()
    perils = set()
    for rlk, func in dic['risk_functions'].items():
        peril, lt, riskid = rlk.split('#')
        perils.add(peril)
        riskid_perils.add((riskid, peril))
        lts.add(lt)
        rf = hdf5.json_to_obj(json.dumps(func))
        if hasattr(rf, 'init'):
            rf.init()
            rf.loss_type = lt
            rf.peril = peril
        if getattr(rf, 'retro', False):
            rf.retro = hdf5.json_to_obj(json.dumps(rf.retro))
            rf.retro.init()
            rf.retro.loss_type = lt
        if hasattr(rf, 'array'):  # fragility
            rf = rf.build(limit_states)
        rfs[riskid].append(rf)
    lts = sorted(lts)
    mal = dic.setdefault('minimum_asset_loss', {lt: 0. for lt in lts})
    for riskid in rfs:
        by_peril = AccumDict(accum=[])
        for rf in rfs[riskid]:
            by_peril[rf.peril].append(rf)
        rm = RiskModel(dic['calculation_mode'], 'taxonomy',
                       {peril: group_by_lt(by_peril[peril]) for peril in by_peril},
                       lrem_steps_per_interval=steps,
                       minimum_asset_loss=mal)
        rm.alias = alias
        rc[riskid] = rm
    if 'wdic' in dic:
        for rlt, weight in dic['wdic'].items():
            riskid, peril = rlt.split('#')
            rc.wdic[riskid, peril] = weight
    else:
        rc.wdic = {(riskid, peril): 1.
                   for riskid, peril in sorted(riskid_perils)}
    rc.P = len(perils)
    rc.loss_types = lts
    rc.minimum_asset_loss = mal
    rc.calculation_mode = dic['calculation_mode']
    return rc


# ######################## CompositeRiskModel #########################

class ValidationError(Exception):
    pass


# TODO: if the consequence tag is different from "taxonomy", pass
# the values of the exposure for that tag
def check_consequences(fname, taxonomies, perils):
    """
    Check that the taxonomy field (if any) and the peril field (if any)
    in the consequence file are consistent with the expected taxonomies
    and perils
    """
    df = pandas.read_csv(fname)
    if 'taxonomy' in df.columns:
        csq_taxonomies = set(df['taxonomy'])
        extra = csq_taxonomies - taxonomies
        missing = taxonomies - csq_taxonomies
        if not csq_taxonomies & taxonomies:
            raise InvalidFile(f'{fname}: no matching taxonomies')
        elif missing:
            raise InvalidFile(f'{fname}: missing taxonomies {missing}')
        elif extra:
            # tested in event_based_damage/case_15
            logging.warning(f'In {fname} there are extra taxonomies missing '
                            f'in the exposure: {extra}')
    if 'peril' in df.columns:
        for line, peril in enumerate(df['peril'], 1):
            if peril not in perils:
                raise InvalidFile(f'{fname}: unknown {peril=} at {line=}')


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
    tmap_df = ()  # to be set

    @classmethod
    # TODO: reading new-style consequences is missing
    def read(cls, dstore, oqparam):
        """
        :param dstore: a DataStore instance
        :returns: a :class:`CompositeRiskModel` instance
        """
        risklist = RiskFuncList()
        if hasattr(dstore, 'get_attr'):
            # missing only in Aristotle mode, where dstore is an hdf5.File
            risklist.limit_states = dstore.get_attr('crm', 'limit_states')
        df = dstore.read_df('crm')
        for i, rf_json in enumerate(df.riskfunc):
            rf = hdf5.json_to_obj(rf_json)
            try:
                rf.peril = df.loc[i].peril
            except AttributeError:  # in engine < 3.22 the peril was not stored
                rf.peril = 'groundshaking'
            lt = rf.loss_type
            if rf.kind == 'fragility':  # rf is a FragilityFunctionList
                risklist.append(rf)
            else:  # rf is a vulnerability function
                rf.init()
                if lt.endswith('_retrofitted'):
                    # strip _retrofitted, since len('_retrofitted') = 12
                    rf.loss_type = lt[:-12]
                    rf.kind = 'vulnerability_retrofitted'
                else:
                    rf.loss_type = lt
                    rf.kind = 'vulnerability'
                risklist.append(rf)
        crm = CompositeRiskModel(oqparam, risklist)
        if 'taxmap' in dstore:
            crm.tmap_df = dstore.read_df('taxmap')
        return crm

    def __init__(self, oqparam, risklist, consdict=()):
        self.oqparam = oqparam
        self.risklist = risklist  # by taxonomy
        self.consdict = consdict or {}  # new style consequences, by anything
        self.init()

    def set_tmap(self, tmap_df, taxidx):
        """
        Set the attribute .tmap_df if the risk IDs in the
        taxonomy mapping are consistent with the fragility functions.
        """
        self.tmap_df = tmap_df
        if 'consequence' not in self.oqparam.inputs:
            return
        csq_files = []
        for fnames in self.oqparam.inputs['consequence'].values():
            if isinstance(fnames, list):
                csq_files.extend(fnames)
            else:
                csq_files.append(fnames)
        for fname in csq_files:
            check_consequences(fname, set(taxidx), self.perils)
        for byname, coeffs in self.consdict.items():
            # reduce the consdict to the taxonomies in the exposure
            self.consdict[byname] = {taxidx[taxo]: arr
                                     for taxo, arr in coeffs.items()
                                     if taxo in taxidx}

    def check_risk_ids(self, inputs):
        """
        Check that there are no missing risk IDs for some risk functions
        """
        ids_by_kind = AccumDict(accum=set())
        for riskfunc in self.risklist:
            ids_by_kind[riskfunc.kind].add(riskfunc.id)
        kinds = tuple(ids_by_kind)  # vulnerability, fragility, ...
        fnames = [fname for kind, fname in inputs.items() if kind.endswith(kinds)]
        if len(ids_by_kind) > 1:
            k = next(iter(ids_by_kind))
            base_ids = set(ids_by_kind.pop(k))
            for kind, ids in ids_by_kind.items():
                if ids != base_ids:
                    raise NameError(
                        'Check in the files %s the IDs %s' %
                        (fnames, sorted(base_ids.symmetric_difference(ids))))

        if self._riskmodels:
            for peril in self.perils:
                # check imt_by_lt has consistent loss types for all taxonomies
                missing = AccumDict(accum=[])
                rms = []
                if len(self.tmap_df):
                    if len(self.tmap_df.peril.unique()) == 1:
                        risk_ids = self.tmap_df.risk_id
                    else:
                        risk_ids = self.tmap_df[self.tmap_df.peril==peril].risk_id
                    for risk_id in risk_ids.unique():
                        rms.append(self._riskmodels[risk_id])
                else:
                    rms.extend(self._riskmodels.values())
                for rm in rms:
                    # NB: in event_based_risk/case_8 the loss types are
                    # area, number, occupants, residents
                    for lt in self.loss_types:
                        try:
                            rm.imt_by_lt[lt]
                        except KeyError:
                            key = '%s/%s/%s' % (peril, kinds[0], lt)
                            fname = self.oqparam._risk_files[key]
                            missing[fname].append(rm.taxonomy)
                if missing:
                    for fname, ids in missing.items():
                        raise InvalidFile(
                            '%s: missing %s %s' % (fname, peril, ' '.join(ids)))

    def compute_csq(self, assets, dd5, tmap_df, oq):
        """
        :param assets: asset array
        :param dd5: distribution functions of shape (P, A, E, L, D)
        :param tmap_df: DataFrame corresponding to the given taxonomy
        :param oq: OqParam instance with .loss_types and .time_event
        :returns: a dict consequence_name, loss_type -> array[P, A, E]
        """
        # by construction all assets have the same taxonomy
        taxi = assets[0]['taxonomy']
        P, A, E, _L, _D = dd5.shape
        csq = AccumDict(accum=numpy.zeros((P, A, E)))
        for byname, coeffs in self.consdict.items():
            # ex. byname = "losses_by_taxonomy"
            if len(coeffs):
                consequence, _tagname = byname.split('_by_')
                for risk_id, df in tmap_df.groupby('risk_id'):
                    for li, lt in enumerate(oq.loss_types):
                        # dict loss_type -> coeffs for the given loss type
                        for pi, peril in enumerate(self.perils):
                            if len(df) == 1:
                                [w] = df.weight
                            else:  # assume one weigth per peril
                                [w] = df[df.peril == peril].weight
                            coeff = (dd5[pi, :, :, li, 1:] @
                                     coeffs[taxi][peril][lt] * w)
                            cAE = scientific.consequence(
                                consequence, assets, coeff, lt, oq.time_event)
                            csq[consequence, li][pi] += cAE
        return csq

    def init(self):
        oq = self.oqparam
        if self.risklist:
            self.perils = oq.set_risk_imts(self.risklist)
        self.damage_states = []
        self._riskmodels = {}  # riskid -> crmodel
        if oq.calculation_mode.endswith('_bcr'):
            # classical_bcr calculator
            for riskid, risk_functions in self.risklist.groupby_id().items():
                self._riskmodels[riskid] = get_riskmodel(riskid, oq, risk_functions)
        elif (any(rf.kind == 'fragility' for rf in self.risklist) or
              'damage' in oq.calculation_mode):
            # classical_damage/scenario_damage calculator
            if oq.calculation_mode in ('classical', 'scenario'):
                # case when the risk files are in the job_hazard.ini file
                oq.calculation_mode += '_damage'
                if 'exposure' not in oq.inputs:
                    raise RuntimeError(
                        'There are risk files in %r but not '
                        'an exposure' % oq.inputs['job_ini'])

            self.damage_states = ['no_damage'] + list(
                self.risklist.limit_states)
            for riskid, ffs_by_lt in self.risklist.groupby_id().items():
                self._riskmodels[riskid] = get_riskmodel(riskid, oq, ffs_by_lt)
        else:
            # classical, event based and scenario calculators
            for riskid, vfs in self.risklist.groupby_id().items():
                self._riskmodels[riskid] = get_riskmodel(riskid, oq, vfs)
        self.imtls = oq.imtls
        self.lti = {}  # loss_type -> idx
        self.covs = 0  # number of coefficients of variation
        # build a sorted list with all the loss_types contained in the model
        ltypes = set()
        for rm in self.values():
            ltypes.update(rm.loss_types)
        self.loss_types = sorted(ltypes)
        self.riskids = set()
        self.distributions = set()
        for riskid, rm in self._riskmodels.items():
            self.riskids.add(riskid)
            rm.compositemodel = self
            for lt, rf in rm.risk_functions.items():
                if hasattr(rf, 'distribution_name'):
                    self.distributions.add(rf.distribution_name)
                if hasattr(rf, 'init'):  # vulnerability function
                    if oq.ignore_covs:
                        rf.covs = numpy.zeros_like(rf.covs)
                    rf.init()
                # save the number of nonzero coefficients of variation
                if hasattr(rf, 'covs') and rf.covs.any():
                    self.covs += 1
        self.curve_params = self.make_curve_params()

        # possibly set oq.minimum_intensity
        iml = collections.defaultdict(list)
        # ._riskmodels is empty if read from the hazard calculation
        for riskid, rm in self._riskmodels.items():
            for lt, rf in rm.risk_functions['groundshaking'].items():
                iml[rf.imt].append(rf.imls[0])

        if oq.impact:
            pass  # don't set minimum_intensity
        elif sum(oq.minimum_intensity.values()) == 0 and iml:
            oq.minimum_intensity = {imt: min(ls) for imt, ls in iml.items()}

    def eid_dmg_dt(self):
        """
        :returns: a dtype (eid, dmg)
        """
        L = len(self.lti)
        D = len(self.damage_states)
        return numpy.dtype([('eid', U32), ('dmg', (F32, (L, D)))])

    def asset_damage_dt(self, float_dmg_dist):
        """
        :returns: a composite dtype with damages and consequences
        """
        dt = F32 if float_dmg_dist else U32
        descr = ([('agg_id', U32), ('event_id', U32), ('loss_id', U8)] +
                 [(dc, dt) for dc in self.get_dmg_csq()])
        return numpy.dtype(descr)

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
        for consequence_by_tagname, arr in self.consdict.items():
            if len(arr):
                csq.append(consequence_by_tagname.split('_by_')[0])
        return csq

    def get_dmg_csq(self):
        """
        :returns: damage states (except no_damage) plus consequences
        """
        D = len(self.damage_states)
        dmgs = ['dmg_%d' % d for d in range(1, D)]
        return dmgs + self.get_consequences()

    def multi_damage_dt(self):
        """
        :returns: composite datatype with fields peril-loss_type-damage_state
        """
        dcs = self.damage_states + self.get_consequences()
        if len(self.perils) == 1:
            lst = [(f'{ltype}-{dc}', F32)
                   for ltype in self.oqparam.loss_types for dc in dcs]
            return numpy.dtype(lst)
        lst = []
        for peril in self.perils:
            for ltype in self.oqparam.loss_types:
                for dc in dcs:
                    lst.append((f'{peril}-{ltype}-{dc}', F32))
        return numpy.dtype(lst)

    def to_multi_damage(self, array5d):
        """
        :param array5d: array of shape (P, A, R, L, Dc)
        :returns: array of shape (A, R) of dtype multi_damage_dt
        """
        P, A, R, L, Dc = array5d.shape
        arr = numpy.zeros((A, R), self.multi_damage_dt())
        for a in range(A):
            for r in range(R):
                lst = []
                for pi in range(P):
                    for li in range(L):
                        for di in range(Dc):
                            lst.append(array5d[pi, a, r, li, di])
                arr[a, r] = tuple(lst)
        return arr
        
    def make_curve_params(self):
        # the CurveParams are used only in classical_risk, classical_bcr
        # NB: populate the inner lists .loss_types too
        cps = []
        for lti, loss_type in enumerate(self.loss_types):
            if self.oqparam.calculation_mode in (
                    'classical', 'classical_risk'):
                curve_resolutions = set()
                lines = []
                allratios = []
                for taxo in sorted(self):
                    rm = self[taxo]
                    rf = rm.risk_functions['groundshaking'][loss_type]
                    if loss_type in rm.loss_ratios:
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
                    lti, loss_type, max(curve_resolutions), allratios[-1], True
                ) if curve_resolutions else scientific.CurveParams(
                    lti, loss_type, 0, [], False)
            else:  # used only to store the association l -> loss_type
                cp = scientific.CurveParams(lti, loss_type, 0, [], False)
            cps.append(cp)
            self.lti[loss_type] = lti
        return cps

    def get_loss_ratios(self):
        """
        :returns: a 1-dimensional composite array with loss ratios by loss type
        """
        lst = [('user_provided', bool)]
        for cp in self.curve_params:
            lst.append((cp.loss_type, F32, len(cp.ratios)))
        loss_ratios = numpy.zeros(1, numpy.dtype(lst))
        for cp in self.curve_params:
            loss_ratios['user_provided'] = cp.user_provided
            loss_ratios[cp.loss_type] = tuple(cp.ratios)
        return loss_ratios

    def __getitem__(self, taxo):
        return self._riskmodels[taxo]

    def get_outputs(self, asset_df, haz, sec_losses=(), rndgen=None, country='?'):
        """
        :param asset_df: a DataFrame of assets with the same taxonomy and country
        :param haz: a DataFrame of GMVs on the sites of the assets
        :param sec_losses: a list of functions
        :param rndgen: a MultiEventRNG instance
        :returns: a list of dictionaries loss_type-> output
        """
        # rc.pprint()
        # dic = rc.todict()
        # rc2 = get_riskcomputer(dic)
        # dic2 = rc2.todict()
        # _assert_equal(dic, dic2)
        [taxidx] = asset_df.taxonomy.unique()
        rc = scientific.RiskComputer(self, taxidx, country)
        out = rc.output(asset_df, haz, sec_losses, rndgen)
        return list(out)

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

    def get_attrs(self):
        loss_types = hdf5.array_of_vstr(self.loss_types)
        limit_states = hdf5.array_of_vstr(self.damage_states[1:]
                                          if self.damage_states else [])
        attrs = dict(covs=self.covs, loss_types=loss_types,
                     limit_states=limit_states,
                     consequences=self.get_consequences())
        rf = next(iter(self.values()))
        if hasattr(rf, 'loss_ratios'):
            for lt in self.loss_types:
                attrs['loss_ratios_' + lt] = rf.loss_ratios[lt]
        return attrs

    def to_dframe(self):
        """
        :returns: a DataFrame containing all risk functions
        """
        dic = {'peril': [], 'riskid': [], 'loss_type': [], 'riskfunc': []}
        for riskid, rm in self._riskmodels.items():
            for peril, rfdict in rm.risk_functions.items():
                for lt, rf in rfdict.items():
                    dic['peril'].append(peril)
                    dic['riskid'].append(riskid)
                    dic['loss_type'].append(lt)
                    dic['riskfunc'].append(hdf5.obj_to_json(rf))
        return pandas.DataFrame(dic)

    def __repr__(self):
        lines = ['%s: %s' % item for item in sorted(self.items())]
        return '<%s\n%s>' % (self.__class__.__name__, '\n'.join(lines))
