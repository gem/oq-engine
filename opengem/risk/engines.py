"""
Top-level managers for computation classes.
"""

from opengem.risk import probabilistic_scenario

class ProbabilisticLossRatioCalculator(object):
    """Computes loss ratio curves based on hazard curves and 
    exposure portfolios"""
    
    def __init__(self, hazard_curves, 
            vulnerability_curves, exposure_portfolio):
        """ Prepare the calculator for computations"""
        self.hazard_curves = hazard_curves
        self.vulnerability_curves = vulnerability_curves
        self.exposure_portfolio = exposure_portfolio
    
    def compute_loss_ratio_curve(self, gridpoint):
        """ Returns the loss ratio curve for a single site"""
        # TODO(jmc): Hazard Curves need to be indexed by gridpoint

        if (gridpoint not in self.hazard_curves.keys()):
            # print "Don't have haz curve"
            return None
        if (gridpoint not in self.exposure_portfolio.keys()):
            print "Gridpoint not in exposure portfolio at %s" % gridpoint
            return None
        print "Gridpoint object is %s" % gridpoint
        asset = self.exposure_portfolio[gridpoint]
        hazard_curve = self.hazard_curves[gridpoint]
        print "Asset is %s" % asset
        for vuln in self.vulnerability_curves:
            print vuln
        vuln_curve = self.vulnerability_curves[asset['VulnerabilityFunction']]
        return probabilistic_scenario.compute_loss_ratio_curve(vuln_curve, hazard_curve)
    
    def compute_loss_curve(self, gridpoint, loss_ratio_curve):
        """ Returns the loss curve based on loss ratio and exposure"""
        if loss_ratio_curve is None:
            # print "No loss ratio curve at %s" % gridpoint
            return None
        # TODO(jmc): Exposure needs to be indexed by gridpoint
        if gridpoint not in self.exposure_portfolio.keys():
            # print "Don't have exposure for this point: %s" % gridpoint
            return None
        return ([0.0, 0.1, 0.2, 0.3], [0.9, 0.8, 0.5, 0.2])

    def compute_all(self, sites_of_interest):
        """Compute ALL the sites (only for testing)"""
        ratio_results = {}
        for site in sites_of_interest:
            ratio_results[site] = self.compute(site)
        return ratio_results


def loss_from_curve(curve, interval):
    return 0.4