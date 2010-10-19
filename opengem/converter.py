# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Converter library, takes things and makes other things.
"""

import os

import guppy
import jpype

from lxml import etree

from opengem.xml import GML, NRML, NSMAP
from opengem.logs import LOG


def convert(input_path, input_module, output_path, output_module):
    """Main conversion method. Currently tooled to run GEM1 parsers
    via jpype, which involves setting static properties on the classes
    for the input directories. The parsing itself is done in the class
    constructor, and output is derived from a writeSources method."""
    
    LOG.info("Starting conversion run...")
    jarpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../lib")
    LOG.debug("Jarpath is %s", jarpath)
    max_mem = 4000
    jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.ext.dirs=%s" % jarpath, "-Xmx%sM" % max_mem)
    input_module.init_paths(input_path, jpype)
    
    root_node = etree.Element(NRML + "SeismicSourceList", nsmap=NSMAP)
    
    # All the GEM1 parsers take a bounding box for the ctor
    (latmin, latmax, lonmin, lonmax) = input_module.BOUNDING_BOX
    
    # TODO(JMC): Make this support non-Java input parsers, too
    for model, _subdir in input_module.JAVA_MODELS:
        outfile = os.path.join(output_path, model+"-foo.xml")
        if os.path.exists(outfile):
            LOG.info("Output exists, skipping generation of %s", outfile)
            # continue
        java_class = jpype.JClass(model)
        input_parser = java_class(latmin, latmax, lonmin, lonmax)
        LOG.debug("Loaded a %s parser with %s sources", 
                    model, input_parser.getNumSources())
        #print(dir(input_parser))
        #print dir(input_parser.srcDataList[0])
        
        for source in input_parser.srcDataList[1:5]:
            source_node = serialize_source(source, root_node)
            
 
        LOG.debug("Writing output to %s", outfile)
        #file_writer_class = jpype.JClass("java.io.FileWriter")
        #input_parser.writeSources2KMLfile(
        #            file_writer_class(outfile))
        et = etree.ElementTree(root_node)
        et.write(outfile, pretty_print=True)
        return
    
    LOG.info("Finished conversion run.")


def serialize_source(source, parent_node):    
    SOURCE_NAMESPACE = "org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData."
    fault_source_class = jpype.JClass(SOURCE_NAMESPACE + "GEMFaultSourceData")
    point_source_class = jpype.JClass(SOURCE_NAMESPACE + "GEMPointSourceData")
    subduction_source_class = jpype.JClass(
                            SOURCE_NAMESPACE + "GEMSubductionFaultSourceData")
    area_source_class = jpype.JClass(SOURCE_NAMESPACE + "GEMAreaSourceData")
    print source.__class__

    if isinstance(source, fault_source_class):
        return serialize_fault_source(source, parent_node)
    return None


def serialize_fault_source(fault_source, parent_node):
    for prop in ['dip', 'floatRuptureFlag', 'hashCode', 
                 'iD', 'id', 'mfd', 'name', 'rake', 'seismDepthLow', 
                 'seismDepthUpp', 'tectReg.name']:
        thing = eval('fault_source.' + prop)
        try:
            thing()
            thing = thing()
        except Exception, _e:
            pass
        #print "%s(%s) : %s" % (prop, type(thing), thing)
    node = etree.SubElement(parent_node, NRML + "Fault", nsmap=NSMAP)
    node.attrib['name'] = fault_source.name
    node.attrib['ID'] = fault_source.id
    node.attrib['description'] = fault_source.name
    node.attrib['ruptureFloating'] = fault_source.floatRuptureFlag and 'Yes' or 'No'
    serialize_mfd(fault_source.mfd, node)
    return node
    
    #print "mfd: %s" % (dir(fault_source.mfd))
    
def serialize_mfd(mfd, parent_node):
    print mfd.__class__.__name__
    if mfd.__class__.__name__ == 'org.opensha.sha.magdist.SummedMagFreqDist':
        mfd_node = etree.SubElement(parent_node, 
                    NRML + "EvenlyDiscretizedMFD", nsmap=NSMAP)
        LOG.debug("Serializing a SummedMFD")
        # print dir(mfd)
        print mfd.points
        values_node = etree.SubElement(mfd_node,
                    NRML + "DistributionValues", nsmap=NSMAP)
        