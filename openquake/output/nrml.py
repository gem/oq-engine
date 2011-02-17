# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Base functionality for NRML serialization.
"""

from lxml import etree

from openquake import logs
from openquake import writer
from openquake import xml

LOG = logs.LOG

NRML_DEFAULT_ID = 'nrml'
RISKRESULT_DEFAULT_ID = 'rr'
HAZARDRESULT_DEFAULT_ID = 'hr'

class TreeNRMLWriter(writer.FileWriter):
    """
    Abstract base class for a writer that doesn't write (site, attribute)
    pairs to file sequentially, but first collects the whole lxml object
    model and then serializes using the close() method.
    This is required when the (site, attribute) pairs have to be collected
    per category in different tree branches (e.g., for loss curves, several
    curves have to be assigned to the same asset). 
    """
    def write(self, point, value):
        """Write out an individual point (has to be implemented in 
        derived class).
        """
        raise NotImplementedError

    def close(self):
        """Overrides the default implementation writing all the
        collected lxml object model to the stream.
        """
        if self.root_node is None:
            error_msg = "You need to add at least data for one site to "\
                        "build a valid output!"
            raise RuntimeError(error_msg)

        self.file.write(etree.tostring(self.root_node, pretty_print=True,
            xml_declaration=True, encoding="UTF-8"))
        super(TreeNRMLWriter, self).close()

    def _create_root_element(self):
        """Adds NRML root element to lxml tree representation.""" 
        self.root_node = etree.Element(xml.NRML_ROOT_TAG, nsmap=xml.NSMAP)


def set_gml_id(element, gml_id):
    """Set gml:id attribute for element"""
    element.set("%sid" % xml.GML, str(gml_id))

