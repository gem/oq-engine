# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""Constants and helper functions for XML processing,
including namespaces, and namespace maps."""

NRML_NS = 'http://opengem.org/xmlns/nrml/0.1'
SHAML_NS = NRML_NS
GML_NS = 'http://www.opengis.net/gml/profile/sfgml/1.0'
GML = "{%s}" % GML_NS
SHAML = "{%s}" % SHAML_NS
NRML = "{%s}" % NRML_NS
NSMAP = { None: SHAML_NS, "gml" : GML_NS}