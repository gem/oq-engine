#!/usr/bin/env python
# encoding: utf-8
"""
A simple memcached reader.

"""

import json

import shapes


class Reader(object):
    """Read objects from memcached and translate them into
    our object model.
    
    """
    
    def __init__(self, client):
        self.client = client
    
    def _check_key_in_cache(self, key):
        """Raise an error if the given key is not in memcached."""
        
        if not self.client.get(key):
            raise ValueError("There's no value for key %s!" % key)
        
    def as_curve(self, key):
        """Read serialized versions of hazard curves
        and produce shapes.FastCurve objects.
        
        TODO (ac): How should we handle other metadata?
        """
        self._check_key_in_cache(key)
        value = self.client.get(key)
        
        decoder = json.JSONDecoder()
        decoded_model = decoder.decode(value)
        
        curves = []
        
        for raw_curves in decoded_model["hcRepList"]:
            for curve in raw_curves["probExList"]:
                curves.append(shapes.FastCurve(
                        zip(raw_curves["gmLevels"], curve)))
        
        return curves
    
    def for_shaml(self, key):
        """Read serialized versions of hazard curves
        and produce a dictionary as expected by the shaml writer.
        
        """
        self._check_key_in_cache(key)
        value = self.client.get(key)
        
        decoder = json.JSONDecoder()
        decoded_model = decoder.decode(value)
        
        curves = {}
        set_counter = 0
        
        for raw_curve in decoded_model["hcRepList"]:
            curve_counter = 0
            
            for curve in raw_curve["probExList"]:
                data = {}
                
                data["IDmodel"] = "FIXED" # fixed, not yet implemented
                data["vs30"] = 0.0 # fixed, not yet implemented
                data["timeSpanDuration"] = raw_curve["timeSpan"]
                data["IMT"] = raw_curve["intensityMeasureType"]
                data["Values"] = curve
                data["IML"] = raw_curve["gmLevels"]
                data["maxProb"] = curve[-1]
                data["minProb"] = curve[0]
                data["endBranchLabel"] = \
                        decoded_model["endBranchLabels"][set_counter]
                
                lon = raw_curve["gridNode"][curve_counter]["location"]["lon"]
                lat = raw_curve["gridNode"][curve_counter]["location"]["lat"]
                
                curves[shapes.Site(lon, lat)] = data
                curve_counter += 1

            set_counter += 1

        return curves
