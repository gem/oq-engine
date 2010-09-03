"""
Top-level managers for computation classes.
"""

class ProbabilisticLossRatioCalculator(object):
    """Computes loss ratio curves based on hazard curves and 
    exposure portfolios"""
    
    def __init__(self, hazard_curves, vulnerability_curves):
        """ Prepare the calculator for computations"""
        self.hazard_curves = hazard_curves
        self.vulnerability_curves = vulnerability_curves
    
    def compute(self, gridpoint):
        """ Returns the loss ratio curve for a single site"""
        # TODO(jmc): Hazard Curves need to be indexed by gridpoint

        if gridpoint not in self.hazard_curves.keys():
            return None
        return ([2.0, 1.0, 0.0], [0.1, 0.2, 0.3])
    
    def compute_all(self, sites_of_interest):
        """Compute ALL the sites (only for testing)"""
        ratio_results = {}
        for site in sites_of_interest:
            ratio_results[site] = self.compute(site)
        return ratio_results


class ProbabilisticLossCalculator(object):
    """Computes loss curves based on exposure portfolio and
    loss ratio curves"""
    def __init__(self, exposure_portfolio):
        self.exposure_portfolio = exposure_portfolio
    
    def compute(self, gridpoint, loss_ratio_curve):
        """ Returns the loss curve based on loss ratio and exposure"""
        if loss_ratio_curve is None:
            print "No loss ratio curve at %s" % gridpoint
            return None
        # TODO(jmc): Exposure needs to be indexed by gridpoint
        if gridpoint not in self.exposure_portfolio.keys():
            print "Don't have exposure for this point: %s" % gridpoint
            return None
        return ([0.0, 0.1, 0.2, 0.3], [0.9, 0.8, 0.5, 0.2])

def loss_from_curve(curve, interval):
    return 0.4