#!/usr/bin/env python
# encoding: utf-8
"""
A simple memcached reader.

"""

import json

import shapes


class Reader(object):
    
    def __init__(self, client):
        self.client = client
    
    def as_curve(self, name):
        value = self.client.get(name)
        
        if not value:
            raise ValueError("There's no value for key %s!" % name)
        
        decoder = json.JSONDecoder()
        decoded_model = decoder.decode(value)
        
        curves = []
        
        for set in decoded_model["hcRepList"]:
            for curve in set["probExList"]:
                curves.append(shapes.FastCurve(zip(set["gmLevels"], curve)))
        
        return curves