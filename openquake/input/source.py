# Copyright (c) 2010-2012, GEM Foundation.
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

import pickle

from django.db import router
from django.db import transaction
from nhlib import geo
from nhlib import mfd
from nhlib import pmf
from nhlib import scalerel
from nhlib import source
from nrml import models as nrml_models
from shapely import wkt

from openquake.db import models


_SCALE_REL_MAP = {
    'PeerMSR': scalerel.PeerMSR,
    'WC1994': scalerel.WC1994,
}


def nrml_to_nhlib(src, mesh_spacing, bin_width, area_src_disc):
    """

    :param mesh_spacing:
        Rupture mesh spacing, in km.
    :param bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :param area_src_disc:
        Area source discretization, in km. Applies only to area sources.
    """
    # The ordering of the switch here matters because:
    #   - AreaSource inherits from PointSource
    #   - ComplexFaultSource inherits from SimpleFaultSource
    if isinstance(src, nrml_models.AreaSource):
        return _area_to_nhlib(src, mesh_spacing, bin_width, area_src_disc)
    elif isinstance(src, nrml_models.PointSource):
        return _point_to_nhlib(src, mesh_spacing, bin_width)
    elif isinstance(src, nrml_models.ComplexFaultSource):
        return _complex_to_nhlib(src, mesh_spacing, bin_width)
    elif isinstance(src, nrml_models.SimpleFaultSource):
        return _simple_to_nhlib(src, mesh_spacing, bin_width)


def _point_to_nhlib(src, mesh_spacing, bin_width):
    shapely_pt = wkt.loads(src.geometry.wkt)

    mf_dist = _mfd_to_nhlib(src.mfd, bin_width)

    # nodal plane distribution:
    npd = pmf.PMF(
        [(x.probability,
          geo.NodalPlane(strike=x.strike, dip=x.dip, rake=x.rake))
         for x in src.nodal_plane_dist]
    )

    # hypocentral depth distribution:
    hd = pmf.PMF([(x.probability, x.depth) for x in src.hypo_depth_dist])

    point = source.PointSource(
        source_id=src.id,
        name=src.name,
        tectonic_region_type=src.trt,
        mfd=mf_dist,
        rupture_mesh_spacing=mesh_spacing,
        magnitude_scaling_relationship=_SCALE_REL_MAP[src.mag_scale_rel](),
        rupture_aspect_ratio=src.rupt_aspect_ratio,
        upper_seismogenic_depth=src.geometry.upper_seismo_depth,
        lower_seismogenic_depth=src.geometry.lower_seismo_depth,
        location=geo.Point(shapely_pt.x, shapely_pt.y),
        nodal_plane_distribution=npd,
        hypocenter_distribution=hd
    )

    return point


def _area_to_nhlib(src, mesh_spacing, bin_width, area_src_disc):
    shapely_polygon = wkt.loads(src.geometry.wkt)
    nhlib_polygon = geo.Polygon(
        # We ignore the last coordinate in the sequence here, since it is a
        # duplicate of the first. nhlib will close the loop for us.
        [geo.Point(*x) for x in list(shapely_polygon.exterior.coords)[:-1]]
    )

    mf_dist = _mfd_to_nhlib(src.mfd, bin_width)

    # nodal plane distribution:
    npd = pmf.PMF(
        [(x.probability,
          geo.NodalPlane(strike=x.strike, dip=x.dip, rake=x.rake))
         for x in src.nodal_plane_dist]
    )

    # hypocentral depth distribution:
    hd = pmf.PMF([(x.probability, x.depth) for x in src.hypo_depth_dist])

    area = source.AreaSource(
        source_id=src.id,
        name=src.name,
        tectonic_region_type=src.trt,
        mfd=mf_dist,
        rupture_mesh_spacing=mesh_spacing,
        magnitude_scaling_relationship=_SCALE_REL_MAP[src.mag_scale_rel](),
        rupture_aspect_ratio=src.rupt_aspect_ratio,
        upper_seismogenic_depth=src.geometry.upper_seismo_depth,
        lower_seismogenic_depth=src.geometry.lower_seismo_depth,
        nodal_plane_distribution=npd, hypocenter_distribution=hd,
        polygon=nhlib_polygon,
        area_discretization=area_src_disc
    )

    return area


