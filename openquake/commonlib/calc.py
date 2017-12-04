# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from __future__ import division
import warnings
import numpy
import h5py

from openquake.baselib import hdf5
from openquake.baselib.python3compat import decode
from openquake.hazardlib.geo.mesh import (
    surface_to_mesh, point3d, RectangularMesh)
from openquake.hazardlib.source.rupture import BaseRupture, EBRupture
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.imt import from_string
from openquake.hazardlib import geo, calc, probability_map, stats

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

event_dt = numpy.dtype([('eid', U64), ('ses', U32), ('sample', U32)])

sids_dt = h5py.special_dtype(vlen=U32)

BaseRupture.init()  # initialize rupture codes

# ############## utilities for the classical calculator ############### #


def convert_to_array(pmap, nsites, imtls):
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
            lst.append(('%s-%s' % (imt, iml), numpy.float64))
    curves = numpy.zeros(nsites, numpy.dtype(lst))
    for sid, pcurve in pmap.items():
        curve = curves[sid]
        idx = 0
        for imt, imls in imtls.items():
            for iml in imls:
                curve['%s-%s' % (imt, iml)] = pcurve.array[idx]
                idx += 1
    return curves


class PmapGetter(object):
    """
    Read hazard curves from the datastore for all realizations or for a
    specific realization.

    :param dstore: a DataStore instance
    :param sids: the subset of sites to consider (if None, all sites)
    :param rlzs_assoc: a RlzsAssoc instance (if None, infers it)
    """
    def __init__(self, dstore, sids=None, rlzs_assoc=None):
        self.rlzs_assoc = rlzs_assoc or dstore['csm_info'].get_rlzs_assoc()
        self.dstore = dstore
        self.weights = [rlz.weight for rlz in self.rlzs_assoc.realizations]
        self.num_levels = len(self.dstore['oqparam'].imtls.array)
        self.sids = sids
        self.nbytes = 0
        if sids is None:
            self.sids = dstore['sitecol'].complete.sids
        # populate _pmap_by_grp
        self._pmap_by_grp = {}
        if 'poes' in self.dstore:
            # build probability maps restricted to the given sids
            for grp, dset in self.dstore['poes'].items():
                sid2idx = {sid: i for i, sid in enumerate(dset.attrs['sids'])}
                L, I = dset.shape[1:]
                pmap = probability_map.ProbabilityMap(L, I)
                for sid in self.sids:
                    try:
                        idx = sid2idx[sid]
                    except KeyError:
                        continue
                    else:
                        pmap[sid] = probability_map.ProbabilityCurve(dset[idx])
                self._pmap_by_grp[grp] = pmap
                self.nbytes += pmap.nbytes

    def get(self, rlzi, grp=None):
        """
        :param rlzi: a realization index
        :param grp: None (all groups) or a string of the form "grp-XX"
        :returns: the hazard curves for the given realization
        """
        assert self.sids is not None
        pmap = probability_map.ProbabilityMap(self.num_levels, 1)
        grps = [grp] if grp is not None else sorted(self._pmap_by_grp)
        array = self.rlzs_assoc.by_grp()
        for grp in grps:
            for gsim_idx, rlzis in array[grp]:
                for r in rlzis:
                    if r == rlzi:
                        pmap |= self._pmap_by_grp[grp].extract(gsim_idx)
                        break
        return pmap

    def get_pmaps(self, sids):  # used in classical
        """
        :param sids: an array of S site IDs
        :returns: a list of R probability maps
        """
        return self.rlzs_assoc.combine_pmaps(self._pmap_by_grp)

    def get_hcurves(self, imtls):
        """
        :param imtls: intensity measure types and levels
        :returns: an array of (R, N) hazard curves
        """
        assert self.sids is not None, 'PmapGetter not bound to sids'
        pmaps = [pmap.convert2(imtls, self.sids)
                 for pmap in self.get_pmaps(self.sids)]
        return numpy.array(pmaps)

    def items(self, kind=''):
        """
        Extract probability maps from the datastore, possibly generating
        on the fly the ones corresponding to the individual realizations.
        Yields pairs (tag, pmap).

        :param kind:
            the kind of PoEs to extract; if not given, returns the realization
            if there is only one or the statistics otherwise.
        """
        num_rlzs = len(self.weights)
        if not kind:  # use default
            if 'hcurves' in self.dstore:
                for k in sorted(self.dstore['hcurves']):
                    yield k, self.dstore['hcurves/' + k]
            elif num_rlzs == 1:
                yield 'rlz-000', self.get(0)
            return
        if 'poes' in self.dstore and kind in ('rlzs', 'all'):
            for rlzi in range(num_rlzs):
                hcurves = self.get(rlzi)
                yield 'rlz-%03d' % rlzi, hcurves
        elif 'poes' in self.dstore and kind.startswith('rlz-'):
            yield kind, self.get(int(kind[4:]))
        if 'hcurves' in self.dstore and kind in ('stats', 'all'):
            for k in sorted(self.dstore['hcurves']):
                yield k, self.dstore['hcurves/' + k]

    def get_mean(self, grp=None):
        """
        Compute the mean curve as a ProbabilityMap

        :param grp:
            if not None must be a string of the form "grp-XX"; in that case
            returns the mean considering only the contribution for group XX
        """
        if self.sids is None:
            self.sids = self.dstore['sitecol'].complete.sids
        if len(self.weights) == 1:  # one realization
            return self.get(0, grp)
        else:  # multiple realizations, assume hcurves/mean is there
            dic = ({g: self.dstore['poes/' + g] for g in self.dstore['poes']}
                   if grp is None else {grp: self.dstore['poes/' + grp]})
            return self.rlzs_assoc.compute_pmap_stats(dic, [stats.mean_curve])

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
def _gmvs_to_haz_curve(gmvs, imls, invest_time, duration):
    """
    Given a set of ground motion values (``gmvs``) and intensity measure levels
    (``imls``), compute hazard curve probabilities of exceedance.

    :param gmvs:
        A list of ground motion values, as floats.
    :param imls:
        A list of intensity measure levels, as floats.
    :param float invest_time:
        Investigation time, in years. It is with this time span that we compute
        probabilities of exceedance.

        Another way to put it is the following. When computing a hazard curve,
        we want to answer the question: What is the probability of ground
        motion meeting or exceeding the specified levels (``imls``) in a given
        time span (``invest_time``).
    :param float duration:
        Time window during which GMFs occur. Another was to say it is, the
        period of time over which we simulate ground motion occurrences.

        NOTE: Duration is computed as the calculation investigation time
        multiplied by the number of stochastic event sets.

    :returns:
        Numpy array of PoEs (probabilities of exceedance).
    """
    # convert to numpy array and redimension so that it can be broadcast with
    # the gmvs for computing PoE values; there is a gmv for each rupture
    # here is an example: imls = [0.03, 0.04, 0.05], gmvs=[0.04750576]
    # => num_exceeding = [1, 1, 0] coming from 0.04750576 > [0.03, 0.04, 0.05]
    imls = numpy.array(imls).reshape((len(imls), 1))
    num_exceeding = numpy.sum(numpy.array(gmvs) >= imls, axis=1)
    poes = 1 - numpy.exp(- (invest_time / duration) * num_exceeding)
    return poes


