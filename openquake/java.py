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

from amqplib import client_0_8 as amqp
import jpype
import os
import sys
import traceback

from celery.decorators import task as celery_task

from functools import wraps

from openquake import flags

FLAGS = flags.FLAGS

# Settings this flag to true pipes Java stderr and stdout to python stderr and
# stdout and has a noticeable effect only when python stderr and stdout are
# redefined.  This happens when running inside celery, where sys.stdout and
# sys.stderr are redefined to be an instance of celery.log.LoggingProxy.  Then
# every line printed by java to stdout will be prefixed by a timestamp and some
# information about the worker.
flags.DEFINE_boolean('capture_java_debug', True,
    "Pipe Java stderr and stdout to python stderr and stdout")

JAVA_CLASSES = {
    'LogicTreeProcessor': "org.gem.engine.LogicTreeProcessor",
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
    "MDC": "org.apache.log4j.MDC",
}

LOG4J_PROPERTIES_PATH = os.path.abspath(
                            os.path.join(os.path.dirname(__file__),
                            "config/log4j.properties"))


def jclass(class_key):
    """Wrapper around jpype.JClass for short class names"""
    jvm()
    return jpype.JClass(JAVA_CLASSES[class_key])


def _set_java_log_level(level):
    """Sets the log level of the java logger.

    :param level: a string, one of the logging levels defined in
    :file:`logs.py`
    """

    if level == 'CRITICAL':
        level = 'FATAL'

    root_logger = jpype.JClass("org.apache.log4j.Logger").getRootLogger()
    jlevel = jpype.JClass("org.apache.log4j.Level").toLevel(level)
    root_logger.setLevel(jlevel)


def _setup_java_capture(out, err):
    """
    Pipes the java System.out and System.error into python files.

    :param out: python file-like object (must implement the write method)
    :param err: python file-like objectt (must implement the write method)
    """
    mystream = jpype.JProxy("org.gem.IPythonPipe", inst=out)
    errstream = jpype.JProxy("org.gem.IPythonPipe", inst=err)
    outputstream = jpype.JClass("org.gem.PythonOutputStream")()
    err_stream = jpype.JClass("org.gem.PythonOutputStream")()
    outputstream.setPythonStdout(mystream)
    err_stream.setPythonStdout(errstream)

    ps = jpype.JClass("java.io.PrintStream")
    jpype.java.lang.System.setOut(ps(outputstream))
    jpype.java.lang.System.setErr(ps(err_stream))


class AMQPConnection(object):
    """Implement the Java `org.gem.log.AMQPConnection` interface"""
    # pylint: disable=C0103

    def __init__(self):
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.virtualhost = None
        self.connection = None
        self.channel = None

    def setHost(self, host):
        """Set the AMQP host"""
        self.host = host

    def setPort(self, port):
        """Set the AMQP port"""
        self.port = port

    def setUsername(self, username):
        """Set the AMQP user name"""
        self.username = username

    def setPassword(self, password):
        """Set the AMQP password"""
        self.password = password

    def setVirtualHost(self, virtualhost):
        """Set the AMQP virtualhost"""
        self.virtualhost = virtualhost

    def close(self):
        """Close the AMQP connection"""
        channel = self.channel
        connection = self.connection

        self.channel = self.connection = None

        if channel:
            channel.close()
        if connection:
            connection.close()

    def publish(self, exchange, routing_key, _timestamp,
                _level, message):
        """Send a new message to the queue"""
        channel = self.getChannel()
        msg = amqp.Message(body=message)

        channel.basic_publish(msg, exchange=exchange,
                              routing_key=routing_key)

    def getChannel(self):
        """Return the existing connection or create a new one"""
        if self.channel:
            return self.channel

        host_port = '%s:%d' % (self.host, self.port or 5672)
        self.connection = amqp.Connection(host=host_port,
                                          userid=self.username,
                                          password=self.password,
                                          virtual_host=self.virtualhost,
                                          insist=False)
        self.channel = self.connection.channel()

        return self.channel


class AMQPFactory(object):
    """Implement the Java org.gem.log.AMQPConnectionFactory interface"""
    # pylint: disable=C0103

    def getConnection(self):  # pylint: disable=R0201
        """Return a new `org.gem.log.AMQPConnection` instance"""
        return jvm().JProxy("org.gem.log.AMQPConnection",
                            inst=AMQPConnection())


def _setup_java_amqp():
    """Set the connection factory for the Log4j AMQP log appender"""
    amqpfactory = jpype.JProxy("org.gem.log.AMQPConnectionFactory",
                               inst=AMQPFactory())
    amqpappender = jpype.JClass("org.gem.log.AMQPAppender")
    amqpappender.setConnectionFactory(amqpfactory)


def jvm(max_mem=None):
    """Return the jpype module, after guaranteeing the JVM is running and
    the classpath has been loaded properly."""
    jarpaths = (os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "../dist")),
                '/usr/share/java')

    if not jpype.isJVMStarted():
        max_mem = get_jvm_max_mem(max_mem)
        jpype.startJVM(jpype.getDefaultJVMPath(),
            "-Djava.ext.dirs=%s:%s" % jarpaths,
            # force the default Xerces parser configuration, otherwise
            # some random system-installed JAR might override it
            "-Dorg.apache.xerces.xni.parser.XMLParserConfiguration=" \
                "org.apache.xerces.parsers.XIncludeAwareParserConfiguration",
            # "-Dlog4j.debug", # turn on log4j internal debugging
            "-Dlog4j.configuration=file://%s" % LOG4J_PROPERTIES_PATH,
            "-Xmx%sM" % max_mem)

        # override the log level set in log4j configuration file this can't be
        # done on the JVM command line (i.e. -Dlog4j.rootLogger= is not
        # supported by log4j)
        _set_java_log_level(FLAGS.debug.upper())

        if FLAGS.capture_java_debug:
            _setup_java_capture(sys.stdout, sys.stderr)

        _setup_java_amqp()

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
