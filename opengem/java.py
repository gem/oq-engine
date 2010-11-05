"""Wrapper around our use of jpype.
Includes classpath arguments, and heap size."""

import os

import jpype

from opengem.logs import LOG




        
def jvm(max_mem=4000):
    jarpaths = (os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib")), 
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../dist")))
    LOG.debug("Jarpath is %s", jarpaths)
    try:
        foo = jpype.JPackage("java.lang.System.out")
    except Exception, e:
        print "Default JVM path is %s" % jpype.getDefaultJVMPath()
        jpype.startJVM(jpype.getDefaultJVMPath(), 
                        "-Djava.ext.dirs=%s:%s" % jarpaths, "-Xmx%sM" % max_mem) # "-Djava.ext.dirs=%s:%s" % jarpaths
    return jpype
