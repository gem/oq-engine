"""
Top-level managers for hazard computation.
"""

import os

from opengem import java
from opengem.kvs import MEMCACHED_PORT, MEMCACHED_HOST
from opengem import config
from opengem.logs import LOG

def run_hazard():
    jpype = java.jvm()
    
    LOG.debug("Constructed a jvm")
    HazardEngineClass = jpype.JClass(
        "org.gem.engine.CommandLineCalculator")
            
    MemcacheClass = jpype.JClass(
        "org.gem.engine.hazard.memcached.Cache")
    cache = MemcacheClass(MEMCACHED_HOST, MEMCACHED_PORT)
    
    # Build source list
    # input_model = jvm.JClass()
    # 
    # engine = GemComputeModel(model.getList(), modelName,
    #             gmpeLogicTree.getGemLogicTree(), latmin, latmax, lonmin,
    #             lonmax, delta, probLevel, outDir, outputHazCurve, calcSet);
    my_job = config.Job.from_files(os.path.abspath("tests/data/risk-config.gem"),
                                    os.path.abspath("tests/data/hazard-config.gem"))
    my_job.to_memcached()
    engine = HazardEngineClass(cache, my_job.key)
    engine.doCalculation()