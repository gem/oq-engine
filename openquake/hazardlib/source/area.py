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
from copy import deepcopy
from openquake.hazardlib.geo import Point
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.baselib.slots import with_slots


@with_slots
class AreaSource(ParametricSeismicSource):
    """
    Area source represents uniform seismicity occurring over a geographical
    region.

    :param polygon:
        An instance of :class:`openquake.hazardlib.geo.polygon.Polygon`
        that defines source's area.
    :param area_discretization:
        Float number, polygon area discretization spacing in kilometers.
        See :meth:`openquake.hazardlib.source.area.AreaSource.iter_ruptures`.

    Other parameters (except ``location``) are the same as for
    :class:`~openquake.hazardlib.source.point.PointSource`.
    """
    _slots_ = ParametricSeismicSource._slots_ + '''upper_seismogenic_depth
    lower_seismogenic_depth nodal_plane_distribution hypocenter_distribution
    polygon area_discretization'''.split()

    MODIFICATIONS = set(())

    RUPTURE_WEIGHT = 1 / 10.

    def __init__(self, source_id, name, tectonic_region_type,
                 mfd, rupture_mesh_spacing,
                 magnitude_scaling_relationship, rupture_aspect_ratio,
                 temporal_occurrence_model,
                 # point-specific parameters (excluding location)
                 upper_seismogenic_depth, lower_seismogenic_depth,
                 nodal_plane_distribution, hypocenter_distribution,
                 # area-specific parameters
                 polygon, area_discretization):
        super(AreaSource, self).__init__(
            source_id, name, tectonic_region_type, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio,
            temporal_occurrence_model)
        self.upper_seismogenic_depth = upper_seismogenic_depth
        self.lower_seismogenic_depth = lower_seismogenic_depth
        self.nodal_plane_distribution = nodal_plane_distribution
        self.hypocenter_distribution = hypocenter_distribution
        self.polygon = polygon
        self.area_discretization = area_discretization
        self.max_radius = 0

    def get_rupture_enclosing_polygon(self, dilation=0):
        """
        Extends the area source polygon by ``dilation`` plus
        :meth:`~openquake.hazardlib.source.point.PointSource._get_max_rupture_projection_radius`.

        See :meth:`superclass method
        <openquake.hazardlib.source.base.BaseSeismicSource.get_rupture_enclosing_polygon>`
        for parameter and return value definition.
        """
        max_rup_radius = self._get_max_rupture_projection_radius()
        return self.polygon.dilate(max_rup_radius + dilation)

    def iter_ruptures(self):
        """
        See :meth:`openquake.hazardlib.source.base.BaseSeismicSource.iter_ruptures`
        for description of parameters and return value.

        Area sources are treated as a collection of point sources
        (see :mod:`openquake.hazardlib.source.point`) with uniform parameters.
        Ruptures of area source are just a union of ruptures
        of those point sources. The actual positions of the implied
        point sources form a uniformly spaced mesh on the polygon.
        Polygon's method :meth:
        `~openquake.hazardlib.geo.polygon.Polygon.discretize`
        is used for creating a mesh of points on the source's area.
        Constructor's parameter ``area_discretization`` is used as
        polygon's discretization spacing (not to be confused with
        rupture surface's mesh spacing which is as well provided
        to the constructor).

        The ruptures' occurrence rates are rescaled with respect to number
        of points the polygon discretizes to.
        """
        polygon_mesh = self.polygon.discretize(self.area_discretization)
        rate_scaling_factor = 1.0 / len(polygon_mesh)

        # take the very first point of the polygon mesh
        [epicenter0] = polygon_mesh[0:1]
        # generate "reference ruptures" -- all the ruptures that have the same
        # epicenter location (first point of the polygon's mesh) but different
        # magnitudes, nodal planes, hypocenters' depths and occurrence rates
        ref_ruptures = []
        for (mag, mag_occ_rate) in self.get_annual_occurrence_rates():
            for (np_prob, np) in self.nodal_plane_distribution.data:
                for (hc_prob, hc_depth) in self.hypocenter_distribution.data:
                    hypocenter = Point(latitude=epicenter0.latitude,
                                       longitude=epicenter0.longitude,
                                       depth=hc_depth)
                    occurrence_rate = (mag_occ_rate
                                       * float(np_prob) * float(hc_prob))
                    occurrence_rate *= rate_scaling_factor
                    surface = self._get_rupture_surface(mag, np, hypocenter)
                    ref_ruptures.append((mag, np.rake, hc_depth,
                                         surface, occurrence_rate))

        # for each of the epicenter positions generate as many ruptures
        # as we generated "reference" ones: new ruptures differ only
        # in hypocenter and surface location
        for epicenter in polygon_mesh:
            for mag, rake, hc_depth, surface, occ_rate in ref_ruptures:
                # translate the surface from first epicenter position
                # to the target one preserving it's geometry
                surface = surface.translate(epicenter0, epicenter)
                hypocenter = deepcopy(epicenter)
                hypocenter.depth = hc_depth
                rupture = ParametricProbabilisticRupture(
                    mag, rake, self.tectonic_region_type, hypocenter,
                    surface, type(self), occ_rate,
                    self.temporal_occurrence_model
                )
                yield rupture

    def count_ruptures(self):
        """
        See
        :meth:`openquake.hazardlib.source.base.BaseSeismicSource.count_ruptures`
        for description of parameters and return value.
        """
        polygon_mesh = self.polygon.discretize(self.area_discretization)
        return (len(polygon_mesh) *
                len(self.get_annual_occurrence_rates()) *
                len(self.nodal_plane_distribution.data) *
                len(self.hypocenter_distribution.data))

    _get_rupture_dimensions = PointSource.__dict__['_get_rupture_dimensions']
    _get_max_rupture_projection_radius = PointSource.__dict__[
        '_get_max_rupture_projection_radius']
    _get_rupture_surface = PointSource.__dict__['_get_rupture_surface']
