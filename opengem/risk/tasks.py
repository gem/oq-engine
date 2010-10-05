#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Tasks in the risk engine include the following:

 * Input parsing
 * Various calculation steps
 * Output generation
 
"""

from opengem.logs import HAZARD_LOG, RISK_LOG
from opengem.risk import engines
import opengem.output.risk
from opengem import shapes
from opengem.output import geotiff
from opengem import producer
from opengem.parser import exposure
from opengem.parser import nrml
from opengem.parser import vulnerability

from opengem import flags
FLAGS = flags.FLAGS
    

# TODO(jmc): rather than passing files in here, determine the right 
# parser to use or create in the binary, and pass in loaded parsers.
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
    
    # TODO(jmc): Pick output generator from config or cli flags
    output_generator = opengem.output.risk.RiskXMLWriter("loss-curves.xml")
    output_generator.serialize(loss_curves)
    #output_generator = output.SimpleOutput()
    #output_generator.serialize(ratio_results)
    output_generator = geotiff.GeoTiffFile(output_file, region_constraint.grid)
    output_generator.serialize(losses_one_perc)
