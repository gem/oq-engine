# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
import os
import operator
import collections
import pickle
import toml
import copy
import logging
from dataclasses import dataclass
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import groupby, block_splitter
from openquake.baselib.node import context, striptag, Node, node_to_dict
from openquake.hazardlib import geo, mfd, pmf, source, tom, valid, InvalidFile
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.filters import split_source
from openquake.hazardlib.source import NonParametricSeismicSource
from openquake.hazardlib.source.multi_fault import MultiFaultSource

U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2**16
EPSILON = 1E-12
source_dt = numpy.dtype([('source_id', U32), ('num_ruptures', U32),
                         ('pik', hdf5.vuint8)])
KNOWN_MFDS = ('incrementalMFD', 'truncGutenbergRichterMFD',
              'arbitraryMFD', 'YoungsCoppersmithMFD', 'multiMFD',
              'taperedGutenbergRichterMFD')

EXCLUDE_FROM_GEOM_PROPS = (
    'Polygon', 'Point', 'MultiPoint', 'LineString', '3D MultiLineString',
    '3D MultiPolygon', 'posList')


def extract_dupl(values):
    """
    :param values: a sequence of values
    :returns: the duplicated values
    """
    c = collections.Counter(values)
    return [value for value, counts in c.items() if counts > 1]


def fix_dupl(dist, fname=None, lineno=None):
    """
    Fix the distribution if it contains identical values or raise an error.

    :param dist:
        a list of pairs [(prob, value)...] for a hypocenter or nodal plane dist
    :param fname:
        the file which is being read; if it is None, it means you are writing
        the distribution: in that case raise an error for duplicated values
    :param lineno:
        the line number of the file which is being read (None in writing mode)
    """
    n = len(dist)
    values = collections.defaultdict(float)  # dict value -> probability
    # value can be a scalar (hypocenter depth) or a triple
    # (strike, dip, rake) for a nodal plane distribution
    got = []
    for prob, value in dist:
        if prob == 0:
            raise ValueError('Zero probability in subnode %s' % value)
        values[value] += prob
        got.append(value)
    if len(values) < n:
        if fname is None:  # when called from the sourcewriter
            raise ValueError('There are repeated values in %s' % got)
        else:
            logging.info('There were repeated values %s in %s:%s',
                         extract_dupl(got), fname, lineno)
            assert abs(sum(values.values()) - 1) < EPSILON  # sanity check
            newdist = sorted([(p, v) for v, p in values.items()])
            if isinstance(newdist[0][1], tuple):  # nodal planes
                newdist = [(p, geo.nodalplane.NodalPlane(*v))
                           for p, v in newdist]
            # run hazardlib/tests/data/context/job.ini to check this;
            # you will get [(0.2, 6.0), (0.2, 8.0), (0.2, 10.0), (0.4, 2.0)]
            dist[:] = newdist


def rounded_unique(mags, idxs):
    """
    :param mags: a list of magnitudes
    :param idxs: a list of tuples of section indices
    :returns: an array of magnitudes rounded to 2 digits
    :raises: ValueError if the rounded magnitudes contain duplicates
    """
    mags = numpy.round(mags, 2)
    mag_idxs = [(mag, ' '.join(idx)) for mag, idx in zip(mags, idxs)]
    dupl = extract_dupl(mag_idxs)
    if dupl:
        logging.error('the pair (mag=%s, idxs=%s) is duplicated' % dupl[0])
    return mags


