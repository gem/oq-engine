# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (c) 2016-2025 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import copy
import logging
import warnings
import numpy
import pandas
import numba
from openquake.baselib.general import cached_property, humansize
from openquake.baselib.performance import compile
from openquake.hazardlib.tom import get_pnes

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
BYTES_PER_FLOAT = 8
TWO20 = 2 ** 20  # 1 MB
TWO24 = 2 ** 24
rates_dt = numpy.dtype([('sid', U32), ('lid', U16), ('gid', U16),
                        ('rate', F32)])


@compile("(float64[:, :], float64[:], uint32[:])")
def combine_probs(array, other, rlzs):
    for li in range(len(array)):
        for ri in rlzs:
            if other[li] != 0.:
                array[li, ri] = (
                    1. - (1. - array[li, ri]) * (1. - other[li]))


def get_mean_curve(dstore, imt, site_id=0):
    """
    Extract the mean hazard curve from the datastore for the first site.
    """
    if 'hcurves-stats' in dstore:  # shape (N, S, M, L1)
        arr = dstore.sel('hcurves-stats', stat='mean', imt=imt)
    else:  # there is only 1 realization
        arr = dstore.sel('hcurves-rlzs', rlz_id=0, imt=imt)
    return arr[site_id, 0, 0]


def get_poe_from_mean_curve(dstore, imt, iml, site_id=0):
    """
    Extract the poe corresponding to the given iml by looking at the mean
    curve for the given imt. `iml` can also be an array.
    """
    imls = dstore['oqparam'].imtls[imt]
    mean_curve = get_mean_curve(dstore, imt, site_id)
    return numpy.interp(imls, mean_curve)[iml]


# ######################### hazard maps ################################### #

# cutoff value for the poe
EPSILON = 1E-30


def compute_hazard_maps(curves, imls, poes):
    """
    Given a set of hazard curve poes, interpolate hazard maps at the specified
    ``poes``.

    :param curves:
        Array of floats of shape N x L. Each row represents a curve, where the
        values in the row are the PoEs (Probabilities of Exceedance)
        corresponding to the ``imls``.
        Each curve corresponds to a geographical location.
    :param imls:
        Intensity Measure Levels associated with these hazard ``curves``. Type
        should be an array-like of floats.
    :param poes:
        Value(s) on which to interpolate a hazard map from the input
        ``curves``.
    :returns:
        An array of shape N x P, where N is the number of curves and P the
        number of poes.
    """
    P = len(poes)
    N, L = curves.shape  # number of levels
    if L != len(imls):
        raise ValueError('The curves have %d levels, %d were passed' %
                         (L, len(imls)))

    log_poes = numpy.log(poes)
    hmap = numpy.zeros((N, P))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # avoid RuntimeWarning: divide by zero for zero levels
        imls = numpy.log(numpy.array(imls[::-1]))
    for n, curve in enumerate(curves):
        # the hazard curve, having replaced the too small poes with EPSILON
        log_curve = numpy.log([max(poe, EPSILON) for poe in curve[::-1]])
        for p, log_poe in enumerate(log_poes):
            if log_poe > log_curve[-1]:
                # special case when the interpolation poe is bigger than the
                # maximum, i.e the iml must be smaller than the minimum;
                # extrapolate the iml to zero as per
                # https://bugs.launchpad.net/oq-engine/+bug/1292093;
                # then the hmap goes automatically to zero
                pass
            else:
                # exp-log interpolation, to reduce numerical errors
                # see https://bugs.launchpad.net/oq-engine/+bug/1252770
                hmap[n, p] = numpy.exp(numpy.interp(log_poe, log_curve, imls))
    return hmap


def compute_hmaps(curvesNML, imtls, poes):
    """
    :param curvesNML: an array of shape (N, M, L1)
    :param imlts: a DictArray with M keys
    :param poes: a sequence of P poes
    :returns: array of shape (N, M, P) with the hazard maps
    """
    N = len(curvesNML)
    M = len(imtls)
    P = len(poes)
    assert M == len(imtls)
    iml3 = numpy.zeros((N, M, P))
    for m, imls in enumerate(imtls.values()):
        curves = curvesNML[:, m]
        iml3[:, m] = compute_hazard_maps(curves, imls, poes)
    return iml3


