# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""Constants and helper functions for XML processing,
including namespaces, and namespace maps."""


NRML_SCHEMA_FILE = 'nrml.xsd'

NRML_NS = 'http://openquake.org/xmlns/nrml/0.2'
GML_NS = 'http://www.opengis.net/gml'
QUAKEML_NS = 'http://quakeml.org/xmlns/quakeml/1.1'

NRML = "{%s}" % NRML_NS
GML = "{%s}" % GML_NS

QUAKEML = "{%s}" % QUAKEML_NS
NSMAP = {None: NRML_NS, "gml": GML_NS}
NSMAP_WITH_QUAKEML = {None: NRML_NS, "gml": GML_NS, "qml": QUAKEML_NS}

# TODO(fab): remove these when transition to new schema is completed
NRML_SCHEMA_FILE_OLD = 'old/nrml.xsd'

NRML_NS_OLD = 'http://openquake.org/xmlns/nrml/0.1'
GML_NS_OLD = 'http://www.opengis.net/gml/profile/sfgml/1.0'

NRML_OLD = "{%s}" % NRML_NS_OLD
GML_OLD = "{%s}" % GML_NS_OLD

NSMAP_OLD = {None: NRML_NS_OLD, "gml": GML_NS_OLD}