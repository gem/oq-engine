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
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.geo.geodetic import point_at
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
    def get_surface(self, msr=None, asr=1.0, mag=6.0, rake=90, dip=90):
        """
        Create a rupture surface. The strike is NS, and the dip direction is
        east.

        :param msr:
            An instance of a magnitude scaling relationship.
        :param asr:
            Aspect ratio
        """
        # Set msr
        if msr is None:
            msr = WC1994()
        # set hypocenter
        hyp = Line([Point(0, 0.5)])
        # set rupture trace
        area = msr.get_median_area(mag, rake)
        rup_wdt = (area / asr)**0.5
        rup_len = rup_wdt * asr
        south = point_at(hyp.longitude, hyp.latitude, 180, rup_len/2)
        north = point_at(hyp.longitude, hyp.latitude, 0, rup_len/2)
        trc = Line([south, north])
        lsd = np.cos(90.-dip) * rup_wdt + 5.
        sfc = SimpleFaultSurface.from_fault_data(fault_trace=trc,
                                                 upper_seismogenic_depth=0,
                                                 lower_seismogenic_depth=lsd,
                                                 dip=dip,
                                                 mesh_spacing=10.)
        return sfc, hyp

    @classmethod
    def get_rupture(self, **kwargs):
        """
        Returns a rupture
        """
        # Parameters
        asr = kwargs['asr'] if 'asr' in kwargs else 1.0
        dip = kwargs['dip'] if 'dip' in kwargs else 90.0
        mag = kwargs['mag'] if 'mag' in kwargs else None
        msr = kwargs['msr'] if 'msr' in kwargs else None
        rake = kwargs['rake'] if 'rake' in kwargs else None
        trt = kwargs['trt'] if 'trt' in kwargs else None
        # Get surface
        sfc, hyp = self.get_surface(msr, asr, mag, rake, dip)
        # Create rupture
        rup = BaseRupture(mag, rake, trt, hyp, sfc)
        # Return rupture
        return rup
