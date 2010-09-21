"""
Top-level managers for computation classes.
"""

from opengem.risk import classical_psha_based

class ProbabilisticLossRatioCalculator(object):
    """Computes loss ratio curves based on hazard curves and 
    exposure portfolios"""
    
    def __init__(self, hazard_curves, exposure_portfolio):
        """ Prepare the calculator for computations"""
        self.hazard_curves = hazard_curves
        self.exposure_portfolio = exposure_portfolio
    
    def compute_loss_ratio_curve(self, gridpoint):
        """ Returns the loss ratio curve for a single gridpoint"""

        if (gridpoint not in self.hazard_curves.keys()):
            return None
        if (gridpoint not in self.exposure_portfolio.keys()):
            return None
        asset = self.exposure_portfolio[gridpoint]
        hazard_curve = self.hazard_curves[gridpoint]
        return classical_psha_based.compute_loss_ratio_curve(
            asset['VulnerabilityFunction'], hazard_curve)
    
    def compute_loss_curve(self, gridpoint, loss_ratio_curve):
        """ Returns the loss curve based on loss ratio and exposure"""
        
        if loss_ratio_curve is None:
            return None
        if gridpoint not in self.exposure_portfolio.keys():
            return None
        asset = self.exposure_portfolio[gridpoint]
        return classical_psha_based.compute_loss_curve(
            loss_ratio_curve, asset['AssetValue'])
        
def compute_loss(loss_curve, pe_interval):
    """Interpolate loss for a specific probability of exceedence interval"""
    loss = classical_psha_based.compute_conditional_loss(
                loss_curve, pe_interval)
    return loss