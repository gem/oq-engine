"""Wrapper around our use of jpype.
Includes classpath arguments, and heap size."""

import os
import sys

import jpype

from opengem.logs import LOG

        
def jvm(max_mem=4000):
    jarpaths = (os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib")), 
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../dist")))
    LOG.debug("Jarpath is %s", jarpaths)
    if not jpype.isJVMStarted():
        print "Default JVM path is %s" % jpype.getDefaultJVMPath()
        jpype.startJVM(jpype.getDefaultJVMPath(), 
            "-Djava.ext.dirs=%s:%s" % jarpaths, 
            "-Dnet.spy.log.LoggerImpl=net.spy.memcached.compat.log.Log4JLogger",
            # "-Dlog4j.debug",
            "-Dlog4j.configuration=log4j.properties",
            "-Xmx%sM" % max_mem)
        
        mystream = jpype.JProxy("org.gem.IPythonPipe", inst=sys.stdout)
        errstream = jpype.JProxy("org.gem.IPythonPipe", inst=sys.stderr)
        outputstream = jpype.JClass("org.gem.PythonOutputStream")()
        outputstream.setPythonStdout(mystream)
        ps = jpype.JClass("java.io.PrintStream")
        err_stream = jpype.JClass("org.gem.PythonOutputStream")()
        err_stream.setPythonStdout(errstream)
        jpype.java.lang.System.setOut(ps(outputstream))
        jpype.java.lang.System.setErr(ps(err_stream))
    return jpype


# TODO(JMC): Use this later for logging:
# self.PropertyConfigurator = jpype.JClass('org.apache.log4j.PropertyConfigurator')
# object.__getattribute__(self, 'PropertyConfigurator').configure(settings.LOG4J_PROPERTIES)