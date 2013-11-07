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

"""Saves source model data (parsed from a NRML file) to the
'hzrdi.parsed_source' table.
"""
import sys
import math

from django.db import router
from django.db import transaction
from itertools import izip

import openquake.nrmllib
from openquake.hazardlib import geo
from openquake.hazardlib import mfd
from openquake.hazardlib import pmf
from openquake.hazardlib import scalerel
from openquake.hazardlib import source
from openquake.hazardlib.source.rupture import Rupture as HazardlibRupture
from openquake.nrmllib import models as nrml_models
from openquake.nrmllib.hazard import parsers as haz_parsers
from openquake.nrmllib.hazard import writers as haz_writers
from shapely import wkt

from openquake.engine.db import models

# Silencing 'Access to protected member' (WRT hazardlib polygons)
# pylint: disable=W0212


def nrml_to_hazardlib(src, mesh_spacing, bin_width, area_src_disc):
    """
    Convert a seismic source or rupture object from the NRML representation to
    the HazardLib representation. Inputs can be point, area, simple fault, or
    complex fault sources, or simple or complex fault ruptures.

    See :mod:`openquake.nrmllib.models` and :mod:`openquake.hazardlib.source`.

    :param src:
        :mod:`openquake.nrmllib.models` seismic source or rupture instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.

        Only needed for converting seismic sources; use `None` for ruptures.
    :param float area_src_disc:
        Area source discretization, in km. Applies only to area sources.
        If the input source is known to be a type other than an area source,
        you can specify `area_src_disc=None`.

        Only needed for converting seismic sources; use `None` for ruptures.
    :returns:
        The HazardLib representation of the input source.
    """
    if isinstance(src, (nrml_models.AreaSource, nrml_models.PointSource,
                        nrml_models.ComplexFaultSource,
                        nrml_models.SimpleFaultSource,
                        nrml_models.CharacteristicSource)):
        return _nrml_source_to_hazardlib(src, mesh_spacing, bin_width,
                                         area_src_disc)
    elif isinstance(src, (nrml_models.ComplexFaultRuptureModel,
                          nrml_models.SimpleFaultRuptureModel)):
        return _nrml_rupture_to_hazardlib(src, mesh_spacing)


def _nrml_source_to_hazardlib(src, mesh_spacing, bin_width, area_src_disc):
    """
    Convert a NRML source object into the HazardLib representation.

    Parameters and return values are the same as :func:`nrml_to_hazardlib`.
    """
    # The ordering of the switch here matters because:
    #   - AreaSource inherits from PointSource
    #   - ComplexFaultSource inherits from SimpleFaultSource
    try:
        if isinstance(src, nrml_models.AreaSource):
            return _area_to_hazardlib(src, mesh_spacing, bin_width,
                                      area_src_disc)
        elif isinstance(src, nrml_models.PointSource):
            return _point_to_hazardlib(src, mesh_spacing, bin_width)
        elif isinstance(src, nrml_models.ComplexFaultSource):
            return _complex_to_hazardlib(src, mesh_spacing, bin_width)
        elif isinstance(src, nrml_models.SimpleFaultSource):
            return _simple_to_hazardlib(src, mesh_spacing, bin_width)
        elif isinstance(src, nrml_models.CharacteristicSource):
            return _characteristic_to_hazardlib(src, mesh_spacing, bin_width)
    except:
        etype, err, tb = sys.exc_info()
        msg = (
            "The following error has occurred with source id='%s', name='%s': "
            "%s" % (src.id, src.name, err.message))
        raise etype, msg, tb


def _nrml_rupture_to_hazardlib(src, mesh_spacing):
    """
    Convert a NRML rupture object into the HazardLib representation.

    Parameters and return values are similar to :func:`nrml_to_hazardlib`.
    """
    if isinstance(src, nrml_models.ComplexFaultRuptureModel):
        return _complex_rupture_to_hazardlib(src, mesh_spacing)
    elif isinstance(src, nrml_models.SimpleFaultRuptureModel):
        return _simple_rupture_to_hazardlib(src, mesh_spacing)


def _point_to_hazardlib(src, mesh_spacing, bin_width):
    """Convert a NRML point source to the HazardLib equivalent.

    See :mod:`openquake.nrmllib.models` and :mod:`openquake.hazardlib.source`.

    :param src:
        :class:`openquake.nrmllib.models.PointSource` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :returns:
        The HazardLib representation of the input source.
    """
    shapely_pt = wkt.loads(src.geometry.wkt)

    mf_dist = _mfd_to_hazardlib(src.mfd, bin_width)

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
        rupture_mesh_spacing=mesh_spacing,
        magnitude_scaling_relationship=msr,
        rupture_aspect_ratio=src.rupt_aspect_ratio,
        upper_seismogenic_depth=src.geometry.upper_seismo_depth,
        lower_seismogenic_depth=src.geometry.lower_seismo_depth,
        location=geo.Point(shapely_pt.x, shapely_pt.y),
        nodal_plane_distribution=npd,
        hypocenter_distribution=hd
    )

    return point


