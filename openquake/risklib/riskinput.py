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

import logging
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import group_array
from openquake.risklib import scientific

U32 = numpy.uint32
F32 = numpy.float32


class RiskInput(object):
    """
    Contains all the assets and hazard values associated to a given
    imt and site.

    :param hazard_getter:
        a callable returning the hazard data for a given realization
    :param assets_by_site:
        array of assets, one per site
    """
    def __init__(self, sid, hazard_getter, assets):
        self.sid = sid
        self.hazard_getter = hazard_getter
        self.assets = assets
        self.weight = len(assets)
        aids = []
        for asset in self.assets:
            aids.append(asset['ordinal'])
        self.aids = numpy.array(aids, numpy.uint32)

    def __repr__(self):
        return '<%s sid=%s, %d asset(s)>' % (
            self.__class__.__name__, self.sid, len(self.aids))


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
    if oq.ignore_covs or not crmodel.covs:
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
