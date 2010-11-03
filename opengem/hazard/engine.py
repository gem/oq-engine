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
    
    # Constructing HazardEngine from files directly, for ERF generation
    engine = HazardEngineClass(os.path.abspath("tests/data/hazard-config.gem"))
    erf_data = engine.createErfLogicTreeData()
    LOG.debug("ERF DATA is %s" % erf_data)
    LOG.debug(dir(erf_data))
    
    erf_data.erfLogicTree.printGemLogicTreeStructure()
    
    erf = engine.sampleGemLogicTreeERF(erf_data.getErfLogicTree())
    LOG.debug("ERF is %s" % erf)
    sources = erf.getSourceList()
    for source in sources:
        # DEBUG:root:['allSourceLocs', 'aveRupTopVersusMag', 'computeApproxTotalProbAbove', 
        # 'computeTotalProb', 'computeTotalProbAbove', 'defaultHypoDepth', 
        # 'drawRandomEqkRuptures', 'duration', 'equals', 'firstStrike', 
        # 'focalMechanisms', 'getAllSourceLocs', 'getClass', 'getDuration', 
        # 'getInfo', 'getMinDistance', 'getMinMag', 'getName', 'getNumRuptures',
        #  'getRegion', 'getRupture', 'getRuptureClone', 'getRuptureList', 
        # 'getRupturesIterator', 'getSourceMetadata', 'getSourceSurface', 
        # 'getTectonicRegionType', 'gridReg', 'gridResolution', 'hashCode', 
        # 'info', 'isPoissonian', 'isPoissonianSource', 'isSourcePoissonian', 
        # 'location', 'lowerSeisDepth', 'magFreqDists', 'magScalingRel', 
        # 'maxLength', 'minMag', 'name', 'nodeWeights', 'notify', 'notifyAll', 
        # 'numRuptures', 'numStrikes', 'pointSources', 'probEqkRupture', 
        # 'probEqkRuptureList', 'rates', 'reg', 'region', 'ruptureList', 
        # 'rupturesIterator', 'setDuration', 'setInfo', 'setTectonicRegionType',
        #  'sourceIndex', 'sourceMetadata', 'sourceSurface', 
        # 'tectonicRegionType', 'toString', 'wait']
        LOG.debug(source.duration)
        LOG.debug(source.name)
        LOG.debug(source.getRuptureList())
    # LOG.debug(erf_data.toString())
    # engine = HazardEngineClass(cache, my_job.key)
    # engine.doCalculation()