class SourceGroup(collections.abc.Sequence):
    """
    A container for the following parameters:

    :param str trt:
        the tectonic region type all the sources belong to
    :param list sources:
        a list of hazardlib source objects
    :param name:
        The name of the group
    :param src_interdep:
        A string specifying if the sources in this cluster are independent or
        mutually exclusive
    :param rup_indep:
        A string specifying if the ruptures within each source of the cluster
        are independent or mutually exclusive
    :param weights:
        A dictionary whose keys are the source IDs of the cluster and the
        values are the weights associated with each source
    :param min_mag:
        the minimum magnitude among the given sources
    :param max_mag:
        the maximum magnitude among the given sources
    :param id:
        an optional numeric ID (default 0) set by the engine and used
        when serializing SourceModels to HDF5
    :param temporal_occurrence_model:
        A temporal occurrence model controlling the source group occurrence
    :param cluster:
        A boolean indicating if the sources behaves as a cluster similarly
        to what used by the USGS for the New Madrid in the 2008 National
        Hazard Model.
    """
    changes = 0  # set in apply_uncertainty

    @classmethod
    def collect(cls, sources):
        """
        :param sources: dictionaries with a key 'tectonicRegion'
        :returns: an ordered list of SourceGroup instances
        """
        source_stats_dict = {}
        for src in sources:
            trt = src['tectonicRegion']
            if trt not in source_stats_dict:
                source_stats_dict[trt] = SourceGroup(trt)
            sg = source_stats_dict[trt]
            if not sg.sources:
                # we append just one source per SourceGroup, so that
                # the memory occupation is insignificant
                sg.sources.append(src)

        # return SourceGroups, ordered by TRT string
        return sorted(source_stats_dict.values())

    def __init__(self, trt, sources=None, name=None, src_interdep='indep',
                 rup_interdep='indep', grp_probability=1.,
                 min_mag={'default': 0}, max_mag=None,
                 temporal_occurrence_model=None, cluster=False):
        # checks
        self.trt = trt
        self.sources = []
        self.name = name
        self.src_interdep = src_interdep
        self.rup_interdep = rup_interdep
        self._check_init_variables(sources, name, src_interdep, rup_interdep)
        self.grp_probability = grp_probability
        self.min_mag = min_mag
        self.max_mag = max_mag
        if sources:
            for src in sorted(sources, key=operator.attrgetter('source_id')):
                self.update(src)
        self.source_model = None  # to be set later, in FullLogicTree
        self.temporal_occurrence_model = temporal_occurrence_model
        self.cluster = cluster
        # check weights in case of mutually exclusive ruptures
        if rup_interdep == 'mutex':
            for src in self.sources:
                assert isinstance(src, NonParametricSeismicSource)
                for rup, _ in src.data:
                    assert rup.weight is not None

    @property
    def grp_id(self):
        """
        The grp_id of the underlying sources
        """
        return self.sources[0].grp_id

    @property
    def trt_smrs(self):
        """
        The trt_smrs of the underlying sources
        """
        return self.sources[0].trt_smrs

    @property
    def tom_name(self):
        """
        :returns: name of the associated temporal occurrence model
        """
        if self.temporal_occurrence_model:
            return self.temporal_occurrence_model.__class__.__name__
        else:
            return 'PoissonTOM'

    @property
    def atomic(self):
        """
        :returns: True if the group cannot be split
        """
        return (self.cluster or self.src_interdep == 'mutex' or
                self.rup_interdep == 'mutex')

    @property
    def weight(self):
        """
        :returns: total weight of the underlying sources
        """
        return sum(src.weight for src in self)

    @property
    def codes(self):
        """
        The codes of the underlying sources as a byte string
        """
        codes = set()
        for src in self.sources:
            codes.add(src.code)
        return b''.join(sorted(codes))

    def _check_init_variables(self, src_list, name,
                              src_interdep, rup_interdep):
        if src_interdep not in ('indep', 'mutex'):
            raise ValueError('source interdependence incorrect %s ' %
                             src_interdep)
        if rup_interdep not in ('indep', 'mutex'):
            raise ValueError('rupture interdependence incorrect %s ' %
                             rup_interdep)
        # check TRT
        if src_list:  # can be None
            for src in src_list:
                assert src.tectonic_region_type == self.trt, (
                    src.tectonic_region_type, self.trt)
                # Mutually exclusive ruptures can only belong to non-parametric
                # sources
                if rup_interdep == 'mutex':
                    if not isinstance(src, NonParametricSeismicSource):
                        msg = "Mutually exclusive ruptures can only be "
                        msg += "modelled using non-parametric sources"
                        raise ValueError(msg)

    def update(self, src):
        """
        Update the attributes sources, min_mag, max_mag
        according to the given source.

        :param src:
            an instance of :class:
            `openquake.hazardlib.source.base.BaseSeismicSource`
        """
        assert src.tectonic_region_type == self.trt, (
            src.tectonic_region_type, self.trt)

        # checking mutex ruptures
        if (not isinstance(src, NonParametricSeismicSource) and
                self.rup_interdep == 'mutex'):
            msg = "Mutually exclusive ruptures can only be "
            msg += "modelled using non-parametric sources"
            raise ValueError(msg)

        self.sources.append(src)
        _, max_mag = src.get_min_max_mag()
        prev_max_mag = self.max_mag
        if prev_max_mag is None or max_mag > prev_max_mag:
            self.max_mag = max_mag

    def get_trt_smr(self):
        """
        :returns: the .trt_smr attribute of the underlying sources
        """
        return self.sources[0].trt_smr

    # not used by the engine
    def count_ruptures(self):
        """
        Set src.num_ruptures on each source in the group
        """
        for src in self:
            src.nsites = 1
            src.num_ruptures = src.count_ruptures()
            print(src.weight)
        return self

    # used only in event_based, where weight = num_ruptures
    def split(self, maxweight):
        """
        Split the group in subgroups with weight <= maxweight, unless it
        it atomic.
        """
        if self.atomic:
            return [self]

        # split multipoint/multifault in advance
        sources = []
        for src in self:
            if src.code in b'MF':
                sources.extend(split_source(src))
            else:
                sources.append(src)
        out = []
        def weight(src):
            if src.code == b'F':  # consider it much heavier
                return src.num_ruptures * 25
            return src.num_ruptures
        for block in block_splitter(sources, maxweight, weight):
            sg = copy.copy(self)
            sg.sources = block
            out.append(sg)
        logging.info('Produced %d subgroup(s) of %s', len(out), self)
        return out

    def get_tom_toml(self, time_span):
        """
        :returns: the TOM as a json string {'PoissonTOM': {'time_span': 50}}
        """
        tom = self.temporal_occurrence_model
        if tom is None:
            return '[PoissonTOM]\ntime_span=%s' % time_span
        dic = {tom.__class__.__name__: vars(tom)}
        return toml.dumps(dic)

    def is_poissonian(self):
        """
        :returns: True if all the sources in the group are poissonian
        """
        tom = getattr(self.sources[0], 'temporal_occurrence_model', None)
        return tom.__class__.__name__ == 'PoissonTOM'

    def __repr__(self):
        return '<%s %s, %d source(s), weight=%d>' % (
            self.__class__.__name__, self.trt, len(self.sources), self.weight)

    def __lt__(self, other):
        """
        Make sure there is a precise ordering of SourceGroup objects.
        Objects with less sources are put first; in case the number
        of sources is the same, use lexicographic ordering on the trts
        """
        num_sources = len(self.sources)
        other_sources = len(other.sources)
        if num_sources == other_sources:
            return self.trt < other.trt
        return num_sources < other_sources

    def __getitem__(self, i):
        return self.sources[i]

    def __iter__(self):
        return iter(self.sources)

    def __len__(self):
        return len(self.sources)

    def __toh5__(self):
        lst = []
        for i, src in enumerate(self.sources):
            buf = pickle.dumps(src, pickle.HIGHEST_PROTOCOL)
            lst.append((src.id, src.num_ruptures,
                        numpy.frombuffer(buf, numpy.uint8)))
        attrs = dict(
            trt=self.trt,
            name=self.name or '',
            src_interdep=self.src_interdep,
            rup_interdep=self.rup_interdep,
            grp_probability=self.grp_probability or '1')
        return numpy.array(lst, source_dt), attrs

    def __fromh5__(self, array, attrs):
        vars(self).update(attrs)
        self.sources = []
        for row in array:
            self.sources.append(pickle.loads(memoryview(row['pik'])))


def split_coords_2d(seq):
    """
    :param seq: a flat list with lons and lats
    :returns: a validated list of pairs (lon, lat)

    >>> split_coords_2d([1.1, 2.1, 2.2, 2.3])
    [(1.1, 2.1), (2.2, 2.3)]
    """
    lons, lats = [], []
    for i, el in enumerate(seq):
        if i % 2 == 0:
            lons.append(valid.longitude(el))
        elif i % 2 == 1:
            lats.append(valid.latitude(el))
    return list(zip(lons, lats))


def split_coords_3d(seq):
    """
    :param seq: a flat list with lons, lats and depths
    :returns: a validated list of (lon, lat, depths) triplets

    >>> split_coords_3d([1.1, 2.1, 0.1, 2.3, 2.4, 0.1])
    [(1.1, 2.1, 0.1), (2.3, 2.4, 0.1)]
    """
    lons, lats, depths = [], [], []
    for i, el in enumerate(seq):
        if i % 3 == 0:
            lons.append(valid.longitude(el))
        elif i % 3 == 1:
            lats.append(valid.latitude(el))
        elif i % 3 == 2:
            depths.append(valid.depth(el))
    return list(zip(lons, lats, depths))


def convert_nonParametricSeismicSource(fname, node, rup_spacing=5.0):
    """
    Convert the given node into a non parametric source object.

    :param fname:
        full pathname to the XML file associated to the node
    :param node:
        a Node object coming from an XML file
    :param rup_spacing:
        Rupture spacing [km]
    :returns:
        a :class:`openquake.hazardlib.source.NonParametricSeismicSource`
        instance
    """
    trt = node.attrib.get('tectonicRegion')
    rups_weights = None
    if 'rup_weights' in node.attrib:
        rups_weights = F64(node['rup_weights'].split())
    nps = source.NonParametricSeismicSource(
        node['id'], node['name'], trt, [], [])
    nps.splittable = 'rup_weights' not in node.attrib
    if fname:
        path = os.path.splitext(fname)[0] + '.hdf5'
        hdf5_fname = path if os.path.exists(path) else None
        if hdf5_fname is None and node.text is None:
            raise OSError(f'Could not find {path}')
        elif node.text is None:
            # gridded source, read the rupture data from the HDF5 file
            with hdf5.File(hdf5_fname, 'r') as h:
                dic = {k: d[:] for k, d in h[node['id']].items()}
                nps.fromdict(dic, rups_weights)
                return nps
    # read the rupture data from the XML nodes
    num_probs = None
    for i, rupnode in enumerate(node):
        po = rupnode['probs_occur']
        probs = pmf.PMF(valid.pmf(po))
        if num_probs is None:  # first time
            num_probs = len(probs.data)
        elif len(probs.data) != num_probs:
            # probs_occur must have uniform length for all ruptures
            raise ValueError(
                'prob_occurs=%s has %d elements, expected %s'
                % (po, len(probs.data), num_probs))
        rup = RuptureConverter(rup_spacing).convert_node(rupnode)
        rup.tectonic_region_type = trt
        rup.weight = None if rups_weights is None else rups_weights[i]
        nps.data.append((rup, probs))
    return nps


