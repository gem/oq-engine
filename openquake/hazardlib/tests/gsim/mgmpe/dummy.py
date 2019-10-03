# The Hazard Library
# Copyright (C) 2012-2019 GEM Foundation
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
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.geo.geodetic import point_at


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
            if 'hyp_lon' in kwargs.keys() and 'hyp_lat' in kwargs.keys():
                s = Site(Point(kwargs['hyp_lon'], kwargs['hyp_lat']))
            else:
                s = Site(Point(0, 0))
            for key in kwargs:
                if np.size(kwargs[key]) > 1:
                    setattr(s, key, kwargs[key][n])
                else:
                    setattr(s, key, kwargs[key])
            sites.append(s)
        return SiteCollection(sites)

    @classmethod
    def get_surface(self, hyp_lon=0.0, hyp_lat=0.5, mag=None, asp_ratio=None, **kwargs):
        """ """
        hyp = Line([Point(hyp_lon, hyp_lat)])
        # Set mesh spacing
        if 'mesh_spacing' in kwargs:
            mesh_spacing = kwargs['mesh_spacing']
        else:
            mesh_spacing = 10.
        # Set aspect ratio
        if asp_ratio is None:
            asp_ratio = 1.5
        # Set trace
        if mag is None:
            trc = Line([Point(0, 0), Point(0, 1)])
        else:
            msr = WC1994()
            len = (msr.get_median_area(mag, 0.0)*asp_ratio)**0.5
            pnt1 = point_at(hyp_lon, hyp_lat, 180, len/2)
            pnt2 = point_at(hyp_lon, hyp_lat, 0, len/2)
            trc = Line([Point(pnt1[0], pnt1[1]), Point(pnt2[0], pnt2[1])])

        sfc = SimpleFaultSurface.from_fault_data(fault_trace=trc,
                                                 upper_seismogenic_depth=0,
                                                 lower_seismogenic_depth=15,
                                                 dip=90.,
                                                 mesh_spacing=mesh_spacing)
        return sfc, hyp

    @classmethod
    def get_rupture(self, **kwargs):
        """
        """
        # Set magnitude
        if 'mag' in kwargs:
            mag = kwargs['mag']
        else:
            mag = 6.0
        # Set rake
        if 'rake' in kwargs:
            rake = kwargs['rake']
        else:
            rake = 0
        # Set tectonic region
        if 'trt' in kwargs:
            trt = kwargs['trt']
        else:
            trt = 0
        # Get surface
        if 'surface' in kwargs:
            sfc = kwargs['surface']
        else:
            if 'hyp_lon' in kwargs and 'hyp_lat' in kwargs:
                hyp_lon = kwargs['hyp_lon']
                hyp_lat = kwargs['hyp_lat']
            else:
                hyp_lon = 0.0
                hyp_lat = 0.0
            sfc, hyp = self.get_surface(mag=mag, hyp_lon=hyp_lon,
                                        hyp_lat=hyp_lat)

        # Create rupture
        rup = BaseRupture(mag, rake, trt, hyp, sfc)

        # Set attributes
        return rup
