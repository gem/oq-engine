"""
Global command-line flags for configuration, plus a wrapper around gflags.
In the future, we may extend this to use either cement, or the nova 
gflags extensions.
"""

# pylint: disable=W0401, W0622, W0614

from gflags import * 
from gflags import FLAGS
from gflags import DEFINE_string
from gflags import DEFINE_boolean, DEFINE_integer

(_, _, _, _) = FLAGS, DEFINE_boolean, DEFINE_integer, DEFINE_string

DEFINE_string('debug', 'warn', 
    'Turns on debug logging and verbose output')