class RuptureConverter(object):
    """
    Convert ruptures from nodes into Hazardlib ruptures.
    """
    fname = None  # should be set externally

    def __init__(self, rupture_mesh_spacing, complex_fault_mesh_spacing=None):
        self.rupture_mesh_spacing = rupture_mesh_spacing
        self.complex_fault_mesh_spacing = (
            complex_fault_mesh_spacing or rupture_mesh_spacing)

    def get_mag_rake_hypo(self, node):
        with context(self.fname, node):
            mag = ~node.magnitude
            rake = ~node.rake
            h = node.hypocenter
            hypocenter = geo.Point(h['lon'], h['lat'], h['depth'])
        return mag, rake, hypocenter

    def convert_node(self, node):
        """
        Convert the given rupture node into a hazardlib rupture, depending
        on the node tag.

        :param node: a node representing a rupture
        """
        return getattr(self, 'convert_' + striptag(node.tag))(node)

    def geo_line(self, edge):
        """
        Utility function to convert a node of kind edge
        into a :class:`openquake.hazardlib.geo.Line` instance.

        :param edge: a node describing an edge
        """
        with context(self.fname, edge.LineString.posList) as plist:
            coords = split_coords_2d(~plist)
        return geo.Line([geo.Point(*p) for p in coords])

    def geo_lines(self, edges):
        """
        Utility function to convert a list of edges into a list of
        :class:`openquake.hazardlib.geo.Line` instances.

        :param edge: a node describing an edge
        """
        lines = []
        for edge in edges:
            with context(self.fname, edge):
                coords = split_coords_3d(~edge.LineString.posList)
            lines.append(geo.Line([geo.Point(*p) for p in coords]))
        return lines

    def geo_planar(self, surface):
        """
        Utility to convert a PlanarSurface node with subnodes
        topLeft, topRight, bottomLeft, bottomRight into a
        :class:`openquake.hazardlib.geo.PlanarSurface` instance.

        :param surface: PlanarSurface node
        """
        with context(self.fname, surface):
            tl = surface.topLeft
            top_left = geo.Point(tl['lon'], tl['lat'], tl['depth'])
            tr = surface.topRight
            top_right = geo.Point(tr['lon'], tr['lat'], tr['depth'])
            bl = surface.bottomLeft
            bottom_left = geo.Point(bl['lon'], bl['lat'], bl['depth'])
            br = surface.bottomRight
            bottom_right = geo.Point(br['lon'], br['lat'], br['depth'])
        return geo.PlanarSurface.from_corner_points(
            top_left, top_right, bottom_right, bottom_left)

    def convert_surfaces(self, surface_nodes, sec_id=''):
        """
        :param surface_nodes: surface nodes as described below

        Utility to convert a list of surface nodes into a single hazardlib
        surface. There are four possibilities:

        1. there is a single simpleFaultGeometry node; returns a
           :class:`openquake.hazardlib.geo.simpleFaultSurface` instance
        2. there is a single complexFaultGeometry node; returns a
           :class:`openquake.hazardlib.geo.complexFaultSurface` instance
        3. there is a single griddedSurface node; returns a
           :class:`openquake.hazardlib.geo.GriddedSurface` instance
        4. there is either a single planarSurface or a list of planarSurface
           nodes; returns a :class:`openquake.hazardlib.geo.PlanarSurface`
           instance or a :class:`openquake.hazardlib.geo.MultiSurface` instance
        5. there is either a single kiteSurface or a list of kiteSurface
           nodes; returns a :class:`openquake.hazardlib.geo.KiteSurface`
           instance or a :class:`openquake.hazardlib.geo.MultiSurface` instance
        """
        surface_node = surface_nodes[0]
        if surface_node.tag.endswith('simpleFaultGeometry'):
            surface = geo.SimpleFaultSurface.from_fault_data(
                self.geo_line(surface_node),
                ~surface_node.upperSeismoDepth,
                ~surface_node.lowerSeismoDepth,
                ~surface_node.dip,
                self.rupture_mesh_spacing)
        elif surface_node.tag.endswith('complexFaultGeometry'):
            surface = geo.ComplexFaultSurface.from_fault_data(
                self.geo_lines(surface_node),
                self.complex_fault_mesh_spacing)
        elif surface_node.tag.endswith('griddedSurface'):
            with context(self.fname, surface_node):
                coords = split_coords_3d(~surface_node.posList)
            points = [geo.Point(*p) for p in coords]
            surface = geo.GriddedSurface.from_points_list(points)
        elif surface_node.tag.endswith('kiteSurface'):
            # single or multiple kite surfaces
            profs = [self.geo_lines(node) for node in surface_nodes]
            if len(profs) == 1:  # there is a single surface_node
                surface = geo.KiteSurface.from_profiles(
                    profs[0], self.rupture_mesh_spacing,
                    self.rupture_mesh_spacing, sec_id=sec_id)
            else:  # normally found in sections.xml
                surfaces = []
                for prof in profs:
                    surfaces.append(geo.KiteSurface.from_profiles(
                        prof, self.rupture_mesh_spacing,
                        self.rupture_mesh_spacing))
                surface = geo.MultiSurface(surfaces)
        else:  # a collection of planar surfaces
            if len(surface_nodes) == 1:
                return self.geo_planar(surface_nodes[0])
            planar_surfaces = list(map(self.geo_planar, surface_nodes))
            surface = geo.MultiSurface(planar_surfaces)
        return surface

    def convert_simpleFaultRupture(self, node):
        """
        Convert a simpleFaultRupture node.

        :param node: the rupture node
        """
        mag, rake, hypocenter = self.get_mag_rake_hypo(node)
        with context(self.fname, node):
            surfaces = [node.simpleFaultGeometry]
        rupt = source.rupture.BaseRupture(
            mag=mag, rake=rake, tectonic_region_type=None,
            hypocenter=hypocenter,
            surface=self.convert_surfaces(surfaces))
        return rupt

    def convert_complexFaultRupture(self, node):
        """
        Convert a complexFaultRupture node.

        :param node: the rupture node
        """
        mag, rake, hypocenter = self.get_mag_rake_hypo(node)
        with context(self.fname, node):
            [surface] = node.getnodes('complexFaultGeometry')
        rupt = source.rupture.BaseRupture(
            mag=mag, rake=rake, tectonic_region_type=None,
            hypocenter=hypocenter,
            surface=self.convert_surfaces([surface]))
        return rupt

    def convert_singlePlaneRupture(self, node):
        """
        Convert a singlePlaneRupture node.

        :param node: the rupture node
        """
        mag, rake, hypocenter = self.get_mag_rake_hypo(node)
        with context(self.fname, node):
            surfaces = [node.planarSurface]
        rupt = source.rupture.BaseRupture(
            mag=mag, rake=rake,
            tectonic_region_type=None,
            hypocenter=hypocenter,
            surface=self.convert_surfaces(surfaces))
        return rupt

    # used in scenarios or nonparametric sources
    def convert_multiPlanesRupture(self, node):
        """
        Convert a multiPlanesRupture node.

        :param node: the rupture node
        """
        mag, rake, hypocenter = self.get_mag_rake_hypo(node)
        with context(self.fname, node):
            if hasattr(node, 'planarSurface'):
                surfaces = list(node.getnodes('planarSurface'))
                for s in surfaces:
                    assert s.tag.endswith('planarSurface')
            elif hasattr(node, 'kiteSurface'):
                surfaces = list(node.getnodes('kiteSurface'))
                for s in surfaces:
                    assert s.tag.endswith('kiteSurface')
            else:
                raise ValueError('Only multiSurfaces of planarSurfaces or'
                                 'kiteSurfaces are supported (no mix)')
        rupt = source.rupture.BaseRupture(
            mag=mag, rake=rake,
            tectonic_region_type=None,
            hypocenter=hypocenter,
            surface=self.convert_surfaces(surfaces))
        return rupt

    def convert_griddedRupture(self, node):
        """
        Convert a griddedRupture node.

        :param node: the rupture node
        """
        mag, rake, hypocenter = self.get_mag_rake_hypo(node)
        with context(self.fname, node):
            surfaces = [node.griddedSurface]
        rupt = source.rupture.BaseRupture(
            mag=mag, rake=rake,
            tectonic_region_type=None,
            hypocenter=hypocenter,
            surface=self.convert_surfaces(surfaces))
        return rupt

    def convert_ruptureCollection(self, node):
        """
        :param node: a ruptureCollection node
        :returns: a dictionary trt_smr -> EBRuptures
        """
        coll = {}
        for grpnode in node:
            trt_smr = int(grpnode['id'])
            coll[trt_smr] = ebrs = []
            for node in grpnode:
                rup = self.convert_node(node)
                rup.rup_id = int(node['id'])
                sesnodes = node.stochasticEventSets
                n = 0  # number of events
                for sesnode in sesnodes:
                    with context(self.fname, sesnode):
                        n += len(sesnode.text.split())
                ebr = source.rupture.EBRupture(rup, 0, 0, numpy.array([n]))
                ebrs.append(ebr)
        return coll