def _area_to_hazardlib(src, mesh_spacing, bin_width, area_src_disc):
    """Convert a NRML area source to the HazardLib equivalent.

    See :mod:`openquake.nrmllib.models` and :mod:`openquake.hazardlib.source`.

    :param src:
        :class:`openquake.nrmllib.models.PointSource` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :param float area_src_disc:
        Area source discretization, in km. Applies only to area sources.
    :returns:
        The HazardLib representation of the input source.
    """
    shapely_polygon = wkt.loads(src.geometry.wkt)
    hazardlib_polygon = geo.Polygon(
        # We ignore the last coordinate in the sequence here, since it is a
        # duplicate of the first. hazardlib will close the loop for us.
        [geo.Point(*x) for x in list(shapely_polygon.exterior.coords)[:-1]]
    )

    mf_dist = _mfd_to_hazardlib(src.mfd, bin_width)

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
        rupture_mesh_spacing=mesh_spacing,
        magnitude_scaling_relationship=msr,
        rupture_aspect_ratio=src.rupt_aspect_ratio,
        upper_seismogenic_depth=src.geometry.upper_seismo_depth,
        lower_seismogenic_depth=src.geometry.lower_seismo_depth,
        nodal_plane_distribution=npd, hypocenter_distribution=hd,
        polygon=hazardlib_polygon,
        area_discretization=area_src_disc
    )

    return area


def _simple_to_hazardlib(src, mesh_spacing, bin_width):
    """Convert a NRML simple fault source to the HazardLib equivalent.

    See :mod:`openquake.nrmllib.models` and :mod:`openquake.hazardlib.source`.

    :param src:
        :class:`openquake.nrmllib.models.SimpleFaultRuptureModel` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :returns:
        The HazardLib representation of the input source.
    """
    shapely_line = wkt.loads(src.geometry.wkt)
    fault_trace = geo.Line([geo.Point(*x) for x in shapely_line.coords])

    mf_dist = _mfd_to_hazardlib(src.mfd, bin_width)
    msr = scalerel.get_available_magnitude_scalerel()[src.mag_scale_rel]()

    simple = source.SimpleFaultSource(
        source_id=src.id,
        name=src.name,
        tectonic_region_type=src.trt,
        mfd=mf_dist,
        rupture_mesh_spacing=mesh_spacing,
        magnitude_scaling_relationship=msr,
        rupture_aspect_ratio=src.rupt_aspect_ratio,
        upper_seismogenic_depth=src.geometry.upper_seismo_depth,
        lower_seismogenic_depth=src.geometry.lower_seismo_depth,
        fault_trace=fault_trace,
        dip=src.geometry.dip,
        rake=src.rake
    )

    return simple


