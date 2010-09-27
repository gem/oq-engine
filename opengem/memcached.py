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
    
    def as_curve(self, name):
        """Read serialized versions of hazard curves
        and produce shapes.FastCurve objects.
        
        TODO (ac): How should we handle other metadata?
        """
        value = self.client.get(name)
        
        if not value:
            raise ValueError("There's no value for key %s!" % name)
        
        decoder = json.JSONDecoder()
        decoded_model = decoder.decode(value)
        
        curves = []
        
        for raw_curves in decoded_model["hcRepList"]:
            for curve in raw_curves["probExList"]:
                curves.append(shapes.FastCurve(
                        zip(raw_curves["gmLevels"], curve)))
        
        return curves