class SourceConverter(RuptureConverter):
    """
    Convert sources from valid nodes into Hazardlib objects.
    """
    def __init__(self, investigation_time=50., rupture_mesh_spacing=5.,
                 complex_fault_mesh_spacing=None, width_of_mfd_bin=1.0,
                 area_source_discretization=None,
                 minimum_magnitude={'default': 0},
                 source_id=(), discard_trts=(),
                 floating_x_step=0, floating_y_step=0,
                 source_nodes=(),
                 infer_occur_rates=False):
        self.investigation_time = investigation_time
        self.area_source_discretization = area_source_discretization
        self.minimum_magnitude = minimum_magnitude
        self.rupture_mesh_spacing = rupture_mesh_spacing
        self.complex_fault_mesh_spacing = (
            complex_fault_mesh_spacing or rupture_mesh_spacing)
        self.width_of_mfd_bin = width_of_mfd_bin
        self.source_id = tuple(source_id)
        self.discard_trts = discard_trts
        self.floating_x_step = floating_x_step
        self.floating_y_step = floating_y_step
        self.source_nodes = source_nodes
        self.infer_occur_rates = infer_occur_rates

    def convert_node(self, node):
        """
        Convert the given node into a hazardlib source or group, depending
        on the node tag.

        :param node: a node representing a source or a SourceGroup
        """
        trt = node.attrib.get('tectonicRegion')
        if trt and trt in self.discard_trts:
            return
        name = striptag(node.tag)
        if name.endswith('Source'):  # source node
            source_id = node['id']
            if self.source_id and not source_id.startswith(self.source_id):
                # if source_id is set in the job.ini, discard all other sources
                return
            elif self.source_nodes and name not in self.source_nodes:
                # if source_nodes is set, discard all other source nodes
                return
        obj = getattr(self, 'convert_' + name)(node)
        if hasattr(obj, 'mfd') and hasattr(obj.mfd, 'slip_rate'):
            # TruncatedGRMFD with slip rate (for Slovenia)
            m = obj.mfd
            obj.mfd = m.from_slip_rate(
                m.min_mag, m.max_mag, m.bin_width, m.b_val,
                m.slip_rate, m.rigidity, obj.get_fault_surface_area())
        return obj

    def convert_geometryModel(self, node):
        """
        :param node: a geometryModel node
        :returns: a dictionary sec_id -> section
        """
        sections = {secnode["id"]: self.convert_node(secnode)
                    for secnode in node}
        return sections

    def convert_section(self, node):
        """
        :param node: a section node
        :returns: a list of surfaces
        """
        with context(self.fname, node):
            if hasattr(node, 'planarSurface'):
                surfaces = list(node.getnodes('planarSurface'))
            elif hasattr(node, 'kiteSurface'):
                surfaces = list(node.getnodes('kiteSurface'))
            else:
                raise ValueError('Only planarSurfaces or kiteSurfaces ' +
                                 'supported')
            return self.convert_surfaces(surfaces, node['id'])

    def get_tom(self, node):
        """
        Convert the given node into a Temporal Occurrence Model object.

        :param node: a node of kind poissonTOM or similar
        :returns: a :class:`openquake.hazardlib.tom.BaseTOM` instance
        """
        occurrence_rate = node.get('occurrence_rate')
        kwargs = {}
        # the occurrence_rate is not None only for clusters of sources,
        # the ones implemented in calc.hazard_curve, see test case_35
        if occurrence_rate:
            tom_cls = tom.registry['ClusterPoissonTOM']
            return tom_cls(self.investigation_time, occurrence_rate)
        if 'tom' in node.attrib:
            tom_cls = tom.registry[node['tom']]
            # if tom is negbinom, sets mu and alpha attr to tom_class
            if node['tom'] == 'NegativeBinomialTOM':
                kwargs = {'alpha': float(node['alpha']),
                          'mu': float(node['mu'])}
        else:
            tom_cls = tom.registry['PoissonTOM']
        return tom_cls(time_span=self.investigation_time, **kwargs)

    def convert_mfdist(self, node):
        """
        Convert the given node into a Magnitude-Frequency Distribution
        object.

        :param node: a node of kind incrementalMFD or truncGutenbergRichterMFD
        :returns: a :class:`openquake.hazardlib.mfd.EvenlyDiscretizedMFD.` or
                  :class:`openquake.hazardlib.mfd.TruncatedGRMFD` instance
        """
        with context(self.fname, node):
            [mfd_node] = [subnode for subnode in node
                          if subnode.tag.endswith(KNOWN_MFDS)]
        with context(self.fname, mfd_node):
            if mfd_node.tag.endswith('incrementalMFD'):
                return mfd.EvenlyDiscretizedMFD(
                    min_mag=mfd_node['minMag'], bin_width=mfd_node['binWidth'],
                    occurrence_rates=~mfd_node.occurRates)
            elif mfd_node.tag.endswith('truncGutenbergRichterMFD'):
                slip_rate = mfd_node.get('slipRate')
                rigidity = mfd_node.get('rigidity')
                if slip_rate:
                    assert rigidity
                    # instantiate with an area of 1, to be fixed later on
                    gr_mfd = mfd.TruncatedGRMFD.from_slip_rate(
                        mfd_node['minMag'], mfd_node['maxMag'],
                        self.width_of_mfd_bin, mfd_node['bValue'],
                        slip_rate, rigidity, area=1)
                else:
                    gr_mfd = mfd.TruncatedGRMFD(
                        a_val=mfd_node['aValue'], b_val=mfd_node['bValue'],
                        min_mag=mfd_node['minMag'], max_mag=mfd_node['maxMag'],
                        bin_width=self.width_of_mfd_bin)
                return gr_mfd
            elif mfd_node.tag.endswith('arbitraryMFD'):
                return mfd.ArbitraryMFD(
                    magnitudes=~mfd_node.magnitudes,
                    occurrence_rates=~mfd_node.occurRates)
            elif mfd_node.tag.endswith('YoungsCoppersmithMFD'):
                return mfd.YoungsCoppersmith1985MFD(
                    min_mag=mfd_node["minMag"],
                    b_val=mfd_node["bValue"],
                    char_mag=mfd_node["characteristicMag"],
                    char_rate=mfd_node.get("characteristicRate"),
                    total_moment_rate=mfd_node.get("totalMomentRate"),
                    bin_width=mfd_node["binWidth"])
            elif mfd_node.tag.endswith('multiMFD'):
                return mfd.multi_mfd.MultiMFD.from_node(
                    mfd_node, self.width_of_mfd_bin)
            elif mfd_node.tag.endswith('taperedGutenbergRichterMFD'):
                return mfd.TaperedGRMFD(
                    mfd_node['minMag'], mfd_node['maxMag'],
                    mfd_node['cornerMag'], self.width_of_mfd_bin,
                    mfd_node['aValue'], mfd_node['bValue'])

    def convert_npdist(self, node):
        """
        Convert the given node into a Nodal Plane Distribution.

        :param node: a nodalPlaneDist node
        :returns: a :class:`openquake.hazardlib.geo.NodalPlane` instance
        """
        with context(self.fname, node):
            npnode = node.nodalPlaneDist
            npdist = []
            for np in npnode:
                prob, strike, dip, rake = (
                    np['probability'], np['strike'], np['dip'], np['rake'])
                npdist.append((prob, geo.NodalPlane(strike, dip, rake)))
        with context(self.fname, npnode):
            fix_dupl(npdist, self.fname, npnode.lineno)
            return pmf.PMF(npdist)

    def convert_hddist(self, node):
        """
        Convert the given node into a probability mass function for the
        hypo depth distribution.

        :param node: a hypoDepthDist node
        :returns: a :class:`openquake.hazardlib.pmf.PMF` instance
        """
        with context(self.fname, node):
            hdnode = node.hypoDepthDist
            hddist = [(hd['probability'], hd['depth']) for hd in hdnode]
        with context(self.fname, hdnode):
            fix_dupl(hddist, self.fname, hdnode.lineno)
            return pmf.PMF(hddist)

    def convert_areaSource(self, node):
        """
        Convert the given node into an area source object.

        :param node: a node with tag areaGeometry
        :returns: a :class:`openquake.hazardlib.source.AreaSource` instance
        """
        with context(self.fname, node):
            geom = node.areaGeometry
            coords = split_coords_2d(~geom.Polygon.exterior.LinearRing.posList)
            polygon = geo.Polygon([geo.Point(*xy) for xy in coords])
            msr = ~node.magScaleRel
            area_discretization = geom.attrib.get(
                'discretization', self.area_source_discretization)
        if area_discretization is None:
            raise ValueError(
                'The source %r has no `discretization` parameter and the job.'
                'ini file has no `area_source_discretization` parameter either'
                % node['id'])
        return source.AreaSource(
            source_id=node['id'],
            name=node['name'],
            tectonic_region_type=node.attrib.get('tectonicRegion'),
            mfd=self.convert_mfdist(node),
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=~node.ruptAspectRatio,
            upper_seismogenic_depth=~geom.upperSeismoDepth,
            lower_seismogenic_depth=~geom.lowerSeismoDepth,
            nodal_plane_distribution=self.convert_npdist(node),
            hypocenter_distribution=self.convert_hddist(node),
            polygon=polygon,
            area_discretization=area_discretization,
            temporal_occurrence_model=self.get_tom(node))

    def convert_pointSource(self, node):
        """
        Convert the given node into a point source object.

        :param node: a node with tag pointGeometry
        :returns: a :class:`openquake.hazardlib.source.PointSource` instance
        """
        geom = node.pointGeometry
        lon_lat = ~geom.Point.pos
        msr = ~node.magScaleRel
        return source.PointSource(
            source_id=node['id'],
            name=node['name'],
            tectonic_region_type=node.attrib.get('tectonicRegion'),
            mfd=self.convert_mfdist(node),
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=~node.ruptAspectRatio,
            upper_seismogenic_depth=~geom.upperSeismoDepth,
            lower_seismogenic_depth=~geom.lowerSeismoDepth,
            location=geo.Point(*lon_lat),
            nodal_plane_distribution=self.convert_npdist(node),
            hypocenter_distribution=self.convert_hddist(node),
            temporal_occurrence_model=self.get_tom(node))

    def convert_multiPointSource(self, node):
        """
        Convert the given node into a MultiPointSource object.

        :param node: a node with tag multiPointGeometry
        :returns: a :class:`openquake.hazardlib.source.MultiPointSource`
        """
        geom = node.multiPointGeometry
        lons, lats = zip(*split_coords_2d(~geom.posList))
        msr = ~node.magScaleRel
        return source.MultiPointSource(
            source_id=node['id'],
            name=node['name'],
            tectonic_region_type=node.attrib.get('tectonicRegion'),
            mfd=self.convert_mfdist(node),
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=~node.ruptAspectRatio,
            upper_seismogenic_depth=~geom.upperSeismoDepth,
            lower_seismogenic_depth=~geom.lowerSeismoDepth,
            nodal_plane_distribution=self.convert_npdist(node),
            hypocenter_distribution=self.convert_hddist(node),
            mesh=geo.Mesh(F32(lons), F32(lats)),
            temporal_occurrence_model=self.get_tom(node))

    def convert_simpleFaultSource(self, node):
        """
        Convert the given node into a simple fault object.

        :param node: a node with tag areaGeometry
        :returns: a :class:`openquake.hazardlib.source.SimpleFaultSource`
                  instance
        """
        geom = node.simpleFaultGeometry
        msr = ~node.magScaleRel
        fault_trace = self.geo_line(geom)
        mfd = self.convert_mfdist(node)
        with context(self.fname, node):
            try:
                hypo_list = valid.hypo_list(node.hypoList)
            except AttributeError:
                hypo_list = ()
            try:
                slip_list = valid.slip_list(node.slipList)
            except AttributeError:
                slip_list = ()
            simple = source.SimpleFaultSource(
                node['id'], node['name'],
                node.attrib.get('tectonicRegion'),
                mfd, self.rupture_mesh_spacing,
                msr, ~node.ruptAspectRatio, self.get_tom(node),
                ~geom.upperSeismoDepth, ~geom.lowerSeismoDepth,
                fault_trace, ~geom.dip, ~node.rake,
                [hypo_list, slip_list])
        return simple

    def convert_kiteFaultSource(self, node):
        """
        Convert the given node into a kite fault object.

        :param node: a node with tag kiteFaultSource
        :returns: a :class:`openquake.hazardlib.source.KiteFaultSource`
                  instance
        """
        as_kite = True
        try:
            geom = node.simpleFaultGeometry
            fault_trace = self.geo_line(geom)
            as_kite = False
        except Exception:
            geom = node.kiteSurface
            profiles = self.geo_lines(geom)

        msr = ~node.magScaleRel
        mfd = self.convert_mfdist(node)

        # get rupture floating steps
        xstep = self.floating_x_step
        ystep = self.floating_y_step

        with context(self.fname, node):
            if as_kite:
                outsrc = source.KiteFaultSource(
                    source_id=node['id'],
                    name=node['name'],
                    tectonic_region_type=node.attrib.get('tectonicRegion'),
                    mfd=mfd,
                    rupture_mesh_spacing=self.rupture_mesh_spacing,
                    magnitude_scaling_relationship=msr,
                    rupture_aspect_ratio=~node.ruptAspectRatio,
                    temporal_occurrence_model=self.get_tom(node),
                    profiles=profiles,
                    floating_x_step=xstep,
                    floating_y_step=ystep,
                    rake=~node.rake,
                    profiles_sampling=None
                    )
            else:
                param = source.base.SourceParam(
                    node['id'], node['name'],
                    node.attrib.get('tectonicRegion'),
                    mfd, self.rupture_mesh_spacing,
                    msr, ~node.ruptAspectRatio, self.get_tom(node))
                outsrc = source.KiteFaultSource.as_simple_fault(
                    param,
                    ~geom.upperSeismoDepth, ~geom.lowerSeismoDepth,
                    fault_trace, ~geom.dip, ~node.rake,
                    xstep, ystep)
        return outsrc

    def convert_complexFaultSource(self, node):
        """
        Convert the given node into a complex fault object.

        :param node: a node with tag areaGeometry
        :returns: a :class:`openquake.hazardlib.source.ComplexFaultSource`
                  instance
        """
        geom = node.complexFaultGeometry
        edges = self.geo_lines(geom)
        mfd = self.convert_mfdist(node)
        msr = ~node.magScaleRel
        with context(self.fname, node):
            cmplx = source.ComplexFaultSource(
                source_id=node['id'],
                name=node['name'],
                tectonic_region_type=node.attrib.get('tectonicRegion'),
                mfd=mfd,
                rupture_mesh_spacing=self.complex_fault_mesh_spacing,
                magnitude_scaling_relationship=msr,
                rupture_aspect_ratio=~node.ruptAspectRatio,
                edges=edges,
                rake=~node.rake,
                temporal_occurrence_model=self.get_tom(node))
        return cmplx

    def convert_characteristicFaultSource(self, node):
        """
        Convert the given node into a characteristic fault object.

        :param node:
            a characteristicFaultSource node
        :returns:
            a :class:`openquake.hazardlib.source.CharacteristicFaultSource`
            instance
        """
        char = source.CharacteristicFaultSource(
            source_id=node['id'],
            name=node['name'],
            tectonic_region_type=node.attrib.get('tectonicRegion'),
            mfd=self.convert_mfdist(node),
            surface=self.convert_surfaces(node.surface),
            rake=~node.rake,
            temporal_occurrence_model=self.get_tom(node))
        return char

    def convert_nonParametricSeismicSource(self, node):
        """
        Convert the given node into a non parametric source object.

        :param node:
            a node with tag areaGeometry
        :returns:
            a :class:`openquake.hazardlib.source.NonParametricSeismicSource`
            instance
        """
        return convert_nonParametricSeismicSource(
            self.fname, node, self.rupture_mesh_spacing)

    # used in UCERF
    def convert_multiFaultSource(self, node):
        """
        Convert the given node into a multi fault source object.

        :param node:
            a node with tag multiFaultSource
        :returns:
            a :class:`openquake.hazardlib.source.multiFaultSource`
            instance
        """
        sid = node.get('id')
        name = node.get('name')
        trt = node.get('tectonicRegion')
        path = os.path.splitext(self.fname)[0] + '.hdf5'
        hdf5_fname = path if os.path.exists(path) else None

        # the first (sub)node called <faults> is optional
        try:
            faults = {f['tag']: f['indexes'] for f in node.faults}
            nodes = node.nodes[1:]  # the other nodes contain the ruptures
        except AttributeError:
            faults = {}
            nodes = node.nodes  # all the nodes contain ruptures

        if hdf5_fname is None and not nodes:
            raise OSError(f'Could not find {path}')
        elif not nodes:
            # read the rupture data from the HDF5 file
            with hdf5.File(hdf5_fname, 'r') as h:
                dic = {k: d[:] for k, d in h[node['id']].items()}
            with context(self.fname, node):
                idxs = [x.decode('utf8').split() for x in dic['rupture_idxs']]
                mags = rounded_unique(dic['mag'], idxs)
            # NB: the sections will be fixed later on, in source_reader
            mfs = MultiFaultSource(sid, name, trt, idxs,
                                   dic['probs_occur'],
                                   mags, dic['rake'], faults,
                                   self.investigation_time,
                                   self.infer_occur_rates)
            return mfs
        probs = []
        mags = []
        rakes = []
        idxs = []
        num_probs = None
        for i, rupnode in enumerate(nodes):
            with context(self.fname, rupnode):
                prb = valid.probabilities(rupnode['probs_occur'])
                if num_probs is None:  # first time
                    num_probs = len(prb)
                elif len(prb) != num_probs:
                    # probs_occur must have uniform length for all ruptures
                    with context(self.fname, rupnode):
                        raise ValueError(
                            'prob_occurs=%s has %d elements, expected %s'
                            % (rupnode['probs_occur'], len(prb),
                               num_probs))
                probs.append(prb)
                mags.append(~rupnode.magnitude)
                rakes.append(~rupnode.rake)
                idxs.append(rupnode.sectionIndexes['indexes'])
        with context(self.fname, node):
            mags = rounded_unique(mags, idxs)
            assert len(mags)
        rakes = numpy.array(rakes)
        # NB: the sections will be fixed later on, in source_reader
        mfs = MultiFaultSource(sid, name, trt, idxs, probs, mags, rakes, faults,
                               self.investigation_time,
                               self.infer_occur_rates)
        return mfs

    def convert_sourceModel(self, node):
        return [self.convert_node(subnode) for subnode in node]

    def convert_sourceGroup(self, node):
        """
        Convert the given node into a SourceGroup object.

        :param node:
            a node with tag sourceGroup
        :returns:
            a :class:`SourceGroup` instance
        """
        trt = node['tectonicRegion']
        srcs_weights = node.attrib.get('srcs_weights')
        grp_attrs = {k: v for k, v in node.attrib.items()
                     if k not in ('name', 'src_interdep', 'rup_interdep',
                                  'srcs_weights')}
        if node.attrib.get('src_interdep') != 'mutex':
            # ignore weights set to 1 in old versions of the engine
            srcs_weights = None
        sg = SourceGroup(trt, min_mag=self.minimum_magnitude)
        sg.temporal_occurrence_model = self.get_tom(node)
        sg.name = node.attrib.get('name')
        # Set attributes related to occurrence
        sg.src_interdep = node.attrib.get('src_interdep', 'indep')
        sg.rup_interdep = node.attrib.get('rup_interdep', 'indep')
        sg.grp_probability = node.attrib.get('grp_probability', 1)
        # Set the cluster attribute
        sg.cluster = node.attrib.get('cluster') == 'true'
        # Filter admitted cases
        # 1. The source group is a cluster. In this case the cluster must have
        #    the attributes required to define its occurrence in time.
        if sg.cluster:
            msg = 'A cluster group requires the definition of a temporal'
            msg += ' occurrence model'
            assert 'tom' in node.attrib, msg
            if isinstance(tom, PoissonTOM):
                # hack in place of a ClusterPoissonTOM
                assert hasattr(sg, 'occurrence_rate')

        for src_node in node:
            src = self.convert_node(src_node)
            if src is None:  # filtered out by source_id
                continue
            # transmit the group attributes to the underlying source
            for attr, value in grp_attrs.items():
                if attr == 'tectonicRegion':
                    src_trt = src_node.get('tectonicRegion')
                    if src_trt and src_trt != trt:
                        with context(self.fname, src_node):
                            raise ValueError('Found %s, expected %s' %
                                             (src_node['tectonicRegion'], trt))
                    src.tectonic_region_type = trt
                elif attr == 'grp_probability':
                    pass  # do not transmit
                else:  # transmit as it is
                    setattr(src, attr, node[attr])
            sg.update(src)
        if sg and sg.src_interdep == 'mutex':
            # sg can be empty if source_id is specified and it is different
            # from any source in sg
            if len(node) and len(srcs_weights) != len(node):
                raise ValueError(
                    'There are %d srcs_weights but %d source(s) in %s'
                    % (len(srcs_weights), len(node), self.fname))
            tot = 0
            with context(self.fname, node):
                for src, sw in zip(sg, srcs_weights):
                    if ':' not in src.source_id:
                        raise NameError('You must use the colon convention '
                                        'with mutex sources')
                    src.mutex_weight = sw
                    tot += sw
                numpy.testing.assert_allclose(
                    tot, 1., err_msg='sum(srcs_weights)', atol=5E-6)

        # check that, when the cluster option is set, the group has a temporal
        # occurrence model properly defined
        if sg.cluster and not hasattr(sg, 'temporal_occurrence_model'):
            msg = 'The Source Group is a cluster but does not have a '
            msg += 'temporal occurrence model'
            raise ValueError(msg)
        return sg


