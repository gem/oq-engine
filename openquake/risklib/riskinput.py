# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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

import copy
import logging
import collections
from urllib.parse import unquote_plus
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import (
    AccumDict, group_array, cached_property)
from openquake.risklib import scientific, riskmodels


class ValidationError(Exception):
    pass


U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32


class TaxonomyMapping(dict):
    """
    A dictionary taxonomy -> kind -> {ids, weights}
    serializable to HDF5 as an array with fields
    taxonomy, fragility_ids, fragility_weights, consequence_ids,
    consequence_weights, vulnerability_ids, vulnerability_weights.
    """
    dt = numpy.dtype([('taxonomy', hdf5.vstr),
                      ('fragility_ids', hdf5.vstr),
                      ('fragility_weights', hdf5.vfloat64),
                      ('consequence_ids', hdf5.vstr),
                      ('consequence_weights', hdf5.vfloat64),
                      ('vulnerability_ids', hdf5.vstr),
                      ('vulnerability_weights', hdf5.vfloat64)])

    def __toh5__(self):
        data = []
        for taxonomy, dic in self.items():
            row = (taxonomy,
                   ' '.join(dic['fragility']['ids']),
                   numpy.array(dic['fragility']['weights']),
                   ' '.join(dic['consequence']['ids']),
                   numpy.array(dic['consequence']['weights']),
                   ' '.join(dic['vulnerability']['ids']),
                   numpy.array(dic['vulnerability']['weights']))
            data.append(row)
        return numpy.array(data, self.dt), {}

    def __fromh5__(self, array, dic):
        for rec in array:
            f = dict(ids=rec['fragility_ids'].split(),
                     weights=rec['fragility_weights'])
            c = dict(ids=rec['consequence_ids'].split(),
                     weights=rec['consequence_weights'])
            v = dict(ids=rec['vulnerability_ids'].split(),
                     weights=rec['vulnerability_weights'])
            self[rec['taxonomy']] = dict(
                fragility=f, consequence=c, vulnerability=v)


def get_assets_by_taxo(assets, epspath=None):
    """
    :param assets: an array of assets
    :param epspath: hdf5 file where the epsilons are (or None)
    :returns: assets_by_taxo with attributes eps and idxs
    """
    assets_by_taxo = AccumDict(group_array(assets, 'taxonomy'))
    assets_by_taxo.idxs = numpy.argsort(numpy.concatenate([
        a['ordinal'] for a in assets_by_taxo.values()]))
    assets_by_taxo.eps = {}
    if epspath is None:  # no epsilons
        return assets_by_taxo
    # otherwise read the epsilons and group them by taxonomy
    with hdf5.File(epspath, 'r') as h5:
        dset = h5['epsilon_matrix']
        for taxo, assets in assets_by_taxo.items():
            lst = [dset[aid] for aid in assets['ordinal']]
            assets_by_taxo.eps[taxo] = numpy.array(lst)
    return assets_by_taxo


