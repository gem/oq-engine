# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
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
Module :mod:`openquake.hazardlib.source.characteristic` defines
:class:`CharacteristicFaultSource`.
"""
import numpy

from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.geo.mesh import RectangularMesh
from openquake.hazardlib.geo import NodalPlane
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.baselib.slots import with_slots


@with_slots
class CharacteristicFaultSource(ParametricSeismicSource):
    """
    Characteristic source typology represents seismicity occuring on a generic
    fault surface with seismic events rupturing the entire fault surface
    independently of their magnitude values.

    Characteristic source typology can be used to model individual faults
    or fault segments that tend to produce essentialy same size earthquakes
    (see for instance: Schwartz, D. P., K. J. Coppersmith, Fault behavior and
    characteristic earthquakes: Examples from the Wasatch and San Andreas fault
    zones, J. Geophys. Res., 89, 5681-5698, 1984)

    :param surface:
        Fault surface, see :mod:`openquake.hazardlib.geo.surface`.
    :param rake:
        Angle describing rupture propagation direction in decimal degrees.

    See also :class:`openquake.hazardlib.source.base.ParametricSeismicSource`
    for description of other parameters.

    Note that a ``CharacteristicFaultSource`` does not need any mesh spacing,
    magnitude scaling relationship, and aspect ratio, therefore the constructor
    sets these parameters to ``None``.

    NB: if you want to convert a characteristic source into XML, you must set
    its attribute `surface_node` to an explicit representation of the surface
    as a LiteralNode object.
    """
    _slots_ = ParametricSeismicSource._slots_ + 'surface rake'.split()

    MODIFICATIONS = set(('set_geometry',))

    def __init__(self, source_id, name, tectonic_region_type,
                 mfd, temporal_occurrence_model, surface, rake,
                 surface_node=None):
        super(CharacteristicFaultSource, self).__init__(
            source_id, name, tectonic_region_type, mfd, None, None, None,
            temporal_occurrence_model
        )
        NodalPlane.check_rake(rake)
        self.surface = surface
        self.rake = rake

    def get_rupture_enclosing_polygon(self, dilation=0):
        """
        Uses :meth:
        `openquake.hazardlib.geo.surface.base.BaseSurface.get_bounding_box()`
        and from bounding box coordinates create
        :class:`openquake.hazardlib.geo.mesh.RectangularMesh` and then calls
        :meth:`openquake.hazardlib.geo.mesh.Mesh.get_convex_hull()` to get a
        polygon representation of the bounding box. Note that this is needed
        to cope with the situation of a vertical rupture for which the bounding
        box collapses to a line. In this case the method ``get_convex_hull()``
        returns a valid polygon obtained by expanding the line by a small
        distance. Finally, a polygon is returned by calling
        :meth:`~openquake.hazardlib.geo.polygon.Polygon.dilate` passing in the
        ``dilation`` parameter.

        See :meth:`superclass method
        <openquake.hazardlib.source.base.BaseSeismicSource.get_rupture_enclosing_polygon>`
        for parameter and return value definition.
        """
        west, east, north, south = self.surface.get_bounding_box()
        mesh = RectangularMesh(numpy.array([[west, east], [west, east]]),
                               numpy.array([[north, north], [south, south]]),
                               None)
        poly = mesh.get_convex_hull()

        return poly.dilate(dilation)

    def iter_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.iter_ruptures`.

        For each magnitude value in the given MFD, return an earthquake
        rupture with a surface always equal to the given surface.
        """
        hypocenter = self.surface.get_middle_point()
        for (mag, occurrence_rate) in self.get_annual_occurrence_rates():
            yield ParametricProbabilisticRupture(
                mag, self.rake, self.tectonic_region_type, hypocenter,
                self.surface, type(self), occurrence_rate,
                self.temporal_occurrence_model
            )

    def count_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.count_ruptures`.
        """
        return len(self.get_annual_occurrence_rates())

    def modify_set_geometry(self, surface, surface_node=None):
        """
        Modifies the current fault geometry

        :param surface:
            Fault surface, see :mod:`openquake.hazardlib.geo.surface`.

        :param surface_node:
            If needed for export, provide the surface as a LiteralNode object
        """
        self.surface = surface
        self.surface_node = surface_node
