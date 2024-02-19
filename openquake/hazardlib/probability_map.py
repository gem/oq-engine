# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (c) 2016-2023 GEM Foundation
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
import math
import copy
import warnings
import numpy
import pandas
from openquake.baselib.general import cached_property
from openquake.baselib.performance import numba, compile
from openquake.hazardlib.tom import get_pnes

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
BYTES_PER_FLOAT = 8
TWO24 = 2 ** 24
rates_dt = {'gid': U16, 'sid': U32, 'lid': U16, 'rate': F32}


if numba:
    @compile("void(float64[:, :], float64[:], uint32[:])")
    def combine_probs(array, other, rlzs):
        for li in range(len(array)):
            for ri in rlzs:
                if other[li] != 0.:
                    array[li, ri] = (
                        1. - (1. - array[li, ri]) * (1. - other[li]))
else:
    def combine_probs(array, other, rlzs):
        for r in rlzs:
            array[:, r] = (1. - (1. - array[:, r]) * (1. - other))


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


class ProbabilityCurve(object):
    """
    This class is a small wrapper over an array of PoEs associated to
    a set of intensity measure types and levels. It provides a few operators,
    including the complement operator `~`

    ~p = 1 - p

    and the inclusive or operator `|`

    p = p1 | p2 = ~(~p1 * ~p2)

    Such operators are implemented efficiently at the numpy level, by
    dispatching on the underlying array.

    Here is an example of use:

    >>> poe = ProbabilityCurve(numpy.array([0.1, 0.2, 0.3, 0, 0]))
    >>> ~(poe | poe) * .5
    <ProbabilityCurve
    [0.405 0.32  0.245 0.5   0.5  ]>
    """
    def __init__(self, array):
        self.array = array

    def __or__(self, other):
        if other == 0:
            return self
        else:
            return self.__class__(1. - (1. - self.array) * (1. - other.array))
    __ror__ = __or__

    def __iadd__(self, other):
        # this is used when composing mutually exclusive probabilities
        self.array += other.array
        return self

    def __add__(self, other):
        # this is used when composing mutually exclusive probabilities
        self.array += other.array
        return self.__class__(self.array)

    def __mul__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self.array * other.array)
        elif other == 1:
            return self
        else:
            return self.__class__(self.array * other)
    __rmul__ = __mul__

    def __pow__(self, n):
        return self.__class__(self.array ** n)

    def __invert__(self):
        return self.__class__(1. - self.array)

    def __bool__(self):
        return bool(self.array.any())

    def __repr__(self):
        return '<ProbabilityCurve\n%s>' % self.array

    def extract(self, inner_idx):
        """
        Extracts the component specified by the index `inner_idx`.
        """
        array = self.array[:, inner_idx].reshape(-1, 1)
        return self.__class__(array)

    # used when exporting to HDF5
    def convert(self, imtls, idx=0):
        """
        Convert a probability curve into a record of dtype `imtls.dt`.

        :param imtls: DictArray instance
        :param idx: extract the data corresponding to the given inner index
        """
        curve = numpy.zeros(1, imtls.dt)
        for imt in imtls:
            curve[imt] = self.array[imtls(imt), idx]
        return curve[0]



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


############################## probability maps ###############################

# numbified below
def update_pmap_i(arr, poes, inv, rates, probs_occur, idxs, itime):
    levels = range(arr.shape[1])
    for i, rate, probs, idx in zip(inv, rates, probs_occur, idxs):
        if itime == 0:  # FatedTOM
            arr[idx] *= 1. - poes[i]
        elif len(probs) == 0 and numba is not None:
            # looping is faster than building arrays
            for lvl in levels:
                arr[idx, lvl] *= math.exp(-rate * poes[i, lvl] * itime)
        else:
            arr[idx] *= get_pnes(rate, probs, poes[i], itime)  # shape L


# numbified below
def update_pmap_m(arr, poes, inv, rates, probs_occur, weights, idxs, itime):
    for i, rate, probs, w, idx in zip(inv, rates, probs_occur, weights, idxs):
        pne = get_pnes(rate, probs, poes[i], itime)  # shape L
        arr[idx] += (1. - pne) * w


if numba:
    t = numba.types
    sig = t.void(t.float64[:, :],                        # pmap
                 t.float64[:, :],                        # poes
                 t.uint32[:],                            # invs
                 t.float64[:],                           # rates
                 t.float64[:, :],                        # probs_occur
                 t.uint32[:],                            # sids
                 t.float64)                              # itime
    update_pmap_i = compile(sig)(update_pmap_i)

    sig = t.void(t.float64[:, :],                        # pmap
                 t.float64[:, :],                        # poes
                 t.uint32[:],                            # invs
                 t.float64[:],                           # rates
                 t.float64[:, :],                        # probs_occur
                 t.float64[:],                           # weights
                 t.uint32[:],                            # sids
                 t.float64)                              # itime
    update_pmap_m = compile(sig)(update_pmap_m)


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


