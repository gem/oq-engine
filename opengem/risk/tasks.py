#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Tasks in the risk engine include the following:

 * Input parsing
 * Various calculation steps
 * Output generation
 
"""

import logging
import sys

from opengem.risk import engines
from opengem import output
from opengem import grid

from opengem import flags
FLAGS = flags.FLAGS




def main():
    """ Typically this will run in daemon mode,
    and these tasks will be spawned from AMQP messages.
    In testing mode, we run directly against a simple set
    of input files."""
    # Parse the input files, and decide what to do
    
    hazard_curves = {}
    for lon in range(10.0, 50.0, 2):
        for lat in range(-60.0, -30.0, 5):
            site = grid.Site(lon, lat)
            hazard_curves[site] = ([1.0, 0.9, 0.4, 0.2, 0.0, 0.0], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    
    vulnerability_curves = {}
    vulnerability_curves['brick'] = ([0.2, 0.3, 0.4, 0.9, 0.95, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    vulnerability_curves['stone'] = ([0.2, 0.21, 0.41, 0.94, 0.95, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    vulnerability_curves['wood'] = ([0.0, 0.0, 0.0, 0.0, 0.0, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    
    # Since we've got hazard curves, let's do probabilistic assessment
    ratio_engine = engines.ProbabilisticLossRatioCalculator(hazard_curves, vulnerability_curves)
    
    exposure_portfolio = {}
    # # Pretend there are only two cities in this country
    exposure_portfolio[grid.Site(-175.2, 49.0)] = (200000, 'New York')
    exposure_portfolio[grid.Site(65.2, 55.0)] = (400000, 'London')
    loss_engine = engines.ProbabilisticLossCalculator(exposure_portfolio)
    # 
    # TODO(jmc): Load this from a portfolio file
    
    sites_of_interest = {}
    assets = {}
    ratio_results = {}
    loss_results = {}
    
    for lon in range(10.0, 50.0):
        for lat in range(-60.0, -30.0):
            # Random asset value
            site = grid.Site(lon, lat)
            assets[site] = 100
            sites_of_interest[site] = True # Is this retarded?
    
    for site in sites_of_interest:
        # TODO(jmc): Spawn a task for each larger region, eg
        # Make smaller sets of sites and batch them off
        ratio_results[site] = ratio_engine.compute(site)
        loss_results[site] = loss_engine.compute(site, ratio_results[site])
    
    # TODO(jmc): Pick output generator from config or cli flags
    output_generator = output.SimpleOutput()
    return output_generator.serialize(loss_results)


if __name__ == "__main__":
    ARGS = FLAGS(sys.argv)
    
    if FLAGS.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    main()