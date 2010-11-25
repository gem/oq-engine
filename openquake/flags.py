"""
Global command-line flags for configuration, plus a wrapper around gflags.
In the future, we may extend this to use either cement, or the nova 
gflags extensions.
"""

from gflags import *  # pylint: disable=F0401
from gflags import FLAGS # pylint: disable=F0401
from gflags import DEFINE_string # pylint: disable=F0401
from gflags import DEFINE_boolean, DEFINE_integer # pylint: disable=F0401

(_, _, _, _) = FLAGS, DEFINE_boolean, DEFINE_integer, DEFINE_string

DEFINE_string('debug', 'warn', 
    'Turns on debug logging and verbose output')