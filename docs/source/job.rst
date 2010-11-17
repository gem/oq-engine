..
      License Header goes here

Jobs
====================
Super job type happy stuff.
-----------------------------------------------


A Job is an object responsible for parsing a configuration, loading the appropriate behaviour based on that configuration, and then executing the tasks associated with that behaviour. The workflow of a Job is broken up into four parts: the Job class, the Mixin class, the Risk and Hazard mixin proxies, and the various Hazard and Risk mixins to define behaviour. 


The :mod:`job` class
--------------------------
.. automodule:: opengem.job
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`mixin` class
--------------------------
.. automodule:: opengem.job.mixins
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`hazard` job proxy and mixins
--------------------------------------
.. automodule:: opengem.hazard.job
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`risk` job proxy and mixins
------------------------------------
.. automodule:: opengem.risk.job
    :members:
    :undoc-members:
    :show-inheritance:


This code is intended to make 

The code is intended to parses data (in the NRML XML format) in order to provide the needed input data to the engine. The class is implemented as a generator for each element and child element in the parsed instance document. Dom and Sax parsing are used where appropriate. 
For Sax parsing the XML etree method was used to parse the xml data. LXML is an open source third-party library that builds on the popular libxml2 parser. It provides a 100% compatible ElementTree API, then extends it with full XPath 1.0 support. We justified the use of LXML etree by comparing it's performance to native XML parsers creating xml_speedtests.py which tests the speed and memory use of parsing a 116mb xml file.

The parser_vulnerability_model 
- Parses the xml document using parser.py
* Calls the meta information
* Calls child elements
* Calls root elements 
* Considers all attributes of Vulnerability Function

