"""Wrapper around our use of jpype.
Includes classpath arguments, and heap size."""

import os

import jpype

from opengem.logs import LOG

JVM = None


def jvm(max_mem=4000):
    global JVM
    if JVM is None:
        jarpaths = (os.path.join(os.path.abspath(__file__), "../lib"), 
                    os.path.join(os.path.abspath(__file__), "../dist"))
        LOG.debug("Jarpath is %s", jarpaths)
        jpype.startJVM(jpype.getDefaultJVMPath(), 
                        "-Djava.ext.dirs=%s" % jarpaths, "-Xmx%sM" % max_mem)
        JVM = jpype
    return JVM
