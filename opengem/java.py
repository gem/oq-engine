"""Wrapper around our use of jpype.
Includes classpath arguments, and heap size."""

import os
import sys

import jpype

from opengem.logs import LOG
from opengem import flags
FLAGS = flags.FLAGS

flags.DEFINE_boolean('capture_java_debug', True, 
    "Pipe Java stderr and stdout to python stderr and stdout")

JAVA_CLASSES = {
    'CommandLineCalculator' : "org.gem.engine.CommandLineCalculator",
    'KVS' : "org.gem.engine.hazard.memcached.Cache",
    'JsonSerializer' : "org.gem.JsonSerializer",
    "EventSetGen" : "org.gem.calc.StochasticEventSetGenerator",
    "Random" : "java.util.Random",
    "GEM1ERF" : "org.gem.engine.hazard.GEM1ERF",
    "HazardCalculator" : "org.gem.calc.HazardCalculator",
    "Properties" : "java.util.Properties",
    "CalculatorConfigHelper" : "org.gem.engine.CalculatorConfigHelper",
    "Configuration" : "org.apache.commons.configuration.Configuration",
    "ConfigurationConverter" : 
        "org.apache.commons.configuration.ConfigurationConverter",
    "ArbitrarilyDiscretizedFunc" : 
        "org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc",
    "ArrayList" : "java.util.ArrayList",
    "GmpeLogicTreeData" : "org.gem.engine.GmpeLogicTreeData",
    "AttenuationRelationship" : "org.opensha.sha.imr.AttenuationRelationship",
    "EqkRupForecastAPI" : "org.opensha.sha.earthquake.EqkRupForecastAPI",
    "DoubleParameter" : "org.opensha.commons.param.DoubleParameter",
    "StringParameter" : "org.opensha.commons.param.StringParameter",
    "ParameterAPI" : "org.opensha.commons.param.ParameterAPI",
    "DiscretizedFuncAPI" : 
        "org.opensha.commons.data.function.DiscretizedFuncAPI",
    "ProbabilityMassFunctionCalc" : "org.gem.calc.ProbabilityMassFunctionCalc",
}


def jclass(class_key):
    """Wrapper around jpype.JClass for short class names"""
    jvm()
    return jpype.JClass(JAVA_CLASSES[class_key])


def jvm(max_mem=4000, capture_log=FLAGS.capture_java_debug):
    """Return the jpype module, after guaranteeing the JVM is running and 
    the classpath has been loaded properly."""
    jarpaths = (os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib")), 
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../dist")))
    # TODO(JMC): Make sure these directories exist
    # LOG.debug("Jarpath is %s", jarpaths)
    if not jpype.isJVMStarted():
        print "Default JVM path is %s" % jpype.getDefaultJVMPath()
        jpype.startJVM(jpype.getDefaultJVMPath(), 
            "-Djava.ext.dirs=%s:%s" % jarpaths, 
            "-Dnet.spy.log.LoggerImpl=net.spy.memcached.compat.log.Log4JLogger",
            # "-Dlog4j.debug",
            "-Dlog4j.configuration=log4j.properties",
            "-Xmx%sM" % max_mem)
        
        if capture_log:
            mystream = jpype.JProxy("org.gem.IPythonPipe", inst=sys.stdout)
            errstream = jpype.JProxy("org.gem.IPythonPipe", inst=sys.stderr)
            outputstream = jpype.JClass("org.gem.PythonOutputStream")()
            err_stream = jpype.JClass("org.gem.PythonOutputStream")()
            outputstream.setPythonStdout(mystream)
            err_stream.setPythonStdout(errstream)
        
            ps = jpype.JClass("java.io.PrintStream")
            jpype.java.lang.System.setOut(ps(outputstream))
            jpype.java.lang.System.setErr(ps(err_stream))
        
    return jpype


# TODO(JMC): Use this later for logging:
# self.PropertyConfigurator = jpype.JClass('org.apache.log4j.PropertyConfigurator')
# object.__getattribute__(self, 'PropertyConfigurator').configure(settings.LOG4J_PROPERTIES)