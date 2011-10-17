# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""Wrapper around our use of jpype.
Includes classpath arguments, and heap size."""

import jpype
import os
import sys
import traceback
import logging

from celery.decorators import task as celery_task

from functools import wraps

from openquake import nrml
from openquake.utils import config


# JVM max. memory size (in MB) to be used (per celery worker process!)
DEFAULT_JVM_MAX_MEM = 768


JAVA_CLASSES = {
    'LogicTreeProcessor': "org.gem.engine.LogicTreeProcessor",
    'LogicTreeReader': "org.gem.engine.LogicTreeReader",
    'KVS': "org.gem.engine.hazard.redis.Cache",
    'JsonSerializer': "org.gem.JsonSerializer",
    "EventSetGen": "org.gem.calc.StochasticEventSetGenerator",
    "Random": "java.util.Random",
    "GEM1ERF": "org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF",
    "HazardCalculator": "org.gem.calc.HazardCalculator",
    "Properties": "java.util.Properties",
    "CalculatorConfigHelper": "org.gem.engine.CalculatorConfigHelper",
    "Configuration": "org.apache.commons.configuration.Configuration",
    "ConfigurationConverter":
        "org.apache.commons.configuration.ConfigurationConverter",
    "ArbitrarilyDiscretizedFunc":
        "org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc",
    "ArrayList": "java.util.ArrayList",
    "GmpeLogicTreeData": "org.gem.engine.GmpeLogicTreeData",
    "AttenuationRelationship": "org.opensha.sha.imr.AttenuationRelationship",
    "EqkRupForecastAPI": "org.opensha.sha.earthquake.EqkRupForecastAPI",
    "DoubleParameter": "org.opensha.commons.param.DoubleParameter",
    "StringParameter": "org.opensha.commons.param.StringParameter",
    "ParameterAPI": "org.opensha.commons.param.ParameterAPI",
    "DiscretizedFuncAPI":
        "org.opensha.commons.data.function.DiscretizedFuncAPI",
    "ProbabilityMassFunctionCalc": "org.gem.calc.ProbabilityMassFunctionCalc",
    "Location": "org.opensha.commons.geo.Location",
    "Site": "org.opensha.commons.data.Site",
    "HashMap": "java.util.HashMap",
    "RuptureReader": "org.gem.engine.hazard.parsers.RuptureReader",
    "GMPEDeserializer":
        "org.gem.ScalarIntensityMeasureRelationshipApiDeserializer",
    "JsonPrimitive": "com.google.gson.JsonPrimitive",
    "GMFCalculator": "org.gem.calc.GroundMotionFieldCalculator",
    "SourceModelReader": "org.gem.engine.hazard.parsers.SourceModelReader",
    "StirlingGriddedSurface":
        "org.opensha.sha.faultSurface.StirlingGriddedSurface",
    "ApproxEvenlyGriddedSurface":
        "org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface",
    "LocationListFormatter": "org.gem.LocationListFormatter",
    "PythonBridgeAppender": "org.gem.log.PythonBridgeAppender",
}


def jclass(class_key):
    """Wrapper around jpype.JClass for short class names"""
    jvm()
    return jpype.JClass(JAVA_CLASSES[class_key])


class JavaLoggingBridge(object):
    """
    :class:`JavaLoggingBridge` is responsible for receiving java logging
    messages and relogging them.
    """
    #: The list of supported levels is used for sanity checks.
    SUPPORTED_LEVELS = set((logging.DEBUG, logging.INFO, logging.WARNING,
                            logging.ERROR, logging.CRITICAL))

    def append(self, event):
        """
        Given java ``LogEvent`` object log the message
        as if it was logged by python logging.
        """
        # log4j uses the following numbers for logging levels by default:
        # 10000 DEBUG, 20000 INFO, 30000 WARNING, 40000 ERROR, 50000 FATAL.
        # Python logging uses 10, 20, 30, 40 and 50 respectively.
        # So for mapping of logging levels we need to divide java
        # log level by 1000.
        java_level = event.getLevel().toInt()
        level, _rem = divmod(java_level, 1000)

        if event.logger.getParent() is None:
            # getParent() returns ``None`` only for root logger.
            # Use the name "java" for it instead of "java.root".
            logger_name = 'java'
        else:
            logger_name = 'java.%s' % event.getLoggerName()
        logger = logging.getLogger(logger_name)

        if _rem != 0 or level not in self.SUPPORTED_LEVELS:
            # java side used some custom logging level.
            # don't try to map it to python level and don't
            # check if python logger was enabled for it
            level = java_level
            logger.warning('unrecognised logging level %d was used', level)
        else:
            if not logger.isEnabledFor(level):
                return

        msg = event.getMessage()

        location_info = event.getLocationInformation()

        filename = location_info.getFileName()
        if filename == '?':
            # mapping of unknown filenames from java "?" to python
            filename = '(unknown file)'

        lineno = location_info.getLineNumber()
        if not lineno.isdigit():
            # java uses "?" for unknown line number, python use 0
            lineno = 0
        else:
            # LocationInformation.getLineNumber() returns string
            lineno = int(lineno)

        classname = location_info.getClassName()
        methname = location_info.getMethodName()
        if '?' in (classname, methname):
            funcname = '(unknown function)'
        else:
            funcname = '%s.%s' % (classname, methname)

        # Now do what logging.Logger._log() does:
        # create log record and handle it.
        record = logger.makeRecord(logger.name, level, filename, lineno, msg,
                                   args=(), exc_info=None, func=funcname,
                                   extra={})
        # these two values are set by LogRecord constructor
        # so we need to overwrite them.
        record.threadName = event.getThreadName()
        logger.handle(record)


def _init_logs():
    """
    Initialize Java logging.

    Is called by :func:`jvm`.
    """
    appender = jclass('PythonBridgeAppender')
    # ``bridge`` is a static property of PythonBridge class.
    # So there will be only one JavaLoggingBridge for all loggers.
    appender.bridge = jpype.JProxy('org.gem.log.PythonBridge',
                                   inst=JavaLoggingBridge())
    props = jclass("Properties")()
    props.setProperty('log4j.rootLogger', 'debug, pythonbridge')
    props.setProperty('log4j.appender.pythonbridge',
                      'org.gem.log.PythonBridgeAppender')
    jpype.JClass("org.apache.log4j.PropertyConfigurator").configure(props)


def get_jvm_max_mem(max_mem):
    """
    Determine what the JVM maximum memory size should be.

    :param max_mem: the `max_mem` parameter value passed
    :type max_mem: integer or None

    :returns: the maximum JVM memory size considering the possible sources in
        the following order
        * the actual value passed
        * the setting in the config file
        * a fixed default (`768` MB).
    """
    if max_mem:
        return max_mem
    cfg = config.get_section("java")
    return int(cfg["mem_max"]) if cfg["mem_max"] else DEFAULT_JVM_MAX_MEM


def jvm(max_mem=None):
    """
    Return the jpype module, after guaranteeing the JVM is running and
    the classpath has been loaded properly.

    :param int max_mem: The maximum RAM (in MB) that should be used per JVM.
        Please note that *every* celery worker process will have its own JVM
        i.e. on the gemsun boxes with 32 cores/celery worker processes the
        JVMs *alone* will consume 24GB of RAM with the default setting above.
    """
    jarpaths = (os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "../dist")),
                '/usr/share/java')

    if not jpype.isJVMStarted():
        max_mem = get_jvm_max_mem(max_mem)
        jpype.startJVM(jpype.getDefaultJVMPath(),
            "-Xmx%sM" % max_mem,
            "-Djava.ext.dirs=%s:%s" % jarpaths,
            # setting Schema path here is ugly, but it's better than
            # doing it before all XML parsing calls
            "-Dopenquake.nrml.schema=%s" % nrml.nrml_schema_file(),
            # force the default Xerces parser configuration, otherwise
            # some random system-installed JAR might override it
            "-Dorg.apache.xerces.xni.parser.XMLParserConfiguration=" \
                "org.apache.xerces.parsers.XIncludeAwareParserConfiguration")

        _init_logs()

    return jpype


def _unpickle_javaexception(message, trace):
    """
    Helper function for unpickling :class:`JavaException` objects;
    required because :module:`pickle` treats exceptions as opaque
    objects.
    """
    e = JavaException()
    e.message = message
    e.trace = trace

    return e


class JavaException(Exception):
    """
    Stores the Java exception description and Java stacktrace in a
    pickleable object.
    """

    def __init__(self, java_exception=None):
        # we don't store the Java exception object to keep the Python
        # object pickleable
        Exception.__init__(self, str(java_exception))

        if java_exception:
            self.trace = self.get_java_stacktrace(java_exception)

    def __str__(self):
        return ('Java traceback (most recent call last):\n' +
                ''.join(traceback.format_list(self.trace)) +
                self.message)

    def __reduce__(self):
        # Exceptions are treated as 'unknown' objects by pickle unless
        # there is a custom serialization handler
        return (_unpickle_javaexception, (self.message, self.trace))

    @classmethod
    def _get_exception(cls, java_exception):
        """Get the Java object wrapper for the exception."""
        if hasattr(java_exception, '__javaobject__'):
            return java_exception.__javaobject__
        else:
            return java_exception

    @classmethod
    def get_java_stacktrace(cls, java_exception):
        """
        Extracts the stacktrace from a Java exception

        :param java_exception: Java exception object
        :type java_exception: :class:`jpype.JavaException`

        :returns: a list of `(filename, line number, function name, None)`
            tuples (the same format used by the Python `traceback` module,
            except there is no source code).
        """
        java_exception = cls._get_exception(java_exception)
        trace = []

        # traceback module returns inner frame first, Java uses
        # reverse order
        for frame in reversed(java_exception.getStackTrace()):
            trace.append((frame.getFileName(),
                          frame.getLineNumber(),
                          '%s.%s' % (frame.getClassName(),
                                     frame.getMethodName()),
                          None))

        return trace


def jexception(func):
    """
    Decorator to extract the stack trace from a Java exception.

    Re-throws a pickleable :class:`JavaException` object containing the
    exception message and Java stack trace.
    """
    @wraps(func)
    def unwrap_exception(*targs, **tkwargs):  # pylint: disable=C0111
        jvm_instance = jvm()

        try:
            return func(*targs, **tkwargs)
        except jvm_instance.JavaException, e:
            trace = sys.exc_info()[2]

            raise JavaException(e), None, trace

    return unwrap_exception


# alternative implementation using the decorator module; this can be composed
# with the Celery task decorator
# import decorator
#
# def jexception(func):
#     @wraps(func)
#     def unwrap_exception(func, *targs, **tkwargs):
#         jvm_instance = jvm()
#
#         try:
#             return func(*targs, **tkwargs)
#         except jvm_instance.JavaException, e:
#             trace = sys.exc_info()[2]
#
#             raise JavaException(e), None, trace
#
#     return decorator.decorator(unwrap_exception, func)


# Java-exception-aware task decorator for celery
def jtask(func, *args, **kwargs):
    """
    Java-exception aware task decorator for Celery.

    Re-throws the exception as a pickleable :class:`JavaException` object.
    """
    task = celery_task(func, *args, **kwargs)
    run = task.run

    @wraps(run)
    def call_task(*targs, **tkwargs):  # pylint: disable=C0111
        jvm_instance = jvm()

        try:
            return run(*targs, **tkwargs)
        except jvm_instance.JavaException, e:
            trace = sys.exc_info()[2]

            raise JavaException(e), None, trace

    # overwrite the run method of the instance with our wrapper; we
    # can't just pass call_task to celery_task because it does not
    # have the right signature (we would need the decorator module as
    # in the example below)
    task.run = call_task

    return task
