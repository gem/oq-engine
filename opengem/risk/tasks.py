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
from ordereddict import *

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


STATE['vulnerability_curves_raw'] = {}
STATE['vulnerability_curves'] = {}
def ingest_vulnerability(path):
    # STATE['vulnerability_curves']['brick'] = ([0.2, 0.3, 0.4, 0.9, 0.95, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    # STATE['vulnerability_curves']['stone'] = ([0.2, 0.21, 0.41, 0.94, 0.95, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    # STATE['vulnerability_curves']['wood'] = ([0.0, 0.0, 0.0, 0.0, 0.0, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

    for data in vulnerability.VulnerabilityModelFile(path):
        # logging.debug('found vulnerability data')
        curve_data = OrderedDict()
        pairs = zip(data['LossRatioValues'], data['CoefficientVariationValues'])
        print data['IntensityMeasureValues']
        for idx, IML in enumerate(data['IntensityMeasureValues']):
            curve_data[IML] = pairs[idx]
        STATE['vulnerability_curves_raw'][data['ID']] = data    
        STATE['vulnerability_curves'][data['ID']] = shapes.Curve(curve_data)
    # logging.debug('vulnerability done')
    

# TODO(jmc): rather than passing files in here, determine the right parser to 
# use or create in the binary, and pass in loaded parsers.
# This will support config setting of cell_size, etc.

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
    shaml_parser = shaml_output.ShamlOutputFile(hazard_curve_file)
    attribute_constraint = \
        shaml_output.ShamlOutputConstraint({'IMT' : 'PGA'})
    
    for site, hazard_curve_data in shaml_parser.filter(region_constraint, attribute_constraint):
        gridpoint = region_constraint.grid.point_at(site)
        print "Hazard data looks like %s" % zip(hazard_curve_data['IML'], hazard_curve_data['Values'])
        hazard_curve = shapes.FastCurve(zip(hazard_curve_data['IML'], hazard_curve_data['Values']))
        hazard_curves[gridpoint] = hazard_curve
        print "Loading hazard curve %s at %s: %s" % (hazard_curve, site.latitude,  site.longitude)
    
    print hazard_curves
    
    ingest_vulnerability(vulnerability_model_file)
    
    exposure_portfolio = {}
    exposure_parser = exposure.ExposurePortfolioFile(exposure_file)
    for site, asset in exposure_parser.filter(region_constraint):
        gridpoint = region_constraint.grid.point_at(site)
        exposure_portfolio[gridpoint] = asset
        print "Loading asset at %s: %s" % (site.latitude,  site.longitude)
    
        
    risk_engine = engines.ProbabilisticLossRatioCalculator(
            hazard_curves, STATE['vulnerability_curves'], exposure_portfolio)
    
    ratio_results = {}
    loss_curves = {}
    losses_one_perc = {}
    interval = 0.01
    
    for gridpoint in region_constraint.grid:
        #logging.debug("Computing loss_ratio_curve for %s", gridpoint)
        # TODO(jmc): Spawn a task for each larger region, eg
        # Make smaller sets of sites and batch them off
        site = gridpoint.site
        val = risk_engine.compute_loss_ratio_curve(gridpoint)
        if val:
            ratio_results[gridpoint] = val
            loss_curve = risk_engine.compute_loss_curve(gridpoint, ratio_results[gridpoint])
            loss_curves[gridpoint] = loss_curve
            losses_one_perc[gridpoint] = engines.loss_from_curve(loss_curve, interval)
    
    # TODO(jmc): Pick output generator from config or cli flags
    output_generator = output.SimpleOutput()
    output_generator.serialize(ratio_results)
    output_generator.serialize(loss_curves)
    output_generator = geotiff.GeoTiffFile(output_file, region_constraint.grid)
    output_generator.serialize(losses_one_perc)