def check_hmaps(hcurves, imtls, poes):
    """
    :param hcurves: hazard curves of shape (N, M, L1)
    :param imtls: a dictionary imt -> imls
    :param poes: a list of poes
    :param poes: P poes
    """
    N, M, _L1 = hcurves.shape
    assert M == len(imtls), (M, len(imtls))
    all_poes = []
    for poe in poes:
        all_poes.extend([poe, poe * .99])
    for m, (imt, imls) in enumerate(imtls.items()):
        hmaps = compute_hazard_maps(hcurves[:, m], imls, all_poes)  # (N, 2*P)
        for site_id in range(N):
            for p, poe in enumerate(poes):
                iml = hmaps[site_id, p*2]
                iml99 = hmaps[site_id, p*2+1]
                if iml + iml99 == 0:  # zero curve
                    logging.error(f'The {imt} hazard curve for {site_id=} cannot '
                                  f'be inverted around {poe=}')
                    continue
                rel_err = abs(iml - iml99) / abs(iml + iml99)
                if  rel_err > .05:
                    raise ValueError(f'The {imt} hazard curve for {site_id=} cannot '
                                     f'be inverted reliably around {poe=}')
                elif rel_err > .01:
                    logging.warning(
                        f'The {imt} hazard curve for {site_id=} cannot be '
                        f'inverted reliably around {poe=}: {iml=}, {iml99=}')


# not used right now
def get_lvl(hcurve, imls, poe):
    """
    :param hcurve: a hazard curve, i.e. array of L1 PoEs
    :param imls: L1 intensity measure levels
    :returns: index of the intensity measure level associated to the poe

    >>> imls = numpy.array([.1, .2, .3, .4])
    >>> hcurve = numpy.array([1., .99, .90, .8])
    >>> get_lvl(hcurve, imls, 1)
    0
    >>> get_lvl(hcurve, imls, .99)
    1
    >>> get_lvl(hcurve, imls, .91)
    2
    >>> get_lvl(hcurve, imls, .8)
    3
    """
    [[iml]] = compute_hazard_maps(hcurve.reshape(1, -1), imls, [poe])
    iml -= 1E-10  # small buffer
    return numpy.searchsorted(imls, iml)

# ############################# probability maps ##############################

t = numba.types
sig_i = t.void(t.float32[:, :, :],                     # pmap
               t.float32[:, :, :],                     # poes
               t.float64[:],                           # rates
               t.float64[:, :],                        # probs_occur
               t.uint32[:],                            # sids
               t.float64)                              # itime

sig_m = t.void(t.float32[:, :, :],                     # pmap
               t.float32[:, :, :],                     # poes
               t.float64[:],                           # rates
               t.float64[:, :],                        # probs_occur
               t.float64[:],                           # weights
               t.uint32[:],                            # sids
               t.float64)                              # itime


@compile(sig_i)
def update_pmap_i(arr, poes, rates, probs_occur, sidxs, itime):
    G = arr.shape[2]
    for poe, rate, probs, sidx in zip(poes, rates, probs_occur, sidxs):
        no_probs = len(probs) == 0
        for g in range(G):
            if no_probs:
                arr[sidx, :, g] *= numpy.exp(-rate * poe[:, g] * itime)
            else:  # nonparametric rupture
                arr[sidx, :, g] *= get_pnes(rate, probs, poe[:, g], itime)  # shape L


@compile(sig_i)
def update_pmap_r(arr, poes, rates, probs_occur, sidxs, itime):
    G = arr.shape[2]
    for poe, rate, probs, sidx in zip(poes, rates, probs_occur, sidxs):
        if len(probs) == 0:
            for g in range(G):
                arr[sidx, :, g] += rate * poe[:, g] * itime
        else:  # nonparametric rupture
            for g in range(G):
                arr[sidx, :, g] += -numpy.log(get_pnes(rate, probs, poe[:, g], itime))


@compile(sig_m)
def update_pmap_m(arr, poes, rates, probs_occur, weights, sidxs, itime):
    G = arr.shape[2]
    for poe, rate, probs, w, sidx in zip(poes, rates, probs_occur, weights, sidxs):
        for g in range(G):
            arr[sidx, :, g] += (1. - get_pnes(rate, probs, poe[:, g], itime)) * w


def fix_probs_occur(probs_occur):
    """
    Try to convert object arrays into regular arrays
    """
    if probs_occur.dtype.name == 'object':
        n = len(probs_occur)
        p = len(probs_occur[0])
        po = numpy.zeros((n, p))
        for p, probs in enumerate(probs_occur):
            po[p] = probs_occur[p]
        return po
    return probs_occur


