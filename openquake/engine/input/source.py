# Copyright (c) 2010-2013, GEM Foundation.
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

import sys
import math
import copy

from itertools import izip

from openquake.hazardlib import geo
from openquake.hazardlib import mfd
from openquake.hazardlib import pmf
from openquake.hazardlib import scalerel
from openquake.hazardlib import source
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.rupture import Rupture as HazardlibRupture
from openquake.nrmllib import models as nrml_models
from openquake.nrmllib.hazard import parsers as haz_parsers
from shapely import wkt

MAX_RUPTURES = 500  # if there are more ruptures, split the source


## NB: this is a job for generic functions
class NrmlHazardlibConverter(object):
    """
    Converter from NRML objects to hazardlib objects
    """
    def __init__(self, hc):
        """
        :param hc:
            a HazardCalculation instance or in general any object with
            attributes investigation_time, rupture_mesh_spacing,
            area_source_discretization, width_of_mfd_bin
        """
        self.hc = hc
        self.default_tom = PoissonTOM(hc.investigation_time) \
            if hc.investigation_time else None  # None for scenario calculator

    def __call__(self, src):
        """
        Convert a seismic source or rupture object from the NRML representation
        to the HazardLib representation. Inputs can be point, area,
        simple fault, or complex fault sources, or simple or complex fault
        ruptures.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :mod:`openquake.nrmllib.models` seismic source or rupture instance.

        :returns:
            The HazardLib representation of the input source or rupture.
        """
        if isinstance(src, (nrml_models.AreaSource, nrml_models.PointSource,
                            nrml_models.ComplexFaultSource,
                            nrml_models.SimpleFaultSource,
                            nrml_models.CharacteristicSource)):
            return self._nrml_source_to_hazardlib(src)
        elif isinstance(src, (nrml_models.ComplexFaultRuptureModel,
                              nrml_models.SimpleFaultRuptureModel)):
            return self._nrml_rupture_to_hazardlib(src)

    def _nrml_source_to_hazardlib(self, src):
        """
        Convert a NRML source object into the HazardLib representation.
        """
        # The ordering of the switch here matters because:
        #   - AreaSource inherits from PointSource
        #   - ComplexFaultSource inherits from SimpleFaultSource
        try:
            if isinstance(src, nrml_models.AreaSource):
                return self._area_to_hazardlib(src)
            elif isinstance(src, nrml_models.PointSource):
                return self._point_to_hazardlib(src)
            elif isinstance(src, nrml_models.ComplexFaultSource):
                return self._complex_to_hazardlib(src)
            elif isinstance(src, nrml_models.SimpleFaultSource):
                return self._simple_to_hazardlib(src)
            elif isinstance(src, nrml_models.CharacteristicSource):
                return self._characteristic_to_hazardlib(src)
        except:
            etype, err, tb = sys.exc_info()
            msg = ("The following error has occurred with "
                   "source id='%s', name='%s': %s" %
                   (src.id, src.name, err.message))
            raise etype, msg, tb

    def _nrml_rupture_to_hazardlib(self, src):
        """
        Convert a NRML rupture object into the HazardLib representation.

        Parameters and return values are similar to :func:`nrml_to_hazardlib`.
        """
        if isinstance(src, nrml_models.ComplexFaultRuptureModel):
            return self._complex_rupture_to_hazardlib(src)
        elif isinstance(src, nrml_models.SimpleFaultRuptureModel):
            return self._simple_rupture_to_hazardlib(src)

    def _point_to_hazardlib(self, src):
        """Convert a NRML point source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.PointSource` instance.
        :returns:
            The HazardLib representation of the input source.
        """
        shapely_pt = wkt.loads(src.geometry.wkt)

        mf_dist = self._mfd_to_hazardlib(src.mfd)

        # nodal plane distribution:
        npd = pmf.PMF(
            [(x.probability,
              geo.NodalPlane(strike=x.strike, dip=x.dip, rake=x.rake))
             for x in src.nodal_plane_dist]
        )

        # hypocentral depth distribution:
        hd = pmf.PMF([(x.probability, x.depth) for x in src.hypo_depth_dist])

        msr = scalerel.get_available_magnitude_scalerel()[src.mag_scale_rel]()

        point = source.PointSource(
            source_id=src.id,
            name=src.name,
            tectonic_region_type=src.trt,
            mfd=mf_dist,
            rupture_mesh_spacing=self.hc.rupture_mesh_spacing,
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=src.rupt_aspect_ratio,
            upper_seismogenic_depth=src.geometry.upper_seismo_depth,
            lower_seismogenic_depth=src.geometry.lower_seismo_depth,
            location=geo.Point(shapely_pt.x, shapely_pt.y),
            nodal_plane_distribution=npd,
            hypocenter_distribution=hd,
            temporal_occurrence_model=self.default_tom,
        )

        return point

    def _area_to_hazardlib(self, src):
        """Convert a NRML area source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.PointSource` instance.
        :returns:
            The HazardLib representation of the input source.
        """
        shapely_polygon = wkt.loads(src.geometry.wkt)
        hazardlib_polygon = geo.Polygon(
            # We ignore the last coordinate in the sequence here, since it is a
            # duplicate of the first. hazardlib will close the loop for us.
            [geo.Point(*x) for x in list(shapely_polygon.exterior.coords)[:-1]]
        )

        mf_dist = self._mfd_to_hazardlib(src.mfd)

        # nodal plane distribution:
        npd = pmf.PMF(
            [(x.probability,
              geo.NodalPlane(strike=x.strike, dip=x.dip, rake=x.rake))
             for x in src.nodal_plane_dist]
        )

        # hypocentral depth distribution:
        hd = pmf.PMF([(x.probability, x.depth) for x in src.hypo_depth_dist])

        msr = scalerel.get_available_magnitude_scalerel()[src.mag_scale_rel]()
        area = source.AreaSource(
            source_id=src.id,
            name=src.name,
            tectonic_region_type=src.trt,
            mfd=mf_dist,
            rupture_mesh_spacing=self.hc.rupture_mesh_spacing,
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=src.rupt_aspect_ratio,
            upper_seismogenic_depth=src.geometry.upper_seismo_depth,
            lower_seismogenic_depth=src.geometry.lower_seismo_depth,
            nodal_plane_distribution=npd, hypocenter_distribution=hd,
            polygon=hazardlib_polygon,
            area_discretization=self.hc.area_source_discretization,
            temporal_occurrence_model=self.default_tom,
        )

        return area

    def _simple_to_hazardlib(self, src):
        """Convert a NRML simple fault source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.SimpleFaultRuptureModel` instance.
        :returns:
            The HazardLib representation of the input source.
        """
        shapely_line = wkt.loads(src.geometry.wkt)
        fault_trace = geo.Line([geo.Point(*x) for x in shapely_line.coords])

        mf_dist = self._mfd_to_hazardlib(src.mfd)
        msr = scalerel.get_available_magnitude_scalerel()[src.mag_scale_rel]()

        simple = source.SimpleFaultSource(
            source_id=src.id,
            name=src.name,
            tectonic_region_type=src.trt,
            mfd=mf_dist,
            rupture_mesh_spacing=self.hc.rupture_mesh_spacing,
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=src.rupt_aspect_ratio,
            upper_seismogenic_depth=src.geometry.upper_seismo_depth,
            lower_seismogenic_depth=src.geometry.lower_seismo_depth,
            fault_trace=fault_trace,
            dip=src.geometry.dip,
            rake=src.rake,
            temporal_occurrence_model=self.default_tom,
        )

        return simple

    def _complex_to_hazardlib(self, src):
        """Convert a NRML complex fault source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.ComplexFaultRuptureModel` instance
        :returns:
            The HazardLib representation of the input source.
        """
        edges_wkt = []
        edges_wkt.append(src.geometry.top_edge_wkt)
        edges_wkt.extend(src.geometry.int_edges)
        edges_wkt.append(src.geometry.bottom_edge_wkt)

        edges = []

        for edge in edges_wkt:
            shapely_line = wkt.loads(edge)
            line = geo.Line([geo.Point(*x) for x in shapely_line.coords])
            edges.append(line)

        mf_dist = self._mfd_to_hazardlib(src.mfd)
        msr = scalerel.get_available_magnitude_scalerel()[src.mag_scale_rel]()

        cmplx = source.ComplexFaultSource(
            source_id=src.id,
            name=src.name,
            tectonic_region_type=src.trt,
            mfd=mf_dist,
            rupture_mesh_spacing=self.hc.rupture_mesh_spacing,
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=src.rupt_aspect_ratio,
            edges=edges,
            rake=src.rake,
            temporal_occurrence_model=self.default_tom,
        )

        return cmplx

    def _characteristic_to_hazardlib(self, src):
        """
        Convert a NRML characteristic fault source to the HazardLib equivalent.

        The surface of a characteristic fault source can be one of the
        following:
            * simple fault
            * complex fault
            * one or more planar surfaces

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.CharacteristicSource` instance.
        :returns:
            The HazardLib representation of the input source.
        """
        mf_dist = self._mfd_to_hazardlib(src.mfd)

        if isinstance(src.surface, nrml_models.SimpleFaultGeometry):
            shapely_line = wkt.loads(src.surface.wkt)
            fault_trace = geo.Line(
                [geo.Point(*x) for x in shapely_line.coords])

            surface = geo.SimpleFaultSurface.from_fault_data(
                fault_trace,
                src.surface.upper_seismo_depth,
                src.surface.lower_seismo_depth,
                src.surface.dip,
                self.hc.rupture_mesh_spacing,
            )
        elif isinstance(src.surface, nrml_models.ComplexFaultGeometry):
            edges_wkt = []
            edges_wkt.append(src.surface.top_edge_wkt)
            edges_wkt.extend(src.surface.int_edges)
            edges_wkt.append(src.surface.bottom_edge_wkt)

            edges = []

            for edge in edges_wkt:
                shapely_line = wkt.loads(edge)
                line = geo.Line([geo.Point(*x) for x in shapely_line.coords])
                edges.append(line)

            surface = geo.ComplexFaultSurface.from_fault_data(
                edges, self.hc.rupture_mesh_spacing)
        else:
            # A collection of planar surfaces
            planar_surfaces = []
            for planar_surface in src.surface:
                kwargs = planar_surface.__dict__
                kwargs.update(dict(mesh_spacing=self.hc.rupture_mesh_spacing))

                planar_surfaces.append(geo.PlanarSurface(**kwargs))

            surface = geo.MultiSurface(planar_surfaces)

        char = source.CharacteristicFaultSource(
            source_id=src.id,
            name=src.name,
            tectonic_region_type=src.trt,
            mfd=mf_dist,
            surface=surface,
            rake=src.rake,
            temporal_occurrence_model=self.default_tom,
        )
        return char

    def _simple_rupture_to_hazardlib(self, src):
        """Convert a NRML simple fault source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.PointSource` instance.
        :returns:
            The HazardLib representation of the input rupture.
        """

        shapely_line = wkt.loads(src.geometry.wkt)
        fault_trace = geo.Line([geo.Point(*x) for x in shapely_line.coords])
        geom = src.geometry

        surface = geo.SimpleFaultSurface.from_fault_data(
            fault_trace, geom.upper_seismo_depth, geom.lower_seismo_depth,
            geom.dip, self.hc.rupture_mesh_spacing)

        rupture = HazardlibRupture(
            mag=src.magnitude, rake=src.rake,
            tectonic_region_type=None, hypocenter=geo.Point(*src.hypocenter),
            surface=surface, source_typology=geo.SimpleFaultSurface)

        return rupture

    def _complex_rupture_to_hazardlib(self, src):
        """Convert a NRML complex fault source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.PointSource` instance.
        :returns:
            The HazardLib representation of the input rupture.
        """

        edges_wkt = []
        edges_wkt.append(src.geometry.top_edge_wkt)
        edges_wkt.extend(src.geometry.int_edges)
        edges_wkt.append(src.geometry.bottom_edge_wkt)

        edges = []

        for edge in edges_wkt:
            shapely_line = wkt.loads(edge)
            line = geo.Line([geo.Point(*x) for x in shapely_line.coords])
            edges.append(line)

        surface = geo.ComplexFaultSurface.from_fault_data(
            edges, self.hc.rupture_mesh_spacing)

        rupture = HazardlibRupture(
            mag=src.magnitude, rake=src.rake,
            tectonic_region_type=None, hypocenter=geo.Point(*src.hypocenter),
            surface=surface, source_typology=geo.ComplexFaultSurface)

        return rupture

    def _mfd_to_hazardlib(self, src_mfd):
        """Convert a NRML MFD to an HazardLib MFD.

        :param src_mfd:
            :class:`openquake.nrmllib.models.IncrementalMFD` or
            :class:`openquake.nrmllib.models.TGRMFD` instance.
        :returns:
            The HazardLib representation of the MFD. See
            :mod:`openquake.hazardlib.mfd`.
        """
        bin_width = self.hc.width_of_mfd_bin
        if isinstance(src_mfd, nrml_models.TGRMFD):
            assert bin_width is not None
            return mfd.TruncatedGRMFD(
                a_val=src_mfd.a_val, b_val=src_mfd.b_val,
                min_mag=src_mfd.min_mag,
                max_mag=src_mfd.max_mag,
                bin_width=bin_width
            )
        elif isinstance(src_mfd, nrml_models.IncrementalMFD):
            return mfd.EvenlyDiscretizedMFD(
                min_mag=src_mfd.min_mag, bin_width=src_mfd.bin_width,
                occurrence_rates=src_mfd.occur_rates
            )


