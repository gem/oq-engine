# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

# pylint: disable=W0232

"""
This module performs hazard calculations using the deterministic
event based approach.
"""

from openquake import java
from openquake import kvs
from openquake import shapes
from openquake.hazard import job


class DeterministicEventBasedMixin:
    """Deterministic Event Based method for performing hazard calculations.

    Note that this mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the job configuration file."""

    def execute(self):
        """Entry point for triggering the computation."""

        number_of_calculations = self.params["NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS"]

        for i in xrange(number_of_calculations):
            gmf = self.compute_ground_motion_field()
            gmf_as_dict = gmf_to_dict(gmf)
            
            for gmv in gmf_as_dict:
                site = shapes.Site(gmv["site_lon"], gmv["site_lat"])
                
                kvs.set_value_json_encoded(
                    kvs.tokens.ground_motion_value_key(
                    self.job_id, site.hash(), i + 1), gmv)

        return [True]

# TODO (ac): Stubbed for now, needs to call the Java calculator
    def compute_ground_motion_field(self):
        hashmap = java.jclass("HashMap")()

        for site in self.sites_for_region():
            location = java.jclass("Location")(site.latitude, site.longitude)
            site = java.jclass("Site")(location)
            hashmap.put(site, 0.5)

        return hashmap


def gmf_to_dict(hashmap):
    gmf = []
    
    for site in hashmap.keySet():
        mag = hashmap.get(site).doubleValue()
        lat = site.getLocation().getLatitude()
        lon = site.getLocation().getLongitude()
        
        gmv = {"site_lat": lat, "site_lon": lon, "mag": mag}
        gmf.append(gmv)

    return gmf


job.HazJobMixin.register(
    "Deterministic", DeterministicEventBasedMixin, order=2)