# ################## utilities for classical calculators ################ #

def get_imts_periods(imtls):
    """
    Returns a list of IMT strings and a list of periods. There is an element
    for each IMT of type Spectral Acceleration, including PGA which is
    considered an alias for SA(0.0). The lists are sorted by period.

    :param imtls: a set of intensity measure type strings
    :returns: a list of IMT strings and a list of periods
    """
    def getperiod(imt):
        return imt[1] or 0
    imts = sorted((from_string(imt) for imt in imtls
                   if imt.startswith('SA') or imt == 'PGA'), key=getperiod)
    return [str(imt) for imt in imts], [imt[1] or 0.0 for imt in imts]


def make_hmap(pmap, imtls, poes):
    """
    Compute the hazard maps associated to the passed probability map.

    :param pmap: hazard curves in the form of a ProbabilityMap
    :param imtls: DictArray with M intensity measure types
    :param poes: P PoEs where to compute the maps
    :returns: a ProbabilityMap with size (N, M * P, 1)
    """
    M, P = len(imtls), len(poes)
    hmap = probability_map.ProbabilityMap.build(M * P, 1, pmap)
    if len(pmap) == 0:
        return hmap  # empty hazard map
    for i, imt in enumerate(imtls):
        curves = numpy.array([pmap[sid].array[imtls.slicedic[imt], 0]
                              for sid in pmap.sids])
        data = compute_hazard_maps(curves, imtls[imt], poes)  # array N x P
        for sid, value in zip(pmap.sids, data):
            array = hmap[sid].array
            for j, val in enumerate(value):
                array[i * P + j] = val
    return hmap


