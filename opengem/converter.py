# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Converter library, takes things and makes NRML.
"""

import os

import jpype

from opengem import logs
from opengem.parser import nshmp
from opengem.parser import esri
from opengem.parser import nrml

log = logs.LOG

PARSERS = {
    'NSHMP' : nshmp,
    'ESRI' : esri,
    'NRML' : nrml,
}



def convert(input_path, input_module, output_path, output_module):
    log.info("Starting conversion run...")
    jarpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../lib")
    jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.ext.dirs=%s" % jarpath)
    
    input_module.init_paths(input_path, jpype)
    
    # TODO(JMC): Make this support non-Java input parsers, too
    
    # All the GEM1 parsers take a bounding box for the ctor
    (latmin, latmax, lonmin, lonmax) = input_module.BOUNDING_BOX
    for model, _subdir in input_module.JAVA_MODELS:
        java_class = jpype.JClass(model)
        input_parser = java_class(latmin, latmax, lonmin, lonmax)
        print "Got a %s parser with %s sources" % (model, input_parser.getNumSources())
        file_writer_class = jpype.JClass("java.io.FileWriter")
        input_parser.writeSources2KMLfile(file_writer_class(output_path + model+"-foo.xml"))