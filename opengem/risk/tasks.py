# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Tasks in the risk engine include the following:

 * Input parsing
 * Various calculation steps
 * Output generation
"""

import json
import os
import sys

from celery.decorators import task

from opengem import flags
from opengem import identifiers
from opengem import memcached

from opengem.risk import engines

FLAGS = flags.FLAGS

DEFAULT_conditional_loss_poe = 0.01

@task
def compute_risk(job_id, block_id, conditional_loss_poe=None, **kwargs):
    """This task computes risk for a block of sites. It requires to have
    pre-initialized in memcache:
     1) list of sites
     2) hazard curves
     3) exposure portfolio (=assets)
     4) vulnerability
    """

    logger = compute_risk.get_logger(**kwargs)

    if conditional_loss_poe is None:
        conditional_loss_poe = DEFAULT_conditional_loss_poe

    # start up memcache client
    memcache_client = memcached.get_client(binary=False)

    # load risk engine, make it use memcache
    # uses hazard, exposure from memcache
    risk_engine = engines.ProbabilisticLossRatioCalculator(
            job_id, block_id, memcache_client)

    # loop over sites for this block
    # assumes that hazard, assets, and risk grid are the same
    # (no nearest-neighbour search)
    #memcache_key_sites = identifiers.get_product_key(
        #job_id, block_id, None, identifiers.SITES_KEY_TOKEN)

    #memcache_result = memcache_client.get(memcache_key_sites)
    #decoder = json.JSONDecoder()

    ## assume that memcache has a JSON-serialized list of sites 
    #sites_list = decoder.decode(memcache_result)

    sites_list = memcached.get_sites_from_memcache(memcache_client,
                                                job_id, block_id)

    logger.debug("sites list for this task w/ job_id %s, block_id %s:\n%s" % (
        job_id, block_id, sites_list))

    for (gridpoint, site) in sites_list:

        logger.debug("processing gridpoint %s, site %s" % (gridpoint, site))
        loss_ratio_curve = risk_engine.compute_loss_ratio_curve(gridpoint)

        if loss_ratio_curve is not None:

            # write to memcache: loss_ratio
            key = identifiers.get_product_key(job_id,
                block_id, gridpoint,identifiers.LOSS_RATIO_CURVE_KEY_TOKEN)

            memcache_client.set(key, loss_ratio_curve)
            logger.debug("wrote loss ratio curve to key %s" % (key))

            logger.debug("RESULT: loss ratio curve is %s" % loss_ratio_curve)

            # compute loss curve
            loss_curve = risk_engine.compute_loss_curve(gridpoint, 
                                                        loss_ratio_curve)
            key = identifiers.get_product_key(job_id, 
                block_id, gridpoint, identifiers.LOSS_CURVE_KEY_TOKEN)

            memcache_client.set(key, loss_curve)
            logger.debug("wrote loss curve to key %s" % (key))

            logger.debug("RESULT: loss curve is %s" % loss_curve)

            # compute conditional loss
            loss_conditional = engines.compute_loss(loss_curve, 
                                                    conditional_loss_poe)
            key = identifiers.get_product_key(job_id, 
                block_id, gridpoint, identifiers.CONDITIONAL_LOSS_KEY_TOKEN)

            memcache_client.set(key, loss_conditional)
            logger.debug("wrote conditional loss to key %s" % (key))

            logger.debug("RESULT: conditional loss is %s" % loss_conditional)
    
    # assembling final product needs to be done by jobber, collecting the
    # results from all tasks
    return True

    
