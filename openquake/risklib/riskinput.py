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
import operator
import logging
import collections
from urllib.parse import unquote_plus
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import (
    groupby, AccumDict, group_array, cached_property)
from openquake.risklib import scientific, riskmodels


class ValidationError(Exception):
    pass


U32 = numpy.uint32
F32 = numpy.float32


def read_composite_risk_model(dstore):
    """
    :param dstore: a DataStore instance
    :returns: a :class:`CompositeRiskModel` instance
    """
    oqparam = dstore['oqparam']
    crm = dstore.getitem(oqparam.risk_model)
    fragdict, vulndict, consdict, retrodict = (
        AccumDict(), AccumDict(), AccumDict(), AccumDict())
    fragdict.limit_states = crm.attrs['limit_states']
    for riskmodel in ('fragility', 'vulnerability', 'consequence'):
        if riskmodel not in dstore:
            continue
        for quotedtaxonomy, rm in crm.items():
            taxo = unquote_plus(quotedtaxonomy)
            fragdict[taxo] = {}
            vulndict[taxo] = {}
            consdict[taxo] = {}
            retrodict[taxo] = {}
            for lt in rm:
                rf = dstore['%s/%s/%s' % (riskmodel, quotedtaxonomy, lt)]
                if riskmodel == 'consequence':
                    # TODO: manage this case by adding HDF5-serialization
                    # to the consequence model
                    pass
                elif riskmodel == 'fragility':  # rf is a FragilityFunctionList
                    try:
                        rf = rf.build(
                            fragdict.limit_states,
                            oqparam.continuous_fragility_discretization,
                            oqparam.steps_per_interval)
                    except ValueError as err:
                        raise ValueError('%s: %s' % (taxo, err))
                    fragdict[taxo][lt] = rf
                else:  # rf is a vulnerability function
                    rf.init()
                    if lt.endswith('_retrofitted'):
                        # strip _retrofitted, since len('_retrofitted') = 12
                        retrodict[taxo][lt[:-12]] = rf
                    else:
                        vulndict[taxo][lt] = rf
    return CompositeRiskModel(oqparam, fragdict, vulndict, consdict, retrodict)


