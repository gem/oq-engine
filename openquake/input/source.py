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

# Silencing 'Access to protected member' (WRT nhlib polygons)
# pylint: disable=W0212

_SCALE_REL_MAP = {
    'PeerMSR': scalerel.PeerMSR,
    'WC1994': scalerel.WC1994,
}


def nrml_to_nhlib(src, mesh_spacing, bin_width, area_src_disc):
    """Convert a seismic source object from the NRML representation to the
    NHLib representation. Inputs can be point, area, simple fault, or complex
    fault sources.

    See :mod:`nrml.models` and :mod:`nhlib.source`.

    :param src:
        :mod:`nrml.models` seismic source instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :param float area_src_disc:
        Area source discretization, in km. Applies only to area sources.
        If the input source is known to be a type other than an area source,
        you can specify `area_src_disc=None`.
    :returns:
        The NHLib representation of the input source.
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
    """Convert a NRML point source to the NHLib equivalent.

    See :mod:`nrml.models` and :mod:`nhlib.source`.

    :param src:
        :class:`nrml.models.PointSource` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :returns:
        The NHLib representation of the input source.
    """
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
    """Convert a NRML area source to the NHLib equivalent.

    See :mod:`nrml.models` and :mod:`nhlib.source`.

    :param src:
        :class:`nrml.models.PointSource` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :param float area_src_disc:
        Area source discretization, in km. Applies only to area sources.
    :returns:
        The NHLib representation of the input source.
    """
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
    """Convert a NRML simple fault source to the NHLib equivalent.

    See :mod:`nrml.models` and :mod:`nhlib.source`.

    :param src:
        :class:`nrml.models.PointSource` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :returns:
        The NHLib representation of the input source.
    """
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
    """Convert a NRML complex fault source to the NHLib equivalent.

    See :mod:`nrml.models` and :mod:`nhlib.source`.

    :param src:
        :class:`nrml.models.PointSource` instance.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :returns:
        The NHLib representation of the input source.
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
    """Convert a NRML MFD to an NHLib MFD.

    :param src_mfd:
        :class:`nrml.models.IncrementalMFD` or :class:`nrml.models.TGRMFD`
        instance.
    :param float bin_width:
        Optional. Required only for Truncated Gutenberg-Richter MFDs.
    :returns:
        The NHLib representation of the MFD. See :mod:`nhlib.mfd`.
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
    if isinstance(src_model, nrml_models.AreaSource):
        return 'area'
    elif isinstance(src_model, nrml_models.PointSource):
        return 'point'
    elif isinstance(src_model, nrml_models.ComplexFaultSource):
        return 'complex'
    elif isinstance(src_model, nrml_models.SimpleFaultSource):
        return 'simple'


class SourceDBWriter(object):
    """Takes a sequence of seismic source objects and saves them to the
    `hzrdi.parsed_source` table in the database.

    The source object data will be stored in the database in pickled blob form.
    The `hzrdi.parsed_source.polygon` field will contain the "rupture
    enclosing" polygon. We use NHLib to generate this polygon. (See
    :method:`nhlib.source.base.SeismicSource.get_rupture_enclosing_polygon`.)

    :param inp:
        :class:`~openquake.db.models.Input` object, the top-level container for
        the sources written to the database. Should have an `input_type` of
        'source'.
    :param source_model:
        :class:`nrml.models.SourceModel` object, which is an Iterable of NRML
        source model objects (parsed from NRML XML). This also includes the
        name of the source model.
    :param float mesh_spacing:
        Rupture mesh spacing, in km.
    :param float bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :param float area_src_disc:
        Area source discretization, in km. Applies only to area sources.
        If the input source is known to be a type other than an area source,
        you can specify `area_src_disc=None`.
    """

    def __init__(self, inp, source_model, mesh_spacing, bin_width,
                 area_src_disc):
        self.inp = inp
        self.source_model = source_model

        self.mesh_spacing = mesh_spacing
        self.bin_width = bin_width
        self.area_src_disc = area_src_disc

    @transaction.commit_on_success(router.db_for_write(models.ParsedSource))
    def serialize(self):
        """Save NRML sources to the database along with
        'rupture-enclosing polygon' geometry for each source.
        """

        assert self.inp.input_type == 'source', (
            "`Input` object has the wrong `input_type`. Expected: 'source'."
            "Got: '%s'."
        ) % self.inp.input_type
        # First, set the input name to the source model name
        self.inp.name = self.source_model.name
        self.inp.save()

        for src in self.source_model:
            nhlib_src = nrml_to_nhlib(
                src, self.mesh_spacing, self.bin_width, self.area_src_disc
            )
            geom = nhlib_src.get_rupture_enclosing_polygon()

            ps = models.ParsedSource(
                input=self.inp, source_type=_source_type(src), nrml=src,
                polygon=geom.wkt
            )
            ps.save()
