# pylint: disable-all
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Converter library, takes things and makes other things.

This library is completely bitrotted and needs to be fixed/refactored.
It should use the openquake.java module instead of the jpype package,
I'm pretty certain that most of the conversion can be done on the python
side instead of the Java side so we could possibly get rid of the java
import altogether.

There's a unit test that is skipped, so we need to also expand that test
suite.
"""




import os

import guppy
import jpype

from lxml import etree

from openquake.xml import GML, NRML, NSMAP
from openquake.logs import LOG


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
        
        for source in input_parser.srcDataList:
            source_node = serialize_source(source, root_node)
            
 
        LOG.debug("Writing output to %s", outfile)
        #file_writer_class = jpype.JClass("java.io.FileWriter")
        #input_parser.writeSources2KMLfile(
        #            file_writer_class(outfile))
        et = etree.ElementTree(root_node)
        et.write(outfile, pretty_print=True)
    
    LOG.info("Finished conversion run.")


def serialize_source(source, parent_node):    
    SOURCE_NAMESPACE = "org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData."
    fault_source_class = jpype.JClass(SOURCE_NAMESPACE + "GEMFaultSourceData")
    point_source_class = jpype.JClass(SOURCE_NAMESPACE + "GEMPointSourceData")
    subduction_source_class = jpype.JClass(
                            SOURCE_NAMESPACE + "GEMSubductionFaultSourceData")
    area_source_class = jpype.JClass(SOURCE_NAMESPACE + "GEMAreaSourceData")

    if isinstance(source, fault_source_class):
        return serialize_fault_source(source, parent_node)
    if isinstance(source, point_source_class):
        return serialize_point_source(source, parent_node)
    if isinstance(source, area_source_class):
        return serialize_area_source(source, parent_node)
    if isinstance(source, subduction_source_class):
        return serialize_subduction_source(source, parent_node)
    else:
        raise Exception("Found unknown source type %s" % source.__class__.__name__)
    return None


def introspect_source(source):
    print dir(source)
    for prop in ['dip', 'floatRuptureFlag', 'hashCode', 
             'iD', 'id', 'mfd', 'name', 'rake', 'seismDepthLow', 
             'seismDepthUpp', 'tectReg.name']:
        try:
            thing = eval('fault_source.' + prop)
            thing()
            thing = thing()
            print "%s(%s) : %s" % (prop, type(thing), thing)
        except Exception, _e:
            pass


def serialize_fault_source(fault_source, parent_node):
    node = etree.SubElement(parent_node, NRML + "Fault", nsmap=NSMAP)
    node.attrib['name'] = fault_source.name.strip()
    node.attrib['ID'] = fault_source.id
    node.attrib['description'] = fault_source.name.strip()
    node.attrib['ruptureFloating'] = fault_source.floatRuptureFlag and 'Yes' or 'No'
    serialize_mfd(fault_source.mfd, node)
    return node


def serialize_point_source(point_source, parent_node):
    return
    
    introspect_source(point_source)
    # ['aveHypoDepth', 'aveRupTopVsMag', 'equals', 'getAveHypoDepth', 'getAveRupTopVsMag', 
    # 'getClass', 'getHypoMagFreqDistAtLoc', 'getID', 'getName', 'getTectReg', 'hashCode', 
    # 'hypoMagFreqDistAtLoc', 'iD', 'id', 'name', 'notify', 'notifyAll', 'setName', 
    # 'setTectReg', 'tectReg', 'toString', 'wait']

# MAKE GRIDDED SEISMICITY 
    
    node = etree.SubElement(parent_node, NRML + "Fault", nsmap=NSMAP)
    node.attrib['name'] = point_source.name.strip()
    node.attrib['ID'] = point_source.id
    node.attrib['description'] = point_source.name.strip()
    # node.attrib['ruptureFloating'] = point_source.floatRuptureFlag and 'Yes' or 'No'
    serialize_mfd(point_source.mfd, node)
    return node


def serialize_area_source(area_source, parent_node):
    introspect_source(area_source)
    
    node = etree.SubElement(parent_node, NRML + "Area", nsmap=NSMAP)
    node.attrib['name'] = area_source.name.strip()
    node.attrib['ID'] = area_source.id
    node.attrib['description'] = area_source.name.strip()
    #node.attrib['ruptureFloating'] = area_source.floatRuptureFlag and 'Yes' or 'No'
    serialize_mfd(area_source.mfd, node)
    return node


def serialize_subduction_source(subduction_source, parent_node):
    #introspect_source(subduction_source)
    # ['__class__', '__delattr__', '__dict__', '__doc__', '__eq__', '__format__', 
    # '__getattribute__', '__hash__', '__init__', '__javaclass__', 
    # '__javaobject__', '__metaclass__', '__module__', '__ne__', '__new__', 
    # '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', 
    # '__str__', '__subclasshook__', '__weakref__', 'bottomTrace', 'equals', 
    # 'floatRuptureFlag', 'getBottomTrace', 'getClass', 'getFloatRuptureFlag', 
    # 'getID', 'getMfd', 'getName', 'getRake', 'getTectReg', 'getTopTrace', 
    # 'hashCode', 'iD', 'id', 'mfd', 'name', 'notify', 'notifyAll', 'rake', 
    # 'setName', 'setTectReg', 'tectReg', 'toString', 'topTrace', 'wait']
    
    node = etree.SubElement(parent_node, NRML + "SubductionFault", nsmap=NSMAP)
    node.attrib['name'] = subduction_source.name.strip()
    node.attrib['ID'] = str(subduction_source.id)
    node.attrib['description'] = subduction_source.name.strip()
    node.attrib['ruptureFloating'] = subduction_source.floatRuptureFlag and 'Yes' or 'No'
    serialize_mfd(subduction_source.mfd, node)
    return node 

def serialize_evenly_discretized_mfd(mfd, parent_node):
    mfd_node = etree.SubElement(parent_node, 
                NRML + "EvenlyDiscretizedMFD", nsmap=NSMAP)
    points = []
    points_iters = mfd.getPointsIterator()
    while points_iters.hasNext():
        point= points_iters.next()
        points.append(str(point.getY()))
    values_node = etree.SubElement(mfd_node,
                NRML + "DistributionValues", nsmap=NSMAP)
    values_node.text = ", ".join(points)
    mfd_node.attrib['binSize'] = str(mfd.getDelta())
    mfd_node.attrib['binCount'] = str(mfd.getNum())
    mfd_node.attrib['minVal'] = str(mfd.getMinX())        

def serialize_mfd(mfd, parent_node):
    if mfd.__class__.__name__ == 'org.opensha.sha.magdist.SummedMagFreqDist':
        LOG.debug("Serializing a SummedMFD")
        mfd_list = mfd.getMagFreqDists()
        if mfd_list is None:
            mfd_list = [mfd]
        for sub_mfd in mfd_list:
            serialize_evenly_discretized_mfd(sub_mfd, parent_node)
    elif mfd.__class__.__name__ == 'org.opensha.sha.magdist.IncrementalMagFreqDist':
        LOG.debug("Serializing an IncrementalMFD")
        serialize_evenly_discretized_mfd(mfd, parent_node)
    else:
        raise Exception("Unhandled mfd class: %s" % mfd.__class__.__name__)
