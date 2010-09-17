# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
XML namespace definitions and other constants
related to xml stuff.

"""

SHAML_NS = 'http://opengem.org/xmlns/shaml/0.1'
GML_NS = 'http://www.opengis.net/gml'
GML = "{%s}" % GML_NS
SHAML = "{%s}" % SHAML_NS
NSMAP = {"shaml" : SHAML_NS, "gml" : GML_NS}