def make_uhs(pmap, imtls, poes, nsites):
    """
    Make Uniform Hazard Spectra curves for each location.

    It is assumed that the `lons` and `lats` for each of the `maps` are
    uniform.

    :param pmap:
        a probability map of hazard curves
    :param imtls:
        a dictionary of intensity measure types and levels
    :param poes:
        a sequence of PoEs for the underlying hazard maps
    :returns:
        an composite array containing nsites uniform hazard maps
    """
    P = len(poes)
    imts, _ = get_imts_periods(imtls)
    hmap = make_hmap(pmap, imtls, poes)
    for sid in range(nsites):  # fill empty positions if any
        hmap.setdefault(sid, 0)
    array = hmap.array
    imts_dt = numpy.dtype([(str(imt), F64) for imt in imts])
    uhs_dt = numpy.dtype([(str(poe), imts_dt) for poe in poes])
    uhs = numpy.zeros(nsites, uhs_dt)
    for j, poe in enumerate(map(str, poes)):
        for i, imt in enumerate(imtls):
            if imt in imts:
                uhs[poe][imt] = array[:, i * P + j, 0]
    return uhs


def fix_minimum_intensity(min_iml, imts):
    """
    :param min_iml: a dictionary, possibly with a 'default' key
    :param imts: an ordered list of IMTs
    :returns: a numpy array of intensities, one per IMT

    Make sure the dictionary minimum_intensity (provided by the user in the
    job.ini file) is filled for all intensity measure types and has no key
    named 'default'. Here is how it works:

    >>> min_iml = {'PGA': 0.1, 'default': 0.05}
    >>> fix_minimum_intensity(min_iml, ['PGA', 'PGV'])
    array([ 0.1 ,  0.05], dtype=float32)
    >>> sorted(min_iml.items())
    [('PGA', 0.1), ('PGV', 0.05)]
    """
    if min_iml:
        for imt in imts:
            try:
                min_iml[imt] = calc.filters.getdefault(min_iml, imt)
            except KeyError:
                raise ValueError(
                    'The parameter `minimum_intensity` in the job.ini '
                    'file is missing the IMT %r' % imt)
    if 'default' in min_iml:
        del min_iml['default']
    return F32([min_iml.get(imt, 0) for imt in imts])


def check_overflow(calc):
    """
    :param calc: an event based calculator

    Raise a ValueError if the number of sites is larger than 65,536 or the
    number of IMTs is larger than 256 or the number of ruptures is larger
    than 4,294,967,296. The limits are due to the numpy dtype used to
    store the GMFs (gmv_dt). They could be relaxed in the future.
    """
    max_ = dict(sites=2**16, events=2**32, imts=2**8)
    num_ = dict(sites=len(calc.sitecol),
                events=len(calc.datastore['events']),
                imts=len(calc.oqparam.imtls))
    for var in max_:
        if num_[var] > max_[var]:
            raise ValueError(
                'The event based calculator is restricted to '
                '%d %s, got %d' % (max_[var], var, num_[var]))


