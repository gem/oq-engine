"""
Top-level managers for computation classes.
"""
import sys
sys.path.append("/Users/benwyss/Projects/opengem")
from opengem.risk import probabilistic_scenario

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
        return probabilistic_scenario.compute_loss_ratio_curve(
            asset['VulnerabilityFunction'], hazard_curve)
    
    def compute_loss_curve(self, gridpoint, loss_ratio_curve):
        """ Returns the loss curve based on loss ratio and exposure"""
        
        if loss_ratio_curve is None:
            return None
        if gridpoint not in self.exposure_portfolio.keys():
            return None
        asset = self.exposure_portfolio[gridpoint]
        return probabilistic_scenario.compute_loss_curve(
            loss_ratio_curve, asset['AssetValue'])
        
def compute_loss(loss_curve, pe_interval):
    return probabilistic_scenario.compute_conditional_loss(loss_curve, pe_interval)



def loss_from_curve(curve, interval):
    return 0.4