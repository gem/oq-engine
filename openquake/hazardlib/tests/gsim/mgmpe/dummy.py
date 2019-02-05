# The Hazard Library
# Copyright (C) 2012-2018 GEM Foundation
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

import numpy as np
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source.rupture import BaseRupture


class Dummy:

    @classmethod
    def get_site_collection(cls, nelements, **kwargs):
        """
        Returns a site collection.

        :param int nelements:
            Number of sites included in the site collection
        """
        sites = []
        for n in range(nelements):
            s = Site(Point(0, 0))
            for key in kwargs:
                if np.size(kwargs[key]) > 1:
                    setattr(s, key, kwargs[key][n])
                else:
                    setattr(s, key, kwargs[key])
            sites.append(s)
        return SiteCollection(sites)

    @classmethod
    def get_surface(self):
        """ """
        hyp = Line([Point(0, 0.5)])
        trc = Line([Point(0, 0), Point(0, 1)])
        sfc = SimpleFaultSurface.from_fault_data(fault_trace=trc,
                                                 upper_seismogenic_depth=0,
                                                 lower_seismogenic_depth=15,
                                                 dip=90.,
                                                 mesh_spacing=10.)
        return sfc, hyp

    @classmethod
    def get_rupture(self, **kwargs):
        """
        """
        # Parameters
        if 'mag' in kwargs:
            mag = kwargs['mag']
        else:
            mag = 6.0
        if 'rake' in kwargs:
            rake = kwargs['rake']
        else:
            rake = 0
        if 'trt' in kwargs:
            trt = kwargs['trt']
        else:
            trt = 0
        # Get surface
        sfc, hyp = self.get_surface()
        # Create rupture
        rup = BaseRupture(mag, rake, trt, hyp, sfc)
        # Set attributes
        return rup