@dataclass
class Row:
    id: str
    name: str
    code: str
    groupname: str
    tectonicregion: str
    mfd: str
    magscalerel: str
    ruptaspectratio: float
    upperseismodepth: float
    lowerseismodepth: float
    nodalplanedist: list
    hypodepthdist: list
    hypoList: list
    slipList: list
    rake: float
    geomprops: list
    geom: str
    coords: list
    wkt: str


Row.__init__.__defaults__ = ('',)  # wkt


@dataclass
class NPRow:
    id: str
    name: str
    code: str
    tectonicregion: str
    geom: str
    coords: list
    wkt: str


def _planar(surface):
    poly = []
    tl = surface.topLeft
    poly.append((tl['lon'], tl['lat'], tl['depth']))
    tr = surface.topRight
    poly.append((tr['lon'], tr['lat'], tr['depth']))
    br = surface.bottomRight
    poly.append((br['lon'], br['lat'], br['depth']))
    bl = surface.bottomLeft
    poly.append((bl['lon'], bl['lat'], bl['depth']))
    poly.append((tl['lon'], tl['lat'], tl['depth']))  # close the polygon
    return [poly]


class RowConverter(SourceConverter):
    """
    Used in the command oq nrml_to_csv to convert source models into
    Row objects.
    """
    def convert_node(self, node):
        """
        Convert the given source node into a Row object
        """
        trt = node.attrib.get('tectonicRegion')
        if trt and trt in self.discard_trts:
            return
        with context(self.fname, node):
            return getattr(self, 'convert_' + striptag(node.tag))(node)

    def convert_mfdist(self, node):
        with context(self.fname, node):
            [mfd_node] = [subnode for subnode in node
                          if subnode.tag.endswith(KNOWN_MFDS)]
        return str(node_to_dict(mfd_node))

    def convert_npdist(self, node):
        lst = []
        for w, np in super().convert_npdist(node).data:
            dic = {'probability': w, 'dip': np.dip, 'rake': np.rake,
                   'strike': np.strike}
            lst.append(dic)
        return str(lst)

    def convert_hddist(self, node):
        lst = []
        for w, hd in super().convert_hddist(node).data:
            lst.append(dict(probability=w, depth=hd))
        return str(lst)

    def convert_hypolist(self, node):
        try:
            hypo_list = node.hypoList
        except AttributeError:
            lst = []
        else:
            lst = [{'alongStrike': hl['alongStrike'],
                    'downDip': hl['downDip'],
                    'weight': hl['weight']} for hl in hypo_list]
        return str(lst)

    def convert_sliplist(self, node):
        try:
            slip_list = node.slipList
        except AttributeError:
            lst = []
        else:
            lst = [node_to_dict(n)['slip'] for n in slip_list.nodes]
        return str(lst)

    def convert_rake(self, node):
        try:
            return ~node.rake
        except AttributeError:
            return ''

    def convert_geomprops(self, node):
        # NOTE: node_to_dict(node) returns a dict having the geometry type as
        # key and the corresponding properties as value, so we get the first
        # value to retrieve the information we need
        full_geom_props = list(node_to_dict(node).values())[0]
        geom_props = {k: full_geom_props[k] for k in full_geom_props
                      if k not in EXCLUDE_FROM_GEOM_PROPS}
        return str(geom_props)

    def convert_areaSource(self, node):
        geom = node.areaGeometry
        coords = split_coords_2d(~geom.Polygon.exterior.LinearRing.posList)
        if coords[0] != coords[-1]:
            coords += [coords[0]]  # close the polygon
        return Row(
            node['id'],
            node['name'],
            'A',
            node.get('groupname', ''),
            node.get('tectonicRegion', ''),
            self.convert_mfdist(node),
            str(~node.magScaleRel),
            ~node.ruptAspectRatio,
            ~geom.upperSeismoDepth,
            ~geom.lowerSeismoDepth,
            self.convert_npdist(node),
            self.convert_hddist(node),
            self.convert_hypolist(node),
            self.convert_sliplist(node),
            self.convert_rake(node),
            self.convert_geomprops(geom),
            'Polygon', [coords])

    def convert_pointSource(self, node):
        geom = node.pointGeometry
        return Row(
            node['id'],
            node['name'],
            'P',
            node.get('groupname', ''),
            node.get('tectonicRegion', ''),
            self.convert_mfdist(node),
            str(~node.magScaleRel),
            ~node.ruptAspectRatio,
            ~geom.upperSeismoDepth,
            ~geom.lowerSeismoDepth,
            self.convert_npdist(node),
            self.convert_hddist(node),
            self.convert_hypolist(node),
            self.convert_sliplist(node),
            self.convert_rake(node),
            self.convert_geomprops(geom),
            'Point', ~geom.Point.pos)

    def convert_multiPointSource(self, node):
        geom = node.multiPointGeometry
        coords = split_coords_2d(~geom.posList)
        return Row(
            node['id'],
            node['name'],
            'M',
            node.get('groupname', ''),
            node.get('tectonicRegion', ''),
            self.convert_mfdist(node),
            str(~node.magScaleRel),
            ~node.ruptAspectRatio,
            ~geom.upperSeismoDepth,
            ~geom.lowerSeismoDepth,
            self.convert_npdist(node),
            self.convert_hddist(node),
            self.convert_hypolist(node),
            self.convert_sliplist(node),
            self.convert_rake(node),
            self.convert_geomprops(geom),
            'MultiPoint', coords)

    def convert_simpleFaultSource(self, node):
        geom = node.simpleFaultGeometry
        return Row(
            node['id'],
            node['name'],
            'S',
            node.get('groupname', ''),
            node.get('tectonicRegion', ''),
            self.convert_mfdist(node),
            str(~node.magScaleRel),
            ~node.ruptAspectRatio,
            ~geom.upperSeismoDepth,
            ~geom.lowerSeismoDepth,
            [],
            [],
            self.convert_hypolist(node),
            self.convert_sliplist(node),
            self.convert_rake(node),
            self.convert_geomprops(geom),
            'LineString', [(p.x, p.y) for p in self.geo_line(geom)])

    def convert_complexFaultSource(self, node):
        geom = node.complexFaultGeometry  # 1005
        edges = []
        for line in self.geo_lines(geom):
            edges.append([(p.x, p.y, p.z) for p in line])
        return Row(
            node['id'],
            node['name'],
            'C',
            node.get('groupname', ''),
            node.get('tectonicRegion', ''),
            self.convert_mfdist(node),
            str(~node.magScaleRel),
            ~node.ruptAspectRatio,
            numpy.nan,
            numpy.nan,
            [],
            [],
            self.convert_hypolist(node),
            self.convert_sliplist(node),
            self.convert_rake(node),
            self.convert_geomprops(geom),
            '3D MultiLineString', edges)

    def convert_characteristicFaultSource(self, node):
        _, kind = node.surface[0].tag.split('}')
        if kind == 'simpleFaultGeometry':
            geom = 'LineString'
            coords = [(point.x, point.y) for point in self.geo_line(
                node.surface.simpleFaultGeometry)]
        elif kind == 'complexFaultGeometry':
            geom = '3D MultiLineString'
            coords = []
            for line in self.geo_lines(node.surface.complexFaultGeometry):
                coords.append([(p.x, p.y, p.z) for p in line])
        elif kind == 'planarSurface':
            geom = '3D MultiPolygon'
            coords = [_planar(surface) for surface in node.surface]
        else:
            raise NotImplementedError(kind)
        return Row(
            node['id'],
            node['name'],
            'X',
            node.get('groupname', ''),
            node.get('tectonicRegion', ''),
            self.convert_mfdist(node),
            numpy.nan,
            numpy.nan,
            numpy.nan,
            numpy.nan,
            [{'rake': ~node.rake}],
            [],
            self.convert_hypolist(node),
            self.convert_sliplist(node),
            self.convert_rake(node),
            self.convert_geomprops(node.surface),
            geom, coords, '')

    def convert_nonParametricSeismicSource(self, node):
        nps = convert_nonParametricSeismicSource(self.fname, node)
        return NPRow(
            node['id'],
            node['name'],
            'N',
            node['tectonicRegion'],
            'Polygon', [nps.polygon.coords], '')

    def convert_multiFaultSource(self, node):
        mfs = super().convert_multiFaultSource(node)
        return NPRow(node['id'], node['name'], 'F',
                     node.get('tectonicRegion', ''), 'Polygon', mfs, '')

