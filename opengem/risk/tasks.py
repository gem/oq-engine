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
from opengem import memcached
from opengem import identifiers
from opengem.logs import HAZARD_LOG, RISK_LOG
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
    memcache_key_sites = identifiers.get_product_key(
        job_id, block_id, None, identifiers.SITES_KEY_TOKEN)

    memcache_result = memcache_client.get(memcache_key_sites)
    decoder = json.JSONDecoder()

    # assume that memcache has a JSON-serialized list of sites 
    sites_list = decoder.decode(memcache_result)

    print sites_list

    for gridpoint in sites_list:

        logger.info("processing gridpoint %s" % (gridpoint))
        loss_ratio_curve = risk_engine.compute_loss_ratio_curve(gridpoint)

        if loss_ratio_curve is not None:

            # write to memcache: loss_ratio
            key = identifiers.get_product_key(job_id,
                block_id, gridpoint,identifiers.LOSS_RATIO_CURVE_KEY_TOKEN)

            memcache_client.set(key, loss_ratio_curve)
            #ratio_results[gridpoint] = val
            logger.info("wrote loss ratio curve to key %s" % (key))

            print "RESULT: loss ratio curve is %s" % loss_ratio_curve

            # compute loss curve
            loss_curve = risk_engine.compute_loss_curve(gridpoint, 
                                                        loss_ratio_curve)
            key = identifiers.get_product_key(job_id, 
                block_id, gridpoint, identifiers.LOSS_CURVE_KEY_TOKEN)

            memcache_client.set(key, loss_curve)
            #loss_curves[gridpoint] = loss_curve
            #print loss_curve
            logger.info("wrote loss curve to key %s" % (key))

            print "RESULT: loss curve is %s" % loss_curve

            # compute conditional loss
            loss_conditional = engines.compute_loss(loss_curve, 
                                                    conditional_loss_poe)
            key = identifiers.get_product_key(job_id, 
                block_id, gridpoint, identifiers.CONDITIONAL_LOSS_KEY_TOKEN)

            memcache_client.set(key, loss_conditional)
            #losses_one_perc[gridpoint] = 
            logger.info("wrote conditional loss to key %s" % (key))

            print "RESULT: conditional loss is %s" % loss_conditional
    
    return True

    # assembling final product needs to be done by jobber


# TODO(jmc): rather than passing files in here, determine the right 
# parser to use or create in the binary, and pass in loaded parsers.
# This will support config setting of cell_size, etc.

#def main(vulnerability_model_file, hazard_curve_file, 
            #region_file, exposure_file, output_file):
    #""" Typically this will run in daemon mode,
    #and these tasks will be spawned from AMQP messages.
    #In testing mode, we run directly against a simple set
    #of input files."""
    
    
    ## TODO(JMC): Support portfolio of sites, not just regions
    #region_constraint = shapes.RegionConstraint.from_file(region_file)
    #region_constraint.cell_size = 1.0
                                                            
    #hazard_curves = {}
    #shaml_parser = shaml_output.ShamlOutputFile(hazard_curve_file)
    #attribute_constraint = \
        #producer.AttributeConstraint({'IMT' : 'MMI'})
    
    #HAZARD_LOG.debug("Going to parse hazard curves")
    #for site, hazard_curve_data in shaml_parser.filter(
            #region_constraint, attribute_constraint):
        #gridpoint = region_constraint.grid.point_at(site)
        #hazard_curve = shapes.FastCurve(zip(hazard_curve_data['IML'], 
                                #hazard_curve_data['Values']))
        #hazard_curves[gridpoint] = hazard_curve
        #HAZARD_LOG.debug("Loading hazard curve %s at %s: %s", 
                    #hazard_curve, site.latitude,  site.longitude)
    
    #vulnerability.load_vulnerability_model(vulnerability_model_file)
    
    #exposure_portfolio = {}
    #exposure_parser = exposure.ExposurePortfolioFile(exposure_file)
    #for site, asset in exposure_parser.filter(region_constraint):
        #gridpoint = region_constraint.grid.point_at(site)
        #exposure_portfolio[gridpoint] = asset
        #RISK_LOG.debug("Loading asset at %s: %s - %s", 
                        #site.latitude,  site.longitude, asset)
    
    #risk_engine = engines.ProbabilisticLossRatioCalculator(
            #hazard_curves, exposure_portfolio)
    
    #ratio_results = {}
    #loss_curves = {}
    #losses_one_perc = {}
    #interval = 0.01
    
    #for gridpoint in region_constraint.grid:
        ## TODO(jmc): Spawn a task for each larger region, eg
        ## Make smaller sets of sites and batch them off
        #site = gridpoint.site
        #val = risk_engine.compute_loss_ratio_curve(gridpoint)
        #if val:
            #ratio_results[gridpoint] = val
            #loss_curve = risk_engine.compute_loss_curve(
                            #gridpoint, ratio_results[gridpoint])
            #print loss_curve
            #loss_curves[gridpoint] = loss_curve
            #print loss_curve
            #losses_one_perc[gridpoint] = engines.compute_loss(
                                    #loss_curve, interval)
    
    ## TODO(jmc): Pick output generator from config or cli flags
    #output_generator = opengem.output.risk.RiskXMLWriter("loss-curves.xml")
    #output_generator.serialize(loss_curves)
    ##output_generator = output.SimpleOutput()
    ##output_generator.serialize(ratio_results)
    #output_generator = geotiff.GeoTiffFile(output_file, region_constraint.grid)
    #output_generator.serialize(losses_one_perc)
