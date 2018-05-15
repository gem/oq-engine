# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

import operator
import logging
import collections
from urllib.parse import unquote_plus
import numpy

from openquake.baselib import hdf5, performance
from openquake.baselib.general import groupby, AccumDict
from openquake.risklib import scientific, riskmodels


class ValidationError(Exception):
    pass


U32 = numpy.uint32
F32 = numpy.float32
by_taxonomy = operator.attrgetter('taxonomy')
indices_dt = numpy.dtype([('start', U32), ('stop', U32)])


def read_composite_risk_model(dstore):
    """
    :param dstore: a DataStore instance
    :returns: a :class:`CompositeRiskModel` instance
    """
    oqparam = dstore['oqparam']
    crm = dstore.getitem('composite_risk_model')
    rmdict, retrodict = AccumDict(), AccumDict()
    rmdict.limit_states = crm.attrs['limit_states']
    for quotedtaxonomy, rm in crm.items():
        taxo = unquote_plus(quotedtaxonomy)
        rmdict[taxo] = {}
        retrodict[taxo] = {}
        for lt in rm:
            lt = str(lt)  # ensure Python 2-3 compatibility
            rf = dstore['composite_risk_model/%s/%s' % (quotedtaxonomy, lt)]
            if len(rmdict.limit_states):
                # rf is a FragilityFunctionList
                rf = rf.build(rmdict.limit_states,
                              oqparam.continuous_fragility_discretization,
                              oqparam.steps_per_interval)
            else:
                # rf is a vulnerability function
                rf.init()
            if lt.endswith('_retrofitted'):
                # strip _retrofitted, since len('_retrofitted') = 12
                retrodict[taxo][lt[:-12]] = rf
            else:
                rmdict[taxo][lt] = rf
    return CompositeRiskModel(oqparam, rmdict, retrodict)


