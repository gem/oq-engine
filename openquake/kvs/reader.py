# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# This file is part of OpenQuake.
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

""" Read objects from kvs and translate them into our object model. """

import json
import math
from openquake import shapes

class Reader(object):
    """Read objects from kvs and translate them into
    our object model.
    """
    
    def __init__(self, client):
        self.client = client
    
    def _check_key_in_cache(self, key):
        """Raise an error if the given key is not in kvs."""
        
        if not self.client.get(key):
            raise ValueError("There's no value for key %s!" % key)
        
    def as_curve(self, key):
        """Read serialized versions of hazard curves
        and produce shapes.Curve objects."""
        
        decoded_model = self._get_and_decode(key)
        
        curves = []
        
        for raw_curves in decoded_model["hcRepList"]:
            for curve in raw_curves["probExList"]:
                curves.append(shapes.Curve(
                        zip(raw_curves["gmLevels"], curve)))
        
        return curves
    
    def _get_and_decode(self, key):
        """Get the value from cache and return the decoded object."""
        
        self._check_key_in_cache(key)
        return json.JSONDecoder().decode(self.client.get(key))
    
    def for_nrml(self, key):
        """Read serialized versions of hazard curves
        and produce a dictionary as expected by the nrml writer."""

        decoded_model = self._get_and_decode(key)
        
        curves = {}
        
        for set_counter, raw_curves in enumerate(decoded_model["hcRepList"]):
            
            for curve_counter, curve in enumerate(raw_curves["probExList"]):
                data = {}
                
                data["IDmodel"] = "FIXED" # fixed, not yet implemented
                data["timeSpanDuration"] = raw_curves["timeSpan"]
                data["IMT"] = raw_curves["intensityMeasureType"]
                data["Values"] = curve
                data["IMLValues"] = raw_curves["gmLevels"]
                data["endBranchLabel"] = \
                        decoded_model["endBranchLabels"][set_counter]
                
                # Longitude and latitude and stored internally in the Java side
                # in radians. That object (org.opensha.commons.geo.Location) is
                # heavily used in the hazard engine and we don't have unit
                # tests, so I prefer to convert to decimal degrees here.
                lon = raw_curves["gridNode"][curve_counter]["location"]["lon"]
                lat = raw_curves["gridNode"][curve_counter]["location"]["lat"]
                
                curves[shapes.Site(math.degrees(lon), math.degrees(lat))] = data

        return curves

