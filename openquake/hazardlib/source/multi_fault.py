# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
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

import numpy as np
from typing import Union

from openquake.baselib import hdf5
from openquake.baselib.general import gen_slices
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.rupture import (
    NonParametricProbabilisticRupture, ParametricProbabilisticRupture)
from openquake.hazardlib.source.non_parametric import (
    NonParametricSeismicSource as NP)
from openquake.hazardlib.geo.surface.kite_fault import (
    geom_to_kite, kite_to_geom)
from openquake.hazardlib.geo.multiline import MultiLine
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo.utils import angular_distance, KM_TO_DEGREES
from openquake.hazardlib.source.base import BaseSeismicSource

KNOWN_DATASETS = {'multi_fault_sections', 'rupture_coos', 'rupture_shift',
                  'rupture_sizes', 'rupture_umax'}
F32 = np.float32
BLOCKSIZE = 2000
# NB: a large BLOCKSIZE uses a lot less memory and is faster in preclassical
# however it uses a lot of RAM in classical when reading the sources


def reshape(coos, sizes):
    """
    Convert an array with lenght sum(sizes) * 3 into a list of arrays
    of shape (size, 3). For instance

    >>> coos = np.array([100, 10, 0, 110, 10, 0])
    >>> sizes = [2]
    >>> reshape(coos, sizes)
    [array([[100,  10,   0],
           [110,  10,   0]])]
    """
    start = 0
    lst = []
    for size in sizes:
        lst.append(coos[start:start + 3 * size].reshape(-1, 3))
        start += 3 * size
    return lst


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
                 occurrence_probs: Union[list, np.ndarray],
                 magnitudes: list, rakes: list, investigation_time=0,
                 infer_occur_rates=False):
        nrups = len(magnitudes)
        assert len(occurrence_probs) == len(rakes) == nrups
        self.probs_occur = occurrence_probs
        self.mags = magnitudes
        self.rakes = rakes
        self.infer_occur_rates = infer_occur_rates
        self.investigation_time = investigation_time
        if infer_occur_rates:
            self.occur_rates = -np.log([p[0] for p in occurrence_probs])
            self.occur_rates[self.occur_rates <= 0] = 1E-30
            self.temporal_occurrence_model = PoissonTOM(investigation_time)
        super().__init__(source_id, name, tectonic_region_type)

    @property
    def rupture_idxs(self):
        """
        Read a list of U16 arrays from hdf5path if set
        """
        if hasattr(self, '_rupture_idxs'):
            # set by the SourceConverter or by the tests
            return self._rupture_idxs
        with hdf5.File(self.hdf5path, 'r') as f:
            return f[f'rupture_idxs/{self.source_id}'][:]
        
    @property
    def multilines(self):
        """
        Build a list of MultiLines from hdf5path
        """
        with hdf5.File(self.hdf5path, 'r') as f:
            cooss = f[f'rupture_coos/{self.source_id}'][:]
            sizess = f[f'rupture_sizes/{self.source_id}'][:]
            shifts = f[f'rupture_shift/{self.source_id}'][:]
            umaxs = f[f'rupture_umax/{self.source_id}'][:]
        mls = []
        for coos, sizes, shift, umax in zip(cooss, sizess, shifts, umaxs):
            mls.append(MultiLine.from_(reshape(coos, sizes), shift, umax))
        return mls

    def is_gridded(self):
        return True  # convertible to HDF5

    def todict(self):
        """
        :returns: dictionary of array, called when converting to HDF5
        """
        ridxs = []
        for rupture_idxs in self.rupture_idxs:
            ridxs.append(' '.join(map(str, rupture_idxs)))
        # each pmf has the form [(prob0, 0), (prob1, 1), ...]
        return dict(mag=self.mags, rake=self.rakes,
                    probs_occur=self.probs_occur, rupture_idxs=ridxs)

    def get_sections(self):
        """
        :returns: the underlying sections as KiteSurfaces
        """
        if self.hdf5path == '':  # in the tests
            return self.sections  # empty hdf5path
        with hdf5.File(self.hdf5path, 'r') as f:
            geoms = f['multi_fault_sections'][:]  # small
        sections = [geom_to_kite(geom) for geom in geoms]
        for idx, sec in enumerate(sections):
            sec.idx = idx
        return sections

    # used in the tests, where the sections are manually given and not
    # read from the HDF5 file
    def set_sections(self, sections, rupture_idxs):
        """
        :param sections: a list of N surfaces
        """
        assert sections
        # this is fundamental for the distance cache.
        for idx, sec in enumerate(sections):
            sec.idx = idx

        # `i` is the index of the rupture of the `n` admitted by this source.
        # In this loop we check that all the IDs of the sections composing one
        # rupture have a object in the section list describing their geometry.
        for i in range(len(self.mags)):
            for idx in rupture_idxs[i]:
                sections[idx]
        self.sections = sections
        self._rupture_idxs = rupture_idxs

    def iter_ruptures(self, **kwargs):
        """
        An iterator for the ruptures.
        """
        # Check
        if not self.hdf5path and 'sections' not in self.__dict__:
            raise RuntimeError('You forgot to call set_sections in %s!' % self)

        # iter on the ruptures
        step = kwargs.get('step', 1)
        n = len(self.mags)
        sec = self.get_sections()  # KiteSurfaces
        rupture_idxs = self.rupture_idxs
        multilines = self.multilines
        for i in range(0, n, step**2):
            idxs = rupture_idxs[i]
            sfc = MultiSurface([sec[idx] for idx in idxs], multilines[i])
            rake = self.rakes[i]
            hypo = sfc.get_middle_point()
            data = [(p, o) for o, p in enumerate(self.probs_occur[i])]
            if self.infer_occur_rates:
                yield ParametricProbabilisticRupture(
                    self.mags[i], rake, self.tectonic_region_type,
                    hypo, sfc, self.occur_rates[i],
                    self.temporal_occurrence_model)
            else:
                yield NonParametricProbabilisticRupture(
                    self.mags[i], rake, self.tectonic_region_type, hypo, sfc,
                    PMF(data))

    def gen_blocks(self, lst):
        if len(self.mags) <= BLOCKSIZE:  # already split
            yield self.source_id, lst
            return
        for i, slc in enumerate(gen_slices(0, len(self.mags), BLOCKSIZE)):
            yield '%s.%d' % (self.source_id, i), lst[slc]

    def __iter__(self):
        if len(self.mags) <= BLOCKSIZE:  # already split
            yield self
            return
        # split in blocks of BLOCKSIZE ruptures each
        for i, slc in enumerate(gen_slices(0, len(self.mags), BLOCKSIZE)):
            src = self.__class__(
                '%s.%d' % (self.source_id, i),
                self.name,
                self.tectonic_region_type,
                self.probs_occur[slc],
                self.mags[slc],
                self.rakes[slc])
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
        surfaces = []
        for sec in self.get_sections():
            if isinstance(sec, MultiSurface):
                surfaces.extend(sec.surfaces)
            else:
                surfaces.append(sec)
        multi_surf = MultiSurface(surfaces)
        west, east, north, south = multi_surf.get_bounding_box()
        a1 = maxdist * KM_TO_DEGREES
        a2 = angular_distance(maxdist, north, south)
        return west - a2, south - a1, east + a2, north + a1


