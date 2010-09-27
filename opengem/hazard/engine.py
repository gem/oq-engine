"""
Top-level managers for hazard computation.
"""

import os

import jpype

from opengem import logs

log = logs.HAZARD_LOG


def init_engine():
    jarpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../lib")
    log.debug("Jarpath is %s", jarpath)
    jpype.startJVM(jpype.getDefaultJVMPath(), " -Xms2048m -Xmx2048m ", "-Djava.ext.dirs=%s" % jarpath)
    input_module.init_paths(input_path, jpype)
    