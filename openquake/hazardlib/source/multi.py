# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
Module :mod:`openquake.hazardlib.source.area` defines :class:`AreaSource`.
"""
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.geo import utils
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.polygon import Polygon


class MultiPointSource(ParametricSeismicSource):
    """
    MultiPointSource class, used to describe point sources with different
    MFDs and the same rupture_mesh_spacing, magnitude_scaling_relationship,
    rupture_aspect_ratio, temporal_occurrence_model, upper_seismogenic_depth,
    lower_seismogenic_depth, nodal_plane_distribution, hypocenter_distribution
    """
    MODIFICATIONS = set(())
    RUPTURE_WEIGHT = 1 / 10.

    def __init__(self, source_id, name, tectonic_region_type,
                 mfd, rupture_mesh_spacing,
                 magnitude_scaling_relationship,
                 rupture_aspect_ratio, temporal_occurrence_model,
                 # point-specific parameters (excluding location)
                 upper_seismogenic_depth, lower_seismogenic_depth,
                 nodal_plane_distribution, hypocenter_distribution, mesh):
        assert len(mfd) == len(mesh), (len(mfd), len(mesh))
        super(MultiPointSource, self).__init__(
            source_id, name, tectonic_region_type, mfd,
            rupture_mesh_spacing, magnitude_scaling_relationship,
            rupture_aspect_ratio, temporal_occurrence_model)
        self.upper_seismogenic_depth = upper_seismogenic_depth
        self.lower_seismogenic_depth = lower_seismogenic_depth
        self.nodal_plane_distribution = nodal_plane_distribution
        self.hypocenter_distribution = hypocenter_distribution
        self.mesh = mesh

    def __iter__(self):
        for i, (mfd, point) in enumerate(zip(self.mfd, self.mesh)):
            name = '%s:%s' % (self.source_id, i)
            ps = PointSource(
                name, name, self.tectonic_region_type,
                mfd, self.rupture_mesh_spacing,
                self.magnitude_scaling_relationship,
                self.rupture_aspect_ratio,
                self.temporal_occurrence_model,
                self.upper_seismogenic_depth,
                self.lower_seismogenic_depth,
                point,
                self.nodal_plane_distribution,
                self.hypocenter_distribution)
            yield ps

    def iter_ruptures(self):
        """
        Yield the ruptures of the underlying point sources
        """
        for ps in self:
            for rupture in ps.iter_ruptures():
                yield rupture

    def count_ruptures(self):
        """
        See
        :meth:`openquake.hazardlib.source.base.BaseSeismicSource.count_ruptures`
        for description of parameters and return value.
        """
        return (len(self.get_annual_occurrence_rates()) *
                len(self.nodal_plane_distribution.data) *
                len(self.hypocenter_distribution.data))

    def filter_sites_by_distance_to_source(self, integration_distance, sites):
        """Do not filter"""
        return sites

    def get_rupture_enclosing_polygon(self, dilation=0):
        """No polygon"""

    def get_bounding_box(self, maxdist):
        w, e, n, s = utils.get_spherical_bounding_box(
            self.mesh.lons, self.mesh.lats)
        poly = Polygon([Point(w, s), Point(e, s), Point(e, n), Point(w, n),
                        Point(w, s)])
        return poly.dilate(maxdist).get_bbox()
