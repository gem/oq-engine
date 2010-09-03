#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Tasks in the risk engine include the following:

 * Input parsing
 * Various calculation steps
 * Output generation
 
"""

import logging
import os
import sys

import eventlet
from eventlet import event
from eventlet import greenpool
from eventlet import queue

logging = eventlet.import_patched('logging')

from opengem.risk import engines
from opengem import output
from opengem import shapes
from opengem.output import geotiff
from opengem.parser import exposure
from opengem.parser import shaml_output
from opengem.parser import vulnerability
from opengem import state
STATE = state.STATE

from opengem import flags
FLAGS = flags.FLAGS


STATE['vulnerability_curves'] = {}
def ingest_vulnerability(path):
    # STATE['vulnerability_curves']['brick'] = ([0.2, 0.3, 0.4, 0.9, 0.95, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    # STATE['vulnerability_curves']['stone'] = ([0.2, 0.21, 0.41, 0.94, 0.95, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    # STATE['vulnerability_curves']['wood'] = ([0.0, 0.0, 0.0, 0.0, 0.0, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

    for data in vulnerability.VulnerabilityModelFile(path):
        logging.debug('found vulnerability data')
        STATE['vulnerability_curves'][data['ID']] = data
    logging.debug('vulnerability done')
    

# TODO(jmc): rather than passing files in here, determine the right parser to 
# use or create in the binary, and pass in loaded parsers.
# This will support config setting of cell_size, etc.

def main(vulnerability_model_file, hazard_curve_file, region_file, exposure_file, output_file):
    """ Typically this will run in daemon mode,
    and these tasks will be spawned from AMQP messages.
    In testing mode, we run directly against a simple set
    of input files."""
    
    # This is our pool of coroutines
    pool = greenpool.GreenPool()
    
    # TODO(JMC): Support portfolio of sites, not just regions
    region_constraint = shapes.RegionConstraint.from_file(region_file)
    region_constraint.cell_size = 1.0
                                                            
    hazard_curves = {}
    shaml_parser = shaml_output.ShamlOutputFile(hazard_curve_file)
    for site, hazard_curve in shaml_parser.filter(region_constraint):
        gridpoint = region_constraint.grid.point_at(site)
        print "%s: %s" % (gridpoint, hazard_curve)
        hazard_curves[gridpoint] = hazard_curve
       
    ingest_vulnerability(vulnerability_model_file)
    
    # Since we've got hazard curves, let's do probabilistic assessment
    ratio_engine = engines.ProbabilisticLossRatioCalculator(
        hazard_curves, STATE['vulnerability_curves'])
    
    exposure_portfolio = {}
    exposure_parser = exposure.ExposurePortfolioFile(exposure_file)
    for site, asset in exposure_parser.filter(region_constraint):
        gridpoint = region_constraint.grid.point_at(site)
        print "%s: %s" % (gridpoint, asset)
        exposure_portfolio[gridpoint] = asset
    loss_engine = engines.ProbabilisticLossCalculator(exposure_portfolio)
    
    ratio_results = {}
    loss_curves = {}
    losses_one_perc = {}
    interval = 0.01
    
    for gridpoint in region_constraint.grid:
        # TODO(jmc): Spawn a task for each larger region, eg
        # Make smaller sets of sites and batch them off
        site = gridpoint.site
        val = ratio_engine.compute(gridpoint)
        if val:
            ratio_results[gridpoint] = val
            loss_curve = loss_engine.compute(gridpoint, ratio_results[gridpoint])
            loss_curves[gridpoint] = loss_curve
            losses_one_perc[gridpoint] = engines.loss_from_curve(loss_curve, interval)
    
    # TODO(jmc): Pick output generator from config or cli flags
    output_generator = output.SimpleOutput()
    output_generator.serialize(ratio_results)
    output_generator.serialize(loss_curves)
    output_generator = geotiff.GeoTiffFile(output_file, region_constraint.grid)
    output_generator.serialize(losses_one_perc)

    
    # These are the computations we are doing
    # loss_grid = computation.Grid(pool, cell_factory=loss.LossComputation)
    # loss_ratio_grid = computation.Grid(
    #         pool, cell_factory=loss_ratio.LossRatioComputation)

    # These are our output formats
    # TODO(jmc): Make this grid the bounding box of the region
    # 
    # image_grid = grid.Grid(ncols=100, nrows=100, 
    #                 xllcorner=123.25, yllcorner=48.35, cellsize=0.1)
    # loss_map = geotiff.GeoTiffFile(FLAGS.loss_map, image_grid)
    # loss_ratio_map = geotiff.GeoTiffFile(FLAGS.loss_ratio_map, image_grid)