def _complex_to_hazardlib(src, mesh_spacing, bin_width):
    """Convert a NRML complex fault source to the HazardLib equivalent.

    See :mod:`openquake.nrmllib.models` and :mod:`openquake.hazardlib.source`.

    :param src:
        :class:`openquake.nrmllib.models.ComplexFaultRuptureModel` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
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

    mf_dist = _mfd_to_hazardlib(src.mfd, bin_width)
    msr = scalerel.get_available_magnitude_scalerel()[src.mag_scale_rel]()

    cmplx = source.ComplexFaultSource(
        source_id=src.id,
        name=src.name,
        tectonic_region_type=src.trt,
        mfd=mf_dist,
        rupture_mesh_spacing=mesh_spacing,
        magnitude_scaling_relationship=msr,
        rupture_aspect_ratio=src.rupt_aspect_ratio,
        edges=edges,
        rake=src.rake,
    )

    return cmplx


def _characteristic_to_hazardlib(src, mesh_spacing, bin_width):
    """
    Convert a NRML characteristic fault source to the HazardLib equivalent.

    The surface of a characteristic fault source can be one of the following:
        * simple fault
        * complex fault
        * one or more planar surfaces

    See :mod:`openquake.nrmllib.models` and :mod:`openquake.hazardlib.source`.

    :param src:
        :class:`openquake.nrmllib.models.CharacteristicSource` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :returns:
        The HazardLib representation of the input source.
    """
    mf_dist = _mfd_to_hazardlib(src.mfd, bin_width)

    if isinstance(src.surface, nrml_models.SimpleFaultGeometry):
        shapely_line = wkt.loads(src.surface.wkt)
        fault_trace = geo.Line([geo.Point(*x) for x in shapely_line.coords])

        surface = geo.SimpleFaultSurface.from_fault_data(
            fault_trace,
            src.surface.upper_seismo_depth,
            src.surface.lower_seismo_depth,
            src.surface.dip,
            mesh_spacing
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

        surface = geo.ComplexFaultSurface.from_fault_data(edges, mesh_spacing)
    else:
        # A collection of planar surfaces
        planar_surfaces = []
        for planar_surface in src.surface:
            kwargs = planar_surface.__dict__
            kwargs.update(dict(mesh_spacing=mesh_spacing))

            planar_surfaces.append(geo.PlanarSurface(**kwargs))

        surface = geo.MultiSurface(planar_surfaces)

    char = source.CharacteristicFaultSource(
        source_id=src.id,
        name=src.name,
        tectonic_region_type=src.trt,
        mfd=mf_dist,
        surface=surface,
        rake=src.rake
    )
    return char


def _simple_rupture_to_hazardlib(src, mesh_spacing):
    """Convert a NRML simple fault source to the HazardLib equivalent.

    See :mod:`openquake.nrmllib.models` and :mod:`openquake.hazardlib.source`.

    :param src:
        :class:`openquake.nrmllib.models.PointSource` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :returns:
        The HazardLib representation of the input rupture.
    """

    shapely_line = wkt.loads(src.geometry.wkt)
    fault_trace = geo.Line([geo.Point(*x) for x in shapely_line.coords])
    geom = src.geometry

    surface = geo.SimpleFaultSurface.from_fault_data(
        fault_trace, geom.upper_seismo_depth, geom.lower_seismo_depth,
        geom.dip, mesh_spacing)

    rupture = HazardlibRupture(
        mag=src.magnitude, rake=src.rake,
        tectonic_region_type=None, hypocenter=geo.Point(*src.hypocenter),
        surface=surface, source_typology=geo.SimpleFaultSurface)

    return rupture


def _complex_rupture_to_hazardlib(src, mesh_spacing):
    """Convert a NRML complex fault source to the HazardLib equivalent.

    See :mod:`openquake.nrmllib.models` and :mod:`openquake.hazardlib.source`.

    :param src:
        :class:`openquake.nrmllib.models.PointSource` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
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

    surface = geo.ComplexFaultSurface.from_fault_data(edges, mesh_spacing)

    rupture = HazardlibRupture(
        mag=src.magnitude, rake=src.rake,
        tectonic_region_type=None, hypocenter=geo.Point(*src.hypocenter),
        surface=surface, source_typology=geo.ComplexFaultSurface)

    return rupture


def _mfd_to_hazardlib(src_mfd, bin_width):
    """Convert a NRML MFD to an HazardLib MFD.

    :param src_mfd:
        :class:`openquake.nrmllib.models.IncrementalMFD` or
        :class:`openquake.nrmllib.models.TGRMFD` instance.
    :param float bin_width:
        Optional. Required only for Truncated Gutenberg-Richter MFDs.
    :returns:
        The HazardLib representation of the MFD. See
        :mod:`openquake.hazardlib.mfd`.
    """
    if isinstance(src_mfd, nrml_models.TGRMFD):
        assert bin_width is not None
        return mfd.TruncatedGRMFD(
            a_val=src_mfd.a_val, b_val=src_mfd.b_val, min_mag=src_mfd.min_mag,
            max_mag=src_mfd.max_mag, bin_width=bin_width
        )
    elif isinstance(src_mfd, nrml_models.IncrementalMFD):
        return mfd.EvenlyDiscretizedMFD(
            min_mag=src_mfd.min_mag, bin_width=src_mfd.bin_width,
            occurrence_rates=src_mfd.occur_rates
        )


def _source_type(src_model):
    """Given of the source types defined in :mod:`openquake.nrmllib.models`,
    get the `source_type` for a
    :class:`~openquake.engine.db.models.ParsedSource`.
    """
    if isinstance(src_model, nrml_models.AreaSource):
        return 'area'
    elif isinstance(src_model, nrml_models.PointSource):
        return 'point'
    elif isinstance(src_model, nrml_models.ComplexFaultSource):
        return 'complex'
    elif isinstance(src_model, nrml_models.SimpleFaultSource):
        return 'simple'
    elif isinstance(src_model, nrml_models.CharacteristicSource):
        return 'characteristic'