class CompositeRiskModel(collections.Mapping):
    """
    A container taxonomy -> riskmodel

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param fragdict:
        a dictionary taxonomy -> loss_type -> fragility functions
    :param vulndict:
        a dictionary taxonomy -> loss_type -> vulnerability function
    :param consdict:
        a dictionary taxonomy -> loss_type -> consequence functions
    :param retrodict:
        a dictionary taxonomy -> loss_type -> vulnerability function
    """
    def __init__(self, oqparam, fragdict, vulndict, consdict, retrodict):
        self.damage_states = []
        self._riskmodels = {}

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
            for taxonomy, ffs_by_lt in fragdict.items():
                self._riskmodels[taxonomy] = riskmodels.get_riskmodel(
                    taxonomy, oqparam, fragility_functions=ffs_by_lt,
                    vulnerability_functions=vulndict[taxonomy],
                    consequence_functions=consdict[taxonomy])
        elif oqparam.calculation_mode.endswith('_bcr'):
            # classical_bcr calculator
            for (taxonomy, vf_orig), (taxonomy_, vf_retro) in \
                    zip(sorted(vulndict.items()), sorted(retrodict.items())):
                assert taxonomy == taxonomy_  # same taxonomies
                self._riskmodels[taxonomy] = riskmodels.get_riskmodel(
                    taxonomy, oqparam,
                    vulnerability_functions_orig=vf_orig,
                    vulnerability_functions_retro=vf_retro)
        else:
            # classical, event based and scenario calculators
            for taxonomy, vfs in vulndict.items():
                for vf in vfs.values():
                    # set the seed; this is important for the case of
                    # VulnerabilityFunctionWithPMF
                    vf.seed = oqparam.random_seed
                self._riskmodels[taxonomy] = riskmodels.get_riskmodel(
                    taxonomy, oqparam, fragility_functions=vulndict[taxonomy],
                    vulnerability_functions=vfs)

        self.init(oqparam)

    # used in ebrisk
    def get_assets_ratios(self, assets, gmvs, imts):
        """
        :param assets: assets on the same site
        :params gmvs: hazard on the given site, shape (E, M)
        :param imts: intensity measure types
        :returns: a list of (assets, loss_ratios) for each taxonomy on the site
        """
        imti = {imt: i for i, imt in enumerate(imts)}
        assets_by_t = groupby(assets, operator.attrgetter('taxonomy'))
        assets_ratios = []
        for taxo, rm in self.items():
            t = self.taxonomy_dict[taxo]
            try:
                assets = assets_by_t[t]
            except KeyError:  # there are no assets of taxonomy taxo
                continue
            assets_ratios.append((assets, rm.get_loss_ratios(gmvs, imti)))
        return assets_ratios

    def init(self, oqparam):
        self.lti = {}  # loss_type -> idx
        self.covs = 0  # number of coefficients of variation
        self.curve_params = self.make_curve_params(oqparam)
        self.loss_types = [cp.loss_type for cp in self.curve_params]
        self.taxonomy = []  # must be set by the engine
        expected_loss_types = set(self.loss_types)
        taxonomies = set()
        for taxonomy, riskmodel in self._riskmodels.items():
            taxonomies.add(taxonomy)
            riskmodel.compositemodel = self
            # save the number of nonzero coefficients of variation
            for vf in riskmodel.risk_functions.values():
                if hasattr(vf, 'covs') and vf.covs.any():
                    self.covs += 1
            missing = expected_loss_types - set(riskmodel.risk_functions)
            if missing:
                raise ValidationError(
                    'Missing vulnerability function for taxonomy %s and loss'
                    ' type %s' % (taxonomy, ', '.join(missing)))
        self.taxonomies = sorted(taxonomies)
        iml = collections.defaultdict(list)
        for taxo, rm in self._riskmodels.items():
            for lt, rf in rm.risk_functions.items():
                iml[rf.imt].append(rf.imls[0])
        self.min_iml = {imt: min(iml[imt]) for imt in iml}

    @cached_property
    def taxonomy_dict(self):
        """
        :returns: a dict taxonomy string -> taxonomy index
        """
        tdict = {taxo: idx for idx, taxo in enumerate(self.taxonomy)}
        return tdict

    def get_extra_imts(self, imts):
        """
        Returns the extra IMTs in the risk functions, i.e. the ones not in
        the `imts` set (the set of IMTs for which there is hazard).
        """
        extra_imts = set()
        for taxonomy in self.taxonomies:
            for lt in self.loss_types:
                imt = self[taxonomy].risk_functions[lt].imt
                if imt not in imts:
                    extra_imts.add(imt)
        return extra_imts

    def make_curve_params(self, oqparam):
        # the CurveParams are used only in classical_risk, classical_bcr
        # NB: populate the inner lists .loss_types too
        cps = []
        loss_types = self._get_loss_types()
        for l, loss_type in enumerate(loss_types):
            if oqparam.calculation_mode in ('classical', 'classical_risk'):
                curve_resolutions = set()
                lines = []
                for key in sorted(self):
                    rm = self[key]
                    if loss_type in rm.loss_ratios:
                        ratios = rm.loss_ratios[loss_type]
                        curve_resolutions.add(len(ratios))
                        lines.append('%s %d' % (
                            rm.vulnerability_functions[loss_type], len(ratios))
                        )
                if len(curve_resolutions) > 1:  # example in test_case_5
                    logging.debug(
                        'Different num_loss_ratios:\n%s', '\n'.join(lines))
                cp = scientific.CurveParams(
                    l, loss_type, max(curve_resolutions), ratios, True)
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

    def _get_loss_types(self):
        """
        :returns: a sorted list with all the loss_types contained in the model
        """
        ltypes = set()
        for rm in self.values():
            ltypes.update(rm.loss_types)
        return sorted(ltypes)

    def __getitem__(self, taxonomy):
        try:
            return self._riskmodels[taxonomy]
        except KeyError:  # taxonomy was an index
            taxo = self.taxonomy[taxonomy]
            return self._riskmodels[taxo]

    def __iter__(self):
        return iter(sorted(self._riskmodels))

    def __len__(self):
        return len(self._riskmodels)

    # used in multi_risk
    def get_damage(self, assets_by_site, gmf):
        """
        :returns:
            an array of shape (A, L, 1, D) with the number of buildings
            in each damage state for each asset and loss type
        """
        A = sum(len(assets) for assets in assets_by_site)
        L = len(self.loss_types)
        D = len(self.damage_states)
        out = numpy.zeros((A, L, 1, D), F32)
        for assets, gmv in zip(assets_by_site, gmf):
            group = group_array(assets, 'taxonomy')
            for taxonomy, assets in group.items():
                for l, loss_type in enumerate(self.loss_types):
                    probs = self[taxonomy](loss_type, assets, ([gmv], None))
                    # probs has shape (1, D)
                    out[assets['ordinal'], l] = [
                        d * n for d, n in zip(probs, assets['number'])]
        return out

    # each riskinput is associated to a single site
    def gen_outputs(self, riskinput, monitor, hazard=None):
        """
        Group the assets per taxonomy and compute the outputs by using the
        underlying riskmodels. Yield the outputs generated as dictionaries
        out_by_lr.

        :param riskinput: a RiskInput instance
        :param monitor: a monitor object used to measure the performance
        """
        self.monitor = monitor
        hazard_getter = riskinput.hazard_getter
        if hazard is None:
            with monitor('getting hazard'):
                hazard_getter.init()
                hazard = hazard_getter.get_hazard()

        # group the assets by taxonomy
        dic = collections.defaultdict(list)
        group = group_array(riskinput.assets, 'taxonomy')
        for taxonomy in group:
            dic[taxonomy].append(
                (group[taxonomy], riskinput.epsilon_getter))
        yield from self._gen_outputs(hazard_getter, hazard, dic)

    def _gen_outputs(self, hazard_getter, hazard, dic):
        imti = {imt: i for i, imt in enumerate(hazard_getter.imts)}
        mon = self.monitor('computing risk', measuremem=False)
        for taxonomy in sorted(dic):
            riskmodel = self[taxonomy]
            imts = [riskmodel.risk_functions[lt].imt
                    for lt in self.loss_types]  # imt for each loss type
            # discard IMTs without hazard
            imt_lt = [imt for imt in imts if imt in imti]
            if not imt_lt:  # a warning is printed in riskmodel.check_imts
                continue
            for assets, epsgetter in dic[taxonomy]:
                if not isinstance(hazard, dict):
                    hazard = group_array(hazard, 'rlzi')
                for rlzi, haz in sorted(hazard.items()):
                    with mon:
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
                            data = [(haz['gmv'][:, imti[imt]], eids)
                                    for imt in imt_lt]
                        elif not haz:  # no hazard for this site
                            eids = []
                            data = [(numpy.zeros(hazard_getter.E),
                                     numpy.arange(hazard_getter.E))
                                    for imt in imt_lt]
                        else:  # classical
                            eids = hazard_getter.eids
                            data = [haz[imti[imt]] for imt in imt_lt]
                        out = riskmodel.get_output(assets, data, epsgetter)
                        out.sid, = hazard_getter.sids
                        out.rlzi = rlzi
                        out.eids = eids
                    yield out

    def reduce(self, taxonomies):
        """
        :param taxonomies: a set of taxonomies
        :returns: a new CompositeRiskModel reduced to the given taxonomies
        """
        new = copy.copy(self)
        new.taxonomies = sorted(taxonomies)
        new._riskmodels = {}
        for taxo, rm in self._riskmodels.items():
            if taxo in taxonomies:
                new._riskmodels[taxo] = rm
                rm.compositemodel = new
        return new

    def __toh5__(self):
        loss_types = hdf5.array_of_vstr(self._get_loss_types())
        limit_states = hdf5.array_of_vstr(self.damage_states[1:]
                                          if self.damage_states else [])
        return self._riskmodels, dict(
            covs=self.covs, loss_types=loss_types, limit_states=limit_states)

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
    :param eps_dict:
        dictionary of epsilons (can be None)
    """
    def __init__(self, hazard_getter, assets, eps_dict=None):
        self.hazard_getter = hazard_getter
        self.assets = assets
        self.eps = eps_dict or {}
        self.weight = len(assets)
        taxonomies_set = set()
        aids = []
        for asset in assets:
            taxonomies_set.add(asset['taxonomy'])
            aids.append(asset['ordinal'])
        self.aids = numpy.array(aids, numpy.uint32)
        self.taxonomies = sorted(taxonomies_set)
        self.by_site = hazard_getter.__class__.__name__ != 'GmfGetter'

    @property
    def imt_taxonomies(self):
        """Return a list of pairs (imt, taxonomies) with a single element"""
        return [(self.imt, self.taxonomies)]

    def epsilon_getter(self, aid, eids):
        """
        :param aid: asset ordinal
        :param eids: an array of event indices
        :returns: an array of E epsilons
        """
        if len(self.eps) == 0:
            return
        try:  # from ruptures
            return self.eps[aid, eids]
        except TypeError:  # from GMFs
            return self.eps[aid][eids]

    def __repr__(self):
        return '<%s taxonomy=%s, %d asset(s)>' % (
            self.__class__.__name__,
            ' '.join(map(str, self.taxonomies)), len(self.aids))


class EpsilonMatrix0(object):
    """
    Mock-up for a matrix of epsilons of size N x E,
    used when asset_correlation=0.

    :param num_assets: N assets
    :param seeds: E seeds, set before calling numpy.random.normal
    """
    def __init__(self, num_assets, seeds):
        self.num_assets = num_assets
        self.seeds = seeds
        self.eps = None

    def make_eps(self):
        """
        Builds a matrix of A x E epsilons
        """
        eps = numpy.zeros((self.num_assets, len(self.seeds)), F32)
        for i, seed in enumerate(self.seeds):
            numpy.random.seed(seed)
            eps[:, i] = numpy.random.normal(size=self.num_assets)
        return eps

    def __getitem__(self, aid):
        if self.eps is None:
            self.eps = self.make_eps()
        return self.eps[aid]

    def __len__(self):
        return self.num_assets


class EpsilonMatrix1(object):
    """
    Mock-up for a matrix of epsilons of size A x E,
    used when asset_correlation=1.

    :param num_assets: number of assets
    :param num_events: number of events
    :param seed: seed used to generate E epsilons
    """
    def __init__(self, num_assets, num_events, seed):
        self.num_assets = num_assets
        self.num_events = num_events
        self.seed = seed
        numpy.random.seed(seed)
        self.eps = numpy.random.normal(size=num_events)

    def __getitem__(self, item):
        if isinstance(item, tuple):
            # item[0] is the asset index, item[1] the event index
            # the epsilons are equal for all assets since asset_correlation=1
            return self.eps[item[1]]
        elif isinstance(item, int):  # item is an asset index
            return self.eps
        else:
            raise TypeError('Invalid item %r' % item)

    def __len__(self):
        return self.num_assets


def make_epsilon_getter(n_assets, n_events, correlation, master_seed, no_eps):
    """
    :returns: a function (start, stop) -> matrix of shape (n_assets, n_events)
    """
    assert n_assets > 0, n_assets
    assert n_events > 0, n_events
    assert correlation in (0, 1), correlation
    assert master_seed >= 0, master_seed
    assert no_eps in (True, False), no_eps
    seeds = master_seed + numpy.arange(n_events)

    def get_eps(start=0, stop=n_events):
        if no_eps:
            eps = None
        elif correlation:
            eps = EpsilonMatrix1(n_assets, stop - start, master_seed)
        else:
            eps = EpsilonMatrix0(n_assets, seeds[start:stop])
        return eps

    return get_eps


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
