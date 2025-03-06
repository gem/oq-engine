# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
Module :mod:`openquake.hazardlib.source.complex_fault`
defines :class:`ComplexFaultSource`.
"""
import copy
import numpy

from openquake.hazardlib import mfd
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.geo.surface.complex_fault import ComplexFaultSurface
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture

MINWEIGHT = 100


def _float_ruptures(rupture_area, rupture_length, cell_area, cell_length):
    """
    Get all possible unique rupture placements on the fault surface.

    :param rupture_area:
        The area of the rupture to float on the fault surface, in squared km.
    :param rupture_length:
        The target length (spatial extension along fault trace) of the rupture,
        in km.
    :param cell_area:
        2d numpy array representing area of mesh cells in squared km.
    :param cell_length:
        2d numpy array of the shape as ``cell_area`` representing cells'
        length in km.
    :returns:
        A list of slice objects. Number of items in the list is equal to number
        of possible locations of the requested rupture on the fault surface.
        Each slice can be used to get a portion of the whole fault surface mesh
        that would represent the location of the rupture.
    """
    nrows, ncols = cell_length.shape

    if rupture_area >= numpy.sum(cell_area):
        # requested rupture area exceeds the total surface area.
        # return the single slice that doesn't cut anything out.
        return [slice(None)]

    rupture_slices = []

    dead_ends = set()
    for row in range(nrows):
        for col in range(ncols):
            if col in dead_ends:
                continue
            # find the lengths of all possible subsurfaces containing
            # only the current row and from the current column till
            # the last one.
            lengths_acc = numpy.add.accumulate(cell_length[row, col:])
            # find the "best match" number of columns, the one that gives
            # the least difference between actual and requested rupture
            # length (note that we only consider top row here, mainly
            # for simplicity: it's not yet clear how many rows will we
            # end up with).
            rup_cols = numpy.argmin(numpy.abs(lengths_acc - rupture_length))
            last_col = rup_cols + col + 1
            if last_col == ncols and lengths_acc[rup_cols] < rupture_length:
                # rupture doesn't fit along length (the requested rupture
                # length is greater than the length of the part of current
                # row that starts from the current column).
                if col != 0:
                    # if we are not in the first column, it means that we
                    # hit the right border, so we need to go to the next
                    # row.
                    break

            # now try to find the optimum (the one providing the closest
            # to requested area) number of rows.
            areas_acc = numpy.sum(cell_area[row:, col:last_col], axis=1)
            areas_acc = numpy.add.accumulate(areas_acc, axis=0)
            rup_rows = numpy.argmin(numpy.abs(areas_acc - rupture_area))
            last_row = rup_rows + row + 1
            if last_row == nrows and areas_acc[rup_rows] < rupture_area:
                # rupture doesn't fit along width.
                # we can try to extend it along length but only if we are
                # at the first row
                if row == 0:
                    if last_col == ncols:
                        # there is no place to extend, exiting
                        return rupture_slices
                    else:
                        # try to extend along length
                        areas_acc = numpy.sum(cell_area[:, col:], axis=0)
                        areas_acc = numpy.add.accumulate(areas_acc, axis=0)
                        rup_cols = numpy.argmin(
                            numpy.abs(areas_acc - rupture_area))
                        last_col = rup_cols + col + 1
                        if last_col == ncols \
                                and areas_acc[rup_cols] < rupture_area:
                            # still doesn't fit, return
                            return rupture_slices
                else:
                    # row is not the first and the required area exceeds
                    # available area starting from target row and column.
                    # mark the column as "dead end" so we don't create
                    # one more rupture from the same column on all
                    # subsequent rows.
                    dead_ends.add(col)

            # here we add 1 to last row and column numbers because we want
            # to return slices for cutting the mesh of vertices, not the cell
            # data (like cell_area or cell_length).
            rupture_slices.append((slice(row, last_row + 1),
                                   slice(col, last_col + 1)))
    return rupture_slices


class ComplexFaultSource(ParametricSeismicSource):
    """
    Complex fault source typology represents seismicity occurring on a fault
    surface with an arbitrarily complex geometry.

    :param edges:
        A list of :class:`~openquake.hazardlib.geo.line.Line` objects,
        representing fault source geometry. See
        :meth:`openquake.hazardlib.geo.surface.complex_fault.ComplexFaultSurface.from_fault_data`.
    :param rake:
        Angle describing rupture propagation direction in decimal degrees.

    See also :class:`openquake.hazardlib.source.base.ParametricSeismicSource`
    for description of other parameters.

    :raises ValueError:
        If :meth:`~openquake.hazardlib.geo.surface.complex_fault.ComplexFaultSurface.check_fault_data`
        fails or if rake value is invalid.
    """
    code = b'C'
    # a slice of the rupture_slices, thus splitting the source
    MODIFICATIONS = {'set_geometry', 'adjust_mfd_from_slip'}

    def __init__(self, source_id, name, tectonic_region_type, mfd,
                 rupture_mesh_spacing, magnitude_scaling_relationship,
                 rupture_aspect_ratio, temporal_occurrence_model,
                 # complex fault specific parameters
                 edges, rake):
        super().__init__(
            source_id, name, tectonic_region_type, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio,
            temporal_occurrence_model)
        NodalPlane.check_rake(rake)
        ComplexFaultSurface.check_fault_data(edges, rupture_mesh_spacing)
        self.edges = edges
        self.rake = rake

    def get_fault_surface_area(self):
        """
        Computes the area covered by the surface of the fault.

        :returns:
            A float defining the area of the surface of the fault [km^2]
        """
        # The mesh spacing is hardcoded to guarantee stability in the values
        # computed
        sfc = ComplexFaultSurface.from_fault_data(self.edges, 2.0)
        return sfc.get_area()

    def iter_ruptures(self, **kwargs):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.iter_ruptures`.

        Uses :func:`_float_ruptures` for finding possible rupture locations
        on the whole fault surface.
        """
        step = kwargs.get('step', 1)
        whole_fault_surface = ComplexFaultSurface.from_fault_data(
            self.edges, self.rupture_mesh_spacing)
        if step > 1:  # do the expensive check only in preclassical
            whole_fault_surface.check_proj_polygon()
        whole_fault_mesh = whole_fault_surface.mesh
        _cell_center, cell_length, _cell_width, cell_area = (
            whole_fault_mesh.get_cell_dimensions())
        for mag, mag_occ_rate in self.get_annual_occurrence_rates()[::step]:
            rupture_area = self.magnitude_scaling_relationship.get_median_area(
                mag, self.rake)
            rupture_length = numpy.sqrt(
                rupture_area * self.rupture_aspect_ratio)
            rupture_slices = _float_ruptures(
                rupture_area, rupture_length, cell_area, cell_length)
            occurrence_rate = mag_occ_rate / float(len(rupture_slices))
            for rupture_slice in rupture_slices[::step**2]:
                mesh = whole_fault_mesh[rupture_slice]
                # XXX: use surface centroid as rupture's hypocenter
                # XXX: instead of point with middle index
                hypocenter = mesh.get_middle_point()
                try:
                    surface = ComplexFaultSurface(mesh)
                except ValueError as e:
                    raise ValueError("Invalid source with id=%s. %s" % (
                        self.source_id, str(e)))
                rup = ParametricProbabilisticRupture(
                    mag, self.rake, self.tectonic_region_type, hypocenter,
                    surface, occurrence_rate, self.temporal_occurrence_model)
                rup.mag_occ_rate = mag_occ_rate
                yield rup

    def count_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.count_ruptures`.
        """
        if self.num_ruptures:
            return self.num_ruptures
        whole_fault_surface = ComplexFaultSurface.from_fault_data(
            self.edges, self.rupture_mesh_spacing)
        whole_fault_mesh = whole_fault_surface.mesh
        _cell_center, cell_length, _cell_width, cell_area = (
            whole_fault_mesh.get_cell_dimensions())
        self._nr = []
        for (mag, mag_occ_rate) in self.get_annual_occurrence_rates():
            if mag_occ_rate == 0:
                continue
            rupture_area = self.magnitude_scaling_relationship.get_median_area(
                mag, self.rake)
            rupture_length = numpy.sqrt(
                rupture_area * self.rupture_aspect_ratio)
            rupture_slices = _float_ruptures(
                rupture_area, rupture_length, cell_area, cell_length)
            self._nr.append(len(rupture_slices))
        return sum(self._nr)

    def modify_set_geometry(self, edges, spacing):
        """
        Modifies the complex fault geometry
        """
        ComplexFaultSurface.check_fault_data(edges, spacing)
        self.edges = edges
        self.rupture_mesh_spacing = spacing

    def __iter__(self):
        mag_rates = self.get_annual_occurrence_rates()
        if len(mag_rates) == 1:  # not splittable
            yield self
            return
        self.count_ruptures()
        for i, (mag, rate) in enumerate(mag_rates):
            src = copy.copy(self)
            src.mfd = mfd.ArbitraryMFD([mag], [rate])
            src.num_ruptures = self._nr[i]
            src.source_id = '%s:%d' % (self.source_id, i)
            yield src

    @property
    def polygon(self):
        """
        The underlying polygon
        `"""
        return ComplexFaultSurface.surface_projection_from_fault_data(
            self.edges)

    def wkt(self):
        """
        :returns: the geometry as a WKT string
        """
        return self.polygon.wkt
