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
from nhlib import source
from nrml import models as nrml_models
from shapely import wkt

from openquake.db import models


def nrml_to_nhlib(src, mesh_spacing, bin_width=None, area_src_disc=None):
    """

    :param mesh_spacing:
        Rupture mesh spacing, in km.
    :param bin_width:
        Truncated Gutenberg-Richter MFD (Magnitude Frequency Distribution) bin
        width.
    :param area_src_disc:
        Area source discretization, in km. Applies only to area sources.
    """
    if isinstance(src, nrml_models.PointSource):
        return _point_to_nhlib(src, mesh_spacing, bin_width=bin_width)
    elif isinstance(src, nrml_models.AreaSource):
        assert area_src_disc is not None, (
            "`area_src_disc` is required for area sources"
        )
        return None


def _point_to_nhlib(src, mesh_spacing, bin_width=None):
    shapely_pt = wkt.loads(src.geometry.wkt)

    npd = pmf.PMF(
        [(x.probability,
          geo.NodalPlane(strike=x.strike, dip=x.dip, rake=x.rake))
         for x in src.nodal_plane_dist]
    )
    hd = pmf.PMF([(x.probability, x.depth) for x in src.hypo_depth_dist])

    point = source.PointSource(
        source_id=src.id, name=src.name, tectonic_region_type=src.trt,
        mfd=_mfd_to_nhlib(src.mfd, bin_width=bin_width),
        rupture_mesh_spacing=mesh_spacing,
        magnitude_scaling_relationship=src.mag_scale_rel,
        rupture_aspect_ratio=src.rupt_aspect_ratio,
        upper_seismogenic_depth=src.geometry.upper_seismo_depth,
        lower_seismogenic_depth=src.geometry.lower_seismo_depth,
        location=geo.Point(shapely_pt.x, shapely_pt.y),
        nodal_plane_distribution=npd,
        hypocenter_distribution=hd
    )
    return point


def _mfd_to_nhlib(src_mfd, bin_width=None):
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
            occurence_rates=src_mfd.occur_rates
        )
    else:
        return None
    return mfd


def _source_type(src_model):
    """Given of the source types defined in :mod:`nrml.models`, get the
    `source_type` for a :class:`~openquake.db.models.ParsedSource`.
    """
    if isinstance(nrml_models.PointSource):
        return 'point'
    elif isinstance(nrml_models.AreaSource):
        return 'area'
    elif isinstance(nrml_models.SimpleFaultSource):
        return 'simple'
    elif isinstance(nrml_models.ComplexFaultSource):
        return 'complex'


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
            wkt = geom._polygon2d.wkt

            ps = models.ParsedSource(
                input=self.inp, source_type=_source_type(source), blob=blob,
                geom=wkt
            )

