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
import operator
import collections
import pickle
import time
import logging
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import groupby
from openquake.baselib.node import context, striptag, Node
from openquake.hazardlib import geo, mfd, pmf, source, tom
from openquake.hazardlib import valid, InvalidFile
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source import NonParametricSeismicSource

U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
source_dt = numpy.dtype([('srcidx', U32), ('num_ruptures', U32),
                         ('pik', hdf5.vuint8)])


class SourceGroup(collections.Sequence):
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
    :param eff_ruptures:
        the number of ruptures contained in the group; if -1,
        the number is unknown and has to be computed by using
        get_set_num_ruptures
    :param tot_ruptures:
        the potential maximum number of ruptures contained in the group
    :param temporal_occurrence_model:
        A temporal occurrence model controlling the source group occurrence
    :param cluster:
        A boolean indicating if the sources behaves as a cluster similarly
        to what used by the USGS for the New Madrid in the 2008 National
        Hazard Model.
    """
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
                 rup_interdep='indep', grp_probability=None,
                 min_mag={'default': 0}, max_mag=None, id=0, eff_ruptures=-1,
                 tot_ruptures=0, temporal_occurrence_model=None,
                 cluster=False):
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
        self.id = id
        self.tot_ruptures = tot_ruptures  # updated in .update(src)
        if sources:
            for src in sorted(sources, key=operator.attrgetter('source_id')):
                self.update(src)
        self.source_model = None  # to be set later, in CompositionInfo
        self.eff_ruptures = eff_ruptures  # set later by get_rlzs_assoc
        self.temporal_occurrence_model = temporal_occurrence_model
        self.cluster = cluster
        # check weights in case of mutually exclusive ruptures
        if rup_interdep == 'mutex':
            for src in self.sources:
                assert isinstance(src, NonParametricSeismicSource)
                for rup, _ in src.data:
                    assert rup.weight is not None

    @property
    def atomic(self):
        """
        :returns: True if the group cannot be split
        """
        return (self.cluster or self.src_interdep == 'mutex' or
                self.rup_interdep == 'mutex')

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
        if not src.min_mag:  # if not set already
            src.min_mag = self.min_mag.get(self.trt) or self.min_mag['default']
        # checking mutex ruptures
        if (not isinstance(src, NonParametricSeismicSource) and
                self.rup_interdep == 'mutex'):
            msg = "Mutually exclusive ruptures can only be "
            msg += "modelled using non-parametric sources"
            raise ValueError(msg)

        nr = get_set_num_ruptures(src)
        if nr == 0:  # the minimum_magnitude filters all ruptures
            return
        self.tot_ruptures += nr
        self.sources.append(src)
        _, max_mag = src.get_min_max_mag()
        prev_max_mag = self.max_mag
        if prev_max_mag is None or max_mag > prev_max_mag:
            self.max_mag = max_mag

    def __repr__(self):
        return '<%s #%d %s, %d source(s), %d effective rupture(s)>' % (
            self.__class__.__name__, self.id, self.trt,
            len(self.sources), self.eff_ruptures)

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
            id=self.id,
            trt=self.trt,
            name=self.name or '',
            eff_ruptures=self.eff_ruptures,
            src_interdep=self.src_interdep,
            rup_interdep=self.rup_interdep,
            grp_probability=self.grp_probability or '')
        return numpy.array(lst, source_dt), attrs

    def __fromh5__(self, array, attrs):
        vars(self).update(attrs)
        self.sources = []
        for row in array:
            self.sources.append(pickle.loads(memoryview(row['pik'])))


def get_set_num_ruptures(src):
    """
    Extract the number of ruptures and set it
    """
    if not src.num_ruptures:
        t0 = time.time()
        src.num_ruptures = src.count_ruptures()
        dt = time.time() - t0
        clsname = src.__class__.__name__
        if dt > 10:
            if 'Area' in clsname:
                logging.warning(
                    '%s.count_ruptures took %d seconds, perhaps the '
                    'area discretization is too small', src, dt)
            elif 'ComplexFault' in clsname:
                logging.warning(
                    '%s.count_ruptures took %d seconds, perhaps the '
                    'complex_fault_mesh_spacing is too small', src, dt)
            elif 'SimpleFault' in clsname:
                logging.warning(
                    '%s.count_ruptures took %d seconds, perhaps the '
                    'rupture_mesh_spacing is too small', src, dt)
            else:
                # multiPointSource
                logging.warning('count_ruptures %s took %d seconds', src, dt)
    return src.num_ruptures


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
        convert = getattr(self, 'convert_' + striptag(node.tag))
        return convert(node)

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

    def convert_surfaces(self, surface_nodes):
        """
        Utility to convert a list of surface nodes into a single hazardlib
        surface. There are four possibilities:

        1. there is a single simpleFaultGeometry node; returns a
           :class:`openquake.hazardlib.geo.simpleFaultSurface` instance
        2. there is a single complexFaultGeometry node; returns a
           :class:`openquake.hazardlib.geo.complexFaultSurface` instance
        3. there is a single griddedSurface node; returns a
           :class:`openquake.hazardlib.geo.GriddedSurface` instance
        4. there is a list of PlanarSurface nodes; returns a
           :class:`openquake.hazardlib.geo.MultiSurface` instance

        :param surface_nodes: surface nodes as just described
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
        else:  # a collection of planar surfaces
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
            surfaces = [node.complexFaultGeometry]
        rupt = source.rupture.BaseRupture(
            mag=mag, rake=rake, tectonic_region_type=None,
            hypocenter=hypocenter,
            surface=self.convert_surfaces(surfaces))
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

    def convert_multiPlanesRupture(self, node):
        """
        Convert a multiPlanesRupture node.

        :param node: the rupture node
        """
        mag, rake, hypocenter = self.get_mag_rake_hypo(node)
        with context(self.fname, node):
            surfaces = list(node.getnodes('planarSurface'))
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
        :returns: a dictionary grp_id -> EBRuptures
        """
        coll = {}
        for grpnode in node:
            grp_id = int(grpnode['id'])
            coll[grp_id] = ebrs = []
            for node in grpnode:
                rup = self.convert_node(node)
                rup.serial = int(node['id'])
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
    def __init__(self, investigation_time=50., rupture_mesh_spacing=10.,
                 complex_fault_mesh_spacing=None, width_of_mfd_bin=1.0,
                 area_source_discretization=None,
                 minimum_magnitude={'default': 0},
                 spinning_floating=True, source_id=None):
        self.investigation_time = investigation_time
        self.area_source_discretization = area_source_discretization
        self.minimum_magnitude = minimum_magnitude
        self.rupture_mesh_spacing = rupture_mesh_spacing
        self.complex_fault_mesh_spacing = (
            complex_fault_mesh_spacing or rupture_mesh_spacing)
        self.width_of_mfd_bin = width_of_mfd_bin
        self.spinning_floating = spinning_floating
        self.source_id = source_id

    def get_tom(self, node):
        """
        Convert the given node into a Temporal Occurrence Model object.

        :param node: a node of kind poissonTOM or brownianTOM
        :returns: a :class:`openquake.hazardlib.mfd.EvenlyDiscretizedMFD.` or
                  :class:`openquake.hazardlib.mfd.TruncatedGRMFD` instance
        """
        if 'tom' in node.attrib:
            tom_cls = tom.registry[node['tom']]
        else:
            tom_cls = tom.registry['PoissonTOM']
        return tom_cls(time_span=self.investigation_time,
                       occurrence_rate=node.get('occurrence_rate'))

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
                          if subnode.tag.endswith(
                              ('incrementalMFD', 'truncGutenbergRichterMFD',
                               'arbitraryMFD', 'YoungsCoppersmithMFD',
                               'multiMFD'))]
            if mfd_node.tag.endswith('incrementalMFD'):
                return mfd.EvenlyDiscretizedMFD(
                    min_mag=mfd_node['minMag'], bin_width=mfd_node['binWidth'],
                    occurrence_rates=~mfd_node.occurRates)
            elif mfd_node.tag.endswith('truncGutenbergRichterMFD'):
                return mfd.TruncatedGRMFD(
                    a_val=mfd_node['aValue'], b_val=mfd_node['bValue'],
                    min_mag=mfd_node['minMag'], max_mag=mfd_node['maxMag'],
                    bin_width=self.width_of_mfd_bin)
            elif mfd_node.tag.endswith('arbitraryMFD'):
                return mfd.ArbitraryMFD(
                    magnitudes=~mfd_node.magnitudes,
                    occurrence_rates=~mfd_node.occurRates)
            elif mfd_node.tag.endswith('YoungsCoppersmithMFD'):
                if "totalMomentRate" in mfd_node.attrib.keys():
                    # Return Youngs & Coppersmith from the total moment rate
                    return mfd.YoungsCoppersmith1985MFD.from_total_moment_rate(
                        min_mag=mfd_node["minMag"], b_val=mfd_node["bValue"],
                        char_mag=mfd_node["characteristicMag"],
                        total_moment_rate=mfd_node["totalMomentRate"],
                        bin_width=mfd_node["binWidth"])
                elif "characteristicRate" in mfd_node.attrib.keys():
                    # Return Youngs & Coppersmith from the total moment rate
                    return mfd.YoungsCoppersmith1985MFD.\
                        from_characteristic_rate(
                            min_mag=mfd_node["minMag"],
                            b_val=mfd_node["bValue"],
                            char_mag=mfd_node["characteristicMag"],
                            char_rate=mfd_node["characteristicRate"],
                            bin_width=mfd_node["binWidth"])
            elif mfd_node.tag.endswith('multiMFD'):
                return mfd.multi_mfd.MultiMFD.from_node(
                    mfd_node, self.width_of_mfd_bin)

    def convert_npdist(self, node):
        """
        Convert the given node into a Nodal Plane Distribution.

        :param node: a nodalPlaneDist node
        :returns: a :class:`openquake.hazardlib.geo.NodalPlane` instance
        """
        with context(self.fname, node):
            npdist = []
            for np in node.nodalPlaneDist:
                prob, strike, dip, rake = (
                    np['probability'], np['strike'], np['dip'], np['rake'])
                npdist.append((prob, geo.NodalPlane(strike, dip, rake)))
            if not self.spinning_floating:
                npdist = [(1, npdist[0][1])]  # consider the first nodal plane
            return pmf.PMF(npdist)

    def convert_hpdist(self, node):
        """
        Convert the given node into a probability mass function for the
        hypo depth distribution.

        :param node: a hypoDepthDist node
        :returns: a :class:`openquake.hazardlib.pmf.PMF` instance
        """
        with context(self.fname, node):
            hcdist = [(hd['probability'], hd['depth'])
                      for hd in node.hypoDepthDist]
            if not self.spinning_floating:  # consider the first hypocenter
                hcdist = [(1, hcdist[0][1])]
            return pmf.PMF(hcdist)

    def convert_areaSource(self, node):
        """
        Convert the given node into an area source object.

        :param node: a node with tag areaGeometry
        :returns: a :class:`openquake.hazardlib.source.AreaSource` instance
        """
        geom = node.areaGeometry
        coords = split_coords_2d(~geom.Polygon.exterior.LinearRing.posList)
        polygon = geo.Polygon([geo.Point(*xy) for xy in coords])
        msr = valid.SCALEREL[~node.magScaleRel]()
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
            hypocenter_distribution=self.convert_hpdist(node),
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
        msr = valid.SCALEREL[~node.magScaleRel]()
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
            hypocenter_distribution=self.convert_hpdist(node),
            temporal_occurrence_model=self.get_tom(node))

    def convert_multiPointSource(self, node):
        """
        Convert the given node into a MultiPointSource object.

        :param node: a node with tag multiPointGeometry
        :returns: a :class:`openquake.hazardlib.source.MultiPointSource`
        """
        geom = node.multiPointGeometry
        lons, lats = zip(*split_coords_2d(~geom.posList))
        msr = valid.SCALEREL[~node.magScaleRel]()
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
            hypocenter_distribution=self.convert_hpdist(node),
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
        msr = valid.SCALEREL[~node.magScaleRel]()
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
                source_id=node['id'],
                name=node['name'],
                tectonic_region_type=node.attrib.get('tectonicRegion'),
                mfd=mfd,
                rupture_mesh_spacing=self.rupture_mesh_spacing,
                magnitude_scaling_relationship=msr,
                rupture_aspect_ratio=~node.ruptAspectRatio,
                upper_seismogenic_depth=~geom.upperSeismoDepth,
                lower_seismogenic_depth=~geom.lowerSeismoDepth,
                fault_trace=fault_trace,
                dip=~geom.dip,
                rake=~node.rake,
                temporal_occurrence_model=self.get_tom(node),
                hypo_list=hypo_list,
                slip_list=slip_list)
        return simple

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
        msr = valid.SCALEREL[~node.magScaleRel]()
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
            a node with tag areaGeometry
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
        trt = node.attrib.get('tectonicRegion')
        rup_pmf_data = []
        rups_weights = None
        if 'rup_weights' in node.attrib:
            tmp = node.attrib.get('rup_weights')
            rups_weights = numpy.array([float(s) for s in tmp.split()])
        for i, rupnode in enumerate(node):
            probs = pmf.PMF(valid.pmf(rupnode['probs_occur']))
            rup = RuptureConverter.convert_node(self, rupnode)
            rup.tectonic_region_type = trt
            rup.weight = None if rups_weights is None else rups_weights[i]
            rup_pmf_data.append((rup, probs))
        nps = source.NonParametricSeismicSource(
            node['id'], node['name'], trt, rup_pmf_data)
        nps.splittable = 'rup_weights' not in node.attrib
        return nps

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
        sg = SourceGroup(trt, min_mag=self.minimum_magnitude)
        sg.temporal_occurrence_model = self.get_tom(node)
        sg.name = node.attrib.get('name')
        # Set attributes related to occurrence
        sg.src_interdep = node.attrib.get('src_interdep', 'indep')
        sg.rup_interdep = node.attrib.get('rup_interdep', 'indep')
        sg.grp_probability = node.attrib.get('grp_probability')
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
                assert hasattr(sg, 'occurrence_rate')
        #
        for src_node in node:
            if self.source_id and self.source_id != src_node['id']:
                continue  # filter by source_id
            src = self.convert_node(src_node)
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
        if srcs_weights is not None:
            if len(node) and len(srcs_weights) != len(node):
                raise ValueError(
                    'There are %d srcs_weights but %d source(s) in %s'
                    % (len(srcs_weights), len(node), self.fname))
            for src, sw in zip(sg, srcs_weights):
                src.mutex_weight = sw
        # check that, when the cluster option is set, the group has a temporal
        # occurrence model properly defined
        if sg.cluster and not hasattr(sg, 'temporal_occurrence_model'):
            msg = 'The Source Group is a cluster but does not have a '
            msg += 'temporal occurrence model'
            raise ValueError(msg)
        return sg

# ################### MultiPointSource conversion ######################## #


def dists(node):
    """
    :returns: hpdist, npdist and magScaleRel from the given pointSource node
    """
    hd = tuple((node['probability'], node['depth'])
               for node in node.hypoDepthDist)
    npd = tuple(
        ((node['probability'], node['rake'], node['strike'], node['dip']))
        for node in node.nodalPlaneDist)
    return hd, npd, ~node.magScaleRel


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
    # converts pointSources with the same hpdist, npdist and msr into a
    # single multiPointSource.
    allsources = []
    for (hd, npd, msr), sources in groupby(srcs, dists).items():
        if len(sources) == 1:  # there is a single source
            allsources.extend(sources)
            continue
        mfds = [src[3] for src in sources]
        points = []
        usd = []
        lsd = []
        rar = []
        for src in sources:
            pg = src.pointGeometry
            points.extend(~pg.Point.pos)
            usd.append(~pg.upperSeismoDepth)
            lsd.append(~pg.lowerSeismoDepth)
            rar.append(~src.ruptAspectRatio)
        geom = Node('multiPointGeometry')
        geom.append(Node('gml:posList', text=points))
        geom.append(Node('upperSeismoDepth', text=collapse(usd)))
        geom.append(Node('lowerSeismoDepth', text=collapse(lsd)))
        node = Node(
            'multiPointSource',
            dict(id='mps-%d' % i, name='multiPointSource-%d' % i),
            nodes=[geom])
        node.append(Node("magScaleRel", text=collapse(msr)))
        node.append(Node("ruptAspectRatio", text=collapse(rar)))
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


def update_source_model(sm_node, fname):
    """
    :param sm_node: a sourceModel Node object containing sourceGroups
    """
    i = 0
    for group in sm_node:
        if 'srcs_weights' in group.attrib:
            raise InvalidFile('srcs_weights must be removed in %s' % fname)
        if not group.tag.endswith('sourceGroup'):
            raise InvalidFile('wrong NRML, got %s instead of '
                              'sourceGroup in %s' % (group.tag, fname))
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


def to_python(fname, converter):
    """
    Convert a source model .hdf5 file into a :class:`SourceModel` object
    """
    with hdf5.File(fname, 'r') as f:
        source_model = f['/']
    for sg in source_model:
        for src in sg:
            if hasattr(src, 'mfd'):
                # multipoint source
                # src.tom = converter.tom
                kwargs = getattr(src.mfd, 'kwargs', {})
                if 'bin_width' not in kwargs:
                    kwargs['bin_width'] = [converter.width_of_mfd_bin]
    return source_model
