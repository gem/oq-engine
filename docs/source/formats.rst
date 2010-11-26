..
      License Header goes here

XML Data Parser
====================
Discrete Vulnerability and Exposure Data Parser
-----------------------------------------------


The code is intended to parses data (in the NRML XML format) in order to provide the needed input data to the engine. The class is implemented as a generator for each element and child element in the parsed instance document. Dom and Sax parsing are used where appropriate. 
For Sax parsing the XML etree method was used to parse the xml data. LXML is an open source third-party library that builds on the popular libxml2 parser. It provides a 100% compatible ElementTree API, then extends it with full XPath 1.0 support. We justified the use of LXML etree by comparing it's performance to native XML parsers creating xml_speedtests.py which tests the speed and memory use of parsing a 116mb xml file.

The parser_vulnerability_model 

* Parses the xml document using parser.py
* Calls the meta information
* Calls child elements
* Calls root elements 
* Considers all attributes of Vulnerability Function

The :mod:`parser` Sub-package
-----------------------------

.. automodule:: openquake.parser.esri
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: openquake.parser.exposure
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: openquake.parser.hazard
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: openquake.parser.nshmp
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: openquake.parser.vulnerability
    :members:
    :undoc-members:
    :show-inheritance:

