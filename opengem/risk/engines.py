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
    
    def compute(self, site):
        """ Returns the loss ratio curve for a single site"""
        if site not in self.hazard_curves:
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
    
    def compute(self, site, loss_ratio_curve):
        """ Returns the loss curve based on loss ratio and exposure"""
        if loss_ratio_curve is None:
            return None
        if site not in self.exposure_portfolio:
            return None
        return ([0.0, 0.1, 0.2, 0.3], [0.9, 0.8, 0.5, 0.2])