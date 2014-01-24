# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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
Module :mod:`openquake.hazardlib.source.simple_fault` defines
:class:`SimpleFaultSource`.
"""
import math

from openquake.hazardlib.source.base import SeismicSource
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.source.rupture import ProbabilisticRupture
from openquake.hazardlib.slots import with_slots


@with_slots
class SimpleFaultSource(SeismicSource):
    """
    Simple fault source typology represents seismicity occurring on a fault
    surface with simple geometry.

    :param upper_seismogenic_depth:
        Minimum depth an earthquake rupture can reach, in km.
    :param lower_seismogenic_depth:
        Maximum depth an earthquake rupture can reach, in km.
    :param fault_trace:
        A :class:`~openquake.hazardlib.geo.line.Line` representing
        the line of intersection between the fault plane and the Earth's
        surface.
    :param dip:
        Angle between earth surface and fault plane in decimal degrees.
    :param rake:
        Angle describing rupture propagation direction in decimal degrees.

    See also :class:`openquake.hazardlib.source.base.SeismicSource`
    for description of other parameters.

    :raises ValueError:
        If :meth:`~openquake.hazardlib.geo.surface.simple_fault.SimpleFaultSurface.check_fault_data`
        fails, if rake value is invalid and if rupture mesh spacing is too high
        for the lowest magnitude value.
    """
    __slots__ = SeismicSource.__slots__ + '''rupture_mesh_spacing
    magnitude_scaling_relationship rupture_aspect_ratio
    upper_seismogenic_depth lower_seismogenic_depth
    fault_trace dip rake'''.split()

    def __init__(self, source_id, name, tectonic_region_type,
                 mfd, rupture_mesh_spacing,
                 magnitude_scaling_relationship, rupture_aspect_ratio,
                 # simple fault specific parameters
                 upper_seismogenic_depth, lower_seismogenic_depth,
                 fault_trace, dip, rake):
        super(SimpleFaultSource, self).__init__(
            source_id, name, tectonic_region_type, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio
        )

        NodalPlane.check_rake(rake)
        SimpleFaultSurface.check_fault_data(
            fault_trace, upper_seismogenic_depth, lower_seismogenic_depth,
            dip, rupture_mesh_spacing
        )
        self.fault_trace = fault_trace
        self.upper_seismogenic_depth = upper_seismogenic_depth
        self.lower_seismogenic_depth = lower_seismogenic_depth
        self.dip = dip
        self.rake = rake

        min_mag = self.mfd.get_min_mag()
        cols_rows = self._get_rupture_dimensions(float('inf'), float('inf'),
                                                 min_mag)
        if 1 in cols_rows:
            raise ValueError('mesh spacing %s is too low to represent '
                             'ruptures of magnitude %s' %
                             (rupture_mesh_spacing, min_mag))

    def get_rupture_enclosing_polygon(self, dilation=0):
        """
        Uses :meth:`openquake.hazardlib.geo.surface.simple_fault.SimpleFaultSurface.surface_projection_from_fault_data`
        for getting the fault's surface projection and then calls
        its :meth:`~openquake.hazardlib.geo.polygon.Polygon.dilate`
        method passing in ``dilation`` parameter.

        See :meth:`superclass method
        <openquake.hazardlib.source.base.SeismicSource.get_rupture_enclosing_polygon>`
        for parameter and return value definition.
        """
        polygon = SimpleFaultSurface.surface_projection_from_fault_data(
            self.fault_trace, self.upper_seismogenic_depth,
            self.lower_seismogenic_depth, self.dip
        )
        if dilation:
            return polygon.dilate(dilation)
        else:
            return polygon

    def iter_ruptures(self, temporal_occurrence_model):
        """
        See :meth:
        `openquake.hazardlib.source.base.SeismicSource.iter_ruptures`.

        Generates a ruptures using the "floating" algorithm: for all the
        magnitude values of assigned MFD calculates the rupture size with
        respect to MSR and aspect ratio and then places ruptures of that
        size on the surface of the whole fault source. The occurrence
        rate of each of those ruptures is the magnitude occurrence rate
        divided by the number of ruptures that can be placed in a fault.
        """
        whole_fault_surface = SimpleFaultSurface.from_fault_data(
            self.fault_trace, self.upper_seismogenic_depth,
            self.lower_seismogenic_depth, self.dip, self.rupture_mesh_spacing
        )
        whole_fault_mesh = whole_fault_surface.get_mesh()
        mesh_rows, mesh_cols = whole_fault_mesh.shape
        fault_length = float((mesh_cols - 1) * self.rupture_mesh_spacing)
        fault_width = float((mesh_rows - 1) * self.rupture_mesh_spacing)

        for (mag, mag_occ_rate) in self.get_annual_occurrence_rates():
            rup_cols, rup_rows = self._get_rupture_dimensions(
                fault_length, fault_width, mag
            )
            num_rup_along_length = mesh_cols - rup_cols + 1
            num_rup_along_width = mesh_rows - rup_rows + 1
            num_rup = num_rup_along_length * num_rup_along_width

            occurrence_rate = mag_occ_rate / float(num_rup)

            for first_row in xrange(num_rup_along_width):
                for first_col in xrange(num_rup_along_length):
                    mesh = whole_fault_mesh[first_row: first_row + rup_rows,
                                            first_col: first_col + rup_cols]
                    hypocenter = mesh.get_middle_point()
                    surface = SimpleFaultSurface(mesh)
                    yield ProbabilisticRupture(
                        mag, self.rake, self.tectonic_region_type, hypocenter,
                        surface, type(self),
                        occurrence_rate, temporal_occurrence_model
                    )

    def count_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.SeismicSource.count_ruptures`.
        """
        whole_fault_surface = SimpleFaultSurface.from_fault_data(
            self.fault_trace, self.upper_seismogenic_depth,
            self.lower_seismogenic_depth, self.dip, self.rupture_mesh_spacing
        )
        whole_fault_mesh = whole_fault_surface.get_mesh()
        mesh_rows, mesh_cols = whole_fault_mesh.shape
        fault_length = float((mesh_cols - 1) * self.rupture_mesh_spacing)
        fault_width = float((mesh_rows - 1) * self.rupture_mesh_spacing)
        counts = 0
        for (mag, mag_occ_rate) in self.get_annual_occurrence_rates():
            rup_cols, rup_rows = self._get_rupture_dimensions(
                fault_length, fault_width, mag
            )
            num_rup_along_length = mesh_cols - rup_cols + 1
            num_rup_along_width = mesh_rows - rup_rows + 1
            counts += num_rup_along_length * num_rup_along_width
        return counts

    def _get_rupture_dimensions(self, fault_length, fault_width, mag):
        """
        Calculate rupture dimensions for a given magnitude.

        :param fault_length:
            The length of the fault as a sum of all segments, in km.
        :param fault_width:
            The width of the fault, in km.
        :param mag:
            Magnitude value to calculate rupture geometry for.
        :returns:
            A tuple of two integer items, representing rupture's dimensions:
            number of mesh points along length and along width respectively.

        The rupture is reshaped (conserving area, if possible) if one
        of dimensions exceeds fault geometry. If both do, the rupture
        is considered to cover the whole fault.
        """
        area = self.magnitude_scaling_relationship.get_median_area(
            mag, self.rake
        )
        rup_length = math.sqrt(area * self.rupture_aspect_ratio)
        rup_width = area / rup_length

        # clip rupture's length and width to fault's length and width
        # if there is no way to fit the rupture otherwise
        if area >= fault_length * fault_width:
            rup_length = fault_length
            rup_width = fault_width
        # reshape rupture (conserving area) if its length or width
        # exceeds fault's length or width
        elif rup_width > fault_width:
            rup_length = rup_length * (rup_width / fault_width)
            rup_width = fault_width
        elif rup_length > fault_length:
            rup_width = rup_width * (rup_length / fault_length)
            rup_length = fault_length

        # round rupture dimensions with respect to mesh_spacing
        # and compute number of points in the rupture along length
        # and width (aka strike and dip)
        rup_cols = int(round(rup_length / self.rupture_mesh_spacing) + 1)
        rup_rows = int(round(rup_width / self.rupture_mesh_spacing) + 1)
        return rup_cols, rup_rows
