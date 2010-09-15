"""
Set up some system-wide loggers
TODO(jmc): init_logs should take filename, or sysout
TODO(jmc): support debug level per logger.

"""
import logging

from opengem import flags
FLAGS = flags.FLAGS

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warn': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

RISK_LOG = logging.getLogger("risk")
HAZARD_LOG = logging.getLogger("hazard")
LOG = logging.getLogger()

def init_logs():
    
    
    level = LEVELS.get(FLAGS.debug, logging.ERROR)
    logging.basicConfig(level=level)
    
    LOG.setLevel(level)
    RISK_LOG.setLevel(level)
    HAZARD_LOG.setLevel(level)    