class CompositeRiskModel(collections.Mapping):
    """
    A container (riskid, kind) -> riskmodel

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param tmap:
        a taxonomy mapping
    :param fragdict:
        a dictionary riskid -> loss_type -> fragility functions
    :param vulndict:
        a dictionary riskid -> loss_type -> vulnerability function
    :param consdict:
        a dictionary riskid -> loss_type -> consequence functions
    :param retrodict:
        a dictionary riskid -> loss_type -> vulnerability function
    """
    @classmethod
    def read(cls, dstore):
        """
        :param dstore: a DataStore instance
        :returns: a :class:`CompositeRiskModel` instance
        """
        oqparam = dstore['oqparam']
        tmap = (dstore['taxonomy_mapping'] if 'taxonomy_mapping' in dstore
                else {})
        crm = dstore.getitem('risk_model')
        # building dictionaries riskid -> loss_type -> risk_func
        fragdict, vulndict, consdict, retrodict = (
            AccumDict(), AccumDict(), AccumDict(), AccumDict())
        fragdict.limit_states = crm.attrs['limit_states']
        for quoted_id, rm in crm.items():
            riskid = unquote_plus(quoted_id)
            fragdict[riskid] = {}
            vulndict[riskid] = {}
            consdict[riskid] = {}
            retrodict[riskid] = {}
            for lt_kind in rm:
                lt, kind = lt_kind.rsplit('-', 1)
                rf = dstore['risk_model/%s/%s' % (quoted_id, lt_kind)]
                if kind == 'consequence':
                    consdict[riskid][lt, kind] = rf
                elif kind == 'fragility':  # rf is a FragilityFunctionList
                    try:
                        rf = rf.build(
                            fragdict.limit_states,
                            oqparam.continuous_fragility_discretization,
                            oqparam.steps_per_interval)
                    except ValueError as err:
                        raise ValueError('%s: %s' % (riskid, err))
                    fragdict[riskid][lt, kind] = rf
                else:  # rf is a vulnerability function
                    rf.init()
                    if lt.endswith('_retrofitted'):
                        # strip _retrofitted, since len('_retrofitted') = 12
                        retrodict[riskid][lt[:-12], kind] = rf
                    else:
                        vulndict[riskid][lt, kind] = rf
        return CompositeRiskModel(
            oqparam, tmap, fragdict, vulndict, consdict, retrodict)

    def __init__(self, oqparam, tmap, fragdict, vulndict, consdict, retrodict):
        self.tmap = tmap
        self.damage_states = []
        self._riskmodels = {}  # riskid -> riskmodel
        self.consequences = sum(len(vals) for vals in consdict.values())
        if sum(len(v) for v in fragdict.values()):
            # classical_damage/scenario_damage calculator
            if oqparam.calculation_mode in ('classical', 'scenario'):
                # case when the risk files are in the job_hazard.ini file
                oqparam.calculation_mode += '_damage'
                if 'exposure' not in oqparam.inputs:
                    raise RuntimeError(
                        'There are risk files in %r but not '
                        'an exposure' % oqparam.inputs['job_ini'])
            self.damage_states = ['no_damage'] + list(fragdict.limit_states)
            for riskid, ffs_by_lt in fragdict.items():
                self._riskmodels[riskid] = (
                    riskmodels.get_riskmodel(
                        riskid, oqparam, fragility_functions=ffs_by_lt,
                        vulnerability_functions=vulndict[riskid],
                        consequence_functions=consdict[riskid]))
            self.kind = 'fragility'
        elif oqparam.calculation_mode.endswith('_bcr'):
            # classical_bcr calculator
            for (riskid, vf_orig), (riskid_, vf_retro) in \
                    zip(sorted(vulndict.items()), sorted(retrodict.items())):
                assert riskid == riskid_  # same IDs
                self._riskmodels[riskid] = (
                    riskmodels.get_riskmodel(
                        riskid, oqparam,
                        vulnerability_functions_orig=vf_orig,
                        vulnerability_functions_retro=vf_retro))
            self.kind = 'vulnerability'
        else:
            # classical, event based and scenario calculators
            for riskid, vfs in vulndict.items():
                for vf in vfs.values():
                    # set the seed; this is important for the case of
                    # VulnerabilityFunctionWithPMF
                    vf.seed = oqparam.random_seed
                self._riskmodels[riskid] = (
                    riskmodels.get_riskmodel(
                        riskid, oqparam, fragility_functions=vulndict[riskid],
                        vulnerability_functions=vfs))
            self.kind = 'vulnerability'

        self.init(oqparam)

    def init(self, oqparam):
        imti = {imt: i for i, imt in enumerate(oqparam.imtls)}
        self.lti = {}  # loss_type -> idx
        self.covs = 0  # number of coefficients of variation
        # build a sorted list with all the loss_types contained in the model
        ltypes = set()
        for rm in self.values():
            ltypes.update(rm.loss_types)
        self.loss_types = sorted(ltypes)

        taxonomies = set()
        for riskid, riskmodel in self._riskmodels.items():
            taxonomies.add(riskid)
            riskmodel.compositemodel = self
            for lt, vf in riskmodel.risk_functions.items():
                # save the number of nonzero coefficients of variation
                if hasattr(vf, 'covs') and vf.covs.any():
                    self.covs += 1
            missing = set(self.loss_types) - set(
                lt for lt, kind in riskmodel.risk_functions)
            if missing:
                raise ValidationError(
                    'Missing vulnerability function for taxonomy %s and loss'
                    ' type %s' % (riskid, ', '.join(missing)))
            riskmodel.imti = {lt: imti[riskmodel.risk_functions[lt, kind].imt]
                              for lt, kind in riskmodel.risk_functions}

        self.taxonomies = sorted(taxonomies)
        self.curve_params = self.make_curve_params(oqparam)
        iml = collections.defaultdict(list)
        for riskid, rm in self._riskmodels.items():
            for lt, rf in rm.risk_functions.items():
                iml[rf.imt].append(rf.imls[0])
        self.min_iml = {imt: min(iml[imt]) for imt in iml}

    @cached_property
    def taxonomy_dict(self):
        """
        :returns: a dict taxonomy string -> taxonomy index
        """
        # .taxonomy must be set by the engine
        tdict = {taxo: idx for idx, taxo in enumerate(self.taxonomy)}
        return tdict

    def get_extra_imts(self, imts):
        """
        Returns the extra IMTs in the risk functions, i.e. the ones not in
        the `imts` set (the set of IMTs for which there is hazard).
        """
        extra_imts = set()
        for taxonomy in self.taxonomies:
            for (lt, kind), rf in self[taxonomy].risk_functions.items():
                if rf.imt not in imts:
                    extra_imts.add(rf.imt)
        return extra_imts

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
                    if loss_type in rm.loss_ratios:
                        ratios = rm.loss_ratios[loss_type]
                        allratios.append(ratios)
                        curve_resolutions.add(len(ratios))
                        lines.append('%s %d' % (
                            rm.vulnerability_functions[
                                loss_type, 'vulnerability'], len(ratios)))
                if len(curve_resolutions) > 1:
                    # number of loss ratios is not the same for all taxonomies:
                    # then use the longest array; see classical_risk case_5
                    allratios.sort(key=len)
                    for rm in self.values():
                        if rm.loss_ratios[loss_type] != allratios[-1]:
                            rm.loss_ratios[loss_type] = allratios[-1]
                            logging.debug('Redefining loss ratios for %s', rm)
                cp = scientific.CurveParams(
                    l, loss_type, max(curve_resolutions), allratios[-1], True)
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

    def __getitem__(self, key):
        if isinstance(key, (int, U16)):  # a taxonomy index
            key = self.taxonomy[key]
        return self._riskmodels[key]

    def __iter__(self):
        return iter(sorted(self._riskmodels))

    def __len__(self):
        return len(self._riskmodels)

    # used in multi_risk
    def get_dmg_csq(self, assets_by_site, gmf):
        """
        :returns:
            an array of shape (A, L, 1, D + 1) with the number of buildings
            in each damage state for each asset and loss type
        """
        A = sum(len(assets) for assets in assets_by_site)
        L = len(self.loss_types)
        D = len(self.damage_states)
        out = numpy.zeros((A, L, 1, D + 1), F32)
        for assets, gmv in zip(assets_by_site, gmf):
            group = group_array(assets, 'taxonomy')
            for taxonomy, assets in group.items():
                for l, loss_type in enumerate(self.loss_types):
                    fracs = self[taxonomy](loss_type, assets, [gmv])
                    for asset, frac in zip(assets, fracs):
                        dmg = asset['number'] * frac[0, :D]
                        csq = asset['value-' + loss_type] * frac[0, D]
                        out[asset['ordinal'], l, 0, :D] = dmg
                        out[asset['ordinal'], l, 0, D] = csq
        return out

    def gen_outputs(self, riskinput, monitor, epspath=None, hazard=None):
        """
        Group the assets per taxonomy and compute the outputs by using the
        underlying riskmodels. Yield one output per realization.

        :param riskinput: a RiskInput instance
        :param monitor: a monitor object used to measure the performance
        """
        self.monitor = monitor
        hazard_getter = riskinput.hazard_getter
        if hazard is None:
            with monitor('getting hazard'):
                hazard_getter.init()
                hazard = hazard_getter.get_hazard()
        sids = hazard_getter.sids
        assert len(sids) == 1
        with monitor('computing risk', measuremem=False):
            # this approach is slow for event_based_risk since a lot of
            # small arrays are passed (one per realization) instead of
            # a long array with all realizations; ebrisk does the right
            # thing since it calls get_output directly
            assets_by_taxo = get_assets_by_taxo(riskinput.assets, epspath)
            for rlzi, haz in sorted(hazard[sids[0]].items()):
                out = self.get_output(assets_by_taxo, haz, rlzi)
                yield out

    def get_output(self, assets_by_taxo, haz, rlzi=None):
        """
        :param assets_by_taxo: a dictionary taxonomy index -> assets on a site
        :param haz: an array or a dictionary of hazard on that site
        :param rlzi: if given, a realization index
        """
        if isinstance(haz, numpy.ndarray):
            # NB: in GMF-based calculations the order in which
            # the gmfs are stored is random since it depends on
            # which hazard task ends first; here we reorder
            # the gmfs by event ID; this is convenient in
            # general and mandatory for the case of
            # VulnerabilityFunctionWithPMF, otherwise the
            # sample method would receive the means in random
            # order and produce random results even if the
            # seed is set correctly; very tricky indeed! (MS)
            haz.sort(order='eid')
            eids = haz['eid']
            data = haz['gmv']  # shape (E, M)
        elif not haz:  # no hazard for this site
            eids = numpy.arange(1)
            data = []
        else:  # classical
            eids = []
            data = haz  # shape M
        dic = dict(eids=eids)
        if rlzi is not None:
            dic['rlzi'] = rlzi
        for l, lt in enumerate(self.loss_types):
            ls = []
            for taxonomy, assets_ in assets_by_taxo.items():
                if len(assets_by_taxo.eps):
                    epsilons = assets_by_taxo.eps[taxonomy][:, eids]
                else:  # no CoVs
                    epsilons = ()
                rm = self[taxonomy]
                if len(data) == 0:
                    dat = [0]
                elif len(eids):  # gmfs
                    dat = data[:, rm.imti[lt]]
                else:  # hcurves
                    dat = data[rm.imti[lt]]
                ls.append(rm(lt, assets_, dat, eids, epsilons))
            arr = numpy.concatenate(ls)
            dic[lt] = arr[assets_by_taxo.idxs] if len(arr) else arr
        return hdf5.ArrayWrapper((), dic)

    def reduce(self, taxonomies):
        """
        :param taxonomies: a set of taxonomies
        :returns: a new CompositeRiskModel reduced to the given taxonomies
        """
        new = copy.copy(self)
        new.taxonomies = sorted(taxonomies)
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
        dic = dict(covs=self.covs, loss_types=loss_types,
                   limit_states=limit_states)
        rf = next(iter(self.values()))
        if hasattr(rf, 'loss_ratios'):
            for lt in self.loss_types:
                dic['loss_ratios_' + lt] = rf.loss_ratios[lt]
        return self._riskmodels, dic

    def __repr__(self):
        lines = ['%s: %s' % item for item in sorted(self.items())]
        return '<%s(%d, %d)\n%s>' % (
            self.__class__.__name__, len(lines), self.covs, '\n'.join(lines))


