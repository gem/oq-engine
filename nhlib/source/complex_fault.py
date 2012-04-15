# nhlib: A New Hazard Library
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
Module :mod:`nhlib.source.complex_fault` defines :class:`ComplexFaultSource`.
"""
import numpy

from nhlib.source.base import SeismicSource
from nhlib.geo.surface.complex_fault import ComplexFaultSurface
from nhlib.geo.nodalplane import NodalPlane
from nhlib.source.rupture import ProbabilisticRupture


class ComplexFaultSource(SeismicSource):
    """
    Complex fault source typology represents seismicity occurring on a fault
    surface with an arbitrarily complex geometry.

    :param edges:
        A list of :class:`~nhlib.geo.line.Line` objects, representing fault
        source geometry. See
        :meth:`nhlib.geo.surface.complex_fault.ComplexFaultSurface.from_fault_data`.
    :param rake:
        Angle describing rupture propagation direction in decimal degrees.

    See also :class:`nhlib.source.base.SeismicSource` for description of other
    parameters.

    :raises ValueError:
        If :meth:`ComplexFaultSurface.check_fault_data` fails or if rake value
        is invalid.
    """
    def __init__(self, source_id, name, tectonic_region_type,
                 mfd, rupture_mesh_spacing,
                 magnitude_scaling_relationship, rupture_aspect_ratio,
                 # complex fault specific parameters
                 edges, rake):
        super(ComplexFaultSource, self).__init__(
            source_id, name, tectonic_region_type, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio
        )

        NodalPlane.check_rake(rake)
        ComplexFaultSurface.check_fault_data(edges, rupture_mesh_spacing)
        self.edges = edges
        self.rake = rake

    def iter_ruptures(self, temporal_occurrence_model):
        """
        See :meth:`nhlib.source.base.SeismicSource.iter_ruptures`.
        """
        # TODO: unittest
        # TODO: document better
        whole_fault_surface = ComplexFaultSurface.from_fault_data(
            self.edges, self.rupture_mesh_spacing
        )
        whole_fault_mesh = whole_fault_surface.get_mesh()
        cell_center, cell_length, cell_width, cell_area = (
            whole_fault_mesh.get_cell_dimensions()
        )
        cell_area = cell_area.reshape(cell_area.shape + (1, ))
        total_area = numpy.sum(cell_area)

        for (mag, mag_occ_rate) in self.mfd.get_annual_occurrence_rates():
            rupture_area = self.magnitude_scaling_relationship.get_median_area(
                mag, self.rake
            )

            rupture_slices = self._float_ruptures(rupture_area, cell_area,
                                                  cell_length, total_area)
            occurrence_rate = mag_occ_rate / float(len(rupture_slices))

            for rupture_slice in rupture_slices:
                mesh = whole_fault_mesh[rupture_slice]
                # XXX: use surface centroid as rupture's hypocenter
                # XXX: instead of point with middle index
                hypocenter = mesh.get_middle_point()
                surface = ComplexFaultSurface(mesh)
                yield ProbabilisticRupture(
                    mag, self.rake, self.tectonic_region_type, hypocenter,
                    surface, occurrence_rate, temporal_occurrence_model
                )

    def _float_ruptures(self, rupture_area, cell_area, cell_length, total_area):
        # TODO: document
        # TODO: clean up
        nrows, ncols = cell_length.shape

        if rupture_area >= total_area:
            return [slice(None)]

        rupture_length = numpy.sqrt(rupture_area * self.rupture_aspect_ratio)
        rupture_slices = []

        first_col = 0
        for row in xrange(nrows):
            for col in xrange(first_col, ncols):
                lengths_acc = numpy.add.accumulate(
                    cell_length[row, col:]
                )
                rup_cols = numpy.argmin(numpy.abs(lengths_acc - rupture_length))
                last_col = rup_cols + col + 1
                if last_col == ncols and lengths_acc[rup_cols] < rupture_length:
                    # rupture doesn't fit along length
                    if col != 0:
                        # go to the next row
                        break

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
                            rup_cols = numpy.argmin(numpy.abs(areas_acc - rupture_area))
                            last_col = rup_cols + col + 1
                            if last_col == ncols and areas_acc[rup_cols] < rupture_area:
                                # still doesn't fit, return
                                return rupture_slices
                    else:
                        # row is not the first
                        first_col += 1

                rupture_slices.append((slice(row, last_row + 1),
                                       slice(col, last_col + 1)))
        return rupture_slices
