# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
import warnings
import numpy

from openquake.baselib import hdf5, general
from openquake.baselib.python3compat import decode
from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib import calc, probability_map

TWO16 = 2 ** 16
MAX_INT = 2 ** 31 - 1  # this is used in the random number generator
# in this way even on 32 bit machines Python will not have to convert
# the generated seed into a long integer

U8 = numpy.uint8
U16 = numpy.uint16
I32 = numpy.int32
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64
F64 = numpy.float64

BaseRupture.init()

# ############## utilities for the classical calculator ############### #


def convert_to_array(pmap, nsites, imtls, inner_idx=0):
    """
    Convert the probability map into a composite array with header
    of the form PGA-0.1, PGA-0.2 ...

    :param pmap: probability map
    :param nsites: total number of sites
    :param imtls: a DictArray with IMT and levels
    :returns: a composite array of lenght nsites
    """
    lst = []
    # build the export dtype, of the form PGA-0.1, PGA-0.2 ...
    for imt, imls in imtls.items():
        for iml in imls:
            lst.append(('%s-%s' % (imt, iml), F32))
    curves = numpy.zeros(nsites, numpy.dtype(lst))
    for sid, pcurve in pmap.items():
        curve = curves[sid]
        idx = 0
        for imt, imls in imtls.items():
            for iml in imls:
                curve['%s-%s' % (imt, iml)] = pcurve.array[idx, inner_idx]
                idx += 1
    return curves


# ######################### hazard maps ################################### #

# cutoff value for the poe
EPSILON = 1E-30


def compute_hazard_maps(curves, imls, poes):
    """
    Given a set of hazard curve poes, interpolate a hazard map at the specified
    ``poe``.

    :param curves:
        2D array of floats. Each row represents a curve, where the values
        in the row are the PoEs (Probabilities of Exceedance) corresponding to
        ``imls``. Each curve corresponds to a geographical location.
    :param imls:
        Intensity Measure Levels associated with these hazard ``curves``. Type
        should be an array-like of floats.
    :param poes:
        Value(s) on which to interpolate a hazard map from the input
        ``curves``. Can be an array-like or scalar value (for a single PoE).
    :returns:
        An array of shape N x P, where N is the number of curves and P the
        number of poes.
    """
    poes = numpy.array(poes)

    if len(poes.shape) == 0:
        # `poes` was passed in as a scalar;
        # convert it to 1D array of 1 element
        poes = poes.reshape(1)

    if len(curves.shape) == 1:
        # `curves` was passed as 1 dimensional array, there is a single site
        curves = curves.reshape((1,) + curves.shape)  # 1 x L

    L = curves.shape[1]  # number of levels
    if L != len(imls):
        raise ValueError('The curves have %d levels, %d were passed' %
                         (L, len(imls)))
    result = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # avoid RuntimeWarning: divide by zero encountered in log
        # happening in the classical_tiling tests
        imls = numpy.log(numpy.array(imls[::-1]))
    for curve in curves:
        # the hazard curve, having replaced the too small poes with EPSILON
        curve_cutoff = [max(poe, EPSILON) for poe in curve[::-1]]
        hmap_val = []
        for poe in poes:
            # special case when the interpolation poe is bigger than the
            # maximum, i.e the iml must be smaller than the minumum
            if poe > curve_cutoff[-1]:  # the greatest poes in the curve
                # extrapolate the iml to zero as per
                # https://bugs.launchpad.net/oq-engine/+bug/1292093
                # a consequence is that if all poes are zero any poe > 0
                # is big and the hmap goes automatically to zero
                hmap_val.append(0)
            else:
                # exp-log interpolation, to reduce numerical errors
                # see https://bugs.launchpad.net/oq-engine/+bug/1252770
                val = numpy.exp(
                    numpy.interp(
                        numpy.log(poe), numpy.log(curve_cutoff), imls))
                hmap_val.append(val)

        result.append(hmap_val)
    return numpy.array(result)


# #########################  GMF->curves #################################### #

# NB (MS): the approach used here will not work for non-poissonian models
def _gmvs_to_haz_curve(gmvs, imls, ses_per_logic_tree_path):
    """
    Given a set of ground motion values (``gmvs``) and intensity measure levels
    (``imls``), compute hazard curve probabilities of exceedance.

    :param gmvs:
        A list of ground motion values, as floats.
    :param imls:
        A list of intensity measure levels, as floats.
    :param ses_per_logic_tree_path:
        Number of stochastic event sets: the larger, the best convergency

    :returns:
        Numpy array of PoEs (probabilities of exceedance).
    """
    # convert to numpy array and redimension so that it can be broadcast with
    # the gmvs for computing PoE values; there is a gmv for each rupture
    # here is an example: imls = [0.03, 0.04, 0.05], gmvs=[0.04750576]
    # => num_exceeding = [1, 1, 0] coming from 0.04750576 > [0.03, 0.04, 0.05]
    imls = numpy.array(imls).reshape((len(imls), 1))
    num_exceeding = numpy.sum(numpy.array(gmvs) >= imls, axis=1)
    poes = 1 - numpy.exp(- num_exceeding / ses_per_logic_tree_path)
    return poes


# ################## utilities for classical calculators ################ #