def save(sources, sections, hdf5path):
    """
    Debug utility to serialize MultiFaultSources
    """
    from openquake.hazardlib.source_reader import save_multilines
    with hdf5.File(hdf5path, 'w') as h5:
        for src in sources:
            src.hdf5path = hdf5path
            h5.save_vlen(f'{src.source_id}/rupture_idxs', src.rupture_idxs)
            h5[f'{src.source_id}/probs_occur'] = src.probs_occur
            h5[f'{src.source_id}/mags'] = src.mags
            h5[f'{src.source_id}/rakes'] = src.rakes
            attrs = h5[f'{src.source_id}'].attrs
            attrs['name'] = src.name
            attrs['tectonic_region_type'] = src.tectonic_region_type
            attrs['investigation_time'] = src.investigation_time
            attrs['infer_occur_rates'] = src.infer_occur_rates
        h5.save_vlen('multi_fault_sections', [
            kite_to_geom(sec) for sec in sections])
        save_multilines(sources, sections, hdf5path)


def load(hdf5path):
    """
    :returns: list of sources serialized with `multi_fault.save`
    """
    srcs = []
    with hdf5.File(hdf5path, 'r') as h5:
        for key in list(h5):
            if key in KNOWN_DATASETS:
                continue
            data = h5[key]
            name = data.attrs['name']
            trt = data.attrs['tectonic_region_type']
            itime = data.attrs['investigation_time']
            infer = data.attrs['infer_occur_rates']
            mags = data['mags'][:]
            rakes = data['rakes'][:]
            probs = data['probs_occur'][:]
            src = MultiFaultSource(key, name, trt, probs, mags, rakes,
                                   itime, infer)
            src._rupture_idxs = data['rupture_idxs'][:]
            src.hdf5path = hdf5path
            srcs.append(src)
    return srcs
