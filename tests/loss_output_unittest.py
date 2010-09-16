"""
Test the output of Loss Curve and Loss Ratio Curve as XML.

"""

import os
import unittest

from opengem import logs
from opengem.risk import engines
from opengem.output import risk as risk_output
from opengem import test
from opengem import shapes

log = logs.RISK_LOG

LOSS_XML_OUTPUT_FILE = 'loss-curves.xml'
LOSS_RATIO_XML_OUTPUT_FILE = 'loss-ratio-curves.xml'

data_dir = os.path.join(os.path.dirname(__file__), 'data')

    
class LossOutputTestCase(unittest.TestCase):
    """Confirm that XML output from risk engine is valid against schema,
    as well as correct given the inputs."""
    
    def setUp(self):
        pass
    
    def test_xml_is_valid(self):
        xml_writer = risk_output.RiskXMLWriter(
            os.path.join(data_dir, LOSS_XML_OUTPUT_FILE))

        # Build up some sample loss curves here
        # Then serialize them to XML
        # save the xml, and run schema validation on it
        # Optionally, compare it to another XML file.

        first_site = shapes.Site(10.0, 10.0)
        first_curve = shapes.FastCurve([(0.0, 0.1), (1.0, 0.9)])
        
        xml_writer.write(first_site, loss_ratio_curves[first_gp])
        xml_writer.close()
