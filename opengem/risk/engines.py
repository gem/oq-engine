

class ProbabalisticLossRatioCalculator(object):
    """ Computes loss ratio curves based on hazard curves and 
    exposure portfolios"""
    
    def __init__(self, hazard_curves, vulnerability_curves):
        """ Prepare the calculator for computations"""
        self.hazard_curves = hazard_curves
        self.vulnerability_curves = vulnerability_curves
    
    def compute(self, site):
        """ Returns the loss ratio curve for a single site"""
        return [2.0, 1.0, 0.0] 


class LossCalculator(object):
    def __init__(self, exposure_portfolio):
        self.exposure_portfolio = exposure_portfolio