class RiskInput(object):
    """
    Contains all the assets and hazard values associated to a given
    imt and site.

    :param hazard_getter:
        a callable returning the hazard data for a given realization
    :param assets_by_site:
        array of assets, one per site
    """
    def __init__(self, hazard_getter, assets):
        self.hazard_getter = hazard_getter
        self.assets = assets
        self.weight = len(assets)
        taxonomies_set = set()
        aids = []
        for asset in self.assets:
            taxonomies_set.add(asset['taxonomy'])
            aids.append(asset['ordinal'])
        self.aids = numpy.array(aids, numpy.uint32)
        self.taxonomies = sorted(taxonomies_set)
        self.by_site = hazard_getter.__class__.__name__ != 'GmfGetter'

    @property
    def imt_taxonomies(self):
        """Return a list of pairs (imt, taxonomies) with a single element"""
        return [(self.imt, self.taxonomies)]

    def __repr__(self):
        return '<%s taxonomy=%s, %d asset(s)>' % (
            self.__class__.__name__,
            ' '.join(map(str, self.taxonomies)), len(self.aids))


# used in scenario_risk
def make_eps(asset_array, num_samples, seed, correlation):
    """
    :param asset_array: an array of assets
    :param int num_samples: the number of ruptures
    :param int seed: a random seed
    :param float correlation: the correlation coefficient
    :returns: epsilons matrix of shape (num_assets, num_samples)
    """
    assets_by_taxo = group_array(asset_array, 'taxonomy')
    eps = numpy.zeros((len(asset_array), num_samples), numpy.float32)
    for taxonomy, assets in assets_by_taxo.items():
        shape = (len(assets), num_samples)
        logging.info('Building %s epsilons for taxonomy %s', shape, taxonomy)
        zeros = numpy.zeros(shape)
        epsilons = scientific.make_epsilons(zeros, seed, correlation)
        for asset, epsrow in zip(assets, epsilons):
            eps[asset['ordinal']] = epsrow
    return eps