class CompositeRiskModel(collections.Mapping):
    """
    A container (imt, taxonomy) -> riskmodel

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param rmdict:
        a dictionary (imt, taxonomy) -> loss_type -> risk_function
    """
    def __init__(self, oqparam, rmdict, retrodict):
        self.damage_states = []
        self._riskmodels = {}

        if len(rmdict.limit_states):
            # classical_damage/scenario_damage calculator
            if oqparam.calculation_mode in ('classical', 'scenario'):
                # case when the risk files are in the job_hazard.ini file
                oqparam.calculation_mode += '_damage'
                if 'exposure' not in oqparam.inputs:
                    raise RuntimeError(
                        'There are risk files in %r but not '
                        'an exposure' % oqparam.inputs['job_ini'])
            self.damage_states = ['no_damage'] + list(rmdict.limit_states)
            for taxonomy, ffs_by_lt in rmdict.items():
                self._riskmodels[taxonomy] = riskmodels.get_riskmodel(
                    taxonomy, oqparam, fragility_functions=ffs_by_lt)
        elif oqparam.calculation_mode.endswith('_bcr'):
            # classical_bcr calculator
            for (taxonomy, vf_orig), (taxonomy_, vf_retro) in \
                    zip(sorted(rmdict.items()), sorted(retrodict.items())):
                assert taxonomy == taxonomy_  # same taxonomies
                self._riskmodels[taxonomy] = riskmodels.get_riskmodel(
                    taxonomy, oqparam,
                    vulnerability_functions_orig=vf_orig,
                    vulnerability_functions_retro=vf_retro)
        else:
            # classical, event based and scenario calculators
            for taxonomy, vfs in rmdict.items():
                for vf in vfs.values():
                    # set the seed; this is important for the case of
                    # VulnerabilityFunctionWithPMF
                    vf.seed = oqparam.random_seed
                    self._riskmodels[taxonomy] = riskmodels.get_riskmodel(
                        taxonomy, oqparam, vulnerability_functions=vfs)

        self.init(oqparam)

    def init(self, oqparam):
        self.lti = {}  # loss_type -> idx
        self.covs = 0  # number of coefficients of variation
        self.curve_params = self.make_curve_params(oqparam)
        self.loss_types = [cp.loss_type for cp in self.curve_params]
        self.insured_losses = oqparam.insured_losses
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

    def get_min_iml(self):
        iml = collections.defaultdict(list)
        for taxo, rm in self._riskmodels.items():
            for lt, rf in rm.risk_functions.items():
                iml[rf.imt].append(rf.imls[0])
        return {imt: min(iml[imt]) for imt in iml}

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
                            rm.risk_functions[loss_type], len(ratios)))
                if len(curve_resolutions) > 1:  # example in test_case_5
                    logging.info(
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

    def gen_outputs(self, riskinput, monitor=performance.Monitor()):
        """
        Group the assets per taxonomy and compute the outputs by using the
        underlying riskmodels. Yield the outputs generated as dictionaries
        out_by_lr.

        :param riskinput: a RiskInput instance
        :param monitor: a monitor object used to measure the performance
        """
        self.monitor = monitor
        hazard_getter = riskinput.hazard_getter
        with monitor('getting hazard'):
            hazard_getter.init()
        sids = hazard_getter.sids
        # group the assets by taxonomy
        dic = collections.defaultdict(list)
        for sid, assets in zip(sids, riskinput.assets_by_site):
            group = groupby(assets, by_taxonomy)
            for taxonomy in group:
                epsgetter = riskinput.epsilon_getter
                dic[taxonomy].append((sid, group[taxonomy], epsgetter))
        if hasattr(hazard_getter, 'rlzs_by_gsim'):
            # save memory in event based risk by working one gsim at the time
            for gsim in hazard_getter.rlzs_by_gsim:
                for out in self._gen_outputs(hazard_getter, dic, gsim):
                    yield out
        else:
            for out in self._gen_outputs(hazard_getter, dic, None):
                yield out

        if hasattr(hazard_getter, 'gmdata'):  # for event based risk
            riskinput.gmdata = hazard_getter.gmdata

    def _gen_outputs(self, hazard_getter, dic, gsim):
        with self.monitor('getting hazard'):
            hazard = hazard_getter.get_hazard(gsim)
        imti = {imt: i for i, imt in enumerate(hazard_getter.imtls)}
        with self.monitor('computing risk'):
            for taxonomy in sorted(dic):
                riskmodel = self[taxonomy]
                imt_lt = [riskmodel.risk_functions[lt].imt
                          for lt in self.loss_types]  # imt for each loss type
                for sid, assets, epsgetter in dic[taxonomy]:
                    for rlzi, haz in sorted(hazard[sid].items()):
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
                                     hazard_getter.eids) for imt in imt_lt]
                        else:  # classical
                            eids = hazard_getter.eids
                            data = [haz[imti[imt]] for imt in imt_lt]
                        out = riskmodel.get_output(assets, data, epsgetter)
                        out.sid = sid
                        out.rlzi = rlzi
                        out.eids = eids
                        yield out

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
    def __init__(self, hazard_getter, assets_by_site, eps_dict=None):
        self.hazard_getter = hazard_getter
        self.assets_by_site = assets_by_site
        self.eps = eps_dict or {}
        taxonomies_set = set()
        aids = []
        for assets in self.assets_by_site:
            for asset in assets:
                taxonomies_set.add(asset.taxonomy)
                aids.append(asset.ordinal)
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
        :param eids: ignored
        :returns: an array of E epsilons
        """
        if len(self.eps) == 0:
            return
        eid2idx = self.hazard_getter.eid2idx
        idx = [eid2idx[eid] for eid in eids]
        try:  # from ruptures
            return self.eps[aid, idx]
        except TypeError:  # from GMFs
            return self.eps[aid][idx]

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
        Builds a matrix of N x E epsilons
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
    Mock-up for a matrix of epsilons of size N x E,
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
def make_eps(assetcol, num_samples, seed, correlation):
    """
    :param assetcol: an AssetCollection instance
    :param int num_samples: the number of ruptures
    :param int seed: a random seed
    :param float correlation: the correlation coefficient
    :returns: epsilons matrix of shape (num_assets, num_samples)
    """
    assets_by_taxo = groupby(assetcol, by_taxonomy)
    eps = numpy.zeros((len(assetcol), num_samples), numpy.float32)
    for taxonomy, assets in assets_by_taxo.items():
        # the association with the epsilons is done in order
        assets.sort(key=operator.attrgetter('ordinal'))
        shape = (len(assets), num_samples)
        logging.info('Building %s epsilons for taxonomy %s', shape, taxonomy)
        zeros = numpy.zeros(shape)
        epsilons = scientific.make_epsilons(zeros, seed, correlation)
        for asset, epsrow in zip(assets, epsilons):
            eps[asset.ordinal] = epsrow
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