class MapArray(object):
    """
    Thin wrapper over a 3D-array of probabilities.
    """
    def __init__(self, sids, shape_y, shape_z, rates=False):
        self.sids = sids
        self.shape = (len(sids), shape_y, shape_z)
        self.rates = rates

    @cached_property
    def sidx(self):
        """
        :returns: an array of length N site_id -> index
        """
        idxs = numpy.zeros(self.sids.max() + 1, numpy.uint32)
        for idx, sid in enumerate(self.sids):
            idxs[sid] = idx
        return idxs

    @property
    def size_mb(self):
        return self.array.nbytes / TWO20
            
    def new(self, arr):
        new = copy.copy(self)
        new.array = arr
        return new

    def split(self):
        """
        :yields: G MapArrays of shape (N, L, 1)
        """
        _N, L, G = self.shape
        for g in range(G):
            new = self.__class__(self.sids, L, 1).new(self.array[:, :, [g]])
            new.gids = [g]
            yield new

    def fill(self, value):
        """
        :param value: a scalar probability

        Fill the MapArray underlying array with the given scalar
        and build the .sidx array
        """
        assert 0 <= value <= 1, value
        self.array = numpy.empty(self.shape, F32)
        self.array.fill(value)
        return self

    def reshape(self, N, M, P):
        """
        :returns: a new Pmap associated to a reshaped array
        """
        return self.new(self.array.reshape(N, M, P))

    # used in calc/disagg_test.py
    def expand(self, full_lt, trt_rlzs):
        """
        Convert a MapArray with shape (N, L, Gt) into a MapArray
        with shape (N, L, R): works only for rates
        """
        N, L, Gt = self.array.shape
        assert Gt == len(trt_rlzs), (Gt, len(trt_rlzs))
        R = full_lt.get_num_paths()
        out = MapArray(range(N), L, R).fill(0., F32)
        for g, trs in enumerate(trt_rlzs):
            for sid in range(N):
                for rlz in trs % TWO24:
                    out.array[sid, :, rlz] += self.array[sid, :, g]
                # NB: for probabilities use
                # combine_probs(out.array[sid], self.array[sid, :, g], rlzs)
        return out

    # used in calc_hazard_curves
    def convert(self, imtls, nsites, idx=0):
        """
        Convert a probability map into a composite array of length `nsites`
        and dtype `imtls.dt`.

        :param imtls:
            DictArray instance
        :param nsites:
            the total number of sites
        :param idx:
            index on the z-axis (default 0)
        """
        curves = numpy.zeros(nsites, imtls.dt)
        for imt in curves.dtype.names:
            curves[imt][self.sids] = self.array[:, imtls(imt), idx]
        return curves

    def to_rates(self, itime=1.):
        """
        Convert into a map containing rates unless the map already contains rates
        """
        if self.rates:
            return self
        pnes = self.array
        # Physically, an extremely small intensity measure level can have an
        # extremely large probability of exceedence,however that probability
        # cannot be exactly 1 unless the level is exactly 0. Numerically,
        # the PoE can be 1 and this give issues when calculating the damage:
        # there is a log(0) in scientific.annual_frequency_of_exceedence.
        # Here we solve the issue by replacing the unphysical probabilities
        # 1 with .9999999999999999 (the float64 closest to 1).
        pnes[pnes == 0.] = 1.11E-16
        return self.new(-numpy.log(pnes) / itime)

    def to_array(self, gid):
        """
        Assuming self contains an array of rates,
        returns a composite array with fields sid, lid, gid, rate
        """
        if len(gid) == 0:
            return numpy.array([], rates_dt)
        outs = []
        for i, g in enumerate(gid):
            rates_g = self.array[:, :, i]
            outs.append(from_rates_g(rates_g, g, self.sids))
        if len(outs) == 1:
            return outs[0]
        return numpy.concatenate(outs, dtype=rates_dt)

    def interp4D(self, imtls, poes):
        """
        :param imtls: a dictionary imt->imls with M items
        :param poes: a list of P PoEs
        :returns: an array of shape (N, M, P, Z)
        """
        poes3 = self.array
        N, _L, Z = poes3.shape
        M = len(imtls)
        P = len(poes)
        L1 = len(imtls[next(iter(imtls))])
        hmap4 = numpy.zeros((N, M, P, Z))
        for m, imt in enumerate(imtls):
            slc = slice(m*L1, m*L1 + L1)
            for z in range(Z):
                hmap4[:, m, :, z] = compute_hazard_maps(
                    poes3[:, slc, z], imtls[imt], poes)
        return hmap4

    # dangerous since it changes the shape by removing sites
    def remove_zeros(self):
        ok = self.array.sum(axis=(1, 2)) > 0
        new = self.__class__(self.sids[ok], self.shape[1], self.shape[2], self.rates)
        new.array = self.array[ok]
        return new

    # used in classical_risk from CSV
    def to_dframe(self):
        """
        :returns: a DataFrame with fields sid, gid, lid, poe
        """
        G = self.array.shape[2]
        arr = self.to_rates().to_array(numpy.arange(G))
        return pandas.DataFrame({name: arr[name] for name in arr.dtype.names})

    def update_indep(self, poes, ctxt, itime):
        """
        Update probabilities for independent ruptures
        """
        rates = ctxt.occurrence_rate
        sidxs = self.sidx[ctxt.sids]
        if self.rates:
            update_pmap_r(self.array, poes, rates, ctxt.probs_occur, sidxs, itime)
        else:
            update_pmap_i(self.array, poes, rates, ctxt.probs_occur, sidxs, itime)

    def update_mutex(self, poes, ctxt, itime, mutex_weight):
        """
        Update probabilities for mutex ruptures
        """
        rates = ctxt.occurrence_rate
        probs_occur = fix_probs_occur(ctxt.probs_occur)
        sidxs = self.sidx[ctxt.sids]
        weights = numpy.array([mutex_weight[src_id, rup_id]
                               for src_id, rup_id in zip(ctxt.src_id, ctxt.rup_id)])
        update_pmap_m(self.array, poes, rates, probs_occur, weights, sidxs, itime)

    def __invert__(self):
        return self.new(1. - self.array)

    def __pow__(self, n):
        return self.new(self.array ** n)

    def __iadd__(self, other):
        # used in calc.mean_rates
        sidx = self.sidx[other.sids]
        G = other.array.shape[2]  # NLG
        for i, g in enumerate(other.gid):
            iadd(self.array[:, :, g], other.array[:, :, i % G], sidx)
        return self

    def __repr__(self):
        tup = self.shape + (humansize(self.array.nbytes),)
        return f'<{self.__class__.__name__}(%d, %d, %d)[%s]>' % tup