# ################### MultiPointSource conversion ######################## #


def multikey(node):
    """
    :returns: (usd, lsd, rar, hddist, npdist, magScaleRel) for the given node
    """
    hd = tuple((node['probability'], node['depth'])
               for node in node.hypoDepthDist)
    npd = tuple(
        ((node['probability'], node['rake'], node['strike'], node['dip']))
        for node in node.nodalPlaneDist)
    geom = node.pointGeometry
    return (round(~geom.upperSeismoDepth, 1), round(~geom.lowerSeismoDepth, 1),
            ~node.ruptAspectRatio, hd, npd, str(~node.magScaleRel))


def collapse(array):
    """
    Collapse a homogeneous array into a scalar; do nothing if the array
    is not homogenous
    """
    if len(set(a for a in array)) == 1:  # homogenous array
        return array[0]
    return array


def mfds2multimfd(mfds):
    """
    Convert a list of MFD nodes into a single MultiMFD node
    """
    _, kind = mfds[0].tag.split('}')
    node = Node('multiMFD', dict(kind=kind, size=len(mfds)))
    lengths = None
    for field in mfd.multi_mfd.ASSOC[kind][1:]:
        alias = mfd.multi_mfd.ALIAS.get(field, field)
        if field in ('magnitudes', 'occurRates'):
            data = [~getattr(m, field) for m in mfds]
            lengths = [len(d) for d in data]
            data = sum(data, [])  # list of lists
        else:
            try:
                data = [m[alias] for m in mfds]
            except KeyError:
                if alias == 'binWidth':
                    # missing bindWidth in GR MDFs is ok
                    continue
                else:
                    raise
        node.append(Node(field, text=collapse(data)))
        if lengths:  # this is the last field if present
            node.append(Node('lengths', text=collapse(lengths)))
    return node


