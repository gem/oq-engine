# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2016 GEM Foundation
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
import math
import copy
import operator
import collections

from openquake.baselib.general import block_splitter
from openquake.baselib.performance import Monitor
from openquake.hazardlib import geo, mfd, pmf, source
from openquake.hazardlib.tom import PoissonTOM
from openquake.risklib import valid
from openquake.commonlib.node import context, striptag
from openquake.commonlib import parallel

# the following is arbitrary, it is used to decide when to parallelize
# the filtering (MS)
LOTS_OF_SOURCES_SITES = 1E5  # arbitrary, set by Michele Simionato
MAGNITUDE_FOR_RUPTURE_SPLITTING = 6.5  # given by Marco Pagani
# NB: the parameter MAGNITUDE_FOR_RUPTURE_SPLITTING cannot go in a
# configuration file, otherwise the tests will break by changing it;
# reason: the numbers in the event based calculators depend on the
# splitting: different sources => different seeds => different numbers
POINT_SOURCE_WEIGHT = 1 / 40.


class SourceGroup(collections.Sequence):
    """
    A container for the following parameters:

    :param str trt:
        the tectonic region type all the sources belong to
    :param list sources:
        a list of hazardlib source objects
    :param min_mag:
        the minimum magnitude among the given sources
    :param max_mag:
        the maximum magnitude among the given sources
    :param id:
        an optional numeric ID (default None) useful to associate
        the model to a database object
    :param eff_ruptures:
        the number of ruptures contained in the group; if -1,
        the number is unknown and has to be computed by using
        get_set_num_ruptures
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

    def __init__(self, trt, sources=None,
                 min_mag=None, max_mag=None, id=0, eff_ruptures=-1):
        self.trt = trt
        self.sources = []
        self.min_mag = min_mag
        self.max_mag = max_mag
        self.id = id
        if sources:
            for src in sorted(sources, key=operator.attrgetter('source_id')):
                self.update(src)
        self.source_model = None  # to be set later, in CompositionInfo
        self.weight = 1
        self.eff_ruptures = eff_ruptures  # set later nby get_rlzs_assoc

    def tot_ruptures(self):
        return sum(src.num_ruptures for src in self.sources)

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
        self.sources.append(src)
        min_mag, max_mag = src.get_min_max_mag()
        prev_min_mag = self.min_mag
        if prev_min_mag is None or min_mag < prev_min_mag:
            self.min_mag = min_mag
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


def get_set_num_ruptures(src):
    """
    Extract the number of ruptures and set it
    """
    if not src.num_ruptures:
        src.num_ruptures = src.count_ruptures()
    return src.num_ruptures


def area_to_point_sources(area_src):
    """
    Split an area source into a generator of point sources.

    MFDs will be rescaled appropriately for the number of points in the area
    mesh.

    :param area_src:
        :class:`openquake.hazardlib.source.AreaSource`
    """
    mesh = area_src.polygon.discretize(area_src.area_discretization)
    num_points = len(mesh)
    area_mfd = area_src.mfd

    if isinstance(area_mfd, mfd.TruncatedGRMFD):
        new_a_val = math.log10(10 ** area_mfd.a_val / float(num_points))
        new_mfd = mfd.TruncatedGRMFD(
            a_val=new_a_val,
            b_val=area_mfd.b_val,
            bin_width=area_mfd.bin_width,
            min_mag=area_mfd.min_mag,
            max_mag=area_mfd.max_mag)
    elif isinstance(area_mfd, mfd.EvenlyDiscretizedMFD):
        new_occur_rates = [float(x) / num_points
                           for x in area_mfd.occurrence_rates]
        new_mfd = mfd.EvenlyDiscretizedMFD(
            min_mag=area_mfd.min_mag,
            bin_width=area_mfd.bin_width,
            occurrence_rates=new_occur_rates)
    elif isinstance(area_mfd, mfd.ArbitraryMFD):
        new_occur_rates = [float(x) / num_points
                           for x in area_mfd.occurrence_rates]
        new_mfd = mfd.ArbitraryMFD(
            magnitudes=area_mfd.magnitudes,
            occurrence_rates=new_occur_rates)

    for i, (lon, lat) in enumerate(zip(mesh.lons, mesh.lats)):
        pt = source.PointSource(
            # Generate a new ID and name
            source_id='%s-%s' % (area_src.source_id, i),
            name='%s-%s' % (area_src.name, i),
            tectonic_region_type=area_src.tectonic_region_type,
            mfd=new_mfd,
            rupture_mesh_spacing=area_src.rupture_mesh_spacing,
            magnitude_scaling_relationship=
            area_src.magnitude_scaling_relationship,
            rupture_aspect_ratio=area_src.rupture_aspect_ratio,
            upper_seismogenic_depth=area_src.upper_seismogenic_depth,
            lower_seismogenic_depth=area_src.lower_seismogenic_depth,
            location=geo.Point(lon, lat),
            nodal_plane_distribution=area_src.nodal_plane_distribution,
            hypocenter_distribution=area_src.hypocenter_distribution,
            temporal_occurrence_model=area_src.temporal_occurrence_model)
        pt.src_group_id = area_src.src_group_id
        pt.num_ruptures = pt.count_ruptures()
        yield pt


def split_fault_source_by_magnitude(src):
    """
    Utility splitting a fault source into fault sources with a single
    magnitude bin.

    :param src:
        an instance of :class:`openquake.hazardlib.source.base.SeismicSource`
    """
    splitlist = []
    i = 0
    for mag, rate in src.mfd.get_annual_occurrence_rates():
        if not rate:  # ignore zero occurency rate
            continue
        new_src = copy.copy(src)
        new_src.source_id = '%s-%s' % (src.source_id, i)
        new_src.mfd = mfd.EvenlyDiscretizedMFD(
            min_mag=mag, bin_width=src.mfd.bin_width,
            occurrence_rates=[rate])
        i += 1
        splitlist.append(new_src)
    return splitlist


def split_fault_source(src, block_size):
    """
    Generator splitting a fault source into several fault sources.

    :param src:
        an instance of :class:`openquake.hazardlib.source.base.SeismicSource`
    """
    # NB: the splitting is tricky; if you don't split, you will not
    # take advantage of the multiple cores; if you split too much,
    # the data transfer will kill you, i.e. multiprocessing/celery
    # will fail to transmit to the workers the generated sources.
    for s in split_fault_source_by_magnitude(src):
        if s.mfd.min_mag < MAGNITUDE_FOR_RUPTURE_SPLITTING:
            s.num_ruptures = s.count_ruptures()
            yield s  # don't split, there would too many ruptures
        else:  # split in MultiRuptureSources
            for ss in MultiRuptureSource.split(s, block_size):
                yield ss


class MultiRuptureSource(object):
    """
    Fake source class used to encapsule a set of ruptures.

    :param rupture:
        an instance of :class:`openquake.hazardlib.source.rupture.
        ParametricProbabilisticRupture`
    :param source_id:
        an ID for the MultiRuptureSource
    :param tectonic_region_type:
        the tectonic region type
    :param src_group_id:
        ID of the tectonic region model the source belongs to
    """
    @classmethod
    def split(cls, src, block_size):
        """
        Split the given fault source into MultiRuptureSources depending
        on the given block size.
        """
        for i, ruptures in enumerate(
                block_splitter(src.iter_ruptures(), block_size)):
            yield cls(ruptures, '%s-%s' % (src.source_id, i),
                      src.tectonic_region_type, src.src_group_id)

    def __init__(self, ruptures, source_id, tectonic_region_type,
                 src_group_id):
        self.ruptures = ruptures
        self.source_id = source_id
        self.tectonic_region_type = tectonic_region_type
        self.src_group_id = src_group_id
        self.weight = self.num_ruptures = len(ruptures)

    def iter_ruptures(self):
        """Yield the ruptures"""
        for rupture in self.ruptures:
            yield rupture

    def count_ruptures(self):
        """Return the block size"""
        return len(self.ruptures)

    def filter_sites_by_distance_to_source(self, maxdist, sitecol):
        """The source has been already filtered, return the sitecol"""
        return sitecol


def split_source(src, block_size=1):
    """
    Split an area source into point sources and a fault sources into
    smaller fault sources.

    :param src:
        an instance of :class:`openquake.hazardlib.source.base.SeismicSource`
    """
    if isinstance(src, source.AreaSource):
        for s in area_to_point_sources(src):
            s.id = src.id
            yield s
    elif isinstance(
            src, (source.SimpleFaultSource, source.ComplexFaultSource)):
        for s in split_fault_source(src, block_size):
            s.id = src.id
            yield s
    else:
        # characteristic and nonparametric sources are not split
        # since they are small anyway
        yield src


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

    def convert_node(self, node):
        """
        Convert the given rupture node into a hazardlib rupture, depending
        on the node tag.

        :param node: a node representing a rupture
        """
        with context(self.fname, node):
            convert_rupture = getattr(self, 'convert_' + striptag(node.tag))
            mag = ~node.magnitude
            rake = ~node.rake
            h = node.hypocenter
            hypocenter = geo.Point(h['lon'], h['lat'], h['depth'])
        return convert_rupture(node, mag, rake, hypocenter)

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
            self.rupture_mesh_spacing,
            top_left, top_right, bottom_right, bottom_left)

    def convert_surfaces(self, surface_nodes):
        """
        Utility to convert a list of surface nodes into a single hazardlib
        surface. There are three possibilities:

        1. there is a single simpleFaultGeometry node; returns a
           :class:`openquake.hazardlib.geo.simpleFaultSurface` instance
        2. there is a single complexFaultGeometry node; returns a
           :class:`openquake.hazardlib.geo.complexFaultSurface` instance
        3. there is a list of PlanarSurface nodes; returns a
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
        else:  # a collection of planar surfaces
            planar_surfaces = list(map(self.geo_planar, surface_nodes))
            surface = geo.MultiSurface(planar_surfaces)
        return surface

    def convert_simpleFaultRupture(self, node, mag, rake, hypocenter):
        """
        Convert a simpleFaultRupture node.

        :param node: the rupture node
        :param mag: the rupture magnitude
        :param rake: the rupture rake angle
        :param hypocenter: the rupture hypocenter
        """
        with context(self.fname, node):
            surfaces = [node.simpleFaultGeometry]
        rupt = source.rupture.Rupture(
            mag=mag, rake=rake, tectonic_region_type=None,
            hypocenter=hypocenter,
            surface=self.convert_surfaces(surfaces),
            source_typology=source.SimpleFaultSource,
            surface_nodes=surfaces)
        return rupt

    def convert_complexFaultRupture(self, node, mag, rake, hypocenter):
        """
        Convert a complexFaultRupture node.

        :param node: the rupture node
        :param mag: the rupture magnitude
        :param rake: the rupture rake angle
        :param hypocenter: the rupture hypocenter
        """
        with context(self.fname, node):
            surfaces = [node.complexFaultGeometry]
        rupt = source.rupture.Rupture(
            mag=mag, rake=rake, tectonic_region_type=None,
            hypocenter=hypocenter,
            surface=self.convert_surfaces(surfaces),
            source_typology=source.ComplexFaultSource,
            surface_nodes=surfaces)
        return rupt

    def convert_singlePlaneRupture(self, node, mag, rake, hypocenter):
        """
        Convert a singlePlaneRupture node.

        :param node: the rupture node
        :param mag: the rupture magnitude
        :param rake: the rupture rake angle
        :param hypocenter: the rupture hypocenter
        """
        with context(self.fname, node):
            surfaces = [node.planarSurface]
        rupt = source.rupture.Rupture(
            mag=mag, rake=rake,
            tectonic_region_type=None,
            hypocenter=hypocenter,
            surface=self.convert_surfaces(surfaces),
            source_typology=source.NonParametricSeismicSource,
            surface_nodes=surfaces)
        return rupt

    def convert_multiPlanesRupture(self, node, mag, rake, hypocenter):
        """
        Convert a multiPlanesRupture node.

        :param node: the rupture node
        :param mag: the rupture magnitude
        :param rake: the rupture rake angle
        :param hypocenter: the rupture hypocenter
        """
        with context(self.fname, node):
            surfaces = list(node.getnodes('planarSurface'))
        rupt = source.rupture.Rupture(
            mag=mag, rake=rake,
            tectonic_region_type=None,
            hypocenter=hypocenter,
            surface=self.convert_surfaces(surfaces),
            source_typology=source.NonParametricSeismicSource,
            surface_nodes=surfaces)
        return rupt


