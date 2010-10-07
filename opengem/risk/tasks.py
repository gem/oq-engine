# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Tasks in the risk engine include the following:

 * Input parsing
 * Various calculation steps
 * Output generation
"""

<<<<<<< HEAD
from opengem.logs import HAZARD_LOG, RISK_LOG
from opengem.risk import engines
import opengem.output.risk
from opengem import shapes
from opengem.output import geotiff
from opengem import producer
from opengem.parser import exposure
from opengem.parser import nrml
from opengem.parser import vulnerability
=======
import json
import os
import sys

from celery.decorators import task
>>>>>>> c5dae567a0454c8508ab0e012a50988e1201cc06

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

    TODO(fab): make conditional_loss_poe (set of probabilities of exceedance
    for which the loss computation is done) a list of floats, and read it from
    the job configuration.
    """

    logger = compute_risk.get_logger(**kwargs)

    if conditional_loss_poe is None:
        conditional_loss_poe = DEFAULT_conditional_loss_poe

    # start up memcache client
    memcache_client = memcached.get_client(binary=False)

    # load risk engine, make it use memcache
    # uses hazard, exposure from memcache
    risk_engine = engines.ClassicalPSHABasedLossRatioCalculator(
            job_id, block_id, memcache_client)

    # loop over sites for this block
    # assumes that hazard, assets, and output risk grid are the same
    # (no nearest-neighbour search to find hazard)
    sites_list = memcached.get_sites_from_memcache(memcache_client,
                                                   job_id, block_id)

    logger.debug("sites list for this task w/ job_id %s, block_id %s:\n%s" % (
        job_id, block_id, sites_list))

    for (gridpoint, site) in sites_list:

        logger.debug("processing gridpoint %s, site %s" % (gridpoint, site))
        loss_ratio_curve = risk_engine.compute_loss_ratio_curve(gridpoint)

        if loss_ratio_curve is not None:

            # write to memcache: loss_ratio
            key = identifiers.generate_product_key(job_id,
                block_id, gridpoint, identifiers.LOSS_RATIO_CURVE_KEY_TOKEN)

            logger.debug("RESULT: loss ratio curve is %s, write to key %s" % (
                loss_ratio_curve, key))
            memcache_client.set(key, loss_ratio_curve)
            
            # compute loss curve
            loss_curve = risk_engine.compute_loss_curve(gridpoint, 
                                                        loss_ratio_curve)
            key = identifiers.generate_product_key(job_id, 
                block_id, gridpoint, identifiers.LOSS_CURVE_KEY_TOKEN)

            logger.debug("RESULT: loss curve is %s, write to key %s" % (
                loss_curve, key))
            memcache_client.set(key, loss_curve)
            
            # compute conditional loss
            loss_conditional = engines.compute_loss(loss_curve, 
                                                    conditional_loss_poe)
            key = identifiers.generate_product_key(job_id, 
                block_id, gridpoint, identifiers.CONDITIONAL_LOSS_KEY_TOKEN)

            logger.debug("RESULT: conditional loss is %s, write to key %s" % (
                loss_conditional, key))
            memcache_client.set(key, loss_conditional)

    # assembling final product needs to be done by jobber, collecting the
    # results from all tasks
    return True

<<<<<<< HEAD
def main(vulnerability_model_file, hazard_curve_file, 
            region_file, exposure_file, output_file):
    """ Typically this will run in daemon mode,
    and these tasks will be spawned from AMQP messages.
    In testing mode, we run directly against a simple set
    of input files."""
    
    
    # TODO(JMC): Support portfolio of sites, not just regions
    region_constraint = shapes.RegionConstraint.from_file(region_file)
    region_constraint.cell_size = 1.0
                                                            
    hazard_curves = {}
    nrml_parser = nrml.NrmlFile(hazard_curve_file)
    attribute_constraint = \
        producer.AttributeConstraint({'IMT' : 'MMI'})
    
    HAZARD_LOG.debug("Going to parse hazard curves")
    for site, hazard_curve_data in nrml_parser.filter(
            region_constraint, attribute_constraint):
        gridpoint = region_constraint.grid.point_at(site)
        hazard_curve = shapes.FastCurve(zip(hazard_curve_data['IML'], 
                                hazard_curve_data['Values']))
        hazard_curves[gridpoint] = hazard_curve
        HAZARD_LOG.debug("Loading hazard curve %s at %s: %s", 
                    hazard_curve, site.latitude,  site.longitude)
    
    vulnerability.load_vulnerability_model(vulnerability_model_file)
    
    exposure_portfolio = {}
    exposure_parser = exposure.ExposurePortfolioFile(exposure_file)
    for site, asset in exposure_parser.filter(region_constraint):
        gridpoint = region_constraint.grid.point_at(site)
        exposure_portfolio[gridpoint] = asset
        RISK_LOG.debug("Loading asset at %s: %s - %s", 
                        site.latitude,  site.longitude, asset)
    
    risk_engine = engines.ProbabilisticLossRatioCalculator(
            hazard_curves, exposure_portfolio)
    
    ratio_results = {}
    loss_curves = {}
    losses_one_perc = {}
    interval = 0.01
    
    for gridpoint in region_constraint.grid:
        # TODO(jmc): Spawn a task for each larger region, eg
        # Make smaller sets of sites and batch them off
        site = gridpoint.site
        val = risk_engine.compute_loss_ratio_curve(gridpoint)
        if val:
            ratio_results[gridpoint] = val
            loss_curve = risk_engine.compute_loss_curve(
                            gridpoint, ratio_results[gridpoint])
            print loss_curve
            loss_curves[gridpoint] = loss_curve
            print loss_curve
            losses_one_perc[gridpoint] = engines.compute_loss(
                                    loss_curve, interval)
=======
>>>>>>> c5dae567a0454c8508ab0e012a50988e1201cc06
    
