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
    
    # " -Xms2048m -Xmx2048m ", 
    jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.ext.dirs=%s" % jarpath)
    input_module.init_paths(input_path, jpype)
    
    SOURCE_NAMESPACE = "org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData."
    fault_source_class = jpype.JClass(SOURCE_NAMESPACE + "GEMFaultSourceData")
    point_source_class = jpype.JClass(SOURCE_NAMESPACE + "GEMPointSourceData")
    subduction_source_class = jpype.JClass(
                            SOURCE_NAMESPACE + "GEMSubductionFaultSourceData")
    area_source_class = jpype.JClass(SOURCE_NAMESPACE + "GEMAreaSourceData")
    
    
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
        print(dir(input_parser))
        print dir(input_parser.srcDataList[0])
        for source in input_parser.srcDataList[1:2]:
            print source.__class__
            print fault_source_class
            print isinstance(source, fault_source_class)
            for prop in ['dip', 'floatRuptureFlag', 'hashCode', 
                         'iD', 'id', 'mfd', 'name', 'rake', 'seismDepthLow', 
                         'seismDepthUpp', 'tectReg.name']:
                thing = eval('source.' + prop)
                try:
                    thing()
                    thing = thing()
                except Exception, _e:
                    pass
                print "%s(%s) : %s" % (prop, type(thing), thing)
        
            print "mfd: %s" % (dir(source.mfd))
            return
        log.debug("Writing output to %s", outfile)
        file_writer_class = jpype.JClass("java.io.FileWriter")
        input_parser.writeSources2KMLfile(
                    file_writer_class(outfile))
    
    log.info("Finished conversion run.")