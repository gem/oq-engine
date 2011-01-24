# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""Constants and helper functions for XML processing,
including namespaces, and namespace maps."""

NRML_NS = 'http://openquake.org/xmlns/nrml/0.1'
GML_NS = 'http://www.opengis.net/gml'
QUAKEML_NS = 'http://quakeml.org/xmlns/quakeml/1.1'
NRML = "{%s}" % NRML_NS
GML = "{%s}" % GML_NS
QUAKEML = "{%s}" % QUAKEML_NS
NSMAP = {None: NRML_NS, "gml": GML_NS}
NSMAP_WITH_QUAKEML = {None: NRML_NS, "gml": GML_NS, "qml": QUAKEML_NS}