class SourceDBWriter(object):
    """Takes a sequence of seismic source objects from nrmllib, convert them
    to hazardlib objects, optionally filter them and saves the result to the
    `hzrdi.parsed_source` table in the database.

    The source object data will be stored in the database in pickled blob form.

    :param job:
        :class:`~openquake.engine.db.models.OqJob` object.
    :param source_model:
        :class:`openquake.nrmllib.models.SourceModel` object, which is an
        Iterable of NRML source model objects (parsed from NRML XML). This
        also includes the name of the source model.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :param float area_src_disc:
        Area source discretization, in km. Applies only to area sources.
        If the input source is known to be a type other than an area source,
        you can specify `area_src_disc=None`.
    :param condition:
        A function hazard source -> boolean to filter the sources to save;
        by default it returns always True and no sources are filtered.
    """

    def __init__(self, job, source_model_filename, source_model,
                 mesh_spacing, bin_width,
                 area_src_disc, condition=lambda src: True):
        self.job = job
        self.source_model = source_model
        self.source_model_filename = source_model_filename
        self.mesh_spacing = mesh_spacing
        self.bin_width = bin_width
        self.area_src_disc = area_src_disc
        self.condition = condition

    @transaction.commit_on_success(router.db_for_write(models.ParsedSource))
    def serialize(self):
        """Save NRML sources to the database in hazardlib format"""
        for src in self.source_model:
            hazardlib_source = nrml_to_hazardlib(
                src, self.mesh_spacing, self.bin_width, self.area_src_disc)
            if self.condition(hazardlib_source):
                models.ParsedSource.objects.create(
                    job=self.job, source_type=_source_type(src),
                    nrml=hazardlib_source,
                    source_model_filename=self.source_model_filename)


def area_source_to_point_sources(area_src, area_src_disc):
    """
    Split an area source into a generator of point sources.

    MFDs will be rescaled appropriately for the number of points in the area
    mesh.

    :param area_src:
        :class:`openquake.nrmllib.models.AreaSource`
    :param float area_src_disc:
        Area source discretization step, in kilometers.
    """
    shapely_polygon = wkt.loads(area_src.geometry.wkt)
    area_polygon = geo.Polygon(
        # We ignore the last coordinate in the sequence here, since it is a
        # duplicate of the first. hazardlib will close the loop for us.
        [geo.Point(*x) for x in list(shapely_polygon.exterior.coords)[:-1]]
    )

    mesh = area_polygon.discretize(area_src_disc)
    num_points = len(mesh)

    area_mfd = area_src.mfd

    if isinstance(area_mfd, nrml_models.TGRMFD):
        new_a_val = math.log10(10 ** area_mfd.a_val / float(num_points))
        new_mfd = nrml_models.TGRMFD(a_val=new_a_val, b_val=area_mfd.b_val,
                                     min_mag=area_mfd.min_mag,
                                     max_mag=area_mfd.max_mag)
    elif isinstance(area_mfd, nrml_models.IncrementalMFD):
        new_occur_rates = [float(x) / num_points for x in area_mfd.occur_rates]
        new_mfd = nrml_models.IncrementalMFD(min_mag=area_mfd.min_mag,
                                             bin_width=area_mfd.bin_width,
                                             occur_rates=new_occur_rates)

    for i, (lon, lat) in enumerate(izip(mesh.lons, mesh.lats)):
        pt = nrml_models.PointSource(
            # Generate a new ID and name
            id='%s-%s' % (area_src.id, i),
            name='%s-%s' % (area_src.name, i),
            trt=area_src.trt,
            geometry=nrml_models.PointGeometry(
                upper_seismo_depth=area_src.geometry.upper_seismo_depth,
                lower_seismo_depth=area_src.geometry.lower_seismo_depth,
                wkt='POINT(%s %s)' % (lon, lat)
            ),
            mag_scale_rel=area_src.mag_scale_rel,
            rupt_aspect_ratio=area_src.rupt_aspect_ratio,
            mfd=new_mfd,
            nodal_plane_dist=area_src.nodal_plane_dist,
            hypo_depth_dist=area_src.hypo_depth_dist
        )
        yield pt


def optimize_source_model(input_path, area_src_disc, output_path):
    """
    Parse the source model located at ``input_path``, discretize area sources
    by ``area_src_disc``, and write the optimized model to ``output_path``.

    :returns:
        ``output_path``
    """
    parser = haz_parsers.SourceModelParser(input_path)
    src_model = parser.parse()

    def split_area(model):
        for src in model:
            if isinstance(src, nrml_models.AreaSource):
                for pt in area_source_to_point_sources(src, area_src_disc):
                    yield pt
            else:
                yield src

    out_source_model = nrml_models.SourceModel(name=src_model.name,
                                               sources=split_area(src_model))
    writer = haz_writers.SourceModelXMLWriter(output_path)
    writer.serialize(out_source_model)

    return output_path
