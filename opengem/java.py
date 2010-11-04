"""Wrapper around our use of jpype.
Includes classpath arguments, and heap size."""

import os

import jpype

from opengem.logs import LOG

JVM = None


def jvm(max_mem=4000):
    global JVM
    if JVM is None:
        jarpath = os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), "../lib")
        LOG.debug("Jarpath is %s", jarpath)
        jpype.startJVM(jpype.getDefaultJVMPath(), 
                        "-Djava.ext.dirs=%s" % jarpath, "-Xmx%sM" % max_mem)
        JVM = jpype
    return JVM