def _simple_to_nhlib(src, mesh_spacing, bin_width):
    shapely_line = wkt.loads(src.geometry.wkt)
    fault_trace = geo.Line([geo.Point(*x) for x in shapely_line.coords])

    mf_dist = _mfd_to_nhlib(src.mfd, bin_width)

    simple = source.SimpleFaultSource(
        source_id=src.id,
        name=src.name,
        tectonic_region_type=src.trt,
        mfd=mf_dist,
        rupture_mesh_spacing=mesh_spacing,
        magnitude_scaling_relationship=_SCALE_REL_MAP[src.mag_scale_rel](),
        rupture_aspect_ratio=src.rupt_aspect_ratio,
        upper_seismogenic_depth=src.geometry.upper_seismo_depth,
        lower_seismogenic_depth=src.geometry.lower_seismo_depth,
        fault_trace=fault_trace,
        dip=src.geometry.dip,
        rake=src.rake
    )

    return simple


def _complex_to_nhlib(src, mesh_spacing, bin_width):
    edges_wkt = []
    edges_wkt.append(src.geometry.top_edge_wkt)
    edges_wkt.extend(src.geometry.int_edges)
    edges_wkt.append(src.geometry.bottom_edge_wkt)

    edges = []

    for edge in edges_wkt:
        shapely_line = wkt.loads(edge)
        line = geo.Line([geo.Point(*x) for x in shapely_line.coords])
        edges.append(line)

    mf_dist = _mfd_to_nhlib(src.mfd, bin_width)

    cmplx = source.ComplexFaultSource(
        source_id=src.id,
        name=src.name,
        tectonic_region_type=src.trt,
        mfd=mf_dist,
        rupture_mesh_spacing=mesh_spacing,
        magnitude_scaling_relationship=_SCALE_REL_MAP[src.mag_scale_rel](),
        rupture_aspect_ratio=src.rupt_aspect_ratio,
        edges=edges,
        rake=src.rake,
    )

    return cmplx


def _mfd_to_nhlib(src_mfd, bin_width):
    """
    :param float bin_width:
        Optional. Required only for Truncated Gutenberg-Richter MFDs.
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
    """Given of the source types defined in :mod:`nrml.models`, get the
    `source_type` for a :class:`~openquake.db.models.ParsedSource`.
    """
    if isinstance(nrml_models.AreaSource):
        return 'area'
    elif isinstance(nrml_models.PointSource):
        return 'point'
    elif isinstance(nrml_models.ComplexFaultSource):
        return 'complex'
    elif isinstance(nrml_models.SimpleFaultSource):
        return 'simple'


class SourceDBWriter(object):
    """
    :param inp:
        :class:`~openquake.db.models.Input` object, the top-level container for
        the sources written to the database. Should have an input_type of
        'source'.
    :param source_model:
        :class:`nrml.models.SourceModel` object, which is an Iterable of NRML
        source model objects (parsed from NRML XML). This also includes the
        name of the source model.
    """

    def __init__(self, inp, source_model, area_source_disc, mesh_spacing,
                 bin_width):
        self.inp = inp
        self.source_model = source_model

        self.area_source_disc = area_source_disc
        self.mesh_spacing = mesh_spacing
        self.bin_width = bin_width

    @transaction.commit_on_success(router.db_for_write(models.ParsedSource))
    def serialize(self):

        # First, set the input name to the source model name
        self.inp.name = self.source_model.name
        self.inp.save()

        for source in self.source_model:
            blob = pickle.dumps(source, pickle.HIGHEST_PROTOCOL)
            nhlib_src = nrml_to_nhlib(source)
            geom = nhlib_src.get_rupture_enclosing_polygon()
            geom._init_polygon2d()
            geom_wkt = geom._polygon2d.wkt

            ps = models.ParsedSource(
                input=self.inp, source_type=_source_type(source), blob=blob,
                geom=geom_wkt
            )