def area_to_point_sources(area_src, area_src_disc):
    """
    Split an area source into a generator of point sources.

    MFDs will be rescaled appropriately for the number of points in the area
    mesh.

    :param area_src:
        :class:`openquake.hazardlib.source.AreaSource`
    :param float area_src_disc:
        Area source discretization step, in kilometers.
    """
    mesh = area_src.polygon.discretize(area_src_disc)
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

    for i, (lon, lat) in enumerate(izip(mesh.lons, mesh.lats)):
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
        yield pt


def split_fault_source(src):
    """
    Generator splitting a fault source into several fault sources,
    one for each magnitude.

    :param src:
        an instance of :class:`openquake.hazardlib.source.base.SeismicSource`
    """
    i = 0  # split source index
    for mag, rate in src.mfd.get_annual_occurrence_rates():
        if rate:  # ignore zero occurency rate
            new_src = copy.copy(src)
            new_src.source_id = '%s-%s' % (src.source_id, i)
            new_src.mfd = mfd.EvenlyDiscretizedMFD(
                min_mag=mag, bin_width=src.mfd.bin_width,
                occurrence_rates=[rate])
            i += 1
        yield new_src


def split_source(src, area_source_discretization):
    """
    Split an area source into point sources and a fault sources into
    smaller fault sources.

    :param src:
        an instance of :class:`openquake.hazardlib.source.base.SeismicSource`
    :param float area_source_discretization:
        area source discretization
    """
    if isinstance(src, source.AreaSource):
        for s in area_to_point_sources(src, area_source_discretization):
            yield s
    elif isinstance(
            src, (source.SimpleFaultSource, source.ComplexFaultSource)):
        for s in split_fault_source(src):
            yield s
    else:  # characteristic sources are not split since they are small
        yield src


