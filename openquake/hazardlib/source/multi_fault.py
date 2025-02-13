# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.source.multi_fault`
defines :class:`MultiFaultSource`.
"""
import copy
import numpy as np
from typing import Union

from openquake.baselib import hdf5, performance, general
from openquake.baselib.general import gen_slices, idxs_by_tag
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.rupture import (
    NonParametricProbabilisticRupture, ParametricProbabilisticRupture)
from openquake.hazardlib.source.non_parametric import (
    NonParametricSeismicSource as NP)
from openquake.hazardlib.geo.surface.kite_fault import (
    geom_to_kite, kite_to_geom)
from openquake.hazardlib.geo.surface.multi import (
    MultiSurface, build_msparams, build_secparams)
from openquake.hazardlib.geo.utils import (
    angular_distance, KM_TO_DEGREES, get_spherical_bounding_box)
from openquake.hazardlib.source.base import BaseSeismicSource
from openquake.hazardlib.calc.filters import FilteredAway

U16 = np.uint16
U32 = np.uint32
F32 = np.float32
F64 = np.float64
BLOCKSIZE = 5000
TWO16 = 2 ** 16
TWO32 = 2 ** 32
# NB: if too large, very few sources will be generated and a lot of
# memory will be used


class MultiFaultSource(BaseSeismicSource):
    """
    The multi-fault source is a source typology specifically supporting the
    calculation of hazard using fault models with segments participating to
    multiple ruptures.

    :param source_id:
        A unique identifier for the source
    :param name:
        The name of the fault
    :param tectonic_region_type:
        A string that defines the TRT of the fault source
    :param rupture_idxs:
        A list of arrays. Each element contains the IDs of the sections
        participating to a rupture. The cardinality of this list is N.
        The IDs are integers.
    :param occurrence_probs:
        A list of N probabilities. Each element specifies the probability
        of 0, 1 ... occurrences of a rupture in the investigation time
    :param magnitudes:
        An iterable with cardinality N containing the magnitudes of the
        ruptures
    :param rakes:
        An iterable with cardinality N containing the rake of each
        rupture
    """
    code = b'F'
    MODIFICATIONS = {}
    hdf5path = ''

    def __init__(self, source_id: str, name: str, tectonic_region_type: str,
                 rupture_idxs: list, occurrence_probs: Union[list, np.ndarray],
                 magnitudes: list, rakes: list, investigation_time=0,
                 infer_occur_rates=False):
        nrups = len(magnitudes)
        assert len(occurrence_probs) == len(rakes) == nrups
        self._rupture_idxs = rupture_idxs
        # NB: using 32 bits for the occurrence_probs would be a disaster:
        # the results are STRONGLY dependent on the precision,
        # in particular the AELO tests for CHN would break
        self.probs_occur = F64(occurrence_probs)  # 64 bit!
        self.mags = F32(magnitudes)
        self.rakes = F32(rakes)
        self.infer_occur_rates = infer_occur_rates
        self.investigation_time = investigation_time
        self.source_id =source_id
        self.name = name
        self.tectonic_region_type = tectonic_region_type

    @property
    def occur_rates(self):
        """
        :returns: poissonian occurrence rates, if infer_occur_rates is set
        """
        assert self.infer_occur_rates
        rates =  -np.log([p[0] for p in self.probs_occur])
        rates[rates <= 0] = 1E-30
        return rates

    @property
    def rupture_idxs(self):
        """
        Read a list of U16 arrays from hdf5path
        """
        assert self.hdf5path
        with hdf5.File(self.hdf5path, 'r') as h5:
            key = f'{self.source_id}/rupture_idxs'
            try:
                return h5[key][:]
            except KeyError:
                raise KeyError(f'{key} not found in {self.hdf5path}')

    def set_sections(self, sections):
        """
        Used in the UCERF converter, not in the engine
        """
        self.sections = sections
        dic = {i: sec for i, sec in enumerate(sections)}
        save_and_split([self], dic, f'{self.source_id}.hdf5',
                       del_rupture_idxs=False)

    def set_msparams(self, secparams, close_sec=None, ry0=False,
                     mon1=performance.Monitor(),
                     mon2=performance.Monitor()):
        self.msparams = build_msparams(
            self.rupture_idxs, secparams, close_sec, ry0, mon1, mon2)

    def is_gridded(self):
        return True  # convertible to HDF5

    def todict(self):
        """
        :returns: dictionary of array, called when converting to HDF5
        """
        ridxs = []
        for rupture_idxs in self._rupture_idxs:
            ridxs.append(' '.join(map(str, rupture_idxs)))
        # each pmf has the form [(prob0, 0), (prob1, 1), ...]
        return dict(mag=self.mags, rake=self.rakes,
                    probs_occur=self.probs_occur,
                    rupture_idxs=np.array(ridxs, dtype=hdf5.vstr))

    def get_unique_idxs(self):
        """
        :returns: indices of the underlying surfaces
        """
        return np.unique(np.concatenate(self.rupture_idxs))

    def get_sections(self, idxs=None):
        """
        :param idxs: indices of the surfaces to return (default all)
        :returns: the underlying sections as KiteSurfaces
        """
        with hdf5.File(self.hdf5path, 'r') as f:
            geoms = f['multi_fault_sections'][:]  # small
        if idxs is None:
            idxs = range(len(geoms))
        sections = [geom_to_kite(geom) for geom in geoms[idxs]]
        for sec, idx in zip(sections, idxs):
            sec.idx = idx
        return sections

    def iter_ruptures(self, **kwargs):
        """
        An iterator for the ruptures.
        """
        # Check
        if not self.hdf5path:
            raise RuntimeError('You forgot to save the multifault sources')

        # iter on the ruptures
        step = kwargs.get('step', 1)
        n = len(self.mags)
        sec = self.get_sections()  # read KiteSurfaces, very fast
        rupture_idxs = self.rupture_idxs
        msparams = self.msparams
        if self.infer_occur_rates:
            occur_rates = self.occur_rates
            tom = PoissonTOM(self.investigation_time)
        for i in range(0, n, step**2):
            if msparams[i]['area'] == 0:  # rupture far away
                continue
            idxs = rupture_idxs[i]
            sfc = MultiSurface([sec[idx] for idx in idxs], msparams[i])
            rake = self.rakes[i]
            hypo = sfc.get_middle_point()
            data = [(p, o) for o, p in enumerate(self.probs_occur[i])]
            if self.infer_occur_rates:
                rup = ParametricProbabilisticRupture(
                    self.mags[i], rake, self.tectonic_region_type,
                    hypo, sfc, occur_rates[i], tom)
            else:
                rup = NonParametricProbabilisticRupture(
                    self.mags[i], rake, self.tectonic_region_type,
                    hypo, sfc, PMF(data))
            yield rup

    def gen_slices(self):
        if len(self.mags) <= BLOCKSIZE:  # already split
            yield self.source_id, slice(0, len(self.mags))
            return
        for i, slc in enumerate(gen_slices(0, len(self.mags), BLOCKSIZE)):
            yield '%s.%d' % (self.source_id, i), slc

    def __iter__(self):
        if len(self.mags) <= BLOCKSIZE:  # already split
            yield self
            return
        # split in blocks of BLOCKSIZE ruptures each
        for srcid, slc in self.gen_slices():
            src = self.__class__(
                srcid,
                self.name,
                self.tectonic_region_type,
                self._rupture_idxs[slc] if hasattr(
                    self, '_rupture_idxs') else [],  # tested in test_ucerf
                self.probs_occur[slc],
                self.mags[slc],
                self.rakes[slc],
                self.investigation_time,
                self.infer_occur_rates)
            src.hdf5path = self.hdf5path
            src.num_ruptures = src.count_ruptures()
            yield src

    def count_ruptures(self):
        """
        :returns: the number of the ruptures in the source
        """
        return len(self.mags)

    def get_min_max_mag(self):
        return np.min(self.mags), np.max(self.mags)

    @property
    def data(self):  # compatibility with NonParametricSeismicSource
        for i, rup in enumerate(self.iter_ruptures()):
            yield rup, self.probs_occur[i]

    polygon = NP.polygon
    wkt = NP.wkt
    mesh_size = NP.mesh_size

    def get_bounding_box(self, maxdist):
        """
        Bounding box containing the surfaces, enlarged by the maximum distance
        """
        p = self.msparams[self.msparams['area'] > 0]  # non-discarded
        if len(p) == 0:
            raise FilteredAway
        lons = np.concatenate([p['west'], p['east']])
        lats = np.concatenate([p['north'], p['south']])
        west, east, north, south = get_spherical_bounding_box(lons, lats)
        a1 = maxdist * KM_TO_DEGREES
        a2 = angular_distance(maxdist, north, south)
        return west - a2, south - a1, east + a2, north + a1


def _set_tags(mfsources, allsections, sitecol1, s2i):
    # set attribute .tags for each source in the mfsources
    dists = np.array([sec.get_min_distance(sitecol1)[0]
                         for sec in allsections])
    for src_id, src in enumerate(mfsources):
        src.tags = []
        for idxs in src._rupture_idxs:
            rids = U32([s2i[idx] for idx in idxs])
            src.tags.append(rids[np.argmin(dists[rids])])


# NB: as side effect delete _rupture_idxs and add .hdf5path and possibly .tags
def save_and_split(mfsources, sectiondict, hdf5path, site1=None,
                   del_rupture_idxs=True):
    """
    Serialize MultiFaultSources
    """
    assert mfsources
    assert len(sectiondict) < TWO32, len(sectiondict)
    s2i = {idx: i for i, idx in enumerate(sectiondict)}
    all_rids = []
    for src in mfsources:
        try:
            rids = [U32([s2i[idx] for idx in idxs])
                    for idxs in src._rupture_idxs]
        except KeyError as exc:
            raise IndexError('The section index %s in source %r is invalid'
                             % (exc.args[0], src.source_id))
        all_rids.append(rids)
        src.hdf5path = hdf5path

    # add tags
    if site1 is not None:
         _set_tags(mfsources, sectiondict.values(), site1, s2i)

    # save memory
    for src in mfsources:
        if del_rupture_idxs:
            delattr(src, '_rupture_idxs')

    # save split sources
    split_dic = general.AccumDict(accum=[])

    with hdf5.File(hdf5path, 'w') as h5:
        for src, rids in zip(mfsources, all_rids):
            if hasattr(src, 'tags'):
                items = [(f'{src.source_id}@{tag}', idxs)
                         for tag, idxs in idxs_by_tag(src.tags).items()]
            else:
                items = [(tag, np.arange(slc.start, slc.stop))
                         for tag, slc in src.gen_slices()]
            for source_id, slc in items:
                split = copy.copy(src)
                split.source_id = source_id
                split.probs_occur = src.probs_occur[slc]
                split.mags = src.mags[slc]
                split.rakes = src.rakes[slc]
                h5.save_vlen(f'{source_id}/rupture_idxs',
                             [rids[rupid] for rupid in slc])
                h5[f'{source_id}/probs_occur'] = split.probs_occur
                h5[f'{source_id}/mags'] = split.mags
                h5[f'{source_id}/rakes'] = split.rakes

                # save attributes
                attrs = h5[f'{source_id}'].attrs
                attrs['name'] = src.name
                attrs['tectonic_region_type'] = src.tectonic_region_type
                attrs['investigation_time'] = src.investigation_time
                attrs['infer_occur_rates'] = src.infer_occur_rates
                split_dic[src.source_id].append(split)
        h5.save_vlen('multi_fault_sections',
                     [kite_to_geom(sec) for sec in sectiondict.values()])
        h5['secparams'] = build_secparams(src.get_sections())

    return split_dic


def load(hdf5path):
    """
    :returns: list of sources serialized with `multi_fault.save`
    """
    srcs = []
    with hdf5.File(hdf5path, 'r') as h5:
        for key in list(h5):
            if key in ('multi_fault_sections', 'secparams'):
                continue
            data = h5[key]
            name = data.attrs['name']
            trt = data.attrs['tectonic_region_type']
            itime = data.attrs['investigation_time']
            infer = data.attrs['infer_occur_rates']
            mags = data['mags'][:]
            rakes = data['rakes'][:]
            probs = data['probs_occur'][:]
            src = MultiFaultSource(key, name, trt,
                                   data['rupture_idxs'][:],
                                   probs, mags, rakes,
                                   itime, infer)
            src.hdf5path = hdf5path
            srcs.append(src)
    return srcs