class SourceConverter(RuptureConverter):
    """
    Convert sources from valid nodes into Hazardlib objects.
    """
    def __init__(self, investigation_time, rupture_mesh_spacing,
                 complex_fault_mesh_spacing=None, width_of_mfd_bin=1.0,
                 area_source_discretization=None):
        self.area_source_discretization = area_source_discretization
        self.rupture_mesh_spacing = rupture_mesh_spacing
        self.complex_fault_mesh_spacing = (
            complex_fault_mesh_spacing or rupture_mesh_spacing)
        self.width_of_mfd_bin = width_of_mfd_bin
        self.tom = PoissonTOM(investigation_time)

    def convert_node(self, node):
        """
        Convert the given node into a hazardlib source, depending
        on the node tag.

        :param node: a node representing a source
        """
        with context(self.fname, node):
            convert_source = getattr(self, 'convert_' + striptag(node.tag))
        return convert_source(node)

    def convert_mfdist(self, node):
        """
        Convert the given node into a Magnitude-Frequency Distribution
        object.

        :param node: a node of kind incrementalMFD or truncGutenbergRichterMFD
        :returns: a :class:`openquake.hazardlib.mdf.EvenlyDiscretizedMFD.` or
                  :class:`openquake.hazardlib.mdf.TruncatedGRMFD` instance
        """
        with context(self.fname, node):
            [mfd_node] = [subnode for subnode in node
                          if subnode.tag.endswith(
                              ('incrementalMFD', 'truncGutenbergRichterMFD',
                               'arbitraryMFD', 'YoungsCoppersmithMFD'))]
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
            return pmf.PMF(npdist)

    def convert_hpdist(self, node):
        """
        Convert the given node into a probability mass function for the
        hypo depth distribution.

        :param node: a hypoDepthDist node
        :returns: a :class:`openquake.hazardlib.pmf.PMF` instance
        """
        with context(self.fname, node):
            return pmf.PMF([(hd['probability'], hd['depth'])
                            for hd in node.hypoDepthDist])

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
            temporal_occurrence_model=self.tom)

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
            temporal_occurrence_model=self.tom)

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
            except NameError:
                hypo_list = ()
            try:
                slip_list = valid.slip_list(node.slipList)
            except NameError:
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
                temporal_occurrence_model=self.tom,
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
                temporal_occurrence_model=self.tom)
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
            temporal_occurrence_model=self.tom,
            surface_node=node.surface)
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
        for rupnode in node:
            probs = pmf.PMF(rupnode['probs_occur'])
            rup = RuptureConverter.convert_node(self, rupnode)
            rup.tectonic_region_type = trt
            rup_pmf_data.append((rup, probs))
        nps = source.NonParametricSeismicSource(
            node['id'], node['name'], trt, rup_pmf_data)
        return nps

    def convert_sourceGroup(self, node):
        """
        Convert the given node into a SourceGroup object.

        :param node:
            a node with tag sourceGroup
        :returns:
            a :class:`openquake.commonlib.source.SourceGroup`
            instance
        """
        trt = node['tectonicRegion']
        srcs_weights = node.attrib.get('srcs_weights')
        grp_attrs = {k: v for k, v in node.attrib.items()
                     if k not in ('name', 'src_interdep', 'srcs_weights')}
        srcs = []
        for n, src_node in enumerate(node):
            src = self.convert_node(src_node)
            # transmit the group attributes to the underlying source
            for attr, value in grp_attrs.items():
                if attr == 'tectonicRegion':
                    src.tectonic_region_type = value
                else:  # transmit as it is
                    setattr(src, attr, node[attr])
            srcs.append(src)
        sg = SourceGroup(trt, srcs)
        if srcs_weights is not None:
            assert len(srcs_weights) == n, 'Expected %d sources, got %d' % (
                len(srcs_weights), n)
        sg.name = node.attrib.get('name')
        sg.src_interdep = node.attrib.get('src_interdep')
        sg.srcs_weights = srcs_weights
        return sg


