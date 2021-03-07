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

import numpy
from openquake.baselib import hdf5

U32 = numpy.uint32
F32 = numpy.float32


def get_output_gmf(crmodel, taxo, assets, haz, rndgen=None):
    """
    :param crmodel: a CompositeRiskModel instance
    :param taxo: a taxonomy index
    :param assets: a DataFrame of assets of the given taxonomy
    :param haz: a DataFrame of GMVs on that site
    :param rndgen: a MultiEventRNG instance
    :returns: an ArrayWrapper loss_type -> array of shape (A, ...)
    """
    primary = crmodel.primary_imtls
    alias = {imt: 'gmv_%d' % i for i, imt in enumerate(primary)}
    # the order in which the gmfs are stored is random since it depends
    # on which hazard task ends first; here we reorder
    # the gmfs by event ID; this is convenient in
    # general and mandatory for the case of
    # VulnerabilityFunctionWithPMF, otherwise the
    # sample method would receive the means in random
    # order and produce random results even if the
    # seed is set correctly; very tricky indeed! (MS)
    haz = haz.sort_values('eid')
    eids = haz.eid.to_numpy()
    dic = dict(eids=eids, assets=assets.to_records(),
               loss_types=crmodel.loss_types, haz=haz, rlzs=haz.rlz.to_numpy())
    for lt in crmodel.loss_types:
        arrays = []
        rmodels, weights = crmodel.get_rmodels_weights(lt, taxo)
        for rm in rmodels:
            imt = rm.imt_by_lt[lt]
            col = alias.get(imt, imt)
            if col not in haz.columns:
                haz[col] = numpy.zeros(len(haz))  # ZeroGetter
            arrays.append(rm(lt, assets, haz, col, rndgen))
        dic[lt] = arrays[0] if len(arrays) == 1 else numpy.average(
            arrays, weights=weights, axis=0)
    return hdf5.ArrayWrapper((), dic)


def get_output_pc(crmodel, taxo, assets, haz, rlzi):
    """
    :param taxo: a taxonomy index
    :param assets: a DataFrame of assets of the given taxonomy
    :param haz: an ArrayWrapper of ProbabilityCurves on that site
    :param rlzi: if given, a realization index
    :returns: an ArrayWrapper loss_type -> array of shape (A, ...)
    """
    dic = dict(assets=assets.to_records(), loss_types=crmodel.loss_types,
               haz=haz, rlzi=rlzi)
    for lt in crmodel.loss_types:
        arrays = []
        rmodels, weights = crmodel.get_rmodels_weights(lt, taxo)
        for rm in rmodels:
            imt = rm.imt_by_lt[lt]
            data = haz.array[crmodel.imtls(imt), 0]
            arrays.append(rm(lt, assets, data))
        dic[lt] = arrays[0] if len(arrays) == 1 else numpy.average(
            arrays, weights=weights, axis=0)
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
        self.aids = assets.ordinal.to_numpy()

    def gen_outputs(self, crmodel, monitor, haz=None):
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
            for taxo, assets in self.assets.groupby('taxonomy'):
                if hasattr(haz, 'groupby'):  # DataFrame
                    yield get_output_gmf(crmodel, taxo, assets, haz)
                else:  # list of probability curves
                    for rlz, pc in enumerate(haz):
                        yield get_output_pc(crmodel, taxo, assets, pc, rlz)

    def __repr__(self):
        [sid] = self.hazard_getter.sids
        return '<%s sid=%s, %d asset(s)>' % (
            self.__class__.__name__, sid, len(self.aids))


class MultiEventRNG(object):
    """
    An object ``MultiEventRNG(master_seed, asset_correlation, eids)``
    has a method ``.get(A, eids)`` which returns a matrix of (A, E)
    normally distributed random numbers.
    If the ``asset_correlation`` is 1 the numbers are the same.

    >>> epsgetter = MultiEventRNG(
    ...     master_seed=42, asset_correlation=1, eids=[0, 1, 2])
    >>> epsgetter.normal(3, 0)
    array([-1.10439952, -1.10439952, -1.10439952])
    >>> epsgetter.normal(3, 1)
    array([-2.46861114, -2.46861114, -2.46861114])
    >>> epsgetter.beta(3, 1, 1.0, 0.1)
    array([0.48157279, 0.48157279, 0.48157279])
    """
    def __init__(self, master_seed, asset_correlation, eids):
        self.master_seed = master_seed
        self.asset_correlation = asset_correlation
        self.rng = {}
        for eid in eids:
            ph = numpy.random.Philox(self.master_seed + eid)
            self.rng[eid] = numpy.random.Generator(ph)

    def normal(self, size, eid):
        """
        :param size: an array shape or size
        :param eid: valid event ID
        :returns: array of shape size and dtype float32
        """
        rng = self.rng[eid]
        if self.asset_correlation:
            return numpy.ones(size) * rng.normal()
        else:
            return rng.normal(size=size)

    def beta(self, size, eid, alpha, beta):
        """
        :param size: an array shape or size
        :param eid: valid event ID
        :param alpha: parameter of the beta distribution
        :param betaa: parameter of the beta distribution
        :returns: array of shape (size, len(eids)) and dtype float32
        """
        rng = self.rng[eid]
        if self.asset_correlation:
            return numpy.ones(size) * rng.beta(alpha, beta)
        else:
            return rng.beta(alpha, beta, size=size)


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
