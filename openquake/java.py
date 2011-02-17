"""Wrapper around our use of jpype.
Includes classpath arguments, and heap size."""

import logging
import os
import sys

import jpype

from openquake.logs import LOG
from openquake import flags
FLAGS = flags.FLAGS

flags.DEFINE_boolean('capture_java_debug', True, 
    "Pipe Java stderr and stdout to python stderr and stdout")

JAVA_CLASSES = {
    'LogicTreeProcessor' : "org.gem.engine.LogicTreeProcessor",
    'KVS' : "org.gem.engine.hazard.redis.Cache",
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

logging.getLogger('jpype').setLevel(logging.ERROR)


def jclass(class_key):
    """Wrapper around jpype.JClass for short class names"""
    jvm()
    return jpype.JClass(JAVA_CLASSES[class_key])


def jvm(max_mem=None):
    """Return the jpype module, after guaranteeing the JVM is running and 
    the classpath has been loaded properly."""
    jarpaths = (os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "../lib")),
                os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "../dist")))
    # TODO(JMC): Make sure these directories exist
    # LOG.debug("Jarpath is %s", jarpaths)
    if not jpype.isJVMStarted():
        max_mem = get_jvm_max_mem(max_mem)
        LOG.debug("Default JVM path is %s" % jpype.getDefaultJVMPath())
        jpype.startJVM(jpype.getDefaultJVMPath(), 
            "-Djava.ext.dirs=%s:%s" % jarpaths, 
        #"-Dnet.spy.log.LoggerImpl=net.spy.memcached.compat.log.Log4JLogger",
            # "-Dlog4j.debug",
            "-Dlog4j.configuration=log4j.properties",
            "-Dlog4j.rootLogger=%s, A1" % (FLAGS.debug.upper()),
            # "-Dlog4j.rootLogger=DEBUG, A1",
            "-Xmx%sM" % max_mem)
        
        if FLAGS.capture_java_debug:
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


# The default JVM max. memory size to be used in the absence of any other
# setting or configuration.
DEFAULT_JVM_MAX_MEM = 4000


def get_jvm_max_mem(max_mem):
    """
    Determine what the JVM maximum memory size should be.

    :param max_mem: the `max_mem` parameter value actually passed to the
        caller.
    :type max_mem: integer or None

    :returns: the maximum JVM memory size considering the possible sources in
        the following order
        * the actual value passed
        * TODO: the value in the config file
        * the value of the `OQ_JVM_MAX_MEM` environment variable
        * a fixed default (`4000`).
    """
    if max_mem:
        return max_mem
    if os.environ.get("OQ_JVM_MAXMEM"):
        return int(os.environ.get("OQ_JVM_MAXMEM"))
    return DEFAULT_JVM_MAX_MEM
