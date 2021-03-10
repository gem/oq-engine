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
                    yield crmodel.get_output(taxo, assets, haz)
                else:  # list of probability curves
                    for rlz, pc in enumerate(haz):
                        yield crmodel.get_output(taxo, assets, pc, rlz=rlz)

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
    >>> epsgetter.normal(3, eid=1)
    array([-2.46861114, -2.46861114, -2.46861114])
    >>> epsgetter.beta(eid=1, alpha=1.1, beta=.1)
    array([0.40714461])
    >>> epsgetter.beta(eid=1, alpha=1.1, beta=0.)  # singular value
    array([1.])
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
        :param size: number of assets affected by the given event
        :param eid: event ID
        :returns: array of dtype float32
        """
        rng = self.rng[eid]
        if self.asset_correlation:
            return numpy.ones(size) * rng.normal()
        else:
            return rng.normal(size=size)

    def beta(self, eid, alpha, beta):
        """
        :param eid: event ID
        :param alpha: parameter(s) of the beta distribution for the given event
        :param beta: parameter(s) of the beta distribution for the given event
        :returns: array of dtype float32 with the same shape as alpha and beta
        """
        rng = self.rng[eid]
        if isinstance(alpha, float):
            size = 1
            assert beta
            assert isinstance(beta, float), beta
            alpha = numpy.array([alpha])
            beta = numpy.array([beta])
        else:
            size = len(alpha)
            assert len(beta) == size, (len(beta), size)
        if self.asset_correlation:
            return numpy.ones(size) * rng.beta(alpha, beta)
        else:
            return rng.beta(alpha, beta)


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