class ProbabilityMap(object):
    """
    Thin wrapper over a 3D-array of probabilities.
    """
    def __init__(self, sids, shape_y, shape_z):
        self.sids = sids
        self.shape = (len(sids), shape_y, shape_z)

    @cached_property
    def sidx(self):
        """
        :returns: an array of length N site_id -> index
        """
        idxs = numpy.zeros(self.sids.max() + 1, numpy.uint32)
        for idx, sid in enumerate(self.sids):
            idxs[sid] = idx
        return idxs

    def new(self, array):
        new = copy.copy(self)
        new.array = array
        return new

    def split(self):
        """
        :yields: G ProbabilityMaps of shape (N, L, 1)
        """
        N, L, G = self.array.shape
        for g in range(G):
            yield self.__class__(self.sids, L, 1).new(self.array[:, :, [g]])

    def fill(self, value):
        """
        :param value: a scalar probability

        Fill the ProbabilityMap underlying array with the given scalar
        and build the .sidx array
        """
        assert 0 <= value <= 1, value
        self.array = numpy.empty(self.shape)
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
        Convert a ProbabilityMap with shape (N, L, Gt) into a ProbabilityMap
        with shape (N, L, R): works only for rates
        """
        N, L, Gt = self.array.shape
        assert Gt == len(trt_rlzs), (Gt, len(trt_rlzs))
        R = full_lt.get_num_paths()
        out = ProbabilityMap(range(N), L, R).fill(0.)
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

    def to_rates(self, slc=slice(None)):
        """
        Assuming self contains an array of probabilities of no exceedance,
        returns an array of rates of shape (N, L, G).
        """
        pnes = self.array[:, slc]
        # Physically, an extremely small intensity measure level can have an
        # extremely large probability of exceedence,however that probability
        # cannot be exactly 1 unless the level is exactly 0. Numerically,
        # the PoE can be 1 and this give issues when calculating the damage:
        # there is a log(0) in scientific.annual_frequency_of_exceedence.
        # Here we solve the issue by replacing the unphysical probabilities
        # 1 with .9999999999999999 (the float64 closest to 1).
        pnes[pnes == 0.] = 1.11E-16
        return -numpy.log(pnes)

    def interp4D(self, imtls, poes):
        """
        :param imtls: a dictionary imt->imls with M items
        :param poes: a list of P PoEs
        :returns: an array of shape (N, M, P, Z)
        """
        poes3 = self.array
        N, L, Z = poes3.shape
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
        if ok.sum() == 0:  # avoid empty array
            ok = slice(0, 1)
        new = self.__class__(self.sids[ok], self.shape[1], self.shape[2])
        new.array = self.array[ok]
        return new

    # used in classical_risk from CSV
    def to_dframe(self):
        """
        :returns: a DataFrame with fields sid, gid, lid, poe
        """
        dic = dict(sid=[], gid=[], lid=[], rate=[])
        for sid, arr in zip(self.sids, self.array):
            for (lid, gid), rate in numpy.ndenumerate(arr):
                dic['sid'].append(sid)
                dic['gid'].append(gid)
                dic['lid'].append(lid)
                dic['rate'].append(rate)
        for key, dt in rates_dt.items():
            dic[key] = dt(dic[key])
        return pandas.DataFrame(dic)

    def multiply_pnes(self, other, g, i):
        """
        Multiply by the probabilities of no exceedence
        """
        # assume other.sids are a subset of self.sids
        self.array[self.sidx[other.sids], :, g] *= other.array[:, :, i]

    def update(self, poes, invs, ctxt, itime, mutex_weight):
        """
        Update probabilities
        """
        rates = ctxt.occurrence_rate
        probs_occur = fix_probs_occur(ctxt.probs_occur)
        idxs = self.sidx[ctxt.sids]
        for i in range(self.shape[-1]):  # G indices
            if len(mutex_weight) == 0:  # indep
                update_pmap_i(self.array[:, :, i], poes[:, :, i], invs, rates,
                              probs_occur, idxs, itime)
            else:  # mutex
                weights = [mutex_weight[src_id, rup_id]
                           for src_id, rup_id in zip(ctxt.src_id, ctxt.rup_id)]
                update_pmap_m(self.array[:, :, i], poes[:, :, i],
                              invs, rates, probs_occur,
                              numpy.array(weights), idxs, itime)

    def __invert__(self):
        return self.new(1. - self.array)

    def __pow__(self, n):
        return self.new(self.array ** n)

    def __repr__(self):
        return '<ProbabilityMap(%d, %d, %d)>' % self.shape