def parse_ses_ruptures(fname):
    """
    Convert a stochasticEventSetCollection file into a set of SES,
    each one containing ruptures with an etag and a seed.
    """
    raise NotImplementedError('parse_ses_ruptures')


@parallel.litetask
def _filter_sources(sources, sitecol, maxdist, monitor):
    # called by filter_sources
    srcs = []
    for src in sources:
        sites = src.filter_sites_by_distance_to_source(maxdist, sitecol)
        if sites is not None:
            srcs.append(src)
    return srcs


def filter_sources(sources, sitecol, maxdist):
    """
    Filter a list of hazardlib sources according to the maximum distance.

    :param sources: the original sources
    :param sitecol: a SiteCollection instance
    :param maxdist: maximum distance
    :returns: the filtered sources ordered by source_id
    """
    mon = Monitor('filter sources')
    if len(sources) * len(sitecol) > LOTS_OF_SOURCES_SITES:
        # filter in parallel on all available cores
        sources = parallel.TaskManager.apply_reduce(
            _filter_sources, (sources, sitecol, maxdist, mon),
            operator.add, [])
    else:
        # few sources and sites, filter sequentially on a single core
        sources = _filter_sources.task_func(sources, sitecol, maxdist, mon)
    return sorted(sources, key=operator.attrgetter('source_id'))
