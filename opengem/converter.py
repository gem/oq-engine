# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Converter library, takes things and makes other things.
"""

import os

import guppy
import jpype

from opengem import logs

log = logs.LOG


def convert(input_path, input_module, output_path, output_module):
    """Main conversion method. Currently tooled to run GEM1 parsers
    via jpype, which involves setting static properties on the classes
    for the input directories. The parsing itself is done in the class
    constructor, and output is derived from a writeSources method."""
    
    log.info("Starting conversion run...")
    jarpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../lib")
    log.debug("Jarpath is %s", jarpath)
    jpype.startJVM(jpype.getDefaultJVMPath(), " -Xms2048m -Xmx2048m ", "-Djava.ext.dirs=%s" % jarpath)
    input_module.init_paths(input_path, jpype)
    
    # All the GEM1 parsers take a bounding box for the ctor
    (latmin, latmax, lonmin, lonmax) = input_module.BOUNDING_BOX
    
    # TODO(JMC): Make this support non-Java input parsers, too
    for model, _subdir in input_module.JAVA_MODELS:
        outfile = os.path.join(output_path, model+"-foo.xml")
        if os.path.exists(outfile):
            log.info("Output exists, skipping generation of %s", outfile)
            continue
        java_class = jpype.JClass(model)
        input_parser = java_class(latmin, latmax, lonmin, lonmax)
        log.debug("Loaded a %s parser with %s sources", 
                    model, input_parser.getNumSources())
        log.debug("Writing output to %s", outfile)
        file_writer_class = jpype.JClass("java.io.FileWriter")
        input_parser.writeSources2KMLfile(
                    file_writer_class(outfile))
                    
        log.debug("\nHeap before cleanup: \n%s", 
                        guppy.hpy().heap())
        del input_parser
        del java_class
        jpype.JClass("java.lang.System").gc()
        
        log.debug("\nHeap after cleanup: \n%s", 
                        guppy.hpy().heap())
    
    log.info("Finished conversion run.")