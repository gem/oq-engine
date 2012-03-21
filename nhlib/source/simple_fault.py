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
Module :mod:`nhlib.source.simple_fault` defines :class:`SimpleFaultSource`.
"""
import math

from nhlib.source.base import SeismicSource
from nhlib.geo.surface.simple_fault import SimpleFaultSurface
from nhlib.source.rupture import ProbabilisticRupture


class SimpleFaultSource(SeismicSource):
    # TODO: document
    # TODO: unittest
    def __init__(self, source_id, name, tectonic_region_type, mfd,
                 rupture_mesh_spacing, fault_trace, upper_seismogenic_depth,
                 lower_seismogenic_depth, dip, rake,
                 magnitude_scaling_relationship, rupture_aspect_ratio):
        super(SimpleFaultSource, self).__init__(source_id, name,
                                                tectonic_region_type, mfd,
                                                rupture_mesh_spacing)

        if upper_seismogenic_depth < 0:
            raise ValueError('upper seismogenic depth must be non-negative')

        if not lower_seismogenic_depth > upper_seismogenic_depth:
            raise ValueError('lower seismogenic depth must be below '
                             'upper seismogenic depth')

        if not rupture_aspect_ratio > 0:
            raise ValueError('rupture aspect ratio must be positive')

        self.fault_trace = fault_trace
        self.upper_seismogenic_depth = upper_seismogenic_depth
        self.lower_seismogenic_depth = lower_seismogenic_depth
        self.magnitude_scaling_relationship = magnitude_scaling_relationship
        self.rupture_aspect_ratio = rupture_aspect_ratio
        self.dip = dip
        self.rake = rake

    def iter_ruptures(self, temporal_occurrence_model):
        """
        See :meth:`nhlib.source.base.SeismicSource.iter_ruptures`.
        """
        # TODO: document better

        # TODO: move creation of the mesh from SimpleFaultSurface
        # TODO: to SimpleFaultSource, make surface class accept mesh
        whole_fault_mesh = SimpleFaultSurface(
            self.fault_trace, self.upper_seismogenic_depth,
            self.lower_seismogenic_depth, self.dip, self.rupture_mesh_spacing
        ).get_mesh()

        mesh_rows, mesh_cols = whole_fault_mesh.shape
        fault_length = (mesh_cols - 1) * self.rupture_mesh_spacing
        fault_width = (mesh_rows - 1) * self.rupture_mesh_spacing

        for (mag, mag_occ_rate) in self.mfd.get_annual_occurrence_rates():
            # compute rupture dimensions
            area = self.magnitude_scaling_relationship.get_median_area(
                mag, self.rake
            )
            rup_length = math.sqrt(area * self.rupture_mesh_spacing)
            rup_width = area / rup_length

            # clip rupture's length and width to
            # fault's length and width if both rupture
            # dimensions are greater than fault dimensions
            if rup_length > fault_length and rup_width > fault_width:
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
            # and strike
            rup_cols = round(rup_length / self.rupture_mesh_spacing) + 1
            rup_rows = round(rup_width / self.rupture_mesh_spacing) + 1
            rup_length = (rup_cols - 1) * self.rupture_mesh_spacing
            rup_width = (rup_rows - 1) * self.rupture_mesh_spacing

            num_rup_along_length = mesh_cols - rup_cols + 1
            num_rup_along_width = mesh_rows - rup_rows + 1
            num_rup = num_rup_along_length * num_rup_along_width

            occurrence_rate = mag_occ_rate / float(num_rup)

            for first_col in xrange(num_rup_along_length):
                for first_row in xrange(num_rup_along_width):
                    mesh = whole_fault_mesh[first_row : first_row + rup_rows,
                                            first_col : first_col + rup_cols]
                    hypocenter = mesh.get_middle_point()
                    # TODO: create a surface from a mesh
                    surface = None
                    yield ProbabilisticRupture(
                        mag, self.rake, self.tectonic_region_type, hypocenter,
                        surface, occurrence_rate, temporal_occurrence_model
                    )