class RuptureData(object):
    """
    Container for information about the ruptures of a given
    tectonic region type.
    """
    def __init__(self, trt, gsims):
        self.trt = trt
        self.cmaker = ContextMaker(gsims)
        self.params = sorted(self.cmaker.REQUIRES_RUPTURE_PARAMETERS -
                             set('mag strike dip rake hypo_depth'.split()))
        self.dt = numpy.dtype([
            ('rup_id', U32), ('multiplicity', U16), ('eidx', U32),
            ('numsites', U32), ('occurrence_rate', F64),
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
            rc = self.cmaker.make_rupture_context(rup)
            ruptparams = tuple(getattr(rc, param) for param in self.params)
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
                (ebr.serial, ebr.multiplicity, ebr.eidx1, len(ebr.sids), rate,
                 rup.mag, point.x, point.y, point.z, rup.surface.get_strike(),
                 rup.surface.get_dip(), rup.rake,
                 'MULTIPOLYGON(%s)' % decode(bounds)) + ruptparams)
        return numpy.array(data, self.dt)


class RuptureSerializer(object):
    """
    Serialize event based ruptures on an HDF5 files. Populate the datasets
    `ruptures` and `sids`.
    """
    rupture_dt = numpy.dtype([
        ('serial', U32), ('code', U8), ('sidx', U32),
        ('eidx1', U32), ('eidx2', U32), ('pmfx', I32), ('seed', U32),
        ('mag', F32), ('rake', F32), ('occurrence_rate', F32),
        ('hypo', point3d), ('sx', U16), ('sy', U8), ('sz', U16),
        ('points', h5py.special_dtype(vlen=point3d)),
        ])

    pmfs_dt = numpy.dtype([
        ('serial', U32), ('pmf', h5py.special_dtype(vlen=F32)),
    ])

    @classmethod
    def get_array_nbytes(cls, ebruptures):
        """
        Convert a list of EBRuptures into a numpy composite array
        """
        lst = []
        nbytes = 0
        for ebrupture in ebruptures:
            rup = ebrupture.rupture
            mesh = surface_to_mesh(rup.surface)
            sx, sy, sz = mesh.shape
            points = mesh.flatten()
            # sanity checks
            assert sx < TWO16, 'Too many multisurfaces: %d' % sx
            assert sy < 256, 'The rupture mesh spacing is too small'
            assert sz < TWO16, 'The rupture mesh spacing is too small'
            hypo = rup.hypocenter.x, rup.hypocenter.y, rup.hypocenter.z
            rate = getattr(rup, 'occurrence_rate', numpy.nan)
            tup = (ebrupture.serial, rup.code, ebrupture.sidx,
                   ebrupture.eidx1, ebrupture.eidx2,
                   getattr(ebrupture, 'pmfx', -1),
                   rup.seed, rup.mag, rup.rake, rate, hypo,
                   sx, sy, sz, points)
            lst.append(tup)
            nbytes += cls.rupture_dt.itemsize + mesh.nbytes
        return numpy.array(lst, cls.rupture_dt), nbytes

    def __init__(self, datastore):
        self.datastore = datastore
        self.sids = {}  # dictionary sids -> sidx
        self.data = []
        self.nbytes = 0

    def save(self, ebruptures, eidx=0):
        """
        Populate a dictionary of site IDs tuples and save the ruptures.

        :param ebruptures: a list of EBRupture objects to save
        :param eidx: the last event index saved
        """
        pmfbytes = 0
        # set the reference to the sids (sidx) correctly
        for ebr in ebruptures:
            mul = ebr.multiplicity
            ebr.eidx1 = eidx
            ebr.eidx2 = eidx + mul
            eidx += mul
            sids_tup = tuple(ebr.sids)
            try:
                ebr.sidx = self.sids[sids_tup]
            except KeyError:
                ebr.sidx = self.sids[sids_tup] = len(self.sids)
                self.data.append(ebr.sids)

            rup = ebr.rupture
            if hasattr(rup, 'pmf'):
                pmfs = numpy.array([(ebr.serial, rup.pmf)], self.pmfs_dt)
                dset = self.datastore.extend(
                    'pmfs/grp-%02d' % ebr.grp_id, pmfs)
                ebr.pmfx = len(dset) - 1
                pmfbytes += self.pmfs_dt.itemsize + rup.pmf.nbytes

        # store the ruptures in a compact format
        array, nbytes = self.get_array_nbytes(ebruptures)
        key = 'ruptures/grp-%02d' % ebr.grp_id
        try:
            dset = self.datastore.getitem(key)
        except KeyError:  # not created yet
            previous = 0
        else:
            previous = dset.attrs['nbytes']
        self.datastore.extend(key, array, nbytes=previous + nbytes)

        # save nbytes occupied by the PMFs
        if pmfbytes:
            if 'nbytes' in dset.attrs:
                dset.attrs['nbytes'] += pmfbytes
            else:
                dset.attrs['nbytes'] = pmfbytes
        self.datastore.flush()

    def close(self):
        """
        Flush the ruptures and the site IDs on the datastore
        """
        self.sids.clear()
        if self.data:
            self.datastore.save_vlen('sids', self.data)
            del self.data[:]


def get_ruptures(dstore, events, grp_id):
    """
    Extracts the ruptures of the given grp_id
    """
    return _get_ruptures(dstore, events, [grp_id], None)


def _get_ruptures(dstore, events, grp_ids, rup_id):
    oq = dstore['oqparam']
    grp_trt = dstore['csm_info'].grp_trt()
    for grp_id in grp_ids:
        trt = grp_trt[grp_id]
        grp = 'grp-%02d' % grp_id
        try:
            recs = dstore['ruptures/' + grp]
        except KeyError:  # no ruptures in grp
            continue
        for rec in recs:
            if rup_id is not None and rup_id != rec['serial']:
                continue
            mesh = rec['points'].reshape(rec['sx'], rec['sy'], rec['sz'])
            rupture_cls, surface_cls, source_cls = BaseRupture.types[
                rec['code']]
            rupture = object.__new__(rupture_cls)
            rupture.surface = object.__new__(surface_cls)
            # MISSING: case complex_fault_mesh_spacing != rupture_mesh_spacing
            if 'Complex' in surface_cls.__name__:
                mesh_spacing = oq.complex_fault_mesh_spacing
            else:
                mesh_spacing = oq.rupture_mesh_spacing
            rupture.source_typology = source_cls
            rupture.mag = rec['mag']
            rupture.rake = rec['rake']
            rupture.seed = rec['seed']
            rupture.hypocenter = geo.Point(*rec['hypo'])
            rupture.occurrence_rate = rec['occurrence_rate']
            rupture.tectonic_region_type = trt
            pmfx = rec['pmfx']
            if pmfx != -1:
                rupture.pmf = dstore['pmfs/' + grp][pmfx]
            if surface_cls is geo.PlanarSurface:
                rupture.surface = geo.PlanarSurface.from_array(
                    mesh_spacing, rec['points'])
            elif surface_cls.__name__.endswith('MultiSurface'):
                rupture.surface.__init__([
                    geo.PlanarSurface.from_array(mesh_spacing, m1.flatten())
                    for m1 in mesh])
            else:  # fault surface, strike and dip will be computed
                rupture.surface.strike = rupture.surface.dip = None
                m = mesh[0]
                rupture.surface.mesh = RectangularMesh(
                    m['lon'], m['lat'], m['depth'])
            sids = dstore['sids'][rec['sidx']]
            evs = events[rec['eidx1']:rec['eidx2']]
            ebr = EBRupture(rupture, sids, evs, grp_id, rec['serial'])
            ebr.eidx1 = rec['eidx1']
            ebr.eidx2 = rec['eidx2']
            ebr.sidx = rec['sidx']
            # not implemented: rupture_slip_direction
            yield ebr
