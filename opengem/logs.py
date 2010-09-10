import logging

from opengem import flags
FLAGS = flags.FLAGS

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warn': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

risk_log = logging.getLogger("risk")
hazard_log = logging.getLogger("hazard")
general_log = logging.getLogger()

def init_logs():
    
    
    level=LEVELS.get(FLAGS.debug, logging.ERROR)
    logging.basicConfig(level=level)
    
    general_log.setLevel(level)
    risk_log.setLevel(level)
    hazard_log.setLevel(level)    
    
    # 
    # ch = logging.StreamHandler()
    # formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # ch.setFormatter(formatter)
    # ch.setLevel(level)
    # 
    # 
    # # add ch to logger
    # general_log.addHandler(ch)
    # risk_log.addHandler(ch)
    # hazard_log.addHandler(ch)