def make_hmap(pmap, imtls, poes):
    """
    Compute the hazard maps associated to the passed probability map.

    :param pmap: hazard curves in the form of a ProbabilityMap
    :param imtls: DictArray with M intensity measure types
    :param poes: P PoEs where to compute the maps
    :returns: a ProbabilityMap with size (N, M, P)
    """
    M, P = len(imtls), len(poes)
    hmap = probability_map.ProbabilityMap.build(M, P, pmap, dtype=F32)
    if len(pmap) == 0:
        return hmap  # empty hazard map
    for i, imt in enumerate(imtls):
        curves = numpy.array([pmap[sid].array[imtls(imt), 0]
                              for sid in pmap.sids])
        data = compute_hazard_maps(curves, imtls[imt], poes)  # array (N, P)
        for sid, value in zip(pmap.sids, data):
            array = hmap[sid].array
            for j, val in enumerate(value):
                array[i, j] = val
    return hmap


def make_hmap_array(pmap, imtls, poes, nsites):
    """
    :returns: a compound array of hazard maps of shape nsites
    """
    if isinstance(pmap, probability_map.ProbabilityMap):
        # this is here for compatibility with the
        # past, it could be removed in the future
        hmap = make_hmap(pmap, imtls, poes)
        pdic = general.DictArray({imt: poes for imt in imtls})
        return convert_to_array(hmap, nsites, pdic)
    try:
        hcurves = pmap.value
    except AttributeError:
        hcurves = pmap
    dtlist = [('%s-%s' % (imt, poe), F32) for imt in imtls for poe in poes]
    array = numpy.zeros(len(pmap), dtlist)
    for imt, imls in imtls.items():
        curves = hcurves[:, imtls(imt)]
        for poe in poes:
            array['%s-%s' % (imt, poe)] = compute_hazard_maps(
                curves, imls, poe).flat
    return array  # array of shape N


def make_uhs(hmap, info):
    """
    Make Uniform Hazard Spectra curves for each location.

    :param hmap:
        array of shape (N, M, P)
    :param info:
        a dictionary with keys poes, imtls, uhs_dt
    :returns:
        a composite array containing uniform hazard spectra
    """
    uhs = numpy.zeros(len(hmap), info['uhs_dt'])
    for p, poe in enumerate(info['poes']):
        for m, imt in enumerate(info['imtls']):
            if imt.startswith(('PGA', 'SA')):
                uhs[str(poe)][imt] = hmap[:, m, p]
    return uhs


class RuptureData(object):
    """
    Container for information about the ruptures of a given
    tectonic region type.
    """
    def __init__(self, trt, gsims):
        self.trt = trt
        self.cmaker = ContextMaker(trt, gsims)
        self.params = sorted(self.cmaker.REQUIRES_RUPTURE_PARAMETERS -
                             set('mag strike dip rake hypo_depth'.split()))
        self.dt = numpy.dtype([
            ('rup_id', U32), ('srcidx', U32), ('multiplicity', U16),
            ('occurrence_rate', F64),
            ('mag', F32), ('lon', F32), ('lat', F32), ('depth', F32),
            ('strike', F32), ('dip', F32), ('rake', F32),
            ('boundary', hdf5.vstr)] + [(param, F32) for param in self.params])

    def to_array(self, ebruptures):
        """
        Convert a list of ebruptures into an array of dtype RuptureRata.dt
        """
        data = []
        for ebr in ebruptures:
            rup = ebr.rupture
            self.cmaker.add_rup_params(rup)
            ruptparams = tuple(getattr(rup, param) for param in self.params)
            point = rup.surface.get_middle_point()
            multi_lons, multi_lats = rup.surface.get_surface_boundaries()
            bounds = ','.join('((%s))' % ','.join(
                '%.5f %.5f' % (lon, lat) for lon, lat in zip(lons, lats))
                              for lons, lats in zip(multi_lons, multi_lats))
            try:
                rate = ebr.rupture.occurrence_rate
            except AttributeError:  # for nonparametric sources
                rate = numpy.nan
            data.append(
                (ebr.serial, ebr.srcidx, ebr.n_occ, rate,
                 rup.mag, point.x, point.y, point.z, rup.surface.get_strike(),
                 rup.surface.get_dip(), rup.rake,
                 'MULTIPOLYGON(%s)' % decode(bounds)) + ruptparams)
        return numpy.array(data, self.dt)


class RuptureSerializer(object):
    """
    Serialize event based ruptures on an HDF5 files. Populate the datasets
    `ruptures` and `sids`.
    """
    def __init__(self, datastore):
        self.datastore = datastore
        self.nbytes = 0
        self.nruptures = 0
        datastore.create_dset('ruptures', calc.stochastic.rupture_dt,
                              attrs={'nbytes': 0})
        datastore.create_dset('rupgeoms', calc.stochastic.point3d)

    def save(self, rup_array):
        """
         Store the ruptures in array format.
        """
        self.nruptures += len(rup_array)
        offset = len(self.datastore['rupgeoms'])
        rup_array.array['gidx1'] += offset
        rup_array.array['gidx2'] += offset
        previous = self.datastore.get_attr('ruptures', 'nbytes', 0)
        self.datastore.extend(
            'ruptures', rup_array, nbytes=previous + rup_array.nbytes)
        self.datastore.extend('rupgeoms', rup_array.geom)
        # TODO: PMFs for nonparametric ruptures are not stored
        self.datastore.flush()

    def close(self):
        """
        Save information about the rupture codes as attributes of the
        'ruptures' dataset.
        """
        if 'ruptures' not in self.datastore:  # for UCERF
            return
        codes = numpy.unique(self.datastore['ruptures']['code'])
        attr = {'code_%d' % code: ' '.join(
            cls.__name__ for cls in BaseRupture.types[code])
                for code in codes}
        self.datastore.set_attrs('ruptures', **attr)
