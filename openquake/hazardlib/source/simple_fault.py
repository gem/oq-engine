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
Module :mod:`openquake.hazardlib.source.simple_fault` defines
:class:`SimpleFaultSource`.
"""
from __future__ import division
import math
from openquake.baselib.python3compat import range, round
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.baselib.slots import with_slots


@with_slots
class SimpleFaultSource(ParametricSeismicSource):
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
        the direction of hanging wall relative to the foot wall.
    :param rupture_slip_direction:
        Angle describing rupture propagation direction in decimal degrees.
    :param hypo_list:
        Array describing the relative position of the hypocentre on the rupture
        surface. Each line represents a hypocentral position defined in terms
        of the relative distance along strike and dip (from the upper, left
        corner of the fault surface i.e. the corner which results from the
        projection at depth of the first vertex of the fault trace) and the
        corresponding weight. Example 1: one single hypocentral position at the
        center of the rupture will be described by the following
        array[(0.5, 0.5, 1.0)]. Example 2: two possible hypocenters are
        admitted for a rupture. One hypocentre is located along the strike at
        1/4 of the fault length and at 1/4 of the fault width along the dip and
        occurs with a weight of 0.3, the other one is at 3/4 of fault length
        along strike and at 3/4 of fault width along strike with a weight of
        0.7. The numpy array would be entered as numpy.array([[0.25, 0.25, 0.3],
        [0.75, 0.75, 0.7]]).
    :param slip_list:
        Array describing the rupture slip direction, which desribes the rupture
        propagation direction on the rupture surface. Each line represents a
        rupture slip direction and the corresponding weight. Example 1: one
        single rupture slip direction with angle 90 degree will be described
        by the following array[(90, 1.0)]. Example 2: two possible rupture slip
        directions are admitted for a rupture. One slip direction is at 90
        degree with a weight of 0.7, the other one is at 135 degree with a
        weight of 0.3. The numpy array would be entered as numpy.array(
        [[90, 0.7], [135, 0.3]]).

    See also :class:`openquake.hazardlib.source.base.ParametricSeismicSource`
    for description of other parameters.

    :raises ValueError:
        If :meth:`~openquake.hazardlib.geo.surface.simple_fault.SimpleFaultSurface.check_fault_data`
        fails, if rake value is invalid and if rupture mesh spacing is too high
        for the lowest magnitude value.
    """
    _slots_ = ParametricSeismicSource._slots_ + '''upper_seismogenic_depth
    lower_seismogenic_depth fault_trace dip rake hypo_list
    slip_list'''.split()

    MODIFICATIONS = set(('set_geometry',
                         'adjust_dip',
                         'set_dip'))

    def __init__(self, source_id, name, tectonic_region_type,
                 mfd, rupture_mesh_spacing,
                 magnitude_scaling_relationship, rupture_aspect_ratio,
                 temporal_occurrence_model,
                 # simple fault specific parameters
                 upper_seismogenic_depth, lower_seismogenic_depth,
                 fault_trace, dip, rake, hypo_list=(), slip_list=()):
        super(SimpleFaultSource, self).__init__(
            source_id, name, tectonic_region_type, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio,
            temporal_occurrence_model
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

        min_mag, max_mag = self.mfd.get_min_max_mag()
        cols_rows = self._get_rupture_dimensions(float('inf'), float('inf'),
                                                 min_mag)
        self.slip_list = slip_list
        self.hypo_list = hypo_list

        if (len(self.hypo_list) and not len(self.slip_list) or
           not len(self.hypo_list) and len(self.slip_list)):
            raise ValueError('hypo_list and slip_list have to be both given '
                             'or neither given')

        if 1 in cols_rows:
            raise ValueError('mesh spacing %s is too high to represent '
                             'ruptures of magnitude %s' %
                             (rupture_mesh_spacing, min_mag))

    def get_rupture_enclosing_polygon(self, dilation=0):
        """
        Uses :meth:`openquake.hazardlib.geo.surface.simple_fault.SimpleFaultSurface.surface_projection_from_fault_data`
        for getting the fault's surface projection and then calls
        its :meth:`~openquake.hazardlib.geo.polygon.Polygon.dilate`
        method passing in ``dilation`` parameter.

        See :meth:`superclass method
        <openquake.hazardlib.source.base.BaseSeismicSource.get_rupture_enclosing_polygon>`
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

    def iter_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.iter_ruptures`.

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

            for first_row in range(num_rup_along_width):
                for first_col in range(num_rup_along_length):
                    mesh = whole_fault_mesh[first_row: first_row + rup_rows,
                                            first_col: first_col + rup_cols]

                    if not len(self.hypo_list) and not len(self.slip_list):

                        hypocenter = mesh.get_middle_point()
                        occurrence_rate_hypo = occurrence_rate
                        surface = SimpleFaultSurface(mesh)

                        yield ParametricProbabilisticRupture(
                            mag, self.rake, self.tectonic_region_type,
                            hypocenter, surface, type(self),
                            occurrence_rate_hypo,
                            self.temporal_occurrence_model
                        )
                    else:
                        for hypo in self.hypo_list:
                            for slip in self.slip_list:
                                surface = SimpleFaultSurface(mesh)
                                hypocenter = surface.get_hypo_location(
                                    self.rupture_mesh_spacing, hypo[:2])
                                occurrence_rate_hypo = occurrence_rate * \
                                    hypo[2] * slip[1]
                                rupture_slip_direction = slip[0]

                                yield ParametricProbabilisticRupture(
                                    mag, self.rake, self.tectonic_region_type,
                                    hypocenter, surface, type(self),
                                    occurrence_rate_hypo,
                                    self.temporal_occurrence_model,
                                    rupture_slip_direction
                                )

    # TODO: fix the count in the case of hypo_list and slip_list
    def count_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.count_ruptures`.
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
                fault_length, fault_width, mag)
            num_rup_along_length = mesh_cols - rup_cols + 1
            num_rup_along_width = mesh_rows - rup_rows + 1
            counts += num_rup_along_length * num_rup_along_width
            n_hypo = len(self.hypo_list) or 1
            n_slip = len(self.slip_list) or 1
        return counts * n_hypo * n_slip

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
            mag, self.rake)
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

    def modify_set_geometry(self, fault_trace, upper_seismogenic_depth,
                            lower_seismogenic_depth, dip, spacing):
        """
        Modifies the current source geometry including trace, seismogenic
        depths and dip
        """
        # Check the new geometries are valid
        SimpleFaultSurface.check_fault_data(
            fault_trace, upper_seismogenic_depth, lower_seismogenic_depth,
            dip, spacing
        )
        self.fault_trace = fault_trace
        self.upper_seismogenic_depth = upper_seismogenic_depth
        self.lower_seismogenic_depth = lower_seismogenic_depth
        self.dip = dip
        self.rupture_mesh_spacing = spacing

    def modify_adjust_dip(self, increment):
        """
        Modifies the dip by an incremental value

        :param float increment:
            Value by which to increase or decrease the dip (the resulting
            dip must still be within 0.0 to 90.0 degrees)
        """
        SimpleFaultSurface.check_fault_data(
            self.fault_trace, self.upper_seismogenic_depth,
            self.lower_seismogenic_depth, self.dip + increment,
            self.rupture_mesh_spacing
        )
        self.dip += increment

    def modify_set_dip(self, dip):
        """
        Modifies the dip to the specified value

        :param float dip:
            New value of dip (must still be within 0.0 to 90.0 degrees)
        """
        SimpleFaultSurface.check_fault_data(
            self.fault_trace, self.upper_seismogenic_depth,
            self.lower_seismogenic_depth, dip, self.rupture_mesh_spacing
        )
        self.dip = dip