def cache_epsilons(dstore, oq, assetcol, riskmodel, E):
    """
    Do nothing if there are no coefficients of variation of ignore_covs is
    set. Otherwise, generate an epsilon matrix of shape (A, E) and save it
    in the cache file, by returning the path to it.
    """
    if oq.ignore_covs or not riskmodel.covs:
        return
    A = len(assetcol)
    hdf5path = dstore.hdf5cache()
    logging.info('Storing the epsilon matrix in %s', hdf5path)
    if oq.calculation_mode == 'scenario_risk':
        eps = make_eps(assetcol.array, E, oq.master_seed, oq.asset_correlation)
    else:  # event based
        if oq.asset_correlation:
            numpy.random.seed(oq.master_seed)
            eps = numpy.array([numpy.random.normal(size=E)] * A)
        else:
            seeds = oq.master_seed + numpy.arange(E)
            eps = numpy.zeros((A, E), F32)
            for i, seed in enumerate(seeds):
                numpy.random.seed(seed)
                eps[:, i] = numpy.random.normal(size=A)
    with hdf5.File(hdf5path) as cache:
        cache['epsilon_matrix'] = eps
    return hdf5path


def str2rsi(key):
    """
    Convert a string of the form 'rlz-XXXX/sid-YYYY/ZZZ'
    into a triple (XXXX, YYYY, ZZZ)
    """
    rlzi, sid, imt = key.split('/')
    return int(rlzi[4:]), int(sid[4:]), imt


def rsi2str(rlzi, sid, imt):
    """
    Convert a triple (XXXX, YYYY, ZZZ) into a string of the form
    'rlz-XXXX/sid-YYYY/ZZZ'
    """
    return 'rlz-%04d/sid-%04d/%s' % (rlzi, sid, imt)