def _pointsources2multipoints(srcs, i):
    # converts pointSources with the same hddist, npdist and msr into a
    # single multiPointSource.
    allsources = []
    for (usd, lsd, rar, hd, npd, msr), sources in groupby(
            srcs, multikey).items():
        if len(sources) == 1:  # there is a single source
            allsources.extend(sources)
            continue
        mfds = [src[3] for src in sources]
        points = []
        for src in sources:
            pg = src.pointGeometry
            points.extend(~pg.Point.pos)
        geom = Node('multiPointGeometry')
        geom.append(Node('gml:posList', text=points))
        geom.append(Node('upperSeismoDepth', text=usd))
        geom.append(Node('lowerSeismoDepth', text=lsd))
        node = Node(
            'multiPointSource',
            dict(id='mps-%d' % i, name='multiPointSource-%d' % i),
            nodes=[geom])
        node.append(Node("magScaleRel", text=collapse(msr)))
        node.append(Node("ruptAspectRatio", text=rar))
        node.append(mfds2multimfd(mfds))
        node.append(Node('nodalPlaneDist', nodes=[
            Node('nodalPlane', dict(probability=prob, rake=rake,
                                    strike=strike, dip=dip))
            for prob, rake, strike, dip in npd]))
        node.append(Node('hypoDepthDist', nodes=[
            Node('hypoDepth', dict(depth=depth, probability=prob))
            for prob, depth in hd]))
        allsources.append(node)
        i += 1
    return i, allsources


def drop_trivial_weights(group):
    ws = group.attrib.get('srcs_weights')
    if ws and len(set(ws)) == 1:  # all equal
        del group.attrib['srcs_weights']


def update_source_model(sm_node, fname):
    """
    :param sm_node: a sourceModel Node object containing sourceGroups
    """
    i = 0
    for group in sm_node:
        if not group.tag.endswith('sourceGroup'):
            raise InvalidFile('wrong NRML, got %s instead of '
                              'sourceGroup in %s' % (group.tag, fname))
        drop_trivial_weights(group)
        psrcs = []
        others = []
        for src in group:
            try:
                del src.attrib['tectonicRegion']  # make the trt implicit
            except KeyError:
                pass  # already missing
            if src.tag.endswith('pointSource'):
                psrcs.append(src)
            else:
                others.append(src)
        others.sort(key=lambda src: (src.tag, src['id']))
        i, sources = _pointsources2multipoints(psrcs, i)
        group.nodes = sources + others
