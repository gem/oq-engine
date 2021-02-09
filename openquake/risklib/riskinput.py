# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2021 GEM Foundation
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

import logging
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import group_array, AccumDict
from openquake.risklib import scientific

U32 = numpy.uint32
F32 = numpy.float32


def get_assets_by_taxo(assets, tempname=None):
    """
    :param assets: an array of assets
    :param tempname: hdf5 file where the epsilons are (or None)
    :returns: assets_by_taxo with attributes eps and idxs
    """
    assets_by_taxo = AccumDict(group_array(assets, 'taxonomy'))
    assets_by_taxo.assets = assets
    assets_by_taxo.idxs = numpy.argsort(numpy.concatenate([
        a['ordinal'] for a in assets_by_taxo.values()]))
    assets_by_taxo.eps = {}
    if tempname is None:  # no epsilons
        return assets_by_taxo
    # otherwise read the epsilons and group them by taxonomy
    with hdf5.File(tempname, 'r') as h5:
        dset = h5['epsilon_matrix']
        for taxo, assets in assets_by_taxo.items():
            lst = [dset[aid] for aid in assets['ordinal']]
            assets_by_taxo.eps[taxo] = numpy.array(lst)
    return assets_by_taxo


def get_output(crmodel, assets_by_taxo, haz, rlzi=None):
    """
    :param assets_by_taxo: a dictionary taxonomy index -> assets on a site
    :param haz: an array or a dictionary of hazard on that site
    :param rlzi: if given, a realization index
    :returns: an ArrayWrapper loss_type -> array of shape (A, ...)
    """
    primary = crmodel.primary_imtls
    alias = {imt: 'gmv_%d' % i for i, imt in enumerate(primary)}
    if hasattr(haz, 'array'):  # classical
        eids = []
        data = {f'gmv_{m}': haz.array[crmodel.imtls(imt), 0]
                for m, imt in enumerate(primary)}
    elif set(haz.columns) - {'sid', 'eid', 'rlz'}:  # regular case
        # NB: in GMF-based calculations the order in which
        # the gmfs are stored is random since it depends on
        # which hazard task ends first; here we reorder
        # the gmfs by event ID; this is convenient in
        # general and mandatory for the case of
        # VulnerabilityFunctionWithPMF, otherwise the
        # sample method would receive the means in random
        # order and produce random results even if the
        # seed is set correctly; very tricky indeed! (MS)
        haz = haz.sort_values('eid')
        eids = haz.eid.to_numpy()
        data = haz
    else:  # ZeroGetter for this site (event based)
        eids = numpy.arange(1)
        data = {f'gmv_{m}': [0] for m, imt in enumerate(primary)}
    dic = dict(eids=eids, assets=assets_by_taxo.assets,
               loss_types=crmodel.loss_types, haz=haz)
    if rlzi is not None:
        dic['rlzi'] = rlzi
    for lt in crmodel.loss_types:
        ls = []
        for taxonomy, assets_ in assets_by_taxo.items():
            if len(assets_by_taxo.eps):
                epsilons = assets_by_taxo.eps[taxonomy][:, eids]
            else:  # no CoVs
                epsilons = ()
            arrays = []
            rmodels, weights = crmodel.get_rmodels_weights(lt, taxonomy)
            for rm in rmodels:
                imt = rm.imt_by_lt[lt]
                dat = data[alias.get(imt, imt)]
                if hasattr(dat, 'to_numpy'):
                    dat = dat.to_numpy()
                arrays.append(rm(lt, assets_, dat, eids, epsilons))
            res = arrays[0] if len(arrays) == 1 else numpy.average(
                arrays, weights=weights, axis=0)
            ls.append(res)
        arr = numpy.concatenate(ls)
        dic[lt] = arr[assets_by_taxo.idxs] if len(arr) else arr
    return hdf5.ArrayWrapper((), dic)


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
        aids = []
        for asset in self.assets:
            aids.append(asset['ordinal'])
        self.aids = numpy.array(aids, numpy.uint32)

    def gen_outputs(self, crmodel, monitor, tempname=None, haz=None):
        """
        Group the assets per taxonomy and compute the outputs by using the
        underlying riskmodels. Yield one output per realization.

        :param crmodel: a CompositeRiskModel instance
        :param monitor: a monitor object used to measure the performance
        """
        self.monitor = monitor
        hazard_getter = self.hazard_getter
        if haz is None:
            with monitor('getting hazard', measuremem=False):
                haz = hazard_getter.get_hazard()
        with monitor('computing risk', measuremem=False):
            # this approach is slow for event_based_risk since a lot of
            # small arrays are passed (one per realization) instead of
            # a long array with all realizations; ebrisk does the right
            # thing since it calls get_output directly
            assets_by_taxo = get_assets_by_taxo(self.assets, tempname)
            if hasattr(haz, 'groupby'):  # DataFrame
                for (sid, rlz), df in haz.groupby(['sid', 'rlz']):
                    yield get_output(crmodel, assets_by_taxo, df, rlz)
            else:  # list of probability curves
                for rlz, pc in enumerate(haz):
                    yield get_output(crmodel, assets_by_taxo, pc, rlz)

    def __repr__(self):
        [sid] = self.hazard_getter.sids
        return '<%s sid=%s, %d asset(s)>' % (
            self.__class__.__name__, sid, len(self.aids))


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


def cache_epsilons(dstore, oq, assetcol, crmodel, E):
    """
    Do nothing if there are no coefficients of variation of ignore_covs is
    set. Otherwise, generate an epsilon matrix of shape (A, E) and save it
    in the cache file, by returning the path to it.
    """
    if oq.ignore_covs or not crmodel.covs or 'LN' not in crmodel.distributions:
        return
    A = len(assetcol)
    logging.info('Storing the epsilon matrix in %s', dstore.tempname)
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
    with hdf5.File(dstore.tempname, 'w') as cache:
        cache['sitecol'] = dstore['sitecol']
        cache['epsilon_matrix'] = eps
    return dstore.tempname


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