def get_num_ruptures_weight(src):
    """
    Compute the weight of a source in a heuristic way. Various experiments show
    that it should be a bit more than linear in the number of ruptures, except
    for point sources.

    :param src:
        an instance of :class:`openquake.hazardlib.source.base.SeismicSource`
    :returns:
        a pair (num_ruptures, weight)
    """
    num_ruptures = src.count_ruptures()
    if isinstance(src, source.PointSource):
        weight = num_ruptures
    elif isinstance(src, source.CharacteristicFaultSource):
        weight = num_ruptures * 50
    else:  # giving more than linear weight to other sources
        weight = num_ruptures ** 1.5
    return num_ruptures, weight


def parse_source_model_smart(fname, is_relevant, apply_uncertainties, hc):
    """
    Parse a NRML source model and yield hazardlib sources.
    Notice that:

    1) uncertainties are applied first
    2) the filter `is_relevant` is applied second
    3) at the end area sources are splitted into point sources.

    :param str fname:
        the full pathname of the source model file
    :param is_relevant:
         a filter function on sources
    :param apply_uncertainties:
        a function modifying the sources
    :param hc:
        an object with attributes rupture_mesh_spacing,
        width_of_mfd_bin, area_source_discretization, investigation_time
    """
    nrml_to_hazardlib = NrmlHazardlibConverter(hc)
    for src_nrml in haz_parsers.SourceModelParser(fname).parse():
        src = nrml_to_hazardlib(src_nrml)
        # the uncertainties must be applied to the original source
        apply_uncertainties(src)
        if not is_relevant(src):
            continue
        num_ruptures, weight = get_num_ruptures_weight(src)
        if num_ruptures > MAX_RUPTURES:
            for s in split_source(src, hc.area_source_discretization):
                yield s, get_num_ruptures_weight(s)[1]
        else:
            yield src, weight
