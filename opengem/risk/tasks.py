# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Tasks in the risk engine include the following:

 * Input parsing
 * Various calculation steps
 * Output generation
"""

from celery.decorators import task

from opengem import flags
from opengem import kvs 
from opengem import risk

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

    TODO(fab): make conditional_loss_poe (set of probabilities of exceedance
    for which the loss computation is done) a list of floats, and read it from
    the job configuration.
    """

    logger = compute_risk.get_logger(**kwargs)

    if conditional_loss_poe is None:
        conditional_loss_poe = DEFAULT_conditional_loss_poe

    # start up memcache client
    memcache_client = kvs.get_client(binary=False)

    # load risk engine, make it use memcache
    # uses hazard, exposure from memcache
    risk_engine = engines.ClassicalPSHABasedLossRatioCalculator(
            job_id, block_id, memcache_client)

    # loop over sites for this block
    # assumes that hazard, assets, and output risk grid are the same
    # (no nearest-neighbour search to find hazard)
    sites_list = kvs.get_sites_from_memcache(memcache_client,
                                                   job_id, block_id)

    logger.debug("sites list for this task w/ job_id %s, block_id %s:\n%s" % (
        job_id, block_id, sites_list))

    for (gridpoint, site) in sites_list:

        logger.debug("processing gridpoint %s, site %s" % (gridpoint, site))
        loss_ratio_curve = risk_engine.compute_loss_ratio_curve(gridpoint)

        if loss_ratio_curve is not None:

            # write to memcache: loss_ratio
            key = kvs.generate_product_key(job_id,
                risk.LOSS_RATIO_CURVE_KEY_TOKEN, block_id, gridpoint)

            logger.debug("RESULT: loss ratio curve is %s, write to key %s" % (
                loss_ratio_curve, key))
            memcache_client.set(key, loss_ratio_curve)
            
            # compute loss curve
            loss_curve = risk_engine.compute_loss_curve(gridpoint, 
                                                        loss_ratio_curve)
            key = kvs.generate_product_key(job_id, 
                risk.LOSS_CURVE_KEY_TOKEN, block_id, gridpoint)

            logger.debug("RESULT: loss curve is %s, write to key %s" % (
                loss_curve, key))
            memcache_client.set(key, loss_curve)
            
            # compute conditional loss
            loss_conditional = engines.compute_loss(loss_curve, 
                                                    conditional_loss_poe)
            key = kvs.generate_product_key(job_id, 
                risk.CONDITIONAL_LOSS_KEY_TOKEN, block_id, gridpoint)

            logger.debug("RESULT: conditional loss is %s, write to key %s" % (
                loss_conditional, key))
            memcache_client.set(key, loss_conditional)

    # assembling final product needs to be done by jobber, collecting the
    # results from all tasks
    return True