@compile("(float32[:, :], float32[:, :], uint32[:])")
def iadd(arr, array, sidx):
    for i, sid in enumerate(sidx):
        arr[sid] += array[i]


def from_rates_g(rates_g, g, sids):
    """
    :param rates_g: an array of shape (N, L)
    :param g: an integer representing a GSIM index
    :param sids: an array of site IDs
    """
    outs = []
    for lid, rates in enumerate(rates_g.T):
        idxs, = rates.nonzero()
        if len(idxs):
            out = numpy.zeros(len(idxs), rates_dt)
            out['sid'] = sids[idxs]
            out['lid'] = lid
            out['gid'] = g
            out['rate'] = rates[idxs]
            outs.append(out)
    if not outs:
        return numpy.array([], rates_dt)
    elif len(outs) == 1:
        return outs[0]
    return numpy.concatenate(outs, dtype=rates_dt)


class RateMap:
    """
    A kind of MapArray specifically for rates
    """
    sidx = MapArray.sidx
    size_mb = MapArray.size_mb
    __repr__ = MapArray.__repr__

    def __init__(self, sids, L, gids):
        self.sids = sids
        self.shape = len(sids), L, len(gids)
        self.array = numpy.zeros(self.shape, F32)
        self.jid = {g: j for j, g in enumerate(gids)}

    def __iadd__(self, other):
        G = self.shape[2]
        sidx = self.sidx[other.sids]
        for i, g in enumerate(other.gid):
            iadd(self.array[:, :, self.jid[g]],
                 other.array[:, :, i % G], sidx)
        return self

    def to_array(self, g):
        """
        Assuming self contains an array of rates,
        returns a composite array with fields sid, lid, gid, rate
        """
        rates_g = self.array[:, :, self.jid[g]]
        return from_rates_g(rates_g, g, self.sids)
