# -*- coding: utf-8 -*-
"""
Top-level managers for computation classes.
"""

from openquake import logs
from openquake import kvs
from openquake import shapes

from openquake.parser import vulnerability
from openquake.risk import classical_psha_based

LOGGER = logs.RISK_LOG

# TODO (ac): This class is not covered by unit tests...
class ClassicalPSHABasedLossRatioCalculator(object):
    """Computes loss ratio curves based on hazard curves and 
    exposure portfolios"""

    def __init__(self, job_id, block_id):
        """ Prepare the calculator for computations"""

        self.job_id = job_id
        self.block_id = block_id

        self.vuln_curves = \
                vulnerability.load_vuln_curves_from_kvs(self.job_id)

        # self.vuln_curves is a dict of {string: Curve}
        LOGGER.debug("ProbabilisticLossRatioCalculator init: vuln curves are")

        for k, v in self.vuln_curves.items():
            LOGGER.debug("%s: %s" % (k, v))
 
    def compute_loss_ratio_curve(self, gridpoint):
        """ Returns the loss ratio curve for a single gridpoint"""

        # check in kvs if hazard and exposure for gridpoint are there
        kvs_key_hazard = kvs.generate_product_key(self.job_id, 
            kvs.tokens.HAZARD_CURVE_KEY_TOKEN, self.block_id, gridpoint)
       
        hazard_curve_json = kvs.get_client(binary=False).get(kvs_key_hazard)
        LOGGER.debug("hazard curve as JSON: %s" % hazard_curve_json)
 
        hazard_curve = shapes.EMPTY_CURVE
        hazard_curve.from_json(hazard_curve_json)

        LOGGER.debug("hazard curve at key %s is %s" % (kvs_key_hazard, 
            hazard_curve))

        if hazard_curve is None:
            LOGGER.debug("no hazard curve found")
            return None

        kvs_key_exposure = kvs.generate_product_key(self.job_id, 
            kvs.tokens.EXPOSURE_KEY_TOKEN, self.block_id, gridpoint)
        
        asset = kvs.get_value_json_decoded(kvs_key_exposure)

        LOGGER.debug("asset at key %s is %s" % (kvs_key_exposure, asset))

        if asset is None:
            LOGGER.debug("no asset found")
            return None

        LOGGER.debug("compute method: vuln curves are")
        for k, v in self.vulnerability_curves.items(): #pylint: disable=E1101
            LOGGER.debug("%s: %s" % (k, v.values))

        #pylint: disable=E1101
        vulnerability_curve = \
            self.vulnerability_curves[asset['VulnerabilityFunction']]

        # selected vuln function is Curve
        return classical_psha_based.compute_loss_ratio_curve(
            vulnerability_curve, hazard_curve)
    
    def compute_loss_curve(self, gridpoint, loss_ratio_curve):
        """Return the loss curve based on loss ratio and exposure."""
        
        if loss_ratio_curve is None:
            return None

        kvs_key_exposure = kvs.generate_product_key(self.job_id,
            kvs.tokens.EXPOSURE_KEY_TOKEN, self.block_id, gridpoint)

        asset = kvs.get_value_json_decoded(kvs_key_exposure)

        if asset is None:
            return None

        return classical_psha_based.compute_loss_curve(
            loss_ratio_curve, asset['AssetValue'])


def compute_loss(loss_curve, pe_interval):
    """Interpolate loss for a specific probability of exceedance interval"""
    loss = classical_psha_based.compute_conditional_loss(loss_curve, 
                                                         pe_interval)
    return loss
