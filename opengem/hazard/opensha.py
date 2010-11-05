"""
Top-level managers for hazard computation.
"""

import os

from opengem import java
from opengem.settings import MEMCACHED_PORT, MEMCACHED_HOST
from opengem import config
from opengem.logs import LOG


def preload(job_file):
    pass

def generate_source_model(job_file):
    """Generates an Earthquake Rupture Forecast, using the source zones and
    logic trees specified in the job config file. Note that this has to be
    done using the file itself, since it has nested references to other files.
    
    job_file should be an absolute path.
    """
    jpype = java.jvm()
    HazardEngineClass = jpype.JClass("org.gem.engine.CommandLineCalculator")
    engine = HazardEngineClass(guarantee_file(job_file))
    erf_data = engine.getJsonSourceList()        
    # erf = engine.sampleGemLogicTreeERF(erf_data.getErfLogicTree())
    return erf


def guarantee_file(file_spec):
    """Resolves a file_spec (http, local relative or absolute path, git url,
    etc.) to an absolute path to a (possibly temporary) file."""
    return file_spec


def _introspect_erf(erf):
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
    sources = erf.getSourceList()
    for source in sources:
        LOG.debug(source.duration)
        LOG.debug(source.name)
        LOG.debug(source.getRuptureList())


# MemcacheClass = jpype.JClass(
#     "org.gem.engine.hazard.memcached.Cache")
# cache = MemcacheClass(MEMCACHED_HOST, MEMCACHED_PORT)
# my_job = config.Job.from_files(os.path.abspath("tests/data/risk-config.gem"),
#                                 os.path.abspath("tests/data/hazard-config.gem"))
# my_job.to_memcached()
# engine = HazardEngineClass(cache, my_job.key)
# engine.doCalculation()