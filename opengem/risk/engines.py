# -*- coding: utf-8 -*-
"""
Top-level managers for computation classes.
"""

import json

from opengem import identifiers
from opengem import logs
from opengem import memcached
from opengem import shapes

from opengem.parser import vulnerability
from opengem.risk import classical_psha_based

logger = logs.RISK_LOG

class ClassicalPSHABasedLossRatioCalculator(object):
    """Computes loss ratio curves based on hazard curves and 
    exposure portfolios"""

    def __init__(self, job_id, block_id, memcache_client=None):
        """ Prepare the calculator for computations"""

        self.job_id = job_id
        self.block_id = block_id

        if memcache_client is not None:
            self.memcache_client = memcache_client
        else:
            self.memcache_client = memcached.get_client(binary=False)

        self.vulnerability_curves = \
            vulnerability.load_vulnerability_curves_from_memcache(
                self.memcache_client, self.job_id)

        # self.vulnerability_curves is a dict of {string: FastCurve},
        # FastCurve.values is OrderedDict key: [v1, v2]
        logger.debug("ProbabilisticLossRatioCalculator init: vuln curves are")
        for k,v in self.vulnerability_curves.items():
            logger.debug("%s: %s" % (k, v.values))
 
    def compute_loss_ratio_curve(self, gridpoint):
        """ Returns the loss ratio curve for a single gridpoint"""

        # check in memcache if hazard and exposure for gridpoint are there
        memcache_key_hazard = identifiers.generate_product_key(self.job_id, 
            self.block_id, gridpoint, identifiers.HAZARD_CURVE_KEY_TOKEN)
       
        hazard_curve_json = self.memcache_client.get(memcache_key_hazard)
        logger.debug("hazard curve as JSON: %s" % hazard_curve_json)
 
        hazard_curve = shapes.EMPTY_CURVE
        hazard_curve.from_json(hazard_curve_json)

        logger.debug("hazard curve at key %s is %s" % (memcache_key_hazard, 
                                                    hazard_curve.values))
        if hazard_curve is None:
            logger.debug("no hazard curve found")
            return None

        memcache_key_exposure = identifiers.generate_product_key(self.job_id, 
            self.block_id, gridpoint, identifiers.EXPOSURE_KEY_TOKEN)
        
        asset = memcached.get_value_json_decoded(self.memcache_client,
                                                 memcache_key_exposure)

        logger.debug("asset at key %s is %s" % (memcache_key_exposure, asset))

        if asset is None:
            logger.debug("no asset found")
            return None

        logger.debug("compute method: vuln curves are")
        for k,v in self.vulnerability_curves.items():
            logger.debug("%s: %s" % (k, v.values))

        vulnerability_curve = \
            self.vulnerability_curves[asset['VulnerabilityFunction']]

        # selected vuln function is FastCurve
        return classical_psha_based.compute_loss_ratio_curve(
            vulnerability_curve, hazard_curve)
    
    def compute_loss_curve(self, gridpoint, loss_ratio_curve):
        """ Returns the loss curve based on loss ratio and exposure"""
        
        if loss_ratio_curve is None:
            return None

        memcache_key_exposure = identifiers.generate_product_key(self.job_id,
            self.block_id, gridpoint, identifiers.EXPOSURE_KEY_TOKEN)
        asset = memcached.get_value_json_decoded(self.memcache_client,
                                                 memcache_key_exposure)
        if asset is None:
            return None

        return classical_psha_based.compute_loss_curve(
            loss_ratio_curve, asset['AssetValue'])


def compute_loss(loss_curve, pe_interval):
    """Interpolate loss for a specific probability of exceedance interval"""
    loss = classical_psha_based.compute_conditional_loss(loss_curve, 
                                                         pe_interval)
    return loss
