# This file is part of OpenQuake.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

# -*- coding: utf-8 -*-
"""
The risk stuff using the classical psha based approach is not
currently implemented. The logic of this class needs to be
moved into one (or more) mixins.
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
                vulnerability.load_vuln_model_from_kvs(self.job_id)

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
